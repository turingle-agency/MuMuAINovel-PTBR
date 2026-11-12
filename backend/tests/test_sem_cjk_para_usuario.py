"""Garante que nenhuma string visível ao usuário ou à IA contenha CJK."""
import ast
import re
from pathlib import Path

import pytest

CJK = re.compile(r"[　-〿㐀-䶿一-鿿＀-￯]")
APP = Path(__file__).resolve().parent.parent / "app"

# Compatibilidade com dados antigos (Task 6): chaves/padrões ficam em chinês.
_ALLOWED_ASSIGN = {
    ("character_state_update_service.py", "INTIMACY_ADJUSTMENTS"),
    ("txt_parser_service.py", "HEADING_PATTERNS"),
}


def _is_log_call(node: ast.Call) -> bool:
    f = node.func
    return (
        isinstance(f, ast.Attribute)
        and isinstance(f.value, ast.Name)
        and f.value.id in {"logger", "logging", "log"}
    )


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Strings soltas como instrução (docstrings ou blocos de texto sem efeito)."""
    return {
        id(n.value)
        for n in ast.walk(tree)
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
    }


def find_cjk_user_strings(root: Path) -> list[tuple[str, int, str]]:
    """Retorna (arquivo, linha, texto) de strings com CJK que chegam ao usuário/IA."""
    root = Path(root)
    out: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        skip = _docstring_nodes(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and _is_log_call(n):
                for sub in ast.walk(n):
                    skip.add(id(sub))
            targets = []
            if isinstance(n, ast.Assign):
                targets = [t for t in n.targets if isinstance(t, ast.Name)]
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                targets = [n.target]
            for t in targets:
                if (path.name, t.id) in _ALLOWED_ASSIGN and n.value is not None:
                    for sub in ast.walk(n.value):
                        skip.add(id(sub))
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                if id(n) in skip or not CJK.search(n.value):
                    continue
                out.append((str(path), n.lineno, n.value))
    return out


def _fmt(found):
    return f"{len(found)} strings\n" + "\n".join(
        f"{f}:{l}: {s[:60]!r}" for f, l, s in found[:50]
    )


def test_nenhuma_string_cjk_para_usuario_api():
    found = find_cjk_user_strings(APP / "api")
    assert found == [], _fmt(found)


@pytest.mark.xfail(reason="Task 11b", strict=False)
def test_nenhuma_string_cjk_para_usuario():
    found = find_cjk_user_strings(APP)
    assert found == [], _fmt(found)
