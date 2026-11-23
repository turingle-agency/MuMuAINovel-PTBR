# Fábrica de Ebooks — Design

Data: 2026-11-11
Base: fork do MuMuAINovel v1.5.8 (`turingle-agency/MuMuAINovel-PTBR`)

## 1. Intenção e o porquê

Transformar o MuMuAINovel — hoje um assistente chinês de escrita de webnovels — numa **fábrica pessoal de ebooks** que:

1. descobre **o que vale a pena criar** (nicho, país, concorrência, preço), a partir de dados reais de mercado e das dores reais do público;
2. **escreve** o produto: ebooks **low ticket** (não-ficção prática, com oferta completa) e **ficção em série** para Amazon KDP;
3. **monta** o produto final (PDF, EPUB, livro impresso, capas, imagens internas);
4. depois, cria **criativos de vídeo** e **publica** direto nas plataformas de venda.

O dono (o usuário) quer usar primeiro para si mesmo, vendendo low tickets no Brasil e em outros países e livros na Amazon KDP. Tudo deve ser configurável e operável pelo frontend.

**Sucesso (nas palavras do dono, ~3 meses):** pesquisas e produtos "saindo redondo"; produtos saindo conforme o público pede, sanando as dores reais; lucro vindo das campanhas.

## 2. Objetivos, não-objetivos e anti-objetivos

### Objetivos
- Radar de Nichos funcionando sob demanda e com sugestões semanais.
- Pipeline de low ticket do nicho até o PDF/EPUB pronto, com order bump, upsell e downsell e preço sugerido.
- Pipeline de ficção em série para KDP (ebook + impresso), reaproveitando o motor atual.
- Interface e saídas em português (e saída no idioma do país-alvo).
- Rodar no Mac do dono; depois num VPS.

### Não-objetivos (por enquanto)
- Ser um SaaS para terceiros (cobrança, onboarding de clientes, limites por cliente). A arquitetura não deve impedir isso no futuro, mas não é construído agora.
- Módulos de criativos de vídeo, publicação automática e microdrama em vídeo — estão no roteiro (seção 6), mas fora do primeiro ciclo de construção.

### Anti-objetivos (o que tornaria isso um fracasso mesmo "funcionando")
- Ebooks genéricos, que não refletem as dores reais pesquisadas — "isso não vende".
- Fábrica de volume de baixa qualidade que gere bloqueio na KDP (a Amazon exige declarar conteúdo gerado por IA e limita uploads por dia).
- Perder a conta Google/Gemini ou a do ChatGPT por uso proibido de login de assinatura.

## 3. Restrições

- **Licença GPL v3** do projeto original: uso pessoal e SaaS ok; se um dia distribuir o software, precisa entregar o código-fonte.
- **Logins de assinatura:**
  - **Gemini:** usar só por chave de API, nunca pelo login da assinatura. Os termos proíbem explicitamente e há banimentos.
  - **Codex/ChatGPT Pro:** login aceito pelo dono para uso pessoal, ciente de que é zona cinzenta nos termos da OpenAI.
- **API de Anúncios da Meta:** fora da UE só retorna anúncios políticos. Anúncios comerciais no Brasil possivelmente sim (a confirmar na doc oficial). Os demais países dependem de scraping (Apify).
- **Agent Reach:** Reddit, X e Instagram exigem login reaproveitado do Chrome. Usar **conta secundária**. Canais experimentais podem quebrar.
- **KDP:** declarar conteúdo de IA, limite diário de títulos, specs de capa (ebook 1600×2560; impresso com capa inteira e lombada calculada pelo nº de páginas).
- **Ambiente:** Mac primeiro (precisa funcionar fora do Docker também, ou com Docker Desktop), VPS depois.

## 4. Decisões do dono (como foram tomadas)

