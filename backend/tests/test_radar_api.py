from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.database import NicheResearch, Offer, Project
from app.schemas.radar import ResearchInput, ResearchSnapshot, SourceResult
from app.services.radar_repository import enqueue_research
from tests.test_radar_settings import logar, radar_client

BASE = "/api/radar/researches"


def pedido(topic="Pães da serra", country="BR"):
    return {"topic": topic, "country": country, "product_type": "lowticket", "request_id": str(uuid4())}


async def registrar(client, **kwargs):
    response = await client.post(BASE, json=pedido(**kwargs))
    assert response.status_code == 202
    return response.json()["id"]


async def fechar(db, pesquisa, status="partial", evidence=True):
    row = await db.get(NicheResearch, pesquisa)
    snapshot = ResearchSnapshot.model_validate(row.signals)
    if evidence:
        snapshot.sources["firecrawl"] = SourceResult.model_validate({
            "source": "firecrawl", "status": "ok", "scope": "BR", "method_version": "1",
            "collected_at": "2026-11-23T10:00:00Z",
            "items": [{"id": "1", "kind": "content", "url": "https://example.org/texto", "label": "Texto"}],
        })
    row.signals = snapshot.model_dump(mode="json")
    row.status = status
    row.finished_at = datetime(2026, 11, 23, 10)
    await db.commit()


@pytest.mark.asyncio
async def test_search_accepts_valid_request_and_returns_202_without_collecting(radar_client):
    logar(radar_client)
    for payload in (pedido("   "), pedido(country="US"), pedido("a" * 301)):
        assert (await radar_client.post(BASE, json=payload)).status_code == 422
    response = await radar_client.post(BASE, json=pedido())
    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    research = (await radar_client.get(f"{BASE}/{response.json()['id']}")).json()
    assert research["snapshot"]["input"]["query"] == "Pães da serra"
    assert research["snapshot"]["sources"] == {}


@pytest.mark.asyncio
async def test_manual_retry_preserves_snapshot_and_conflict_is_409(radar_client):
    logar(radar_client)
    payload = pedido()
    first = await radar_client.post(BASE, json=payload)
    profiles = (await radar_client.get("/api/radar/settings")).json()["profiles"]
    profiles[0]["active"] = False
    profiles[0]["language"] = "fr-FR"
    saved = await radar_client.put("/api/radar/settings", json={"profiles": profiles})
    assert saved.status_code == 200
    repeated = await radar_client.post(BASE, json=payload)
    assert repeated.status_code == 202
    assert repeated.json()["id"] == first.json()["id"]
    research = (await radar_client.get(f"{BASE}/{repeated.json()['id']}")).json()
    assert research["snapshot"]["input"]["language"] == "pt-BR"
    conflict = await radar_client.post(BASE, json={**payload, "topic": "Tema diferente"})
    assert conflict.status_code == 409
    changed_confirmation = await radar_client.post(BASE, json={**payload, "budget_confirmation": True})
    assert changed_confirmation.status_code == 409


@pytest.mark.asyncio
async def test_latest_with_filters_and_distinct_history(radar_client, db_session):
    logar(radar_client)
    first = await registrar(radar_client)
    latest = await registrar(radar_client, topic="PÃES DA SERRA")
    older, newer = [await db_session.get(NicheResearch, id_) for id_ in (first, latest)]
    older.created_at = datetime(2026, 11, 21)
    newer.created_at = datetime(2026, 11, 22)
    await db_session.commit()
    results = (await radar_client.get(BASE, params={"country": "BR", "mode": "manual"})).json()
    assert [row["id"] for row in results["items"]] == [latest]
    assert results["total"] == 1
    paged = (await radar_client.get(f"{BASE}/{first}/history", params={"page_size": 1, "page": 2})).json()
    assert (paged["total"], paged["page_size"], paged["page"]) == (2, 1, 2)
    assert [row["id"] for row in paged["items"]] == [first]
    assert (await radar_client.get(BASE, params={"country": "PT"})).json()["total"] == 0
    assert (await radar_client.get(BASE, params={"page_size": 101})).status_code == 422


