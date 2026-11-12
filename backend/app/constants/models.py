"""Modelos de IA padrão: fonte única de verdade do backend.

Para atualizar os modelos, edite SOMENTE este arquivo (e o espelho no frontend,
frontend/src/constants/models.ts) e ajuste MODELS_CHECKED_AT para a data da conferência
na documentação oficial de cada provedor.
"""
from typing import Optional

MODELS_CHECKED_AT = "2026-11-12"

DEFAULT_TEXT_MODELS = {
    "openai": "gpt-6.1-terra",
    "anthropic": "claude-sonnet-5-5",
    "gemini": "gemini-3.8-flash",
}

DEFAULT_COVER_MODELS = {
    "gemini": "gemini-3.1-flash-image",
    "grok": "grok-imagine-image",
}

# Padrões antigos do upstream que ainda podem estar gravados na linha de configurações do usuário.
LEGACY_DEFAULT_MODELS = frozenset({"gpt-4", "gpt-4o-mini"})


def default_text_model(provider: Optional[str]) -> str:
    """Modelo de texto padrão do provedor; Codex usa o padrão da própria CLI ("")."""
    key = (provider or "").lower().strip()
    if key == "codex":
        return ""
    return DEFAULT_TEXT_MODELS.get(key, DEFAULT_TEXT_MODELS["openai"])
