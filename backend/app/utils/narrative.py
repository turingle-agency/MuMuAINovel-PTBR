"""Perspectiva narrativa: normaliza o valor guardado no projeto para o texto usado nos prompts.

Valores novos são guardados em português ("primeira pessoa", "terceira pessoa",
"onisciente"). Projetos antigos podem ter valores chineses vindos do frontend
original ('第一人称', '第三人称', '全知视角') ou os identificadores em inglês
(first_person/third_person/omniscient); todos são mapeados para o texto PT.
"""
from typing import Optional

PRIMEIRA_PESSOA = "primeira pessoa"
TERCEIRA_PESSOA = "terceira pessoa"
ONISCIENTE = "onisciente"

# Valores aceitos pelo frontend/novos projetos (os que passam a ser gravados).
NARRATIVE_PERSPECTIVES_PT = (PRIMEIRA_PESSOA, TERCEIRA_PESSOA, ONISCIENTE)

# Chaves já em minúsculas e sem espaços extras. Os valores chineses são o legado.
_CJK_COMPAT_PERSPECTIVE_ALIASES = {
    "第一人称": PRIMEIRA_PESSOA,
    "第一人称视角": PRIMEIRA_PESSOA,
    "第三人称": TERCEIRA_PESSOA,
    "第三人称视角": TERCEIRA_PESSOA,
    "全知视角": ONISCIENTE,
    "全知": ONISCIENTE,
}
_ALIASES = {
    "first_person": PRIMEIRA_PESSOA,
    "first person": PRIMEIRA_PESSOA,
    "primeira pessoa": PRIMEIRA_PESSOA,
    "third_person": TERCEIRA_PESSOA,
    "third person": TERCEIRA_PESSOA,
    "terceira pessoa": TERCEIRA_PESSOA,
    "omniscient": ONISCIENTE,
    "onisciente": ONISCIENTE,
}


def narrative_perspective_pt(value: Optional[str], default: str = TERCEIRA_PESSOA) -> str:
    """Devolve o texto PT da perspectiva narrativa (valores desconhecidos passam como estão)."""
    text = (value or "").strip()
    if not text:
        return default
    key = text.lower()
    return _ALIASES.get(key) or _CJK_COMPAT_PERSPECTIVE_ALIASES.get(text) or text
