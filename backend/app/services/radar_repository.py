"""Persistência das pesquisas no âmbito do administrador."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import unicodedata

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import NicheResearch, WritingBrief
from app.schemas.radar import (
    PageFilters, ResearchFilters, ResearchInput, ResearchPage, ResearchProgress, ResearchSnapshot,
    ResearchRequest, ResearchStatus, SourceResult, SourceStatus,
)
from app.services.radar_scoring import score_research

LEASE_DURATION = timedelta(minutes=15)


class ResearchConflict(ValueError):
    """A chave informada já vincula outra entrada."""


def normalize_topic(topic: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", topic).split()).casefold()


def insert_once(db, model, values, key):
    insert = sqlite_insert if db.get_bind().dialect.name == "sqlite" else pg_insert
    return insert(model).values(**values).on_conflict_do_nothing(index_elements=[key])


def _manual_key(admin_id: str, request_id: str) -> str:
    return hashlib.sha256(f"manual:{admin_id}:{request_id}".encode()).hexdigest()


def _verify_manual_input(research: NicheResearch, topic: str, country: str, product_type: str,
                         confirmation: bool) -> None:
    original = (
        research.topic, research.country, research.product_type,
        (research.signals or {}).get("budget_confirmation", False),
    )
    if original != (topic.strip(), country, product_type, confirmation):
        raise ResearchConflict("Esta chave já foi usada em uma pesquisa diferente.")


async def get_manual_retry(
    db: AsyncSession, admin_id: str, payload: ResearchRequest,
) -> NicheResearch | None:
    row = await db.scalar(select(NicheResearch).where(
        NicheResearch.user_id == admin_id,
        NicheResearch.input_key == _manual_key(admin_id, str(payload.request_id)),
    ))
    if row is not None:
        _verify_manual_input(row, payload.topic, payload.country, payload.product_type, payload.budget_confirmation)
    return row


async def enqueue_research(db: AsyncSession, admin_id: str, input: ResearchInput) -> NicheResearch:
    research, _ = await enqueue_research_once(db, admin_id, input)
    return research


async def enqueue_research_once(
    db: AsyncSession, admin_id: str, input: ResearchInput,
) -> tuple[NicheResearch, bool]:
    topic_key = normalize_topic(input.topic)
    if input.mode == "manual":
        key = _manual_key(admin_id, input.input_key)
    else:
        identity = (admin_id, input.mode, input.week_key, topic_key, input.country, input.product_type)
        key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
    values = dict(
        user_id=admin_id, topic=input.topic.strip(), topic_key=topic_key, country=input.country,
        product_type=input.product_type, mode=input.mode, week_key=input.week_key,
        topic_hash=hashlib.sha256(topic_key.encode()).hexdigest(),
        input_key=key, signals=input.snapshot.model_dump(mode="json"),
    )
    stmt = insert_once(db, NicheResearch, values, NicheResearch.input_key).returning(NicheResearch)
    inserted = await db.scalar(stmt)
    if inserted is not None:
        return inserted, True
    research = (await db.scalars(select(NicheResearch).where(
        NicheResearch.user_id == admin_id, NicheResearch.input_key == key,
    ))).one()
    if input.mode == "manual":
        _verify_manual_input(
            research, input.topic, input.country, input.product_type, input.snapshot.budget_confirmation,
        )
    return research, False


async def get_research(db: AsyncSession, admin_id: str, research_id: str) -> NicheResearch | None:
    return await db.scalar(select(NicheResearch).where(
        NicheResearch.user_id == admin_id, NicheResearch.id == research_id,
    ))


async def _page(db, query, filters, *order_by):
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    items = await db.scalars(query.order_by(*order_by).limit(filters.page_size).offset(
        (filters.page - 1) * filters.page_size,
    ))
    return ResearchPage(items=list(items), total=total, **filters.model_dump(include={"page", "page_size"}))


async def list_researches(db: AsyncSession, admin_id: str, filters: ResearchFilters) -> ResearchPage:
    research = NicheResearch
    order = (research.created_at.desc().nulls_last(), research.id.desc())
    rank = select(research.id, func.row_number().over(
        partition_by=(research.topic_key, research.country, research.product_type,
                      case((research.topic_key.is_(None), research.id))),
        order_by=order,
    ).label("position")).where(research.user_id == admin_id)
    for name in ("country", "product_type", "mode", "week_key"):
        value = getattr(filters, name)
        if value is not None:
            rank = rank.where(getattr(research, name) == value)
    ranked = rank.subquery()
    query = select(research).join(ranked, ranked.c.id == research.id).where(ranked.c.position == 1)
    if filters.mode == "weekly" or filters.week_key:
        order = (research.score.desc().nulls_last(), research.topic_key, research.country,
                 research.product_type, research.id)
    return await _page(db, query, filters, *order)


def _history_query(research: NicheResearch):
    model = NicheResearch
    query = select(model).where(model.user_id == research.user_id)
    if research.topic_key is None:
        query = query.where(model.id == research.id)
    else:
        query = query.where(
            model.topic_key == research.topic_key,
            model.topic_hash == research.topic_hash,
            model.country == research.country,
            model.product_type == research.product_type,
        )
    return query


async def list_history(db: AsyncSession, research: NicheResearch, filters: PageFilters) -> ResearchPage:
    model = NicheResearch
    return await _page(db, _history_query(research), filters, model.created_at.desc().nulls_last(), model.id.desc())


async def previous_research(db: AsyncSession, research: NicheResearch) -> NicheResearch | None:
    if research.topic_key is None or research.created_at is None:
        return None
    model = NicheResearch
    return await db.scalar(_history_query(research).where(or_(
        model.created_at < research.created_at,
        and_(model.created_at == research.created_at, model.id < research.id),
    )).order_by(model.created_at.desc(), model.id.desc()).limit(1))


def _brief_query(admin_id: str):
    return select(WritingBrief, NicheResearch).join(
        NicheResearch, NicheResearch.id == WritingBrief.research_id,
    ).where(WritingBrief.admin_id == admin_id, NicheResearch.user_id == admin_id)


async def get_brief(db: AsyncSession, admin_id: str, brief_id: str):
    return (await db.execute(_brief_query(admin_id).where(WritingBrief.id == brief_id))).one_or_none()


async def list_briefs(db: AsyncSession, admin_id: str, filters: PageFilters) -> ResearchPage:
    query = _brief_query(admin_id)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    pairs = await db.execute(query.order_by(WritingBrief.created_at.desc(), WritingBrief.id.desc())
        .limit(filters.page_size).offset((filters.page - 1) * filters.page_size))
    return ResearchPage(items=list(pairs), total=total, page=filters.page, page_size=filters.page_size)


async def create_brief(db: AsyncSession, research: NicheResearch) -> tuple[WritingBrief, bool]:
    stmt = insert_once(db, WritingBrief, {
        "research_id": research.id, "admin_id": research.user_id,
    }, WritingBrief.research_id).returning(WritingBrief)
    brief = await db.scalar(stmt)
    if brief is not None:
        return brief, True
    brief = (await db.scalars(select(WritingBrief).where(
        WritingBrief.research_id == research.id, WritingBrief.admin_id == research.user_id,
    ))).one()
    return brief, False


async def claim_next(db: AsyncSession, now: datetime) -> NicheResearch | None:
    model = NicheResearch
    candidate = select(model.id).where(
        model.status == "pending", model.mode.is_not(None),
    ).order_by(model.created_at.asc().nulls_last(), model.id).limit(1).scalar_subquery()
    stmt = update(model).where(model.id == candidate, model.status == "pending").values(
        status="running", lease_until=_db_utc(now) + LEASE_DURATION,
    ).returning(model)
    return await db.scalar(stmt)


def _db_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def unavailable_source(name: str, snapshot: ResearchSnapshot, now: datetime, status: SourceStatus,
                       reason: str) -> SourceResult:
    return SourceResult(
        source=name, status=status, collected_at=now, scope=snapshot.input.country if snapshot.input else "",
        method_version="1", limits={"notes": [reason]},
    )


def finish_snapshot(
    snapshot: ResearchSnapshot, now: datetime, reason: str, *, interrupted: bool = False,
) -> ResearchStatus:
    for source in snapshot.enabled_sources:
        if source not in snapshot.sources:
            snapshot.sources[source] = unavailable_source(source, snapshot, now, "error", reason)
    snapshot.progress = ResearchProgress(done=len(snapshot.sources), total=len(snapshot.enabled_sources))
    snapshot.score = score_research(snapshot)
    results = list(snapshot.sources.values())
    usable = any(
        result.status == "empty" or (result.status in {"ok", "partial"} and result.items)
        for result in results
    )
    if not interrupted and snapshot.score.score is not None and all(
        result.status in {"ok", "empty", "not_applicable"} for result in results
    ):
        return "complete"
    return "partial" if usable else "failed"


async def save_running_snapshot(
    db: AsyncSession, research_id: str, lease: datetime, now: datetime, snapshot: ResearchSnapshot,
    *, terminal: ResearchStatus | None = None,
) -> bool:
    values = {"signals": snapshot.model_dump(mode="json")}
    if terminal:
        values.update(status=terminal, finished_at=_db_utc(now),
                      score=snapshot.score.score if snapshot.score else None, lease_until=None)
    query = update(NicheResearch).where(
        NicheResearch.id == research_id, NicheResearch.status == "running",
        NicheResearch.lease_until == lease, NicheResearch.lease_until > _db_utc(now),
    ).values(**values).returning(NicheResearch.id)
    return await db.scalar(query) is not None


async def seal_expired(db: AsyncSession, now: datetime) -> int:
    model = NicheResearch
    expired = await db.scalars(select(model).where(
        model.status == "running", model.lease_until <= _db_utc(now),
    ))
    count = 0
    for row in expired:
        snapshot = ResearchSnapshot.model_validate(row.signals)
        status = finish_snapshot(snapshot, now, "A coleta foi interrompida.", interrupted=True)
        query = update(model).where(
            model.id == row.id, model.status == "running", model.lease_until <= _db_utc(now),
        ).values(status=status, signals=snapshot.model_dump(mode="json"), finished_at=_db_utc(now),
                 score=snapshot.score.score, lease_until=None).returning(model.id)
        count += await db.scalar(query) is not None
    return count
