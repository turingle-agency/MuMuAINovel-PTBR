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


class FalhaApi(StubApi):
    def __init__(self, exc):
        super().__init__()
        self.exc = exc

    async def generate(self, *a, **k):
        raise self.exc

    async def generate_stream(self, *a, **k):
        raise self.exc
        yield  # pragma: no cover


def _http_status(code):
    import httpx
    req = httpx.Request("POST", "https://api.exemplo/v1")
    return httpx.HTTPStatusError("Client error 401 Unauthorized for url", request=req,
                                 response=httpx.Response(code, request=req, text="Incorrect API key"))


@pytest.mark.parametrize("exc,motivo", [
    (_http_status(401), "chave inválida (401)"),
    (_http_status(402), "sem créditos (402)"),
    (_http_status(429), "limite de uso ou sem créditos (429)"),
    (_http_status(503), "erro do provedor (503)"),
    (TimeoutError(), "tempo esgotado"),
    (RuntimeError("boom in english"), "erro do provedor"),
])
async def test_reserva_tambem_falha_da_503_pt_br(monkeypatch, exc, motivo):
    svc, _ = _servico(monkeypatch, "quota")
    svc._fallback_service._openai_provider = FalhaApi(exc)
    with pytest.raises(HTTPException) as e:
        await svc.generate_text(prompt="oi")
    assert e.value.status_code == 503
    d = e.value.detail
    assert d.startswith("O Codex não respondeu (cota esgotada) e a API de reserva também falhou (")
    assert motivo in d
    assert "Incorrect API key" not in d and "Unauthorized" not in d and "boom" not in d


async def test_stream_reserva_tambem_falha(monkeypatch):
    svc, _ = _servico(monkeypatch, "quota")
    svc._fallback_service._openai_provider = FalhaApi(_http_status(401))
    with pytest.raises(HTTPException) as e:
        _ = [c async for c in svc.generate_text_stream(prompt="oi")]
    assert e.value.status_code == 503 and "chave inválida (401)" in str(e.value)


TOOLS = [{"type": "function", "function": {"name": "t", "description": "d", "parameters": {"type": "object", "properties": {}}}}]


class RastreiaTools(StubApi):
    def __init__(self):
        super().__init__()
        self.tools_recebidas = []

    async def generate(self, prompt, model, temperature, max_tokens, system_prompt=None, tools=None, tool_choice=None):
        self.tools_recebidas.append(tools)
        return await super().generate(prompt, model, temperature, max_tokens, system_prompt, tools, tool_choice)


async def test_chamada_com_tools_vai_para_a_reserva_sem_tocar_no_codex(monkeypatch, tmp_path):
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    svc, _ = _servico(monkeypatch, "ok")
    stub = RastreiaTools()
    svc._fallback_service._openai_provider = stub
    r = await svc.generate_text(prompt="oi", tools=TOOLS, tool_choice="auto", auto_mcp=False, handle_tool_calls=False)
    assert r["content"] == "da api"
    assert stub.tools_recebidas == [TOOLS] and stub.models == ["gpt-x"]
    assert not args_file.exists()


async def test_chamada_com_tools_sem_reserva_da_erro_pt_br(monkeypatch):
    svc, _ = _servico(monkeypatch, "ok", com_fallback=False)
    with pytest.raises(HTTPException) as e:
        await svc.generate_text(prompt="oi", tools=TOOLS, auto_mcp=False)
    assert e.value.status_code == 503
    assert e.value.detail == ("O Assistente de Criação precisa de um provedor com suporte a ferramentas; "
                              "configure uma API de reserva em Configurações.")


async def test_geracao_comum_continua_no_codex(monkeypatch):
    svc, stub = _servico(monkeypatch, "ok")
    assert (await svc.generate_text(prompt="oi", auto_mcp=False))["content"] == "resposta falsa"
    assert stub.models == []


async def test_tools_vazias_nao_roteiam(monkeypatch):
    svc, stub = _servico(monkeypatch, "ok")
    assert (await svc.generate_text(prompt="oi", tools=[], auto_mcp=False))["content"] == "resposta falsa"


async def test_mcp_automatico_nao_e_carregado_com_codex(monkeypatch):
    svc, _ = _servico(monkeypatch, "ok")
    chamado = []

    async def prepara(*a, **k):
        chamado.append(1)
        return TOOLS

    svc._prepare_mcp_tools = prepara
    assert (await svc.generate_text(prompt="oi"))["content"] == "resposta falsa"
    assert [c async for c in svc.generate_text_stream(prompt="oi")] == ["resposta falsa"]
    assert chamado == []
