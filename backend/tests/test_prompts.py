import json
import re
import string
from pathlib import Path

import pytest

from app.services.prompt_service import PromptService

CJK = re.compile(r"[一-鿿]")
ORIGINAL = json.loads(
    (Path(__file__).parent / "fixtures" / "original_placeholders.json").read_text(encoding="utf-8")
)

TRANSLATED = [
    "WORLD_BUILDING",
    "CAREER_SYSTEM_GENERATION",
    "MCP_WORLD_BUILDING_PLANNING",
    "CHARACTERS_BATCH_GENERATION",
    "SINGLE_CHARACTER_GENERATION",
    "SINGLE_ORGANIZATION_GENERATION",
    "AUTO_CHARACTER_ANALYSIS",
    "AUTO_CHARACTER_GENERATION",
    "AUTO_ORGANIZATION_ANALYSIS",
    "AUTO_ORGANIZATION_GENERATION",
    "MCP_CHARACTER_PLANNING",
    "OUTLINE_CREATE",
    "OUTLINE_CONTINUE",
    "CHAPTER_GENERATION_ONE_TO_MANY",
    "CHAPTER_GENERATION_ONE_TO_ONE",
    "CHAPTER_GENERATION_ONE_TO_ONE_NEXT",
    "CHAPTER_GENERATION_ONE_TO_MANY_NEXT",
    "CHAPTER_REGENERATION_SYSTEM",
    "PARTIAL_REGENERATE",
    "PLOT_ANALYSIS",
    "OUTLINE_EXPAND_SINGLE",
    "OUTLINE_EXPAND_MULTI",
]


def _fields(template: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(template) if f}


def test_fixture_cobre_os_36_templates():
    assert len(ORIGINAL) == 36
    assert set(TRANSLATED) <= set(ORIGINAL)


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_sem_cjk(key):
    assert not CJK.search(getattr(PromptService, key))


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_mantem_placeholders(key):
    assert _fields(getattr(PromptService, key)) - {"output_language"} == set(ORIGINAL[key])


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_exige_idioma(key):
    assert "{output_language}" in getattr(PromptService, key)


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_formata_com_todos_os_parametros(key):
    params = {name: "X" for name in ORIGINAL[key]}
    rendered = PromptService.format_prompt(
        getattr(PromptService, key), output_language="inglês (Estados Unidos)", **params
    )
    assert "inglês (Estados Unidos)" in rendered
    assert "{output_language}" not in rendered


def test_templates_traduzidos_estao_no_catalogo():
    keys = {t["template_key"]: t for t in PromptService.get_all_system_templates()}
    for key in TRANSLATED:
        info = keys[key]
        assert not CJK.search(info["template_name"] + info["description"] + info["category"])


def test_format_ignora_extras_e_aplica_idioma():
    assert PromptService.format_prompt("A {x} em {output_language}", x=1, extra=2) == "A 1 em português do Brasil"


def test_template_personalizado_antigo_sem_idioma_nao_quebra():
    assert PromptService.format_prompt("模板 {title}", title="X", output_language="inglês (Estados Unidos)") == "模板 X"


def test_format_param_ausente():
    with pytest.raises(ValueError, match="Parâmetro obrigatório ausente: title"):
        PromptService.format_prompt("{title}")


def test_plot_analysis_pede_intimacy_delta():
    assert '"intimacy_delta"' in PromptService.PLOT_ANALYSIS
    assert '"change"' in PromptService.PLOT_ANALYSIS


@pytest.mark.asyncio
async def test_prompt_de_reescrita_usa_idioma_e_palavras():
    prompt = await PromptService.get_chapter_regeneration_prompt(
        chapter_number=1, title="T", word_count=1234, content="texto",
        modification_instructions="melhorar", project_context={"output_language": "inglês (Estados Unidos)"},
        style_content="", target_word_count=2000,
    )
    assert "inglês (Estados Unidos)" in prompt
    assert "{output_language}" not in prompt
    assert "1234 palavras" in prompt and "2000 palavras" in prompt
