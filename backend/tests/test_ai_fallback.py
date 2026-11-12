from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services.ai_providers.base_provider import BaseAIProvider
from app.services.ai_providers.codex_provider import CodexProvider
from app.services.ai_service import AIService, FallbackConfig

FAKE = str(Path(__file__).parent / "fixtures" / "fake_codex.py")


class StubApi(BaseAIProvider):
    def __init__(self):
        self.models = []

    async def generate(self, prompt, model, temperature, max_tokens, system_prompt=None, tools=None, tool_choice=None):
        self.models.append(model)
        return {"content": "da api", "tool_calls": None, "finish_reason": "stop", "usage": {}}

    async def generate_stream(self, prompt, model, temperature, max_tokens, system_prompt=None,
                              tools=None, tool_choice=None, user_id=None):
        self.models.append(model)
        yield "da api"


def _servico(monkeypatch, modo, com_fallback=True):
    monkeypatch.setenv("FAKE_CODEX_MODE", modo)
    fb = FallbackConfig("openai", "k", None, "gpt-x") if com_fallback else None
    svc = AIService(api_provider="codex", default_model="", enable_mcp=False, fallback=fb)
    svc._codex_provider = CodexProvider(FAKE, 5, 2)
    stub = StubApi()
    if fb:
        svc._fallback_service._openai_provider = stub
    return svc, stub


async def test_fallback_quando_cota_acaba(monkeypatch):
    svc, stub = _servico(monkeypatch, "quota")
    r = await svc.generate_text(prompt="oi")
    assert r["content"] == "da api"
    assert stub.models == ["gpt-x"]


async def test_fallback_quando_codex_trava(monkeypatch):
    svc, _ = _servico(monkeypatch, "hang")
    svc._codex_provider = CodexProvider(FAKE, 1, 2)
    assert (await svc.generate_text(prompt="oi"))["content"] == "da api"


async def test_codex_ok_nao_aciona_reserva(monkeypatch):
    svc, stub = _servico(monkeypatch, "ok")
    assert (await svc.generate_text(prompt="oi"))["content"] == "resposta falsa"
    assert stub.models == []


@pytest.mark.parametrize("modo,motivo", [
    ("quota", "cota esgotada"),
    ("auth", "não logado"),
    ("outro", "erro de execução"),
])
async def test_sem_fallback_erro_claro(monkeypatch, modo, motivo):
    svc, _ = _servico(monkeypatch, modo, com_fallback=False)
    with pytest.raises(HTTPException) as e:
        await svc.generate_text(prompt="oi")
    assert e.value.status_code == 503
    assert motivo in e.value.detail
    assert "Configure uma API de reserva em Configurações." in e.value.detail


async def test_sem_fallback_timeout(monkeypatch):
    svc, _ = _servico(monkeypatch, "hang", com_fallback=False)
    svc._codex_provider = CodexProvider(FAKE, 1, 2)
    with pytest.raises(HTTPException) as e:
        await svc.generate_text(prompt="oi")
    assert "tempo esgotado" in e.value.detail


async def test_stream_com_fallback(monkeypatch):
    svc, stub = _servico(monkeypatch, "quota")
    chunks = [c async for c in svc.generate_text_stream(prompt="oi")]
    assert "".join(chunks) == "da api"
    assert stub.models == ["gpt-x"]


async def test_stream_sem_fallback_erro_claro(monkeypatch):
    svc, _ = _servico(monkeypatch, "auth", com_fallback=False)
    with pytest.raises(HTTPException) as e:
        _ = [c async for c in svc.generate_text_stream(prompt="oi")]
    assert e.value.status_code == 503 and "não logado" in e.value.detail


async def test_str_do_erro_e_so_o_detalhe_pt_br(monkeypatch):
    # handlers SSE usam str(e): não pode virar "503: ..."
    svc, _ = _servico(monkeypatch, "quota", com_fallback=False)
    with pytest.raises(HTTPException) as e:
        await svc.generate_text(prompt="oi")
    assert str(e.value) == e.value.detail
    assert str(e.value).startswith("O Codex não respondeu (cota esgotada)")


async def test_sse_generator_envia_detalhe_pt_br(monkeypatch):
    from app.utils.sse_response import create_sse_generator

    svc, _ = _servico(monkeypatch, "quota", com_fallback=False)
    saidas = [x async for x in create_sse_generator(svc.generate_text_stream(prompt="oi"))]
    texto = "".join(saidas)
    assert "O Codex não respondeu (cota esgotada)" in texto and "503:" not in texto


async def test_lote_nao_espera_codex_de_novo_apos_timeout(monkeypatch, tmp_path):
    import time
    svc, stub = _servico(monkeypatch, "hang")
    svc._codex_provider = CodexProvider(FAKE, 1, 2)
    await svc.generate_text(prompt="1")
    t = time.monotonic()
    for i in range(3):
        assert (await svc.generate_text(prompt=str(i)))["content"] == "da api"
    assert time.monotonic() - t < 1  # nenhuma nova espera de timeout
    assert len(stub.models) == 4


async def test_cooldown_sem_reserva_da_503_pt_br(monkeypatch):
    svc, _ = _servico(monkeypatch, "quota", com_fallback=False)
    for _ in range(2):
        with pytest.raises(HTTPException) as e:
            await svc.generate_text(prompt="oi")
        assert e.value.status_code == 503 and "cota esgotada" in e.value.detail
