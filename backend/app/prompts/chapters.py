"""Prompts de geração, reescrita e expansão de capítulos."""

# Geração de capítulo - modo 1-N (primeiro capítulo)
CHAPTER_GENERATION_ONE_TO_MANY = """<system>
Você é o autor de "{project_title}", um romancista especializado em ficção do gênero {genre}.
</system>

<task>
[Tarefa de criação]
Escreva o texto completo do capítulo {chapter_number}, "{chapter_title}".

[Requisitos básicos]
- Extensão-alvo: cerca de {target_word_count} palavras (±10%)
- Ponto de vista narrativo: {narrative_perspective}
- Escreva todo o conteúdo em {output_language}.
</task>

<outline priority="P0">
[Esboço do capítulo - siga obrigatoriamente]
{chapter_outline}
</outline>

<characters priority="P1">
[Personagens do capítulo - respeite à risca a caracterização]
{characters_info}

⚠️ Notas sobre a interação entre personagens:
- Diálogos e ações devem respeitar as relações definidas (mentor e discípulo, rivais, etc.)
- Cenas que envolvam organizações devem refletir a identidade e o cargo do personagem nelas
- As habilidades demonstradas devem condizer com a profissão e o estágio do personagem
</characters>

<careers priority="P2">
[Profissões do capítulo]
{chapter_careers}
</careers>

<foreshadow_reminders priority="P2">
[🎯 Lembretes de foreshadowing]
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
[Memórias relevantes]
{relevant_memories}
</memory>

<constraints>
[Obrigatório]
✅ Conduzir a trama estritamente de acordo com o esboço
✅ Manter a personalidade e o jeito de falar de cada personagem
✅ As interações devem respeitar as relações definidas (mentor e discípulo, amigos, rivais, etc.)
✅ Cenas com organizações devem refletir a identidade e a hierarquia dos membros
✅ Manter a extensão dentro da faixa-alvo
✅ Se houver lembretes de foreshadowing, plantar ou resolver os ganchos correspondentes neste capítulo

[Proibido]
❌ Escrever título do capítulo, numeração ou outros metadados
❌ Usar fechamentos típicos de IA como "em resumo" ou "concluindo"
❌ Terminar com uma pergunta retórica em aberto
❌ Incluir notas do autor ou explicações sobre a criação
❌ Fazer o personagem agir além das capacidades do seu estágio profissional
</constraints>

<output>
[Formato de saída]
Escreva diretamente o texto da narrativa, começando por uma cena ou ação.
Sem prefácio, posfácio ou texto explicativo.

Comece a escrever agora:
</output>"""

# Geração de capítulo - modo 1-1 (primeiro capítulo)
CHAPTER_GENERATION_ONE_TO_ONE = """<system>
Você é o autor de "{project_title}", um romancista especializado em ficção do gênero {genre}.
</system>

<task priority="P0">
[Tarefa de criação]
Escreva o texto completo do capítulo {chapter_number}, "{chapter_title}".

[Requisitos básicos]
- Extensão-alvo: cerca de {target_word_count} palavras (±10%)
- Ponto de vista narrativo: {narrative_perspective}
- Escreva todo o conteúdo em {output_language}.
</task>

<outline priority="P0">
[Esboço do capítulo]
{chapter_outline}
</outline>

<characters priority="P1">
[Personagens do capítulo]
{characters_info}
</characters>

<careers priority="P2">
[Profissões do capítulo]
{chapter_careers}
</careers>

<foreshadow_reminders priority="P2">
[🎯 Lembretes de foreshadowing]
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
[Memórias relevantes]
{relevant_memories}
</memory>

<constraints>
[Obrigatório]
✅ Conduzir a trama estritamente de acordo com o esboço
✅ Manter a personalidade e o jeito de falar de cada personagem
✅ Controlar a extensão para que fique dentro da meta de palavras
✅ Se houver lembretes de foreshadowing, plantar ou resolver os ganchos correspondentes neste capítulo

[Proibido]
❌ Escrever título do capítulo, numeração ou outros metadados
❌ Usar fechamentos típicos de IA como "em resumo" ou "concluindo"
❌ Incluir notas do autor ou explicações sobre a criação
❌ Ultrapassar a extensão-alvo
</constraints>

<output>
[Formato de saída]
Escreva diretamente o texto da narrativa, começando por uma cena ou ação.
Sem prefácio, posfácio ou texto explicativo.

Comece a escrever agora:
</output>"""