@pytest.mark.asyncio
async def test_weekly_researches_order_scored_rows_before_unscored(radar_client, db_session):
    logar(radar_client)
    for topic, score in [("Abacate", None), ("Zimbro", 65), ("Canela", 65), ("Banana", 73)]:
        row = await enqueue_research(db_session, "admin-a", ResearchInput(
            topic=topic, country="BR", product_type="fiction", mode="weekly",
            input_key="2026-W48", week_key="2026-W48", snapshot=ResearchSnapshot(score={"score": score}),
        ))
        row.status = "complete" if score is not None else "partial"
        row.score = score
    await db_session.commit()
    result = (await radar_client.get(BASE, params={"week_key": "2026-W48"})).json()
    assert [(row["topic"], row["score"]) for row in result["items"]] == [
        ("Banana", 73), ("Canela", 65), ("Zimbro", 65), ("Abacate", None),
    ]


@pytest.mark.asyncio
async def test_foreign_admin_ids_are_404(radar_client, db_session):
    logar(radar_client)
    id_ = await registrar(radar_client)
    await fechar(db_session, id_)
    brief = (await radar_client.post(f"{BASE}/{id_}/brief")).json()["id"]
    logar(radar_client, "admin-b")
    for path in (f"{BASE}/{id_}", f"{BASE}/{id_}/history", f"/api/radar/briefs/{brief}"):
        assert (await radar_client.get(path)).status_code == 404
    assert (await radar_client.post(f"{BASE}/{id_}/brief")).status_code == 404
    assert (await radar_client.get("/api/radar/briefs")).json()["total"] == 0


@pytest.mark.asyncio
async def test_brief_creation_201_then_200_and_returns_same_full_snapshot(radar_client, db_session):
    logar(radar_client)
    older = await registrar(radar_client)
    await fechar(db_session, older)
    created = await radar_client.post(f"{BASE}/{older}/brief")
    assert created.status_code == 201
    newer = await registrar(radar_client)
    replay = await radar_client.post(f"{BASE}/{older}/brief")
    assert replay.status_code == 200
    assert replay.json() == created.json()
    data = created.json()
    assert data["research"]["id"] == older != newer
    assert data["research"]["snapshot"]["sources"]["firecrawl"]["items"][0]["id"] == "1"
    brief = data["id"]
    assert (await radar_client.get(f"/api/radar/briefs/{brief}")).json() == data
    assert (await radar_client.get("/api/radar/briefs")).json()["total"] == 1
    assert await db_session.scalar(select(func.count()).select_from(Project)) == 0
    assert await db_session.scalar(select(func.count()).select_from(Offer)) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(("status", "evidence"), [("running", True), ("partial", False), ("failed", False)])
async def test_ineligible_brief_returns_409(radar_client, db_session, status, evidence):
    logar(radar_client)
    id_ = await registrar(radar_client)
    await fechar(db_session, id_, status=status, evidence=evidence)
    assert (await radar_client.post(f"{BASE}/{id_}/brief")).status_code == 409


@pytest.mark.asyncio
async def test_legacy_research_remains_readable_without_comparable_score(radar_client, db_session):
    logar(radar_client)
    db_session.add(NicheResearch(id="legada", user_id="admin-a", topic="Tema antigo", score=90,
                                 status="complete", signals={"token": "segredo legado"}))
    await db_session.commit()
    response = await radar_client.get(f"{BASE}/legada")
    data = response.json()
    assert data["legacy"] is True and data["topic"] == "Tema antigo"
    assert data["score"] is None and data["snapshot"] is None
    assert "segredo legado" not in response.text
    assert (await radar_client.post(f"{BASE}/legada/brief")).status_code == 409
