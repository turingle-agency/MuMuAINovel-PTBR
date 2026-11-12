"""章节重新生成任务模型"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base
import uuid


class RegenerationTask(Base):
    """章节重新生成任务表"""
    __tablename__ = "regeneration_tasks"
    
    # 基本信息
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String(36), ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False, index=True)
    analysis_id = Column(String(36), nullable=True, comment="ID do resultado de análise associado")
    user_id = Column(String(50), nullable=False, index=True)
    project_id = Column(String(36), nullable=False, index=True)
    
    # 修改指令
    modification_instructions = Column(Text, nullable=False, comment="Instruções consolidadas de modificação")
    original_suggestions = Column(JSON, comment="Lista original de sugestões da análise")
    selected_suggestion_indices = Column(JSON, comment="Índices das sugestões escolhidas pelo usuário")
    custom_instructions = Column(Text, comment="Observações de modificação do usuário")
    
    # 生成参数
    style_id = Column(Integer, nullable=True, comment="ID do estilo de escrita")
    target_word_count = Column(Integer, default=3000, comment="Meta de palavras")
    focus_areas = Column(JSON, comment="Focos de otimização")
    preserve_elements = Column(JSON, comment="Configuração dos elementos a preservar")
    
    # 状态跟踪
    status = Column(String(20), default='pending', comment="pending/running/completed/failed")
    progress = Column(Integer, default=0, comment="Progresso 0-100")
    error_message = Column(Text, nullable=True)
    
    # 内容版本
    original_content = Column(Text, comment="Snapshot do conteúdo original do capítulo")
    original_word_count = Column(Integer, comment="Contagem original de palavras")
    regenerated_content = Column(Text, comment="Conteúdo regenerado")
    regenerated_word_count = Column(Integer, comment="Contagem de palavras do novo conteúdo")
    version_number = Column(Integer, default=1, comment="Número da versão")
    version_note = Column(String(500), comment="Descrição da versão")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<RegenerationTask(id={self.id[:8]}..., chapter_id={self.chapter_id[:8]}..., status={self.status})>"

