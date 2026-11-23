"""Preferências do Radar, chaves cifradas e cobertura por mercado."""
from datetime import datetime, timezone
from typing import get_args

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import NicheResearch, RadarBudgetMonth, RadarBudgetReservation, RadarSettings
from app.schemas.radar import (
    BudgetView, CoverageView, CredentialView, MarketProfile, RadarConfig, RadarSettingsPatch,
    RadarSettingsView, SecretSource, SourceCheck, SourceName,
)
from app.services.radar_repository import insert_once

CREDENTIAL_SOURCES = get_args(SecretSource)
SOURCE_NAMES = get_args(SourceName)
AVAILABLE_SOURCES = {"firecrawl", "youtube"}


class SecretStorageUnavailable(ValueError):
    """A chave do ambiente não permite cifrar credenciais."""


def _cipher() -> Fernet | None:
    try:
        return Fernet(settings.radar_secret_key) if settings.radar_secret_key else None
    except (ValueError, TypeError):
        return None


def _decrypt(cipher: Fernet | None, value: str | None) -> str | None:
    try:
        return cipher.decrypt(value.encode()).decode() if cipher and value else None
    except (InvalidToken, UnicodeError):
        return None


def _coverage(profile: MarketProfile, source: SourceName, creds: dict) -> CoverageView:
    enabled = source in profile.sources
    if source == "amazon" and profile.country == "PT":
        status, detail = "unsupported", "O marketplace Kindle de Portugal ainda não foi verificado."
    elif source == "agent_reach":
        status, detail = "unsupported", "A conexão usa uma conta secundária no Mac. Integração local pendente."
    elif source not in AVAILABLE_SOURCES:
        status, detail = "unsupported", "Coleta pendente de integração e validação neste mercado."
    elif not enabled:
        status, detail = "disabled", "Fonte desativada neste perfil."
    elif not creds[source].usable:
        status, detail = "not_configured", "Cadastre uma credencial válida antes de coletar."
    else:
        status, detail = "ready", "Credencial disponível. Use o diagnóstico para verificar o acesso."
    return CoverageView(enabled=enabled, status=status, detail=detail)


def _view(row: RadarSettings | None) -> RadarSettingsView:
    config = RadarConfig.model_validate(row.config if row else {})
    encrypted = row.encrypted_secrets if row else {}
    cipher = _cipher()
    creds = {
        source: CredentialView(present=source in encrypted, usable=bool(_decrypt(cipher, encrypted.get(source))))
        for source in CREDENTIAL_SOURCES
    }
    coverage = {
        profile.country: {source: _coverage(profile, source, creds) for source in SOURCE_NAMES}
        for profile in config.profiles
    }
    return RadarSettingsView(
        **config.model_dump(), encryption_available=cipher is not None, credentials=creds, coverage=coverage,
    )


async def load_radar_settings(db: AsyncSession, admin_id: str) -> RadarSettingsView:
    return _view(await db.get(RadarSettings, admin_id))


async def save_radar_settings(db: AsyncSession, admin_id: str, patch: RadarSettingsPatch) -> RadarSettingsView:
    cipher = _cipher()
    if cipher is None and any(value is not None for value in patch.secrets.values()):
        raise SecretStorageUnavailable("Configure RADAR_SECRET_KEY para salvar credenciais.")
    await db.execute(insert_once(db, RadarSettings, {"admin_id": admin_id}, RadarSettings.admin_id))
    row = (await db.scalars(select(RadarSettings).where(
        RadarSettings.admin_id == admin_id,
    ).with_for_update().execution_options(populate_existing=True))).one()

    updates = patch.model_dump(exclude={"secrets"}, exclude_none=True)
    config = RadarConfig.model_validate({**row.config, **updates})
    encrypted = dict(row.encrypted_secrets)
    for source, secret in patch.secrets.items():
        if secret is None:
            encrypted.pop(source, None)
        else:
            encrypted[source] = cipher.encrypt(secret.get_secret_value().encode()).decode()
    row.config = config.model_dump(mode="json")
    row.encrypted_secrets = encrypted
    await db.flush()
    return _view(row)


async def read_source_secret(db: AsyncSession, admin_id: str, source: str) -> str | None:
    row = await db.get(RadarSettings, admin_id)
    return _decrypt(_cipher(), row.encrypted_secrets.get(source)) if row else None


async def _probe(source: SourceName, secret: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            if source == "firecrawl":
                response = await client.get(
                    "https://api.firecrawl.dev/v2/team/credit-usage",
                    headers={"Authorization": f"Bearer {secret}"},
                )
                return response.is_success and response.json().get("success") is True
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/videoCategories",
                params={"part": "snippet", "regionCode": "BR"}, headers={"x-goog-api-key": secret},
            )
            return response.is_success and isinstance(response.json().get("items"), list)
    except (httpx.HTTPError, ValueError, AttributeError):
        return False


async def check_source(db: AsyncSession, admin_id: str, source: SourceName) -> SourceCheck:
    view = await load_radar_settings(db, admin_id)
    secret_source = {"amazon": "apify", "trends": "apify"}.get(source, source)
    secret = await read_source_secret(db, admin_id, secret_source)
    status_path = NicheResearch.signals["sources"][source]["status"].as_string()
    data = await db.scalar(select(status_path).where(
        NicheResearch.user_id == admin_id, NicheResearch.finished_at.is_not(None), status_path.is_not(None),
    ).order_by(NicheResearch.finished_at.desc(), NicheResearch.id.desc()).limit(1))
    await db.rollback()
    access, detail = "not_tested", "O diagnóstico informa a configuração e o último resultado disponível."
    if source in AVAILABLE_SOURCES and secret:
        ok = await _probe(source, secret)
        access, detail = ("ok", "Acesso confirmado.") if ok else ("error", "Acesso indisponível.")
    return SourceCheck(
        source=source, configured=bool(secret), access=access, last_status=data,
        coverage={country: coverage[source] for country, coverage in view.coverage.items()}, detail=detail,
    )


async def load_budget(db: AsyncSession, admin_id: str) -> BudgetView:
    config = await load_radar_settings(db, admin_id)
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    limit = int(config.budget.monthly_limit_usd * 1_000_000)
    row = await db.get(RadarBudgetMonth, (admin_id, month))
    charged, reserved = (row.charged_microusd, row.reserved_microusd) if row else (0, 0)
    pending = await db.scalar(select(func.count()).select_from(RadarBudgetReservation).where(
        RadarBudgetReservation.admin_id == admin_id, RadarBudgetReservation.month == month,
        RadarBudgetReservation.status.in_(["reserved", "uncertain"]),
    ))
    return BudgetView(
        month=month, limit_microusd=limit, charged_microusd=charged, reserved_microusd=reserved,
        committed_microusd=charged + reserved, blocked=charged + reserved >= limit, pending_count=pending,
    )
