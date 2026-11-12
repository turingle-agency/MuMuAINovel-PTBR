"""Série de ebooks/livros"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Series(Base):
    __tablename__ = "series"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    language = Column(String(10), nullable=False, default="pt-BR", server_default="pt-BR")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Series(id={self.id}, title={self.title})>"
