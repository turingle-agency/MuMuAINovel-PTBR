# MuMuAINovel PT-BR

Fábrica de e-books em português: um assistente de escrita com IA que cria o mundo, os personagens, o esboço e os capítulos de um livro, mantém uma memória de longo prazo da história (busca semântica em Qdrant) e gera a capa. A interface é em português do Brasil, e o texto gerado sai no idioma de cada projeto (padrão `pt-BR`; também há `es-MX`, `en` e outros).

- Backend: FastAPI + SQLAlchemy (SQLite local ou PostgreSQL), Qdrant embutido ou em servidor.
- Frontend: React + Ant Design + Vite.
- IA: provider **Codex** (assinatura ChatGPT, pela CLI oficial `codex`), com **API de reserva** automática, além de OpenAI, Gemini, Anthropic e outros compatíveis.
- Licença: GPL v3.

Este repositório é um fork de [MuMuAINovel](https://github.com/xiamuceer-j/MuMuAINovel) (GPL v3), mantido de forma independente em [turingle-agency/MuMuAINovel-PTBR](https://github.com/turingle-agency/MuMuAINovel-PTBR).

## Requisitos

- Python 3.12 e [uv](https://docs.astral.sh/uv/)
- Node.js 20 ou superior
- Para usar o Codex: a [CLI do Codex](https://github.com/openai/codex) instalada e uma assinatura ChatGPT
- Opcional: Docker (PostgreSQL + Qdrant em servidor)

## Rodar localmente (macOS/Linux)

```bash
git clone git@github.com:turingle-agency/MuMuAINovel-PTBR.git
cd MuMuAINovel-PTBR

# 1. Modelo de embedding (ONNX, ~120 MB, baixado uma vez e validado por sha256)
bash backend/scripts/download_embedding_model.sh

# 2. Login do Codex (uma vez; o app só executa `codex exec` e nunca lê o seu token)
codex login

# 3. Configuração
cp backend/.env.example backend/.env
#    edite backend/.env: troque LOCAL_AUTH_USERNAME e LOCAL_AUTH_PASSWORD

# 4. Sobe backend e frontend
bash scripts/dev.sh
```

`scripts/dev.sh` cria o ambiente Python e instala as dependências do frontend se faltarem, aplica as migrações (SQLite em `backend/data/app.db`) e inicia:

- backend em <http://localhost:8000> (`uvicorn app.main:app --reload`), com o Qdrant embutido gravando em `backend/data/qdrant`;
- frontend em <http://localhost:5173> (o Vite repassa `/api` para a porta 8000). Abra este endereço e entre com o usuário e a senha do `.env`.

Ctrl+C encerra os dois.

## Configuração (`backend/.env`)

| Variável | Para que serve |
| --- | --- |
| `LOCAL_AUTH_USERNAME`, `LOCAL_AUTH_PASSWORD` | Login do administrador local |
| `DATABASE_URL` | Padrão do `dev.sh`: `sqlite+aiosqlite:///./data/app.db`. Para PostgreSQL: `postgresql+asyncpg://usuario:senha@host:5432/banco` |
| `DEFAULT_AI_PROVIDER` | `codex` (padrão deste fork), `openai`, `gemini`, `anthropic`... |
| `CODEX_BINARY`, `CODEX_TIMEOUT_S`, `CODEX_MAX_CONCURRENCY` | Caminho da CLI, tempo limite (600 s) e execuções simultâneas (2) |
| `CODEX_FAILURE_COOLDOWN_S` | Após cota esgotada, login expirado ou tempo limite, o app não chama o Codex por esse período (300 s; 0 desliga) e vai direto à API de reserva |
| `QDRANT_PATH` | Qdrant embutido (padrão `data/qdrant`) |
| `QDRANT_URL`, `QDRANT_API_KEY` | Se definida a URL, usa um servidor Qdrant no lugar do modo embutido |

### Codex e API de reserva

Em **Configurações**, escolha "Codex (assinatura ChatGPT)" como provider. Configure também a **API de reserva** (provider, chave e modelo): se o Codex falhar no meio de uma geração (cota esgotada, login expirado, tempo limite), a geração continua pela API de reserva sem perder o pedido. Sem reserva configurada, você recebe uma mensagem clara em português, sem stack trace. Capas também podem ser geradas pelo Codex; a reserva da capa é Gemini ou Grok com chave de API.

Os modelos de IA padrão ficam em `backend/app/constants/models.py` (e `frontend/src/constants/models.ts`), conferidos na documentação oficial em 12/11/2026; atualize esses arquivos quando surgirem modelos novos.

**Isolamento do Codex.** Cada chamada roda `codex exec` com `--ignore-user-config` (não carrega o seu `config.toml`: nada de MCPs pessoais, hooks ou instruções próprias; a autenticação continua valendo), `--ignore-rules`, `--disable hooks/memories/plugins/apps`, `-c mcp_servers={}` e `-c project_doc_max_bytes=0`, em um diretório temporário vazio. Limitação: não existe flag para ignorar o `AGENTS.md` global em `~/.codex`; se você mantém instruções pessoais ali, elas podem ser lidas pelo Codex. O Codex não suporta ferramentas/MCP: chamadas com ferramentas (Assistente de Criação) usam a API de reserva, e sem reserva retornam um erro claro.

O Gemini é usado só por chave de API, nunca pelo login da assinatura.

## Docker (PostgreSQL + Qdrant)

```bash
cp backend/.env.example .env
# edite .env: senhas do PostgreSQL, LOCAL_AUTH_*, chave de API do provider
docker compose up -d --build
```

Sobe o app em <http://localhost:8000> com PostgreSQL e um servidor Qdrant (`QDRANT_URL=http://qdrant:6333`), aplicando as migrações na partida. A imagem não inclui a CLI do Codex: no Docker use um provider por API (OpenAI, Gemini etc.), ou rode localmente com `scripts/dev.sh` para usar a assinatura.

Só o Qdrant em servidor, para o desenvolvimento local:

```bash
docker run -d --name qdrant -p 6333:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant
echo 'QDRANT_URL=http://localhost:6333' >> backend/.env
```

## Testes e verificações

```bash
cd backend && source .venv/bin/activate && pytest -q
cd frontend && npm run check:cjk && npm run build
python scripts/e2e_smoke.py main   # com o backend rodando: fluxo real pelo Codex (poucas chamadas)
```

`npm run check:cjk` falha se sobrar texto em chinês na interface.

## Estrutura

```
backend/    API FastAPI, serviços de IA, memória vetorial, migrações (alembic/sqlite e alembic/postgres)
frontend/   Interface React
scripts/    dev.sh (ambiente local) e e2e_smoke.py (verificação ponta a ponta)
```

## Licença e créditos

GPL v3 (veja `LICENSE`). Baseado no projeto original MuMuAINovel, de xiamuceer-j.
