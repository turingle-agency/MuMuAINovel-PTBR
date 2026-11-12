"""提示词管理服务"""
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
        return f"{base_prompt}\n\n请直接输出章节正文内容，不要包含章节标题和其他说明文字。"


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

    NOVEL_COVER_PROMPT_TEMPLATE = """创作一幅高质量小说封面插图，适用于竖版书籍封面。

小说标题是：“{title}”。
类型为 {genre}。核心主题是 {theme}。故事摘要如下：{description}

画面应具有电影感、精致、富有氛围和情感表现力，并具备清晰的视觉焦点和强烈的象征性意象。请优先展现符合小说类型的视觉叙事和情绪，而不是死板地描绘具体场景。

这必须看起来像一幅专业的网络小说或实体出版物风格的封面。

硬性要求：
- 必须在画面醒目位置包含小说标题文字：“{title}”，文字排版需极具艺术感，并与小说的 {genre} 类型风格完美融合。
- 适用于标准小说封面的竖版构图（2:3 比例）。
- 画面中只能出现标题文字，绝不能出现作者名字、副标题或其他无关的随机字母。
- 无标志 (Logo)。
- 无水印。
- 无边框。
- 无 UI 元素。
- 无样机展示效果 (Mockup)。

最终图像必须是一张完整、专业的书籍封面艺术作品，背景插画与标题排版需相得益彰。"""

    @classmethod
    async def build_novel_cover_prompt(
        cls,
        project: Any,
        user_id: str = None,
        db = None,
    ) -> str:
        """基于项目基础信息构建小说封面提示词，支持用户自定义模板"""
        title = (getattr(project, "title", "") or "未命名小说").strip()
        genre = (getattr(project, "genre", "") or "未指定类型").strip()
        theme = (getattr(project, "theme", "") or "未指定主题").strip()
        description = (getattr(project, "description", "") or "无额外简介").strip()

        compact_description = description[:300]
        template = await cls.get_template_with_fallback(
            "NOVEL_COVER_PROMPT_TEMPLATE",
            user_id=user_id,
            db=db,
        )
        return template.format(
            title=title,
            genre=genre,
            theme=theme,
            description=compact_description,
        )
    
    # ========== V2版本提示词模板（RTCO框架）==========
    
    # MCP工具测试提示词
    MCP_TOOL_TEST = """你是MCP插件测试助手，需要测试插件 '{plugin_name}' 的功能。

⚠️ 重要规则：生成参数时，必须严格使用工具 schema 中定义的原始参数名称，不要转换为 snake_case 或其他格式。
例如：如果 schema 中是 'nextThoughtNeeded'，就必须使用 'nextThoughtNeeded'，不能改成 'next_thought_needed'。

请选择一个合适的工具进行测试，优先选择搜索、查询类工具。
生成真实有效的测试参数（例如搜索"人工智能最新进展"而不是"test"）。

现在开始测试这个插件。"""

    MCP_TOOL_TEST_SYSTEM = """你是专业的API测试工具。当给定工具列表时，选择一个工具并使用合适的参数调用它。

⚠️ 关键规则：调用工具时，必须严格使用 schema 中定义的原始参数名，不要自行转换命名风格。
- 如果参数名是 camelCase（如 nextThoughtNeeded），就使用 camelCase
- 如果参数名是 snake_case（如 next_thought），就使用 snake_case
- 保持与 schema 中定义的完全一致，包括大小写和命名风格"""
    
    # 灵感模式 - 书名生成（系统提示词）
    INSPIRATION_TITLE_SYSTEM = """你是一位专业的小说创作顾问。
用户的原始想法：{initial_idea}

请根据用户的想法，生成6个吸引人的书名建议，要求：
1. 紧扣用户的原始想法和核心故事构思
2. 富有创意和吸引力
3. 涵盖不同的风格倾向
4. 书名中不要带有"《》"符号

返回JSON格式：
{{
    "prompt": "根据你的想法，我为你准备了几个书名建议：",
    "options": ["书名1", "书名2", "书名3", "书名4", "书名5", "书名6"]
}}

只返回纯JSON，不要有其他文字。"""

    # 灵感模式 - 书名生成（用户提示词）
    INSPIRATION_TITLE_USER = "用户的想法：{initial_idea}\n请生成6个书名建议"

    # 灵感模式 - 简介生成（系统提示词）
    INSPIRATION_DESCRIPTION_SYSTEM = """你是一位专业的小说创作顾问。
用户的原始想法：{initial_idea}
已确定的书名：{title}

请生成6个精彩的小说简介，要求：
1. 必须紧扣用户的原始想法，确保简介是原始想法的具体展开
2. 符合已确定的书名风格
3. 简洁有力，每个50-100字
4. 包含核心冲突
5. 涵盖不同的故事走向，但都基于用户的原始构思

返回JSON格式：
{{"prompt":"选择一个简介：","options":["简介1","简介2","简介3","简介4","简介5","简介6"]}}

只返回纯JSON，不要有其他文字，不要换行。"""

    # 灵感模式 - 简介生成（用户提示词）
    INSPIRATION_DESCRIPTION_USER = "原始想法：{initial_idea}\n书名：{title}\n请生成6个简介选项"

    # 灵感模式 - 主题生成（系统提示词）
    INSPIRATION_THEME_SYSTEM = """你是一位专业的小说创作顾问。
用户的原始想法：{initial_idea}
小说信息：
- 书名：{title}
- 简介：{description}

请生成6个深刻的主题选项，要求：
1. 必须与用户的原始想法保持高度一致
2. 符合书名和简介的风格
3. 有深度和思想性
4. 每个50-150字
5. 涵盖不同角度（如：成长、复仇、救赎、探索等），但都围绕用户的核心构思

返回JSON格式：
{{"prompt":"这本书的核心主题是什么？","options":["主题1","主题2","主题3","主题4","主题5","主题6"]}}

只返回纯JSON，不要有其他文字，不要换行。"""

    # 灵感模式 - 主题生成（用户提示词）
    INSPIRATION_THEME_USER = "原始想法：{initial_idea}\n书名：{title}\n简介：{description}\n请生成6个主题选项"

    # 灵感模式 - 类型生成（系统提示词）
    INSPIRATION_GENRE_SYSTEM = """你是一位专业的小说创作顾问。
用户的原始想法：{initial_idea}
小说信息：
- 书名：{title}
- 简介：{description}
- 主题：{theme}

请生成6个合适的类型标签（每个2-4字），要求：
1. 必须符合用户原始想法中暗示的类型倾向
2. 符合小说整体风格
3. 可以多选组合

常见类型：玄幻、都市、科幻、武侠、仙侠、历史、言情、悬疑、奇幻、修仙等

返回JSON格式：
{{"prompt":"选择类型标签（可多选）：","options":["类型1","类型2","类型3","类型4","类型5","类型6"]}}

只返回紧凑的纯JSON，不要换行，不要有其他文字。"""

    # 灵感模式 - 类型生成（用户提示词）
    INSPIRATION_GENRE_USER = "原始想法：{initial_idea}\n书名：{title}\n简介：{description}\n主题：{theme}\n请生成6个类型标签"

    # 灵感模式智能补全提示词
    INSPIRATION_QUICK_COMPLETE = """你是一位专业的小说创作顾问。用户提供了部分小说信息，请补全缺失的字段。

用户已提供的信息：
{existing}

请生成完整的小说方案，包含：
1. title: 书名（3-6字，如果用户已提供则保持原样）
2. description: 简介（50-100字，必须基于用户提供的信息，不要偏离原意）
3. theme: 核心主题（30-50字，必须与用户提供的信息保持一致）
4. genre: 类型标签数组（2-3个）

重要：所有补全的内容都必须与用户提供的信息保持高度关联，确保前后一致性。

返回JSON格式：
{{
    "title": "书名",
    "description": "简介内容...",
    "theme": "主题内容...",
    "genre": ["类型1", "类型2"]
}}

只返回纯JSON，不要有其他文字。"""
    # 拆书导入-反向项目提炼提示词
    BOOK_IMPORT_REVERSE_PROJECT_SUGGESTION = """<system>
你是资深网文策划编辑，擅长从小说正文中反向提炼项目立项信息。
</system>

<task>
【任务】
基于提供的前3章内容，提炼该小说的核心立项信息，用于创建新项目。

【目标】
在不偏离原文的前提下，输出可直接用于项目初始化的结构化信息。
</task>

<input priority="P0">
【输入信息】
书名：{title}
前3章内容：
{sampled_text}
</input>

<output priority="P0">
【输出格式】
仅输出一个纯JSON对象（不要markdown、不要代码块、不要解释）：

{{
  "description": "小说简介",
  "theme": "核心主题",
  "genre": "小说类型",
  "narrative_perspective": "第一人称/第三人称/全知视角",
  "target_words": 100000
}}

【字段要求】
1) description：120-260字，聚焦主角、核心冲突、主线目标与故事张力。
2) theme：120-260字，提炼作品想表达的核心命题。
3) genre：2-12字，如都市、玄幻、悬疑、科幻、言情等。
4) narrative_perspective：只能是“第一人称”或“第三人称”或“全知视角”。
5) target_words：整数。按网文体量合理预估；无法判断时返回100000。
</output>

<constraints>
【必须遵守】
✅ 严格基于已给正文内容，不凭空添加关键设定
✅ 保持信息自洽，避免互相矛盾
✅ 输出必须是可解析JSON对象
✅ 小说的genre可以由多个类型组成

【禁止事项】
❌ 输出JSON以外的任何文字
❌ 使用markdown标记或代码块包裹
❌ narrative_perspective输出枚举值之外的内容
❌ target_words输出非整数
</constraints>"""

    # 拆书导入-反向生成章节大纲（严格对齐 OUTLINE_CREATE 结构）
    BOOK_IMPORT_REVERSE_OUTLINES = """<system>
你是资深网文总编与剧情策划，擅长基于已完成章节反向提炼标准化章节大纲。
</system>

<task>
【任务】
基于给定的章节正文（每批最多5章），为每章反向生成对应大纲结构。

【核心目标】
输出结构必须与系统现有大纲生成结构严格一致（与 OUTLINE_CREATE 字段一致），用于直接入库。
</task>

<project priority="P0">
【项目信息】
书名：{title}
类型：{genre}
主题：{theme}
叙事视角：{narrative_perspective}
</project>

<input priority="P0">
【批次范围】
第{start_chapter}章 - 第{end_chapter}章（共{expected_count}章）

【章节内容】
{chapters_text}
</input>

<output priority="P0">
【输出格式】
仅输出纯JSON数组（不要markdown、不要代码块、不要解释）。
数组长度必须严格等于 {expected_count}。

每个对象字段必须严格为：
[
  {{
    "chapter_number": 1,
    "title": "章节标题",
    "summary": "章节概要（200-600字）：主要情节、角色互动、关键事件、冲突与转折",
    "scenes": ["场景1描述", "场景2描述"],
    "characters": [
      {{"name": "角色名1", "type": "character"}},
      {{"name": "组织/势力名1", "type": "organization"}}
    ],
    "key_points": ["情节要点1", "情节要点2"],
    "emotion": "本章情感基调",
    "goal": "本章叙事目标"
  }}
]

【字段约束】
- chapter_number：必须与输入章节号一致
- title：必须与输入章节标题一致
- summary：根据本章正文反向提炼，不得臆造未出现关键事件
- scenes：2-6条
- characters：可为空；type 仅允许 character 或 organization
- key_points：2-6条
- emotion：一句话
- goal：一句话
</output>

<constraints>
【必须遵守】
✅ 严格一章对应一个对象，数量与顺序完全一致
✅ 字段名、字段层级、字段类型严格一致
✅ 仅基于输入正文提炼，不擅自扩展设定
✅ 输出必须可被JSON直接解析

【禁止事项】
❌ 输出JSON之外任何文本
❌ 缺失字段或新增字段
❌ chapter_number/title 与输入不一致
❌ 使用 markdown 或代码块
</constraints>"""

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
        except Exception:
            # Modelo personalizado antigo com chaves soltas: usa o texto como está
            pass

        prompt_parts = [system_template]
        
        # 原始章节信息
        prompt_parts.append(f"""## 📖 原始章节信息

**章节**：第{chapter_number}章
**标题**：{title}
**字数**：{word_count} palavras

**原始内容**：
{content}

---
""")
        
        # 修改指令
        prompt_parts.append(modification_instructions)
        prompt_parts.append("\n---\n")
        
        # 项目背景信息
        prompt_parts.append(f"""## 🌍 项目背景信息

**小说标题**：{project_context.get('project_title', '未知')}
**题材**：{project_context.get('genre', '未设定')}
**主题**：{project_context.get('theme', '未设定')}
**叙事视角**：{project_context.get('narrative_perspective', '第三人称')}
**世界观设定**：
- 时代背景：{project_context.get('time_period', '未设定')}
- 地理位置：{project_context.get('location', '未设定')}
- 氛围基调：{project_context.get('atmosphere', '未设定')}

---
""")
        
        # 角色信息
        if project_context.get('characters_info'):
            prompt_parts.append(f"""## 👥 角色信息

{project_context['characters_info']}

---
""")
        
        # 章节大纲
        if project_context.get('chapter_outline'):
            prompt_parts.append(f"""## 📝 本章大纲

{project_context['chapter_outline']}

---
""")
        
        # 前置章节上下文
        if project_context.get('previous_context'):
            prompt_parts.append(f"""## 📚 前置章节上下文

{project_context['previous_context']}

---
""")
        
        # 写作风格要求
        if style_content:
            prompt_parts.append(f"""## 🎨 写作风格要求

{style_content}

请在重新创作时严格遵循上述写作风格。

---
""")
        
        # 创作要求
        prompt_parts.append(f"""## ✨ 创作要求

1. **解决问题**：针对上述修改指令中提到的所有问题进行改进
2. **保持连贯**：确保与前后章节的情节、人物、风格保持一致
3. **提升质量**：在节奏、情感、描写等方面明显优于原版
4. **保留精华**：保持原章节中优秀的部分和关键情节
5. **字数控制**：目标长度约 {target_word_count} palavras（可适当浮动±10%）
{f'6. **风格一致**：严格按照上述写作风格进行创作' if style_content else ''}

---

## 🎬 开始创作

请现在开始创作改进后的新版本章节内容。

**重要提示**：
- 直接输出章节正文内容，从故事内容开始写
- **不要**输出章节标题（如"第X章"、"第X章：XXX"等）
- **不要**输出任何额外的说明、注释或元数据
- 只需要纯粹的故事正文内容

现在开始：
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
        获取MCP工具测试的提示词（支持自定义）
        
        Args:
            plugin_name: 插件名称
            user_id: 用户ID（可选）
            db: 数据库会话（可选）
            
        Returns:
            包含user和system提示词的字典
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
                "name": "小说封面生成",
                "category": "Capa",
                "description": "根据项目基础信息生成小说封面绘制提示词，适用于竖版书籍封面",
                "parameters": ["title", "genre", "theme", "description"]
            },
            "WORLD_BUILDING": {
                "name": "Criação de mundo",
                "category": "Criação de mundo",
                "description": "Gera a ambientação do livro: época, local, atmosfera e regras do mundo",
                "parameters": ["title", "theme", "genre", "description"]
            },
            "BOOK_IMPORT_REVERSE_PROJECT_SUGGESTION": {
                "name": "拆书导入-反向项目提炼",
                "category": "Importação de livro",
                "description": "基于前3章内容反向提炼简介、主题、类型、叙事视角与目标字数",
                "parameters": ["title", "sampled_text"]
            },
            "BOOK_IMPORT_REVERSE_OUTLINES": {
                "name": "拆书导入-反向章节大纲",
                "category": "Importação de livro",
                "description": "基于章节正文反向生成与OUTLINE_CREATE一致结构的大纲（单批次5章）",
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
                "name": "MCP工具测试(用户提示词)",
                "category": "Teste MCP",
                "description": "用于测试MCP插件功能的用户提示词",
                "parameters": ["plugin_name"]
            },
            "MCP_TOOL_TEST_SYSTEM": {
                "name": "MCP工具测试(系统提示词)",
                "category": "Teste MCP",
                "description": "用于测试MCP插件功能的系统提示词",
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
                "name": "灵感模式-书名生成(系统提示词)",
                "category": "Modo inspiração",
                "description": "根据用户的原始想法生成6个书名建议的系统提示词",
                "parameters": ["initial_idea"]
            },
            "INSPIRATION_TITLE_USER": {
                "name": "灵感模式-书名生成(用户提示词)",
                "category": "Modo inspiração",
                "description": "根据用户的原始想法生成6个书名建议的用户提示词",
                "parameters": ["initial_idea"]
            },
            "INSPIRATION_DESCRIPTION_SYSTEM": {
                "name": "灵感模式-简介生成(系统提示词)",
                "category": "Modo inspiração",
                "description": "根据用户想法和书名生成6个简介选项的系统提示词",
                "parameters": ["initial_idea", "title"]
            },
            "INSPIRATION_DESCRIPTION_USER": {
                "name": "灵感模式-简介生成(用户提示词)",
                "category": "Modo inspiração",
                "description": "根据用户想法和书名生成6个简介选项的用户提示词",
                "parameters": ["initial_idea", "title"]
            },
            "INSPIRATION_THEME_SYSTEM": {
                "name": "灵感模式-主题生成(系统提示词)",
                "category": "Modo inspiração",
                "description": "根据书名和简介生成6个深刻的主题选项的系统提示词",
                "parameters": ["initial_idea", "title", "description"]
            },
            "INSPIRATION_THEME_USER": {
                "name": "灵感模式-主题生成(用户提示词)",
                "category": "Modo inspiração",
                "description": "根据书名和简介生成6个深刻的主题选项的用户提示词",
                "parameters": ["initial_idea", "title", "description"]
            },
            "INSPIRATION_GENRE_SYSTEM": {
                "name": "灵感模式-类型生成(系统提示词)",
                "category": "Modo inspiração",
                "description": "根据小说信息生成6个合适的类型标签的系统提示词",
                "parameters": ["initial_idea", "title", "description", "theme"]
            },
            "INSPIRATION_GENRE_USER": {
                "name": "灵感模式-类型生成(用户提示词)",
                "category": "Modo inspiração",
                "description": "根据小说信息生成6个合适的类型标签的用户提示词",
                "parameters": ["initial_idea", "title", "description", "theme"]
            },
            "INSPIRATION_QUICK_COMPLETE": {
                "name": "灵感模式-智能补全",
                "category": "Modo inspiração",
                "description": "根据用户提供的部分信息智能补全完整的小说方案",
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
