from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app import database, main
from app.database import NicheResearch, User
from app.schemas.radar import RadarSettingsPatch
from app.services import ai_service
from app.services.radar_schedule import enqueue_due_weeks, weekly_key
from app.services.radar_settings import save_radar_settings


def utc(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


@pytest.mark.parametrize(("zone", "before", "after"), [
    ("America/Sao_Paulo", "2026-11-23T11:59", "2026-11-23T12:00"),
    ("Europe/Madrid", "2026-11-23T07:59", "2026-11-23T08:00"),
])
def test_monday_at_nine_in_configured_timezone(zone, before, after):
    assert weekly_key(utc(before), zone) is None
    assert weekly_key(utc(after), zone) == "2026-W48"


async def configure(db, admin="admin", enabled=True, active=True):
    db.add(User(user_id=admin, username=admin, display_name=admin, linuxdo_id=admin,
                is_admin=True, trust_level=0 if active else -1))
    await save_radar_settings(db, admin, RadarSettingsPatch(schedule={
        "enabled": enabled, "timezone": "America/Sao_Paulo",
        "entries": [
            {"topic": "Crochê Criativo", "country": "BR", "product_type": "fiction"},
            {"topic": " CROCHÊ   CRIATIVO ", "country": "BR", "product_type": "fiction"},
        ],
    }))
    await db.commit()


@pytest.mark.asyncio
async def test_catchup_only_current_week_and_no_duplicates(db_session):
    await configure(db_session)
    await configure(db_session, "inativo", active=False)
    wednesday = utc("2026-12-30T12:00")
    assert await enqueue_due_weeks(db_session, wednesday) == 1
    await db_session.commit()
    assert await enqueue_due_weeks(db_session, utc("2027-01-01T12:00")) == 0
    assert await enqueue_due_weeks(db_session, utc("2027-01-04T12:00")) == 1
    await db_session.commit()
    rows = (await db_session.scalars(select(NicheResearch).order_by(NicheResearch.week_key))).all()
    assert [(r.week_key, r.mode, r.user_id) for r in rows] == [
        ("2026-W53", "weekly", "admin"), ("2027-W01", "weekly", "admin"),
    ]
    assert rows[0].signals["input"]["language"] == "pt-BR"


@pytest.mark.asyncio
async def test_disabled_schedule_makes_no_jobs(db_session):
    await configure(db_session, enabled=False)
    assert await enqueue_due_weeks(db_session, utc("2026-11-25T12:00")) == 0


@pytest.mark.asyncio
async def test_lifespan_shuts_worker_before_clients(db_session, monkeypatch):
    events = []

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            events.append("http")

    async def engine(_):
        return db_session.bind

    async def worker(stop, registry):
        assert set(registry) == {"firecrawl", "youtube"}
        await stop.wait()
        events.append("radar")

    def noop():
        return None

    def close(name):
        async def run():
            events.append(name)
        return run

    monkeypatch.setattr(database, "get_engine", engine)
    monkeypatch.setattr(main, "AsyncClient", Client)
    monkeypatch.setattr(main, "register_status_sync", noop)
    monkeypatch.setattr(main, "run_radar_loop", worker)
    monkeypatch.setattr(main, "mcp_client", SimpleNamespace(cleanup=close("mcp")))
    monkeypatch.setattr(main, "close_db", close("db"))
    monkeypatch.setattr(ai_service, "cleanup_http_clients", close("ia"))

    async with main.lifespan(main.app):
        assert not events
    assert events == ["radar", "http", "mcp", "ia", "db"]
