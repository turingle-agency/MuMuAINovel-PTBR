from pathlib import Path

import pytest

from app.services.ai_providers.codex_provider import (
    CodexAuthError,
    CodexExecError,
    CodexProvider,
    CodexQuotaError,
    CodexTimeoutError,
)

FAKE = str(Path(__file__).parent / "fixtures" / "fake_codex.py")

ARGS = dict(prompt="oi", model="", temperature=0.7, max_tokens=100, system_prompt="sys")


async def test_codex_ok(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    r = await CodexProvider(FAKE, 5, 2).generate(**ARGS)
    assert r["content"] == "resposta falsa"
    assert r["tool_calls"] is None
    assert r["finish_reason"] == "stop"
    assert r["usage"] == {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}


async def test_codex_quota(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "quota")
    with pytest.raises(CodexQuotaError):
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)


async def test_codex_auth(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "auth")
    with pytest.raises(CodexAuthError):
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)


async def test_codex_erro_generico(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "outro")
    with pytest.raises(CodexExecError):
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)


async def test_codex_timeout(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "hang")
    with pytest.raises(CodexTimeoutError):
        await CodexProvider(FAKE, 1, 2).generate(**ARGS)


async def test_codex_prompt_vai_no_stdin(monkeypatch, tmp_path):
    stdin_file = tmp_path / "stdin.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    monkeypatch.setenv("FAKE_CODEX_STDIN_FILE", str(stdin_file))
    await CodexProvider(FAKE, 5, 2).generate(**ARGS)
    recebido = stdin_file.read_text(encoding="utf-8")
    assert "sys\n\n---\n\noi" in recebido
    assert recebido.endswith("Responda apenas com o conteúdo solicitado. Não execute comandos nem use ferramentas.")


async def test_codex_comando_exato(monkeypatch, tmp_path):
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    await CodexProvider(FAKE, 5, 2).generate(**{**ARGS, "model": "gpt-x"})
    args = args_file.read_text(encoding="utf-8").split("\n")
    assert args[:6] == ["exec", "--json", "--ephemeral", "--skip-git-repo-check", "-s", "read-only"]
    assert args[6] == "-C" and args[8] == "-o" and args[9].endswith("last.txt")
    assert args[-3:] == ["-m", "gpt-x", "-"]


async def test_codex_stream_entrega_tudo_de_uma_vez(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    chunks = [c async for c in CodexProvider(FAKE, 5, 2).generate_stream(**ARGS)]
    assert chunks == ["resposta falsa"]


@pytest.mark.parametrize("modelo,passa", [("", False), ("gpt-4", False), ("gpt-5-codex", True)])
async def test_codex_ignora_modelo_padrao_de_outro_provider(monkeypatch, tmp_path, modelo, passa):
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    await CodexProvider(FAKE, 5, 2).generate(**{**ARGS, "model": modelo})
    assert ("-m" in args_file.read_text().split("\n")) is passa


async def test_codex_ignora_default_model_das_configuracoes(monkeypatch, tmp_path):
    from app.config import settings as app_settings
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    monkeypatch.setattr(app_settings, "default_model", "meu-modelo-padrao")
    await CodexProvider(FAKE, 5, 2).generate(**{**ARGS, "model": "meu-modelo-padrao"})
    assert "-m" not in args_file.read_text().split("\n")
