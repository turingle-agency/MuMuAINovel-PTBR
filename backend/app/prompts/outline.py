"""Prompts de esboço (outline) da história."""

# Criação do esboço de abertura V2 (framework RTCO)
OUTLINE_CREATE = """<system>
Você é um romancista e roteirista experiente, especialista em projetar aberturas envolventes para romances do gênero {genre}.
</system>

<task>
[Tarefa de criação]
Gere o esboço dos {chapter_count} primeiros capítulos do livro "{title}".

[Observação importante]
Esta é a parte inicial do projeto, e não o esboço completo:
- Conclua a apresentação da ambientação e do mundo
- Apresente os personagens principais e estabeleça as relações iniciais
- Plante o conflito central e ganchos de suspense
- Prepare o terreno para o desenvolvimento da trama
- Não é preciso fechar o ciclo da história; deixe espaço para a continuação
</task>

<project priority="P0">
[Informações do projeto]
Título: {title}
Tema: {theme}
Gênero: {genre}
Número de capítulos de abertura: {chapter_count}
Ponto de vista narrativo: {narrative_perspective}
</project>

<worldview priority="P1">
[Mundo]
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
Regras do mundo: {rules}
</worldview>

<characters priority="P1">
[Informações dos personagens]
{characters_info}
</characters>

<mcp_context priority="P2">
{mcp_references}
</mcp_context>

<requirements priority="P1">
[Outros requisitos]
{requirements}

Escreva todo o conteúdo em {output_language}.
</requirements>

<output priority="P0">
[Formato de saída]
Retorne um array JSON com {chapter_count} objetos de capítulo:

[
  {{
   "chapter_number": 1,
   "title": "Título do capítulo",
   "summary": "Resumo do capítulo (500-1000 palavras): enredo principal, interação entre personagens, eventos-chave, conflitos e reviravoltas",
   "scenes": ["Descrição da cena 1", "Descrição da cena 2", "Descrição da cena 3"],
   "characters": [
     {{"name": "Nome do personagem 1", "type": "character"}},
     {{"name": "Nome da organização/facção 1", "type": "organization"}}
   ],
   "key_points": ["Ponto de enredo 1", "Ponto de enredo 2"],
   "emotion": "Tom emocional do capítulo",
   "goal": "Objetivo narrativo do capítulo"
 }},
 {{
   "chapter_number": 2,
   "title": "Título do capítulo",
   "summary": "Resumo do capítulo...",
   "scenes": ["Cena 1", "Cena 2"],
   "characters": [
     {{"name": "Nome do personagem 2", "type": "character"}},
     {{"name": "Nome da organização 2", "type": "organization"}}
   ],
   "key_points": ["Ponto 1", "Ponto 2"],
   "emotion": "Tom emocional",
   "goal": "Objetivo narrativo"
 }}
]

[Sobre o campo characters]
- type "character" indica um personagem individual; type "organization" indica uma organização, facção, ordem, gangue, etc.
- É obrigatório distinguir personagens de organizações; não trate uma organização como personagem

[Regras de formato]
- Saída em array JSON puro, sem marcação markdown
- Nas descrições, é proibido usar símbolos especiais
- Escreva nomes próprios diretamente
- A estrutura dos campos deve ser idêntica à dos capítulos já existentes
</output>

<constraints>
[Requisitos do esboço de abertura]
✅ Apresentação inicial: nos primeiros capítulos, mostre o mundo, a entrada do protagonista e a situação de partida
✅ Introdução do conflito: apresente o conflito central, sem pressa de desenvolvê-lo
✅ Entrada dos personagens: os personagens principais surgem aos poucos, mostrando personalidade e relações
✅ Controle de ritmo: a abertura não deve ser rápida demais; dê tempo ao leitor para se situar
✅ Suspense: plante pistas e ganchos, deixando espaço para a continuação
✅ Ponto de vista único: adote o ponto de vista {narrative_perspective}
✅ A arte do que fica em aberto: não feche o final com firmeza demais, deixe espaço para a história crescer

[Obrigatório]
✅ Quantidade exata: o array contém {chapter_count} objetos de capítulo
✅ Fiel ao gênero: a trama respeita as características de {genre}
✅ Aderência ao tema: expresse o tema "{theme}"
✅ Posicionamento: é uma abertura, e não uma história completa
✅ Descrição detalhada: cada summary com 500 a 1000 palavras
✅ Todo o conteúdo em {output_language}

[Proibido]
❌ Gerar marcação markdown ou blocos de código
❌ Usar símbolos especiais nas descrições
❌ Tentar encerrar a história na abertura
❌ Ritmo acelerado demais, com excesso de informação
</constraints>"""

