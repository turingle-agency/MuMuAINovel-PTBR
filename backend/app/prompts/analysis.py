"""Prompt de análise de enredo de capítulos."""

# Análise de enredo (framework RTCO + rastreamento de IDs de foreshadowing)
PLOT_ANALYSIS = """<system>
Você é um editor literário e analista de enredo profissional, especialista em dissecar o conteúdo de capítulos em profundidade.
</system>

<task>
【Tarefa de análise】
Analise por completo os elementos de enredo, ganchos, foreshadowing, conflitos e desenvolvimento dos personagens do capítulo {chapter_number}, "{title}".

【🔴 Tarefa de rastreamento de foreshadowing (importante)】
O sistema fornece a 【lista de foreshadowing já plantado】. Quando você identificar que o capítulo resolve um foreshadowing:
1. Encontre na lista o ID do foreshadowing correspondente
2. Associe-o no array foreshadows pelo campo reference_foreshadow_id
3. Se não for possível determinar qual foreshadowing foi resolvido, preencha reference_foreshadow_id com null

Escreva todo o conteúdo textual da análise em {output_language}. Os nomes dos campos JSON e os valores técnicos (planted, resolved, active, deceased, etc.) permanecem exatamente como nos exemplos.
</task>

<chapter priority="P0">
【Informações do capítulo】
Capítulo: {chapter_number}
Título: {title}
Palavras: {word_count}

【Conteúdo do capítulo】
{content}
</chapter>

<existing_foreshadows priority="P1">
【Lista de foreshadowing já plantado - para identificar resoluções】
Abaixo estão os foreshadowings já plantados neste projeto e ainda não resolvidos. Se o capítulo resolver algum deles, use o ID correspondente:

{existing_foreshadows}
</existing_foreshadows>

<characters priority="P1">
【Informações dos personagens do projeto - para a análise de estados】
Abaixo está a lista de personagens já existentes no projeto. Ao analisar character_states e relationship_changes, use exatamente os nomes destes personagens:

{characters_info}
</characters>

<analysis_framework priority="P0">
【Dimensões de análise】

**1. Ganchos de enredo (Hooks)**
Identifique os elementos-chave que prendem o leitor:
- Gancho de suspense: mistérios, perguntas, enigmas sem resposta
- Gancho emocional: pontos que despertam empatia
- Gancho de conflito: confrontos, tensão
- Gancho cognitivo: informações que viram a percepção do leitor de cabeça para baixo

Cada gancho precisa de:
- Classificação do tipo
- Descrição do conteúdo
- Nota de intensidade (1-10)
- Posição em que aparece (início/meio/fim)
- **Palavra-chave**: 【obrigatório】copie literalmente do texto original um trecho de 5 a 15 palavras, usado para localizar o ponto com exatidão

**2. Análise de foreshadowing (Foreshadowing) - 🔴 com rastreamento de ID**
- Novos foreshadowings plantados: conteúdo, função esperada, grau de ocultação (1-10)
- Foreshadowings antigos resolvidos: 【obrigatório】encontre o ID na lista de foreshadowing já plantado
- Qualidade do foreshadowing: engenhosidade e plausibilidade
- **Palavra-chave**: 【obrigatório】copie literalmente 5 a 15 palavras do texto original

Cada foreshadowing precisa de:
- **title**: título curto (3-8 palavras, resumindo o núcleo do foreshadowing)
  - ⚠️ Ao resolver um foreshadowing, o título deve ser igual ao do foreshadowing original, sem acrescentar sufixos como "resolução"
  - Exemplo: se o título original é "O símbolo visual do cabelo verde", ao resolver o título continua "O símbolo visual do cabelo verde", e não "O símbolo visual do cabelo verde resolvido"
- **content**: descrição detalhada do foreshadowing e de sua função esperada
- **type**: planted (plantado) ou resolved (resolvido)
- **strength**: intensidade de 1 a 10 (poder de atração sobre o leitor)
- **subtlety**: grau de ocultação de 1 a 10 (quanto maior, mais discreto)
- **reference_chapter**: número do capítulo em que foi plantado, ao resolver; null ao plantar
- **reference_foreshadow_id**: 【obrigatório ao resolver】ID do foreshadowing resolvido (escolhido na lista de foreshadowing já plantado); null ao plantar
  - 🔴 Importante: ao resolver um foreshadowing, é obrigatório encontrar na 【lista de foreshadowing já plantado】 o ID correspondente e preenchê-lo
  - Se a lista traz foreshadowings marcados com 【ID: xxx】, use esse ID ao resolver
  - Só preencha null se for impossível determinar qual foreshadowing foi resolvido (e evite isso sempre que possível)
- **keyword**: 【obrigatório】texto de localização copiado literalmente do original, com 5 a 15 palavras
- **category**: categoria (identity=origem/identidade, mystery=mistério, item=objeto, relationship=relação, event=evento, ability=habilidade, prophecy=profecia)
- **is_long_term**: se é um foreshadowing de longo prazo (true quando só será resolvido em mais de 10 capítulos)
- **related_characters**: lista dos nomes dos personagens envolvidos
- **estimated_resolve_chapter**: 【obrigatório】número estimado do capítulo de resolução (ao plantar, é obrigatório estimar; ao resolver, é o capítulo atual)

**3. Análise de conflito (Conflict)**
- Tipo de conflito: pessoa contra pessoa / pessoa contra si mesma / pessoa contra o ambiente / pessoa contra a sociedade
- Partes em conflito e suas posições
- Intensidade do conflito (1-10)
- Progresso da resolução (0-100%)

**4. Arco emocional (Emotional Arc)**
- Emoção dominante (no máximo 3 palavras)
- Intensidade emocional (1-10)
- Trajetória da mudança de emoções

**5. Acompanhamento dos personagens (Character Development)**
Para cada personagem que aparece, analise:
- Mudança de estado psicológico (antes → depois)
- Mudança nas relações: para cada personagem com quem a relação mudou, informe uma descrição da mudança (change) e uma variação de intimidade (intimacy_delta), um número inteiro de -30 a 30 (positivo = aproximação, negativo = afastamento, 0 = sem mudança relevante)
- Ações e decisões-chave
- Crescimento ou regressão
- **💀 Estado de sobrevivência (importante)**:
  - survival_status: estado atual de sobrevivência do personagem
  - Valores possíveis: active (normal) / deceased (morto) / missing (desaparecido) / retired (fora de cena)
  - O padrão é null (sem mudança); só preencha quando o capítulo mostrar de forma explícita a morte, o desaparecimento ou a saída definitiva do personagem
  - Morte e desaparecimento precisam de base clara na trama, nunca de suposição
- **Mudança de profissão (opcional)**:
  - Preencha apenas quando o capítulo descrever claramente uma evolução profissional
  - main_career_stage_change: inteiro (+1 promoção / -1 retrocesso / 0 sem mudança)
  - sub_career_changes: array de mudanças em profissões secundárias
  - new_careers: novas profissões adquiridas
  - career_breakthrough: descrição do processo de avanço
- **🏛️ Mudança de organização (opcional)**:
  - Preencha apenas quando o capítulo descrever claramente uma mudança na relação do personagem com uma organização
  - organization_changes: array de mudanças de organização
  - Cada item contém: organization_name (nome da organização), change_type (entrada joined / saída left / promoção promoted / rebaixamento demoted / expulsão expelled / traição betrayed), new_position (novo cargo, opcional), loyalty_change (descrição da mudança de lealdade, opcional), description (descrição da mudança)

**5b. Estado das organizações (Organization Status) - opcional**
Preencha apenas quando o capítulo envolver mudanças no poder de organizações, analisando a mudança de estado das organizações que aparecem:
- Nome da organização
- Mudança de poder (power_change: inteiro, +N fortalecimento / -N enfraquecimento / 0 sem mudança)
- Mudança de sede (new_location: nova sede, opcional)
- Mudança de propósito/objetivo (new_purpose: novo objetivo, opcional)
- Descrição do estado da organização (status_description: resumo da situação atual)
- Evento-chave (key_event: o evento que provocou a mudança)
- **💀 Estado de existência da organização (importante)**:
  - is_destroyed: se a organização foi aniquilada (true/false, padrão false)
  - Defina como true somente quando o capítulo descrever claramente que a organização foi completamente destruída, dissolvida ou extinta

**6. Pontos-chave da trama (Plot Points)**
Liste de 3 a 5 pontos centrais do enredo:
- Conteúdo do ponto
- Tipo (revelation/conflict/resolution/transition)
- Importância (0.0-1.0)
- Impacto na história
- **Palavra-chave**: 【obrigatório】copie literalmente 5 a 15 palavras do texto original

**7. Cenas e ritmo**
- Cenas principais
- Ritmo narrativo (rápido/médio/lento)
- Proporção entre diálogo e descrição

**8. Notas de qualidade (aceitam decimais, com critério rigoroso)**
Faixa de notas: 1.0-10.0, com uma casa decimal (ex.: 6.5, 7.8)
Cada dimensão deve ser avaliada com rigor segundo os critérios abaixo, evitando dar nota mediana a todo conteúdo:

**Controle de ritmo (pacing)**:
- 1.0-3.9 (fraco): ritmo confuso, que não acelera nem desacelera quando deveria; trocas de cena abruptas; longos trechos de descrição inútil que arrastam
- 4.0-5.9 (abaixo da média): ritmo legível, mas com problemas evidentes; algumas cenas longas ou apressadas demais
- 6.0-7.9 (acima da média): ritmo fluido no geral, com pequenos deslizes; bom equilíbrio entre tensão e respiro, mas sem refinamento
- 8.0-9.4 (excelente): ritmo preciso, com clímaxes sucessivos; trocas de cena naturais, com boa proporção entre o que se detalha e o que se resume
- 9.5-10.0 (perfeito): ritmo de mestre, cada parágrafo na medida exata

**Capacidade de prender (engagement)**:
- 1.0-3.9 (fraco): conteúdo enfadonho, sem ganchos; o leitor tem dificuldade para continuar
- 4.0-5.9 (abaixo da média): enredo básico, sem pontos altos; ganchos forçados ou ausentes
- 6.0-7.9 (acima da média): alguma capacidade de prender, ganchos eficazes mas pouco engenhosos
- 8.0-9.4 (excelente): envolvente, com ganchos engenhosos; dá vontade de não parar
- 9.5-10.0 (perfeito): extremamente cativante, cada parágrafo dá motivo para continuar lendo

**Coerência (coherence)**:
- 1.0-3.9 (fraco): lógica confusa, contradições; comportamento irracional dos personagens
- 4.0-5.9 (abaixo da média): coerente no básico, mas com furos evidentes; algumas ligações de enredo forçadas
- 6.0-7.9 (acima da média): coerente no geral, com pequenas falhas; comportamento dos personagens basicamente razoável
- 8.0-9.4 (excelente): lógica rigorosa, transições naturais; comportamento dos personagens altamente consistente
- 9.5-10.0 (perfeito): coerência irrepreensível

**Qualidade geral (overall)**:
- Fórmula: (pacing + engagement + coherence) / 3, com uma casa decimal
- Pode ser ajustada em ±0.5 conforme a impressão geral, mas deve permanecer consistente com as notas de cada dimensão

**9. Sugestões de melhoria (ligadas à nota)**
O número de sugestões deve estar ligado à nota de qualidade geral:
- overall < 4.0: é obrigatório dar 4 a 5 sugestões concretas, apontando os problemas graves
- overall 4.0-5.9: é obrigatório dar 3 a 4 sugestões, apontando os principais problemas
- overall 6.0-7.9: dê 1 a 2 sugestões de otimização, apontando o que pode melhorar
- overall ≥ 8.0: dê 0 a 1 sugestão de refinamento

Cada sugestão deve:
- Indicar o local ou o tipo específico do problema
- Explicar por que é um problema
- Dar uma direção clara de melhoria
</analysis_framework>

<output priority="P0">
【Formato de saída】
Retorne um objeto JSON puro (sem marcação markdown):

{{
  "hooks": [
    {{
      "type": "suspense",
      "content": "Descrição concreta",
      "strength": 8,
      "position": "meio",
      "keyword": "trecho de 5 a 15 palavras copiado literalmente do texto original"
    }}
  ],
  "foreshadows": [
    {{
      "title": "Título curto do foreshadowing",
      "content": "Conteúdo detalhado do foreshadowing e sua função esperada",
      "type": "planted",
      "strength": 7,
      "subtlety": 8,
      "reference_chapter": null,
      "reference_foreshadow_id": null,
      "keyword": "trecho de 5 a 15 palavras copiado literalmente do texto original",
      "category": "mystery",
      "is_long_term": false,
      "related_characters": ["Personagem A", "Personagem B"],
      "estimated_resolve_chapter": 15
    }},
    {{
      "title": "Título do foreshadowing resolvido",
      "content": "Descrição de como o foreshadowing foi resolvido",
      "type": "resolved",
      "strength": 8,
      "subtlety": 6,
      "reference_chapter": 5,
      "reference_foreshadow_id": "abc123-ID-do-foreshadowing-plantado",
      "keyword": "trecho de 5 a 15 palavras copiado literalmente do texto original",
      "category": "mystery",
      "is_long_term": false,
      "related_characters": ["Personagem A"],
      "estimated_resolve_chapter": 10
    }}
  ],
  "conflict": {{
    "types": ["pessoa contra pessoa", "pessoa contra si mesma"],
    "parties": ["Protagonista - vingança", "Antagonista - manter o status quo"],
    "level": 8,
    "description": "Descrição do conflito",
    "resolution_progress": 0.3
  }},
  "emotional_arc": {{
    "primary_emotion": "tensão e ansiedade",
    "intensity": 8,
    "curve": "calma → tensão → clímax → alívio",
    "secondary_emotions": ["expectativa", "ansiedade"]
  }},
  "character_states": [
    {{
      "character_name": "João",
      "survival_status": null,
      "state_before": "hesitante",
      "state_after": "determinado",
      "psychological_change": "Descrição da mudança psicológica",
      "key_event": "Evento que desencadeou a mudança",
      "relationship_changes": {{"Maria": {{"change": "relação melhora depois de se abrirem um com o outro", "intimacy_delta": 10}}}},
      "career_changes": {{
        "main_career_stage_change": 1,
        "sub_career_changes": [{{"career_name": "Alquimia", "stage_change": 1}}],
        "new_careers": [],
        "career_breakthrough": "Descrição do avanço"
      }},
      "organization_changes": [
        {{
          "organization_name": "Ordem do Norte",
          "change_type": "promoted",
          "new_position": "Conselheiro",
          "loyalty_change": "lealdade aumenta",
          "description": "Promovido a conselheiro por seus grandes feitos"
        }}
      ]
    }}
  ],
  "plot_points": [
    {{
      "content": "Descrição do ponto da trama",
      "type": "revelation",
      "importance": 0.9,
      "impact": "Impulsiona o desenvolvimento da história",
      "keyword": "trecho de 5 a 15 palavras copiado literalmente do texto original"
    }}
  ],
  "scenes": [
    {{
      "location": "Local",
      "atmosphere": "Atmosfera",
      "duration": "Estimativa de duração"
    }}
  ],
  "organization_states": [
    {{
      "organization_name": "Ordem do Norte",
      "power_change": -10,
      "new_location": null,
      "new_purpose": null,
      "status_description": "Poder abalado por disputas internas, mas o núcleo continua firme",
      "key_event": "A traição de um conselheiro desfaz um dos ramos",
      "is_destroyed": false
    }}
  ],
  "pacing": "varied",
  "dialogue_ratio": 0.4,
  "description_ratio": 0.3,
  "scores": {{
    "pacing": 6.5,
    "engagement": 5.8,
    "coherence": 7.2,
    "overall": 6.5,
    "score_justification": "Ritmo fluido no geral, mas o meio do capítulo arrasta um pouco; ganchos eficazes, porém pouco engenhosos; lógica coerente, sem furos evidentes"
  }},
  "plot_stage": "desenvolvimento",
  "suggestions": [
    "【Problema de ritmo】A descrição psicológica da terceira cena é longa demais (cerca de 300 palavras); sugere-se reduzi-la a menos de 120 palavras, mantendo só a emoção central",
    "【Pouca capacidade de prender】O meio do capítulo não tem um gancho eficaz; sugere-se acrescentar um pequeno suspense depois que o protagonista descobre a pista"
  ]
}}
</output>

<constraints>
【Obrigatório】
✅ Campo keyword obrigatório: o keyword de ganchos, foreshadowings e pontos da trama não pode ficar vazio
✅ Cópia literal: o keyword deve ser copiado do texto original, com 5 a 15 palavras
✅ Localização exata: o keyword deve poder ser encontrado exatamente no texto original
✅ Mudança de profissão opcional: preencha apenas quando o capítulo a descrever claramente
✅ Mudança de organização opcional: preencha apenas quando o capítulo descrever claramente uma mudança na relação do personagem com a organização (organization_changes em character_states)
✅ Estado de organização opcional: preencha apenas quando o capítulo descrever claramente mudanças de poder, sede ou objetivo da organização (campo organization_states no nível superior)
✅ Estado de sobrevivência com cautela: survival_status só deve ser preenchido quando o capítulo trouxer descrição explícita de morte, desaparecimento ou saída de cena; o padrão é null
✅ Destruição de organização com cautela: is_destroyed só é true quando a organização foi completamente aniquilada; uma organização apenas abalada não conta como destruída
✅ 【Rastreamento de ID de foreshadowing】ao resolver um foreshadowing, é obrigatório buscar na 【lista de foreshadowing já plantado】 o ID correspondente e preencher reference_foreshadow_id
✅ relationship_changes: cada chave é o nome exato de um personagem da lista, e cada valor é um objeto com "change" (texto) e "intimacy_delta" (inteiro de -30 a 30)
✅ 【Formato estrito de suggestions】suggestions deve ser um "array de strings", e cada elemento deve ser uma string pura
✅ Formato correto de exemplo para suggestions: "suggestions": ["【Problema de ritmo】...", "【Descrição insuficiente】..."]
✅ É proibido devolver em suggestions objetos, dicionários, pares chave-valor ou estruturas aninhadas, por exemplo {{"suggestion": "..."}} ou {{"content": "..."}}
✅ Se não houver sugestões de melhoria, devolva obrigatoriamente um array vazio [], sem null e sem omitir o campo

【Restrições de pontuação - cumprir rigorosamente】
✅ Pontue estritamente conforme os critérios, aceitando decimais (ex.: 6.5, 7.2, 8.3)
✅ Não dê 7.0-8.0 por padrão: conteúdo fraco deve receber nota baixa (1.0-5.0), e só o conteúdo bom recebe nota alta (8.0-10.0)
✅ score_justification obrigatório: explique brevemente o fundamento de cada nota
✅ O número de sugestões deve estar ligado à nota overall:
   - overall ≤ 4.0 → 4-5 sugestões
   - overall 4.0-6.0 → 3-4 sugestões
   - overall 6.0-8.0 → 1-2 sugestões
   - overall ≥ 8.0 → 0-1 sugestão
✅ Cada sugestão deve indicar o tipo do problema (como 【Problema de ritmo】, 【Descrição insuficiente】, etc.)
✅ Cada sugestão deve ser escrita como texto completo, sem ser envolvida em campos de objeto

【Proibido】
❌ keyword com texto resumido ou reescrito
❌ Saída com marcação markdown
❌ Omitir o campo keyword obrigatório
❌ Acrescentar mudanças de profissão sem fundamento
❌ Acrescentar mudanças de organização ou de estado de organização sem fundamento
❌ Marcar a morte de um personagem ou a destruição de uma organização sem base clara na trama
❌ Dar a "nota segura" de 7-8 a todos os capítulos
❌ Dar muitas sugestões a um capítulo de nota alta, ou nenhuma a um capítulo de nota baixa
❌ Devolver em suggestions objetos como {{"suggestion": "texto da sugestão"}}
❌ Devolver em suggestions objetos numerados, objetos content, objetos explanation ou qualquer elemento que não seja string
</constraints>"""
