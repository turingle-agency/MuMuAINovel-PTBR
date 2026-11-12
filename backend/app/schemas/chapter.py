"""章节相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChapterBase(BaseModel):
    """章节基础模型"""
    title: str = Field(..., description="Título do capítulo")
    chapter_number: int = Field(..., description="Número do capítulo")
    content: Optional[str] = Field(None, description="Conteúdo do capítulo")
    summary: Optional[str] = Field(None, description="Resumo do capítulo")
    word_count: Optional[int] = Field(0, description="Palavras")
    status: Optional[str] = Field("draft", description="Status do capítulo")
    outline_id: Optional[str] = Field(None, description="ID do esboço associado")
    sub_index: Optional[int] = Field(1, description="Número do subcapítulo dentro do esboço")
    expansion_plan: Optional[str] = Field(None, description="Detalhes do planejamento de expansão (JSON)")


class ChapterCreate(BaseModel):
    """创建章节的请求模型"""
    project_id: str = Field(..., description="ID do projeto proprietário")
    title: str = Field(..., description="Título do capítulo")
    chapter_number: int = Field(..., description="Número do capítulo")
    content: Optional[str] = Field(None, description="Conteúdo do capítulo")
    summary: Optional[str] = Field(None, description="Resumo do capítulo")
    status: Optional[str] = Field("draft", description="Status do capítulo")
    outline_id: Optional[str] = Field(None, description="ID do esboço associado")
    sub_index: Optional[int] = Field(1, description="Número do subcapítulo dentro do esboço")
    expansion_plan: Optional[str] = Field(None, description="Detalhes do planejamento de expansão (JSON)")


class ChapterUpdate(BaseModel):
    """更新章节的请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    # chapter_number 不允许修改，只能通过大纲的重排序来调整
    summary: Optional[str] = None
    # word_count 自动计算，不允许手动修改
    status: Optional[str] = None


class ChapterResponse(BaseModel):
    """章节响应模型"""
    id: str
    project_id: str
    title: str
    chapter_number: int
    content: Optional[str] = None
    summary: Optional[str] = None
    word_count: int = 0
    status: str
    outline_id: Optional[str] = None
    sub_index: Optional[int] = 1
    expansion_plan: Optional[str] = None
    outline_title: Optional[str] = None  # 大纲标题（从Outline表联查）
    outline_order: Optional[int] = None  # 大纲排序序号（从Outline表联查）
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChapterListResponse(BaseModel):
    """章节列表响应模型"""
    total: int
    items: list[ChapterResponse]


class AnalysisTaskStatusResponse(BaseModel):
    """单章节分析任务状态响应"""
    has_task: bool
    task_id: Optional[str] = None
    chapter_id: str
    status: str
    progress: int = 0
    error_message: Optional[str] = None
    auto_recovered: bool = False
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchAnalysisStatusRequest(BaseModel):
    """批量查询分析状态请求"""
    chapter_ids: Optional[List[str]] = Field(None, description="IDs dos capítulos a consultar; se vazio, consulta todos os capítulos do projeto")


class BatchAnalysisStatusResponse(BaseModel):
    """批量查询分析状态响应"""
    project_id: str
    total: int
    items: Dict[str, AnalysisTaskStatusResponse]


class BatchAnalyzeUnanalyzedRequest(BaseModel):
    """一键分析未分析章节请求"""
    chapter_ids: Optional[List[str]] = Field(None, description="Opcional: limita a lista de capítulos a analisar; se vazio, identifica automaticamente todos os capítulos ainda não analisados do projeto")


class BatchAnalyzeUnanalyzedResponse(BaseModel):
    """一键分析未分析章节响应"""
    project_id: str
    total_candidates: int = Field(0, description="Total de capítulos candidatos (com conteúdo)")
    total_started: int = Field(0, description="Tarefas de análise iniciadas agora")
    total_skipped_no_content: int = Field(0, description="Ignorados: capítulos sem conteúdo")
    total_skipped_running: int = Field(0, description="Ignorados: capítulos já em análise")
    total_already_completed: int = Field(0, description="Ignorados: capítulos já analisados")
    started_tasks: Dict[str, AnalysisTaskStatusResponse] = Field(default_factory=dict, description="Mapa de status das tarefas de análise iniciadas")


class ChapterGenerateRequest(BaseModel):
    """AI生成章节内容的请求模型"""
    style_id: Optional[int] = Field(None, description="ID do estilo de escrita; se omitido, nenhum estilo é usado")
    target_word_count: Optional[int] = Field(
        3000,
        description="Meta de palavras, padrão 3000",
        ge=500,   # 最小500字
        le=10000  # 最大10000字
    )
    enable_mcp: bool = Field(True, description="Habilitar reforço com ferramentas MCP (busca de referências)")
    model: Optional[str] = Field(None, description="Modelo de IA a usar; se omitido, usa o modelo padrão do usuário")
    narrative_perspective: Optional[str] = Field(None, description="Perspectiva narrativa temporária: primeira pessoa/terceira pessoa/onisciente; se omitida, usa a do projeto")
    skill_key: Optional[str] = Field(None, description="Identificador do Skill; quando informado, o fluxo desse Skill orienta a criação")