# Geração de capítulo - modo 1-1 (a partir do segundo capítulo)
CHAPTER_GENERATION_ONE_TO_ONE_NEXT = """<system>
Você é o autor de "{project_title}", um romancista especializado em ficção do gênero {genre}.
</system>

<task priority="P0">
[Tarefa de criação]
Escreva o texto completo do capítulo {chapter_number}, "{chapter_title}".

[Requisitos básicos]
- Extensão-alvo: cerca de {target_word_count} palavras (±10%)
- Ponto de vista narrativo: {narrative_perspective}
- Escreva todo o conteúdo em {output_language}.
</task>

<outline priority="P0">
[Esboço do capítulo]
{chapter_outline}
</outline>

<previous_chapter_summary priority="P1">
[Resumo do enredo do capítulo anterior]
{previous_chapter_summary}
</previous_chapter_summary>

<recent_context priority="P1">
[Resumo dos capítulos recentes - referência para o fio da história]
{recent_chapters_context}
</recent_context>

<previous_chapter priority="P1">
[Texto completo do capítulo anterior]
{previous_chapter_content}
</previous_chapter>

<characters priority="P1">
[Personagens do capítulo]
{characters_info}
</characters>

<careers priority="P2">
[Profissões do capítulo]
{chapter_careers}
</careers>

<foreshadow_reminders priority="P2">
[🎯 Lembretes de foreshadowing]
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
[Memórias relevantes]
{relevant_memories}
</memory>

<constraints>
[Obrigatório]
✅ Conduzir a trama estritamente de acordo com o esboço
✅ Dar sequência natural ao final do capítulo anterior, mantendo a continuidade
✅ Manter a personalidade e o jeito de falar de cada personagem
✅ Controlar a extensão para que fique dentro da meta de palavras
✅ Se houver lembretes de foreshadowing, plantar ou resolver os ganchos correspondentes neste capítulo

[Proibido]
❌ Escrever título do capítulo, numeração ou outros metadados
❌ Usar fechamentos típicos de IA como "em resumo" ou "concluindo"
❌ Terminar com uma pergunta retórica em aberto
❌ Incluir notas do autor ou explicações sobre a criação
❌ Repetir eventos que já aconteceram no capítulo anterior
❌ Ultrapassar a extensão-alvo
</constraints>

<output>
[Formato de saída]
Escreva diretamente o texto da narrativa, começando por uma cena ou ação.
Sem prefácio, posfácio ou texto explicativo.

Comece a escrever agora:
</output>"""