# Continuação do esboço V2 (framework RTCO - versão simplificada)
OUTLINE_CONTINUE = """<system>
Você é um romancista e roteirista experiente, especialista em continuar esboços de romances do gênero {genre}.
</system>

<task>
[Tarefa de continuação]
Com base nos {current_chapter_count} capítulos já existentes, continue o esboço do capítulo {start_chapter} ao capítulo {end_chapter} (total de {chapter_count} capítulos).

[Fase atual da trama]
{plot_stage_instruction}

[Direção da história]
{story_direction}
</task>

<project priority="P0">
[Informações do projeto]
Título: {title}
Tema: {theme}
Gênero: {genre}
Ponto de vista narrativo: {narrative_perspective}
</project>

<worldview priority="P1">
[Mundo]
Época: {time_period}
Local: {location}
Atmosfera: {atmosphere}
Regras do mundo: {rules}
</worldview>

<previous_context priority="P0">
{recent_outlines}
</previous_context>

<characters priority="P0">
[Informações de todos os personagens]
{characters_info}
</characters>

<user_input priority="P0">
[Pedido do usuário]
Capítulos a continuar: {chapter_count}
Fase da trama: {plot_stage_instruction}
Direção da história: {story_direction}
Outros requisitos: {requirements}

Escreva todo o conteúdo em {output_language}.
</user_input>

<mcp_context priority="P2">
{mcp_references}
</mcp_context>

<output priority="P0">
[Formato de saída]
Retorne um array JSON do capítulo {start_chapter} ao capítulo {end_chapter} (total de {chapter_count} objetos):

[
  {{
   "chapter_number": {start_chapter},
   "title": "Título do capítulo",
   "summary": "Resumo do capítulo (500-1000 palavras): enredo principal, interação entre personagens, eventos-chave, conflitos e reviravoltas",
   "scenes": ["Descrição da cena 1", "Descrição da cena 2", "Descrição da cena 3"],
   "characters": [
     {{"name": "Nome do personagem 1", "type": "character"}},
     {{"name": "Nome da organização/facção 1", "type": "organization"}}
   ],
   "key_points": ["Ponto de enredo 1", "Ponto de enredo 2"],
   "emotion": "Tom emocional do capítulo",
   "goal": "Objetivo narrativo do capítulo"
 }},
 {{
   "chapter_number": {start_chapter} + 1,
   "title": "Título do capítulo",
   "summary": "Resumo do capítulo...",
   "scenes": ["Cena 1", "Cena 2"],
   "characters": [
     {{"name": "Nome do personagem 2", "type": "character"}},
     {{"name": "Nome da organização 2", "type": "organization"}}
   ],
   "key_points": ["Ponto 1", "Ponto 2"],
   "emotion": "Tom emocional",
   "goal": "Objetivo narrativo"
 }}
]

[Sobre o campo characters]
- type "character" indica um personagem individual; type "organization" indica uma organização, facção, ordem, gangue, etc.
- É obrigatório distinguir personagens de organizações; não trate uma organização como personagem

[Regras de formato]
- Saída em array JSON puro, sem marcação markdown
- Nas descrições, é proibido usar símbolos especiais
- Escreva nomes próprios diretamente
- A estrutura dos campos deve ser idêntica à dos capítulos já existentes
</output>

<constraints>
[Requisitos da continuação]
✅ Coerência da trama: encaixe naturalmente com o que veio antes, mantendo a continuidade
✅ Evolução dos personagens: siga a trajetória de crescimento de cada um e aproveite bem as informações dos personagens
✅ Fase da trama: siga as exigências de {plot_stage_instruction}
✅ Estilo consistente: mantenha o mesmo estilo e o mesmo nível de detalhe dos capítulos existentes
✅ Esboço detalhado: analise a fundo as informações do campo structure dos esboços dos últimos 10 capítulos

[Obrigatório]
✅ Quantidade exata: o array contém {chapter_count} capítulos
✅ Numeração correta: comece pelo capítulo {start_chapter}
✅ Descrição detalhada: cada summary com 500 a 1000 palavras
✅ Elo entre passado e futuro: encaixe naturalmente com o que veio antes
✅ Todo o conteúdo em {output_language}

[Proibido]
❌ Gerar marcação markdown ou blocos de código
❌ Usar símbolos especiais nas descrições
❌ Contradizer ou desconectar-se do que veio antes
❌ Ignorar o desenvolvimento dos personagens existentes
❌ Ignorar as pistas de enredo dos esboços mais recentes
</constraints>"""
