# Guia de Skills: como adicionar ou modificar uma Skill

## 1. Visão geral da arquitetura de Skills

```
backend/app/skills/          ← Pasta com todas as Skills
├── story-short-write/       ← Uma pasta por Skill
│   ├── SKILL.md            ← Obrigatório: metadados YAML + instruções do fluxo de trabalho
│   └── references/         ← Opcional: base de conhecimento (arquivos .md)
│       ├── xxx.md
│       └── ...
├── story-long-write/
│   ├── SKILL.md
│   └── references/...
└── ...

backend/app/services/skill_loader.py   ← Carregador de Skills (varre a pasta skills/ automaticamente)
backend/app/api/skills.py              ← Endpoints da API (/api/skills/list)
backend/app/services/prompt_service.py ← Injeta a Skill no prompt de sistema
```

**Mecanismo central**: na inicialização, o `skill_loader.py` varre a pasta `skills/`, lê o `SKILL.md` de cada subpasta, interpreta os metadados YAML e as instruções do fluxo de trabalho, anexa os materiais de `references/` e entrega tudo à IA.

---

## 2. Adicionar uma nova Skill (3 passos)

### Passo 1: criar a pasta da Skill

Crie uma nova pasta em `backend/app/skills/`. Recomenda-se nome em letras minúsculas, sem acentos, com hifens:

```bash
mkdir -p backend/app/skills/my-new-skill/references
```

### Passo 2: criar o SKILL.md (obrigatório)

Crie o `SKILL.md` na pasta. O formato é fixo: **frontmatter YAML + corpo em Markdown**:

```markdown
---
name: my-new-skill
display_name: Nome exibido na interface
category: Skill · Minha categoria
description: |
  Descrição em uma frase do que esta Skill faz.
  Como acionar: /my-new-skill, "me ajude a fazer xxx"
triggers:
  - /my-new-skill
  - me ajude a fazer xxx
---

# my-new-skill: título de exibição da Skill

Você é um especialista em xxx. Sua tarefa é ajudar o usuário a concluir xxx.

## Princípios centrais

- Princípio 1...
- Princípio 2...

## Fluxo de trabalho

### Fase 1: confirmar a necessidade
...

### Fase 2: execução
...

### Fase 3: entrega
...

## Formato de saída
...
```

**Campos do frontmatter YAML**:

| Campo | Obrigatório | Descrição |
|------|------|------|
| `name` | Sim | Identificador interno da Skill; mantenha igual ao nome da pasta. É usado como chave da Skill, **não traduza nem altere** |
| `description` | Sim | Descrição da Skill |
| `display_name` | Não | Nome exibido na lista da interface. Se omitido, usa-se a primeira frase da `description` |
| `category` | Não | Categoria exibida na interface. Se omitida, é inferida pelo `name` (ver abaixo) |
| `triggers` | Não | Lista de gatilhos (comandos e frases) que acionam a Skill |

**Classificação automática** (em `skill_loader.py`, quando `category` não é informada):

| O `name` contém | Categoria exibida na interface |
|-----------|-------------|
| `long` | Skill · Romance longo |
| `short` | Skill · Conto |
| `deslop` | Skill · Revisão |
| `browser` | Skill · Ferramentas |
| outros | Skill |

### Passo 3: adicionar materiais de referência (opcional)

Coloque arquivos `.md` em `references/`; cada um é anexado automaticamente ao conteúdo do SKILL.md como "material de referência":

```
references/
├── technique-a.md      ← carregado automaticamente, com o título "Material de referência: technique-a"
├── technique-b.md      ← carregado automaticamente, com o título "Material de referência: technique-b"
└── examples.md
```

**Pronto!** Depois de reiniciar o serviço, a nova Skill aparece sozinha na lista da interface, sem mudar nenhum código.

---

## 3. Modificar uma Skill existente

### Alterar as instruções do fluxo de trabalho

Edite diretamente a parte em Markdown, abaixo do `---`, no `SKILL.md` da pasta da Skill.

### Alterar os metadados (nome, descrição)

Edite o frontmatter YAML no início do `SKILL.md`:

