"""Execução serial e persistente de pesquisas do Radar."""
import asyncio
from datetime import timedelta, timezone
import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.settings import get_user_ai_service_from_db
from app.database import NicheResearch, Settings, get_engine
from app.schemas.radar import ResearchProgress, ResearchSnapshot
from app.services.radar_collectors import CollectorRegistry
from app.services.radar_collectors.base import Clock, CollectionContext, utc_now
from app.services.radar_repository import (
    LEASE_DURATION, claim_next, finish_snapshot, save_running_snapshot, seal_expired, unavailable_source,
)
from app.services.radar_summary import summarize_research, summary_error
from app.services.radar_schedule import enqueue_due_weeks
from app.services.radar_settings import read_source_secret

logger = logging.getLogger(__name__)
RUN_DURATION = timedelta(minutes=12)
SOURCE_TIMEOUT_SECONDS = 120
IDLE_SECONDS = 2


async def process_research(research_id: str, registry: CollectorRegistry, *, clock: Clock = utc_now) -> None:
    engine = await get_engine("system")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        row = await db.get(NicheResearch, research_id)
        if not row or row.status != "running" or row.lease_until is None:
            return
        lease = row.lease_until
        deadline = lease.replace(tzinfo=timezone.utc) - LEASE_DURATION + RUN_DURATION
        snapshot = ResearchSnapshot.model_validate(row.signals)

    for name in snapshot.enabled_sources:
        if name in snapshot.sources:
            continue
        if clock() >= deadline:
            break
        snapshot.progress = ResearchProgress(
            done=len(snapshot.sources), total=len(snapshot.enabled_sources), current_source=name,
        )
        collector = registry.get(name)
        async with sessions.begin() as db:
            if not await save_running_snapshot(db, research_id, lease, clock(), snapshot):
                return
            secret = await read_source_secret(db, row.user_id, name) if collector else None

        context = CollectionContext(row.user_id, research_id, deadline, clock, secret)
        if collector is None or snapshot.input is None:
            result = unavailable_source(name, snapshot, clock(), "unsupported", "Fonte indisponível.")
        else:
            try:
                result = await asyncio.wait_for(
                    collector.collect(snapshot.input, context),
                    timeout=min(SOURCE_TIMEOUT_SECONDS, context.remaining()),
                )
                if not context.remaining():
                    break
                if result.source != name:
                    raise ValueError("Fonte divergente.")
            except TimeoutError:
                result = unavailable_source(name, snapshot, clock(), "error", "Tempo de coleta esgotado.")
            except Exception:
                result = unavailable_source(name, snapshot, clock(), "error", "Falha na coleta da fonte.")
        snapshot.sources[name] = result
        snapshot.progress = ResearchProgress(done=len(snapshot.sources), total=len(snapshot.enabled_sources))
        async with sessions.begin() as db:
            if not await save_running_snapshot(db, research_id, lease, clock(), snapshot):
                return

    now = clock()
    status = finish_snapshot(snapshot, now, "Prazo total de coleta esgotado.")
    if snapshot.citable_evidence() and now < deadline:
        try:
            async with asyncio.timeout((deadline - now).total_seconds()):
                async with sessions() as db:
                    configured = await db.scalar(select(Settings.id).where(
                        Settings.user_id == row.user_id,
                        (Settings.api_provider == "codex") | (Settings.api_key != ""),
                    ))
                    ai = await get_user_ai_service_from_db(row.user_id, db) if configured else None
                if ai is not None:
                    snapshot.summary = await summarize_research(ai, snapshot)
        except Exception:
            snapshot.summary = summary_error()
    async with sessions.begin() as db:
        await save_running_snapshot(db, research_id, lease, clock(), snapshot, terminal=status)


async def run_radar_loop(stop: asyncio.Event, registry: CollectorRegistry) -> None:
    engine = await get_engine("system")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    while not stop.is_set():
        try:
            async with sessions.begin() as db:
                now = utc_now()
                await seal_expired(db, now)
                await enqueue_due_weeks(db, now)
                row = await claim_next(db, now)
            if row is not None:
                await process_research(row.id, registry)
                continue
        except (SQLAlchemyError, ValueError):
            logger.warning("O executor do Radar não conseguiu concluir o ciclo.")
        try:
            await asyncio.wait_for(stop.wait(), timeout=IDLE_SECONDS)
        except TimeoutError:
            pass
