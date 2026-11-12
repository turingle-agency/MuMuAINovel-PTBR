#!/usr/bin/env bash
# Baixa o modelo de embedding ONNX (paraphrase-multilingual-MiniLM-L12-v2) e valida os sha256.
# Mesmas URLs, revisão e hashes do Dockerfile. Uso: backend/scripts/download_embedding_model.sh [destino]
set -euo pipefail

REVISION="${EMBEDDING_MODEL_REVISION:-60750e200f336606cdd1ecbda9bb33fbf4d5b2a1}"
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$BACKEND_DIR/embedding/onnx/paraphrase-multilingual-MiniLM-L12-v2}"
URL="https://modelscope.cn/models/mumujie/paraphrase-multilingual-MiniLM-L12-v2-ONNX/resolve/${REVISION}"

if command -v sha256sum >/dev/null 2>&1; then
  sha256() { sha256sum "$1" | cut -d' ' -f1; }
else
  sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }
fi

mkdir -p "$DEST"

fetch() {
  local name="$1" expected="$2" target="$DEST/$1"
  if [ -f "$target" ] && [ "$(sha256 "$target")" = "$expected" ]; then
    echo "OK (já existe): $name"
    return
  fi
  curl --fail --location --retry 5 --retry-all-errors "$URL/$name" -o "$target"
  local actual
  actual="$(sha256 "$target")"
  if [ "$actual" != "$expected" ]; then
    echo "sha256 inválido em $name: esperado $expected, obtido $actual" >&2
    rm -f "$target"
    exit 1
  fi
  echo "OK: $name"
}

fetch model.onnx e7515ed8b2f63e84f99dfed652b572e61a9a799f694a1c9399a7f3845b69cda5
fetch tokenizer.json 2c3387be76557bd40970cec13153b3bbf80407865484b209e655e5e4729076b8
fetch embedding_config.json d9cfbb22ea59e66294db9bd5b35b452326658a2fe1580e409f0c806be01973c2

echo "Modelo pronto em: $DEST"
