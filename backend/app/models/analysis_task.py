"""分析任务模型 - 追踪异步章节分析任务状态"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AnalysisTask(Base):
    """
    分析任务表 - 追踪异步分析任务的执行状态
    
    状态流转: pending -> running -> completed/failed
    """
    __tablename__ = "analysis_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="ID da tarefa")
    chapter_id = Column(String(36), ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False, comment="ID do capítulo")
    user_id = Column(String(50), nullable=False, comment="ID do usuário")
    project_id = Column(String(36), nullable=False, comment="ID do projeto")
    
    # 任务状态
    status = Column(String(20), nullable=False, default='pending', comment="Status da tarefa: pending/running/completed/failed")
    progress = Column(Integer, default=0, comment="Progresso 0-100")
    error_message = Column(Text, nullable=True, comment="Mensagem de erro")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    started_at = Column(DateTime, nullable=True, comment="Data de início da execução")
    completed_at = Column(DateTime, nullable=True, comment="Data de conclusão")

    # 任务面板归档时间。归档只隐藏任务记录，不影响章节分析状态判断。
    archived_at = Column(DateTime, nullable=True, comment="Data de arquivamento no painel de tarefas")
    
    # 索引优化查询
    __table_args__ = (
        Index('idx_chapter_id_created', 'chapter_id', 'created_at'),
        Index('idx_status', 'status'),
        Index('idx_analysis_task_panel', 'project_id', 'user_id', 'archived_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id[:8]}..., chapter_id={self.chapter_id[:8]}..., status={self.status})>"
