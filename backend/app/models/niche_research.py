"""Pesquisa de nicho"""
from sqlalchemy import Column, String, Float, JSON, DateTime, Index, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid


class NicheResearch(Base):
    __tablename__ = "niche_researches"
    __table_args__ = (
        Index("ux_niche_researches_input_key", "input_key", unique=True),
        Index("ix_niche_researches_claim", "status", "created_at", "id"),
        Index("ix_niche_researches_history", "user_id", "topic_hash", "created_at", "id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True)
    topic = Column(String(300), nullable=False)
    country = Column(String(10))
    product_type = Column(String(50))
    score = Column(Float)
    signals = Column(JSON)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    created_at = Column(DateTime, server_default=func.now())
    input_key = Column(String(64))
    topic_key = Column(Text)
    topic_hash = Column(String(64))
    mode = Column(String(10))
    week_key = Column(String(8))
    lease_until = Column(DateTime)
    finished_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NicheResearch(id={self.id}, topic={self.topic})>"
