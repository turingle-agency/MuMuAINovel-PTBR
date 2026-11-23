from types import SimpleNamespace
from datetime import datetime

import httpx
import pytest
import pytest_asyncio
from cryptography.fernet import Fernet

from app.config import settings
from app.database import NicheResearch, RadarSettings, get_db
from app.main import app
from app.security import create_session_token
from app.services.radar_settings import read_source_secret
from app.user_manager import user_manager


@pytest_asyncio.fixture
async def radar_client(db_session, monkeypatch):
    async def fake_user(user_id):
        return SimpleNamespace(user_id=user_id, is_admin=user_id != "comum", trust_level=0)

    async def db():
        yield db_session

    monkeypatch.setattr(user_manager, "get_user", fake_user)
    monkeypatch.setitem(app.dependency_overrides, get_db, db)
    monkeypatch.setattr(settings, "radar_secret_key", Fernet.generate_key().decode())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client


def logar(client, user="admin-a"):
    client.cookies.set("session_token", create_session_token(user, 300))


@pytest.mark.asyncio
async def test_admin_only_and_settings_isolated(radar_client):
    path = "/api/radar/settings"
    assert (await radar_client.get(path)).status_code == 401
    logar(radar_client, "comum")
    assert (await radar_client.get(path)).status_code == 403
    logar(radar_client)
    response = await radar_client.put(path, json={"weights": {"demand": 100, "competition": 0, "price": 0}})
    assert response.status_code == 200
    assert response.json()["weights"]["demand"] == 100
    logar(radar_client, "admin-b")
    assert (await radar_client.get(path)).json()["weights"]["demand"] == 50


@pytest.mark.asyncio
async def test_secret_never_roundtrips_or_leaks_in_validation(radar_client, db_session, monkeypatch, caplog):
    monkeypatch.setattr(settings, "debug", True)
    logar(radar_client)
    path = "/api/radar/settings"
    secret = "segredo-provedor-123"
    put = await radar_client.put(path, json={"secrets": {"firecrawl": secret}})
    assert put.status_code == 200
    assert secret not in put.text
    row = await db_session.get(RadarSettings, "admin-a")
    assert secret not in str(row.encrypted_secrets)
    assert await read_source_secret(db_session, "admin-a", "firecrawl") == secret
    assert await read_source_secret(db_session, "admin-b", "firecrawl") is None

    untouched = await radar_client.put(path, json={"weights": {"demand": 100, "competition": 0, "price": 0}})
    assert untouched.json()["credentials"]["firecrawl"]["present"]
    assert secret not in (await radar_client.get(path)).text
    invalid = await radar_client.put(path, json={"secrets": {"firecrawl": {"token": secret}}})
    assert invalid.status_code == 422
    assert secret not in invalid.text + caplog.text
    removal = await radar_client.put(path, json={"secrets": {"firecrawl": None}})
    assert not removal.json()["credentials"]["firecrawl"]["present"]
    assert await read_source_secret(db_session, "admin-a", "firecrawl") is None


@pytest.mark.asyncio
async def test_default_profiles_weights_and_schedule_limits(radar_client):
    logar(radar_client)
    path = "/api/radar/settings"
    default = (await radar_client.get(path)).json()
    assert [p["country"] for p in default["profiles"] if p["active"]] == ["BR"]
    assert default["weights"] == {"demand": 50, "competition": 30, "price": 20}
    assert default["schedule"] == {"enabled": False, "timezone": "America/Sao_Paulo", "entries": []}
    bad_timezone = await radar_client.put(path, json={"schedule": {"timezone": "Fuso/Incorreto"}})
    assert bad_timezone.status_code == 422
    bad_schedule = await radar_client.put(path, json={"schedule": {"entries": [
        {"topic": str(i), "country": "BR", "product_type": "fiction"} for i in range(13)
    ]}})
    assert bad_schedule.status_code == 422


@pytest.mark.asyncio
async def test_paid_source_check_changes_no_budget(radar_client, db_session, monkeypatch):
    async def no_network(*args, **kwargs):
        pytest.fail("Diagnóstico de fonte paga chamou HTTP")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", no_network)
    logar(radar_client)
    db_session.add_all([
        NicheResearch(user_id="admin-a", topic="Tema", status="partial", finished_at=datetime(2026, 11, 21),
                      signals={"sources": {"apify": {"status": "budget_blocked"}}}),
        NicheResearch(user_id="admin-b", topic="Tema", status="partial", finished_at=datetime(2026, 11, 22),
                      signals={"sources": {"apify": {"status": "error"}}}),
    ])
    await db_session.commit()
    before = (await radar_client.get("/api/radar/budget")).json()
    response = await radar_client.post("/api/radar/sources/apify/check")
    assert response.status_code == 200
    assert response.json()["access"] == "not_tested"
    assert response.json()["last_status"] == "budget_blocked"
    assert (await radar_client.get("/api/radar/budget")).json() == before


@pytest.mark.asyncio
async def test_portugal_does_not_fall_back_to_spain_amazon(radar_client):
    logar(radar_client)
    coverage = (await radar_client.get("/api/radar/settings")).json()["coverage"]
    assert coverage["PT"]["amazon"]["status"] == "unsupported"
    assert "Portugal" in coverage["PT"]["amazon"]["detail"]


@pytest.mark.asyncio
async def test_invalid_encryption_key_rejects_storage(radar_client, db_session, monkeypatch):
    logar(radar_client)
    monkeypatch.setattr(settings, "radar_secret_key", "invalida")
    response = await radar_client.put("/api/radar/settings", json={"secrets": {"youtube": "segredo-youtube"}})
    assert response.status_code == 503
    assert "segredo-youtube" not in response.text
    assert await db_session.get(RadarSettings, "admin-a") is None
