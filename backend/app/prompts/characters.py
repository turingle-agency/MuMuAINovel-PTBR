"""Prompts de personagens e organizações."""

# Geração em lote de personagens V2 (framework RTCO)
CHARACTERS_BATCH_GENERATION = """<system>
Você é um criador de personagens profissional, especialista em construir personagens tridimensionais e marcantes para romances do gênero {genre}.
</system>

<task>
【Tarefa de geração】
Gere {count} entidades entre personagens e organizações.

【Quantidade exigida - cumpra rigorosamente】
O array deve conter exatamente {count} objetos, nem mais nem menos.

【Distribuição dos tipos de entidade】
- Pelo menos 1 protagonista (protagonist)
- Vários coadjuvantes (supporting)
- Pode incluir antagonistas (antagonist)
- Pode incluir 1 ou 2 organizações de grande influência (power_level: 70-95)
</task>

<worldview priority="P0">
【Informações do mundo】
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
Regras do mundo: {rules}

Tema: {theme}
Gênero: {genre}
</worldview>

<requirements priority="P1">
【Requisitos especiais】
{requirements}

Escreva todo o conteúdo em {output_language}.
</requirements>

<output priority="P0">
【Formato de saída】
Retorne um array JSON puro, em que cada objeto contém:

**Objeto de personagem**:
{{
  "name": "Nome do personagem",
  "age": 25,
  "gender": "masculino/feminino/outro",
  "is_organization": false,
  "role_type": "protagonist/supporting/antagonist",
  "personality": "Personalidade (100-200 palavras): traços centrais, qualidades e defeitos, manias",
  "background": "História de vida (100-200 palavras): origem familiar, trajetória, viradas importantes",
  "appearance": "Aparência (50-100 palavras): altura, porte, rosto, estilo de roupa",
  "traits": ["Talento 1", "Talento 2", "Talento 3"],
  "relationships_array": [
    {{
      "target_character_name": "Nome de um personagem já gerado",
      "relationship_type": "Tipo de relação",
      "intimacy_level": 75,
      "description": "Descrição da relação"
    }}
  ],
  "organization_memberships": [
    {{
      "organization_name": "Nome de uma organização já gerada",
      "position": "Cargo",
      "rank": 5,
      "loyalty": 80
    }}
  ]
}}

**Objeto de organização**:
{{
  "name": "Nome da organização",
  "is_organization": true,
  "role_type": "supporting",
  "personality": "Características da organização (100-200 palavras): funcionamento, ideais centrais, estilo de atuação",
  "background": "História da organização (100-200 palavras): fundação, trajetória, eventos importantes",
  "appearance": "Manifestação externa (50-100 palavras): localização da sede, edifícios marcantes",
  "organization_type": "Tipo de organização",
  "organization_purpose": "Propósito da organização",
  "organization_members": ["Membro 1", "Membro 2"],
  "power_level": 85,
  "location": "Sede ou principal área de atuação",
  "motto": "Lema, divisa ou missão da organização",
  "color": "Cor que a representa",
  "traits": []
}}

【Referência de tipos de relação】
- Família: pai, mãe, irmão, irmã, filho(a), cônjuge, namorado(a)
- Social: mestre, aprendiz, amigo, colega de escola, colega de trabalho, vizinho, confidente
- Profissional: chefe, subordinado, parceiro de negócios
- Hostil: inimigo, desafeto, concorrente, arqui-inimigo

【Faixas de valores】
- intimacy_level: de -100 a 100 (valores negativos indicam hostilidade)
- loyalty: de 0 a 100
- rank: de 0 a 10 (nível do cargo)
- power_level: de 70 a 95 (influência da organização)
</output>

<constraints>
【Obrigatório】
✅ Quantidade exata: o array deve conter {count} objetos
✅ Coerência com o mundo: personagens alinhados à ambientação
✅ Profundidade: personalidade e história tridimensionais
✅ Rede de relações: os personagens formam relações plausíveis entre si
✅ Organizações plausíveis: organizações são forças que movem a trama
✅ Todo o conteúdo em {output_language}

【Restrições de relações】
✅ relationships_array só pode citar personagens que já apareceram neste lote
✅ organization_memberships só pode citar organizações deste lote
✅ O relationships_array do primeiro personagem deve ser []
✅ Sem alucinações: não cite personagens ou organizações inexistentes

【Restrições de formato】
✅ Saída em array JSON puro, sem marcação markdown
✅ Nas descrições, é proibido usar símbolos especiais (aspas, colchetes, etc.)
✅ Escreva nomes próprios diretamente, sem envolvê-los em símbolos

【Proibido】
❌ Quantidade diferente de {count} (a mais ou a menos)
❌ Citar personagens ou organizações inexistentes
❌ Gerar organizações irrelevantes e de pouca influência
❌ Usar marcação markdown ou blocos de código
❌ Usar símbolos especiais nas descrições
</constraints>"""

