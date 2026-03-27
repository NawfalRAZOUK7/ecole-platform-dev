"""Phase 14 CSV/XLSX data export service."""

from __future__ import annotations

import csv
import io
import json
import tempfile
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.reporting import DataExport
from app.repositories.reports import ReportsRepository
from app.schemas.reports import ExportFilters

try:  # pragma: no cover - optional runtime dependency
    from openpyxl import Workbook
except Exception:  # pragma: no cover - handled at runtime
    Workbook = None


SUPPORTED_EXPORT_ENTITIES = {"students", "grades", "attendance", "invoices", "payments"}
MAX_EXPORT_ROWS = 10_000
EXPORT_BATCH_SIZE = 500


def _serialize_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


class DataExportService:
    """Streaming CSV and write-only XLSX exports."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ReportsRepository(db)

    def parse_filters(self, filters_json: str | None) -> dict[str, Any]:
        if not filters_json:
            return {}
        try:
            parsed = json.loads(filters_json)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                "filters must be valid JSON",
                error_code="ERR-EXPORT-422",
            ) from exc
        validated = ExportFilters.model_validate(parsed)
        return validated.model_dump(mode="json", exclude_none=True)

    async def prepare_export(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        entity: str,
        filters: dict[str, Any],
        export_format: str,
    ) -> DataExport:
        if entity not in SUPPORTED_EXPORT_ENTITIES:
            raise ValidationError(
                "Unsupported export entity",
                error_code="ERR-EXPORT-422",
            )
        row_count = await self.repo.count_export_rows(
            school_id=school_id,
            entity=entity,
            filters=filters,
        )
        if row_count > MAX_EXPORT_ROWS:
            raise ValidationError(
                f"Export exceeds the maximum size of {MAX_EXPORT_ROWS} rows",
                error_code="ERR-EXPORT-413",
            )
        export_log = DataExport(
            school_id=school_id,
            requester_id=requester_id,
            entity=entity,
            filters=filters,
            format=export_format,
            row_count=row_count,
        )
        await self.repo.create_export_log(export_log)
        return export_log

    async def stream_csv(
        self,
        *,
        school_id: uuid.UUID,
        entity: str,
        filters: dict[str, Any],
    ) -> AsyncIterator[str]:
        first_batch = await self.repo.fetch_export_rows(
            school_id=school_id,
            entity=entity,
            filters=filters,
            offset=0,
            limit=EXPORT_BATCH_SIZE,
        )
        if not first_batch:
            yield ""
            return

        fieldnames = list(first_batch[0].keys())
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        offset = 0
        batch = first_batch
        while batch:
            for row in batch:
                writer.writerow(
                    {key: _serialize_value(value) for key, value in row.items()}
                )
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
            offset += len(batch)
            batch = await self.repo.fetch_export_rows(
                school_id=school_id,
                entity=entity,
                filters=filters,
                offset=offset,
                limit=EXPORT_BATCH_SIZE,
            )

    async def build_xlsx(
        self,
        *,
        school_id: uuid.UUID,
        entity: str,
        filters: dict[str, Any],
    ) -> Path:
        if Workbook is None:  # pragma: no cover
            raise RuntimeError("openpyxl is not installed")

        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet(title=entity[:31])
        offset = 0
        header_written = False

        while True:
            batch = await self.repo.fetch_export_rows(
                school_id=school_id,
                entity=entity,
                filters=filters,
                offset=offset,
                limit=EXPORT_BATCH_SIZE,
            )
            if not batch:
                break

            if not header_written:
                sheet.append(list(batch[0].keys()))
                header_written = True

            for row in batch:
                sheet.append([_serialize_value(value) for value in row.values()])
            offset += len(batch)

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".xlsx",
            prefix=f"ecole_{entity}_",
        )
        temp_file.close()
        workbook.save(temp_file.name)
        return Path(temp_file.name)
