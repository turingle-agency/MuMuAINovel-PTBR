"""Rotas administrativas do Radar de Nichos."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import check_admin
from app.database import User, get_db
from app.schemas.radar import BudgetView, RadarSettingsPatch, RadarSettingsView, SourceCheck, SourceName
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