# Personagem único V2 (framework RTCO)
SINGLE_CHARACTER_GENERATION = """<system>
Você é um criador de personagens profissional, especialista em construir personagens ricos e tridimensionais para romances.
</system>

<task>
【Tarefa de design】
Com base no pedido do usuário e no contexto do projeto, crie uma ficha de personagem completa.
</task>

<context priority="P0">
【Contexto do projeto】
{project_context}

【Pedido do usuário】
{user_input}
</context>

<output priority="P0">
【Formato de saída】
Gere um objeto JSON com a ficha completa do personagem:

{{
  "name": "Nome do personagem (se o usuário não informar, gere um nome coerente com o mundo)",
  "age": "Idade (número exato ou faixa etária)",
  "gender": "masculino/feminino/outro",
  "appearance": "Aparência (100-150 palavras): altura e porte, traços do rosto, estilo de roupa",
  "personality": "Personalidade (150-200 palavras): traços centrais, qualidades e defeitos, manias",
  "background": "História de vida (200-300 palavras): origem familiar, trajetória, viradas importantes, ligação com o tema",
  "traits": ["Talento 1", "Talento 2", "Talento 3"],
  "relationships_text": "Descrição em linguagem natural das relações pessoais",
  "relationships": [
    {{
      "target_character_name": "Nome de um personagem existente",
      "relationship_type": "Tipo de relação",
      "intimacy_level": 75,
      "description": "Descrição detalhada da relação",
      "started_at": "Momento da história em que a relação começou (opcional)"
    }}
  ],
  "organization_memberships": [
    {{
      "organization_name": "Nome de uma organização existente",
      "position": "Nome do cargo",
      "rank": 8,
      "loyalty": 80,
      "joined_at": "Momento da entrada (opcional)",
      "status": "active"
    }}
  ],
  "career_info": {{
    "main_career_name": "Nome da carreira escolhido na lista de carreiras principais disponíveis",
    "main_career_stage": 5,
    "sub_careers": [
      {{
        "career_name": "Nome da carreira escolhido na lista de carreiras secundárias disponíveis",
        "stage": 3
      }}
    ]
  }}
}}

【Informações de carreira】
Se o contexto do projeto incluir uma lista de carreiras:
- Carreira principal: escolha, na lista de carreiras principais disponíveis, a que melhor combina com o personagem
- Estágio da carreira principal: defina um estágio coerente com a força do personagem (de 1 até max_stage)
- Carreiras secundárias: pode escolher de 0 a 2
- ⚠️ Preencha o nome da carreira, não o ID; o sistema faz a correspondência automaticamente
- A escolha deve combinar muito bem com a história, as habilidades e o papel do personagem

【Referência de tipos de relação】
- Família: pai, mãe, irmão, irmã, filho(a), cônjuge, namorado(a)
- Social: mestre, aprendiz, amigo, colega de escola, colega de trabalho, vizinho, confidente
- Profissional: chefe, subordinado, parceiro de negócios
- Hostil: inimigo, desafeto, concorrente, arqui-inimigo

【Faixas de valores】
- intimacy_level: de -100 a 100 (valores negativos indicam hostilidade)
- loyalty: de 0 a 100
- rank: de 0 a 10

Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
【Obrigatório】
✅ Coerência com o mundo: a ficha deve estar alinhada ao mundo do projeto
✅ Ligação com o tema: a história de vida se relaciona com o tema do projeto
✅ Tridimensionalidade: personalidade complexa e contraditória, sem estereótipos
✅ Serve à história: a ficha deve impulsionar a trama
✅ Carreira adequada: a carreira escolhida combina muito bem com o personagem
✅ Todo o conteúdo em {output_language}

【Papel do personagem】
✅ Protagonista: tem espaço para crescer, além de objetivo e motivação
✅ Antagonista: tem motivação plausível, sem ser caricato
✅ Coadjuvante: tem singularidade, não é mero instrumento da trama

【Restrições de relações】
✅ relationships só cita personagens existentes
✅ organization_memberships só cita organizações existentes
✅ Sem relações ou organizações, o array correspondente fica vazio []

【Restrições de formato】
✅ Saída em objeto JSON puro, sem marcação markdown
✅ Nas descrições, é proibido usar símbolos especiais
✅ Escreva nomes próprios diretamente

【Proibido】
❌ Gerar marcação markdown ou blocos de código
❌ Usar símbolos especiais nas descrições (aspas, colchetes, etc.)
❌ Citar personagens ou organizações inexistentes
❌ Criar personagens caricatos ou estereotipados
</constraints>"""

