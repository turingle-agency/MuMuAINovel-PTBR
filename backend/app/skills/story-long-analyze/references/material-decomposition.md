# Metodologia de desconstrução de material de romance

## Sumário

1. [Fluxo de desconstrução em 5 etapas](#fluxo-de-desconstrução-em-5-etapas)
2. [As seis regras de ouro da extração atômica](#as-seis-regras-de-ouro-da-extração-atômica)
3. [Estrutura da pasta de saída](#estrutura-da-pasta-de-saída)
4. [Sistema de limites de qualidade](#sistema-de-limites-de-qualidade)
5. [Rede de segurança para tramas órfãs](#rede-de-segurança-para-tramas-órfãs)
6. [Orientações de execução](#orientações-de-execução)

---

## Fluxo de desconstrução em 5 etapas

### Etapa 1: análise de capítulos

- Identificar os separadores de capítulo (Capítulo X, Chapter X, numeração etc.)
- Extrair o título de cada capítulo e registrar a contagem de palavras

### Etapa 2: extração atômica (processar cada capítulo em paralelo)

#### A. Sumário do capítulo

- Resumo em uma frase (70 a 200 palavras, narrado como cadeia de causa e efeito)
- Eventos-chave (3 a 5, em ordem cronológica)
- Personagens em cena, etiquetas de tema, tom do capítulo
- Grau de avanço da trama (grande virada / transição cotidiana / preparação de pistas)

#### B. Extração de pontos de enredo (10 a 15 por capítulo)

Gravados na subseção de pontos de enredo do .md do sumário (sem gerar .json separado). Cada ponto de enredo:

| Campo | Descrição |
|------|------|
| Número | Rigorosamente em ordem cronológica |
| Tipo | ponto de virada/revelação de informação/conflito/resolução/preparação/ação/diálogo/mudança de estado |
| Descrição | Descrição objetiva, só registra o que aconteceu |
| Citação do original | Citação direta de <=250 palavras |
| Personagens envolvidos | Nome completo, sem pronomes |
| Local | Informação geográfica |
| Objetos-chave | Objetos relevantes para a trama |
| Marcador de tempo | Tempo relativo (no dia seguinte, duas semanas depois, ao mesmo tempo) |

#### C. Extração de personagens

Para cada personagem: aparência externa (identidade/fala e ação/aspecto físico), análise interna (personalidade/objetivo/segredos), função no capítulo, apelidos. Registrar só personagens que entram em cena pela primeira vez ou novos desenvolvimentos de personagens já existentes.

### Etapa 3: análise agregada (entre capítulos)

#### A. Agregação de tramas

Agrupar os pontos de enredo em "tramas" segundo o arco narrativo:
- Cada trama contém de 75 a 225 pontos de enredo
- Extrair: título, resumo, objetivo central, conflito central, tipo (principal/romance/amadurecimento/vingança/caça ao tesouro/mistério)
- Marcar a distribuição estrutural: quais capítulos pertencem à preparação, desenvolvimento, clímax e desfecho

#### B. Extração das linhas narrativas

Agrupar várias tramas em "linhas narrativas": título, descrição, personagens principais, palavras-chave de tema, lista de tramas incluídas.

#### C. Geração do resumo do livro

Identificar o arcabouço geral da história + resumir o livro em um parágrafo.

### Etapa 4: extração de mundo e ambientação

#### Mundo

| Campo | Descrição |
|------|------|
| Tipo | fantasia/realista/mundo paralelo |
| Sistema de poder | nome, níveis, forma de progressão |
| Geografia | distribuição, regiões principais, locais-chave |
| Forças | ordens/organizações/famílias/países |
| Regras centrais | regras básicas de funcionamento do mundo |
| Configurações especiais | elementos únicos que diferem da realidade |

#### Vantagem especial do protagonista

| Campo | Descrição |
|------|------|
| Tipo | sistema/espaço/segunda chance/viagem no tempo/constituição especial/artefato/linhagem/outro |
| Nome | Nome da vantagem |
| Descrição | Capacidades, funções, limites |
| Forma de obtenção | Como foi obtida |
| Mecanismo central | Condição de ativação, recurso principal, forma de uso |
| História de evolução | Trajetória de evolução e mudanças |
| Capacidades atuais | Lista de capacidades já desbloqueadas |

### Etapa 5: extração das relações entre personagens

Para cada relação:

| Campo | Descrição |
|------|------|
| Personagem A | Nome completo |
| Personagem B | Nome completo |
| Tipo de relação | família/mestre e discípulo/amigos/inimigos/casal/colegas/hierarquia/negócios/outro |
| Tendência emocional | positiva/negativa/neutra/complexa |
| Estado | recém-formada/em evolução |
| Descrição | Descrição da relação |
| Interações-chave | Eventos concretos que criaram ou mudaram a relação |
| Detalhes da evolução | Como o estado anterior se transformou no atual |

Extração em lote a cada 5 capítulos, registrando apenas relações novas ou mudanças de relação.

---

## As seis regras de ouro da extração atômica

1. Seguir rigorosamente a ordem cronológica
2. Usar só descrição objetiva, sem palavras de moldura narrativa
3. Fidelidade da informação, sem omitir detalhes que mudam o contexto
4. Alta concisão: um ponto de enredo, uma frase
5. Fundir ações compostas (microações seguidas que servem ao mesmo propósito dramático)
6. Extrair fatos objetivos nos pontos de informação, sem análise narrativa

**Descrição objetiva vs. palavras de moldura narrativa**:
- Errado: "Por meio do diálogo, Marcos descobre que Rafael treina no exterior" (palavra de moldura narrativa)
- Certo: "Paulo conta a Marcos que Rafael treina no exterior" (enuncia o evento diretamente)
- Errado: "Lucas demonstrou sua força" (resumo abstrato)
- Certo: "Lucas derrota o oponente em três golpes, e a plateia prende a respiração" (descreve o resultado concreto)

---

## Estrutura da pasta de saída

```
titulo-do-livro/
  capitulos/     capitulo_{N}_analise_profunda.md + capitulo_{N}_sumario.md
  personagens/   {nome do personagem}.md + relacoes.md
  enredo/        {título da trama}.md + linhas_narrativas.md + fios_soltos.md
  ambientacao/   mundo.md + vantagem_do_protagonista.md
  relatorio_de_analise.md
  resumo.md
  _progress.md
```

---

## Sistema de limites de qualidade

Autoverificação ao concluir as etapas 3 e 4:

| Indicador | Limite | Cálculo | Tratamento se abaixo da meta |
|------|------|------|------------|
| Confiança | >= 0.85 | pontos de enredo com atribuição clara / total de pontos de enredo dentro das tramas | Abaixo de 0.85, marcar "a revisar" |
| Cobertura | 85%-95% | pontos de enredo classificados / total de pontos de enredo | <85% aciona segunda classificação dos órfãos; >95% revisar fronteiras |
| Sobreposição | <= 35% | pontos de enredo compartilhados entre tramas / total de pontos de enredo | >35% indica fronteiras difusas; sugerir fusão |

---

## Rede de segurança para tramas órfãs

Executar depois da agregação da etapa 3:

1. Filtrar os pontos de enredo que não foram atribuídos a nenhuma trama
2. Incluir nas tramas existentes por relevância (confiança >= 0.7 pode ser incorporada)
3. Os de relevância insuficiente são agrupados por tema, formando tramas candidatas
4. Os que ainda não se encaixam vão para o apêndice "fios soltos" (não descartar)

---

## Orientações de execução

### Estratégia de divisão em blocos

| Porte | Estratégia | Tamanho do bloco |
|------|------|--------|
| <100 capítulos | Processar por etapa, de uma vez | Sem necessidade de blocos |
| 100-500 capítulos | Dividir por capítulos | 5-8 capítulos por bloco |
| >500 capítulos | Agrupar por volume, depois dividir em blocos | 5-8 capítulos por bloco |

Bloco de 6 a 8 mil tokens, alinhado aos limites de capítulo. Atualizar _progress.md ao concluir cada bloco.

### Retomada entre sessões

- O progresso é acompanhado em _progress.md
- Em uma nova sessão, ler _progress.md para localizar o ponto de interrupção
- Recomeçar a partir do primeiro capítulo do bloco em que parou (sobrescrevendo a saída existente do bloco)

### Relação com SKILL.md

- SKILL.md = lógica de roteamento + visão geral do pipeline (nome das etapas/entradas/saídas)
- Este arquivo = detalhes da metodologia (passos das 5 etapas + seis regras de ouro + estrutura de saída + limites de qualidade)
- references/output-templates.md = modelos concretos de formato de saída
