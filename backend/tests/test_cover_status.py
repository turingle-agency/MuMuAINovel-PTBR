import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

import app.database  # noqa: F401
from app.models.project import Project
from app.models.settings import Settings
from app.services.cover_generation_service import (
    COVER_IN_PROGRESS_MESSAGE,
    CoverGenerationService,
    reset_interrupted_covers,
)
from app.services.cover_providers.base_cover_provider import BaseCoverProvider


async def _projeto(db, status="none"):
    p = Project(title="Livro", user_id="u1", cover_status=status)
    db.add(p)
    db.add(Settings(user_id="u1", cover_api_provider="codex", cover_enabled=True))
    await db.commit()
    return p


async def test_reinicio_redefine_capas_presas(db_session):
    a = await _projeto(db_session, "generating")
    b = Project(title="Outro", user_id="u1", cover_status="ready")
    db_session.add(b)
    await db_session.commit()
    assert await reset_interrupted_covers(db_session) == 1
    await db_session.commit()
    await db_session.refresh(a)
    await db_session.refresh(b)
    assert a.cover_status == "failed" and "gere novamente" in a.cover_error
    assert b.cover_status == "ready"


async def test_segunda_geracao_enquanto_gera_da_409_pt_br(db_session):
    p = await _projeto(db_session, "generating")
    with pytest.raises(HTTPException) as e:
        await CoverGenerationService().generate_cover(db=db_session, user_id="u1", project_id=p.id)
    assert e.value.status_code == 409 and e.value.detail == COVER_IN_PROGRESS_MESSAGE
    assert "em geração" in e.value.detail


async def test_cancelamento_nao_deixa_capa_gerando(db_session, monkeypatch):
    p = await _projeto(db_session)

    class Trava(BaseCoverProvider):
        async def generate_cover(self, **kw):
            await asyncio.sleep(30)

    svc = CoverGenerationService()
    monkeypatch.setattr(svc, "_build_provider", lambda s: Trava())

    async def prompt(*a, **k):
        return "prompt"

    monkeypatch.setattr("app.services.cover_generation_service.PromptService.build_novel_cover_prompt", prompt)
    task = asyncio.create_task(svc.generate_cover(db=db_session, user_id="u1", project_id=p.id))
    await asyncio.sleep(0.3)
    await db_session.refresh(p)
    assert p.cover_status == "generating"
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await db_session.refresh(p)
    assert p.cover_status == "failed" and "interrompida" in p.cover_error