# Organização única V2 (framework RTCO)
SINGLE_ORGANIZATION_GENERATION = """<system>
Você é um designer de organizações profissional, especialista em criar organizações e facções completas.
</system>

<task>
【Tarefa de design】
Com base no pedido do usuário e no contexto do projeto, crie a ficha completa de uma organização ou facção.
</task>

<context priority="P0">
【Contexto do projeto】
{project_context}

【Pedido do usuário】
{user_input}
</context>

<output priority="P0">
【Formato de saída】
Gere um objeto JSON com a ficha completa da organização:

{{
  "name": "Nome da organização (se o usuário não informar, gere um nome coerente com o mundo)",
  "is_organization": true,
  "organization_type": "Tipo de organização (gangue, empresa, ordem, academia, órgão governamental, organização religiosa, etc.)",
  "personality": "Características da organização (150-200 palavras): ideais centrais, estilo de atuação, cultura e valores, funcionamento",
  "background": "História da organização (200-300 palavras): fundação, trajetória, eventos importantes, posição atual",
  "appearance": "Manifestação externa (100-150 palavras): localização da sede, edifícios marcantes, emblema, uniformes, etc.",
  "organization_purpose": "Propósito e missão da organização: objetivos claros, visão de longo prazo, princípios de ação",
  "power_level": 75,
  "location": "Localização: principal área de atuação, esfera de influência",
  "motto": "Lema ou divisa da organização",
  "traits": ["Característica 1", "Característica 2", "Característica 3"],
  "color": "Cor que representa a organização (por exemplo: vermelho escuro, dourado, preto, etc.)",
  "organization_members": ["Membro importante 1", "Membro importante 2", "Membro importante 3"]
}}

【Descrição dos campos】
- power_level: inteiro de 0 a 100, indica a influência no mundo
- organization_members: lista de nomes dos membros importantes (pode se ligar a personagens existentes)
- Data de fundação: descreva dentro de background

Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
【Obrigatório】
✅ Coerência com o mundo: a organização deve estar alinhada ao mundo do projeto
✅ Ligação com o tema: a história se relaciona com o tema do projeto
✅ Move a trama: a organização deve impulsionar a história
✅ Estrutura hierárquica: níveis e estrutura internos bem definidos
✅ Interação entre forças: relações com outras facções
✅ Todo o conteúdo em {output_language}

【Papel da organização】
✅ Necessária: não é um mero cenário dispensável
✅ Objetivos plausíveis: nem idealizados demais nem caricatos
✅ Detalhes concretos: descrição específica, sem generalidades

【Restrições de formato】
✅ Saída em objeto JSON puro, sem marcação markdown
✅ Nas descrições, é proibido usar símbolos especiais
✅ Escreva nomes próprios diretamente

【Proibido】
❌ Gerar marcação markdown ou blocos de código
❌ Usar símbolos especiais nas descrições (aspas, colchetes, etc.)
❌ Criar organizações idealizadas demais ou caricatas
❌ Descrições vagas
</constraints>"""

# Pesquisa MCP para personagens
MCP_CHARACTER_PLANNING = """Você está desenvolvendo os personagens do livro "{title}".

【Informações do livro】
- Gênero: {genre}
- Tema: {theme}
- Época: {time_period}
- Local: {location}

【Tarefa】
Use as ferramentas disponíveis para pesquisar material de referência e criar personagens mais verossímeis e mais profundos.
Você pode consultar:
1. Características de figuras históricas reais dessa época ou região
2. Contexto cultural e costumes sociais
3. Particularidades das profissões e modos de vida
4. Arquétipos de personagens da área envolvida

Faça apenas a consulta mais importante (no máximo 1 pergunta).

Escreva todo o conteúdo em {output_language}."""

