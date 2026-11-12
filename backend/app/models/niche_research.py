"""Pesquisa de nicho"""
from sqlalchemy import Column, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base
import uuid


class NicheResearch(Base):
    __tablename__ = "niche_researches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True)
    topic = Column(String(300), nullable=False)
    country = Column(String(10))
    product_type = Column(String(50))
    score = Column(Float)
    signals = Column(JSON)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NicheResearch(id={self.id}, topic={self.topic})>"
