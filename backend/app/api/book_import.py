"""拆书导入 API"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logger import get_logger
from app.schemas.book_import import (
    BookImportApplyRequest,
    BookImportApplyResponse,
    BookImportPreviewResponse,
    BookImportRetryRequest,
    BookImportTaskCreateResponse,
    BookImportTaskCreateRequest,
    BookImportTaskStatusResponse,
)
from app.services.book_import_service import book_import_service
from app.api.settings import get_user_ai_service_from_db
from app.utils.sse_response import SSEResponse, create_sse_response

router = APIRouter(prefix="/book-import", tags=["Importação de livros"])
logger = get_logger(__name__)

MAX_TXT_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/tasks", response_model=BookImportTaskCreateResponse, summary="Criar tarefa de importação de livro (enviar TXT)")
async def create_book_import_task(
    request: Request,
    file: UploadFile = File(..., description="Arquivo TXT"),
    project_id: str | None = Form(default=None, description="Parâmetro de compatibilidade: a versão atual sempre cria um projeto novo, não aceita este valor"),
    create_new_project: bool = Form(default=True, description="Parâmetro de compatibilidade: a versão atual só aceita true"),
    import_mode: str = Form(default="append", description="Modo de importação: append/overwrite"),
    extract_mode: str = Form(default="tail", description="Escopo da análise: tail=últimos capítulos, full=livro inteiro"),
    tail_chapter_count: int = Form(default=10, description="Com extract_mode=tail, quantidade de capítulos finais a extrair; deve ser múltiplo de 5; acima de 50 o livro é analisado inteiro"),
):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .txt são aceitos")

    if import_mode not in {"append", "overwrite"}:
        raise HTTPException(status_code=400, detail="import_mode aceita apenas append ou overwrite")

    if extract_mode not in {"tail", "full"}:
        raise HTTPException(status_code=400, detail="extract_mode aceita apenas tail ou full")
    if tail_chapter_count < 5:
        raise HTTPException(status_code=400, detail="tail_chapter_count não pode ser menor que 5")
    if tail_chapter_count % 5 != 0:
        raise HTTPException(status_code=400, detail="tail_chapter_count deve ser múltiplo de 5")

    if tail_chapter_count > 50:
        extract_mode = "full"

    if project_id:
        raise HTTPException(status_code=400, detail="Por enquanto só é possível importar para um projeto novo, não é possível informar project_id")
    if not create_new_project:
        raise HTTPException(status_code=400, detail="Por enquanto só é possível importar para um projeto novo")

    create_payload = BookImportTaskCreateRequest(
        extract_mode=extract_mode,
        tail_chapter_count=tail_chapter_count,
    )

    content = await file.read()
    if len(content) > MAX_TXT_SIZE:
        raise HTTPException(status_code=413, detail="O arquivo excede o limite de 50MB")

    task = await book_import_service.create_task(
        user_id=user_id,
        filename=file.filename,
        file_content=content,
        project_id=None,
        create_new_project=True,
        import_mode=import_mode,
        extract_mode=create_payload.extract_mode,
        tail_chapter_count=create_payload.tail_chapter_count,
    )
    return task


@router.get("/tasks/{task_id}", response_model=BookImportTaskStatusResponse, summary="Consultar o status da tarefa de importação")
async def get_book_import_task_status(task_id: str, request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    return await book_import_service.get_task_status(task_id=task_id, user_id=user_id)


@router.get("/tasks/{task_id}/preview", response_model=BookImportPreviewResponse, summary="Obter a pré-visualização da importação")
async def get_book_import_preview(task_id: str, request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    return await book_import_service.get_preview(task_id=task_id, user_id=user_id)


@router.post("/tasks/{task_id}/apply", response_model=BookImportApplyResponse, summary="Confirmar e importar")
async def apply_book_import(
    task_id: str,
    payload: BookImportApplyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    return await book_import_service.apply_import(
        task_id=task_id,
        user_id=user_id,
        payload=payload,
        db=db,
    )


@router.delete("/tasks/{task_id}", summary="Cancelar tarefa de importação")
async def cancel_book_import_task(task_id: str, request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    return await book_import_service.cancel_task(task_id=task_id, user_id=user_id)


@router.post("/tasks/{task_id}/apply-stream", summary="Confirmar e importar (progresso via SSE)")
async def apply_book_import_stream(
    task_id: str,
    payload: BookImportApplyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    SSE 流式接口：执行基础导入后，分步生成世界观/职业/角色并实时推送进度。
    使用 asyncio.Queue 在服务与 SSE 生成器之间传递进度消息。
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    # 使用 asyncio.Queue 实现实时进度推送
    progress_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _progress_callback(message: str, progress: int, status: str = "processing") -> None:
        """进度回调：放入队列供 SSE 生成器消费"""
        sse_msg = SSEResponse.format_sse({
            "type": "progress",
            "message": message,
            "progress": progress,
            "status": status,
        })
        await progress_queue.put(sse_msg)

    async def _run_import() -> None:
        """在后台任务中执行导入并通过队列推送进度"""
        try:
            ai_service = await get_user_ai_service_from_db(user_id, db)
            result = await book_import_service.apply_import_stream(
                task_id=task_id,
                user_id=user_id,
                payload=payload,
                db=db,
                progress_callback=_progress_callback,
                ai_service=ai_service,
            )

            # 发送结果
            await progress_queue.put(await SSEResponse.send_result({
                "success": result.success,
                "project_id": result.project_id,
                "statistics": result.statistics,
            }))
            await progress_queue.put(await SSEResponse.send_progress("Importação concluída!", 100, "success"))
            await progress_queue.put(await SSEResponse.send_done())
        except HTTPException as exc:
            await progress_queue.put(await SSEResponse.send_error(exc.detail, exc.status_code))
        except Exception as exc:
            logger.error(f"拆书SSE导入失败: {exc}", exc_info=True)
            await progress_queue.put(await SSEResponse.send_error(str(exc), 500))
        finally:
            # 发送终止信号
            await progress_queue.put(None)

    async def _streaming_generator() -> AsyncGenerator[str, None]:
        yield await SSEResponse.send_progress("Iniciando a importação dos dados do livro...", 0, "processing")

        # 启动后台导入任务
        import_task = asyncio.create_task(_run_import())

        try:
            while True:
                msg = await progress_queue.get()
                if msg is None:
                    break
                yield msg
        except GeneratorExit:
            import_task.cancel()
        except Exception as exc:
            logger.error(f"SSE生成器异常: {exc}", exc_info=True)
            yield await SSEResponse.send_error(str(exc), 500)

    return create_sse_response(_streaming_generator())


@router.post("/tasks/{task_id}/retry-stream", summary="Tentar de novo as etapas de geração que falharam (progresso via SSE)")
async def retry_failed_steps_stream(
    task_id: str,
    payload: BookImportRetryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    SSE 流式接口：仅重试之前导入过程中失败的AI生成步骤（世界观/职业/角色）。
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    progress_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _progress_callback(message: str, progress: int, status: str = "processing") -> None:
        sse_msg = SSEResponse.format_sse({
            "type": "progress",
            "message": message,
            "progress": progress,
            "status": status,
        })
        await progress_queue.put(sse_msg)

    async def _run_retry() -> None:
        try:
            ai_service = await get_user_ai_service_from_db(user_id, db)
            result = await book_import_service.retry_failed_steps_stream(
                task_id=task_id,
                user_id=user_id,
                steps_to_retry=payload.steps,
                db=db,
                progress_callback=_progress_callback,
                ai_service=ai_service,
            )

            await progress_queue.put(await SSEResponse.send_result(result))

            if result.get("still_failed"):
                await progress_queue.put(await SSEResponse.send_progress(
                    f"Nova tentativa concluída, ainda há {len(result['still_failed'])} etapas com falha",
                    100,
                    "warning",
                ))
            else:
                await progress_queue.put(await SSEResponse.send_progress("Todas as etapas foram refeitas com sucesso!", 100, "success"))

            await progress_queue.put(await SSEResponse.send_done())
        except HTTPException as exc:
            await progress_queue.put(await SSEResponse.send_error(exc.detail, exc.status_code))
        except Exception as exc:
            logger.error(f"拆书SSE重试失败: {exc}", exc_info=True)
            await progress_queue.put(await SSEResponse.send_error(str(exc), 500))
        finally:
            await progress_queue.put(None)

    async def _streaming_generator() -> AsyncGenerator[str, None]:
        yield await SSEResponse.send_progress("Iniciando nova tentativa das etapas de geração que falharam...", 0, "processing")

        retry_task = asyncio.create_task(_run_retry())

        try:
            while True:
                msg = await progress_queue.get()
                if msg is None:
                    break
                yield msg
        except GeneratorExit:
            retry_task.cancel()
        except Exception as exc:
            logger.error(f"SSE重试生成器异常: {exc}", exc_info=True)
            yield await SSEResponse.send_error(str(exc), 500)

    return create_sse_response(_streaming_generator())