# Introdução automática de personagens - análise preditiva V2 (framework RTCO)
AUTO_CHARACTER_ANALYSIS = """<system>
Você é um consultor de design de personagens para romances, especialista em prever as necessidades de personagens geradas pelo rumo da trama.
</system>

<task>
【Tarefa de análise】
Preveja se, nos próximos {chapter_count} capítulos a serem escritos, será preciso introduzir novos personagens, de acordo com a direção e a fase da trama.

【Observação importante】
Esta é uma análise preditiva, e não uma análise posterior de conteúdo já gerado.
</task>

<project priority="P1">
【Informações do projeto】
Título: {title}
Gênero: {genre}
Tema: {theme}

【Mundo】
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
</project>

<context priority="P0">
【Personagens existentes】
{existing_characters}

【Visão geral dos capítulos existentes】
{all_chapters_brief}

【Plano de continuação】
- Capítulo inicial: capítulo {start_chapter}
- Quantidade a escrever: {chapter_count} capítulos
- Fase da trama: {plot_stage}
- Direção da história: {story_direction}
</context>

<analysis_framework priority="P0">
【Dimensões da análise preditiva】

**1. Necessidades da trama**
Pela direção da história, quais cenas e conflitos exigem novos personagens?

**2. Suficiência do elenco**
Os personagens atuais bastam para sustentar o que vai acontecer?

**3. Momento da entrada**
Em qual capítulo cada novo personagem deve aparecer?

**4. Grau de importância**
Qual será o impacto do novo personagem na trama a seguir?

【Bases da previsão】
- Necessidades típicas de personagens em cada fase da trama (por exemplo: no clímax pode ser preciso um oponente forte)
- Necessidades lógicas da direção da história (por exemplo: ao chegar a um novo lugar, são necessários personagens locais)
- Necessidades da escalada do conflito (por exemplo: um vilão mais forte, um aliado inesperado)
- Necessidades de expansão do mundo (por exemplo: representantes de novas organizações e forças)
</analysis_framework>

<output priority="P0">
【Formato de saída】
Retorne um objeto JSON puro (um dos dois casos):

**Caso A: são necessários novos personagens**
{{
  "needs_new_characters": true,
  "reason": "Motivo da previsão (150-200 palavras), explicando por que a trama que vem exige novos personagens",
  "character_count": 2,
  "character_specifications": [
    {{
      "name": "Nome sugerido para o personagem (opcional)",
      "role_description": "Posição e função do personagem na trama (100-150 palavras)",
      "suggested_role_type": "supporting/antagonist/protagonist",
      "importance": "high/medium/low",
      "appearance_chapter": {start_chapter},
      "key_abilities": ["Habilidade 1", "Habilidade 2"],
      "plot_function": "Função específica na trama",
      "relationship_suggestions": [
        {{
          "target_character": "Nome de um personagem existente",
          "relationship_type": "Tipo de relação sugerido",
          "reason": "Por que estabelecer essa relação"
        }}
      ]
    }}
  ]
}}

**Caso B: não são necessários novos personagens**
{{
  "needs_new_characters": false,
  "reason": "Os personagens atuais bastam para sustentar a trama que vem; explique o motivo"
}}

Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
【Obrigatório】
✅ É uma análise preditiva, voltada para a trama futura
✅ Considere o desenvolvimento natural e o ritmo da trama
✅ Garanta a necessidade da entrada, sem introduzir só por introduzir
✅ Dê prioridade ao papel de longo prazo do personagem
✅ Todo o conteúdo em {output_language}

【Proibido】
❌ Gerar marcação markdown
❌ Fazer análise posterior com base em conteúdo já gerado
❌ Forçar a entrada de um personagem sem necessidade
❌ Projetar personagens de função única e descartável
</constraints>"""

