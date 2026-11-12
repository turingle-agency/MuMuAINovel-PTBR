"""Provider Codex: executa a CLI oficial `codex exec` (sem tocar em credenciais)."""
import asyncio
import tempfile
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.config import settings as app_settings
from app.logger import get_logger
from .base_provider import BaseAIProvider

logger = get_logger(__name__)

SUFIXO_PROMPT = "Responda apenas com o conteúdo solicitado. Não execute comandos nem use ferramentas."


class CodexError(Exception):
    """Falha ao usar o Codex."""


class CodexQuotaError(CodexError):
    """Cota/limite de uso esgotado."""


class CodexAuthError(CodexError):
    """Codex não está logado."""


class CodexTimeoutError(CodexError):
    """Codex excedeu o tempo limite."""


class CodexExecError(CodexError):
    """Qualquer outra falha de execução."""


class CodexCooldownError(CodexError):
    """Codex em período de espera após uma falha recente (cota/login/tempo esgotado)."""

    def __init__(self, reason: str, restante_s: int):
        super().__init__(f"em espera por {restante_s}s após falha recente ({reason})")
        self.reason = reason
        self.restante_s = restante_s


# Isolamento do Codex em chamadas do app: sem config do usuário (MCPs pessoais, hooks,
# instruções), sem regras de execpolicy, sem memórias/plugins/apps e sem docs de projeto.
# `--ignore-user-config` mantém a autenticação (CODEX_HOME). Limitação conhecida: o
# AGENTS.md global do usuário em CODEX_HOME não tem flag para ser desligado.
ISOLATION_FLAGS: List[str] = [
    "--ignore-user-config",
    "--ignore-rules",
    "--disable", "hooks",
    "--disable", "memories",
    "--disable", "plugins",
    "--disable", "apps",
    "-c", "mcp_servers={}",
    "-c", "project_doc_max_bytes=0",
]


# Memória de falhas do Codex (por processo): evita esperar N x timeout num lote.
_cooldown_until: float = 0.0
_cooldown_reason: str = ""


def reset_codex_cooldown() -> None:
    global _cooldown_until, _cooldown_reason
    _cooldown_until = 0.0
    _cooldown_reason = ""


def _check_cooldown() -> None:
    restante = _cooldown_until - time.monotonic()
    if restante > 0:
        raise CodexCooldownError(_cooldown_reason, int(restante) + 1)


def _register_failure(error: CodexError) -> None:
    global _cooldown_until, _cooldown_reason
    cooldown = int(app_settings.codex_failure_cooldown_s)
    if isinstance(error, (CodexQuotaError, CodexAuthError, CodexTimeoutError)) and cooldown > 0:
        _cooldown_until = time.monotonic() + cooldown
        _cooldown_reason = codex_reason(error)


# Modelos padrão de outros providers que podem ter ficado salvos em llm_model.
_MODELOS_NAO_CODEX = {"", "gpt-4"}


_semaphore: Optional[asyncio.Semaphore] = None
_semaphore_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_semaphore(max_concurrency: int) -> asyncio.Semaphore:
    """Semáforo único do processo (recriado só se o event loop mudar, p.ex. em testes)."""
    global _semaphore, _semaphore_loop
    loop = asyncio.get_running_loop()
    if _semaphore is None or _semaphore_loop is not loop:
        _semaphore = asyncio.Semaphore(max(1, max_concurrency))
        _semaphore_loop = loop
    return _semaphore


def classify_failure(output: str) -> CodexError:
    texto = output.lower()
    resumo = output.strip()[-500:]
    if any(s in texto for s in ("usage limit", "rate limit", "quota")):
        return CodexQuotaError(resumo)
    if any(s in texto for s in ("not logged in", "login", "unauthorized")):
        return CodexAuthError(resumo)
    return CodexExecError(resumo)


async def run_codex_process(cmd: List[str], stdin_text: str, timeout_s: int, binary: str) -> str:
    """Executa o subprocesso do Codex, mata-o em timeout/cancelamento e classifica falhas.

    Devolve a saída combinada (stdout+stderr); levanta CodexError se o código de saída != 0.
    O chamador deve segurar o semáforo compartilhado (`_get_semaphore`).
    Falhas de cota/login/timeout abrem um período de espera (`codex_failure_cooldown_s`)
    em que novas chamadas falham de imediato com `CodexCooldownError`.
    """
    _check_cooldown()
    try:
        return await _run_codex_process(cmd, stdin_text, timeout_s, binary)
    except CodexError as e:
        _register_failure(e)
        raise


