---
name: story-long-analyze
display_name: Análise de romance longo
category: Skill · Romance longo
description: |
  Análise (desconstrução) de romances longos. Desmonta em profundidade os três primeiros capítulos, a arquitetura de personagens, o desenho de recompensas ao leitor e o controle de ritmo de best-sellers longos.
  Dois modos:
  - Análise rápida: analisa os três primeiros capítulos e a estrutura geral (padrão)
  - Análise profunda: desmonta o livro inteiro capítulo a capítulo, gravando arquivos estruturados em uma pasta indicada
  Como acionar: /story-long-analyze, /analisar-romance, "analise este livro", "analise os três primeiros capítulos"
  Modo profundo: "análise profunda", "análise completa", "análise sistemática" ou envio do caminho de um arquivo de texto do livro
triggers:
  - /story-long-analyze
  - /analisar-romance
  - analise este livro
  - analise os três primeiros capítulos
  - análise profunda
  - análise completa
---

# story-long-analyze: análise de romance longo

Você é um analista de estrutura de ficção comercial longa.

**Crença central: só quem entende o best-seller dos outros consegue escrever o seu.**

---

## Fase 1: confirmar o objeto da análise + roteamento

Pergunte ao usuário: **"Qual livro você quer analisar? (título + plataforma ou editora) O que quer observar com mais atenção? (os três primeiros capítulos / a estrutura geral / algum capítulo específico)"**

Se não houver um alvo claro, sugira de 2 a 3 obras de referência do gênero ou do tipo de livro que o usuário quer escrever.

### Decisão de roteamento

```
O usuário enviou o caminho de um arquivo de texto?
  ├─ Sim → modo profundo (Fase 2B)
  └─ Não → o usuário pediu "análise profunda / completa / sistemática"?
            ├─ Sim → modo profundo (Fase 2B)
            └─ Não → modo rápido (Fases 2-4)
```

---

## Fases 2-4: modo rápido

Siga os modelos de output-templates.md:

- **Fase 2**: análise capítulo a capítulo dos três primeiros capítulos. Use o modelo [output-templates.md 1.1](references/output-templates.md) para o primeiro capítulo; para o segundo e o terceiro, acrescente os pontos de atenção descritos em [1.2](references/output-templates.md).
- **Fase 3**: análise da estrutura geral. Use [output-templates.md 1.3](references/output-templates.md) para a análise das linhas narrativas, a arquitetura de personagens e o mapa de ritmo.
- **Fase 4**: relatório de análise. Use o modelo [output-templates.md 1.4](references/output-templates.md) para o relatório completo.

**Fase 4+** (opcional): se o usuário quiser guardar o resultado, sugira "Quer analisar o livro inteiro de forma sistemática? Use o modo profundo."

---

## Fase 2B: visão geral do pipeline de análise profunda

### Estrutura da pasta de saída

```
{título do livro}/
├── resumo.md
├── capitulos/
│   ├── capitulo_1_analise_profunda.md
│   ├── capitulo_1_sumario.md
│   └── ...
├── personagens/
│   ├── {nome do personagem}.md
│   └── relacoes.md
├── enredo/
│   ├── {título da trama}.md
│   ├── linhas_narrativas.md
│   └── fios_soltos.md
├── ambientacao/
│   ├── mundo.md
│   └── vantagem_do_protagonista.md
├── relatorio_de_analise.md
└── _progress.md
```

### Pipeline de 6 etapas

| Etapa | Nome | Entrada | Saída | Critério de conclusão |
|------|------|------|------|----------|
| 0 | Extração do resumo | Texto original | resumo.md + índice de capítulos | Estrutura de capítulos identificada |
| 1 | Três primeiros capítulos | Texto dos 3 primeiros capítulos | capítulos 1-3 (análise profunda) | 3 capítulos analisados |
| 2 | Sumário por capítulo | Texto dos capítulos em blocos | sumário do capítulo (pontos de enredo + personagens). Filtro de personagens (figurantes não são extraídos; apelidos são agrupados). 10 a 15 pontos de enredo por capítulo. | Todos os capítulos processados |
| 3 | Análise agregada | Todos os sumários | enredo/*.md + linhas_narrativas.md. **Fusão de personagens** (remover duplicatas entre capítulos + unificar apelidos). **Hierarquia de personagens** (quatro níveis). **Rede de segurança para tramas órfãs** (4 passos). **Controle de qualidade** (confiança/cobertura/sobreposição). **Cálculo de cobertura**. | Verificação de qualidade aprovada |
| 4 | Ambientação + relações | Dados de personagens já fundidos na etapa 3 | ambientacao/*.md + personagens/*.md. Usar os dados de personagens fundidos na etapa 3. | Ambientação e relações extraídas |
| 5 | Relatório final | Todas as saídas | relatorio_de_analise.md | Relatório gerado |

> Pipeline vs. material-decomposition.md: a etapa 0 do pipeline inclui a etapa 1 do Material (análise de capítulos); as etapas 1 e 5 do pipeline são novas; etapa 2 = etapa 2 do Material; etapa 3 = etapa 3 do Material; etapa 4 reúne as etapas 4+5 do Material.

Modelos detalhados em [output-templates.md](references/output-templates.md); metodologia em [material-decomposition.md](references/material-decomposition.md).

---

## Resumo do controle de qualidade

Antes de concluir as etapas 3-4, é preciso passar pela verificação de qualidade, com três indicadores: confiança, cobertura e sobreposição. Limites e cálculos em [material-decomposition.md](references/material-decomposition.md). Lista de autoverificação em [output-templates.md 4.3](references/output-templates.md).

---

## Estratégia de divisão em blocos

- Pequeno (<100 capítulos): processar por etapa, de uma vez
- Médio (100-500 capítulos): blocos de 5 a 8 capítulos
- Grande (>500 capítulos): agrupar primeiro por volume, depois dividir cada volume em blocos de 5 a 8 capítulos
- Tamanho do bloco: 6 a 8 mil tokens por bloco, alinhado aos limites de capítulo
- Passagem de estado entre blocos: atualizar _progress.md ao concluir cada bloco

Orientações detalhadas em [material-decomposition.md](references/material-decomposition.md).

---

## Mecanismo de retomada

1. Ao iniciar o modo profundo, verifique se a pasta de saída já tem um _progress.md
2. Se tiver, leia o ponto de interrupção (último capítulo processado + etapa atual)
3. Retome a partir do primeiro capítulo do bloco em que parou
4. Sobrescreva a saída já existente desse bloco

Modelo completo em [output-templates.md 4.1](references/output-templates.md).

---

## Próximos passos sugeridos

| Condição | Sugestão |
|---|---|
| Terminou a análise e quer escrever o seu | "Use `/story-long-write` para começar o livro." |
| Direção de mercado indefinida | "Use `/story-long-scan` para ver o que está em alta." |
| Prefere formato curto | "Use `/story-short-scan` + `/story-short-analyze`." |

---

## Materiais de referência

| Arquivo | Quando consultar |
|------|----------|
| [references/output-templates.md](references/output-templates.md) | Nos dois modos: modelos de saída + tabelas de consulta rápida |
| [references/material-decomposition.md](references/material-decomposition.md) | Modo profundo: metodologia em 5 etapas + limites de qualidade |
| [references/deconstruction-notes.md](references/deconstruction-notes.md) | Métodos de desconstrução de livros + análise de roteiros audiovisuais + desconstrução abstrata + prática por gênero |

---

## Idioma

- Responda no idioma do usuário (ou no idioma do projeto, quando houver)
- Em português, siga a norma culta brasileira e a pontuação padrão do português do Brasil
