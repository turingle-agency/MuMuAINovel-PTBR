"""O teste de conexão deve funcionar para o provider codex (sem chave nem modelo)."""
import pytest

from app.api import settings as settings_api
from app.schemas.settings import APIKeyPresetConfig


def test_api_test_request_aceita_codex_sem_chave_e_modelo():
    req = settings_api.ApiTestRequest(provider="codex")
    assert req.api_key == ""
    assert req.llm_model == ""


def test_preset_config_aceita_codex_sem_chave_e_modelo():
    cfg = APIKeyPresetConfig(api_provider="codex")
    assert cfg.api_key == ""
    assert cfg.llm_model == ""


@pytest.mark.asyncio
async def test_test_api_connection_codex_com_valores_vazios(monkeypatch):
    capturado = {}

    class FakeAIService:
        def __init__(self, **kwargs):
            capturado.update(kwargs)

        async def generate_text(self, **kwargs):
            capturado["generate"] = kwargs
            return "teste bem-sucedido"

    monkeypatch.setattr(settings_api, "AIService", FakeAIService)
    result = await settings_api.test_api_connection(
        settings_api.ApiTestRequest(provider="codex", api_key="", llm_model="")
    )
    assert result["success"] is True
    assert capturado["api_provider"] == "codex"
    assert capturado["default_model"] == ""
