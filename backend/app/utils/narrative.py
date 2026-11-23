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


# Termos soltos (busca por substring) aceitos ao interpretar a resposta da IA ou dados antigos.
_CJK_COMPAT_PERSPECTIVE_HINTS = (
    (("第一人称", "第一视角", "主角视角", "我视角"), PRIMEIRA_PESSOA),
    (("第三人称", "第三视角", "旁观视角"), TERCEIRA_PESSOA),
    (("全知", "上帝视角"), ONISCIENTE),
)
_HINTS = (
    (("primeira pessoa", "first person", "first_person", "1st person"), PRIMEIRA_PESSOA),
    (("terceira pessoa", "third person", "third_person", "3rd person"), TERCEIRA_PESSOA),
    (("onisciente", "omniscient", "god view"), ONISCIENTE),
)


def parse_narrative_perspective(value: Optional[str]) -> Optional[str]:
    """Reconhece a perspectiva em PT/EN/CJK e devolve o texto PT canônico; None se não reconhecer."""
    text = (value or "").strip()
    if not text:
        return None
    key = text.lower()
    exact = _ALIASES.get(key) or _CJK_COMPAT_PERSPECTIVE_ALIASES.get(text)
    if exact:
        return exact
    for hints, canonical in _CJK_COMPAT_PERSPECTIVE_HINTS:
        if any(hint in text for hint in hints):
            return canonical
    spaced = key.replace("_", " ").replace("-", " ")
    for hints, canonical in _HINTS:
        if any(hint in spaced for hint in hints):
            return canonical
    return None


def narrative_perspective_pt(value: Optional[str], default: str = TERCEIRA_PESSOA) -> str:
    """Devolve o texto PT da perspectiva narrativa (valores desconhecidos passam como estão)."""
    text = (value or "").strip()
    if not text:
        return default
    return parse_narrative_perspective(text) or text
