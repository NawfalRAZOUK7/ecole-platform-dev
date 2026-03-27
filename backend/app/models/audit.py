"""Audit domain models — Audit logs.

Reference: Pack C4 (Data Model — Audit section), D6 (Security Enforcement), Sprint 1 story S-019.
Migration group: G6-Audit (depends on G1-IAM for user FK).
"""

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class AuditLog(TimestampMixin, Base):
    """Append-only audit log for security-relevant events.

    INV-AUDIT-ACTOR: actor_id is null only for SYS-originated events (enforced in app layer).
    entity_before/entity_after use JSONB for flexible schema.
    Retention: 12-24 months (managed by archival job, not migration).
    """

    __tablename__ = "audit_logs"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    entity_before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    entity_after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_correlation_id", "correlation_id"),
        Index("idx_audit_logs_school_created", "school_id", "created_at"),
        Index("idx_audit_logs_actor_action", "actor_id", "action_type"),
    )
