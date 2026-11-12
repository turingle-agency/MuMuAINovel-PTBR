"""Provider de capas via Codex CLI (`codex exec --enable image_generation`).

Spike (Codex real, 2026-11-12): rodando o comando abaixo em um diretório novo,
o Codex gerou a imagem com a skill `imagegen` (que a grava em
~/.codex/generated_images/<thread>/...png) e depois a COPIOU/redimensionou para
`<-C dir>/cover.png` (PNG 1600x2560, ~6 MB, ~1-2 min). O JSONL de `--json` cita
o caminho `<-C dir>/cover.png` na mensagem final e nos comandos. Portanto basta
procurar a imagem mais nova dentro do diretório temporário; não é preciso ler
nada em ~/.codex.

    codex exec --enable image_generation -s workspace-write -C <dir> \\
        --skip-git-repo-check --ephemeral -o <dir>/last.txt -
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import settings as app_settings
from app.services.ai_providers.codex_provider import (
    CodexError,
    _get_semaphore,
    run_codex_process,
)
from app.services.cover_providers.base_cover_provider import BaseCoverProvider, CoverGenerationResult

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class CodexImageUnavailableError(CodexError):
    """O Codex terminou sem gerar nenhum arquivo de imagem."""


class CodexCoverProvider(BaseCoverProvider):
    def __init__(self, binary: str, timeout_s: int):
        self.binary = binary
        self.timeout_s = timeout_s

    async def generate_cover(
        self,
        *,
        prompt: str,
        model: str,
        width: int,
        height: int,
    ) -> CoverGenerationResult:
        stdin_text = (
            f"{prompt}\n\n"
            f"Gere uma imagem de capa de livro de {width}x{height} pixels, sem nenhum texto, "
            "letras ou marca d'água, e salve como cover.png no diretório atual."
        )
        async with _get_semaphore(app_settings.codex_max_concurrency):
            with tempfile.TemporaryDirectory(prefix="codex_cover_") as tmp:
                cmd = [
                    self.binary, "exec", "--enable", "image_generation", "-s", "workspace-write",
                    "-C", tmp, "--skip-git-repo-check", "--ephemeral",
                    "-o", str(Path(tmp) / "last.txt"),
                ]
                # Nunca passa -m: cover_image_model é nome de modelo de imagem de outro provider.
                cmd.append("-")

                await run_codex_process(cmd, stdin_text, self.timeout_s, self.binary)

                imagens = [
                    p for p in Path(tmp).iterdir()
                    if p.is_file() and p.suffix.lower() in _MIME
                ]
                if not imagens:
                    raise CodexImageUnavailableError("o Codex não gerou nenhuma imagem")
                imagem = max(imagens, key=lambda p: p.stat().st_mtime)
                content = imagem.read_bytes()
                suffix = imagem.suffix.lower()

        return {
            "content": content,
            "mime_type": _MIME[suffix],
            "file_extension": suffix.lstrip(".").replace("jpeg", "jpg"),
            "revised_prompt": None,
            "provider": "codex",
            "model": "codex",
        }
