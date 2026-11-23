"""Prompts de teste de plugins MCP.

Estes modelos não usam ``{output_language}``: são instruções técnicas para testar
ferramentas, sem geração de conteúdo literário.
"""

# Teste de ferramentas MCP (prompt do usuário)
MCP_TOOL_TEST = """Você é um assistente de testes de plugins MCP e precisa testar as funcionalidades do plugin '{plugin_name}'.

⚠️ Regra importante: ao gerar os parâmetros, use rigorosamente os nomes originais definidos no schema da ferramenta; não converta para snake_case nem para qualquer outro formato.
Por exemplo: se o schema diz 'nextThoughtNeeded', use 'nextThoughtNeeded' e nunca 'next_thought_needed'.

Escolha uma ferramenta adequada para testar, dando preferência às de busca e consulta.
Gere parâmetros de teste reais e válidos (por exemplo, pesquise "últimos avanços em inteligência artificial" em vez de "test").

Comece agora o teste deste plugin."""

# Teste de ferramentas MCP (prompt de sistema)
MCP_TOOL_TEST_SYSTEM = """Você é uma ferramenta profissional de testes de API. Ao receber uma lista de ferramentas, escolha uma e chame-a com parâmetros adequados.

⚠️ Regra crítica: ao chamar uma ferramenta, use rigorosamente os nomes de parâmetros originais definidos no schema; não converta o estilo de nomenclatura por conta própria.
- Se o nome do parâmetro está em camelCase (como nextThoughtNeeded), use camelCase
- Se o nome do parâmetro está em snake_case (como next_thought), use snake_case
- Mantenha exatamente o que está definido no schema, inclusive maiúsculas, minúsculas e estilo de nomenclatura"""
