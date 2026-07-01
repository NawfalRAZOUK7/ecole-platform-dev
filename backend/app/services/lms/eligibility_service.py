"""Eligibility rules service (Phase 3.4 / G50d).

Built-in condition types:

  - ``has_completed_program``
      condition_params = {"program_id": "<uuid>"}
      Passes if the student has any enrollment (status != "dropped") in
      the given program.

  - ``min_attendance_rate``
      condition_params = {"min_rate": <float 0..1>, "academic_year_id": "<uuid>"}
      Passes if the student's attendance rate (present / total) for the
      year is >= min_rate.

  - ``min_grade_average``
      condition_params = {"min_average": <float>, "academic_year_id": "<uuid>"}
      Passes if the student's average grade for the year is >= min_average.

This is intentionally a small fixed catalog — see the design doc note:
"start as Python service code; promote to a rules table only when ≥10
rules need non-engineer editability." A row in eligibility_rules names
ONE of these condition_types and supplies its params.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.models.erp import (
    AttendanceRecord,
    AttendanceSession,
    EligibilityRule,
    Enrollment,
    Program,
)
from app.models.iam import User
from app.models.lms import Assignment, Course, Grade, Submission
from app.services.platform.audit import AuditService

KNOWN_CONDITION_TYPES = {
    "has_completed_program",
    "min_attendance_rate",
    "min_grade_average",
}


class EligibilityService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def _to_response(self, rule: EligibilityRule) -> dict:
        return {
            "id": str(rule.id),
            "school_id": str(rule.school_id),
            "kind": rule.kind,
            "target_program_id": str(rule.target_program_id),
            "condition_type": rule.condition_type,
            "condition_params": rule.condition_params,
            "message_key": rule.message_key,
            "is_active": rule.is_active,
            "created_at": rule.created_at.isoformat(),
            "updated_at": (
                rule.updated_at.isoformat() if rule.updated_at is not None else None
            ),
        }

    async def list_rules(
        self,
        *,
        auth: AuthContext,
        kind: str | None = None,
        target_program_id: uuid.UUID | None = None,
        active_only: bool = True,
    ) -> list[dict]:
        stmt = select(EligibilityRule).where(
            EligibilityRule.school_id == auth.school_id
        )
        if kind is not None:
            stmt = stmt.where(EligibilityRule.kind == kind)
        if target_program_id is not None:
            stmt = stmt.where(EligibilityRule.target_program_id == target_program_id)
        if active_only:
            stmt = stmt.where(EligibilityRule.is_active.is_(True))
        stmt = stmt.order_by(desc(EligibilityRule.created_at))
        result = await self.db.execute(stmt)
        return [self._to_response(r) for r in result.scalars().all()]

    async def create_rule(
        self,
        *,
        kind: str,
        target_program_id: uuid.UUID,
        condition_type: str,
        condition_params: dict,
        message_key: str,
        is_active: bool,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if condition_type not in KNOWN_CONDITION_TYPES:
            raise ValidationError(
                "Unknown condition_type",
                error_code="ERR-VAL-422",
                details={"allowed": sorted(KNOWN_CONDITION_TYPES)},
            )

        program_result = await self.db.execute(
            select(Program).where(Program.id == target_program_id)
        )
        program = program_result.scalar_one_or_none()
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            rule = EligibilityRule(
                school_id=auth.school_id,
                kind=kind,
                target_program_id=target_program_id,
                condition_type=condition_type,
                condition_params=condition_params,
                message_key=message_key,
                is_active=is_active,
            )
            uow.session.add(rule)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ELIGIBILITY_RULE_CREATED",
                outcome="success",
                target_type="eligibility_rule",
                target_id=rule.id,
                entity_after={
                    "kind": kind,
                    "target_program_id": str(target_program_id),
                    "condition_type": condition_type,
                    "is_active": is_active,
                },
                ip_address=ip_address,
            )
            await uow.commit()
        return self._to_response(rule)

    async def delete_rule(
        self,
        *,
        rule_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> None:
        result = await self.db.execute(
            select(EligibilityRule).where(EligibilityRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise NotFoundError("Rule not found", error_code="ERR-ERP-404")
        verify_school_boundary(rule.school_id, auth)

        async with UnitOfWork(self.db) as uow:
            attached = await uow.session.get(EligibilityRule, rule.id)
            if attached is None:
                raise NotFoundError("Rule not found", error_code="ERR-ERP-404")
            await uow.session.delete(attached)
            await uow.session.flush()

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ELIGIBILITY_RULE_DELETED",
                outcome="success",
                target_type="eligibility_rule",
                target_id=rule.id,
                entity_before={
                    "kind": rule.kind,
                    "target_program_id": str(rule.target_program_id),
                    "condition_type": rule.condition_type,
                },
                ip_address=ip_address,
            )
            await uow.commit()

    # ------------------------------------------------------------------
    # Evaluator
    # ------------------------------------------------------------------
    async def check_eligibility(
        self,
        *,
        student_id: uuid.UUID,
        target_program_id: uuid.UUID,
        kind: str,
        auth: AuthContext,
    ) -> dict:
        # Validate student + program belong to the auth school.
        student_result = await self.db.execute(
            select(User).where(User.id == student_id)
        )
        student = student_result.scalar_one_or_none()
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student.school_id, auth)

        program_result = await self.db.execute(
            select(Program).where(Program.id == target_program_id)
        )
        program = program_result.scalar_one_or_none()
        if program is None:
            raise NotFoundError("Program not found", error_code="ERR-ERP-404")
        verify_school_boundary(program.school_id, auth)

        rules_result = await self.db.execute(
            select(EligibilityRule).where(
                EligibilityRule.school_id == auth.school_id,
                EligibilityRule.kind == kind,
                EligibilityRule.target_program_id == target_program_id,
                EligibilityRule.is_active.is_(True),
            )
        )
        rules = list(rules_result.scalars().all())

        results = []
        for rule in rules:
            try:
                passed, detail = await self._evaluate(
                    student_id=student_id,
                    rule=rule,
                )
            except Exception as exc:  # noqa: BLE001 — never crash the check
                passed, detail = False, f"evaluator error: {exc}"
            results.append(
                {
                    "rule_id": str(rule.id),
                    "condition_type": rule.condition_type,
                    "message_key": rule.message_key,
                    "passed": passed,
                    "detail": detail,
                }
            )

        return {
            "student_id": str(student_id),
            "target_program_id": str(target_program_id),
            "kind": kind,
            "eligible": all(r["passed"] for r in results),
            "rules": results,
        }

    async def _evaluate(
        self,
        *,
        student_id: uuid.UUID,
        rule: EligibilityRule,
    ) -> tuple[bool, str | None]:
        ct = rule.condition_type
        params: dict[str, Any] = rule.condition_params or {}

        if ct == "has_completed_program":
            program_id = params.get("program_id")
            if not program_id:
                return False, "missing program_id"
            stmt = select(Enrollment.id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == rule.school_id,
                Enrollment.program_id == program_id,
                Enrollment.status != "dropped",
            )
            row = (await self.db.execute(stmt)).first()
            return (row is not None), None

        if ct == "min_attendance_rate":
            min_rate = float(params.get("min_rate", 0.0))
            academic_year_id = params.get("academic_year_id")
            stmt = (
                select(
                    func.count(AttendanceRecord.id).label("total"),
                    func.count()
                    .filter(AttendanceRecord.status == "present")
                    .label("present"),
                )
                .select_from(AttendanceRecord)
                .join(
                    AttendanceSession,
                    AttendanceSession.id == AttendanceRecord.attendance_session_id,
                )
                .where(
                    AttendanceRecord.school_id == rule.school_id,
                    AttendanceRecord.student_id == student_id,
                )
            )
            if academic_year_id:
                # Constrain via period→academic_year. We resolve the AY
                # window once and filter session_date by it — this avoids
                # an extra join while giving correct semantics.
                from app.models.erp import AcademicYear as _AY

                ay_result = await self.db.execute(
                    select(_AY.date_start, _AY.date_end).where(
                        _AY.id == academic_year_id,
                        _AY.school_id == rule.school_id,
                    )
                )
                ay_row = ay_result.first()
                if ay_row is None:
                    return False, "academic_year not found in this school"
                stmt = stmt.where(
                    AttendanceSession.session_date >= ay_row.date_start,
                    AttendanceSession.session_date <= ay_row.date_end,
                )
            result = (await self.db.execute(stmt)).first()
            total = int(result.total or 0)
            present = int(result.present or 0)
            rate = (present / total) if total else 0.0
            scope = f", year={str(academic_year_id)[:8]}…" if academic_year_id else ""
            return (
                rate >= min_rate,
                f"rate={rate:.2f} (required >= {min_rate:.2f}, n={total}{scope})",
            )

        if ct == "min_grade_average":
            min_average = float(params.get("min_average", 0.0))
            stmt = (
                select(func.avg(Grade.score))
                .select_from(Grade)
                .join(Submission, Submission.id == Grade.submission_id)
                .join(Assignment, Assignment.id == Submission.assignment_id)
                .join(Course, Course.id == Assignment.course_id)
                .where(
                    Course.school_id == rule.school_id,
                    Submission.student_id == student_id,
                )
            )
            avg_score = (await self.db.execute(stmt)).scalar_one_or_none()
            if avg_score is None:
                return False, "no grades"
            ok = float(avg_score) >= min_average
            return ok, f"avg={float(avg_score):.2f} (required >= {min_average:.2f})"

        return False, f"unknown condition_type: {ct}"
