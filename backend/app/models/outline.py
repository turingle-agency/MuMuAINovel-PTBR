"""大纲数据模型"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Outline(Base):
    """大纲表"""
    __tablename__ = "outlines"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False, comment="Título do esboço")
    content = Column(Text, comment="Conteúdo do esboço")
    structure = Column(Text, comment="Dados estruturados do esboço (JSON)")
    order_index = Column(Integer, comment="Número de ordem")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<Outline(id={self.id}, title={self.title})>"