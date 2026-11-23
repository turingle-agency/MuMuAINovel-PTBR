"""Persistência das pesquisas no âmbito do administrador."""
import hashlib
import json
import unicodedata

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import NicheResearch, WritingBrief
from app.schemas.radar import PageFilters, ResearchFilters, ResearchInput, ResearchPage


class ResearchConflict(ValueError):
    """A chave informada já vincula outra entrada."""


def normalize_topic(topic: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", topic).split()).casefold()


def insert_once(db, model, values, key):
    insert = sqlite_insert if db.get_bind().dialect.name == "sqlite" else pg_insert
    return insert(model).values(**values).on_conflict_do_nothing(index_elements=[key])


async def enqueue_research(db: AsyncSession, admin_id: str, input: ResearchInput) -> NicheResearch:
    topic_key = normalize_topic(input.topic)
    identidade = (topic_key, input.country, input.product_type)
    origem = (*identidade, input.week_key) if input.mode == "weekly" else (input.input_key,)
    key = hashlib.sha256(json.dumps((admin_id, input.mode, origem)).encode()).hexdigest()
    values = dict(
        user_id=admin_id, topic=input.topic.strip(), topic_key=topic_key, country=input.country,
        product_type=input.product_type, mode=input.mode, week_key=input.week_key,
        topic_hash=hashlib.sha256(topic_key.encode()).hexdigest(),
        input_key=key, signals=input.snapshot.model_dump(mode="json"),
    )
    await db.execute(insert_once(db, NicheResearch, values, NicheResearch.input_key))
    research = (await db.scalars(select(NicheResearch).where(
        NicheResearch.user_id == admin_id, NicheResearch.input_key == key,
    ))).one()
    if input.mode == "manual" and (
        (research.topic, research.country, research.product_type)
        != (values["topic"], input.country, input.product_type)
    ):
        raise ResearchConflict("Esta chave já foi usada em uma pesquisa diferente.")
    return research


async def get_research(db: AsyncSession, admin_id: str, research_id: str) -> NicheResearch | None:
    return await db.scalar(select(NicheResearch).where(
        NicheResearch.user_id == admin_id, NicheResearch.id == research_id,
    ))


async def _page(db, query, filters, *order_by):
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    items = await db.scalars(query.order_by(*order_by).limit(filters.page_size).offset(
        (filters.page - 1) * filters.page_size,
    ))
    return ResearchPage(items=list(items), total=total, **filters.model_dump(include={"page", "page_size"}))


async def list_researches(db: AsyncSession, admin_id: str, filters: ResearchFilters) -> ResearchPage:
    research = NicheResearch
    order = (research.created_at.desc().nulls_last(), research.id.desc())
    rank = select(research.id, func.row_number().over(
        partition_by=(research.topic_key, research.country, research.product_type,
                      case((research.topic_key.is_(None), research.id))),
        order_by=order,
    ).label("position")).where(research.user_id == admin_id)
    for name in ("country", "product_type", "mode", "week_key"):
        value = getattr(filters, name)
        if value is not None:
            rank = rank.where(getattr(research, name) == value)
    ranked = rank.subquery()
    query = select(research).join(ranked, ranked.c.id == research.id).where(ranked.c.position == 1)
    return await _page(db, query, filters, *order)


async def list_history(db: AsyncSession, research: NicheResearch, filters: PageFilters) -> ResearchPage:
    model = NicheResearch
    query = select(model).where(model.user_id == research.user_id)
    if research.topic_key is None:
        query = query.where(model.id == research.id)
    else:
        query = query.where(
            model.topic_key == research.topic_key,
            model.topic_hash == research.topic_hash,
            model.country == research.country,
            model.product_type == research.product_type,
        )
    return await _page(db, query, filters, model.created_at.desc().nulls_last(), model.id.desc())


async def create_brief(db: AsyncSession, research: NicheResearch) -> tuple[WritingBrief, bool]:
    stmt = insert_once(db, WritingBrief, {
        "research_id": research.id, "admin_id": research.user_id,
    }, WritingBrief.research_id).returning(WritingBrief)
    brief = await db.scalar(stmt)
    if brief is not None:
        return brief, True
    brief = (await db.scalars(select(WritingBrief).where(
        WritingBrief.research_id == research.id, WritingBrief.admin_id == research.user_id,
    ))).one()
    return brief, False
