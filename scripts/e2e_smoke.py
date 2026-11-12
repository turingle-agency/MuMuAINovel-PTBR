#!/usr/bin/env python3
"""Roteiro de fumaça ponta a ponta contra o backend em execução (equivale ao roteiro manual da UI).

Uso (com o backend em http://localhost:8000):
  python scripts/e2e_smoke.py main         # Codex real: projeto es-MX, capítulo 1, memórias, capa
  python scripts/e2e_smoke.py codex-fail   # backend iniciado com CODEX_BINARY inválido: erro/reserva em PT-BR

Credenciais: LOCAL_AUTH_USERNAME / LOCAL_AUTH_PASSWORD de backend/.env (nunca são impressas).
Faz poucas chamadas reais ao Codex. Requer httpx (já está em backend/requirements.txt).
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx

ENV = Path(__file__).resolve().parent.parent / "backend" / ".env"
ES = [" el ", " los ", " las ", " del ", " una ", " y ", " que ", " por "]
PT = [" não ", " uma ", " os ", " do ", " da ", " é ", " e ", "ção", " com "]
CJK = re.compile(r"[　-ヿ一-鿿]")
ok_all = True


def check(name: str, cond: bool, detail: str = "") -> None:
    global ok_all
    ok_all &= bool(cond)
    print(f"[{'OK' if cond else 'FALHA'}] {name}" + (f" -- {detail}" if detail else ""))


def env_value(key: str) -> str:
    for line in ENV.read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return ""


def lang_score(text: str) -> tuple[int, int]:
    t = " " + text.lower().replace("\n", " ") + " "
    return sum(t.count(w) for w in ES), sum(t.count(w) for w in PT)


def sse(client: httpx.Client, path: str, body: dict, timeout: float = 900):
    """POST com resposta SSE; devolve a lista de eventos (dict)."""
    events = []
    with client.stream("POST", path, json=body, timeout=timeout) as r:
        if r.status_code != 200:
            return [{"type": "http_error", "status": r.status_code, "body": r.read().decode()[:500]}]
        for line in r.iter_lines():
            if line.startswith("data: "):
                try:
                    events.append(json.loads(line[6:]))
                except ValueError:
                    pass
    return events


def result_of(events):
    return next((e.get("data") for e in events if e.get("type") == "result"), None)


def error_of(events):
    for e in events:
        if e.get("type") == "error":
            return e.get("error") or e.get("message") or json.dumps(e, ensure_ascii=False)
        if e.get("type") == "http_error":
            return f"HTTP {e['status']}: {e['body']}"
    return None


def set_settings(c: httpx.Client, **kw) -> None:
    body = {"api_provider": "codex", "llm_model": "", "temperature": 0.7, "max_tokens": 8000,
            "cover_api_provider": "codex", "cover_enabled": True, **kw}
    r = c.post("/api/settings", json=body)
    check("salvar configurações", r.status_code == 200, f"{r.status_code} provider={r.json().get('api_provider')}")


def login(c: httpx.Client) -> None:
    r = c.post("/api/auth/local/login", json={
        "username": env_value("LOCAL_AUTH_USERNAME"), "password": env_value("LOCAL_AUTH_PASSWORD")})
    check("login local", r.status_code == 200, str(r.status_code))
    if r.status_code != 200:
        sys.exit(1)


def make_chapter(c: httpx.Client, pid: str, n: int, title: str, resumo: str) -> str:
    o = c.post("/api/outlines", json={"project_id": pid, "title": title, "content": resumo, "order_index": n})
    check(f"criar esboço {n}", o.status_code == 200, str(o.status_code))
    ch = c.post("/api/chapters", json={"project_id": pid, "title": title, "chapter_number": n,
                                       "outline_id": o.json().get("id"), "summary": resumo})
    check(f"criar capítulo {n}", ch.status_code == 200, str(ch.status_code))
    return ch.json()["id"]


def gen_chapter(c, cid: str, words: int):
    t0 = time.time()
    events = sse(c, f"/api/chapters/{cid}/generate-stream", {"target_word_count": words, "enable_mcp": False})
    return events, time.time() - t0


def phase_main(c: httpx.Client) -> None:
    # 2. Configurações: Codex + reserva deliberadamente inválida
    set_settings(c, fallback_api_provider="openai", fallback_api_key="sk-invalido-e2e",
                 fallback_llm_model="gpt-4o-mini")

    # 3. Projeto es-MX pelo assistente (1 chamada ao Codex)
    events = sse(c, "/api/wizard-stream/world-building", {
        "title": "El faro de Veracruz", "description": "Una guardiana de faro descubre un secreto.",
        "theme": "memoria y perdón", "genre": "misterio", "narrative_perspective": "terceira pessoa",
        "target_words": 20000, "chapter_count": 5, "character_count": 3, "language": "es-MX",
        "enable_mcp": False})
    res = result_of(events)
    check("mundo gerado via SSE", res is not None, error_of(events) or "")
    if not res:
        return
    pid = res["project_id"]
    proj = c.get(f"/api/projects/{pid}").json()
    check("Project.language == es-MX", proj.get("language") == "es-MX", str(proj.get("language")))
    world = " ".join(str(res.get(k, "")) for k in ("time_period", "location", "atmosphere", "rules"))
    es, pt = lang_score(world)
    check("mundo em espanhol", es > pt and not CJK.search(world), f"marcadores es={es} pt={pt}")
    print("  trecho:", world[:160].replace("\n", " "))

    # 4. Capítulo 1 (1 geração + análise)
    cid = make_chapter(c, pid, 1, "El faro", "La guardiana encuentra una carta antigua en la torre del faro.")
    events, secs = gen_chapter(c, cid, 600)
    err = error_of(events)
    ch = c.get(f"/api/chapters/{cid}").json()
    wc = ch.get("word_count") or 0
    check("capítulo 1 gerado pelo Codex", not err and wc > 0, err or f"{wc} palavras em {secs:.0f}s")
    check("palavras próximas da meta (600, faixa 300-1200)", 300 <= wc <= 1200, str(wc))
    es, pt = lang_score(ch.get("content") or "")
    check("capítulo em espanhol", es > pt, f"es={es} pt={pt}")

    stats = {}
    for _ in range(60):  # a análise roda em segundo plano
        st = c.get(f"/api/chapters/{cid}/analysis/status").json()
        if st.get("status") in ("completed", "failed"):
            break
        time.sleep(5)
    check("análise do capítulo concluída", st.get("status") == "completed", json.dumps(st, ensure_ascii=False)[:200])
    stats = c.get(f"/api/memories/projects/{pid}/stats").json()
    check("memórias gravadas no Qdrant embutido", ((stats.get("stats") or stats).get("total_count") or 0) > 0, json.dumps(stats)[:200])

    # 5. Capa via Codex
    t0 = time.time()
    r = c.post(f"/api/projects/{pid}/cover/generate", json={"overwrite": True}, timeout=900)
    check("capa gerada pelo Codex", r.status_code == 200, f"{r.status_code} {r.text[:200]} ({time.time() - t0:.0f}s)")
    if r.status_code == 200:
        d = c.get(f"/api/projects/{pid}/cover/download")
        check("download da capa (imagem)", d.status_code == 200 and d.content[:8] == b"\x89PNG\r\n\x1a\n",
              f"{d.status_code} {d.headers.get('content-type')} {len(d.content)} bytes")
    Path("/tmp/e2e_project_id").write_text(pid)


def phase_fail(c: httpx.Client) -> None:
    pid = Path("/tmp/e2e_project_id").read_text().strip()
    cid = make_chapter(c, pid, 2, "La carta", "La guardiana lee la carta y viaja al puerto.")
    pt_msg = re.compile(r"(Codex|reserva|configur|conex|falh|indispon)", re.I)

    for label, kw in (("com reserva inválida", dict(fallback_api_provider="openai", fallback_api_key="sk-invalido-e2e",
                                                      fallback_llm_model="gpt-4o-mini")),
                      ("sem reserva", dict(fallback_api_provider=None, fallback_api_key=None, fallback_llm_model=None))):
        set_settings(c, **kw)
        events, _ = gen_chapter(c, cid, 500)
        err = error_of(events) or ""
        if kw.get("fallback_api_provider"):
            # A reserva (chave inválida de propósito) assume: o erro vem dela, não do "Codex não respondeu".
            # Obs.: a mensagem da API de reserva chega como veio do provedor (hoje em inglês).
            check("capítulo, Codex indisponível, com reserva inválida: reserva acionada",
                  bool(err) and "O Codex não respondeu" not in err and "401" in err, err[:200])
        else:
            check("capítulo, Codex indisponível, sem reserva: erro claro em PT-BR",
                  bool(pt_msg.search(err)) and "Traceback" not in err and not CJK.search(err), err[:300])
        r = c.post(f"/api/projects/{pid}/cover/generate", json={"overwrite": True}, timeout=300)
        det = r.text
        check(f"capa, Codex indisponível, {label}: erro claro em PT-BR", r.status_code >= 400 and bool(pt_msg.search(det))
              and "Traceback" not in det and not CJK.search(det), f"{r.status_code} {det[:300]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["main", "codex-fail"])
    ap.add_argument("--base", default="http://localhost:8000")
    a = ap.parse_args()
    with httpx.Client(base_url=a.base, timeout=60) as c:
        login(c)
        (phase_main if a.phase == "main" else phase_fail)(c)
    print("RESULTADO:", "tudo OK" if ok_all else "HÁ FALHAS")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
