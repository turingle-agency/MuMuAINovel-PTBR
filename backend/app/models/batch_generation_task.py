"""批量生成任务数据模型"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid


class BatchGenerationTask(Base):
    """批量生成任务表"""
    __tablename__ = "batch_generation_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False, comment="ID do projeto")
    user_id = Column(String(100), nullable=False, comment="ID do usuário")
    
    # 任务配置
    start_chapter_number = Column(Integer, nullable=False, comment="Número do capítulo inicial")
    chapter_count = Column(Integer, nullable=False, comment="Quantidade de capítulos a gerar")
    chapter_ids = Column(JSON, nullable=False, comment="Lista de IDs dos capítulos a gerar")
    style_id = Column(Integer, comment="ID do estilo de escrita usado")
    target_word_count = Column(Integer, default=3000, comment="Meta de palavras")
    enable_analysis = Column(Boolean, default=False, comment="Análise síncrona habilitada")
    
    # 任务状态
    status = Column(String(20), default="pending", comment="Status da tarefa: pending/running/completed/failed/cancelled")
    total_chapters = Column(Integer, default=0, comment="Total de capítulos")
    completed_chapters = Column(Integer, default=0, comment="Capítulos concluídos")
    failed_chapters = Column(JSON, default=list, comment="Lista de capítulos com falha")
    current_chapter_id = Column(String(36), comment="ID do capítulo em geração")
    current_chapter_number = Column(Integer, comment="Número do capítulo em geração")
    current_retry_count = Column(Integer, default=0, comment="Tentativas do capítulo atual")
    max_retries = Column(Integer, default=3, comment="Máximo de tentativas")
    
    # 时间记录
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    started_at = Column(DateTime, comment="Data de início")
    completed_at = Column(DateTime, comment="Data de conclusão")
    
    # Mensagem de erro
    error_message = Column(String(500), comment="Mensagem de erro")
    
    def __repr__(self):
        return f"<BatchGenerationTask(id={self.id}, status={self.status}, completed={self.completed_chapters}/{self.total_chapters})>"