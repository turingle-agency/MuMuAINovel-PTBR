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
    "INSPIRATION_TITLE_SYSTEM",
    "INSPIRATION_TITLE_USER",
    "INSPIRATION_DESCRIPTION_SYSTEM",
    "INSPIRATION_DESCRIPTION_USER",
    "INSPIRATION_THEME_SYSTEM",
    "INSPIRATION_THEME_USER",
    "INSPIRATION_GENRE_SYSTEM",
    "INSPIRATION_GENRE_USER",
    "INSPIRATION_QUICK_COMPLETE",
    "BOOK_IMPORT_REVERSE_PROJECT_SUGGESTION",
    "BOOK_IMPORT_REVERSE_OUTLINES",
    "NOVEL_COVER_PROMPT_TEMPLATE",
    "MCP_TOOL_TEST",
    "MCP_TOOL_TEST_SYSTEM",
]

# Instruções técnicas de teste de plugin: não geram conteúdo literário, não precisam de idioma
SEM_IDIOMA = {"MCP_TOOL_TEST", "MCP_TOOL_TEST_SYSTEM"}
COM_IDIOMA = [k for k in TRANSLATED if k not in SEM_IDIOMA]


def _fields(template: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(template) if f}


def test_fixture_cobre_os_36_templates():
    assert len(ORIGINAL) == 36
    assert set(TRANSLATED) == set(ORIGINAL)


def test_catalogo_de_templates_todo_em_pt_br():
    for info in PromptService.get_all_system_templates():
        texto = info["template_name"] + info["description"] + info["category"]
        assert not CJK.search(texto), info["template_key"]


def test_prompt_de_capa_nao_pede_texto_na_imagem():
    rendered = PromptService.format_prompt(
        PromptService.NOVEL_COVER_PROMPT_TEMPLATE,
        title="T", genre="fantasia", theme="x", description="y",
    )
    assert "NÃO inclua nenhum texto" in rendered


@pytest.mark.asyncio
async def test_prompt_de_capa_usa_idioma_do_projeto():
    from types import SimpleNamespace

    project = SimpleNamespace(title="T", genre="romance", theme="x", description="y", language="en-US")
    prompt = await PromptService.build_novel_cover_prompt(project)
    assert "inglês (Estados Unidos)" in prompt
    assert not CJK.search(prompt)


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_sem_cjk(key):
    assert not CJK.search(getattr(PromptService, key))


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_mantem_placeholders(key):
    assert _fields(getattr(PromptService, key)) - {"output_language"} == set(ORIGINAL[key])


@pytest.mark.parametrize("key", COM_IDIOMA)
def test_template_exige_idioma(key):
    assert "{output_language}" in getattr(PromptService, key)


@pytest.mark.parametrize("key", TRANSLATED)
def test_template_formata_com_todos_os_parametros(key):
    params = {name: "X" for name in ORIGINAL[key]}
    rendered = PromptService.format_prompt(
        getattr(PromptService, key), output_language="inglês (Estados Unidos)", **params
    )
    assert "{output_language}" not in rendered
    if key not in SEM_IDIOMA:
        assert "inglês (Estados Unidos)" in rendered


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


def test_importacao_aceita_ponto_de_vista_em_portugues():
    import app.database  # noqa: F401  (evita import circular dos modelos)
    from app.services.book_import_service import BookImportService

    service = BookImportService.__new__(BookImportService)
    assert service._normalize_narrative_perspective("primeira pessoa") == "primeira pessoa"
    assert service._normalize_narrative_perspective("Terceira pessoa") == "terceira pessoa"
    assert service._normalize_narrative_perspective("onisciente") == "onisciente"
    # valores antigos (chinês) e em inglês continuam aceitos e viram texto PT
    assert service._normalize_narrative_perspective("第一人称") == "primeira pessoa"
    assert service._normalize_narrative_perspective("全知视角") == "onisciente"
    assert service._normalize_narrative_perspective("third_person") == "terceira pessoa"


def test_prompt_de_inspiracao_aplica_idioma_padrao():
    rendered = PromptService.format_prompt(PromptService.INSPIRATION_TITLE_SYSTEM, initial_idea="um dragão")
    assert "português do Brasil" in rendered
    assert '"options"' in rendered