class BatchGenerateRequest(BaseModel):
    """批量生成章节的请求模型"""
    start_chapter_number: int = Field(..., description="Número do capítulo inicial")
    count: int = Field(..., description="Quantidade de capítulos a gerar", ge=1, le=20)
    style_id: Optional[int] = Field(None, description="ID do estilo de escrita")
    target_word_count: Optional[int] = Field(
        3000,
        description="Meta de palavras, padrão 3000",
        ge=500,
        le=10000
    )
    enable_analysis: bool = Field(True, description="Análise síncrona habilitada")
    enable_mcp: bool = Field(True, description="Habilitar reforço com ferramentas MCP (busca de referências)")
    max_retries: int = Field(3, description="Máximo de tentativas por capítulo", ge=0, le=5)
    model: Optional[str] = Field(None, description="Modelo de IA a usar; se omitido, usa o modelo padrão do usuário")
    narrative_perspective: Optional[str] = Field(None, description="Perspectiva narrativa temporária; se omitida, usa a do projeto")
    skill_key: Optional[str] = Field(None, description="Identificador do Skill; quando informado, o fluxo desse Skill orienta a criação")


class BatchGenerateResponse(BaseModel):
    """批量生成响应模型"""
    batch_id: str = Field(..., description="ID do lote")
    message: str = Field(..., description="Mensagem de resposta")
    chapters_to_generate: list[dict] = Field(..., description="Lista de capítulos a gerar")
    estimated_time_minutes: int = Field(..., description="Tempo estimado (minutos)")


class BatchGenerateStatusResponse(BaseModel):
    """批量生成状态响应模型"""
    batch_id: str
    status: str
    total: int
    completed: int
    current_chapter_id: Optional[str] = None
    current_chapter_number: Optional[int] = None
    current_retry_count: Optional[int] = None
    max_retries: Optional[int] = None
    failed_chapters: list[dict] = []
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class SceneData(BaseModel):
    """场景数据模型"""
    location: str = Field(..., description="Local da cena")
    characters: List[str] = Field(..., description="Lista de personagens participantes")
    purpose: str = Field(..., description="Objetivo da cena")


class ExpansionPlanUpdate(BaseModel):
    """章节规划更新模型"""
    summary: Optional[str] = Field(None, description="Resumo da trama do capítulo")
    key_events: Optional[List[str]] = Field(None, description="Lista de eventos-chave")
    character_focus: Optional[List[str]] = Field(None, description="Lista de personagens envolvidos")
    emotional_tone: Optional[str] = Field(None, description="Tom emocional")
    narrative_goal: Optional[str] = Field(None, description="Objetivo narrativo")
    conflict_type: Optional[str] = Field(None, description="Tipo de conflito")
    estimated_words: Optional[int] = Field(None, description="Estimativa de palavras", ge=500, le=10000)
    scenes: Optional[List[SceneData]] = Field(None, description="Lista de cenas")
    
    model_config = ConfigDict(json_schema_extra={
            "example": {
                "key_events": ["O protagonista enfrenta um desafio", "Momento de decisão crucial"],
                "character_focus": ["João", "Pedro"],
                "emotional_tone": "tenso e intenso",
                "narrative_goal": "avançar a trama principal",
                "conflict_type": "conflito interno",
                "estimated_words": 3000,
                "scenes": [
                    {
                        "location": "Praça da cidade",
                        "characters": ["João", "Pedro"],
                        "purpose": "Primeiro encontro"
                    }
                ]
            }
        })


class ExpansionPlanResponse(BaseModel):
    """章节规划响应模型"""
    id: str = Field(..., description="ID do capítulo")
    expansion_plan: Optional[Dict[str, Any]] = Field(None, description="Dados de planejamento")
    message: str = Field(..., description="Mensagem de resposta")


class PartialRegenerateRequest(BaseModel):
    """局部重写请求参数"""
    selected_text: str = Field(..., description="Trecho original selecionado")
    start_position: int = Field(..., description="Posição inicial no conteúdo do capítulo (índice de caractere)", ge=0)
    end_position: int = Field(..., description="Posição final no conteúdo do capítulo (índice de caractere)", ge=0)
    user_instructions: str = Field(..., description="Instruções de modificação do usuário", min_length=1, max_length=1000)
    
    # 可选参数
    context_chars: int = Field(
        500,
        description="Tamanho do contexto (caracteres antes e depois)",
        ge=100,
        le=2000
    )
    style_id: Optional[int] = Field(None, description="ID do estilo de escrita; se omitido, usa o estilo padrão do projeto")
    length_mode: Optional[str] = Field(
        "similar",
        description="Modo de ajuste de tamanho: similar (manter próximo)/expand (expandir)/condense (condensar)/custom (personalizado)"
    )
    target_word_count: Optional[int] = Field(
        None,
        description="Meta de palavras (válida apenas quando length_mode é custom)",
        ge=10,
        le=5000
    )
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "selected_text": "Lucas desferiu a espada contra o inimigo; a lâmina cintilou ferozmente e um único golpe bastou.",
            "start_position": 1234,
            "end_position": 1260,
            "user_instructions": "Adicionar uma descrição de luta mais detalhada e incluir os pensamentos do protagonista",
            "context_chars": 500,
            "length_mode": "expand"
        }
    })


class PartialRegenerateResponse(BaseModel):
    """局部重写响应模型"""
    success: bool = Field(..., description="Sucesso")
    new_text: str = Field(..., description="Novo conteúdo reescrito")
    word_count: int = Field(..., description="Contagem de palavras do novo conteúdo")
    original_word_count: int = Field(..., description="Palavras do original")
    message: str = Field("Reescrita concluída", description="Mensagem de resposta")
