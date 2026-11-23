import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.schemas.radar import EvidenceItem, ResearchInput, ResearchSnapshot, SourceResult
from app.services import radar_worker
from app.services.radar_repository import (
    claim_next, enqueue_research, get_research, save_running_snapshot, seal_expired,
)

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)


def item():
    return EvidenceItem(id="obs-1", kind="content", label="Observação", url="https://example.org/artigo")


async def pendente(db_session, fontes=("web",)):
    row = await enqueue_research(db_session, "admin", ResearchInput(
        topic="Tema", country="BR", product_type="lowticket", mode="manual", input_key="id",
        snapshot=ResearchSnapshot(
            input={"query": "Tema", "country": "BR", "language": "pt-BR", "currency": "BRL",
                   "product_type": "lowticket", "start_date": "2026-09-28", "end_date": "2026-11-22"},
            enabled_sources=fontes,
        ),
    ))
    await db_session.commit()
    return row


def fake_collector(source, clock=lambda: NOW, fail=False):
    class Fake:
        async def collect(self, input, context):
            if fail:
                raise ValueError("segredo do provedor")
            return SourceResult(source=source, status="ok", collected_at=clock(),
                                scope=input.country, method_version="1", items=[item()])

    return Fake()


async def claim(db_session):
    row = await claim_next(db_session, NOW)
    await db_session.commit()
    return row


async def stored(db_session, research):
    async with async_sessionmaker(db_session.bind)() as db:
        return await get_research(db, "admin", research.id)


def use_database(db_session, monkeypatch):
    async def engine(_):
        return db_session.bind

    monkeypatch.setattr(radar_worker, "get_engine", engine)


@pytest.mark.asyncio
async def test_two_claims_only_one_wins(db_session):
    research = await pendente(db_session)
    maker = async_sessionmaker(db_session.bind, expire_on_commit=False)

    async def take():
        async with maker.begin() as db:
            return await claim_next(db, NOW)

    first, second = await asyncio.gather(take(), take())
    assert [row.id for row in (first, second) if row] == [research.id]


@pytest.mark.asyncio
@pytest.mark.parametrize("all_collected", [False, True])
async def test_interrupted_run_with_committed_results_becomes_partial(db_session, all_collected):
    await pendente(db_session, ("web", "meta"))
    row = await claim(db_session)
    snapshot = ResearchSnapshot.model_validate(row.signals)
    snapshot.sources["web"] = SourceResult(
        source="web", status="ok" if all_collected else "partial",
        collected_at=NOW, scope="BR", method_version="1",
        items=[item()],
    )
    if all_collected:
        snapshot.weights = {"demand": 0, "competition": 100, "price": 0}
        snapshot.sources["meta"] = SourceResult(
            source="meta", status="empty", collected_at=NOW, scope="BR", method_version="1",
        )
    assert await save_running_snapshot(db_session, row.id, row.lease_until, NOW, snapshot)
    await db_session.commit()
    assert await seal_expired(db_session, NOW + timedelta(minutes=15)) == 1
    await db_session.commit()
    final = await stored(db_session, row)
    assert final.status == "partial"
    assert final.signals["sources"]["web"]["items"][0]["id"] == "obs-1"
    assert await claim_next(db_session, NOW + timedelta(minutes=16)) is None


@pytest.mark.asyncio
async def test_one_source_failure_keeps_other_items_and_does_not_synthesize_zero(db_session, monkeypatch):
    use_database(db_session, monkeypatch)
    await pendente(db_session, ("meta", "web"))
    row = await claim(db_session)
    await radar_worker.process_research(
        row.id, {"meta": fake_collector("meta", fail=True), "web": fake_collector("web")}, clock=lambda: NOW,
    )
    final = await stored(db_session, row)
    assert final.status == "partial"
    assert final.score is None
    assert final.signals["score"]["competition"] is None
    assert final.signals["sources"]["meta"]["status"] == "error"
    assert "segredo" not in str(final.signals)
    assert final.signals["progress"] == {"done": 2, "total": 2, "current_source": None}


@pytest.mark.asyncio
async def test_deadline_closes_job_and_never_runs_late_sources(db_session, monkeypatch):
    use_database(db_session, monkeypatch)
    await pendente(db_session, ("web", "youtube"))
    row = await claim(db_session)
    time = NOW
    called = []

    class Slow:
        async def collect(self, input, context):
            nonlocal time
            assert context.deadline == NOW + timedelta(minutes=12)
            time = context.deadline
            return await fake_collector("web").collect(input, context)

    class Late:
        async def collect(self, input, context):
            called.append(True)
            return await fake_collector("youtube").collect(input, context)

    await radar_worker.process_research(row.id, {"web": Slow(), "youtube": Late()}, clock=lambda: time)
    final = await stored(db_session, row)
    assert not called
    assert final.status == "failed"
    assert final.signals["sources"]["web"]["status"] == "error"
    assert final.signals["sources"]["youtube"]["status"] == "error"


@pytest.mark.asyncio
async def test_terminal_snapshot_cannot_be_overwritten(db_session):
    await pendente(db_session)
    row = await claim(db_session)
    lease = row.lease_until
    now = NOW + timedelta(minutes=15)
    assert await seal_expired(db_session, now) == 1
    await db_session.commit()
    assert not await save_running_snapshot(
        db_session, row.id, lease, now, ResearchSnapshot(), terminal="complete",
    )
    final = await stored(db_session, row)
    assert final.status == "failed"
