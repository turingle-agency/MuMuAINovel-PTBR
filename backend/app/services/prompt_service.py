"""Serviço de gerenciamento de prompts."""
from typing import Dict, Any, Optional
import json
import string
from app.services.skill_loader import get_all_skills_cached
from app import prompts
from app.constants.languages import language_name, DEFAULT_LANGUAGE

DEFAULT_OUTPUT_LANGUAGE = language_name(DEFAULT_LANGUAGE)


class WritingStyleManager:
    """写作风格管理器"""
    
    @staticmethod
    def apply_style_to_prompt(base_prompt: str, style_content: str) -> str:
        """
        将写作风格应用到基础提示词中
        
        注意：写作风格已通过 system_prompt 注入（system_prompt_with_style），
        此方法仅追加输出指令，不再重复注入 style_content，避免风格信息被注入两次。
        
        Args:
            base_prompt: 基础提示词
            style_content: 风格要求内容（已通过 system_prompt 注入，此处不使用）
            
        Returns:
            追加输出指令后的提示词
        """
        # 写作风格已在 system_prompt 中注入，此处只追加输出格式指令
        return f"{base_prompt}\n\nEscreva diretamente o texto do capítulo, sem incluir o título do capítulo nem outras observações."


class PromptService:
    """提示词模板管理"""

    # Templates em PT-BR vivem em app/prompts; reexportados aqui para manter PromptService.<KEY>
    WORLD_BUILDING = prompts.WORLD_BUILDING
    CAREER_SYSTEM_GENERATION = prompts.CAREER_SYSTEM_GENERATION
    MCP_WORLD_BUILDING_PLANNING = prompts.MCP_WORLD_BUILDING_PLANNING
    CHARACTERS_BATCH_GENERATION = prompts.CHARACTERS_BATCH_GENERATION
    SINGLE_CHARACTER_GENERATION = prompts.SINGLE_CHARACTER_GENERATION
    SINGLE_ORGANIZATION_GENERATION = prompts.SINGLE_ORGANIZATION_GENERATION
    AUTO_CHARACTER_ANALYSIS = prompts.AUTO_CHARACTER_ANALYSIS
    AUTO_CHARACTER_GENERATION = prompts.AUTO_CHARACTER_GENERATION
    AUTO_ORGANIZATION_ANALYSIS = prompts.AUTO_ORGANIZATION_ANALYSIS
    AUTO_ORGANIZATION_GENERATION = prompts.AUTO_ORGANIZATION_GENERATION
    MCP_CHARACTER_PLANNING = prompts.MCP_CHARACTER_PLANNING
    OUTLINE_CREATE = prompts.OUTLINE_CREATE
    OUTLINE_CONTINUE = prompts.OUTLINE_CONTINUE
    CHAPTER_GENERATION_ONE_TO_MANY = prompts.CHAPTER_GENERATION_ONE_TO_MANY
    CHAPTER_GENERATION_ONE_TO_ONE = prompts.CHAPTER_GENERATION_ONE_TO_ONE
    CHAPTER_GENERATION_ONE_TO_ONE_NEXT = prompts.CHAPTER_GENERATION_ONE_TO_ONE_NEXT
    CHAPTER_GENERATION_ONE_TO_MANY_NEXT = prompts.CHAPTER_GENERATION_ONE_TO_MANY_NEXT
    CHAPTER_REGENERATION_SYSTEM = prompts.CHAPTER_REGENERATION_SYSTEM
    PARTIAL_REGENERATE = prompts.PARTIAL_REGENERATE
    PLOT_ANALYSIS = prompts.PLOT_ANALYSIS
    OUTLINE_EXPAND_SINGLE = prompts.OUTLINE_EXPAND_SINGLE
    OUTLINE_EXPAND_MULTI = prompts.OUTLINE_EXPAND_MULTI
    BOOK_IMPORT_REVERSE_OUTLINES = prompts.BOOK_IMPORT_REVERSE_OUTLINES
    BOOK_IMPORT_REVERSE_PROJECT_SUGGESTION = prompts.BOOK_IMPORT_REVERSE_PROJECT_SUGGESTION
    NOVEL_COVER_PROMPT_TEMPLATE = prompts.NOVEL_COVER_PROMPT_TEMPLATE
    INSPIRATION_DESCRIPTION_SYSTEM = prompts.INSPIRATION_DESCRIPTION_SYSTEM
    INSPIRATION_DESCRIPTION_USER = prompts.INSPIRATION_DESCRIPTION_USER
    INSPIRATION_GENRE_SYSTEM = prompts.INSPIRATION_GENRE_SYSTEM
    INSPIRATION_GENRE_USER = prompts.INSPIRATION_GENRE_USER
    INSPIRATION_QUICK_COMPLETE = prompts.INSPIRATION_QUICK_COMPLETE
    INSPIRATION_THEME_SYSTEM = prompts.INSPIRATION_THEME_SYSTEM
    INSPIRATION_THEME_USER = prompts.INSPIRATION_THEME_USER
    INSPIRATION_TITLE_SYSTEM = prompts.INSPIRATION_TITLE_SYSTEM
    INSPIRATION_TITLE_USER = prompts.INSPIRATION_TITLE_USER
    MCP_TOOL_TEST = prompts.MCP_TOOL_TEST
    MCP_TOOL_TEST_SYSTEM = prompts.MCP_TOOL_TEST_SYSTEM

    @classmethod
    async def build_novel_cover_prompt(
        cls,
        project: Any,
        user_id: str = None,
        db = None,
    ) -> str:
        """Monta o prompt da capa a partir dos dados do projeto (aceita modelo personalizado)."""
        title = (getattr(project, "title", "") or "Sem título").strip()
        genre = (getattr(project, "genre", "") or "Gênero não informado").strip()
        theme = (getattr(project, "theme", "") or "Tema não informado").strip()
        description = (getattr(project, "description", "") or "Sem sinopse adicional").strip()
        output_language = language_name(getattr(project, "language", None))

        compact_description = description[:300]
        template = await cls.get_template_with_fallback(
            "NOVEL_COVER_PROMPT_TEMPLATE",
            user_id=user_id,
            db=db,
        )
        return cls.format_prompt(
            template,
            output_language=output_language,
            title=title,
            genre=genre,
            theme=theme,
            description=compact_description,
        )
    
    @staticmethod
    def format_prompt(template: str, *, output_language: str = DEFAULT_OUTPUT_LANGUAGE, **kwargs) -> str:
        """
        Formata um modelo de prompt.

        Argumentos extras são ignorados (modelos personalizados antigos podem não usar
        todos os campos) e ``output_language`` é sempre fornecido. Falta de argumento
        obrigatório gera ValueError em português.
        """
        values = {**kwargs, "output_language": output_language}
        try:
            return string.Formatter().vformat(template, (), values)
        except KeyError as e:
            raise ValueError(f"Parâmetro obrigatório ausente: {e.args[0]}")

    @classmethod
    async def get_chapter_regeneration_prompt(cls, chapter_number: int, title: str, word_count: int, content: str,
                                        modification_instructions: str, project_context: Dict[str, Any],
                                        style_content: str, target_word_count: int,
                                        user_id: str = None, db = None) -> str:
        """
        获取章节重写提示词（支持用户自定义）
        
        Args:
            chapter_number: 章节序号
            title: 章节标题
            word_count: 原始字数
            content: 原始内容
            modification_instructions: 修改指令
            project_context: 项目上下文
            style_content: 写作风格
            target_word_count: 目标字数
            user_id: 用户ID（可选，用于获取自定义模板）
            db: 数据库会话（可选，用于查询自定义模板）
            
        Returns:
            完整的章节重写提示词
        """
        # 获取系统提示词模板（支持用户自定义）
        if user_id and db:
            system_template = await cls.get_template("CHAPTER_REGENERATION_SYSTEM", user_id, db)
        else:
            system_template = cls.CHAPTER_REGENERATION_SYSTEM
        
        # Idioma de saída vem de project_context (preenchido a partir de Project.language)
        output_language = project_context.get('output_language') or DEFAULT_OUTPUT_LANGUAGE
        try:
            system_template = cls.format_prompt(system_template, output_language=output_language)
        except Exception as exc:
            # Modelo personalizado antigo com chaves soltas: usa o texto como está
            from app.logger import get_logger
            get_logger(__name__).warning(
                f"Não foi possível formatar o template CHAPTER_REGENERATION_SYSTEM; usando o texto original: {exc}"
            )

        prompt_parts = [system_template]
        
        # 原始章节信息
        prompt_parts.append(f"""## 📖 Informações do capítulo original

**Capítulo**: {chapter_number}
**Título**: {title}
**Extensão**: {word_count} palavras

**Conteúdo original**:
{content}

---
""")
        
        # 修改指令
        prompt_parts.append(modification_instructions)
        prompt_parts.append("\n---\n")
        
        # 项目背景信息
        prompt_parts.append(f"""## 🌍 Contexto do projeto

**Título do livro**: {project_context.get('project_title', 'Desconhecido')}
**Gênero**: {project_context.get('genre', 'Não definido')}
**Tema**: {project_context.get('theme', 'Não definido')}
**Ponto de vista narrativo**: {project_context.get('narrative_perspective', 'Terceira pessoa')}
**Mundo**:
- Época: {project_context.get('time_period', 'Não definida')}
- Local: {project_context.get('location', 'Não definido')}
- Atmosfera: {project_context.get('atmosphere', 'Não definida')}

---
""")
        
        # 角色信息
        if project_context.get('characters_info'):
            prompt_parts.append(f"""## 👥 Personagens

{project_context['characters_info']}

---
""")
        
        # 章节大纲
        if project_context.get('chapter_outline'):
            prompt_parts.append(f"""## 📝 Esboço deste capítulo

{project_context['chapter_outline']}

---
""")
        
        # 前置章节上下文
        if project_context.get('previous_context'):
            prompt_parts.append(f"""## 📚 Contexto dos capítulos anteriores

{project_context['previous_context']}

---
""")
        
        # 写作风格要求
        if style_content:
            prompt_parts.append(f"""## 🎨 Requisitos de estilo de escrita

{style_content}

Siga rigorosamente o estilo de escrita acima ao reescrever.

---
""")
        
        # 创作要求
        prompt_parts.append(f"""## ✨ Requisitos de criação

1. **Resolver os problemas**: corrija todos os pontos apontados nas instruções de modificação acima
2. **Manter a coerência**: garanta consistência de enredo, personagens e estilo com os capítulos anteriores e seguintes
3. **Elevar a qualidade**: supere claramente a versão original em ritmo, emoção e descrição
4. **Preservar o melhor**: mantenha as partes excelentes e os acontecimentos-chave do capítulo original
5. **Controle de extensão**: extensão-alvo de cerca de {target_word_count} palavras (pode variar ±10%)
{f'6. **Estilo consistente**: escreva seguindo rigorosamente o estilo de escrita acima' if style_content else ''}
7. **Idioma**: escreva todo o conteúdo em {output_language}

---

## 🎬 Comece a escrever

Escreva agora a nova versão aprimorada do capítulo.

**Observações importantes**:
- Produza diretamente o texto do capítulo, começando pelo conteúdo da história
- **Não** escreva o título do capítulo (como "Capítulo X" ou "Capítulo X: XXX")
- **Não** escreva explicações, comentários ou metadados adicionais
- Escreva apenas o texto puro da história

Comece agora:
""")
        
        return "\n".join(prompt_parts)

    @classmethod
    async def get_mcp_tool_test_prompts(
        cls,
        plugin_name: str,
        user_id: str = None,
        db = None
    ) -> Dict[str, str]:
        """
        Obtém os prompts de teste de ferramentas MCP (aceita modelos personalizados).

        Args:
            plugin_name: nome do plugin
            user_id: ID do usuário (opcional)
            db: sessão do banco de dados (opcional)

        Returns:
            Dicionário com os prompts "user" e "system"
        """
        # 获取用户自定义或系统默认的user提示词
        if user_id and db:
            user_template = await cls.get_template("MCP_TOOL_TEST", user_id, db)
        else:
            user_template = cls.MCP_TOOL_TEST
        
        # 获取用户自定义或系统默认的system提示词
        if user_id and db:
            system_template = await cls.get_template("MCP_TOOL_TEST_SYSTEM", user_id, db)
        else:
            system_template = cls.MCP_TOOL_TEST_SYSTEM
        
        return {
            "user": cls.format_prompt(user_template, plugin_name=plugin_name),
            "system": system_template
        }

    # ========== 自定义提示词支持 ==========
    
    @classmethod
    async def get_template_with_fallback(cls,
                                        template_key: str,
                                        user_id: str = None,
                                        db = None) -> str:
        """
        获取提示词模板（优先用户自定义，支持降级）
        
        Args:
            template_key: 模板键名
            user_id: 用户ID（可选，如果不提供则直接返回系统默认）
            db: 数据库会话（可选）
            
        Returns:
            提示词模板内容
        """
        # 如果没有提供user_id或db，直接返回系统默认
        if not user_id or not db:
            return getattr(cls, template_key, None)
        
        # 尝试获取用户自定义模板
        return await cls.get_template(template_key, user_id, db)
    
    @classmethod
    async def get_template(cls,
                          template_key: str,
                          user_id: str,
                          db) -> str:
        """
        获取提示词模板（优先用户自定义）
        
        Args:
            template_key: 模板键名
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            提示词模板内容
        """
        from sqlalchemy import select
        from app.models.prompt_template import PromptTemplate
        from app.logger import get_logger
        
        logger = get_logger(__name__)
        
        # 1. 尝试从数据库获取用户自定义模板
        result = await db.execute(
            select(PromptTemplate).where(
                PromptTemplate.user_id == user_id,
                PromptTemplate.template_key == template_key,
                PromptTemplate.is_active == True
            )
        )
        custom_template = result.scalar_one_or_none()
        
        if custom_template:
            logger.info(f"✅ 使用用户自定义提示词: user_id={user_id}, template_key={template_key}, template_name={custom_template.template_name}")
            return custom_template.template_content
        
        # 2. 降级到系统默认模板
        logger.info(f"⚪ 使用系统默认提示词: user_id={user_id}, template_key={template_key} (未找到自定义模板)")
        
        # 直接从类属性获取系统默认模板
        template_content = getattr(cls, template_key, None)
        
        if template_content is None:
            logger.warning(f"⚠️ 未找到系统默认模板: {template_key}")
        
        return template_content
    
    @classmethod
    def get_all_system_templates(cls) -> list:
        """
        获取所有系统默认模板的信息
        
        Returns:
            系统模板列表
        """
        templates = []
        
        # 定义所有模板及其元信息
        template_definitions = {
            "NOVEL_COVER_PROMPT_TEMPLATE": {
                "name": "Geração de capa do livro",
                "category": "Capa",
                "description": "Gera o prompt de ilustração da capa a partir dos dados do projeto, em formato vertical, sem texto na imagem",
                "parameters": ["title", "genre", "theme", "description"]
            },
            "WORLD_BUILDING": {
                "name": "Criação de mundo",
                "category": "Criação de mundo",
                "description": "Gera a ambientação do livro: época, local, atmosfera e regras do mundo",
                "parameters": ["title", "theme", "genre", "description"]
            },
            "BOOK_IMPORT_REVERSE_PROJECT_SUGGESTION": {
                "name": "Importação de livro - extração do projeto",
                "category": "Importação de livro",
                "description": "Extrai sinopse, tema, gênero, ponto de vista narrativo e meta de palavras a partir dos 3 primeiros capítulos",
                "parameters": ["title", "sampled_text"]
            },
            "BOOK_IMPORT_REVERSE_OUTLINES": {
                "name": "Importação de livro - esboço dos capítulos",
                "category": "Importação de livro",
                "description": "Gera, a partir do texto dos capítulos, um esboço com a mesma estrutura de OUTLINE_CREATE (lotes de 5 capítulos)",
                "parameters": [
                    "title", "genre", "theme", "narrative_perspective",
                    "start_chapter", "end_chapter", "expected_count", "chapters_text"
                ]
            },
            "CHARACTERS_BATCH_GENERATION": {
                "name": "Geração de personagens em lote",
                "category": "Geração de personagens",
                "description": "Gera vários personagens e organizações de uma vez, criando a rede de relações entre eles",
                "parameters": ["count", "time_period", "location", "atmosphere", "rules", "theme", "genre", "requirements"]
            },
            "SINGLE_CHARACTER_GENERATION": {
                "name": "Geração de personagem único",
                "category": "Geração de personagens",
                "description": "Gera a ficha detalhada de um personagem",
                "parameters": ["project_context", "user_input"]
            },
            "SINGLE_ORGANIZATION_GENERATION": {
                "name": "Geração de organização",
                "category": "Geração de personagens",
                "description": "Gera a ficha detalhada de uma organização ou facção",
                "parameters": ["project_context", "user_input"]
            },
            "OUTLINE_CREATE": {
                "name": "Criação de esboço",
                "category": "Geração de esboço",
                "description": "Gera o esboço completo dos capítulos a partir das informações do projeto",
                "parameters": ["title", "theme", "genre", "chapter_count", "narrative_perspective", "target_words", 
                             "time_period", "location", "atmosphere", "rules", "characters_info", "requirements", "mcp_references"]
            },
            "OUTLINE_CONTINUE": {
                "name": "Continuação de esboço",
                "category": "Geração de esboço",
                "description": "Continua o esboço a partir dos capítulos já existentes",
                "parameters": ["title", "theme", "genre", "narrative_perspective", "chapter_count", "time_period", 
                             "location", "atmosphere", "rules", "characters_info", "current_chapter_count", 
                             "all_chapters_brief", "recent_plot", "memory_context", "mcp_references", 
                             "plot_stage_instruction", "start_chapter", "end_chapter", "story_direction", "requirements"]
            },
            "CHAPTER_GENERATION_ONE_TO_MANY": {
                "name": "Capítulo - modo 1-N (capítulo 1)",
                "category": "Criação de capítulos",
                "description": "Modo 1-N: escreve o capítulo a partir do esboço (para o capítulo 1, sem capítulos anteriores)",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "characters_info"]
            },
            "CHAPTER_GENERATION_ONE_TO_MANY_NEXT": {
                "name": "Capítulo - modo 1-N (capítulo 2 em diante)",
                "category": "Criação de capítulos",
                "description": "Modo 1-N: escreve um novo capítulo com base nos capítulos anteriores (do capítulo 2 em diante)",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "characters_info", "continuation_point",
                             "foreshadow_reminders", "relevant_memories", "story_skeleton", "previous_chapter_summary"]
            },
            "CHAPTER_GENERATION_ONE_TO_ONE": {
                "name": "Capítulo - modo 1-1 (capítulo 1)",
                "category": "Criação de capítulos",
                "description": "Modo 1-1: escreve o capítulo (para o capítulo 1, sem capítulos anteriores)",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "characters_info", "chapter_careers"]
            },
            "CHAPTER_GENERATION_ONE_TO_ONE_NEXT": {
                "name": "Capítulo - modo 1-1 (capítulo 2 em diante)",
                "category": "Criação de capítulos",
                "description": "Modo 1-1: escreve um novo capítulo com base no capítulo anterior (do capítulo 2 em diante)",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "previous_chapter_content",
                             "characters_info", "chapter_careers", "foreshadow_reminders", "relevant_memories"]
            },
            "CHAPTER_REGENERATION_SYSTEM": {
                "name": "Prompt de sistema da reescrita de capítulo",
                "category": "Reescrita de capítulos",
                "description": "Prompt de sistema usado na reescrita de capítulos",
                "parameters": ["chapter_number", "title", "word_count", "content", "modification_instructions",
                             "project_context", "style_content", "target_word_count"]
            },
            "PARTIAL_REGENERATE": {
                "name": "Reescrita parcial",
                "category": "Reescrita de capítulos",
                "description": "Reescreve o trecho selecionado conforme o pedido de modificação do usuário",
                "parameters": ["context_before", "original_word_count", "selected_text", "context_after",
                             "user_instructions", "length_requirement", "style_content"]
            },
            "PLOT_ANALYSIS": {
                "name": "Análise de enredo",
                "category": "Análise de enredo",
                "description": "Analisa a fundo o enredo do capítulo: ganchos, foreshadowing, conflitos etc.",
                "parameters": ["chapter_number", "title", "content", "word_count"]
            },
            "OUTLINE_EXPAND_SINGLE": {
                "name": "Expansão do esboço (lote único)",
                "category": "Expansão de enredo",
                "description": "Desdobra um nó do esboço em planejamento detalhado de capítulos (lote único)",
                "parameters": ["project_title", "project_genre", "project_theme", "project_narrative_perspective", 
                             "project_world_time_period", "project_world_location", "project_world_atmosphere", 
                             "characters_info", "outline_order_index", "outline_title", "outline_content", 
                             "context_info", "strategy_instruction", "target_chapter_count", "scene_instruction", "scene_field"]
            },
            "OUTLINE_EXPAND_MULTI": {
                "name": "Expansão do esboço (em lotes)",
                "category": "Expansão de enredo",
                "description": "Desdobra um nó do esboço em planejamento detalhado de capítulos (em lotes)",
                "parameters": ["project_title", "project_genre", "project_theme", "project_narrative_perspective", 
                             "project_world_time_period", "project_world_location", "project_world_atmosphere", 
                             "characters_info", "outline_order_index", "outline_title", "outline_content", 
                             "context_info", "previous_context", "strategy_instruction", "start_index", 
                             "end_index", "target_chapter_count", "scene_instruction", "scene_field"]
            },
            "MCP_TOOL_TEST": {
                "name": "Teste de ferramentas MCP (prompt do usuário)",
                "category": "Teste MCP",
                "description": "Prompt do usuário usado para testar as funções de um plugin MCP",
                "parameters": ["plugin_name"]
            },
            "MCP_TOOL_TEST_SYSTEM": {
                "name": "Teste de ferramentas MCP (prompt de sistema)",
                "category": "Teste MCP",
                "description": "Prompt de sistema usado para testar as funções de um plugin MCP",
                "parameters": []
            },
            "MCP_WORLD_BUILDING_PLANNING": {
                "name": "Planejamento do mundo via MCP",
                "category": "Reforço MCP",
                "description": "Usa ferramentas MCP para pesquisar material de apoio à criação do mundo",
                "parameters": ["title", "genre", "theme", "description"]
            },
            "MCP_CHARACTER_PLANNING": {
                "name": "Planejamento de personagens via MCP",
                "category": "Reforço MCP",
                "description": "Usa ferramentas MCP para pesquisar material de apoio à criação de personagens",
                "parameters": ["title", "genre", "theme", "time_period", "location"]
            },
            "AUTO_CHARACTER_ANALYSIS": {
                "name": "Análise automática de personagens",
                "category": "Introdução automática de personagens",
                "description": "Analisa o esboço recém-gerado e decide se é preciso introduzir novos personagens",
                "parameters": ["title", "genre", "theme", "time_period", "location", "atmosphere",
                             "existing_characters", "new_outlines", "start_chapter", "end_chapter"]
            },
            "AUTO_CHARACTER_GENERATION": {
                "name": "Geração automática de personagens",
                "category": "Introdução automática de personagens",
                "description": "Gera automaticamente a ficha completa de novos personagens conforme as necessidades da trama",
                "parameters": ["title", "genre", "theme", "time_period", "location", "atmosphere", "rules",
                             "existing_characters", "plot_context", "character_specification", "mcp_references"]
            },
            "AUTO_ORGANIZATION_ANALYSIS": {
                "name": "Análise automática de organizações",
                "category": "Introdução automática de organizações",
                "description": "Analisa o esboço recém-gerado e decide se é preciso introduzir novas organizações",
                "parameters": ["title", "genre", "theme", "time_period", "location", "atmosphere",
                             "existing_organizations", "existing_characters", "all_chapters_brief", "start_chapter", "chapter_count", "plot_stage", "story_direction"]
            },
            "AUTO_ORGANIZATION_GENERATION": {
                "name": "Geração automática de organizações",
                "category": "Introdução automática de organizações",
                "description": "Gera automaticamente a ficha completa de novas organizações conforme as necessidades da trama",
                "parameters": ["title", "genre", "theme", "time_period", "location", "atmosphere", "rules",
                             "existing_organizations", "existing_characters", "plot_context", "organization_specification", "mcp_references"]
            },
            "CAREER_SYSTEM_GENERATION": {
                "name": "Geração do sistema de carreiras",
                "category": "Criação de mundo",
                "description": "Gera um sistema de carreiras completo (principal e secundária) a partir do mundo e da sinopse do projeto",
                "parameters": ["title", "genre", "theme", "description", "time_period", "location", "atmosphere", "rules"]
            },
            "INSPIRATION_TITLE_SYSTEM": {
                "name": "Modo inspiração - geração de título (prompt de sistema)",
                "category": "Modo inspiração",
                "description": "Prompt de sistema que gera 6 sugestões de título a partir da ideia original do usuário",
                "parameters": ["initial_idea"]
            },
            "INSPIRATION_TITLE_USER": {
                "name": "Modo inspiração - geração de título (prompt do usuário)",
                "category": "Modo inspiração",
                "description": "Prompt do usuário que pede 6 sugestões de título a partir da ideia original",
                "parameters": ["initial_idea"]
            },
            "INSPIRATION_DESCRIPTION_SYSTEM": {
                "name": "Modo inspiração - geração de sinopse (prompt de sistema)",
                "category": "Modo inspiração",
                "description": "Prompt de sistema que gera 6 opções de sinopse a partir da ideia e do título",
                "parameters": ["initial_idea", "title"]
            },
            "INSPIRATION_DESCRIPTION_USER": {
                "name": "Modo inspiração - geração de sinopse (prompt do usuário)",
                "category": "Modo inspiração",
                "description": "Prompt do usuário que pede 6 opções de sinopse a partir da ideia e do título",
                "parameters": ["initial_idea", "title"]
            },
            "INSPIRATION_THEME_SYSTEM": {
                "name": "Modo inspiração - geração de tema (prompt de sistema)",
                "category": "Modo inspiração",
                "description": "Prompt de sistema que gera 6 opções de tema profundas a partir do título e da sinopse",
                "parameters": ["initial_idea", "title", "description"]
            },
            "INSPIRATION_THEME_USER": {
                "name": "Modo inspiração - geração de tema (prompt do usuário)",
                "category": "Modo inspiração",
                "description": "Prompt do usuário que pede 6 opções de tema a partir do título e da sinopse",
                "parameters": ["initial_idea", "title", "description"]
            },
            "INSPIRATION_GENRE_SYSTEM": {
                "name": "Modo inspiração - geração de gênero (prompt de sistema)",
                "category": "Modo inspiração",
                "description": "Prompt de sistema que gera 6 etiquetas de gênero adequadas às informações do livro",
                "parameters": ["initial_idea", "title", "description", "theme"]
            },
            "INSPIRATION_GENRE_USER": {
                "name": "Modo inspiração - geração de gênero (prompt do usuário)",
                "category": "Modo inspiração",
                "description": "Prompt do usuário que pede 6 etiquetas de gênero a partir das informações do livro",
                "parameters": ["initial_idea", "title", "description", "theme"]
            },
            "INSPIRATION_QUICK_COMPLETE": {
                "name": "Modo inspiração - preenchimento automático",
                "category": "Modo inspiração",
                "description": "Completa a proposta do livro a partir das informações parciais fornecidas pelo usuário",
                "parameters": ["existing"]
            }
        }
        
        for key, info in template_definitions.items():
            template_content = getattr(cls, key, None)
            if template_content:
                templates.append({
                    "template_key": key,
                    "template_name": info["name"],
                    "category": info["category"],
                    "description": info["description"],
                    "parameters": info["parameters"],
                    "content": template_content
                })
        
        # 加载 Skill 提示词模板
        try:
            skill_templates = get_all_skills_cached()
            templates.extend(skill_templates)
        except Exception as e:
            from app.logger import get_logger
            get_logger(__name__).warning(f"加载 Skill 模板失败: {e}")
        
        return templates
    
    @classmethod
    def get_system_template_info(cls, template_key: str) -> dict:
        """
        获取指定系统模板的信息
        
        Args:
            template_key: 模板键名
            
        Returns:
            模板信息字典
        """
        all_templates = cls.get_all_system_templates()
        for template in all_templates:
            if template["template_key"] == template_key:
                return template
        return None

# ========== 全局实例 ==========
prompt_service = PromptService()
