"""大纲导入导出服务。"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.models.outline import Outline
from app.models.project import Project
from app.schemas.outline_transfer import (
    OutlineExportDocument,
    OutlineImportDetail,
    OutlineImportMode,
    OutlineImportPreviewResponse,
    OutlineImportResult,
    OutlineImportStatistics,
    OutlineSourceProject,
    OutlineTransferItem,
)


@dataclass
class ParsedOutlineDocument:
    version: str = ""
    source_type: str = "unknown"
    source_project: OutlineSourceProject | None = None
    items: list[OutlineTransferItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class OutlineTransferService:
    """提供大纲文件解析、预览以及原子导入。"""

    OUTLINE_FORMAT_VERSION = "1.0.0"
    PROJECT_FORMAT_VERSIONS = {"1.0.0", "1.1.0"}
    MAX_ITEMS = 5000

    @classmethod
    async def export_outlines(
        cls,
        project: Project,
        outline_ids: list[str] | None,
        db: AsyncSession,
    ) -> OutlineExportDocument:
        query = select(Outline).where(Outline.project_id == project.id)

        requested_ids: list[str] | None = None
        if outline_ids is not None:
            requested_ids = list(dict.fromkeys(outline_ids))
            if not requested_ids:
                raise ValueError("Selecione pelo menos um esboço")
            query = query.where(Outline.id.in_(requested_ids))

        result = await db.execute(query.order_by(Outline.order_index, Outline.created_at))
        outlines = result.scalars().all()

        if requested_ids is not None and len(outlines) != len(requested_ids):
            raise ValueError("Alguns esboços não existem ou não pertencem ao projeto atual")

        items = [
            OutlineTransferItem(
                order_index=outline.order_index,
                title=outline.title,
                content=outline.content or "",
                structure=outline.structure,
            )
            for outline in outlines
        ]

        return OutlineExportDocument(
            version=cls.OUTLINE_FORMAT_VERSION,
            export_time=datetime.now(timezone.utc),
            source_project=OutlineSourceProject(
                title=project.title,
                outline_mode=project.outline_mode,
            ),
            count=len(items),
            data=items,
        )

    @classmethod
    def parse_file(cls, content: bytes) -> ParsedOutlineDocument:
        parsed = ParsedOutlineDocument()
        try:
            raw = json.loads(content.decode("utf-8-sig"))
        except UnicodeDecodeError:
            parsed.errors.append("O arquivo deve usar a codificação UTF-8")
            return parsed
        except json.JSONDecodeError as exc:
            parsed.errors.append(f"Erro de formato JSON: linha {exc.lineno}, coluna {exc.colno}")
            return parsed

        if not isinstance(raw, dict):
            parsed.errors.append("O nó raiz do arquivo deve ser um objeto JSON")
            return parsed

        raw_items: Any = None
        declared_count: Any = None
        export_type = raw.get("export_type")

        if export_type == "outlines":
            parsed.source_type = "outlines"
            parsed.version = str(raw.get("version") or "")
            raw_items = raw.get("data")
            declared_count = raw.get("count")
            parsed.source_project = cls._parse_source_project(raw.get("source_project"))
            if parsed.version != cls.OUTLINE_FORMAT_VERSION:
                parsed.errors.append(
                    f"Versão do arquivo de esboços não suportada: {parsed.version or 'ausente'}, versão atualmente suportada: {cls.OUTLINE_FORMAT_VERSION}"
                )
        elif isinstance(raw.get("outlines"), list) and isinstance(raw.get("project"), dict):
            parsed.source_type = "project"
            parsed.version = str(raw.get("version") or "")
            raw_items = raw.get("outlines")
            declared_count = len(raw_items)
            project_data = raw["project"]
            parsed.source_project = cls._parse_source_project(
                {
                    "title": project_data.get("title", "Projeto desconhecido"),
                    "outline_mode": project_data.get("outline_mode", "one-to-many"),
                }
            )
            parsed.warnings.append("Arquivo de exportação de projeto completo detectado; apenas os dados de esboço serão importados")
            if parsed.version not in cls.PROJECT_FORMAT_VERSIONS:
                parsed.errors.append(
                    f"Versão do arquivo de projeto não suportada: {parsed.version or 'ausente'}"
                )
        else:
            parsed.errors.append("Não é um arquivo válido de exportação de esboços nem de projeto completo")
            return parsed

        if not isinstance(raw_items, list):
            parsed.errors.append("O campo data/outlines deve ser um array")
            return parsed
        if len(raw_items) > cls.MAX_ITEMS:
            parsed.errors.append(f"A quantidade de esboços não pode exceder {cls.MAX_ITEMS} itens")
            return parsed
        if declared_count is not None and declared_count != len(raw_items):
            parsed.warnings.append(
                f"O arquivo declara {declared_count} esboços, mas contém {len(raw_items)} itens"
            )

        seen_orders: set[int] = set()
        for index, raw_item in enumerate(raw_items, start=1):
            item, item_errors = cls._parse_item(raw_item, index)
            parsed.errors.extend(item_errors)
            if item is None:
                continue
            if item.order_index in seen_orders:
                parsed.errors.append(f"O esboço nº {index} tem a ordem {item.order_index} duplicada")
                continue
            seen_orders.add(item.order_index)
            parsed.items.append(item)

        parsed.items.sort(key=lambda item: item.order_index)
        if not parsed.items and not parsed.errors:
            parsed.errors.append("O arquivo não contém esboços importáveis")
        return parsed

    @staticmethod
    def _parse_source_project(raw: Any) -> OutlineSourceProject | None:
        if not isinstance(raw, dict):
            return None
        mode = raw.get("outline_mode")
        if mode not in {"one-to-one", "one-to-many"}:
            return None
        return OutlineSourceProject(
            title=str(raw.get("title") or "Projeto desconhecido"),
            outline_mode=mode,
        )

    @staticmethod
    def _parse_item(raw: Any, index: int) -> tuple[OutlineTransferItem | None, list[str]]:
        errors: list[str] = []
        if not isinstance(raw, dict):
            return None, [f"O esboço nº {index} deve ser um objeto"]

        order_index = raw.get("order_index")
        if isinstance(order_index, bool) or not isinstance(order_index, int) or order_index < 1:
            errors.append(f"O esboço nº {index} deve ter order_index inteiro positivo")

        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"O esboço nº {index} não tem um título válido")
        elif len(title.strip()) > 200:
            errors.append(f"O esboço nº {index} tem título com mais de 200 caracteres")

        content = raw.get("content", "")
        if content is None:
            content = ""
        elif not isinstance(content, str):
            errors.append(f"O esboço nº {index} deve ter content do tipo string")

        structure = raw.get("structure")
        if isinstance(structure, (dict, list)):
            structure = json.dumps(structure, ensure_ascii=False)
        elif structure is not None and not isinstance(structure, str):
            errors.append(f"O esboço nº {index} deve ter structure do tipo string, objeto ou null")

        if errors:
            return None, errors
        return (
            OutlineTransferItem(
                order_index=order_index,
                title=title.strip(),
                content=content,
                structure=structure,
            ),
            [],
        )

    @staticmethod
    def _synchronize_structure(
        structure: str | None,
        title: str,
        content: str,
    ) -> str | None:
        """同步 structure 中用于展示和生成上下文的重复字段。"""
        if not structure:
            structure_data: Any = {}
        else:
            try:
                structure_data = json.loads(structure)
            except json.JSONDecodeError:
                # 保留非 JSON 的历史数据，列表接口仍会使用顶层字段正确展示。
                return structure

        if not isinstance(structure_data, dict):
            return structure

        structure_data["title"] = title
        structure_data["summary"] = content
        structure_data["content"] = content
        return json.dumps(structure_data, ensure_ascii=False)

    @classmethod
    async def preview_import(
        cls,
        parsed: ParsedOutlineDocument,
        project: Project,
        mode: OutlineImportMode,
        db: AsyncSession,
    ) -> OutlineImportPreviewResponse:
        errors = list(parsed.errors)
        warnings = list(parsed.warnings)

        if parsed.source_project and parsed.source_project.outline_mode != project.outline_mode:
            warnings.append(
                "O modo de esboço do projeto de origem difere do projeto de destino; a ligação com os capítulos seguirá o modo do projeto de destino"
            )

        result = await db.execute(
            select(Outline).where(Outline.project_id == project.id)
        )
        existing_outlines = result.scalars().all()
        existing_by_order = {outline.order_index: outline for outline in existing_outlines}

        will_create = len(parsed.items)
        will_update = 0
        will_create_chapters = 0

        if mode == "merge":
            will_update = sum(1 for item in parsed.items if item.order_index in existing_by_order)
            will_create = len(parsed.items) - will_update

        if project.outline_mode == "one-to-one" and parsed.items:
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.project_id == project.id)
            )
            chapters = chapter_result.scalars().all()
            chapters_by_number = {chapter.chapter_number: chapter for chapter in chapters}

            if mode == "append":
                will_create_chapters = len(parsed.items)
            else:
                for item in parsed.items:
                    existing_outline = existing_by_order.get(item.order_index)
                    chapter = chapters_by_number.get(item.order_index)
                    if existing_outline is None and chapter is not None:
                        errors.append(
                            f"A ordem {item.order_index} já tem capítulo mas não tem esboço correspondente; não é possível mesclar por ordem"
                        )
                    elif chapter is None:
                        will_create_chapters += 1

        if mode == "append" and parsed.items:
            warnings.append("O modo de anexar preserva a ordem relativa do arquivo e renumera a partir do final atual")

        return OutlineImportPreviewResponse(
            valid=not errors,
            version=parsed.version,
            source_type=parsed.source_type,
            source_project=parsed.source_project,
            target_outline_mode=project.outline_mode,
            mode=mode,
            statistics=OutlineImportStatistics(
                total=len(parsed.items),
                will_create=will_create,
                will_update=will_update,
                will_create_chapters=will_create_chapters,
            ),
            errors=errors,
            warnings=warnings,
        )

    @classmethod
    async def import_outlines(
        cls,
        parsed: ParsedOutlineDocument,
        project: Project,
        mode: OutlineImportMode,
        db: AsyncSession,
    ) -> OutlineImportResult:
        preview = await cls.preview_import(parsed, project, mode, db)
        if not preview.valid:
            raise ValueError("; ".join(preview.errors))

        details: list[OutlineImportDetail] = []
        imported = 0
        updated = 0
        created_chapters = 0

        try:
            outline_result = await db.execute(
                select(Outline).where(Outline.project_id == project.id)
            )
            existing_outlines = outline_result.scalars().all()
            existing_by_order = {outline.order_index: outline for outline in existing_outlines}

            chapter_result = await db.execute(
                select(Chapter).where(Chapter.project_id == project.id)
            )
            chapters = chapter_result.scalars().all()
            chapters_by_number = {chapter.chapter_number: chapter for chapter in chapters}

            if mode == "append":
                max_outline_order = max(
                    (order for order in existing_by_order if isinstance(order, int)),
                    default=0,
                )
                max_chapter_order = max(chapters_by_number, default=0) if project.outline_mode == "one-to-one" else 0
                next_order = max(max_outline_order, max_chapter_order) + 1

                for offset, item in enumerate(parsed.items):
                    target_order = next_order + offset
                    synchronized_structure = cls._synchronize_structure(
                        item.structure,
                        item.title,
                        item.content,
                    )
                    outline = Outline(
                        project_id=project.id,
                        title=item.title,
                        content=item.content,
                        structure=synchronized_structure,
                        order_index=target_order,
                    )
                    db.add(outline)
                    await db.flush()

                    if project.outline_mode == "one-to-one":
                        db.add(cls._new_chapter(project.id, outline, target_order))
                        created_chapters += 1

                    imported += 1
                    details.append(
                        OutlineImportDetail(
                            source_order_index=item.order_index,
                            target_order_index=target_order,
                            title=item.title,
                            action="created",
                        )
                    )
            else:
                for item in parsed.items:
                    outline = existing_by_order.get(item.order_index)
                    action = "updated"
                    synchronized_structure = cls._synchronize_structure(
                        item.structure,
                        item.title,
                        item.content,
                    )
                    if outline is None:
                        outline = Outline(
                            project_id=project.id,
                            title=item.title,
                            content=item.content,
                            structure=synchronized_structure,
                            order_index=item.order_index,
                        )
                        db.add(outline)
                        await db.flush()
                        existing_by_order[item.order_index] = outline
                        imported += 1
                        action = "created"
                    else:
                        outline.title = item.title
                        outline.content = item.content
                        outline.structure = synchronized_structure
                        updated += 1

                    if project.outline_mode == "one-to-one":
                        chapter = chapters_by_number.get(item.order_index)
                        if chapter is None:
                            chapter = cls._new_chapter(project.id, outline, item.order_index)
                            db.add(chapter)
                            chapters_by_number[item.order_index] = chapter
                            created_chapters += 1
                        else:
                            chapter.outline_id = outline.id
                            chapter.title = item.title
                            chapter.summary = item.content

                    details.append(
                        OutlineImportDetail(
                            source_order_index=item.order_index,
                            target_order_index=item.order_index,
                            title=item.title,
                            action=action,
                        )
                    )

            await db.commit()
        except Exception:
            await db.rollback()
            raise

        return OutlineImportResult(
            success=True,
            message=f"Importação concluída: {imported} adicionados, {updated} atualizados",
            mode=mode,
            imported=imported,
            updated=updated,
            created_chapters=created_chapters,
            details=details,
            warnings=preview.warnings,
        )

    @staticmethod
    def _new_chapter(project_id: str, outline: Outline, chapter_number: int) -> Chapter:
        return Chapter(
            project_id=project_id,
            chapter_number=chapter_number,
            title=outline.title,
            content="",
            summary=outline.content,
            word_count=0,
            status="pending",
            outline_id=outline.id,
            sub_index=1,
        )
