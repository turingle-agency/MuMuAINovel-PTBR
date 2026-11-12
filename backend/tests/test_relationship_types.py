from app.database import Base  # noqa: F401  (importar antes de app.models evita o ciclo)
import re

from app.init_relationship_types import RELATIONSHIP_TYPES
from app.prompts import characters

CJK = re.compile(r"[一-鿿]")
LISTING = re.compile(r"Um dos tipos permitidos \(copie o nome exato\): ([^\"]+)\"")
SEEDED = {rt["name"] for rt in RELATIONSHIP_TYPES}


def test_semente_sem_chines():
    for rt in RELATIONSHIP_TYPES:
        assert not CJK.search("".join(str(v) for v in rt.values())), rt


def test_nomes_listados_nos_prompts_existem_na_semente():
    prompts = [
        characters.CHARACTERS_BATCH_GENERATION,
        characters.SINGLE_CHARACTER_GENERATION,
        characters.AUTO_CHARACTER_ANALYSIS,
        characters.AUTO_CHARACTER_GENERATION,
    ]
    for prompt in prompts:
        listings = LISTING.findall(prompt)
        assert listings, "prompt sem lista de tipos de relação"
        for listing in listings:
            names = {n.strip() for n in listing.split(",")}
            assert names == SEEDED


def test_migracao_igual_a_semente():
    import importlib.util
    from pathlib import Path

    path = next(
        (Path(__file__).parent.parent / "alembic" / "sqlite" / "versions").glob("*_seed_ptbr.py")
    )
    spec = importlib.util.spec_from_file_location("seed_ptbr", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    migrated = {v[0]: (v[1], v[2]) for v in mod.RELATIONSHIP_TYPES_PTBR.values()}
    seeded = {rt["name"]: (rt["reverse_name"], rt["description"]) for rt in RELATIONSHIP_TYPES}
    assert migrated == seeded
