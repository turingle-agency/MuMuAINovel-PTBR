"""大纲导入导出 API。"""
from urllib.parse import quote
from typing import cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common import verify_project_access
from app.database import get_db
from app.logger import get_logger
from app.schemas.outline_transfer import (
    OutlineExportRequest,
    OutlineImportMode,
    OutlineImportPreviewResponse,
    OutlineImportResult,
)
from app.services.outline_transfer_service import OutlineTransferService


router = APIRouter(prefix="/outlines", tags=["Importação e exportação de esboços"])
logger = get_logger(__name__)

MAX_IMPORT_SIZE = 10 * 1024 * 1024


async def _read_import_file(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Apenas arquivos JSON são aceitos")
    content = await file.read(MAX_IMPORT_SIZE + 1)
    if len(content) > MAX_IMPORT_SIZE:
        raise HTTPException(status_code=413, detail="O arquivo excede o limite de 10MB")
    return content


def _parse_mode(mode: str) -> OutlineImportMode:
    if mode not in {"append", "merge"}:
        raise HTTPException(status_code=422, detail="O modo de importação deve ser append ou merge")
    return cast(OutlineImportMode, mode)


@router.post("/export", summary="Exportar esboço do projeto")
async def export_outlines(
    export_request: OutlineExportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    project = await verify_project_access(export_request.project_id, user_id, db)
    try:
        document = await OutlineTransferService.export_outlines(
            project=project,
            outline_ids=export_request.outline_ids,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    safe_title = "".join(char for char in project.title if char.isalnum() or char in (" ", "-", "_"))
    filename = f"outlines_{safe_title or 'project'}.json"
    logger.info("用户 %s 导出项目 %s 的 %s 条大纲", user_id, project.id, document.count)
    return Response(
        content=document.model_dump_json(indent=2, exclude_none=True).encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.post(
    "/import/preview",
    response_model=OutlineImportPreviewResponse,
    summary="Pré-visualizar importação de esboço",
)
async def preview_outline_import(
    request: Request,
    project_id: str = Form(...),
    mode: str = Form("append"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    import_mode = _parse_mode(mode)
    user_id = getattr(request.state, "user_id", None)
    project = await verify_project_access(project_id, user_id, db)
    parsed = OutlineTransferService.parse_file(await _read_import_file(file))
    return await OutlineTransferService.preview_import(parsed, project, import_mode, db)


@router.post(
    "/import",
    response_model=OutlineImportResult,
    summary="Importar esboço do projeto",
)
async def import_outlines(
    request: Request,
    project_id: str = Form(...),
    mode: str = Form("append"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    import_mode = _parse_mode(mode)
    user_id = getattr(request.state, "user_id", None)
    project = await verify_project_access(project_id, user_id, db)
    parsed = OutlineTransferService.parse_file(await _read_import_file(file))
    try:
        result = await OutlineTransferService.import_outlines(
            parsed=parsed,
            project=project,
            mode=import_mode,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Falha na validação do arquivo importado: {exc}") from exc
    except Exception as exc:
        logger.error("大纲导入失败: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Falha ao importar o esboço, tente novamente mais tarde") from exc

    logger.info(
        "用户 %s 向项目 %s 导入大纲：新增 %s，更新 %s",
        user_id,
        project.id,
        result.imported,
        result.updated,
    )
    return result
