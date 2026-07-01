"""Transcript service for academic history snapshots and live previews."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import io
from pathlib import Path
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError, ValidationError
from app.models.erp import AcademicSnapshot, AcademicYear, Program
from app.models.iam import User
from app.models.school import School
from app.services.content.academic_snapshot_service import AcademicSnapshotService
from app.services.lms.program_service import ProgramService

try:  # pragma: no cover - optional runtime dependency
    from weasyprint import HTML
except Exception:  # pragma: no cover - handled at runtime
    HTML = None

try:  # pragma: no cover - optional fallback dependency
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - handled at runtime
    A4 = None
    canvas = None

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_datetime(value: Any) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            return value
    return str(value)


_jinja_env.globals.update(
    fmt_datetime=_format_datetime,
)


class TranscriptService:
    """Build transcript payloads from frozen snapshots or live preview data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.snapshot_service = AcademicSnapshotService(db)
        self.program_service = ProgramService(db)

    async def get_snapshot_transcript(
        self,
        *,
        snapshot_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        snapshot = await self._get_snapshot(snapshot_id)
        if snapshot is None:
            raise NotFoundError("Snapshot not found", error_code="ERR-ERP-404")
        verify_school_boundary(snapshot.school_id, auth)
        await self.program_service._authorize_student_read(
            student_id=snapshot.student_id,
            auth=auth,
        )
        return await self._transcript_from_snapshot(snapshot=snapshot, auth=auth)

    async def render_snapshot_transcript_html(
        self,
        *,
        snapshot_id: uuid.UUID,
        auth: AuthContext,
        lang: str = "fr",
    ) -> str:
        payload = await self.get_snapshot_transcript(
            snapshot_id=snapshot_id,
            auth=auth,
        )
        return self._render_html(payload=payload, lang=lang)

    async def download_snapshot_transcript_pdf(
        self,
        *,
        snapshot_id: uuid.UUID,
        auth: AuthContext,
        lang: str = "fr",
    ) -> bytes:
        html = await self.render_snapshot_transcript_html(
            snapshot_id=snapshot_id,
            auth=auth,
            lang=lang,
        )
        return self._render_pdf_bytes(html)

    async def get_student_transcript(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        mode: str,
        auth: AuthContext,
    ) -> dict[str, Any]:
        normalized_mode = (mode or "preview").strip().lower()
        if normalized_mode not in {"preview", "snapshot"}:
            raise ValidationError(
                "Invalid transcript mode",
                error_code="ERR-VAL-422",
                details={"allowed": ["preview", "snapshot"]},
            )

        await self.program_service._authorize_student_read(
            student_id=student_id,
            auth=auth,
        )
        student = await self._get_student(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student.school_id, auth)

        academic_year = await self._get_academic_year(academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-ERP-404")
        verify_school_boundary(academic_year.school_id, auth)

        if normalized_mode == "snapshot":
            snapshot = await self._get_latest_snapshot(
                student_id=student_id,
                academic_year_id=academic_year_id,
                school_id=auth.school_id,
            )
            if snapshot is None:
                raise NotFoundError(
                    "Transcript snapshot not found",
                    error_code="ERR-ERP-404",
                )
            return await self._transcript_from_snapshot(snapshot=snapshot, auth=auth)

        blob = await self.snapshot_service._build_blob(
            student=student,
            academic_year=academic_year,
            auth=auth,
        )
        school = await self._get_school(auth.school_id)
        return await self._compose_transcript(
            blob=blob,
            school=school,
            auth=auth,
            source={
                "mode": "preview",
                "generated_at": _utc_now().isoformat(),
            },
        )

    async def render_student_transcript_html(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        mode: str,
        auth: AuthContext,
        lang: str = "fr",
    ) -> str:
        payload = await self.get_student_transcript(
            student_id=student_id,
            academic_year_id=academic_year_id,
            mode=mode,
            auth=auth,
        )
        return self._render_html(payload=payload, lang=lang)

    async def download_student_transcript_pdf(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        mode: str,
        auth: AuthContext,
        lang: str = "fr",
    ) -> bytes:
        html = await self.render_student_transcript_html(
            student_id=student_id,
            academic_year_id=academic_year_id,
            mode=mode,
            auth=auth,
            lang=lang,
        )
        return self._render_pdf_bytes(html)

    async def _transcript_from_snapshot(
        self,
        *,
        snapshot: AcademicSnapshot,
        auth: AuthContext,
    ) -> dict[str, Any]:
        school = await self._get_school(snapshot.school_id)
        return await self._compose_transcript(
            blob=snapshot.snapshot_data or {},
            school=school,
            auth=auth,
            source={
                "mode": "snapshot",
                "snapshot_id": str(snapshot.id),
                "snapshot_kind": snapshot.snapshot_kind,
                "taken_at": snapshot.taken_at.isoformat(),
                "taken_by": (
                    str(snapshot.taken_by) if snapshot.taken_by is not None else None
                ),
                "generated_at": _utc_now().isoformat(),
            },
        )

    async def _compose_transcript(
        self,
        *,
        blob: dict[str, Any],
        school: School | None,
        auth: AuthContext,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        enrollments = list(blob.get("enrollments") or [])
        program_ids = {
            uuid.UUID(program["id"])
            for item in enrollments
            for program in [item.get("program")]
            if isinstance(program, dict) and program.get("id")
        }

        return {
            "student": blob.get("student") or {},
            "school": self._school_payload(school, auth.school_id),
            "academic_year": blob.get("academic_year") or {},
            "source": {
                **source,
                "resolved_at": blob.get("resolved_at"),
                "schema_version": blob.get("schema_version"),
            },
            "enrollments": enrollments,
            "program_events": list(blob.get("program_events") or []),
            "grades_summary": list(blob.get("grades_summary") or []),
            "attendance_summary": dict(blob.get("attendance_summary") or {}),
            "equivalence_resolutions": await self._build_equivalence_resolutions(
                auth=auth,
                program_ids=program_ids,
            ),
        }

    async def _build_equivalence_resolutions(
        self,
        *,
        auth: AuthContext,
        program_ids: set[uuid.UUID],
    ) -> list[dict[str, Any]]:
        if not program_ids:
            return []

        items: list[dict[str, Any]] = []
        for program_id in sorted(program_ids, key=str):
            source_program = await self.program_service._fetch_program(program_id)
            resolved_ids = await self.program_service.equivalent_program_ids(
                auth=auth,
                program_id=program_id,
            )
            result = await self.db.execute(
                select(Program)
                .where(Program.id.in_(resolved_ids))
                .order_by(Program.code.asc())
            )
            resolved_programs = result.scalars().all()
            items.append(
                {
                    "program": self._program_payload(
                        source_program, fallback_id=program_id
                    ),
                    "resolved_program_ids": [
                        str(item.id) for item in resolved_programs
                    ],
                    "resolved_programs": [
                        self._program_payload(item, fallback_id=item.id)
                        for item in resolved_programs
                    ],
                }
            )
        return items

    async def _get_snapshot(self, snapshot_id: uuid.UUID) -> AcademicSnapshot | None:
        result = await self.db.execute(
            select(AcademicSnapshot).where(AcademicSnapshot.id == snapshot_id)
        )
        return result.scalar_one_or_none()

    async def _get_latest_snapshot(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> AcademicSnapshot | None:
        result = await self.db.execute(
            select(AcademicSnapshot)
            .where(
                AcademicSnapshot.school_id == school_id,
                AcademicSnapshot.student_id == student_id,
                AcademicSnapshot.academic_year_id == academic_year_id,
            )
            .order_by(desc(AcademicSnapshot.taken_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_student(self, student_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == student_id))
        return result.scalar_one_or_none()

    async def _get_academic_year(
        self, academic_year_id: uuid.UUID
    ) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def _get_school(self, school_id: uuid.UUID) -> School | None:
        result = await self.db.execute(select(School).where(School.id == school_id))
        return result.scalar_one_or_none()

    def _school_payload(
        self,
        school: School | None,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        if school is None:
            return {"id": str(school_id), "name": None, "code": None}
        return {
            "id": str(school.id),
            "name": school.name,
            "code": school.code,
            "city": school.city,
            "region": school.region,
        }

    def _program_payload(
        self,
        program: Program | None,
        *,
        fallback_id: uuid.UUID,
    ) -> dict[str, Any]:
        if program is None:
            return {
                "id": str(fallback_id),
                "code": None,
                "name": None,
                "version_label": None,
            }
        return {
            "id": str(program.id),
            "code": program.code,
            "name": program.name,
            "version_label": program.version_label,
        }

    def _render_html(self, *, payload: dict[str, Any], lang: str) -> str:
        normalized_lang = lang if lang in {"fr", "en", "ar"} else "fr"
        template = _jinja_env.get_template("reports/transcript.html")
        return template.render(
            lang=normalized_lang,
            is_rtl=normalized_lang == "ar",
            report_title=self._report_title(normalized_lang),
            period=self._academic_year_label(payload.get("academic_year") or {}),
            generated_at=payload.get("source", {}).get("generated_at"),
            transcript=payload,
            source_label=self._source_label(
                normalized_lang,
                payload.get("source", {}).get("mode"),
            ),
        )

    def _report_title(self, lang: str) -> str:
        if lang == "ar":
            return "كشف المسار الدراسي"
        if lang == "en":
            return "Academic Transcript"
        return "Releve academique"

    def _source_label(self, lang: str, mode: object) -> str:
        is_snapshot = str(mode or "").lower() == "snapshot"
        if lang == "ar":
            return "نسخة مجمدة" if is_snapshot else "معاينة مباشرة"
        if lang == "en":
            return "Frozen snapshot" if is_snapshot else "Live preview"
        return "Snapshot fige" if is_snapshot else "Apercu direct"

    def _academic_year_label(self, academic_year: dict[str, Any]) -> str:
        label = academic_year.get("label")
        if label:
            return str(label)
        start = academic_year.get("date_start")
        end = academic_year.get("date_end")
        if start and end:
            return f"{start} -> {end}"
        return "—"

    def _render_pdf_bytes(self, html: str) -> bytes:
        if HTML is not None:  # pragma: no branch
            return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()

        if canvas is None or A4 is None:  # pragma: no cover
            raise RuntimeError(
                "No PDF renderer available. Install weasyprint or reportlab."
            )

        plain_text = re.sub(r"<[^>]+>", "", html)
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _width, height = A4
        y = height - 40
        for line in plain_text.splitlines():
            text = line.strip()
            if not text:
                continue
            pdf.drawString(40, y, text[:120])
            y -= 14
            if y < 40:
                pdf.showPage()
                y = height - 40
        pdf.save()
        return buffer.getvalue()
