"""Rotas administrativas do Radar de Nichos."""
from datetime import datetime, timezone
from typing import Annotated, get_args

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import check_admin
from app.database import NicheResearch, User, WritingBrief, get_db
from app.schemas.radar import (
    BriefDetail, BriefListItem, BudgetView, PageFilters, RadarSettingsPatch, RadarSettingsView,
    ResearchAccepted, ResearchDetail, ResearchFilters, ResearchInput, ResearchListItem, ResearchPage,
    ResearchRequest, ResearchSnapshot, ResearchStatus, SourceCheck, SourceName,
)
from app.services.radar_collectors.base import utc_now
from app.services.radar_repository import (
    ResearchConflict, create_brief, enqueue_research, get_brief, get_manual_retry, get_research,
    list_briefs, list_history, list_researches, previous_research,
)
from app.services.radar_schedule import build_snapshot
from app.services.radar_scoring import comparable_scores
from app.services.radar_settings import (
    SecretStorageUnavailable, check_source, load_budget, load_radar_settings, save_radar_settings,
)

router = APIRouter(prefix="/radar", tags=["Radar de Nichos"])
Admin = Annotated[User, Depends(check_admin)]
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/settings")
async def settings_view(admin: Admin, db: DB) -> RadarSettingsView:
    return await load_radar_settings(db, admin.user_id)


@router.put("/settings")
async def update_settings(patch: RadarSettingsPatch, admin: Admin, db: DB) -> RadarSettingsView:
    try:
        result = await save_radar_settings(db, admin.user_id, patch)
    except SecretStorageUnavailable as error:
        raise HTTPException(503, str(error)) from None
    except ValidationError:
        raise HTTPException(422, "Configuração do Radar inválida.") from None
    await db.commit()
    return result


@router.post("/sources/{source}/check")
async def source_check(source: SourceName, admin: Admin, db: DB) -> SourceCheck:
    return await check_source(db, admin.user_id, source)


@router.get("/budget")
async def budget_view(admin: Admin, db: DB) -> BudgetView:
    return await load_budget(db, admin.user_id)


def _snapshot(row: NicheResearch | None) -> ResearchSnapshot | None:
    if row and isinstance(row.signals, dict) and row.signals.get("version") == 1:
        return ResearchSnapshot.model_validate(row.signals)
    return None


def _utc(value: datetime | None) -> datetime | None:
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def _research_item(row: NicheResearch, snapshot: ResearchSnapshot | None) -> ResearchListItem:
    status = row.status if row.status in get_args(ResearchStatus) else "failed"
    result = ResearchListItem(
        id=row.id, topic=row.topic, country=row.country, product_type=row.product_type,
        status=status, mode=row.mode, week_key=row.week_key, legacy=snapshot is None,
        created_at=_utc(row.created_at), finished_at=_utc(row.finished_at),
    )
    if snapshot is None:
        return result

    score = snapshot.score
    if score is not None:
        result.score = score.score
        result.direction_points = score.direction_points
        result.amazon_average = score.amazon_average
        result.amazon_count = score.amazon_count
    if snapshot.input is not None:
        result.currency = snapshot.input.currency
        result.kindle_category = snapshot.input.category
    result.source_statuses = {key: value.status for key, value in snapshot.sources.items()}
    result.citable_count = len(snapshot.citable_evidence())
    if row.product_type == "fiction" and (amazon := snapshot.sources.get("amazon")):
        result.kindle_best_rank = min((
            item.data.rank for item in amazon.items
            if item.kind == "book" and item.data.rank is not None and not item.data.sponsored
        ), default=None)
    if row.product_type == "lowticket" and (meta := snapshot.sources.get("meta")):
        ids = {item.id for item in meta.items if item.kind == "ad" and item.data.active and item.data.commercial}
        if (ids and meta.status in {"ok", "partial"}) or meta.status == "empty":
            result.meta_ads_count = len(ids)
    return result


def _detail(row: NicheResearch, snapshot: ResearchSnapshot | None,
            before: ResearchSnapshot | None = None) -> ResearchDetail:
    delta = None
    if snapshot and before and snapshot.score and before.score and comparable_scores(snapshot.score, before.score):
        delta = round(snapshot.score.score - before.score.score, 1)
    return ResearchDetail(**_research_item(row, snapshot).model_dump(), snapshot=snapshot, score_delta=delta)


