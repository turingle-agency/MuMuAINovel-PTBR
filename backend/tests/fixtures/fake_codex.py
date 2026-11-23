#!/usr/bin/env python3
"""Substituto do binário `codex` para testes. Comportamento via FAKE_CODEX_MODE."""
import os
import sys
import time

args = sys.argv[1:]
stdin_data = sys.stdin.read()

stdin_file = os.environ.get("FAKE_CODEX_STDIN_FILE")
if stdin_file:
    with open(stdin_file, "w", encoding="utf-8") as f:
        f.write(stdin_data)

args_file = os.environ.get("FAKE_CODEX_ARGS_FILE")
if args_file:
    with open(args_file, "w", encoding="utf-8") as f:
        f.write("\n".join(args))

mode = os.environ.get("FAKE_CODEX_MODE", "ok")
out_file = args[args.index("-o") + 1] if "-o" in args else None

if mode == "ok":
    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("resposta falsa")
    sys.exit(0)
if mode == "quota":
    print("You've hit your usage limit", file=sys.stderr)
    sys.exit(1)
if mode == "auth":
    print("Not logged in")
    sys.exit(1)
if mode == "hang":
    time.sleep(60)
    sys.exit(0)
if mode == "image":
    import base64
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    chdir = args[args.index("-C") + 1] if "-C" in args else "."
    with open(os.path.join(chdir, "cover.png"), "wb") as f:
        f.write(png)
    if out_file:
        with open(out_file, "wb") as f:
            f.write(png)
    sys.exit(0)
print("erro desconhecido", file=sys.stderr)
sys.exit(2)