# Introdução automática de personagens - geração V2 (framework RTCO)
AUTO_CHARACTER_GENERATION = """<system>
Você é um criador de personagens profissional, especialista em criar fichas completas a partir das necessidades da trama.
</system>

<task>
【Tarefa de geração】
Gere a ficha completa de um novo personagem para o romance, incluindo dados básicos, personalidade e história, rede de relações e informações de carreira.
</task>

<project priority="P1">
【Informações do projeto】
Título: {title}
Gênero: {genre}
Tema: {theme}

【Mundo】
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
Regras do mundo: {rules}
</project>

<context priority="P0">
【Personagens existentes】
{existing_characters}

【Contexto da trama】
{plot_context}

【Especificação do personagem】
{character_specification}
</context>

<mcp_context priority="P2">
【Referências das ferramentas MCP】
{mcp_references}
</mcp_context>

<requirements priority="P0">
【Requisitos centrais】
1. O personagem deve atender às necessidades da trama e à ambientação do mundo
2. **É obrigatório analisar a relação do novo personagem com os existentes**, estabelecendo pelo menos 1 a 3 relações significativas
3. Personalidade e história devem ter profundidade e singularidade
4. A descrição da aparência deve ser concreta e vívida
5. Talentos e habilidades devem combinar com o papel do personagem
6. **Se a seção 【Personagens existentes】 trouxer uma lista de carreiras, é obrigatório definir uma carreira para o personagem**
7. Escreva todo o conteúdo em {output_language}

【Orientação para estabelecer relações】
- Examine com atenção a lista de 【Personagens existentes】 e pense com quais deles o novo personagem se conecta
- Estabeleça relações plausíveis conforme as necessidades da trama
- Cada relação precisa de tipo, grau de intimidade e descrição claros
- As relações devem servir ao desenvolvimento da trama
- Se o novo personagem for membro de uma organização, não se esqueça de preencher organization_memberships

【Requisitos de carreira】
Se a seção 【Personagens existentes】 contiver a "Lista de carreiras principais disponíveis" ou a "Lista de carreiras secundárias disponíveis":
- Examine com atenção as listas de carreiras principais e secundárias disponíveis
- Escolha a carreira mais adequada conforme a história, as habilidades e o papel do personagem na trama
- Carreira principal: escolha uma da "Lista de carreiras principais disponíveis" e preencha o nome
- Estágio da carreira principal: defina um estágio atual coerente com as informações de estágio da carreira e a força do personagem
- Carreiras secundárias: pode escolher de 0 a 2
- ⚠️ Importante: preencha o nome da carreira, nunca o ID
</requirements>

<output priority="P0">
【Formato de saída】
Retorne um objeto JSON puro:

{{
  "name": "Nome do personagem",
  "age": 25,
  "gender": "masculino/feminino/outro",
  "role_type": "supporting",
  "personality": "Descrição detalhada da personalidade (100-200 palavras)",
  "background": "Descrição detalhada da história de vida (100-200 palavras)",
  "appearance": "Descrição da aparência (50-100 palavras)",
  "traits": ["Talento 1", "Talento 2", "Talento 3"],
  "relationships_text": "Descrição em linguagem natural da rede de relações do personagem com os demais",
  
  "relationships": [
    {{
      "target_character_name": "Nome de um personagem existente",
      "relationship_type": "Tipo de relação",
      "intimacy_level": 75,
      "description": "Descrição específica da relação",
      "status": "active"
    }}
  ],
  "organization_memberships": [
    {{
      "organization_name": "Nome de uma organização existente",
      "position": "Cargo",
      "rank": 5,
      "loyalty": 80
    }}
  ],
  
  "career_info": {{
    "main_career_name": "Nome da carreira escolhido na lista de carreiras principais disponíveis",
    "main_career_stage": 5,
    "sub_careers": [
      {{
        "career_name": "Nome da carreira escolhido na lista de carreiras secundárias disponíveis",
        "stage": 3
      }}
    ]
  }}
}}

【Referência de tipos de relação】
Relações familiares, sociais, profissionais, hostis e de outros tipos

【Faixas de valores】
- intimacy_level: de -100 a 100 (valores negativos indicam hostilidade)
- loyalty: de 0 a 100
- rank: de 0 a 10
</output>

<constraints>
【Obrigatório】
✅ Atender às necessidades da trama e à ambientação do mundo
✅ O array relationships é obrigatório: pelo menos 1 a 3 relações
✅ target_character_name deve corresponder exatamente a um nome em 【Personagens existentes】
✅ organization_memberships só pode citar organizações existentes
✅ A carreira deve ser escolhida entre as listas disponíveis
✅ Todo o conteúdo em {output_language}

【Proibido】
❌ Gerar marcação markdown
❌ Usar símbolos especiais nas descrições
❌ Citar personagens ou organizações inexistentes
❌ Usar o ID da carreira em vez do nome
</constraints>"""