async def _require_research(db: AsyncSession, admin_id: str, research_id: str) -> NicheResearch:
    row = await get_research(db, admin_id, research_id)
    if row is None:
        raise HTTPException(404, "Pesquisa não encontrada.")
    return row


@router.post("/researches", status_code=202)
async def submit_research(payload: ResearchRequest, admin: Admin, db: DB) -> ResearchAccepted:
    try:
        row = await get_manual_retry(db, admin.user_id, payload)
        if row is None:
            config = await load_radar_settings(db, admin.user_id)
            profile = next((p for p in config.profiles if p.country == payload.country and p.active), None)
            if profile is None:
                raise HTTPException(422, "Selecione um mercado ativo.")
            snapshot = build_snapshot(config, profile, payload.topic, payload.product_type, utc_now())
            snapshot.budget_confirmation = payload.budget_confirmation
            row = await enqueue_research(db, admin.user_id, ResearchInput(
                topic=payload.topic, country=payload.country, product_type=payload.product_type,
                mode="manual", input_key=str(payload.request_id), snapshot=snapshot,
            ))
            await db.commit()
    except ResearchConflict as error:
        raise HTTPException(409, str(error)) from None
    return ResearchAccepted(id=row.id, status=row.status)


def _research_page(result: ResearchPage) -> ResearchPage[ResearchListItem]:
    return ResearchPage[ResearchListItem](
        items=[_research_item(row, _snapshot(row)) for row in result.items], total=result.total,
        page=result.page, page_size=result.page_size,
    )


@router.get("/researches")
async def researches(admin: Admin, db: DB, filters: Annotated[ResearchFilters, Query()]) -> ResearchPage[ResearchListItem]:
    return _research_page(await list_researches(db, admin.user_id, filters))


@router.get("/researches/{research_id}")
async def research_detail(research_id: str, admin: Admin, db: DB) -> ResearchDetail:
    row = await _require_research(db, admin.user_id, research_id)
    snapshot = _snapshot(row)
    before = await previous_research(db, row) if snapshot and snapshot.score else None
    return _detail(row, snapshot, _snapshot(before))


@router.get("/researches/{research_id}/history")
async def research_history(
    research_id: str, admin: Admin, db: DB, filters: Annotated[PageFilters, Query()],
) -> ResearchPage[ResearchListItem]:
    row = await _require_research(db, admin.user_id, research_id)
    return _research_page(await list_history(db, row, filters))


def _brief_detail(brief: WritingBrief, research: NicheResearch, snapshot: ResearchSnapshot | None) -> BriefDetail:
    return BriefDetail(
        id=brief.id, status=brief.status, created_at=_utc(brief.created_at), research=_detail(research, snapshot),
    )


@router.post("/researches/{research_id}/brief", status_code=201, responses={200: {"model": BriefDetail}})
async def submit_brief(research_id: str, response: Response, admin: Admin, db: DB) -> BriefDetail:
    research = await _require_research(db, admin.user_id, research_id)
    snapshot = _snapshot(research)
    if research.status not in {"complete", "partial"} or snapshot is None or not snapshot.citable_evidence():
        raise HTTPException(409, "A pesquisa precisa estar concluída e conter evidência citável.")
    brief, created = await create_brief(db, research)
    await db.commit()
    if not created:
        response.status_code = 200
    return _brief_detail(brief, research, snapshot)


@router.get("/briefs")
async def briefs(admin: Admin, db: DB, filters: Annotated[PageFilters, Query()]) -> ResearchPage[BriefListItem]:
    result = await list_briefs(db, admin.user_id, filters)
    items = [
        BriefListItem(id=brief.id, status=brief.status, created_at=_utc(brief.created_at),
                      research=_research_item(row, _snapshot(row)))
        for brief, row in result.items
    ]
    return ResearchPage[BriefListItem](items=items, total=result.total, page=result.page, page_size=result.page_size)


@router.get("/briefs/{brief_id}")
async def brief_detail(brief_id: str, admin: Admin, db: DB) -> BriefDetail:
    pair = await get_brief(db, admin.user_id, brief_id)
    if pair is None:
        raise HTTPException(404, "Briefing não encontrado.")
    brief, row = pair
    return _brief_detail(brief, row, _snapshot(row))
