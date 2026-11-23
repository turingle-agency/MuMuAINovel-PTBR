"""Constantes de categorias da oficina de prompts"""

PROMPT_CATEGORIES = {
    "general": "Geral",
    "fantasy": "Fantasia",
    "martial": "Artes marciais",
    "romance": "Romance",
    "scifi": "Ficção científica",
    "horror": "Suspense/Terror",
    "history": "Histórico",
    "urban": "Urbano",
    "game": "Games/eSports",
    "other": "Outros",
}

CATEGORY_LIST = [
    {"id": k, "name": v} for k, v in PROMPT_CATEGORIES.items()
]

# Tags populares (sugestões)
POPULAR_TAGS = [
    "fantasia", "fantasia épica", "sistema de poder", "progressão", "ação",
    "artes marciais", "época", "romance", "romance leve", "drama",
    "ficção científica", "interestelar", "pós-apocalíptico", "suspense", "investigação",
    "terror", "histórico", "mundo alternativo", "urbano", "corporativo",
    "games", "eSports", "anime", "novel leve", "sistema de jogo",
    "protagonista poderoso", "ritmo lento", "slice of life", "reconfortante"
]
