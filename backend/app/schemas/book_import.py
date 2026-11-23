"""拆书导入相关的 Pydantic Schema"""
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


TaskStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
ImportMode = Literal["append", "overwrite"]
ExtractLevel = Literal["basic", "standard", "deep"]
WarningLevel = Literal["info", "warning", "error"]
BookImportExtractMode = Literal["tail", "full"]


class BookImportWarning(BaseModel):
    """导入告警信息"""
    code: str = Field(..., description="Código do aviso")
    message: str = Field(..., description="Conteúdo do aviso")
    level: WarningLevel = Field(default="warning", description="Nível do aviso")


class ProjectSuggestion(BaseModel):
    """项目建议信息（可在预览页修改）"""
    title: str = Field(..., min_length=1, max_length=200, description="Título do projeto")
    description: Optional[str] = Field(None, description="Descrição do projeto")
    theme: Optional[str] = Field(None, description="Tema")
    genre: Optional[str] = Field(None, description="Gênero")
    narrative_perspective: str = Field(default="terceira pessoa", description="Perspectiva narrativa")
    target_words: int = Field(default=100000, ge=1000, description="Meta de palavras (padrão: 100 mil)")


class BookImportChapter(BaseModel):
    """预览章节"""
    title: str = Field(..., min_length=1, max_length=200, description="Título do capítulo")
    content: str = Field(default="", description="Texto do capítulo")
    summary: Optional[str] = Field(None, description="Resumo do capítulo")
    chapter_number: int = Field(..., ge=1, description="Número do capítulo")
    outline_title: Optional[str] = Field(None, description="Título do esboço associado (opcional)")


class BookImportOutline(BaseModel):
    """预览大纲"""
    title: str = Field(..., min_length=1, max_length=200, description="Título do esboço")
    content: Optional[str] = Field(None, description="Conteúdo do esboço")
    order_index: int = Field(..., ge=1, description="Número de ordem")
    structure: Optional[dict[str, Any]] = Field(None, description="Esboço estruturado (mesma estrutura gerada pelo sistema)")


class BookImportTaskCreateRequest(BaseModel):
    """创建拆书任务请求"""
    extract_mode: BookImportExtractMode = Field(default="tail", description="Escopo da extração: tail=últimos capítulos, full=livro inteiro")
    tail_chapter_count: int = Field(default=10, ge=5, le=9999, description="Com extract_mode=tail, quantidade de capítulos finais a extrair; deve ser múltiplo de 5, acima de 50 é tratado como livro inteiro")


class BookImportTaskCreateResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    status: TaskStatus


class BookImportTaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: TaskStatus
    progress: int = Field(..., ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BookImportPreviewResponse(BaseModel):
    """预览数据响应"""
    task_id: str
    project_suggestion: ProjectSuggestion
    chapters: list[BookImportChapter]
    outlines: list[BookImportOutline]
    warnings: list[BookImportWarning]


class BookImportApplyRequest(BaseModel):
    """确认导入请求（支持前端修订后的数据）"""
    project_suggestion: ProjectSuggestion
    chapters: list[BookImportChapter]
    outlines: list[BookImportOutline] = Field(default_factory=list)
    import_mode: ImportMode = Field(default="append", description="Modo de importação")


class BookImportApplyResponse(BaseModel):
    """确认导入响应"""
    success: bool
    project_id: str
    statistics: dict[str, int]
    warnings: list[BookImportWarning] = Field(default_factory=list)


class BookImportRetryRequest(BaseModel):
    """重试失败步骤请求"""
    steps: list[str] = Field(..., min_length=1, description="Lista de etapas a repetir, ex.: world_building / career_system / characters")
