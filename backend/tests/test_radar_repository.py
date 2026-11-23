import asyncio
import os
from datetime import datetime
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.schemas.radar import PageFilters, ResearchFilters, ResearchInput, ResearchSnapshot
from app.services.radar_repository import (
    ResearchConflict, create_brief, enqueue_research, get_research, list_history,
    list_researches, normalize_topic,
)


def pedido(chave, tema="  Ｃafé   com Leite ", modo="manual", semana=None):
    return ResearchInput(
        topic=tema, country="BR", product_type="lowticket", mode=modo,
        input_key=chave, week_key=semana, snapshot=ResearchSnapshot(),
    )


async def gravar(maker, admin, entrada):
    async with maker.begin() as db:
        return await enqueue_research(db, admin, entrada)


@pytest.mark.asyncio
async def test_enqueue_is_idempotent_and_conflicts_on_changed_input(db_session):
    maker = async_sessionmaker(db_session.bind, expire_on_commit=False)
    uma, outra = await asyncio.gather(
        gravar(maker, "a", pedido("x")), gravar(maker, "a", pedido("x")),
    )
    assert uma.id == outra.id
    assert uma.topic_key == normalize_topic("café com leite") == "café com leite"
    with pytest.raises(ResearchConflict):
        await gravar(maker, "a", pedido("x", "Outro tema"))
    assert (await gravar(maker, "b", pedido("x"))).id != uma.id


@pytest.mark.asyncio
async def test_history_is_scoped_and_stably_paginated(db_session):
    maker = async_sessionmaker(db_session.bind, expire_on_commit=False)
    uma = await gravar(maker, "a", pedido("x"))
    outra = await gravar(maker, "a", pedido("y"))
    semanal = await gravar(maker, "a", pedido("w", modo="weekly", semana="2026-W48"))
    for id_, data in [(uma.id, 1), (outra.id, 1), (semanal.id, 2)]:
        linha = await get_research(db_session, "a", id_)
        linha.created_at = datetime(2026, 11, data)
    await db_session.commit()
    assert await get_research(db_session, "b", uma.id) is None
    assert (await list_researches(db_session, "b", ResearchFilters())).total == 0
    atual = await list_researches(db_session, "a", ResearchFilters())
    assert [r.id for r in atual.items] == [semanal.id]
    manual = await list_researches(db_session, "a", ResearchFilters(mode="manual"))
    assert [r.id for r in manual.items] == [max(uma.id, outra.id)]
    historico = await list_history(db_session, uma, PageFilters(page=2, page_size=1))
    assert historico.total == 3
    assert [r.id for r in historico.items] == [max(uma.id, outra.id)]


@pytest.mark.asyncio
async def test_brief_is_unique_and_keeps_original_snapshot(db_session):
    maker = async_sessionmaker(db_session.bind, expire_on_commit=False)
    antiga = await gravar(maker, "a", pedido("x"))

    async def criar():
        async with maker.begin() as db:
            return await create_brief(db, antiga)

    (um, criado_um), (outro, criado_outro) = await asyncio.gather(criar(), criar())
    nova = await gravar(maker, "a", pedido("y"))
    assert um.id == outro.id
    assert {criado_um, criado_outro} == {True, False}
    assert um.research_id == antiga.id != nova.id
    assert (await get_research(db_session, "a", um.research_id)).signals["version"] == 1


def test_sqlite_upgrade_preserves_legacy_row(tmp_path):
    arquivo = tmp_path / "legado.db"
    backend = Path(__file__).resolve().parents[1]
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{arquivo}"}

    def upgrade(revisao):
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic-sqlite.ini", "upgrade", revisao],
            cwd=backend, env=env, check=True, capture_output=True, text=True,
        )

    upgrade("20261112_fallback")
    with sqlite3.connect(arquivo) as db:
        db.execute(
            "INSERT INTO niche_researches (id, user_id, topic, status, signals) "
            "VALUES ('antiga', 'a', 'Tema', 'complete', '{\"legado\": true}')"
        )
    upgrade("20261123_radar")
    with sqlite3.connect(arquivo) as db:
        assert db.execute("SELECT topic, input_key, signals FROM niche_researches").fetchone() == (
            "Tema", None, '{"legado": true}',
        )
