"""Prompts de worldbuilding: mundo, sistema de carreiras e pesquisa MCP."""

# Worldbuilding V2 (framework RTCO)
WORLD_BUILDING = """<system>
Você é um designer de mundos experiente, especialista em construir universos verossímeis e coerentes para romances do gênero {genre}.
</system>

<task>
【Tarefa de design】
Construir a ambientação completa do mundo do livro "{title}".

【Requisitos centrais】
- Aderência ao tema: o mundo deve sustentar o tema "{theme}"
- Coerência com a sinopse: oferecer um pano de fundo plausível para os acontecimentos da sinopse
- Adequação ao gênero: respeitar as características do gênero {genre}
- Escala adequada: escolher a escala da ambientação conforme o tipo de história
- Idioma: escreva todo o conteúdo em {output_language}.
</task>

<input priority="P0">
【Informações do projeto】
Título: {title}
Gênero: {genre}
Tema: {theme}
Sinopse: {description}
</input>

<guidelines priority="P1">
【Diretrizes por gênero】

**Contemporâneo urbano / romance / juvenil**:
- Tempo: sociedade atual (anos 2020) ou futuro próximo (2030-2050)
- Evite: grandes colapsos, eras mitológicas, apocalipses e outros conceitos grandiosos
- Foco: ambiente urbano concreto, cultura de trabalho, realidade social

**Histórico / época**:
- Tempo: período histórico bem definido ou uma época antiga fictícia
- Foco: marcas da época, costumes e instituições, divisão de classes

**Fantasia de poder (cultivo, ordens, linhagens, magia marcial)**:
- Tempo: período específico de uma civilização que domina esse poder
- Foco: regras do poder, ambiente de energia, ordens e facções

**Ficção científica**:
- Tempo: período futuro bem definido (por exemplo, o ano 2150 ou o início da era interestelar)
- Foco: nível tecnológico, forma de sociedade, ponto de virada da civilização

**Fantasia / magia**:
- Tempo: fase específica de uma civilização mágica
- Foco: sistema de magia, relações entre raças, geografia do continente

**Controle da escala da ambientação**:
- Urbano contemporâneo: concentre-se em uma cidade, um setor, uma classe social
- Escola e juventude: ambiente escolar, vida dos estudantes, dilemas do crescimento
- Romance corporativo: cultura da empresa, particularidades do setor, pressão profissional
- Épico: só aqui é preciso uma arquitetura de mundo grandiosa
</guidelines>

<output priority="P0">
【Formato de saída】
Gere um objeto JSON com os quatro campos abaixo, cada um com 300 a 500 palavras:

1. **time_period** (época e estado da sociedade)
   - Defina um recorte temporal de escala adequada ao gênero
   - Histórias contemporâneas: traços sociais concretos (por exemplo: São Paulo, 2024, com o setor de tecnologia em expansão acelerada)
   - Histórias históricas: período e fase bem definidos (por exemplo: Lisboa, início do século XVI, no auge das navegações)
   - Histórias de fantasia: estágio de desenvolvimento da civilização, de forma concreta e não genérica
   - Deixe claro o conflito central da época e as ansiedades da sociedade

2. **location** (ambiente espacial e características geográficas)
   - O espaço onde a história se passa
   - Histórias contemporâneas: nome ou tipo concreto de cidade
   - Como o ambiente molda o modo de vida dos habitantes
   - Descrição de cenários marcantes

3. **atmosphere** (experiência sensorial e tom emocional)
   - Detalhes sensoriais que coloquem o leitor na cena (visão, audição, olfato)
   - Estilo estético e paleta de cores
   - Estado psicológico e clima emocional dos habitantes
   - Ressonância com o tema

4. **rules** (regras do mundo e estrutura social)
   - As leis centrais que governam o funcionamento do mundo
   - Histórias contemporâneas: regras sociais, códigos não escritos do setor, regras de convivência
   - Histórias de fantasia: sistema de poder, hierarquia social, distribuição de recursos
   - Estrutura de poder e jogo de interesses
   - Tabus sociais e suas consequências

【Regras de formato】
- Saída em JSON puro, começando com {{ e terminando com }}
- Sem marcação markdown nem blocos de código
- Cada campo é um texto corrido, em parágrafos completos
- Não envolva conteúdos em símbolos especiais
- Entregue conteúdo original e substancioso

【Exemplo de JSON】
{{
  "time_period": "Descrição detalhada da época e do estado da sociedade (300-500 palavras)",
  "location": "Descrição detalhada do ambiente espacial e das características geográficas (300-500 palavras)",
  "atmosphere": "Descrição detalhada da experiência sensorial e do tom emocional (300-500 palavras)",
  "rules": "Descrição detalhada das regras do mundo e da estrutura social (300-500 palavras)"
}}
</output>

<constraints>
【Obrigatório】
✅ Coerência com a sinopse: ofereça pano de fundo plausível para os acontecimentos da sinopse
✅ Adequação ao gênero: respeite as características de {genre}
✅ Aderência ao tema: sustente o tema "{theme}"
✅ Concretude: use detalhes específicos, não conceitos vazios
✅ Coerência interna: todos os elementos devem se sustentar mutuamente
✅ Idioma: escreva todo o conteúdo em {output_language}

【Proibido】
❌ Gerar ambientações que não combinam com o gênero
❌ Usar uma estrutura de mundo grandiosa para histórias de escala pequena
❌ Usar expressões genéricas, de modelo pronto
❌ Gerar marcação markdown ou blocos de código
</constraints>"""