async def _run_codex_process(cmd: List[str], stdin_text: str, timeout_s: int, binary: str) -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as e:
        raise CodexExecError(f"não foi possível executar '{binary}': {e}") from e

    try:
        out, _ = await asyncio.wait_for(
            proc.communicate(stdin_text.encode("utf-8")), timeout=timeout_s
        )
    except asyncio.TimeoutError as e:
        proc.kill()
        await proc.wait()
        raise CodexTimeoutError(f"excedeu {timeout_s}s") from e
    except asyncio.CancelledError:
        proc.kill()
        await proc.wait()
        raise

    saida = out.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise classify_failure(saida)
    return saida


def codex_reason(error: CodexError) -> str:
    if isinstance(error, CodexCooldownError):
        return error.reason
    if isinstance(error, CodexQuotaError):
        return "cota esgotada"
    if isinstance(error, CodexAuthError):
        return "não logado"
    if isinstance(error, CodexTimeoutError):
        return "tempo esgotado"
    return "erro de execução"


def api_failure_reason(error: BaseException) -> str:
    """Motivo curto, em PT-BR, de uma falha da API de reserva (sem texto cru do provedor)."""
    import httpx

    status = None
    if isinstance(error, httpx.HTTPStatusError) and error.response is not None:
        status = error.response.status_code
    else:
        status = getattr(error, "status_code", None)
        if not isinstance(status, int):
            status = None
    if status in (401, 403):
        return f"chave inválida ({status})"
    if status == 402:
        return "sem créditos (402)"
    if status == 429:
        return "limite de uso ou sem créditos (429)"
    if status == 404:
        return "modelo ou endereço não encontrado (404)"
    if status in (400, 422):
        return f"requisição recusada pelo provedor ({status})"
    if status is not None and status >= 500:
        return f"erro do provedor ({status})"
    if status is not None:
        return f"erro do provedor ({status})"
    if isinstance(error, (httpx.TimeoutException, asyncio.TimeoutError, TimeoutError)):
        return "tempo esgotado"
    if isinstance(error, httpx.TransportError):
        return "sem conexão com o provedor"
    return "erro do provedor"


def fallback_failure_message(codex_error: CodexError, fallback_error: BaseException) -> str:
    return (
        f"O Codex não respondeu ({codex_reason(codex_error)}) e a API de reserva também falhou "
        f"({api_failure_reason(fallback_error)}). Verifique as configurações."
    )


class CodexProvider(BaseAIProvider):
    def __init__(self, binary: str, timeout_s: int, max_concurrency: int):
        self.binary = binary
        self.timeout_s = timeout_s
        self.max_concurrency = max_concurrency

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        if tools or tool_choice:
            logger.warning("Codex não suporta tools/MCP; parâmetros tools/tool_choice ignorados")

        stdin_text = f"{system_prompt or ''}\n\n---\n\n{prompt}\n\n{SUFIXO_PROMPT}"

        async with _get_semaphore(self.max_concurrency):
            with tempfile.TemporaryDirectory(prefix="codex_") as tmp:
                last = Path(tmp) / "last.txt"
                cmd = [
                    self.binary, "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                    "-s", "read-only", *ISOLATION_FLAGS, "-C", tmp, "-o", str(last),
                ]
                if model and model not in _MODELOS_NAO_CODEX and model != app_settings.default_model:
                    cmd += ["-m", model]
                cmd.append("-")

                await run_codex_process(cmd, stdin_text, self.timeout_s, self.binary)

                content = last.read_text(encoding="utf-8").strip() if last.exists() else ""
                if not content:
                    raise CodexExecError("o Codex terminou sem produzir resposta")

        return {
            "content": content,
            "tool_calls": None,
            "finish_reason": "stop",
            "usage": {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
        }

    async def generate_stream(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        result = await self.generate(
            prompt=prompt, model=model, temperature=temperature, max_tokens=max_tokens,
            system_prompt=system_prompt, tools=tools, tool_choice=tool_choice,
        )
        yield result["content"]