# Introdução automática de organizações - análise preditiva (framework RTCO)
AUTO_ORGANIZATION_ANALYSIS = """<system>
Você é um consultor de construção de mundos para romances, especialista em prever as necessidades de organizações e facções geradas pelo rumo da trama.
</system>

<task>
【Tarefa de análise】
Preveja se, nos próximos {chapter_count} capítulos a serem escritos, será preciso introduzir novas organizações ou facções, de acordo com a direção e a fase da trama.

【Observação importante】
Esta é uma análise preditiva, e não uma análise posterior de conteúdo já gerado.
Organizações incluem: gangues, ordens, empresas, órgãos governamentais, grupos misteriosos, famílias, etc.
</task>

<project priority="P1">
【Informações do projeto】
Título: {title}
Gênero: {genre}
Tema: {theme}

【Mundo】
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
</project>

<context priority="P0">
【Organizações existentes】
{existing_organizations}

【Personagens existentes】
{existing_characters}

【Visão geral dos capítulos existentes】
{all_chapters_brief}

【Plano de continuação】
- Capítulo inicial: capítulo {start_chapter}
- Quantidade a escrever: {chapter_count} capítulos
- Fase da trama: {plot_stage}
- Direção da história: {story_direction}
</context>

<analysis_framework priority="P0">
【Dimensões da análise preditiva】

**1. Necessidade de expandir o mundo**
Pela direção da história, são necessárias novas forças ou organizações para enriquecer o mundo?

**2. Necessidade de escalar o conflito**
A trama precisa de novas forças opostas, organizações rivais ou grupos misteriosos?

**3. Necessidade de pertencimento dos personagens**
Algum personagem atual precisa entrar em uma nova organização ou combatê-la?

**4. Necessidade de impulsionar a trama**
A nova organização pode se tornar uma força decisiva para a história?

**5. Momento da entrada**
Em qual capítulo a nova organização deve aparecer?

【Bases da previsão】
- Necessidades típicas de organizações em cada fase da trama (por exemplo: no clímax pode ser preciso uma força hostil poderosa)
- Necessidades lógicas da direção da história (por exemplo: ao chegar a um novo lugar, são necessárias forças locais)
- Necessidade de completude do mundo (por exemplo: o equilíbrio de poder exige várias forças)
- Necessidades do crescimento dos personagens (por exemplo: o protagonista precisa entrar em uma organização ou criar uma)
</analysis_framework>

<output priority="P0">
【Formato de saída】
Retorne um objeto JSON puro (um dos dois casos):

**Caso A: são necessárias novas organizações**
{{
"needs_new_organizations": true,
"reason": "Motivo da previsão (150-200 palavras), explicando por que a trama que vem exige novas organizações",
"organization_count": 1,
"organization_specifications": [
{{
  "name": "Nome sugerido para a organização (opcional)",
  "organization_description": "Posição e função da organização na trama (100-150 palavras)",
  "organization_type": "gangue/ordem/empresa/governo/família/organização misteriosa, etc.",
  "importance": "high/medium/low",
  "appearance_chapter": {start_chapter},
  "power_level": 70,
  "plot_function": "Função específica na trama",
  "location": "Sede ou área de atuação da organização",
  "motto": "Lema ou missão da organização (opcional)",
  "initial_members": [
    {{
      "character_name": "Nome de um personagem existente (se for entrar)",
      "position": "Cargo",
      "reason": "Por que entra"
    }}
  ],
  "relationship_suggestions": [
    {{
      "target_organization": "Nome de uma organização existente",
      "relationship_type": "Tipo de relação sugerido (aliada/hostil/rival/cooperação, etc.)",
      "reason": "Por que estabelecer essa relação"
    }}
  ]
}}
]
}}

**Caso B: não são necessárias novas organizações**
{{
"needs_new_organizations": false,
"reason": "As organizações atuais bastam para sustentar a trama que vem; explique o motivo"
}}

Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
【Obrigatório】
✅ É uma análise preditiva, voltada para a trama futura
✅ Considere a riqueza e a completude do mundo
✅ Garanta a necessidade da entrada, sem introduzir só por introduzir
✅ Dê prioridade ao papel de longo prazo da organização
✅ A organização deve ser uma força que impulsiona a trama
✅ Todo o conteúdo em {output_language}

【Proibido】
❌ Gerar marcação markdown
❌ Fazer análise posterior com base em conteúdo já gerado
❌ Forçar a entrada de uma organização sem necessidade
❌ Projetar organizações de função única e descartável
❌ Criar organizações que repitam a função das existentes
</constraints>"""

