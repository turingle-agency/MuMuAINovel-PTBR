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
        settings=_settings(fallback_api_provider="gemini", fallback_api_key="k", fallback_llm_model="gemini-image"),
        prompt="x", codex_error=_Quota("limite"),
    )
    assert r["provider"] == "gemini" and chamado == {"key": "k", "model": "gemini-image"}


async def test_capa_nunca_passa_flag_m(monkeypatch, tmp_path):
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "image")
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    r = await CodexCoverProvider(FAKE, 5).generate_cover(**{**ARGS, "model": "gpt-image-1"})
    argv = args_file.read_text().split("\n")
    assert "-m" not in argv and "gpt-image-1" not in argv
    assert r["model"] == "codex"


async def test_capa_comando_isolado_e_com_geracao_de_imagem(monkeypatch, tmp_path):
    from app.services.ai_providers.codex_provider import ISOLATION_FLAGS
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "image")
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    await CodexCoverProvider(FAKE, 5).generate_cover(**ARGS)
    argv = args_file.read_text().split("\n")
    assert argv[:5] == ["exec", "--enable", "image_generation", "-s", "workspace-write"]
    assert argv[5:5 + len(ISOLATION_FLAGS)] == ISOLATION_FLAGS
    assert "image_generation" not in ISOLATION_FLAGS


async def test_reserva_de_capa_com_modelo_de_texto_da_503_pt_br():
    with pytest.raises(HTTPException) as ei:
        await CoverGenerationService()._generate_with_fallback(
            settings=_settings(fallback_api_provider="gemini", fallback_api_key="k", fallback_llm_model="gemini-2.5-pro"),
            prompt="x", codex_error=_Quota("limite"),
        )
    assert ei.value.status_code == 503
    assert "cota esgotada" in ei.value.detail and "não parece gerar imagens" in ei.value.detail


async def test_reserva_de_capa_com_provedor_sem_imagem_da_503_pt_br():
    with pytest.raises(HTTPException) as ei:
        await CoverGenerationService()._generate_with_fallback(
            settings=_settings(fallback_api_provider="openai", fallback_api_key="k", fallback_llm_model="gpt-4o"),
            prompt="x", codex_error=_Quota("limite"),
        )
    assert ei.value.status_code == 503 and "não gera imagens" in ei.value.detail


async def test_reserva_de_capa_que_falha_da_503_pt_br(monkeypatch):
    import httpx

    class Quebrada(BaseCoverProvider):
        def __init__(self, api_key, base_url):
            pass

        async def generate_cover(self, *, prompt, model, width, height):
            req = httpx.Request("POST", "https://x")
            raise httpx.HTTPStatusError("Unauthorized", request=req, response=httpx.Response(401, request=req))

    monkeypatch.setattr("app.services.cover_generation_service.GeminiCoverProvider", Quebrada)
    with pytest.raises(HTTPException) as ei:
        await CoverGenerationService()._generate_with_fallback(
            settings=_settings(fallback_api_provider="gemini", fallback_api_key="k", fallback_llm_model="gemini-2.5-flash-image"),
            prompt="x", codex_error=_Quota("limite"),
        )
    assert ei.value.status_code == 503
    assert "reserva também falhou (chave inválida (401))" in ei.value.detail