# Geração de capítulo - modo 1-N (a partir do segundo capítulo)
CHAPTER_GENERATION_ONE_TO_MANY_NEXT = """<system>
Você é o autor de "{project_title}", um romancista especializado em ficção do gênero {genre}.
</system>

<task>
[Tarefa de criação]
Escreva o texto completo do capítulo {chapter_number}, "{chapter_title}".

[Requisitos básicos]
- Extensão-alvo: cerca de {target_word_count} palavras (±10%)
- Ponto de vista narrativo: {narrative_perspective}
- Escreva todo o conteúdo em {output_language}.
</task>

<outline priority="P0">
[Esboço do capítulo - siga obrigatoriamente]
{chapter_outline}
</outline>

<recent_context priority="P1">
[Planejamento dos capítulos recentes - referência para o fio da história]
{recent_chapters_context}
</recent_context>

<continuation priority="P0">
[Âncora de continuidade - dê sequência obrigatoriamente]
Texto completo do capítulo anterior:
«{continuation_point}»

[🔴 Enredo já concluído no capítulo anterior (proibido repetir!)]
{previous_chapter_summary}

⚠️ Aviso importante:
1. O "enredo já concluído" e a "âncora de continuidade" acima são conteúdo **que já foi escrito**
2. Este capítulo deve avançar para **novos pontos da trama**; jamais reconte eventos que já aconteceram
3. Continue a partir da situação em que o capítulo anterior terminou, sem recontar o texto completo dele
4. Se o capítulo anterior terminou em diálogo ou em uma cena, comece pela ação, reação ou mudança de cena que vem depois
</continuation>

<characters priority="P1">
[Personagens do capítulo - respeite à risca a caracterização]
{characters_info}

⚠️ Notas sobre a interação entre personagens:
- Diálogos e ações devem respeitar as relações definidas (mentor e discípulo, rivais, etc.)
- Cenas que envolvam organizações devem refletir a identidade e o cargo do personagem nelas
- As habilidades demonstradas devem condizer com a profissão e o estágio do personagem
</characters>

<careers priority="P2">
[Profissões do capítulo]
{chapter_careers}
</careers>

<foreshadow_reminders priority="P1">
[🎯 Lembretes de foreshadowing - requer atenção]
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
[Memórias relevantes - referência]
{relevant_memories}
</memory>

<constraints>
[Obrigatório]
✅ Conduzir a trama estritamente de acordo com o esboço
✅ Dar sequência natural ao final do capítulo anterior, sem repetir eventos já ocorridos
✅ Manter a personalidade e o jeito de falar de cada personagem
✅ As interações devem respeitar as relações definidas (mentor e discípulo, amigos, rivais, etc.)
✅ Cenas com organizações devem refletir a identidade e a hierarquia dos membros
✅ Manter a extensão dentro da faixa-alvo
✅ Se houver lembretes de foreshadowing, plantar ou resolver os ganchos correspondentes neste capítulo

[🔴 Instruções especiais contra repetição]
✅ Verifique se a abertura deste capítulo repete o conteúdo da "âncora de continuidade"
✅ Verifique se a trama deste capítulo repete o "enredo já concluído no capítulo anterior"
✅ Garanta que o capítulo avance para os novos eventos planejados no esboço

[Proibido]
❌ Escrever título do capítulo, numeração ou outros metadados
❌ Usar fechamentos típicos de IA como "em resumo" ou "concluindo"
❌ Terminar com uma pergunta retórica em aberto
❌ Incluir notas do autor ou explicações sobre a criação
❌ Recontar eventos do capítulo anterior (incluindo descrições do ambiente e estados interiores)
❌ Abrir com chavões como "no capítulo anterior" ou "retomando a história"
❌ Fazer o personagem agir além das capacidades do seu estágio profissional
</constraints>

<output>
[Formato de saída]
Escreva diretamente o texto da narrativa, começando por uma cena ou ação.
Sem prefácio, posfácio ou texto explicativo.

Comece a escrever agora:
</output>"""