# Introdução automática de organizações - geração (framework RTCO)
AUTO_ORGANIZATION_GENERATION = """<system>
Você é um construtor de mundos profissional, especialista em criar fichas completas de organizações e facções a partir das necessidades da trama.
</system>

<task>
【Tarefa de geração】
Gere a ficha completa de uma nova organização para o romance, incluindo dados básicos, características, história e estrutura de membros.
</task>

<project priority="P1">
【Informações do projeto】
Título: {title}
Gênero: {genre}
Tema: {theme}

【Mundo】
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
Regras do mundo: {rules}
</project>

<context priority="P0">
【Organizações existentes】
{existing_organizations}

【Personagens existentes】
{existing_characters}

【Contexto da trama】
{plot_context}

【Especificação da organização】
{organization_specification}
</context>

<mcp_context priority="P2">
【Referências das ferramentas MCP】
{mcp_references}
</mcp_context>

<requirements priority="P0">
【Requisitos centrais】
1. A organização deve atender às necessidades da trama e à ambientação do mundo
2. A organização precisa de propósito, estrutura e identidade claros
3. Características e história devem ter profundidade e singularidade
4. A manifestação externa deve ser concreta e vívida
5. Considere a relação e a interação com as organizações existentes
6. Se necessário, sugira a entrada de personagens existentes na organização
7. Escreva todo o conteúdo em {output_language}
</requirements>

<output priority="P0">
【Formato de saída】
Retorne um objeto JSON puro:

{{
"name": "Nome da organização",
"is_organization": true,
"role_type": "supporting",
"organization_type": "Tipo de organização (gangue/ordem/empresa/governo/família/organização misteriosa, etc.)",
"personality": "Descrição detalhada das características da organização (150-200 palavras): funcionamento, ideais centrais, estilo de atuação, cultura e valores",
"background": "História da organização (200-300 palavras): fundação, trajetória, eventos importantes, posição atual",
"appearance": "Manifestação externa (100-150 palavras): localização da sede, edifícios marcantes, emblema, vestimenta dos membros",
"organization_purpose": "Propósito e missão da organização: objetivos claros, visão de longo prazo, princípios de ação",
"power_level": 75,
"location": "Localização: principal área de atuação, esfera de influência",
"motto": "Lema ou divisa da organização",
"color": "Cor que representa a organização",
"traits": ["Característica 1", "Característica 2", "Característica 3"],

"initial_members": [
{{
  "character_name": "Nome de um personagem existente",
  "position": "Nome do cargo",
  "rank": 8,
  "loyalty": 80,
  "joined_at": "Momento da entrada (opcional)",
  "status": "active"
}}
],

"organization_relationships": [
{{
  "target_organization_name": "Nome de uma organização existente",
  "relationship_type": "aliada/hostil/rival/cooperação/subordinada, etc.",
  "description": "Descrição específica da relação"
}}
]
}}

【Faixas de valores】
- power_level: inteiro de 0 a 100, indica a influência no mundo
- rank: de 0 a 10 (nível do cargo)
- loyalty: de 0 a 100 (lealdade do membro)
</output>

<constraints>
【Obrigatório】
✅ Atender às necessidades da trama e à ambientação do mundo
✅ A organização deve ter posicionamento e valor únicos
✅ character_name deve corresponder exatamente a um nome em 【Personagens existentes】
✅ target_organization_name deve corresponder exatamente a um nome em 【Organizações existentes】
✅ A organização deve impulsionar a trama
✅ Todo o conteúdo em {output_language}

【Proibido】
❌ Gerar marcação markdown
❌ Usar símbolos especiais nas descrições
❌ Citar personagens ou organizações inexistentes
❌ Criar organizações que repitam a função das existentes
❌ Criar organizações sem nenhum papel real na trama
</constraints>"""
