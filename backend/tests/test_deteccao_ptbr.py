"""Detectores que rodam sobre texto importado/gerado agora reconhecem PT-BR (e mantêm CJK)."""
import pytest
from fastapi import HTTPException

import app.database  # noqa: F401  (resolve a ordem de import circular de app.models)

from app.security import validate_ai_http_url, validate_public_http_url
from app.services.book_import_service import BookImportService
from app.services.character_state_update_service import (
    CJK_COMPAT_LOYALTY_ADJUSTMENTS,
    _LOYALTY_PT_PATTERNS,
)
from app.services.plot_expansion_service import _infer_ending_type


def _service():
    return BookImportService.__new__(BookImportService)


def test_book_import_detecta_genero_pt_e_chines():
    s = _service()
    assert s._detect_genre_from_text("O detetive investigou o assassinato") == "Suspense"
    assert s._detect_genre_from_text("他在宗门修仙") == "Xianxia (cultivo)"
    assert s._detect_genre_from_text("texto neutro") == "Geral"


def test_book_import_prefixo_de_capitulo_pt_e_chines():
    s = _service()
    assert s._strip_chapter_prefix("Capítulo 3 - A fuga") == "A fuga"
    assert s._strip_chapter_prefix("第3章 逃亡") == "逃亡"


def test_book_import_perspectiva_guardada_em_pt():
    s = _service()
    assert s._detect_narrative_perspective("eu " * 40) == "primeira pessoa"
    assert s._detect_narrative_perspective("ele andou. ela riu. " * 30) == "terceira pessoa"
    assert s._normalize_narrative_perspective("全知视角") == "onisciente"


@pytest.mark.parametrize(
    "objetivo,esperado",
    [
        ("criar suspense sobre o segredo", "suspense"),
        ("aumentar o conflito entre os irmãos", "escalada de conflito"),
        ("uma grande reviravolta", "reviravolta"),
        ("fechamento emocional", "fechamento emocional"),
        ("悬念", "suspense"),
    ],
)
def test_plot_expansion_infere_tipo_de_final(objetivo, esperado):
    assert _infer_ending_type(objetivo.lower(), 0) == esperado
    assert _infer_ending_type("nada a ver", 2) == "transição natural-3"


def test_lealdade_reconhece_pt_e_chines():
    texto = "a lealdade aumenta depois do resgate"
    assert any(p.search(texto) for p, _ in _LOYALTY_PT_PATTERNS)
    assert "背叛" in CJK_COMPAT_LOYALTY_ADJUSTMENTS


def test_security_sugere_endpoint_privado_para_mensagem_traduzida():
    with pytest.raises(HTTPException) as direto:
        validate_public_http_url("http://127.0.0.1:8000")
    assert "rede interna" in direto.value.detail

    with pytest.raises(HTTPException) as ia:
        validate_ai_http_url("http://127.0.0.1:8000")
    assert "ALLOW_PRIVATE_AI_ENDPOINTS" in ia.value.detail
