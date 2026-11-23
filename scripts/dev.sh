#!/usr/bin/env bash
# Sobe o ambiente de desenvolvimento local: backend (SQLite + Qdrant embutido) e frontend (Vite).
# Uso: scripts/dev.sh        (Ctrl+C encerra os dois processos)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
MODEL_DIR="$BACKEND/embedding/onnx/paraphrase-multilingual-MiniLM-L12-v2"

die() { echo "Erro: $*" >&2; exit 1; }

command -v uv >/dev/null 2>&1 || die "uv não encontrado. Instale em https://docs.astral.sh/uv/"
command -v npm >/dev/null 2>&1 || die "npm não encontrado. Instale o Node.js 20 ou superior."

# .env do backend
if [ ! -f "$BACKEND/.env" ]; then
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  echo "Criado backend/.env a partir de .env.example. Ajuste LOCAL_AUTH_USERNAME e LOCAL_AUTH_PASSWORD."
fi

# Ambiente Python
if [ ! -d "$BACKEND/.venv" ]; then
  uv venv --python 3.12 "$BACKEND/.venv"
  uv pip install --python "$BACKEND/.venv/bin/python" -r "$BACKEND/requirements.txt"
fi

# Modelo de embedding (baixa só se faltar)
if [ ! -f "$MODEL_DIR/model.onnx" ]; then
  bash "$BACKEND/scripts/download_embedding_model.sh"
fi

# Dependências do frontend
if [ ! -d "$FRONTEND/node_modules" ]; then
  (cd "$FRONTEND" && npm install)
fi

# Banco local: SQLite, salvo se o .env ou o ambiente já definir DATABASE_URL
if [ -z "${DATABASE_URL:-}" ] && ! grep -Eq '^DATABASE_URL=' "$BACKEND/.env"; then
  export DATABASE_URL="sqlite+aiosqlite:///./data/app.db"
fi
# Em http://localhost o cookie de sessão não pode ser Secure (o Safari o descartaria)
export SESSION_COOKIE_SECURE="${SESSION_COOKIE_SECURE:-false}"
mkdir -p "$BACKEND/data"

cd "$BACKEND"
# shellcheck disable=SC1091
source .venv/bin/activate

case "${DATABASE_URL:-$(grep -E '^DATABASE_URL=' .env | head -1 | cut -d= -f2-)}" in
  sqlite*) ALEMBIC_INI="alembic-sqlite.ini" ;;
  *)       ALEMBIC_INI="alembic-postgres.ini" ;;
esac
alembic -c "$ALEMBIC_INI" upgrade head

uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

cd "$FRONTEND"
echo "Backend: http://localhost:8000   Frontend: http://localhost:5173"
npm run dev
