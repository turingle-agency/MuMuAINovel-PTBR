"""Prompt de geração de capa do livro."""

NOVEL_COVER_PROMPT_TEMPLATE = """Crie uma ilustração de capa de livro de alta qualidade, em formato vertical, adequada para a capa de um livro.

O título do livro é: "{title}" (serve apenas de inspiração; ele não deve aparecer escrito na imagem).
O gênero é {genre}. O tema central é {theme}. Resumo da história: {description}

A imagem deve ser cinematográfica, refinada, atmosférica e emocionalmente expressiva, com um foco visual claro e imagens fortemente simbólicas. O estilo visual, a paleta de cores e a composição devem vir do gênero do livro ({genre}): priorize a narrativa visual e o clima típicos desse gênero, em vez de retratar uma cena específica de forma literal.

Deve parecer a capa profissional de um livro publicado, no padrão do mercado editorial e de ebooks do gênero.

Requisitos obrigatórios:
- Composição vertical padrão de capa de livro (proporção 2:3).
- NÃO inclua nenhum texto na imagem: nada de título, nome de autor, subtítulo, letras, números ou caracteres aleatórios. A tipografia será aplicada depois, em outra etapa.
- Deixe uma área limpa e com menos detalhes no terço superior ou inferior da imagem, onde o título poderá ser posicionado depois.
- Referências culturais e visuais coerentes com o público leitor de {output_language}.
- Sem logotipo.
- Sem marca d'água.
- Sem bordas.
- Sem elementos de interface (UI).
- Sem mockup.

A imagem final deve ser uma arte de capa completa e profissional, apenas ilustração, sem nenhum texto."""
