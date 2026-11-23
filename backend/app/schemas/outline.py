"""大纲相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class OutlineBase(BaseModel):
    """大纲基础模型"""
    title: str = Field(..., description="Título do capítulo")
    content: str = Field(..., description="Resumo do conteúdo do capítulo")


class OutlineCreate(BaseModel):
    """创建大纲的请求模型"""
    project_id: str = Field(..., description="ID do projeto proprietário")
    title: str = Field(..., description="Título do capítulo")
    content: str = Field(..., description="Resumo do conteúdo do capítulo")
    order_index: int = Field(..., description="Número do capítulo", ge=1)
    structure: Optional[str] = Field(None, description="Dados estruturados do esboço (JSON)")


class OutlineUpdate(BaseModel):
    """更新大纲的请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    structure: Optional[str] = Field(None, description="Dados estruturados do esboço (JSON)")
    # order_index 不允许通过普通更新修改，只能通过 reorder_outlines 接口批量调整


class OutlineResponse(BaseModel):
    """大纲响应模型"""
    id: str
    project_id: str
    title: str
    content: str
    structure: Optional[str] = None
    order_index: int
    has_chapters: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("content", mode="before")
    @classmethod
    def normalize_legacy_null_content(cls, value: Any) -> str:
        """兼容历史导入或旧版本生成的 NULL 大纲内容。"""
        return "" if value is None else value

    model_config = ConfigDict(from_attributes=True)


class OutlineGenerateRequest(BaseModel):
    """AI生成大纲的请求模型 - 支持全新生成和智能续写"""
    project_id: str = Field(..., description="ID do projeto")
    genre: Optional[str] = Field(None, description="Gênero do livro, ex.: fantasia, urbano, suspense etc.")
    theme: str = Field(..., description="Tema do livro")
    chapter_count: int = Field(..., ge=1, description="Quantidade de capítulos")
    narrative_perspective: str = Field(..., description="Perspectiva narrativa")
    world_context: Optional[dict] = Field(None, description="Contexto do mundo")
    characters_context: Optional[list] = Field(None, description="Informações dos personagens")
    target_words: int = Field(100000, description="Meta de palavras")
    requirements: Optional[str] = Field(None, description="Outros requisitos especiais")
    provider: Optional[str] = Field(None, description="Provedor de IA")
    model: Optional[str] = Field(None, description="Modelo de IA")
    
    # 续写相关参数
    mode: str = Field("auto", description="Modo de geração: auto (automático), new (novo), continue (continuação)")
    story_direction: Optional[str] = Field(None, description="Dica de direção da história (usada na continuação)")
    plot_stage: str = Field("development", description="Estágio da trama: development (desenvolvimento), climax (clímax), ending (desfecho)")
    keep_existing: bool = Field(False, description="Manter o esboço existente (na continuação)")
    enable_mcp: bool = Field(True, description="Habilitar reforço com ferramentas MCP (busca de referências de enredo)")


class ChapterOutlineGenerateRequest(BaseModel):
    """为单个章节生成大纲的请求模型"""
    outline_id: str = Field(..., description="ID do esboço")
    context: Optional[str] = Field(None, description="Contexto adicional")
    provider: Optional[str] = Field(None, description="Provedor de IA")
    model: Optional[str] = Field(None, description="Modelo de IA")


class OutlineListResponse(BaseModel):
    """大纲列表响应模型"""
    total: int
    items: list[OutlineResponse]


class ChapterPlanItem(BaseModel):
    """单个章节规划项"""
    sub_index: int = Field(..., description="Número do subcapítulo", ge=1)
    title: str = Field(..., description="Título do capítulo")
    plot_summary: str = Field(..., description="Resumo da trama (200-300 palavras)")
    key_events: list[str] = Field(..., description="Lista de eventos-chave")
    character_focus: list[str] = Field(..., description="Principais personagens envolvidos")
    emotional_tone: str = Field(..., description="Tom emocional")
    narrative_goal: str = Field(..., description="Objetivo narrativo")
    conflict_type: str = Field(..., description="Tipo de conflito")
    estimated_words: int = Field(3000, description="Estimativa de palavras", ge=1000)
    scenes: Optional[list[str]] = Field(None, description="Lista de cenas (opcional)")


class OutlineExpansionRequest(BaseModel):
    """大纲展开为多章节的请求模型（outline_id从路径参数获取）"""
    target_chapter_count: int = Field(3, description="Quantidade-alvo de capítulos", ge=1, le=10)
    expansion_strategy: str = Field("balanced", description="Estratégia de expansão: balanced (equilibrada), climax (foco no clímax), detail (rica em detalhes)")
    enable_scene_analysis: bool = Field(False, description="Incluir planejamento de cenas")
    auto_create_chapters: bool = Field(True, description="Criar registros de capítulos automaticamente")
    provider: Optional[str] = Field(None, description="Provedor de IA")
    model: Optional[str] = Field(None, description="Modelo de IA")


class OutlineExpansionResponse(BaseModel):
    """大纲展开响应模型"""
    outline_id: str = Field(..., description="ID do esboço")
    outline_title: str = Field(..., description="Título do esboço")
    target_chapter_count: int = Field(..., description="Quantidade-alvo de capítulos")
    actual_chapter_count: int = Field(..., description="Capítulos efetivamente gerados")
    expansion_strategy: str = Field(..., description="Estratégia de expansão usada")
    chapter_plans: list[ChapterPlanItem] = Field(..., description="Lista de planejamento de capítulos")
    created_chapters: Optional[list] = Field(None, description="Lista de capítulos criados")


class BatchOutlineExpansionRequest(BaseModel):
    """批量大纲展开请求模型"""
    project_id: str = Field(..., description="ID do projeto")
    outline_ids: Optional[list[str]] = Field(None, description="IDs dos esboços a expandir (se vazio, expande todos)")
    chapters_per_outline: int = Field(3, description="Capítulos-alvo por esboço", ge=1, le=10)
    expansion_strategy: str = Field("balanced", description="Estratégia de expansão")
    enable_scene_analysis: bool = Field(False, description="Incluir planejamento de cenas")
    auto_create_chapters: bool = Field(True, description="Criar registros de capítulos automaticamente")
    provider: Optional[str] = Field(None, description="Provedor de IA")
    model: Optional[str] = Field(None, description="Modelo de IA")


class BatchOutlineExpansionResponse(BaseModel):
    """批量大纲展开响应模型"""
    project_id: str = Field(..., description="ID do projeto")
    total_outlines_expanded: int = Field(..., description="Total de esboços expandidos")
    total_chapters_created: int = Field(..., description="Total de capítulos criados")
    expansion_results: list[OutlineExpansionResponse] = Field(..., description="Lista de resultados da expansão")
    skipped_outlines: Optional[list[dict]] = Field(None, description="Lista de esboços ignorados (já expandidos)")


class CreateChaptersFromPlansRequest(BaseModel):
    """根据已有规划创建章节的请求模型"""
    chapter_plans: list[ChapterPlanItem] = Field(..., description="Lista de planejamento de capítulos (de uma geração de IA anterior)")


class CreateChaptersFromPlansResponse(BaseModel):
    """根据已有规划创建章节的响应模型"""
    outline_id: str = Field(..., description="ID do esboço")
    outline_title: str = Field(..., description="Título do esboço")
    chapters_created: int = Field(..., description="Capítulos criados")
    created_chapters: list = Field(..., description="Lista de capítulos criados")