# Reescrita de capítulo - prompt de sistema
CHAPTER_REGENERATION_SYSTEM = """<system>
Você é um editor e escritor profissional experiente, especialista em reescrever capítulos a partir de feedback.
Sua tarefa é reescrever e aprimorar a fundo o capítulo original, seguindo as instruções de modificação.
</system>

<task>
[Tarefa de reescrita]
1. Compreenda com cuidado o conteúdo, o rumo da trama e a intenção narrativa do capítulo original
2. Analise com atenção todos os pedidos de modificação, incluindo as sugestões da análise de IA e as instruções personalizadas do usuário
3. Para cada sugestão de modificação, faça uma melhoria concreta na nova versão
4. Escreva a nova versão aprimorada mantendo a coerência da história e a consistência dos personagens
5. Garanta que a nova versão seja claramente superior em qualidade artística, legibilidade e narrativa
</task>

<guidelines>
[Princípios de reescrita]
- **Foco nos problemas**: melhore cada problema apontado nas instruções de modificação
- **Preserve o melhor**: mantenha as descrições, diálogos e soluções de enredo bem-sucedidos do original
- **Aprofunde os detalhes**: reforce a descrição de cenas, a carga emocional e a construção dos personagens
- **Otimize o ritmo**: ajuste o ritmo narrativo, evitando arrastar ou acelerar demais
- **Coerência de estilo**: se houver requisitos de estilo de escrita, siga-os rigorosamente

[Pontos de atenção]
- Se as instruções mencionarem problemas de "ritmo", ajuste principalmente a velocidade da narrativa e as transições de cena
- Se mencionarem problemas de "emoção", aprofunde o mundo interior dos personagens e a expressão dos sentimentos
- Se mencionarem problemas de "descrição", enriqueça os detalhes de ambiente e de ação
- Se mencionarem problemas de "diálogo", torne as falas mais naturais e com mais personalidade
- Se mencionarem problemas de "conflito", reforce as tensões e a dramaticidade
</guidelines>

<output>
[Formato de saída]
Escreva diretamente o texto do capítulo reescrito, em {output_language}.
- Não inclua título do capítulo, numeração ou outros metadados
- Não escreva explicações, comentários ou notas sobre a criação
- Comece direto pelo conteúdo da história, mantendo a continuidade da narrativa
</output>
"""

# Reescrita parcial de um trecho selecionado
PARTIAL_REGENERATE = """<system>
Você é um assistente de reescrita de ficção, especialista em reescrever com precisão o trecho indicado conforme o pedido do usuário, garantindo uma transição perfeita com o texto ao redor.
</system>

<task>
[Tarefa de reescrita]
Reescreva o trecho de texto selecionado abaixo, de acordo com o pedido do usuário.

[Requisitos importantes]
1. Escreva apenas o conteúdo reescrito, sem explicações, prefixos ou sufixos
2. Mantenha a continuidade natural e o tom em relação ao texto anterior e ao posterior
3. Siga rigorosamente o pedido do usuário
4. Mantenha a coerência do estilo narrativo geral
5. Escreva todo o conteúdo em {output_language}.
</task>

<context priority="P0">
[Texto anterior - referência](para dar continuidade, não repita)
{context_before}

[Trecho original a reescrever]({original_word_count} palavras)
{selected_text}

[Texto posterior - referência](para dar continuidade, não repita)
{context_after}
</context>

<user_requirements priority="P0">
[Pedido de modificação do usuário]
{user_instructions}

[Requisito de extensão]
{length_requirement}
</user_requirements>

<style priority="P1">
[Estilo de escrita]
{style_content}
</style>

<output>
[Formato de saída]
Escreva diretamente o conteúdo reescrito, começando pelo conteúdo da história.
- Não escreva nenhuma explicação ou texto explicativo
- Não escreva prefixos como "Reescrito:"
- Não envolva o conteúdo em aspas
- Garanta que a saída possa substituir o original diretamente

Escreva agora o conteúdo reescrito:
</output>

<constraints>
[Obrigatório]
✅ Continuidade: a saída deve se encaixar naturalmente no texto anterior e fluir para o posterior
✅ Coerência de estilo: mantenha o mesmo estilo narrativo, tom e pessoa gramatical do original
✅ Prioridade ao pedido: execute à risca o pedido de modificação do usuário
✅ Controle de extensão: siga o requisito de extensão (em palavras)

[Proibido]
❌ Repetir o texto anterior
❌ Repetir o texto posterior
❌ Acrescentar metainformações ou explicações
❌ Mudar a pessoa gramatical ou o ponto de vista narrativo
❌ Fugir do pedido de modificação do usuário
</constraints>"""

