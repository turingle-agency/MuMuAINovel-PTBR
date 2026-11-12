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
    
# 批量角色生成提示词 V2（RTCO框架）
# 大纲生成提示词 V2（RTCO框架）
# 大纲续写提示词 V2（RTCO框架 - 简化版）
# 章节生成 - 1-N模式（第1章）
    CHAPTER_GENERATION_ONE_TO_MANY = """<system>
你是《{project_title}》的作者，一位专注于{genre}类型的网络小说家。
</system>

<task>
【创作任务】
撰写第{chapter_number}章《{chapter_title}》的完整正文。

【基本要求】
- 目标字数：{target_word_count}字（允许±200字浮动）
- 叙事视角：{narrative_perspective}
</task>

<outline priority="P0">
【本章大纲 - 必须遵循】
{chapter_outline}
</outline>

<characters priority="P1">
【本章角色 - 请严格遵循角色设定】
{characters_info}

⚠️ 角色互动须知：
- 角色之间的对话和行为必须符合其关系设定（如师徒、敌对等）
- 涉及组织的情节须体现角色在组织中的身份和职位
- 角色的能力表现须符合其职业和阶段设定
</characters>

<careers priority="P2">
【本章职业】
{chapter_careers}
</careers>

<foreshadow_reminders priority="P2">
【🎯 伏笔提醒】
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
【相关记忆】
{relevant_memories}
</memory>

<constraints>
【必须遵守】
✅ 严格按照大纲推进情节
✅ 保持角色性格、说话方式一致
✅ 角色互动须符合关系设定（师徒、朋友、敌对等）
✅ 组织相关情节须体现成员身份和职位层级
✅ 字数控制在目标范围内
✅ 如有伏笔提醒，请在本章中适当埋入或回收相应伏笔

【禁止事项】
❌ 输出章节标题、序号等元信息
❌ 使用"总之"、"综上所述"等AI常见总结语
❌ 在结尾处使用开放式反问
❌ 添加作者注释或创作说明
❌ 角色行为超出其职业阶段的能力范围
</constraints>

<output>
【输出规范】
直接输出小说正文内容，从故事场景或动作开始。
无需任何前言、后记或解释性文字。

现在开始创作：
</output>"""

    # 章节生成 - 1-1模式（第1章）
    CHAPTER_GENERATION_ONE_TO_ONE = """<system>
你是《{project_title}》的作者，一位专注于{genre}类型的网络小说家。
</system>

<task priority="P0">
【创作任务】
撰写第{chapter_number}章《{chapter_title}》的完整正文。

【基本要求】
- 目标字数：{target_word_count}字（允许±200字浮动）
- 叙事视角：{narrative_perspective}
</task>

<outline priority="P0">
【本章大纲】
{chapter_outline}
</outline>

<characters priority="P1">
【本章角色】
{characters_info}
</characters>

<careers priority="P2">
【本章职业】
{chapter_careers}
</careers>

<foreshadow_reminders priority="P2">
【🎯 伏笔提醒】
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
【相关记忆】
{relevant_memories}
</memory>

<constraints>
【必须遵守】
✅ 严格按照大纲推进情节
✅ 保持角色性格、说话方式一致
✅ 字数需要严格控制在目标字数内
✅ 如有伏笔提醒，请在本章中适当埋入或回收相应伏笔

【禁止事项】
❌ 输出章节标题、序号等元信息
❌ 使用"总之"、"综上所述"等AI常见总结语
❌ 添加作者注释或创作说明
❌ 生成字数禁止超过目标字数
</constraints>

<output>
【输出规范】
直接输出小说正文内容，从故事场景或动作开始。
无需任何前言、后记或解释性文字。

现在开始创作：
</output>"""

    # 章节生成 - 1-1模式（第2章及以后）
    CHAPTER_GENERATION_ONE_TO_ONE_NEXT = """<system>
你是《{project_title}》的作者，一位专注于{genre}类型的网络小说家。
</system>

<task priority="P0">
【创作任务】
撰写第{chapter_number}章《{chapter_title}》的完整正文。

【基本要求】
- 目标字数：{target_word_count}字（允许±200字浮动）
- 叙事视角：{narrative_perspective}
</task>

<outline priority="P0">
【本章大纲】
{chapter_outline}
</outline>

<previous_chapter_summary priority="P1">
【上一章剧情概要】
{previous_chapter_summary}
</previous_chapter_summary>

<recent_context priority="P1">
【最近章节摘要 - 故事脉络参考】
{recent_chapters_context}
</recent_context>

<previous_chapter priority="P1">
【上一章完整正文】
{previous_chapter_content}
</previous_chapter>

<characters priority="P1">
【本章角色】
{characters_info}
</characters>

<careers priority="P2">
【本章职业】
{chapter_careers}
</careers>

<foreshadow_reminders priority="P2">
【🎯 伏笔提醒】
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
【相关记忆】
{relevant_memories}
</memory>

<constraints>
【必须遵守】
✅ 严格按照大纲推进情节
✅ 自然承接上一章末尾内容，保持连贯性
✅ 保持角色性格、说话方式一致
✅ 字数需要严格控制在目标字数内
✅ 如有伏笔提醒，请在本章中适当埋入或回收相应伏笔

【禁止事项】
❌ 输出章节标题、序号等元信息
❌ 使用"总之"、"综上所述"等AI常见总结语
❌ 在结尾处使用开放式反问
❌ 添加作者注释或创作说明
❌ 重复上一章已发生的事件
❌ 生成字数禁止超过目标字数
</constraints>

<output>
【输出规范】
直接输出小说正文内容，从故事场景或动作开始。
无需任何前言、后记或解释性文字。

现在开始创作：
</output>"""

    # 章节生成 - 1-N模式（第2章及以后）
    CHAPTER_GENERATION_ONE_TO_MANY_NEXT = """<system>
你是《{project_title}》的作者，一位专注于{genre}类型的网络小说家。
</system>

<task>
【创作任务】
撰写第{chapter_number}章《{chapter_title}》的完整正文。

【基本要求】
- 目标字数：{target_word_count}字（允许±200字浮动）
- 叙事视角：{narrative_perspective}
</task>

<outline priority="P0">
【本章大纲 - 必须遵循】
{chapter_outline}
</outline>

<recent_context priority="P1">
【最近章节规划 - 故事脉络参考】
{recent_chapters_context}
</recent_context>

<continuation priority="P0">
【衔接锚点 - 必须承接】
上一章完整正文：
「{continuation_point}」

【🔴 上一章已完成剧情（禁止重复！）】
{previous_chapter_summary}

⚠️ 严重警告：
1. 上述"已完成剧情"和"衔接锚点"是**已经写过的**内容
2. 本章必须推进到**新的情节点**，绝对不能重新叙述已经发生的事件
3. 本章应承接上一章最后的情境继续推进，不要复述上一章完整正文
4. 如果上一章以对话或场景结束，请从结束后的动作、反应或场景转换开始
</continuation>

<characters priority="P1">
【本章角色 - 请严格遵循角色设定】
{characters_info}

⚠️ 角色互动须知：
- 角色之间的对话和行为必须符合其关系设定（如师徒、敌对等）
- 涉及组织的情节须体现角色在组织中的身份和职位
- 角色的能力表现须符合其职业和阶段设定
</characters>

<careers priority="P2">
【本章职业】
{chapter_careers}
</careers>

<foreshadow_reminders priority="P1">
【🎯 伏笔提醒 - 需关注】
{foreshadow_reminders}
</foreshadow_reminders>

<memory priority="P2">
【相关记忆 - 参考】
{relevant_memories}
</memory>

<constraints>
【必须遵守】
✅ 严格按照大纲推进情节
✅ 自然承接上一章结尾，不重复已发生事件
✅ 保持角色性格、说话方式一致
✅ 角色互动须符合关系设定（师徒、朋友、敌对等）
✅ 组织相关情节须体现成员身份和职位层级
✅ 字数控制在目标范围内
✅ 如有伏笔提醒，请在本章中适当埋入或回收相应伏笔

【🔴 反重复特别指令】
✅ 检查本章开篇是否与"衔接锚点"内容重复
✅ 检查本章情节是否与"上一章已完成剧情"重复
✅ 确保本章推进到了大纲中规划的新事件

【禁止事项】
❌ 输出章节标题、序号等元信息
❌ 使用"总之"、"综上所述"等AI常见总结语
❌ 在结尾处使用开放式反问
❌ 添加作者注释或创作说明
❌ 重复叙述上一章已发生的事件（包括环境描写、心理活动）
❌ 在开篇使用"接上回"、"书接上文"等套话
❌ 角色行为超出其职业阶段的能力范围
</constraints>

<output>
【输出规范】
直接输出小说正文内容，从故事场景或动作开始。
无需任何前言、后记或解释性文字。

现在开始创作：
</output>"""