### 4.1 Radar de Nichos (módulo 1)
- Mostra **nichos em alta, concorrência e preço médio por país**.
- Dois modos: **sob demanda** (digita tema + país) e **sugestões semanais** automáticas.
- Fontes:
  - Google Trends (via Apify ou similar);
  - Amazon (mais vendidos, preço, ranking por categoria/país — Apify);
  - Meta Ads (API oficial onde houver dados comerciais + Apify no resto);
  - Reddit e outras redes via **Agent Reach** (https://github.com/Panniantong/agent-reach);
  - **YouTube**: comentários (API oficial do YouTube ou yt-dlp) e **transcrições** (Agent Reach);
  - **Firecrawl** para buscar e ler páginas relevantes.
- Tela: **painel único com tabela** (opção B do esboço) — linhas = nicho × país; colunas = nota, tendência, preço médio Amazon, anúncios ativos na Meta, sinal do Reddit/redes, ação "✨ Criar". A busca sob demanda adiciona linhas na mesma tabela. Esboço salvo em `.superpowers/brainstorm/*/content/pesquisa-nichos.html`.
- Confirmado pelo dono no playback:
  - clicar numa linha abre o detalhe (livros concorrentes, anúncios mais antigos, dores do Reddit/YouTube);
  - nota calculada a partir de demanda × concorrência × preço, com pesos ajustáveis;
  - sugestões semanais usam lista de países/temas definida nas configurações;
  - pesquisas ficam salvas para comparar semana a semana;
  - "Criar ebook" leva o nicho **com toda a pesquisa** para a escrita;
  - todas as chaves e logins são configurados pelo frontend.

### 4.2 Escrita low ticket (módulo 2a)
- Pausas para aprovação humana: **sumário** e **capa**. Todo o resto automático.
- Padrão aprovado:
  - 30–60 páginas, 8–12 capítulos curtos e práticos;
  - checklist/exercício/passo a passo por capítulo, mais um bônus;
  - uma imagem por capítulo no estilo da capa;
  - escrito **direto no idioma do país-alvo**;
  - conteúdo baseado nas dores e dados trazidos pelo Radar e pelo Firecrawl.
- **Oferta completa**, cada item gerado pela máquina, com sumário e capa aprovados pelo dono:
  - **order bump** (algo pequeno e complementar, ~30–50% do preço principal);
  - **upsell** (mais profundo, ~2–4× o principal);
  - **downsell** (versão enxuta, para quem recusou o upsell);
  - **preço sugerido por país**, com justificativa baseada nos dados do Radar;
  - texto curto de página de vendas para cada produto.

### 4.3 Ficção para KDP (módulo 2b)
- Vendida na **Amazon KDP**, em **ebook e livro impresso**, **em séries**; vários países; atenção ao gosto brasileiro por histórias coreanas/orientais.
- Confirmado no playback:
  - aprovação humana em **mundo + personagens**, **esboço** de cada livro e **capa**; capítulos automáticos;
  - gênero/país pode vir do Radar (categorias da Kindle Store);
  - introduzir o nível **Série** acima de Projeto (mundo, personagens, profissões, relações, foreshadowings e memória compartilhados entre volumes);
  - impresso: miolo em PDF no formato KDP (ex. 6×9) + capa inteira (frente, lombada, verso).

### 4.4 Montagem (módulo 3)
- Cada ebook sai em **PDF** e **EPUB**; ficção também como PDF de miolo para impresso + capa inteira.
- Sistema de **temas** escolhidos por ebook. Padrão do low ticket: **"Infoproduto colorido"** (faixas de cor, caixas de dica, emojis, tom leve). Ficção: tema **clássico/editorial**. Esboço salvo em `.superpowers/brainstorm/*/content/estilo-pdf-lowticket.html`.
- Título/autor sobrepostos na capa por código (não pela IA).

### 4.5 Motor de IA
- **Principal:** login do **Codex com a assinatura ChatGPT Pro** do dono, para texto **e imagens** (capas e imagens internas).
- **Reserva:** APIs (OpenAI, Gemini, OpenRouter), usadas automaticamente quando a cota do plano acabar.
- **Gemini:** apenas via chave de API.

### 4.6 Infraestrutura
- Rodar **no Mac primeiro**, **VPS depois**.
- **Qdrant** no lugar do ChromaDB (pedido do dono).
- Tudo **configurável pelo frontend**.

### 4.7 Fork, volume e orçamento (respostas após a revisão)
- **O fork segue por conta própria**; não vamos puxar atualizações do projeto chinês. Reestruturar livremente é permitido: quebrar arquivos gigantes, reescrever prompts, traduzir a interface inteira.
- **Volume-alvo inicial:** **2 low tickets + 1 volume de ficção por semana**.
- **Orçamento de serviços pagos:**
  - **Apify:** plano gratuito, **US$ 5/mês** — recurso escasso.
  - **Firecrawl:** mais de 40 mil créditos disponíveis — pode ser usado à vontade.
  - **Codex (ChatGPT Pro):** cota farta, com reset acumulado — motor principal sem preocupação de custo.
  - **Agent Reach:** grátis, aposta do dono como fonte principal de redes sociais.

## 5. O que já existe e será reaproveitado

| Necessidade | Já existe em | Observação |
|---|---|---|
| Pipeline de ficção (mundo → personagens → esboço → capítulos → análise) | `api/wizard_stream.py`, `api/outlines.py`, `api/chapters.py`, `services/chapter_context_service.py`, `services/plot_analyzer.py` | núcleo da ficção; precisa de PT-BR e do nível Série |
| Memória vetorial | `services/memory_service.py`, `services/knowledge_vector_store.py` | trocar ChromaDB → Qdrant atrás de uma interface |
| Camada de IA multi-provider + streaming SSE | `services/ai_service.py`, `ai_providers/`, `ai_clients/`, `utils/sse_response.py` | adicionar provider Codex + fallback |
| Prompts | `services/prompt_service.py` (+ override por usuário em `api/prompt_templates.py`) | todos em chinês |
| Skills (fluxos em Markdown) | `app/skills/` + `services/skill_loader.py` | útil para novos fluxos (low ticket) |
| Capas | `services/cover_generation_service.py`, `cover_providers/` | adicionar provider OpenAI/Codex, specs KDP |
| Tarefas em segundo plano | `services/background_task_service.py` | base para pesquisas longas e geração de oferta |
| MCP (ferramentas externas para a IA) | `app/mcp/` | possível via de integração do Firecrawl |
| Base de conhecimento por projeto | `services/knowledge_service.py` | pode guardar o material de pesquisa do nicho |
| Exportação | `api/projects.py` (TXT/JSON) | insuficiente; PDF/EPUB são novos |

Problemas conhecidos do código atual que afetam o produto:
- contagem de palavras = `len(content)` (caracteres chineses) em `api/chapters.py:151`;
- `max_tokens` = palavras × 3 em `api/chapters.py:1782`;
- metas "±200字" nos prompts;
- ajuste de intimidade por palavras-chave chinesas em `character_state_update_service.py`;
- fuso `Asia/Shanghai`;
- dependências do servidor do autor original (oficina de prompts, anúncios, changelog em `mumuverse.space`), links de patrocínio/QQ;
- nenhum teste automatizado; arquivos muito grandes (`api/chapters.py` 5,2 mil linhas).

## 6. Roteiro de construção (ordem acordada)

Cada módulo é um projeto próprio; tudo foi desenhado em linhas gerais agora, mas a construção segue esta ordem, um de cada vez:

0. **Fundação:**
   - interface em PT-BR;
   - prompts com idioma de saída parametrizável;
   - correções de contagem de palavras/tokens;
   - remover dependências do autor original;
   - provider Codex + fallback;
   - Qdrant.
1. **Radar de Nichos.**
2. **Escrita:** low ticket + oferta (2a) e ficção em série (2b).
3. **Montagem:** PDF/EPUB/impresso, temas, capas.
4. **Criativos de vídeo** — o dono vai passar ângulos e formatos depois.
5. **Publicação automática** em Kiwify, Hotmart e outras plataformas escolhidas. Antes de desenhar, verificar até onde as APIs permitem **criar produto** (provavelmente parte exige automação de navegador). É também onde entram dados de venda/campanha para medir o "lucro vindo das campanhas".
6. **Microdrama em vídeo** (referência: tutorial "Claude + H3 一个人拍 AI 短剧" — roteiro → storyboard → fichas visuais → vídeo com voz → edição), reaproveitando personagens e esboços da ficção.

## 7. Decisões que tomei (o dono pode revisar)

- **Codex via CLI oficial:** a integração com o Codex usa o **CLI oficial `codex`** (ex. `codex exec`) logado na conta do dono. Não usa extração do token OAuth nem chamadas diretas ao backend do ChatGPT, porque é mais estável e menos arriscado.
- **Interface:** traduzida para **PT-BR** com estrutura de i18n, para facilitar outros idiomas no futuro. Os ebooks saem no idioma do país-alvo independentemente da interface.
- **Remover ou desligar:**
  - login LinuxDO, oficina de prompts em nuvem, anúncios e changelog remotos;
  - página de patrocínio, QQ, componente de Ano Novo Chinês.
- **Mantido:** multiusuário (já existe, custa nada manter).
- **Meta:** usar a API oficial da Biblioteca de Anúncios onde ela traz dados comerciais (UE; Brasil a confirmar) e Apify para os demais países.
- **Low ticket como tipo de projeto novo:** é um **tipo de projeto novo** ao lado da ficção, não uma adaptação forçada do fluxo de personagens/foreshadowings. Reaproveita IA, tarefas, SSE, base de conhecimento, capas e montagem.
- **Banco:** PostgreSQL continua como principal; SQLite segue suportado para rodar no Mac sem Docker, se for mais simples.
- **Escopo do primeiro plano:** o primeiro plano de implementação cobre só o **Módulo 0 (Fundação)**. Os modelos de dados de Série, Nicho/Pesquisa e Oferta são esboçados já nele, para a fundação não precisar ser refeita depois.
- **Apify como recurso escasso (US$ 5/mês):**
  - prioridade das fontes: Agent Reach, Firecrawl e APIs oficiais gratuitas (YouTube, Meta onde houver) primeiro; Apify só para Amazon e Meta Ads fora do alcance da API oficial;
  - cache agressivo (resultado reaproveitado por vários dias);
  - medidor de gasto no frontend, com bloqueio e pedido de confirmação ao se aproximar do limite mensal configurado.
- **Order bump e downsell** são formatos **mais leves** (pacote de checklists, planilha, modelos, guia curto), gerados pelo mesmo pipeline com um molde menor. O **upsell** pode ser um guia mais longo/avançado. Cada um mantém as duas pausas de aprovação (sumário e capa), como o dono confirmou.
- **Codex:**
  - imagens via geração de imagem do próprio Codex logado no plano. Se algum tipo de imagem não estiver disponível por ali, cai para a API de imagem (OpenAI/Gemini) dentro do orçamento;
  - o Codex CLI não faz streaming token a token como o pipeline atual; para ele, a interface mostra progresso por etapas em vez do texto aparecendo ao vivo.
- **Começo do zero:** não há dados antigos a preservar, então nada de migração ChromaDB → Qdrant; projetos antigos em chinês não precisam continuar funcionando.
- **Radar único para os dois tipos:** a mesma tabela tem uma coluna/filtro **Tipo** (low ticket / ficção). As linhas de ficção usam sinais da Kindle Store (categoria, ranking, preço) no lugar de Meta Ads.
- **Agent Reach roda no Mac:** começa rodando só no Mac (onde está o Chrome logado). É desenhado como um "coletor" separado, que no futuro pode continuar no Mac e enviar resultados ao VPS.
- **Dono único:** o código multiusuário fica, mas o sistema é tratado como de dono único. Chaves, provider Codex e pesquisas são globais/admin; nada de cota por usuário agora.
- **Volume (3 produtos/semana):** cabe numa fila de tarefas simples com concorrência baixa (1–2 gerações em paralelo) no Mac; não precisa de infraestrutura pesada de filas.

## 8. Deixado para quem constrói

- Motor de PDF/EPUB (ex. HTML+CSS → PDF via WeasyPrint ou Chromium; EPUB via biblioteca Python).
- Agendador das sugestões semanais.
- Fórmula inicial da nota do nicho e pesos padrão.
- Escolha concreta das ferramentas da Apify (preço e qualidade variam; verificar páginas atuais).
- Como empacotar Agent Reach e yt-dlp (CLI chamada por subprocesso).
- Modelo de dados de Série, Nicho/Pesquisa e Oferta.
- Estratégia de testes (hoje não há nenhum).
