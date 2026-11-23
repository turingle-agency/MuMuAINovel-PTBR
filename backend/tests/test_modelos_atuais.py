"""Garante que não restam IDs de modelos de IA desatualizados no código."""
import re
from pathlib import Path

import pytest

from app.constants.models import DEFAULT_TEXT_MODELS, LEGACY_DEFAULT_MODELS, default_text_model
from app.services.ai_service import AIService

RAIZ = Path(__file__).resolve().parents[2]
ESTE_ARQUIVO = Path(__file__).resolve()
CONSTANTES = (RAIZ / "backend/app/constants/models.py").resolve()

PADRAO_OBSOLETO = re.compile(
    r"gpt-3\.5|gpt-4\b|gpt-4o|gpt-4-turbo|gpt-image-1\b|dall-e|gemini-1\.|gemini-2\.0|gemini-2\.5"
    r"|claude-3|claude-(sonnet|opus|haiku)-4|grok-2-image"
)
ALVOS = ["backend/app", "frontend/src", "backend/.env.example", "docker-compose.yml", "README.md", "scripts"]
IGNORAR_PARTES = {"node_modules", "__pycache__", ".venv"}
EXTENSOES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".md", ".yml", ".yaml", ".example", ".sh", ".html", ".css", ".json"}


def _arquivos():
    for alvo in ALVOS:
        caminho = RAIZ / alvo
        candidatos = [caminho] if caminho.is_file() else caminho.rglob("*")
        for f in candidatos:
            if not f.is_file() or IGNORAR_PARTES & set(f.parts):
                continue
            if f.suffix not in EXTENSOES:
                continue
            if f.suffix == ".json" and "i18n" in f.parts:
                continue
            if f.resolve() in (ESTE_ARQUIVO, CONSTANTES):
                continue
            yield f


def test_sem_ids_de_modelo_desatualizados():
    achados = []
    for f in _arquivos():
        try:
            linhas = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for n, linha in enumerate(linhas, 1):
            if PADRAO_OBSOLETO.search(linha):
                achados.append(f"{f.relative_to(RAIZ)}:{n}: {linha.strip()[:120]}")
    assert not achados, "IDs de modelo desatualizados:\n" + "\n".join(achados)


@pytest.mark.parametrize("provider,esperado", [
    ("openai", "gpt-6.1-terra"),
    ("anthropic", "claude-sonnet-5-5"),
    ("gemini", "gemini-3.8-flash"),
    ("OpenAI ", "gpt-6.1-terra"),
    ("codex", ""),
    ("desconhecido", "gpt-6.1-terra"),
    (None, "gpt-6.1-terra"),
])
def test_default_text_model(provider, esperado):
    assert default_text_model(provider) == esperado


@pytest.mark.parametrize("armazenado", ["gpt-4", "gpt-4o-mini", "", None])
def test_ai_service_troca_modelo_legado_ou_vazio_pelo_padrao(armazenado):
    svc = AIService(api_provider="openai", api_key="k", default_model=armazenado)
    assert svc.default_model == DEFAULT_TEXT_MODELS["openai"]


def test_ai_service_usa_padrao_do_proprio_provider():
    assert AIService(api_provider="anthropic", api_key="k", default_model="gpt-4").default_model == "claude-sonnet-5-5"


def test_ai_service_mantem_modelo_personalizado_e_codex_vazio():
    assert AIService(api_provider="openai", api_key="k", default_model="meu-modelo").default_model == "meu-modelo"
    assert AIService(api_provider="codex", default_model="").default_model == ""


def test_legado_contem_antigos_padroes():
    assert {"gpt-4", "gpt-4o-mini"} <= LEGACY_DEFAULT_MODELS
