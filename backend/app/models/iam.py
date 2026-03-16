"""IAM domain models — Users, Memberships, Sessions, Invitations, Recovery, Parent-Child Links.

Reference: Pack C4 (Data Model — IAM section), Sprint 1 stories S-014, S-021.
Phase 1A: parent_child_links table for explicit parent-child relationships.
Migration group: G1-IAM (no dependencies).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class RoleCode(str, enum.Enum):
    ADM = "ADM"  # School administrator
    DIR = "DIR"  # Director / principal
    TCH = "TCH"  # Teacher
    PAR = "PAR"  # Parent
    STD = "STD"  # Student
    SUP = "SUP"  # Super-admin (platform ops)
    SYS = "SYS"  # System account


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RecoveryStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    RESET = "reset"


class LinkStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class User(TimestampMixin, Base):
    """Platform user — one row per person across schools.

    school_id is NOT a FK (schools managed externally per DEC-001).
    email uniqueness is scoped per school via partial unique index.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserStatus.ACTIVE.value
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # INV-IAM-EMAIL: unique email per school
        UniqueConstraint("email", "school_id", name="uq_users_email_school"),
        Index("idx_users_school_id", "school_id"),
    )


class Membership(TimestampMixin, Base):
    """Role assignment — links a user to a school with a specific role.

    Partial unique index ensures only one active membership per (user, school, role).
    """

    __tablename__ = "memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    role_code: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MembershipStatus.ACTIVE.value
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memberships")

    __table_args__ = (
        # idx_memberships_user_school_role — unique active membership per role
        Index(
            "uq_memberships_user_school_role_active",
            "user_id",
            "school_id",
            "role_code",
            unique=True,
            postgresql_where="status = 'active'",
        ),
    )


class Session(TimestampMixin, Base):
    """Auth session — tracks JWT refresh sessions with revocation.

    revoke_at IS NULL means the session is still active.
    """

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    revoke_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")

    __table_args__ = (
        # idx_sessions_school_user_active — active sessions per user in school
        Index(
            "idx_sessions_school_user_active",
            "school_id",
            "user_id",
            postgresql_where="revoke_at IS NULL",
        ),
        Index("idx_sessions_correlation_id", "correlation_id"),
    )


class InvitationCode(TimestampMixin, Base):
    """Invitation code — one-time codes for user onboarding.

    code_hash is a bcrypt or SHA-256 hash of the actual code sent to the user.
    """

    __tablename__ = "invitation_codes"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    issuer_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role_target: Mapped[str] = mapped_column(String(10), nullable=False)
    consumed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    issuer: Mapped["User | None"] = relationship(
        foreign_keys=[issuer_user_id]
    )
    consumer: Mapped["User | None"] = relationship(
        foreign_keys=[consumed_by]
    )

    __table_args__ = (
        Index("idx_invitation_codes_hash", "code_hash", unique=True),
        Index("idx_invitation_codes_school_expires", "school_id", "expires_at"),
    )


class AccountRecoveryRequest(TimestampMixin, Base):
    """Account recovery — password reset flow with OTP and attempt tracking."""

    __tablename__ = "account_recovery_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RecoveryStatus.PENDING.value
    )
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    lock_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_recovery_user_status", "user_id", "status"),
    )


class ParentChildLink(TimestampMixin, Base):
    """Explicit parent-child relationship for ABAC ownership guard.

    Phase 1A: replaces the enrollment-based derivation in get_parent_child_ids().
    A parent (PAR role) is linked to one or more students (STD role) in a school.
    linked_by tracks who created the link (ADM or the parent themselves).
    """

    __tablename__ = "parent_child_links"

    parent_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    child_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=LinkStatus.ACTIVE.value
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    linked_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    parent: Mapped["User"] = relationship(foreign_keys=[parent_user_id])
    child: Mapped["User"] = relationship(foreign_keys=[child_user_id])
    linker: Mapped["User | None"] = relationship(foreign_keys=[linked_by])

    __table_args__ = (
        UniqueConstraint(
            "parent_user_id", "child_user_id", "school_id",
            name="uq_parent_child_links_parent_child_school",
        ),
        Index("idx_parent_child_links_parent", "parent_user_id", "school_id"),
        Index("idx_parent_child_links_child", "child_user_id"),
    )