# 单个组织生成提示词 V2（RTCO框架）
# 情节分析提示词 V2（RTCO框架 + 伏笔ID追踪）
    PLOT_ANALYSIS = """<system>
你是专业的小说编辑和剧情分析师，擅长深度剖析章节内容。
</system>

<task>
【分析任务】
全面分析第{chapter_number}章《{title}》的剧情要素、钩子、伏笔、冲突和角色发展。

【🔴 伏笔追踪任务（重要）】
系统已提供【已埋入伏笔列表】，当你识别到章节中有回收伏笔时：
1. 必须从列表中找出对应的伏笔ID
2. 在 foreshadows 数组中使用 reference_foreshadow_id 字段关联
3. 如果无法确定是哪个伏笔，reference_foreshadow_id 填 null
</task>

<chapter priority="P0">
【章节信息】
章节：第{chapter_number}章
标题：{title}
字数：{word_count}字

【章节内容】
{content}
</chapter>

<existing_foreshadows priority="P1">
【已埋入伏笔列表 - 用于回收匹配】
以下是本项目中已埋入但尚未回收的伏笔，分析时如发现章节内容回收了某个伏笔，请使用对应的ID：

{existing_foreshadows}
</existing_foreshadows>

<characters priority="P1">
【项目角色信息 - 用于角色状态分析】
以下是项目中已有的角色列表，分析 character_states 和 relationship_changes 时请使用这些角色的准确名称：

{characters_info}
</characters>

<analysis_framework priority="P0">
【分析维度】

**1. 剧情钩子 (Hooks)**
识别吸引读者的关键元素：
- 悬念钩子：未解之谜、疑问、谜团
- 情感钩子：引发共鸣的情感点
- 冲突钩子：矛盾对抗、紧张局势
- 认知钩子：颠覆认知的信息

每个钩子需要：
- 类型分类
- 具体内容描述
- 强度评分(1-10)
- 出现位置(开头/中段/结尾)
- **关键词**：【必填】从原文逐字复制8-25字的文本片段，用于精确定位

**2. 伏笔分析 (Foreshadowing) - 🔴 支持ID追踪**
- 埋下的新伏笔：内容、预期作用、隐藏程度(1-10)
- 回收的旧伏笔：【必须】从已埋入伏笔列表中匹配ID
- 伏笔质量：巧妙性和合理性
- **关键词**：【必填】从原文逐字复制8-25字

每个伏笔需要：
- **title**：简洁标题（10-20字，概括伏笔核心）
  - ⚠️ 回收伏笔时，标题应与原伏笔标题保持一致，不要添加"回收"等后缀
  - 例如：原伏笔标题是"绿头发的视觉符号"，回收时标题仍为"绿头发的视觉符号"，而非"绿头发的视觉符号回收"
- **content**：详细描述伏笔内容和预期作用
- **type**：planted（埋下）或 resolved（回收）
- **strength**：强度1-10（对读者的吸引力）
- **subtlety**：隐藏度1-10（越高越隐蔽）
- **reference_chapter**：回收时引用的原埋入章节号，埋下时为null
- **reference_foreshadow_id**：【回收时必填】被回收伏笔的ID（从已埋入伏笔列表中选择），埋下时为null
  - 🔴 重要：回收伏笔时，必须从【已埋入伏笔列表】中找到对应的伏笔ID并填写
  - 如果列表中有标注【ID: xxx】的伏笔，回收时必须使用该ID
  - 如果无法确定是哪个伏笔，才填写null（但应尽量避免）
- **keyword**：【必填】从原文逐字复制8-25字的定位文本
- **category**：分类（identity=身世/mystery=悬念/item=物品/relationship=关系/event=事件/ability=能力/prophecy=预言）
- **is_long_term**：是否长线伏笔（跨10章以上回收为true）
- **related_characters**：涉及的角色名列表
- **estimated_resolve_chapter**：【必填】预估回收章节号（埋下时必须预估，回收时为当前章节）

**3. 冲突分析 (Conflict)**
- 冲突类型：人与人/人与己/人与环境/人与社会
- 冲突各方及立场
- 冲突强度(1-10)
- 解决进度(0-100%)

**4. 情感曲线 (Emotional Arc)**
- 主导情绪（最多10字）
- 情感强度(1-10)
- 情绪变化轨迹

**5. 角色状态追踪 (Character Development)**
对每个出场角色分析：
- 心理状态变化(前→后)
- 关系变化
- 关键行动和决策
- 成长或退步
- **💀 存活状态（重要）**：
  - survival_status: 角色当前存活状态
  - 可选值：active(正常)/deceased(死亡)/missing(失踪)/retired(退场)
  - 默认为null（表示无变化），仅当章节中角色明确死亡、失踪或永久退场时才填写
  - 死亡/失踪需要有明确的剧情依据，不可臆测
- ** 职业变化（可选）**：
  - 仅当章节明确描述职业进展时填写
  - main_career_stage_change: 整数(+1晋升/-1退步/0无变化)
  - sub_career_changes: 副职业变化数组
  - new_careers: 新获得职业
  - career_breakthrough: 突破过程描述
- **🏛️ 组织变化（可选）**：
  - 仅当章节明确描述角色与组织关系变化时填写
  - organization_changes: 组织变动数组
  - 每项包含：organization_name(组织名)、change_type(加入joined/离开left/晋升promoted/降级demoted/开除expelled/叛变betrayed)、new_position(新职位，可选)、loyalty_change(忠诚度变化描述，可选)、description(变化描述)

**5b. 组织状态追踪 (Organization Status) - 可选**
仅当章节涉及组织势力变化时填写，分析出场组织的状态变化：
- 组织名称
- 势力等级变化(power_change: 整数，+N增强/-N削弱/0无变化)
- 据点变化(new_location: 新据点，可选)
- 宗旨/目标变化(new_purpose: 新目标，可选)
- 组织状态描述(status_description: 当前状态概述)
- 关键事件(key_event: 触发变化的事件)
- **💀 组织存续状态（重要）**：
  - is_destroyed: 组织是否被覆灭（true/false，默认false）
  - 仅当章节明确描述组织被彻底消灭、瓦解、灭亡时设为true

**6. 关键情节点 (Plot Points)**
列出3-5个核心情节点：
- 情节内容
- 类型(revelation/conflict/resolution/transition)
- 重要性(0.0-1.0)
- 对故事的影响
- **关键词**：【必填】从原文逐字复制8-25字

**7. 场景与节奏**
- 主要场景
- 叙事节奏(快/中/慢)
- 对话与描写比例

**8. 质量评分（支持小数，严格区分度）**
评分范围：1.0-10.0，支持一位小数（如 6.5、7.8）
每个维度必须根据以下标准严格评分，避免所有内容都打中等分数：

**节奏把控 (pacing)**：
- 1.0-3.9（差）：节奏混乱，该快不快该慢不慢；场景切换生硬；大段无意义描写拖沓
- 4.0-5.9（中下）：节奏基本可读但有明显问题；部分场景过于冗长或仓促
- 6.0-7.9（中上）：节奏整体流畅，偶有小问题；张弛有度但不够精妙
- 8.0-9.4（优秀）：节奏把控精准，高潮迭起；场景切换自然，详略得当
- 9.5-10.0（完美）：节奏大师级，每个段落都恰到好处

**吸引力 (engagement)**：
- 1.0-3.9（差）：内容乏味，缺乏钩子；读者难以继续阅读
- 4.0-5.9（中下）：有基本情节但缺乏亮点；钩子设置生硬或缺失
- 6.0-7.9（中上）：有一定吸引力，钩子有效但不够巧妙
- 8.0-9.4（优秀）：引人入胜，钩子设置精妙；让人欲罢不能
- 9.5-10.0（完美）：极具吸引力，每个段落都有阅读动力

**连贯性 (coherence)**：
- 1.0-3.9（差）：逻辑混乱，前后矛盾；角色行为不合理
- 4.0-5.9（中下）：基本连贯但有明显漏洞；部分情节衔接生硬
- 6.0-7.9（中上）：整体连贯，偶有小瑕疵；角色行为基本合理
- 8.0-9.4（优秀）：逻辑严密，衔接自然；角色行为高度一致
- 9.5-10.0（完美）：无懈可击的连贯性

**整体质量 (overall)**：
- 计算公式：(pacing + engagement + coherence) / 3，保留一位小数
- 可根据综合印象±0.5调整，必须与各项分数保持一致性

**9. 改进建议（与分数关联）**
建议数量必须与整体质量分数关联：
- overall < 4.0：必须提供4-5条具体改进建议，指出严重问题
- overall 4.0-5.9：必须提供3-4条改进建议，指出主要问题
- overall 6.0-7.9：提供1-2条优化建议，指出可提升之处
- overall ≥ 8.0：提供0-1条锦上添花的建议

每条建议必须：
- 指出具体问题位置或类型
- 说明为什么是问题
- 给出明确的改进方向
</analysis_framework>

<output priority="P0">
【输出格式】
返回纯JSON对象（无markdown标记）：

{{
  "hooks": [
    {{
      "type": "悬念",
      "content": "具体描述",
      "strength": 8,
      "position": "中段",
      "keyword": "从原文逐字复制的8-25字文本"
    }}
  ],
  "foreshadows": [
    {{
      "title": "伏笔简洁标题",
      "content": "伏笔详细内容和预期作用",
      "type": "planted",
      "strength": 7,
      "subtlety": 8,
      "reference_chapter": null,
      "reference_foreshadow_id": null,
      "keyword": "从原文逐字复制的8-25字文本",
      "category": "mystery",
      "is_long_term": false,
      "related_characters": ["角色A", "角色B"],
      "estimated_resolve_chapter": 15
    }},
    {{
      "title": "回收的伏笔标题",
      "content": "伏笔如何被回收的描述",
      "type": "resolved",
      "strength": 8,
      "subtlety": 6,
      "reference_chapter": 5,
      "reference_foreshadow_id": "abc123-已埋入伏笔的ID",
      "keyword": "从原文逐字复制的8-25字文本",
      "category": "mystery",
      "is_long_term": false,
      "related_characters": ["角色A"],
      "estimated_resolve_chapter": 10
    }}
  ],
  "conflict": {{
    "types": ["人与人", "人与己"],
    "parties": ["主角-复仇", "反派-维护现状"],
    "level": 8,
    "description": "冲突描述",
    "resolution_progress": 0.3
  }},
  "emotional_arc": {{
    "primary_emotion": "紧张焦虑",
    "intensity": 8,
    "curve": "平静→紧张→高潮→释放",
    "secondary_emotions": ["期待", "焦虑"]
  }},
  "character_states": [
    {{
      "character_name": "张三",
      "survival_status": null,
      "state_before": "犹豫",
      "state_after": "坚定",
      "psychological_change": "心理变化描述",
      "key_event": "触发事件",
      "relationship_changes": {{"李四": "关系改善"}},
      "career_changes": {{
        "main_career_stage_change": 1,
        "sub_career_changes": [{{"career_name": "炼丹", "stage_change": 1}}],
        "new_careers": [],
        "career_breakthrough": "突破描述"
      }},
      "organization_changes": [
        {{
          "organization_name": "某门派",
          "change_type": "promoted",
          "new_position": "长老",
          "loyalty_change": "忠诚度提升",
          "description": "因立下大功被提拔为长老"
        }}
      ]
    }}
  ],
  "plot_points": [
    {{
      "content": "情节点描述",
      "type": "revelation",
      "importance": 0.9,
      "impact": "推动故事发展",
      "keyword": "从原文逐字复制的8-25字文本"
    }}
  ],
  "scenes": [
    {{
      "location": "地点",
      "atmosphere": "氛围",
      "duration": "时长估计"
    }}
  ],
  "organization_states": [
    {{
      "organization_name": "某门派",
      "power_change": -10,
      "new_location": null,
      "new_purpose": null,
      "status_description": "因内乱势力受损，但核心力量未动摇",
      "key_event": "长老叛变导致分支瓦解",
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
    "score_justification": "节奏整体流畅但中段略显拖沓；钩子设置有效但不够巧妙；逻辑连贯无明显漏洞"
  }},
  "plot_stage": "发展",
  "suggestions": [
    "【节奏问题】第三场景的心理描写过长（约500字），建议精简至200字以内，保留核心情感即可",
    "【吸引力不足】章节中段缺乏有效钩子，建议在主角发现线索后增加一个小悬念"
  ]
}}
</output>

<constraints>
【必须遵守】
✅ keyword字段必填：钩子、伏笔、情节点的keyword不能为空
✅ 逐字复制：keyword必须从原文复制，长度8-25字
✅ 精确定位：keyword能在原文中精确找到
✅ 职业变化可选：仅当章节明确描述时填写
✅ 组织变化可选：仅当章节明确描述角色与组织关系变动时填写（character_states中的organization_changes）
✅ 组织状态可选：仅当章节明确描述组织势力/据点/目标变化时填写（organization_states顶级字段）
✅ 存活状态谨慎：survival_status仅当章节有明确死亡/失踪/退场描写时填写，默认null
✅ 组织覆灭谨慎：is_destroyed仅当组织被彻底消灭时设true，组织受损不算覆灭
✅ 【伏笔ID追踪】回收伏笔时，必须从【已埋入伏笔列表】中查找匹配的ID填入 reference_foreshadow_id
✅ 【suggestions严格格式】suggestions 必须是“字符串数组”，每个元素都必须是纯字符串
✅ suggestions 的正确格式示例："suggestions": ["【节奏问题】...", "【描写不足】..."]
✅ suggestions 中禁止返回对象、字典、键值对或嵌套结构，例如禁止 {{"suggestion": "..."}}、{{"content": "..."}}
✅ 如果没有改进建议，必须返回空数组 []，不要返回 null，不要省略字段

【评分约束 - 严格执行】
✅ 严格按评分标准打分，支持小数（如6.5、7.2、8.3）
✅ 不要默认给7.0-8.0分，差的内容必须给低分（1.0-5.0），好的内容才给高分（8.0-10.0）
✅ score_justification必填：简要说明各项评分的依据
✅ 建议数量必须与overall分数关联：
   - overall≤4.0 → 4-5条建议
   - overall 4.0-6.0 → 3-4条建议
   - overall 6.0-8.0 → 1-2条建议
   - overall≥8.0 → 0-1条建议
✅ 每条建议必须标注问题类型（如【节奏问题】【描写不足】等）
✅ 每条建议必须直接输出完整文本，不能包裹为对象字段

【禁止事项】
❌ keyword使用概括或改写的文字
❌ 输出markdown标记
❌ 遗漏必填的keyword字段
❌ 无根据地添加职业变化
❌ 无根据地添加组织变化或组织状态变化
❌ 无确切剧情依据地标记角色死亡或组织覆灭
❌ 所有章节都打7-8分的"安全分"
❌ 高分章节给大量建议，或低分章节不给建议
❌ suggestions 返回 {{"suggestion": "建议内容"}} 这类对象数组
❌ suggestions 返回带编号对象、content对象、explanation对象等任何非字符串元素
</constraints>"""

    # 大纲单批次展开提示词 V2（RTCO框架）
    OUTLINE_EXPAND_SINGLE = """<system>
你是专业的小说情节架构师，擅长将大纲节点展开为详细章节规划。
</system>

<task>
【展开任务】
将第{outline_order_index}节大纲《{outline_title}》展开为{target_chapter_count}个章节的详细规划。

【展开策略】
{strategy_instruction}
</task>

<project priority="P1">
【项目信息】
小说名称：{project_title}
类型：{project_genre}
主题：{project_theme}
叙事视角：{project_narrative_perspective}

【世界观背景】
时间背景：{project_world_time_period}
地理位置：{project_world_location}
氛围基调：{project_world_atmosphere}
</project>

<characters priority="P1">
【角色信息】
{characters_info}
</characters>

<outline_node priority="P0">
【当前大纲节点 - 展开对象】
序号：第 {outline_order_index} 节
标题：{outline_title}
内容：{outline_content}
</outline_node>

<context priority="P2">
【上下文参考】
{context_info}
</context>

<output priority="P0">
【输出格式】
返回{target_chapter_count}个章节规划的JSON数组：

[
  {{
    "sub_index": 1,
    "title": "章节标题（体现核心冲突或情感）",
    "plot_summary": "剧情摘要（200-300字）：详细描述该章发生的事件，仅限当前大纲内容",
    "key_events": ["关键事件1", "关键事件2", "关键事件3"],
    "character_focus": ["角色A", "角色B"],
    "emotional_tone": "情感基调（如：紧张、温馨、悲伤）",
    "narrative_goal": "叙事目标（该章要达成的叙事效果）",
    "conflict_type": "冲突类型（如：内心挣扎、人际冲突）",
    "estimated_words": 3000{scene_field}
  }}
]

【格式规范】
- 纯JSON数组输出，无其他文字
- 内容描述中严禁使用特殊符号
</output>

<constraints>
【⚠️ 内容边界约束 - 必须严格遵守】
✅ 只能展开当前大纲节点的内容
✅ 深化当前大纲，而非跨越到后续
✅ 放慢叙事节奏，充分体验当前阶段

❌ 绝对不能推进到后续大纲内容
❌ 不要让剧情快速推进
❌ 不要提前展开【后一节】的内容

【展开原则】
✅ 将单一事件拆解为多个细节丰富的章节
✅ 深入挖掘情感、心理、环境、对话
✅ 每章是当前大纲内容的不同侧面或阶段

【🔴 相邻章节差异化约束（防止重复）】
✅ 每章有独特的开场方式（不同场景、时间点、角色状态）
✅ 每章有独特的结束方式（不同悬念、转折、情感收尾）
✅ key_events在相邻章节间绝不重叠
✅ plot_summary描述该章独特内容，不与其他章雷同
✅ 同一事件的不同阶段要明确区分"前、中、后"

【章节间要求】
✅ 衔接自然流畅（每章从不同起点开始）
✅ 剧情递进合理（但不超出当前大纲边界）
✅ 节奏张弛有度
✅ 每章有明确且独特的叙事价值
✅ 最后一章结束时恰好完成当前大纲内容
✅ 关键事件无重叠：检查相邻章节key_events

【禁止事项】
❌ 输出非JSON格式
❌ 剧情越界到后续大纲
❌ 相邻章节内容重复
❌ 关键事件雷同
</constraints>"""

    # 大纲分批展开提示词 V2（RTCO框架）
    OUTLINE_EXPAND_MULTI = """<system>
你是专业的小说情节架构师，擅长分批展开大纲节点。
</system>

<task>
【展开任务】
继续展开第{outline_order_index}节大纲《{outline_title}》，生成第{start_index}-{end_index}节（共{target_chapter_count}个章节）的详细规划。

【分批说明】
- 这是整个展开的一部分
- 必须与前面已生成的章节自然衔接
- 从第{start_index}节开始编号
- 继续深化当前大纲内容

【展开策略】
{strategy_instruction}
</task>

<project priority="P1">
【项目信息】
小说名称：{project_title}
类型：{project_genre}
主题：{project_theme}
叙事视角：{project_narrative_perspective}

【世界观背景】
时间背景：{project_world_time_period}
地理位置：{project_world_location}
氛围基调：{project_world_atmosphere}
</project>

<characters priority="P1">
【角色信息】
{characters_info}
</characters>

<outline_node priority="P0">
【当前大纲节点 - 展开对象】
序号：第 {outline_order_index} 节
标题：{outline_title}
内容：{outline_content}
</outline_node>

<context priority="P2">
【上下文参考】
{context_info}

【已生成的前序章节】
{previous_context}
</context>

<output priority="P0">
【输出格式】
返回第{start_index}-{end_index}节章节规划的JSON数组（共{target_chapter_count}个对象）：

[
  {{
    "sub_index": {start_index},
    "title": "章节标题",
    "plot_summary": "剧情摘要（200-300字）：详细描述该章发生的事件",
    "key_events": ["关键事件1", "关键事件2", "关键事件3"],
    "character_focus": ["角色A", "角色B"],
    "emotional_tone": "情感基调",
    "narrative_goal": "叙事目标",
    "conflict_type": "冲突类型",
    "estimated_words": 3000{scene_field}
  }}
]

【格式规范】
- 纯JSON数组输出，无其他文字
- 内容描述中严禁使用特殊符号
- sub_index从{start_index}开始
</output>

<constraints>
【⚠️ 内容边界约束】
✅ 只能展开当前大纲节点的内容
✅ 深化当前大纲，而非跨越到后续
✅ 放慢叙事节奏

❌ 绝对不能推进到后续大纲内容
❌ 不要让剧情快速推进

【分批连续性约束】
✅ 与前面已生成章节自然衔接
✅ 从第{start_index}节开始编号
✅ 保持叙事连贯性

【🔴 相邻章节差异化约束（防止重复）】
✅ 每章有独特的开场和结束方式
✅ key_events在相邻章节间绝不重叠
✅ plot_summary描述该章独特内容
✅ 特别注意与前序章节的差异化
✅ 避免重复已有内容

【章节间要求】
✅ 与前面章节衔接自然流畅
✅ 剧情递进合理（但不超出当前大纲边界）
✅ 节奏张弛有度
✅ 每章有明确且独特的叙事价值
✅ 关键事件无重叠：检查本批次和前序章节的key_events

【禁止事项】
❌ 输出非JSON格式
❌ 剧情越界到后续大纲
❌ 相邻章节内容重复
❌ 与前序章节key_events雷同
</constraints>"""

    # 章节重写系统提示词 V2（RTCO框架）
    CHAPTER_REGENERATION_SYSTEM = """<system>
你是经验丰富的专业小说编辑和作家，擅长根据反馈意见重新创作章节。
你的任务是根据修改指令，对原始章节进行深度改写和优化。
</system>

<task>
【重写任务】
1. 仔细理解原始章节的内容、情节走向和叙事意图
2. 认真分析所有的修改要求，包括AI分析建议和用户自定义指令
3. 针对每一条修改建议，在新版本中进行具体改进
4. 在保持故事连贯性和角色一致性的前提下，创作改进后的新版本
5. 确保新版本在艺术性、可读性和叙事质量上都有明显提升
</task>

<guidelines>
【改写原则】
- **问题导向**：针对修改指令中指出的每个问题进行改进
- **保持精华**：保留原章节中优秀的描写、对话和情节设计
- **深化细节**：增强场景描写、情感渲染和人物刻画
- **节奏优化**：调整叙事节奏，避免拖沓或过快
- **风格一致**：如果提供了写作风格要求，必须严格遵循

【重点关注】
- 如果修改指令提到"节奏"问题，重点调整叙事速度和场景切换
- 如果修改指令提到"情感"问题，重点深化人物内心戏和情感表达
- 如果修改指令提到"描写"问题，重点丰富环境和动作细节
- 如果修改指令提到"对话"问题，重点让对话更自然、更有个性
- 如果修改指令提到"冲突"问题，重点强化矛盾和戏剧张力
</guidelines>

<output>
【输出规范】
直接输出重写后的章节正文内容。
- 不要包含章节标题、序号或其他元信息
- 不要输出任何解释、注释或创作说明
- 从故事内容直接开始，保持叙事的连贯性
</output>
"""
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
# 角色资料收集提示词（MCP增强用）
# 自动角色引入 - 生成提示词 V2（RTCO框架）
# 自动组织引入 - 预测性分析提示词（RTCO框架）
# 自动组织引入 - 生成提示词（RTCO框架）
# 局部重写提示词（RTCO框架）
    PARTIAL_REGENERATE = """<system>
你是一位专业的小说改写助手，擅长根据用户的修改要求精准改写指定段落，同时确保与前后文无缝衔接。
</system>

<task>
【改写任务】
根据用户的修改要求，重写下面选中的文本段落。

【重要要求】
1. 只输出重写后的内容，不要包含任何解释、前缀或后缀
2. 保持与前后文的自然衔接和语气连贯
3. 严格遵循用户的修改要求
4. 保持整体叙事风格的一致性
</task>

<context priority="P0">
【前文参考】（用于衔接，勿重复）
{context_before}

【需要重写的原文】（共{original_word_count}字）
{selected_text}

【后文参考】（用于衔接，勿重复）
{context_after}
</context>

<user_requirements priority="P0">
【用户修改要求】
{user_instructions}

【字数要求】
{length_requirement}
</user_requirements>

<style priority="P1">
【写作风格】
{style_content}
</style>

<output>
【输出规范】
直接输出重写后的内容，从故事内容开始写。
- 不要输出任何解释或说明文字
- 不要输出"重写后："等前缀
- 不要输出引号包裹内容
- 确保输出内容可以直接替换原文

请直接输出重写后的内容：
</output>

<constraints>
【必须遵守】
✅ 前后衔接：输出内容必须与前文自然衔接，与后文平滑过渡
✅ 风格一致：保持与原文相同的叙事风格、语气和人称
✅ 要求优先：严格执行用户的修改要求
✅ 字数控制：遵循字数要求

【禁止事项】
❌ 重复前文内容
❌ 重复后文内容
❌ 添加任何元信息或说明
❌ 改变叙事人称或视角
❌ 偏离用户的修改要求
</constraints>"""

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
        
        prompt_parts = [system_template]
        
        # 原始章节信息
        prompt_parts.append(f"""## 📖 原始章节信息

**章节**：第{chapter_number}章
**标题**：{title}
**字数**：{word_count}字

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
5. **字数控制**：目标字数约{target_word_count}字（可适当浮动±20%）
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
                "name": "章节创作-1-N模式（第1章）",
                "category": "Criação de capítulos",
                "description": "1-N模式：根据大纲创作章节内容（用于第1章，无前置章节）",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "characters_info"]
            },
            "CHAPTER_GENERATION_ONE_TO_MANY_NEXT": {
                "name": "章节创作-1-N模式（第2章及以后）",
                "category": "Criação de capítulos",
                "description": "1-N模式：基于前置章节内容创作新章节（用于第2章及以后）",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "characters_info", "continuation_point",
                             "foreshadow_reminders", "relevant_memories", "story_skeleton", "previous_chapter_summary"]
            },
            "CHAPTER_GENERATION_ONE_TO_ONE": {
                "name": "章节创作-1-1模式（第1章）",
                "category": "Criação de capítulos",
                "description": "1-1模式：章节创作（用于第1章，无前置章节）",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "characters_info", "chapter_careers"]
            },
            "CHAPTER_GENERATION_ONE_TO_ONE_NEXT": {
                "name": "章节创作-1-1模式（第2章及以后）",
                "category": "Criação de capítulos",
                "description": "1-1模式：基于上一章内容创作新章节（用于第2章及以后）",
                "parameters": ["project_title", "genre", "chapter_number", "chapter_title", "chapter_outline",
                             "target_word_count", "narrative_perspective", "previous_chapter_content",
                             "characters_info", "chapter_careers", "foreshadow_reminders", "relevant_memories"]
            },
            "CHAPTER_REGENERATION_SYSTEM": {
                "name": "章节重写系统提示",
                "category": "Reescrita de capítulos",
                "description": "用于章节重写的系统提示词",
                "parameters": ["chapter_number", "title", "word_count", "content", "modification_instructions",
                             "project_context", "style_content", "target_word_count"]
            },
            "PARTIAL_REGENERATE": {
                "name": "局部重写",
                "category": "Reescrita de capítulos",
                "description": "根据用户修改要求重写选中的段落内容",
                "parameters": ["context_before", "original_word_count", "selected_text", "context_after",
                             "user_instructions", "length_requirement", "style_content"]
            },
            "PLOT_ANALYSIS": {
                "name": "情节分析",
                "category": "Análise de enredo",
                "description": "深度分析章节的剧情、钩子、伏笔等",
                "parameters": ["chapter_number", "title", "content", "word_count"]
            },
            "OUTLINE_EXPAND_SINGLE": {
                "name": "大纲单批次展开",
                "category": "Expansão de enredo",
                "description": "将大纲节点展开为详细章节规划（单批次）",
                "parameters": ["project_title", "project_genre", "project_theme", "project_narrative_perspective", 
                             "project_world_time_period", "project_world_location", "project_world_atmosphere", 
                             "characters_info", "outline_order_index", "outline_title", "outline_content", 
                             "context_info", "strategy_instruction", "target_chapter_count", "scene_instruction", "scene_field"]
            },
            "OUTLINE_EXPAND_MULTI": {
                "name": "大纲分批展开",
                "category": "Expansão de enredo",
                "description": "将大纲节点展开为详细章节规划（分批）",
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
