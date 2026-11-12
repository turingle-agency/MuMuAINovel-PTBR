from pathlib import Path

import pytest

from app.services.ai_providers.codex_provider import CodexQuotaError
from app.services.cover_providers.codex_cover_provider import (
    CodexCoverProvider,
    CodexImageUnavailableError,
)

FAKE = str(Path(__file__).parent / "fixtures" / "fake_codex.py")
ARGS = dict(prompt="um farol", model="", width=1600, height=2560)


async def test_capa_imagem(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "image")
    r = await CodexCoverProvider(FAKE, 5).generate_cover(**ARGS)
    assert r["content"].startswith(b"\x89PNG")
    assert r["mime_type"] == "image/png"
    assert r["file_extension"] == "png"
    assert r["provider"] == "codex"


async def test_capa_sem_arquivo(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    with pytest.raises(CodexImageUnavailableError):
        await CodexCoverProvider(FAKE, 5).generate_cover(**ARGS)


async def test_capa_quota(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "quota")
    with pytest.raises(CodexQuotaError):
        await CodexCoverProvider(FAKE, 5).generate_cover(**ARGS)


# --- reserva no serviço de capa ---
from types import SimpleNamespace

from fastapi import HTTPException

from app.services.ai_providers.codex_provider import CodexQuotaError as _Quota
import app.database  # noqa: F401  (evita import circular de app.models)
from app.services.cover_generation_service import CoverGenerationService
from app.services.cover_providers.base_cover_provider import BaseCoverProvider


def _settings(**kw):
    base = dict(
        cover_api_provider="codex", cover_api_key=None, cover_image_model=None, cover_enabled=True,
        fallback_api_provider=None, fallback_api_key=None, fallback_api_base_url=None,
        fallback_llm_model=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_validacao_codex_nao_exige_chave():
    CoverGenerationService()._validate_cover_settings(_settings())


def test_build_provider_codex():
    p = CoverGenerationService()._build_provider_from_values(provider="codex", api_key="", api_base_url=None)
    assert isinstance(p, CodexCoverProvider)


async def test_sem_reserva_503():
    with pytest.raises(HTTPException) as ei:
        await CoverGenerationService()._generate_with_fallback(
            settings=_settings(), prompt="x", codex_error=_Quota("limite")
        )
    assert ei.value.status_code == 503
    assert ei.value.detail == "Não foi possível gerar a imagem pelo Codex: cota esgotada."


async def test_com_reserva_usa_gemini(monkeypatch):
    chamado = {}

    class FakeGemini(BaseCoverProvider):
        def __init__(self, api_key, base_url):
            chamado["key"] = api_key

        async def generate_cover(self, *, prompt, model, width, height):
            chamado["model"] = model
            return {"content": b"x", "mime_type": "image/png", "file_extension": "png",
                    "revised_prompt": None, "provider": "gemini", "model": model}

    monkeypatch.setattr("app.services.cover_generation_service.GeminiCoverProvider", FakeGemini)
    r = await CoverGenerationService()._generate_with_fallback(
        settings=_settings(fallback_api_provider="gemini", fallback_api_key="k", fallback_llm_model="img"),
        prompt="x", codex_error=_Quota("limite"),
    )
    assert r["provider"] == "gemini" and chamado == {"key": "k", "model": "img"}
