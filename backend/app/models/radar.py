"""Tabelas administrativas do Radar."""
import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, String, UniqueConstraint, func

from app.database import Base


class RadarSettings(Base):
    __tablename__ = "radar_settings"

    admin_id = Column(String(100), primary_key=True)
    config = Column(JSON, nullable=False, default=dict)
    encrypted_secrets = Column(JSON, nullable=False, default=dict)


class RadarSourceCache(Base):
    __tablename__ = "radar_source_cache"

    admin_id = Column(String(100), primary_key=True)
    cache_key = Column(String(64), primary_key=True)
    result = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class RadarBudgetMonth(Base):
    __tablename__ = "radar_budget_months"

    admin_id = Column(String(100), primary_key=True)
    month = Column(String(7), primary_key=True)
    charged_microusd = Column(BigInteger, nullable=False, default=0, server_default="0")
    reserved_microusd = Column(BigInteger, nullable=False, default=0, server_default="0")


class RadarBudgetReservation(Base):
    __tablename__ = "radar_budget_reservations"

    research_id = Column(ForeignKey("niche_researches.id", ondelete="RESTRICT"), primary_key=True)
    source = Column(String(40), primary_key=True)
    admin_id = Column(String(100), nullable=False)
    month = Column(String(7), nullable=False)
    reserved_microusd = Column(BigInteger, nullable=False)
    charged_microusd = Column(BigInteger)
    status = Column(String(20), nullable=False)
    remote_run_id = Column(String(100))


class WritingBrief(Base):
    __tablename__ = "writing_briefs"
    __table_args__ = (UniqueConstraint("research_id", name="uq_writing_briefs_research"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String(100), nullable=False, index=True)
    research_id = Column(ForeignKey("niche_researches.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="ready", server_default="ready")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