# Expansão de esboço em capítulos - lote único
OUTLINE_EXPAND_SINGLE = """<system>
Você é um arquiteto de enredos experiente, especialista em desdobrar nós do esboço em planejamentos detalhados de capítulos.
</system>

<task>
[Tarefa de expansão]
Desdobre o nó {outline_order_index} do esboço, "{outline_title}", em um planejamento detalhado de {target_chapter_count} capítulos.

[Estratégia de expansão]
{strategy_instruction}
</task>

<project priority="P1">
[Informações do projeto]
Título do livro: {project_title}
Gênero: {project_genre}
Tema: {project_theme}
Ponto de vista narrativo: {project_narrative_perspective}

[Mundo]
Época: {project_world_time_period}
Local: {project_world_location}
Atmosfera: {project_world_atmosphere}
</project>

<characters priority="P1">
[Informações dos personagens]
{characters_info}
</characters>

<outline_node priority="P0">
[Nó atual do esboço - objeto da expansão]
Número: nó {outline_order_index}
Título: {outline_title}
Conteúdo: {outline_content}
</outline_node>

<context priority="P2">
[Contexto de referência]
{context_info}
</context>

<output priority="P0">
[Formato de saída]
Retorne um array JSON com o planejamento de {target_chapter_count} capítulos:

[
  {{
    "sub_index": 1,
    "title": "Título do capítulo (reflete o conflito ou a emoção central)",
    "plot_summary": "Resumo do enredo (150-250 palavras): descreva em detalhe os eventos do capítulo, restritos ao conteúdo do nó atual",
    "key_events": ["Evento-chave 1", "Evento-chave 2", "Evento-chave 3"],
    "character_focus": ["Personagem A", "Personagem B"],
    "emotional_tone": "Tom emocional (ex.: tenso, acolhedor, triste)",
    "narrative_goal": "Objetivo narrativo (o efeito que o capítulo deve alcançar)",
    "conflict_type": "Tipo de conflito (ex.: luta interior, conflito interpessoal)",
    "estimated_words": 3000{scene_field}
  }}
]

[Regras de formato]
- Saída em array JSON puro, sem nenhum outro texto
- Nas descrições, é proibido usar símbolos especiais
- Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
[⚠️ Limites de conteúdo - cumpra rigorosamente]
✅ Desdobre somente o conteúdo do nó atual do esboço
✅ Aprofunde o esboço atual, sem saltar para o que vem depois
✅ Desacelere o ritmo narrativo e explore por completo a etapa atual

❌ Jamais avance para o conteúdo dos nós seguintes
❌ Não deixe o enredo andar depressa demais
❌ Não adiante o conteúdo do nó seguinte

[Princípios de expansão]
✅ Divida um único evento em vários capítulos ricos em detalhes
✅ Explore a fundo emoções, psicologia, ambiente e diálogos
✅ Cada capítulo é uma faceta ou etapa diferente do conteúdo do esboço atual

[🔴 Diferenciação entre capítulos adjacentes (evitar repetição)]
✅ Cada capítulo tem uma abertura própria (cena, momento ou estado dos personagens diferentes)
✅ Cada capítulo tem um fechamento próprio (suspense, virada ou desfecho emocional diferentes)
✅ Os key_events de capítulos adjacentes jamais se sobrepõem
✅ O plot_summary descreve o conteúdo único do capítulo, sem se parecer com os outros
✅ Etapas diferentes do mesmo evento devem ser distinguidas com clareza ("início, meio e fim")

[Requisitos entre capítulos]
✅ Transições naturais e fluidas (cada capítulo parte de um ponto diferente)
✅ Progressão razoável do enredo (sem ultrapassar os limites do esboço atual)
✅ Ritmo com alternância de tensão e respiro
✅ Cada capítulo tem um valor narrativo claro e único
✅ O último capítulo termina exatamente quando o conteúdo do esboço atual se completa
✅ Sem sobreposição de eventos-chave: confira os key_events dos capítulos adjacentes

[Proibido]
❌ Saída fora do formato JSON
❌ Enredo que invade o esboço seguinte
❌ Conteúdo repetido entre capítulos adjacentes
❌ Eventos-chave parecidos
</constraints>"""

