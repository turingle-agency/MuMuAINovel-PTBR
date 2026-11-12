"""Métricas de texto independentes de idioma (contagem de palavras e estimativa de tokens)."""
import re
from typing import Optional

# Cada caractere CJK (han, kana, hangul) conta como uma palavra.
_CJK_RE = re.compile(r"[一-鿿぀-ヿ가-힯]")
# Token: sequência \w+ que pode ter - ' ’ . , ENTRE letras/dígitos ("guarda-chuva", "19,90").
_WORD_RE = re.compile(r"\w+(?:[-'’.,]\w+)*")


def count_words(text: Optional[str]) -> int:
    """Conta palavras: caracteres CJK valem 1 cada; o resto conta tokens por regex."""
    if not text:
        return 0
    cjk_chars = len(_CJK_RE.findall(text))
    rest = _CJK_RE.sub(" ", text)
    return cjk_chars + len(_WORD_RE.findall(rest))


def estimate_max_tokens(target_words: int, floor: int = 2000, ceiling: int = 16000) -> int:
    """Estima max_tokens (~2 tokens por palavra) limitado ao intervalo [floor, ceiling]."""
    return max(floor, min(ceiling, int(target_words * 2)))
