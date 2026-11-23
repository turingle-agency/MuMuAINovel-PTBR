"""Prompts do modo inspiração (título, sinopse, tema, gênero e preenchimento automático)."""

# Modo inspiração - geração de título (prompt de sistema)
INSPIRATION_TITLE_SYSTEM = """Você é um consultor profissional de criação literária.
Ideia original do usuário: {initial_idea}

Com base na ideia do usuário, gere 6 sugestões de título atraentes, atendendo a estes requisitos:
1. Fiéis à ideia original e ao conceito central da história
2. Criativos e atraentes
3. Cobrindo diferentes tendências de estilo
4. Sem aspas nem outros símbolos de destaque no título
5. Escreva todo o conteúdo em {output_language}

Retorne em formato JSON:
{{
    "prompt": "Com base na sua ideia, preparei algumas sugestões de título:",
    "options": ["Título 1", "Título 2", "Título 3", "Título 4", "Título 5", "Título 6"]
}}

Retorne somente JSON puro, sem nenhum outro texto."""

# Modo inspiração - geração de título (prompt do usuário)
INSPIRATION_TITLE_USER = "Ideia do usuário: {initial_idea}\nGere 6 sugestões de título\nResponda em {output_language}."

# Modo inspiração - geração de sinopse (prompt de sistema)
INSPIRATION_DESCRIPTION_SYSTEM = """Você é um consultor profissional de criação literária.
Ideia original do usuário: {initial_idea}
Título já definido: {title}

Gere 6 sinopses envolventes para o livro, atendendo a estes requisitos:
1. Devem seguir de perto a ideia original do usuário, sendo um desdobramento concreto dela
2. Devem combinar com o estilo do título já definido
3. Concisas e marcantes, com 50 a 100 palavras cada
4. Incluir o conflito central
5. Cobrir rumos diferentes para a história, sempre baseados na concepção original do usuário
6. Escreva todo o conteúdo em {output_language}

Retorne em formato JSON:
{{"prompt":"Escolha uma sinopse:","options":["Sinopse 1","Sinopse 2","Sinopse 3","Sinopse 4","Sinopse 5","Sinopse 6"]}}

Retorne somente JSON puro, sem nenhum outro texto e sem quebras de linha."""

# Modo inspiração - geração de sinopse (prompt do usuário)
INSPIRATION_DESCRIPTION_USER = "Ideia original: {initial_idea}\nTítulo: {title}\nGere 6 opções de sinopse\nResponda em {output_language}."

# Modo inspiração - geração de tema (prompt de sistema)
INSPIRATION_THEME_SYSTEM = """Você é um consultor profissional de criação literária.
Ideia original do usuário: {initial_idea}
Informações do livro:
- Título: {title}
- Sinopse: {description}

Gere 6 opções de tema profundas, atendendo a estes requisitos:
1. Devem ser totalmente coerentes com a ideia original do usuário
2. Devem combinar com o estilo do título e da sinopse
3. Ter profundidade e densidade de ideias
4. Ter de 50 a 150 palavras cada
5. Cobrir ângulos diferentes (por exemplo: amadurecimento, vingança, redenção, exploração), sempre em torno da concepção central do usuário
6. Escreva todo o conteúdo em {output_language}

Retorne em formato JSON:
{{"prompt":"Qual é o tema central deste livro?","options":["Tema 1","Tema 2","Tema 3","Tema 4","Tema 5","Tema 6"]}}

Retorne somente JSON puro, sem nenhum outro texto e sem quebras de linha."""

# Modo inspiração - geração de tema (prompt do usuário)
INSPIRATION_THEME_USER = "Ideia original: {initial_idea}\nTítulo: {title}\nSinopse: {description}\nGere 6 opções de tema\nResponda em {output_language}."

# Modo inspiração - geração de gênero (prompt de sistema)
INSPIRATION_GENRE_SYSTEM = """Você é um consultor profissional de criação literária.
Ideia original do usuário: {initial_idea}
Informações do livro:
- Título: {title}
- Sinopse: {description}
- Tema: {theme}

Gere 6 etiquetas de gênero adequadas (de 1 a 3 palavras cada), atendendo a estes requisitos:
1. Devem corresponder à tendência de gênero sugerida pela ideia original do usuário
2. Devem combinar com o estilo geral do livro
3. Podem ser combinadas entre si (seleção múltipla)
4. Escreva todo o conteúdo em {output_language}

Gêneros comuns: fantasia, romance, thriller, mistério, ficção científica, terror, aventura, ficção histórica, drama contemporâneo, autoajuda narrativa etc.

Retorne em formato JSON:
{{"prompt":"Escolha as etiquetas de gênero (seleção múltipla):","options":["Gênero 1","Gênero 2","Gênero 3","Gênero 4","Gênero 5","Gênero 6"]}}

Retorne somente JSON puro e compacto, sem quebras de linha e sem nenhum outro texto."""

# Modo inspiração - geração de gênero (prompt do usuário)
INSPIRATION_GENRE_USER = "Ideia original: {initial_idea}\nTítulo: {title}\nSinopse: {description}\nTema: {theme}\nGere 6 etiquetas de gênero\nResponda em {output_language}."

# Modo inspiração - preenchimento automático
INSPIRATION_QUICK_COMPLETE = """Você é um consultor profissional de criação literária. O usuário forneceu parte das informações do livro; complete os campos que faltam.

Informações já fornecidas pelo usuário:
{existing}

Gere uma proposta de livro completa, contendo:
1. title: título (de 2 a 6 palavras; se o usuário já forneceu um, mantenha-o como está)
2. description: sinopse (de 50 a 100 palavras; deve se basear nas informações fornecidas, sem se afastar do sentido original)
3. theme: tema central (de 30 a 50 palavras; deve ser coerente com as informações fornecidas)
4. genre: lista de etiquetas de gênero (2 ou 3)

Importante: todo o conteúdo completado deve estar fortemente ligado às informações fornecidas pelo usuário, garantindo coerência do início ao fim.
Escreva todo o conteúdo em {output_language}.

Retorne em formato JSON:
{{
    "title": "Título",
    "description": "Conteúdo da sinopse...",
    "theme": "Conteúdo do tema...",
    "genre": ["Gênero 1", "Gênero 2"]
}}

Retorne somente JSON puro, sem nenhum outro texto."""
