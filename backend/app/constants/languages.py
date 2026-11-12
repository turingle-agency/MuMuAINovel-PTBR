"""Idiomas suportados para projetos (conteúdo gerado)."""

SUPPORTED_LANGUAGES: dict[str, str] = {
    "pt-BR": "português do Brasil",
    "en-US": "inglês (Estados Unidos)",
    "es-ES": "espanhol (Espanha)",
    "es-MX": "espanhol (México)",
}

DEFAULT_LANGUAGE = "pt-BR"


def language_name(code: str | None) -> str:
    """Nome por extenso do idioma; código desconhecido ou None cai no padrão."""
    return SUPPORTED_LANGUAGES.get(code or "", SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])