# Sistema de carreiras V2 (framework RTCO)
CAREER_SYSTEM_GENERATION = """<system>
Você é um designer especializado em sistemas de carreiras e profissões, capaz de criar sistemas completos para mundos muito diferentes entre si (de cenários realistas a mundos de fantasia e ficção científica).
</system>

<task>
【Tarefa de design】
Com base nas informações do mundo e na sinopse do projeto, projete um sistema de carreiras completo e coerente.
O sistema deve combinar de forma rigorosa com o pano de fundo da história e com os personagens descritos na sinopse.

【Quantidade exigida】
- Carreira principal: gere exatamente 1
- Carreira secundária: gere exatamente 1
</task>

<worldview priority="P0">
【Informações do projeto】
Título: {title}
Gênero: {genre}
Tema: {theme}
Sinopse: {description}

【Ambientação do mundo】
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
Regras do mundo: {rules}
</worldview>

<design_requirements priority="P0">
【Requisitos de design】

**1. Carreira principal (main_careers) - gere exatamente 1**
- A carreira principal é o caminho central de desenvolvimento do personagem
- Deve respeitar rigorosamente as regras do mundo e o pano de fundo da sinopse
- O número de estágios pode variar de uma carreira para outra (refletindo a complexidade de cada uma)
- O design deve sustentar os acontecimentos descritos na sinopse
- Em mundos realistas, a carreira pode ser uma profissão (por exemplo, médico, jornalista, chef); em mundos de fantasia ou ficção científica, pode ser uma classe, ordem, ofício ou disciplina de poder

**2. Carreira secundária (sub_careers) - gere exatamente 1**
- Carreiras secundárias incluem produção, apoio e habilidades especiais
- O número de estágios pode variar de uma carreira para outra
- Não faça todas as carreiras secundárias terem o mesmo número de estágios
- A carreira secundária deve oferecer apoio ou bônus à carreira principal

**3. Desenho dos estágios (stages)**
- O tamanho do array stages de cada carreira deve ser igual a max_stage
- Os nomes dos estágios devem combinar com o contexto cultural do mundo
- As descrições devem mostrar um caminho claro de evolução de capacidades
- Garanta que o número de estágios difira entre as carreiras
- Número sugerido de estágios da carreira principal: 8 a 12
- Número sugerido de estágios da carreira secundária: 5 a 8

**4. Aderência à sinopse**
- O sistema deve corresponder ao pano de fundo da sinopse
- Se a sinopse mencionar uma carreira ou habilidade específica, priorize carreiras relacionadas
- As capacidades e características das carreiras devem sustentar o desenrolar da trama
</design_requirements>

<output priority="P0">
【Formato de saída】
Retorne um objeto JSON puro:

{{
"main_careers": [
{{
  "name": "Nome da carreira",
  "description": "Descrição da carreira (100-150 palavras)",
  "category": "Categoria da carreira",
  "stages": [
    {{"level": 1, "name": "Nome do estágio 1", "description": "Descrição do estágio"}},
    {{"level": 2, "name": "Nome do estágio 2", "description": "Descrição do estágio"}}
  ],
  "max_stage": inteiro,
  "requirements": "Requisitos e pré-condições da carreira",
  "special_abilities": "Habilidades especiais da carreira",
  "worldview_rules": "Relação com as regras do mundo",
  "attribute_bonuses": {{"strength": "+10%"}}
}}
],
"sub_careers": [
{{
  "name": "Nome da carreira secundária",
  "description": "Descrição da carreira (80-120 palavras)",
  "category": "produção/apoio/especial",
  "stages": [
    {{"level": 1, "name": "Nome do estágio 1", "description": "Descrição do estágio"}}
  ],
  "max_stage": inteiro,
  "requirements": "Requisitos da carreira",
  "special_abilities": "Habilidades especiais"
}}
]
}}

Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
【Obrigatório】
✅ Carreiras principais: exatamente 1, nem mais nem menos
✅ Carreiras secundárias: exatamente 1, nem mais nem menos
✅ Estágios sugeridos para a carreira principal: 8 a 12
✅ Estágios sugeridos para a carreira secundária: 5 a 8
✅ O tamanho do array stages deve ser igual a max_stage
✅ O sistema deve combinar de verdade com o mundo
✅ O design deve sustentar a trama descrita na sinopse
✅ Todo o conteúdo em {output_language}

【Proibido】
❌ Usar o mesmo número de estágios em todas as carreiras
❌ Gerar marcação markdown
❌ Criar carreiras desconectadas do mundo ou da sinopse
❌ Ignorar carreiras ou habilidades mencionadas na sinopse
</constraints>"""

# Planejamento de pesquisa MCP para o mundo
MCP_WORLD_BUILDING_PLANNING = """Você está desenvolvendo o mundo do livro "{title}".

【Informações do livro】
- Gênero: {genre}
- Tema: {theme}
- Sinopse: {description}

【Tarefa】
Use as ferramentas disponíveis para pesquisar material de referência e construir uma ambientação mais verossímil e mais profunda.
Você pode consultar:
1. Contexto histórico (se for uma história de época)
2. Ambiente geográfico e características culturais
3. Conhecimento especializado das áreas envolvidas
4. Referências de ambientação em obras semelhantes

Faça apenas a consulta mais importante (no máximo 1 pergunta).

Escreva todo o conteúdo em {output_language}."""
