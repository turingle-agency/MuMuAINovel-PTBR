"""Garante que o código não depende mais do projeto original (MuMuAINovel upstream)."""
import re
from pathlib import Path

import pytest

# `linuxdo_id` é o nome legado da coluna de id único em `users` (também usada por
# usuários locais); por isso só proibimos outras referências a LinuxDO.
UPSTREAM = re.compile(r"mumuverse|linux\.do|linuxdo(?!_id)|qq\.com|xiaomimimo|Asia/Shanghai", re.I)

APP_DIR = Path(__file__).resolve().parent.parent / "app"


def test_codigo_sem_referencias_upstream():
    hits = [
        str(p.relative_to(APP_DIR))
        for p in APP_DIR.rglob("*.py")
        if UPSTREAM.search(p.read_text(encoding="utf-8"))
    ]
    assert hits == []


@pytest.mark.skip(reason="habilitado na Task 8")
def test_rotas_removidas():
    from app.main import app

    paths = {r.path for r in app.routes}
    proibidos = ("/api/prompt-workshop", "/api/announcements", "/api/changelog", "/api/auth/linuxdo")
    assert not any(p.startswith(proibidos) for p in paths)
