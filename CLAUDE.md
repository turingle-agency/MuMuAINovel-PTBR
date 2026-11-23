# CLAUDE.md — MuMuAINovel-PTBR (Fábrica de Ebooks)

## GitHub: repositório da turingle-agency

O repositório é `turingle-agency/MuMuAINovel-PTBR`. A conta pessoal `alissonryan` tem só leitura nele, então:

- **Push**: sempre pelo alias SSH `github-turingle` (chave `~/.ssh/alisson-turingle`, autentica como `turingle-agency`), sem alterar o `origin`:
  ```bash
  git push git@github-turingle:turingle-agency/MuMuAINovel-PTBR.git <branch>:<branch>
  ```
- **PRs e API do GitHub (`gh`)**: trocar para a conta da turingle antes, e voltar para a pessoal depois:
  ```bash
  gh auth switch -u turingle-agency
  gh pr create --repo turingle-agency/MuMuAINovel-PTBR --base main --head <branch> ...
  gh auth switch -u alissonryan
  ```
- A conta ativa padrão do `gh` neste Mac é `alissonryan`.

## Modelos de IA

- Antes de escrever ou manter qualquer ID de modelo (padrões, placeholders, exemplos, testes), conferir a documentação oficial atual de cada provedor — nunca confiar em IDs herdados do upstream ou de memória.
- Os modelos padrão ficam num só lugar: `backend/app/constants/models.py` (espelho em `frontend/src/constants/models.ts`), com a data da conferência em `MODELS_CHECKED_AT`. O teste `backend/tests/test_modelos_atuais.py` falha se um ID desatualizado aparecer.

## Referências

- Design: `docs/superpowers/specs/2026-11-11-fabrica-de-ebooks-design.md`
- Plano da Fundação: `docs/superpowers/plans/2026-11-12-fundacao.md` (a pasta `docs/` é ignorada pelo git; use `git add -f` para versionar)
- Desenvolvimento local: `scripts/dev.sh`; testes: `cd backend && source .venv/bin/activate && pytest -q`; frontend: `cd frontend && npm run check:cjk && npm run build`
