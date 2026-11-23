"""章节重新生成相关的Schema定义"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PreserveElementsConfig(BaseModel):
    """保留元素配置"""
    preserve_structure: bool = Field(False, description="Preservar a estrutura geral")
    preserve_dialogues: List[str] = Field(default_factory=list, description="Palavras-chave de trechos de diálogo a preservar")
    preserve_plot_points: List[str] = Field(default_factory=list, description="Palavras-chave de pontos da trama a preservar")
    preserve_character_traits: bool = Field(True, description="Manter a personalidade dos personagens consistente")


class ChapterRegenerateRequest(BaseModel):
    """章节重新生成请求"""
    
    # 修改来源
    modification_source: str = Field("custom", description="Origem da modificação: custom/analysis_suggestions/mixed")
    
    # 基于分析建议
    selected_suggestion_indices: Optional[List[int]] = Field(None, description="Índices das sugestões selecionadas")
    
    # 自定义修改指令
    custom_instructions: Optional[str] = Field(None, description="Instruções de modificação do usuário")
    
    # 保留配置
    preserve_elements: Optional[PreserveElementsConfig] = Field(None, description="Configuração dos elementos a preservar")
    
    # 生成参数
    style_id: Optional[int] = Field(None, description="ID do estilo de escrita")
    target_word_count: int = Field(3000, description="Meta de palavras", ge=500, le=10000)
    focus_areas: List[str] = Field(default_factory=list, description="Focos de otimização")
    
    # 版本管理
    save_as_version: bool = Field(True, description="Salvar como nova versão")
    version_note: Optional[str] = Field(None, description="Descrição da versão", max_length=500)
    auto_apply: bool = Field(False, description="Aplicar automaticamente (substitui o conteúdo atual)")


class RegenerationTaskResponse(BaseModel):
    """重新生成任务响应"""
    task_id: str
    chapter_id: str
    status: str
    message: str
    estimated_time_seconds: int = 120


class RegenerationTaskStatus(BaseModel):
    """重新生成任务状态"""
    task_id: str
    chapter_id: str
    status: str
    progress: int
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 结果信息
    original_word_count: Optional[int] = None
    regenerated_word_count: Optional[int] = None
    version_number: Optional[int] = None

