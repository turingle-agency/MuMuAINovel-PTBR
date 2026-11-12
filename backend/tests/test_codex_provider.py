from pathlib import Path

import pytest

from app.services.ai_providers.codex_provider import (
    ISOLATION_FLAGS,
    CodexAuthError,
    CodexCooldownError,
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
    assert args[6:6 + len(ISOLATION_FLAGS)] == ISOLATION_FLAGS
    resto = args[6 + len(ISOLATION_FLAGS):]
    assert resto[0] == "-C" and resto[2] == "-o" and resto[3].endswith("last.txt")
    assert args[-3:] == ["-m", "gpt-x", "-"]


async def test_codex_stream_entrega_tudo_de_uma_vez(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    chunks = [c async for c in CodexProvider(FAKE, 5, 2).generate_stream(**ARGS)]
    assert chunks == ["resposta falsa"]


@pytest.mark.parametrize("modelo,passa", [("", False), ("gpt-4", False), ("gpt-6.1-terra", False), ("gpt-5-codex", True)])
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


def test_flags_de_isolamento_desligam_config_do_usuario():
    f = ISOLATION_FLAGS
    assert "--ignore-user-config" in f and "--ignore-rules" in f
    assert ["-c", "mcp_servers={}"] == f[f.index("mcp_servers={}") - 1: f.index("mcp_servers={}") + 1]
    for feat in ("hooks", "memories", "plugins", "apps"):
        assert f[f.index(feat) - 1] == "--disable"
    assert "--enable" not in f


async def test_cooldown_depois_de_cota_pula_o_codex(monkeypatch, tmp_path):
    args_file = tmp_path / "args.txt"
    monkeypatch.setenv("FAKE_CODEX_MODE", "quota")
    monkeypatch.setenv("FAKE_CODEX_ARGS_FILE", str(args_file))
    with pytest.raises(CodexQuotaError):
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)
    args_file.unlink()
    with pytest.raises(CodexCooldownError) as e:
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)
    assert not args_file.exists()  # o binário nem foi executado
    from app.services.ai_providers.codex_provider import codex_reason
    assert codex_reason(e.value) == "cota esgotada"


async def test_cooldown_depois_de_timeout_evita_novas_esperas(monkeypatch):
    import time
    monkeypatch.setenv("FAKE_CODEX_MODE", "hang")
    with pytest.raises(CodexTimeoutError):
        await CodexProvider(FAKE, 1, 2).generate(**ARGS)
    t = time.monotonic()
    with pytest.raises(CodexCooldownError):
        await CodexProvider(FAKE, 1, 2).generate(**ARGS)
    assert time.monotonic() - t < 0.5


async def test_erro_generico_nao_abre_cooldown(monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_MODE", "outro")
    with pytest.raises(CodexExecError):
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    assert (await CodexProvider(FAKE, 5, 2).generate(**ARGS))["content"] == "resposta falsa"


async def test_cooldown_desligado_com_zero(monkeypatch):
    from app.config import settings as app_settings
    monkeypatch.setattr(app_settings, "codex_failure_cooldown_s", 0)
    monkeypatch.setenv("FAKE_CODEX_MODE", "quota")
    for _ in range(2):
        with pytest.raises(CodexQuotaError):
            await CodexProvider(FAKE, 5, 2).generate(**ARGS)


async def test_cooldown_expira(monkeypatch):
    from app.services.ai_providers import codex_provider as cp
    monkeypatch.setenv("FAKE_CODEX_MODE", "quota")
    with pytest.raises(CodexQuotaError):
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)
    monkeypatch.setattr(cp, "_cooldown_until", 0.0)
    with pytest.raises(CodexQuotaError):  # voltou a chamar o binário
        await CodexProvider(FAKE, 5, 2).generate(**ARGS)