# Expansão de esboço em capítulos - em lotes
OUTLINE_EXPAND_MULTI = """<system>
Você é um arquiteto de enredos experiente, especialista em expandir nós do esboço em lotes.
</system>

<task>
[Tarefa de expansão]
Continue desdobrando o nó {outline_order_index} do esboço, "{outline_title}", gerando o planejamento detalhado dos capítulos {start_index} a {end_index} ({target_chapter_count} capítulos no total).

[Sobre os lotes]
- Esta é apenas uma parte da expansão completa
- Deve se encaixar naturalmente nos capítulos já gerados
- A numeração começa no capítulo {start_index}
- Continue aprofundando o conteúdo do esboço atual

[Estratégia de expansão]
{strategy_instruction}
</task>

<project priority="P1">
[Informações do projeto]
Título do livro: {project_title}
Gênero: {project_genre}
Tema: {project_theme}
Ponto de vista narrativo: {project_narrative_perspective}

[Mundo]
Época: {project_world_time_period}
Local: {project_world_location}
Atmosfera: {project_world_atmosphere}
</project>

<characters priority="P1">
[Informações dos personagens]
{characters_info}
</characters>

<outline_node priority="P0">
[Nó atual do esboço - objeto da expansão]
Número: nó {outline_order_index}
Título: {outline_title}
Conteúdo: {outline_content}
</outline_node>

<context priority="P2">
[Contexto de referência]
{context_info}

[Capítulos anteriores já gerados]
{previous_context}
</context>

<output priority="P0">
[Formato de saída]
Retorne um array JSON com o planejamento dos capítulos {start_index} a {end_index} ({target_chapter_count} objetos):

[
  {{
    "sub_index": {start_index},
    "title": "Título do capítulo",
    "plot_summary": "Resumo do enredo (150-250 palavras): descreva em detalhe os eventos do capítulo",
    "key_events": ["Evento-chave 1", "Evento-chave 2", "Evento-chave 3"],
    "character_focus": ["Personagem A", "Personagem B"],
    "emotional_tone": "Tom emocional",
    "narrative_goal": "Objetivo narrativo",
    "conflict_type": "Tipo de conflito",
    "estimated_words": 3000{scene_field}
  }}
]

[Regras de formato]
- Saída em array JSON puro, sem nenhum outro texto
- Nas descrições, é proibido usar símbolos especiais
- sub_index começa em {start_index}
- Escreva todo o conteúdo em {output_language}.
</output>

<constraints>
[⚠️ Limites de conteúdo]
✅ Desdobre somente o conteúdo do nó atual do esboço
✅ Aprofunde o esboço atual, sem saltar para o que vem depois
✅ Desacelere o ritmo narrativo

❌ Jamais avance para o conteúdo dos nós seguintes
❌ Não deixe o enredo andar depressa demais

[Continuidade entre lotes]
✅ Encaixe-se naturalmente nos capítulos já gerados
✅ Comece a numeração no capítulo {start_index}
✅ Mantenha a coerência narrativa

[🔴 Diferenciação entre capítulos adjacentes (evitar repetição)]
✅ Cada capítulo tem abertura e fechamento próprios
✅ Os key_events de capítulos adjacentes jamais se sobrepõem
✅ O plot_summary descreve o conteúdo único do capítulo
✅ Atenção especial à diferença em relação aos capítulos anteriores
✅ Evite repetir conteúdo já existente

[Requisitos entre capítulos]
✅ Transições naturais e fluidas com os capítulos anteriores
✅ Progressão razoável do enredo (sem ultrapassar os limites do esboço atual)
✅ Ritmo com alternância de tensão e respiro
✅ Cada capítulo tem um valor narrativo claro e único
✅ Sem sobreposição de eventos-chave: confira os key_events deste lote e dos capítulos anteriores

[Proibido]
❌ Saída fora do formato JSON
❌ Enredo que invade o esboço seguinte
❌ Conteúdo repetido entre capítulos adjacentes
❌ Key_events parecidos com os dos capítulos anteriores
</constraints>"""
