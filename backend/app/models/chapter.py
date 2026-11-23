"""章节数据模型"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Chapter(Base):
    """章节表"""
    __tablename__ = "chapters"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False, comment="Número do capítulo")
    title = Column(String(200), nullable=False, comment="Título do capítulo")
    content = Column(Text, comment="Conteúdo do capítulo")
    summary = Column(Text, comment="Resumo do capítulo")
    word_count = Column(Integer, default=0, comment="Contagem de palavras")
    status = Column(String(20), default="draft", comment="Status do capítulo")
    
    # 大纲关联字段（实现一对多关系）
    outline_id = Column(String(36), ForeignKey("outlines.id", ondelete="SET NULL"), nullable=True, comment="ID do esboço associado")
    sub_index = Column(Integer, default=1, comment="Número do subcapítulo dentro do esboço")
    
    # 大纲展开规划数据（JSON格式）
    expansion_plan = Column(Text, comment="Detalhes do planejamento de expansão (JSON): inclui key_events, character_focus, emotional_tone etc.")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<Chapter(id={self.id}, chapter_number={self.chapter_number}, title={self.title}, outline_id={self.outline_id})>"