```yaml
---
name: story-short-write          ← identificador interno (não altere)
description: |                   ← altere a descrição
  Nova descrição em uma frase. Detalhes em seguida...
---
```

### Adicionar ou remover materiais de referência

Basta adicionar ou remover arquivos `.md` em `references/`; a mudança vale após reiniciar.

### Alterar a classificação automática

Edite a lógica de classificação em `backend/app/services/skill_loader.py` (função `_infer_category`):

```python
def _infer_category(name: str) -> str:
    if "long" in name:
        return "Skill · Romance longo"
    if "short" in name:
        return "Skill · Conto"
    # 👇 Adicione aqui novas regras de classificação
    if "my-keyword" in name:
        return "Skill · Nova categoria"
    return "Skill"
```

---

## 4. Como a Skill circula pelo sistema

Entender como a Skill é usada ajuda a investigar problemas:

### 4.1 Página SkillChat (conversa independente)

```
O usuário escolhe uma Skill no SkillChat
  → o frontend chama /api/skills/list para obter a lista
  → o frontend chama /api/skills/execute para enviar a mensagem
  → o skill_loader do backend carrega o SKILL.md + references
  → injeta no prompt de sistema → chama a IA → devolve o resultado
```

### 4.2 Geração de capítulos (individual / em lote)

```
O usuário escolhe uma Skill na lista suspensa
  → o frontend envia a skill_key ao backend
  → o backend obtém o conteúdo da Skill pelo prompt_service
  → injeta no prompt de sistema da geração de capítulos
  → a IA gera o capítulo guiada pela Skill
```

Pontos-chave no código:
- **Ponto de injeção no backend**: método `get_skill_content()` em `backend/app/services/prompt_service.py`
- **Geração individual**: `backend/app/store/hooks.ts` → `generateChapterContentStream()`
- **Geração em lote**: `backend/app/api/chapters.py` → `generate_single_chapter_for_batch()`

---

## 5. Exemplo completo: adicionar uma Skill de "verificação de ritmo"

```bash
# 1. Criar a pasta
mkdir -p backend/app/skills/story-pacing-check/references

# 2. Criar o SKILL.md
cat > backend/app/skills/story-pacing-check/SKILL.md << 'EOF2'
---
name: story-pacing-check
display_name: Diagnóstico de ritmo
description: |
  Diagnóstico de ritmo. Analisa o ritmo narrativo dos capítulos existentes, aponta trechos arrastados ou apressados e sugere correções.
  Como acionar: /story-pacing-check, "verifique o ritmo", "o ritmo está com problema"
triggers:
  - /story-pacing-check
  - verifique o ritmo
---

# story-pacing-check: diagnóstico de ritmo narrativo

Você é um especialista em ritmo narrativo. Sua tarefa é ajudar o usuário a analisar problemas de ritmo nos capítulos.

## Dimensões de análise

### 1. Densidade de informação
- Cada parágrafo traz informação nova que faz a história avançar?
- Há expressões repetidas?

### 2. Curva emocional
- A emoção tem altos e baixos?
- Há preparação suficiente antes do clímax?

### 3. Troca de cenas
- A transição entre cenas é natural?
- A linha do tempo está clara?

## Formato de saída

Apresente: local do problema → análise da causa → sugestão de correção
EOF2

# 3. Reinicie o serviço!
```

---

## 6. Observações

1. **Codificação do SKILL.md**: deve ser UTF-8
2. **Formato YAML**: o conteúdo depois de `description: |` precisa estar indentado
3. **Regras de nomenclatura**: o nome da pasta e o campo `name` usam letras minúsculas e hifens (como `my-skill-name`)
4. **Cache**: as Skills ficam em cache na memória; depois de alterar, reinicie o serviço. Também é possível chamar `refresh_skills_cache()` para atualizar a quente
5. **Tamanho dos arquivos de referência**: todos os arquivos de `references/` são concatenados ao prompt, então cuide para que o tamanho total não ultrapasse o limite de contexto do modelo
6. **Não é preciso mudar código**: adicionar uma Skill padrão (apenas SKILL.md + references) não exige alterar nenhum código Python/TypeScript
