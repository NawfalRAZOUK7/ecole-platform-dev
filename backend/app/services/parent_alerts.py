"""Parent alerts service — rule-based triggers for parent notifications.

Phase B2: Système d'alertes parent (non-AI).
Rules:
  1. Grade drop: latest grade < 10/20 → notify parent
  2. Inactivity: no login session for 3+ days → notify parent
  3. Unjustified absence: attendance_records with status='absent' and no justification → notify parent

Runs as an ARQ cron job every 6 hours. Uses the existing notification_hub
to deliver alerts via in-app + push + email.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, desc, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.erp import AbsenceJustification, AttendanceRecord
from app.models.iam import ParentChildLink, Session, User
from app.models.lms import Grade, Submission
from app.services.notification_hub import NotificationHubService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Alert thresholds (configurable later)
# ---------------------------------------------------------------------------
GRADE_DROP_THRESHOLD = 10.0  # /20
INACTIVITY_DAYS = 3
ALERT_CATEGORY = "academic"
ALERT_PRIORITY = "high"


class ParentAlertService:
    """Rule-based parent alert engine."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notification_hub = NotificationHubService(db)

    # ------------------------------------------------------------------
    # Main entry point — run all checks
    # ------------------------------------------------------------------
    async def run_all_checks(self) -> dict[str, int]:
        """Execute all alert rules and return counts of alerts sent."""
        counts = {
            "grade_drop": 0,
            "inactivity": 0,
            "unjustified_absence": 0,
        }

        # Get all active parent-child links
        links = await self._get_active_links()
        if not links:
            logger.info("No active parent-child links found, skipping alerts.")
            return counts

        for link in links:
            try:
                counts["grade_drop"] += await self._check_grade_drop(link)
                counts["inactivity"] += await self._check_inactivity(link)
                counts["unjustified_absence"] += await self._check_unjustified_absence(
                    link
                )
            except Exception:
                logger.exception(
                    "Error checking alerts for parent=%s child=%s",
                    link["parent_id"],
                    link["child_id"],
                )

        logger.info("Parent alerts completed: %s", counts)
        return counts

    # ------------------------------------------------------------------
    # Load all active parent-child links
    # ------------------------------------------------------------------
    async def _get_active_links(self) -> list[dict[str, uuid.UUID]]:
        result = await self.db.execute(
            select(
                ParentChildLink.parent_user_id,
                ParentChildLink.child_user_id,
                ParentChildLink.school_id,
            ).where(ParentChildLink.status == "active")
        )
        return [
            {
                "parent_id": row.parent_user_id,
                "child_id": row.child_user_id,
                "school_id": row.school_id,
            }
            for row in result.all()
        ]

    # ------------------------------------------------------------------
    # Rule 1: Grade drop — latest grade < threshold
    # ------------------------------------------------------------------
    async def _check_grade_drop(self, link: dict[str, uuid.UUID]) -> int:
        """Check if child's most recent grade is below the threshold."""
        child_id = link["child_id"]

        # Get the most recent published grade for this student
        latest_grade_q = (
            select(Grade.score, Grade.created_at)
            .join(Submission, Grade.submission_id == Submission.id)
            .where(
                Submission.student_id == child_id,
                Grade.published_at.isnot(None),
            )
            .order_by(desc(Grade.created_at))
            .limit(1)
        )
        result = await self.db.execute(latest_grade_q)
        row = result.one_or_none()

        if row is None:
            return 0

        score = float(row.score)
        grade_time = row.created_at

        # Only alert for grades in the last 24 hours to avoid re-alerting
        if grade_time and (_utc_now() - grade_time) > timedelta(hours=24):
            return 0

        if score < GRADE_DROP_THRESHOLD:
            # Get child's name for the notification
            child_name = await self._get_user_name(child_id)
            await self.notification_hub.create_single_notification(
                school_id=link["school_id"],
                user_id=link["parent_id"],
                title=f"⚠️ Note faible : {child_name}",
                body=(
                    f"{child_name} a obtenu {score:.1f}/20 dans sa dernière évaluation. "
                    f"N'hésitez pas à le/la soutenir et encourager."
                ),
                category=ALERT_CATEGORY,
                priority=ALERT_PRIORITY,
                action_url=f"/family/review/{child_id}",
                idempotency_key=f"grade-drop:{child_id}:{grade_time.date().isoformat()}",
            )
            return 1

        return 0

    # ------------------------------------------------------------------
    # Rule 2: Inactivity — no login for N days
    # ------------------------------------------------------------------
    async def _check_inactivity(self, link: dict[str, uuid.UUID]) -> int:
        """Check if child has not logged in for INACTIVITY_DAYS."""
        child_id = link["child_id"]
        threshold = _utc_now() - timedelta(days=INACTIVITY_DAYS)

        # Get the most recent session
        latest_session_q = (
            select(Session.created_at)
            .where(Session.user_id == child_id)
            .order_by(desc(Session.created_at))
            .limit(1)
        )
        result = await self.db.execute(latest_session_q)
        row = result.one_or_none()

        if row is None:
            # No sessions at all — this is also inactivity
            last_active_str = "jamais"
        elif row.created_at and row.created_at > threshold:
            return 0  # Active recently
        else:
            last_active_str = (
                row.created_at.strftime("%d/%m/%Y") if row.created_at else "inconnu"
            )

        child_name = await self._get_user_name(child_id)
        today_str = _utc_now().date().isoformat()

        await self.notification_hub.create_single_notification(
            school_id=link["school_id"],
            user_id=link["parent_id"],
            title=f"📵 {child_name} est inactif(ve)",
            body=(
                f"{child_name} ne s'est pas connecté(e) depuis plus de "
                f"{INACTIVITY_DAYS} jours (dernière connexion : {last_active_str}). "
                f"Encouragez-le/la à reprendre ses activités !"
            ),
            category=ALERT_CATEGORY,
            priority="normal",
            action_url=f"/family/review/{child_id}",
            idempotency_key=f"inactivity:{child_id}:{today_str}",
        )
        return 1

    # ------------------------------------------------------------------
    # Rule 3: Unjustified absence
    # ------------------------------------------------------------------
    async def _check_unjustified_absence(self, link: dict[str, uuid.UUID]) -> int:
        """Check for recent unjustified absences in the last 24h."""
        child_id = link["child_id"]
        since = _utc_now() - timedelta(hours=24)

        # Find attendance records marked 'absent' without justification
        # created in the last 24h
        absent_q = (
            select(func.count())
            .select_from(AttendanceRecord)
            .outerjoin(
                AbsenceJustification,
                AttendanceRecord.id == AbsenceJustification.attendance_record_id,
            )
            .where(
                AttendanceRecord.student_id == child_id,
                AttendanceRecord.status == "absent",
                AttendanceRecord.created_at >= since,
                AbsenceJustification.id.is_(None),  # no justification
            )
        )
        result = await self.db.execute(absent_q)
        count = result.scalar_one()

        if count == 0:
            return 0

        child_name = await self._get_user_name(child_id)
        today_str = _utc_now().date().isoformat()

        await self.notification_hub.create_single_notification(
            school_id=link["school_id"],
            user_id=link["parent_id"],
            title=f"🚫 Absence non justifiée : {child_name}",
            body=(
                f"{child_name} a été marqué(e) absent(e) sans justification "
                f"({count} occurrence{'s' if count > 1 else ''} aujourd'hui). "
                f"Veuillez justifier cette absence."
            ),
            category="attendance",
            priority=ALERT_PRIORITY,
            action_url=f"/attendance/justify?studentId={child_id}",
            idempotency_key=f"absence:{child_id}:{today_str}",
        )
        return 1

    # ------------------------------------------------------------------
    # Helper: get user display name
    # ------------------------------------------------------------------
    async def _get_user_name(self, user_id: uuid.UUID) -> str:
        result = await self.db.execute(
            select(User.full_name).where(User.id == user_id)
        )
        name = result.scalar_one_or_none()
        return name or "Élève"
