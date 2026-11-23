import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.database  # noqa: F401  (evita import circular dos modelos)
from app.services import skill_loader
from app.services.project_agent_extended_tools import EXTENDED_TOOL_SPECS
from app.services.project_agent_operational_tools import OPERATIONAL_TOOL_SPECS
from app.services.project_agent_service import SYSTEM_PROMPT
from app.services.project_agent_tools import ProjectAgentToolRegistry

CJK = re.compile(r"[一-鿿]")
SKILLS_DIR = Path(skill_loader.SKILLS_DIR).resolve()
ARQUIVOS = sorted(SKILLS_DIR.glob("*/SKILL.md")) + sorted(SKILLS_DIR.glob("*/references/*.md")) + [
    SKILLS_DIR / "README_HOW_TO_ADD_SKILL.md"
]


def test_ha_skills_para_testar():
    assert len(list(SKILLS_DIR.glob("*/SKILL.md"))) == 7
    assert len(ARQUIVOS) > 50


@pytest.mark.parametrize("path", ARQUIVOS, ids=lambda p: str(p.relative_to(SKILLS_DIR)))
def test_arquivo_de_skill_sem_cjk(path):
    assert not CJK.search(path.read_text(encoding="utf-8"))


def test_skills_mantem_nome_chave_e_carregam():
    skills = {s["name"]: s for s in skill_loader.load_skills()}
    assert set(skills) == {
        "story-deslop", "story-long-analyze", "story-long-scan", "story-long-write",
        "story-short-analyze", "story-short-scan", "story-short-write",
    }
    for name, skill in skills.items():
        assert skill["template_key"] == "SKILL_" + name.upper().replace("-", "_")
        for campo in ("template_name", "category", "description", "content"):
            assert skill[campo] and not CJK.search(skill[campo]), (name, campo)
        assert skill["triggers"][0] == f"/{name}"
        assert all(not CJK.search(t) for t in skill["triggers"])


def test_links_de_referencias_existem():
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        texto = skill_md.read_text(encoding="utf-8")
        for ref in re.findall(r"\(references/([\w\-]+\.md)", texto):
            assert (skill_md.parent / "references" / ref).exists(), (skill_md.parent.name, ref)


def test_get_skill_by_trigger_em_portugues():
    assert skill_loader.get_skill_by_trigger("/story-deslop")["name"] == "story-deslop"
    assert skill_loader.get_skill_by_trigger("esse texto está com tom de IA")["name"] == "story-deslop"
    assert skill_loader.get_skill_by_trigger("quero escrever conto")["name"] == "story-short-write"


def test_prompt_de_sistema_do_agente_em_pt_br():
    assert not CJK.search(SYSTEM_PROMPT)
    assert "Assistente de Criação" in SYSTEM_PROMPT


def test_descricoes_das_ferramentas_do_agente_em_pt_br():
    registry = ProjectAgentToolRegistry(SimpleNamespace(id="p1"), None)
    descricoes = [tool.description for tool in registry._tools.values()]
    descricoes += [spec["description"] for spec in EXTENDED_TOOL_SPECS + OPERATIONAL_TOOL_SPECS]
    assert len(descricoes) > 40
    for descricao in descricoes:
        assert not CJK.search(descricao), descricao
