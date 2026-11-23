"""Agenda semanal e construção da fotografia da consulta."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import NicheResearch, RadarSettings, User
from app.schemas.radar import (
    CollectorInput, MarketProfile, ProductType, RadarConfig, ResearchInput, ResearchSnapshot,
)
from app.services.radar_repository import enqueue_research_once, normalize_topic


def weekly_key(now: datetime, timezone: str) -> str | None:
    local = now.astimezone(ZoneInfo(timezone))
    if local.weekday() == 0 and local.hour < 9:
        return None
    iso = local.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def build_snapshot(config: RadarConfig, profile: MarketProfile, topic: str, product_type: ProductType,
                   now: datetime) -> ResearchSnapshot:
    end = now.astimezone(timezone.utc).date() - timedelta(days=1)
    category = None
    if product_type == "fiction" and profile.country != "PT":
        categories = {normalize_topic(key): value for key, value in profile.kindle_categories.items()}
        category = categories.get(normalize_topic(topic))
    return ResearchSnapshot(
        input=CollectorInput(
            query=topic, country=profile.country, language=profile.language, currency=profile.currency,
            product_type=product_type, category=category,
            start_date=end - timedelta(days=55), end_date=end,
        ),
        writing_language=profile.language, weights=config.weights,
        price_reference=profile.price_references.get(product_type),
        enabled_sources=[
            source for source in profile.sources if source != "meta" or product_type == "lowticket"
        ],
    )


async def enqueue_due_weeks(db: AsyncSession, now: datetime) -> int:
    settings = await db.execute(select(RadarSettings.admin_id, RadarSettings.config)
        .join(User, User.user_id == RadarSettings.admin_id)
        .where(User.is_admin.is_(True), User.trust_level.is_distinct_from(-1)))
    created = 0
    for admin_id, config_values in settings:
        config = RadarConfig.model_validate(config_values)
        if not config.schedule.enabled:
            continue
        week = weekly_key(now, config.schedule.timezone)
        if week is None:
            continue
        profiles = {profile.country: profile for profile in config.profiles if profile.active}
        research = NicheResearch
        existing = set((await db.execute(select(research.topic_key, research.country, research.product_type)
            .where(research.user_id == admin_id, research.mode == "weekly", research.week_key == week))).all())
        for entry in config.schedule.entries:
            niche = (normalize_topic(entry.topic), entry.country, entry.product_type)
            if niche in existing or entry.country not in profiles:
                continue
            existing.add(niche)
            _, inserted = await enqueue_research_once(db, admin_id, ResearchInput(
                topic=entry.topic, country=entry.country, product_type=entry.product_type,
                mode="weekly", input_key=week, week_key=week,
                snapshot=build_snapshot(config, profiles[entry.country], entry.topic, entry.product_type, now),
            ))
            created += inserted
    return created
