"""小说封面生成服务"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import PROJECT_ROOT, settings as app_settings
from app.logger import get_logger
from app.models.project import Project
from app.models.settings import Settings
from app.services.ai_providers.codex_provider import (
    CodexError,
    codex_reason,
    fallback_failure_message,
    reset_codex_cooldown,
)
from app.services.cover_providers.base_cover_provider import BaseCoverProvider, CoverGenerationResult
from app.services.cover_providers.codex_cover_provider import CodexCoverProvider
from app.services.cover_providers.gemini_cover_provider import GeminiCoverProvider
from app.services.cover_providers.grok_cover_provider import GrokCoverProvider
from app.services.prompt_service import PromptService

logger = get_logger(__name__)

COVER_WIDTH = 1024
COVER_HEIGHT = 1536
GENERATED_COVER_STORAGE_DIR = PROJECT_ROOT / "storage" / "generated_covers"
GENERATED_COVER_PUBLIC_PREFIX = "/generated-assets/covers"


COVER_INTERRUPTED_MESSAGE = "A geração da capa foi interrompida; gere novamente."
COVER_IN_PROGRESS_MESSAGE = "A capa ainda está em geração; aguarde a conclusão."


async def reset_interrupted_covers(executor) -> int:
    """Marca como falha as capas presas em "generating" (ex.: reinício do serviço).

    `executor` é uma AsyncConnection ou AsyncSession. Devolve quantas linhas foram alteradas.
    """
    result = await executor.execute(
        sql_update(Project)
        .where(Project.cover_status == "generating")
        .values(
            cover_status="failed",
            cover_error="Serviço reiniciado; a geração da capa foi interrompida, gere novamente.",
        )
    )
    return result.rowcount or 0


@dataclass
class CoverTestResult:
    success: bool
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None


class CoverGenerationService:
    """封面生成服务"""

    async def generate_cover(
        self,
        *,
        db: AsyncSession,
        user_id: str,
        project_id: str,
        overwrite: bool = True,
    ) -> dict:
        project = await self._get_project(db=db, user_id=user_id, project_id=project_id)
        settings = await self._get_settings(db=db, user_id=user_id)
        self._validate_cover_settings(settings)

        if project.cover_status == "generating":
            raise HTTPException(status_code=409, detail=COVER_IN_PROGRESS_MESSAGE)
        if project.cover_status == "ready" and project.cover_image_url and not overwrite:
            raise HTTPException(status_code=400, detail="O projeto já tem capa; para sobrescrever, envie overwrite=true")

        prompt = await PromptService.build_novel_cover_prompt(
            project,
            user_id=user_id,
            db=db,
        )
        project.cover_status = "generating"
        project.cover_error = None
        project.cover_prompt = prompt
        await db.commit()
        await db.refresh(project)

        try:
            provider = self._build_provider(settings)
            try:
                result = await provider.generate_cover(
                    prompt=prompt,
                    model=settings.cover_image_model or "",
                    width=COVER_WIDTH,
                    height=COVER_HEIGHT,
                )
            except CodexError as codex_error:
                result = await self._generate_with_fallback(
                    settings=settings, prompt=prompt, codex_error=codex_error
                )
            image_url = self._save_cover_file(
                user_id=user_id,
                project_id=project.id,
                content=result["content"],
                file_extension=result["file_extension"],
            )

            project.cover_image_url = image_url
            project.cover_status = "ready"
            project.cover_error = None
            project.cover_updated_at = datetime.utcnow()
            project.cover_prompt = result.get("revised_prompt") or prompt
            await db.commit()
            await db.refresh(project)

            return {
                "project_id": project.id,
                "cover_status": project.cover_status,
                "cover_image_url": project.cover_image_url,
                "cover_prompt": project.cover_prompt,
                "provider": result["provider"],
                "model": result["model"],
                "message": "Capa gerada com sucesso",
            }
        except asyncio.CancelledError:
            # Requisição cancelada (cliente desconectou/desligamento): não deixa a capa presa em "generating".
            logger.warning("Geração de capa cancelada: project_id=%s", project.id)
            await self._mark_cover_failed(db, project, COVER_INTERRUPTED_MESSAGE)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error("封面生成上游 HTTP 错误: project_id=%s error=%s", project.id, exc, exc_info=True)
            detail = self._extract_upstream_error_detail(exc)
            project.cover_status = "failed"
            project.cover_error = detail
            await db.commit()
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except HTTPException as exc:
            logger.error("封面生成业务错误: project_id=%s error=%s", project.id, exc.detail, exc_info=True)
            project.cover_status = "failed"
            project.cover_error = str(exc.detail)
            await db.commit()
            raise
        except Exception as exc:
            logger.error("封面生成失败: project_id=%s error=%s", project.id, exc, exc_info=True)
            project.cover_status = "failed"
            project.cover_error = str(exc)
            await db.commit()
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @staticmethod
    async def _mark_cover_failed(db: AsyncSession, project: Project, message: str) -> None:
        try:
            await db.rollback()
            project.cover_status = "failed"
            project.cover_error = message
            await db.commit()
        except BaseException as exc:  # noqa: BLE001 - melhor esforço; a sessão pode estar inutilizável
            logger.error("Não foi possível marcar a capa como falha: %r", exc)

    async def test_cover_settings(
        self,
        *,
        provider: str,
        api_key: str,
        api_base_url: Optional[str],
        model: str,
    ) -> CoverTestResult:
        is_codex = (provider or "").lower().strip() == "codex"
        if not provider or (not is_codex and (not api_key or not model)):
            raise HTTPException(status_code=400, detail="Configuração da imagem de capa incompleta: informe provider, api_key e model")

        provider_instance = self._build_provider_from_values(
            provider=provider,
            api_key=api_key,
            api_base_url=api_base_url,
        )
        reset_codex_cooldown()  # teste explícito: ignora a espera pós-falha
        test_prompt = (
            "Create a clean fantasy novel cover illustration, vertical book cover, "
            "standard 2:3 ratio, atmospheric lighting, no text, no watermark."
        )
        try:
            await provider_instance.generate_cover(
                prompt=test_prompt,
                model=model,
                width=COVER_WIDTH,
                height=COVER_HEIGHT,
            )
        except CodexError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Não foi possível gerar a imagem pelo Codex: {codex_reason(exc)}.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = self._extract_upstream_error_detail(exc)
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc

        return CoverTestResult(
            success=True,
            message="Teste da API de imagem de capa bem-sucedido",
            provider=provider,
            model=model,
        )

    async def get_cover_download_path(
        self,
        *,
        db: AsyncSession,
        user_id: str,
        project_id: str,
    ) -> tuple[Project, Path]:
        project = await self._get_project(db=db, user_id=user_id, project_id=project_id)
        if project.cover_status != "ready" or not project.cover_image_url:
            raise HTTPException(status_code=404, detail="O projeto ainda não tem capa disponível para download")

        absolute_path = self._resolve_cover_path(project.cover_image_url)
        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail="Arquivo da capa não encontrado, gere novamente")
        return project, absolute_path

    async def clear_cover_metadata(self, *, db: AsyncSession, project: Project) -> None:
        project.cover_image_url = None
        project.cover_prompt = None
        project.cover_status = "none"
        project.cover_error = None
        project.cover_updated_at = None
        await db.commit()

    async def _get_project(self, *, db: AsyncSession, user_id: str, project_id: str) -> Project:
        result = await db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return project

    async def _get_settings(self, *, db: AsyncSession, user_id: str) -> Settings:
        result = await db.execute(select(Settings).where(Settings.user_id == user_id))
        settings = result.scalar_one_or_none()
        if not settings:
            raise HTTPException(status_code=400, detail="Configure primeiro a imagem de capa na página de configurações")
        return settings

    def _validate_cover_settings(self, settings: Settings) -> None:
        if not settings.cover_enabled:
            raise HTTPException(status_code=400, detail="A função de imagem de capa não está habilitada; ative-a na página de configurações")
        is_codex = (settings.cover_api_provider or "").lower().strip() == "codex"
        if not settings.cover_api_provider:
            raise HTTPException(status_code=400, detail="Configuração da imagem de capa incompleta; complete-a na página de configurações")
        if not is_codex and (not settings.cover_api_key or not settings.cover_image_model):
            raise HTTPException(status_code=400, detail="Configuração da imagem de capa incompleta; complete-a na página de configurações")

    def _build_provider(self, settings: Settings) -> BaseCoverProvider:
        return self._build_provider_from_values(
            provider=settings.cover_api_provider or "",
            api_key=settings.cover_api_key or "",
            api_base_url=settings.cover_api_base_url,
        )

    def _build_provider_from_values(
        self,
        *,
        provider: str,
        api_key: str,
        api_base_url: Optional[str],
    ) -> BaseCoverProvider:
        provider_value = (provider or "").lower().strip()
        normalized_base_url = (api_base_url or "").rstrip("/")
        if provider_value == "codex":
            return CodexCoverProvider(
                binary=app_settings.codex_binary,
                timeout_s=app_settings.codex_timeout_s,
            )
        if provider_value == "gemini":
            return GeminiCoverProvider(api_key=api_key, base_url=normalized_base_url)
        if provider_value == "grok":
            return GrokCoverProvider(api_key=api_key, base_url=normalized_base_url)
        raise HTTPException(status_code=400, detail="Provedor de capa não suportado: use Codex, Gemini ou Grok")

    async def _generate_with_fallback(
        self,
        *,
        settings: Settings,
        prompt: str,
        codex_error: CodexError,
    ) -> CoverGenerationResult:
        """Codex falhou: tenta a API de reserva (Gemini/Grok com chave) ou levanta 503 em PT-BR."""
        fallback_provider = (settings.fallback_api_provider or "").lower().strip()
        motivo_codex = codex_reason(codex_error)
        if fallback_provider and settings.fallback_api_key:
            if fallback_provider not in ("gemini", "grok"):
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"O Codex não gerou a capa ({motivo_codex}) e a API de reserva "
                        f"({fallback_provider}) não gera imagens. Use Gemini ou Grok como reserva em Configurações."
                    ),
                ) from codex_error
            if "imag" not in (settings.fallback_llm_model or "").lower():
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"O Codex não gerou a capa ({motivo_codex}) e o modelo da API de reserva "
                        f"({settings.fallback_llm_model or 'não definido'}) não parece gerar imagens. "
                        "Configure um modelo de imagem (nome com \"image\" ou \"imagen\") em Configurações."
                    ),
                ) from codex_error
        if (
            fallback_provider in ("gemini", "grok")
            and settings.fallback_api_key
            and settings.fallback_llm_model
        ):
            logger.warning("Codex falhou ao gerar capa (%s); usando API de reserva %s", codex_error, fallback_provider)
            provider = self._build_provider_from_values(
                provider=fallback_provider,
                api_key=settings.fallback_api_key,
                api_base_url=settings.fallback_api_base_url,
            )
            try:
                return await provider.generate_cover(
                    prompt=prompt,
                    model=settings.fallback_llm_model,
                    width=COVER_WIDTH,
                    height=COVER_HEIGHT,
                )
            except Exception as fallback_error:
                logger.error("API de reserva da capa também falhou: %r", fallback_error)
                raise HTTPException(
                    status_code=503,
                    detail=fallback_failure_message(codex_error, fallback_error),
                ) from fallback_error
        logger.error("Codex falhou ao gerar capa e não há reserva: %s", codex_error)
        raise HTTPException(
            status_code=503,
            detail=f"Não foi possível gerar a imagem pelo Codex: {codex_reason(codex_error)}.",
        ) from codex_error

    def _save_cover_file(
        self,
        *,
        user_id: str,
        project_id: str,
        content: bytes,
        file_extension: str,
    ) -> str:
        user_dir = GENERATED_COVER_STORAGE_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        safe_extension = (file_extension or "png").lstrip(".")
        filename = f"{project_id}_{timestamp}.{safe_extension}"
        file_path = user_dir / filename
        file_path.write_bytes(content)
        logger.info("封面文件已保存: project_id=%s path=%s", project_id, file_path)
        return f"{GENERATED_COVER_PUBLIC_PREFIX}/{quote(user_id)}/{quote(filename)}"

    def _resolve_cover_path(self, cover_image_url: Optional[str]) -> Path:
        if not cover_image_url:
            raise HTTPException(status_code=404, detail="O projeto ainda não tem capa disponível para download")

        if cover_image_url.startswith(f"{GENERATED_COVER_PUBLIC_PREFIX}/"):
            relative_path = cover_image_url.replace(f"{GENERATED_COVER_PUBLIC_PREFIX}/", "", 1)
            return GENERATED_COVER_STORAGE_DIR / relative_path

        if cover_image_url.startswith("/assets/generated_covers/"):
            relative_path = cover_image_url.replace("/assets/generated_covers/", "", 1)
            return GENERATED_COVER_STORAGE_DIR / relative_path

        raise HTTPException(status_code=404, detail="Caminho do arquivo da capa inválido, gere novamente")

    @staticmethod
    def _extract_upstream_error_detail(exc: httpx.HTTPStatusError) -> str:
        response = exc.response
        if response is None:
            return str(exc)

        try:
            data = response.json()
        except json.JSONDecodeError:
            text = response.text.strip()
            return text or str(exc)

        if isinstance(data, dict):
            for key in ("detail", "message", "error", "msg"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, dict):
                    for nested_key in ("message", "detail", "msg"):
                        nested_value = value.get(nested_key)
                        if isinstance(nested_value, str) and nested_value.strip():
                            return nested_value.strip()
                if isinstance(value, list) and value:
                    first_item = value[0]
                    if isinstance(first_item, str) and first_item.strip():
                        return first_item.strip()

        text = response.text.strip()
        if text:
            return text
        return str(exc)


cover_generation_service = CoverGenerationService()
