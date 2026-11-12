"""Oferta (produto principal, order bump, upsell, downsell)"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Offer(Base):
    __tablename__ = "offers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True)
    niche_research_id = Column(
        String(36), ForeignKey("niche_researches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at = Column(DateTime, server_default=func.now())


class OfferItem(Base):
    __tablename__ = "offer_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_id = Column(String(36), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    suggested_price = Column(Numeric(10, 2))
    currency = Column(String(3))
    price_rationale = Column(Text)

    __table_args__ = (
        CheckConstraint(
            "role IN ('main', 'order_bump', 'upsell', 'downsell')",
            name="check_offer_item_role",
        ),
    )
