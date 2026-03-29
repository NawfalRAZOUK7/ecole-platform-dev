"""IAM domain models — Users, Memberships, Sessions, Invitations, Recovery, Parent-Child Links.

Reference: Pack C4 (Data Model — IAM section), Sprint 1 stories S-014, S-021.
Phase 1A: parent_child_links table for explicit parent-child relationships.
Phase 2B: TOTP 2FA columns + email verification on User model.
Migration group: G1-IAM (no dependencies).
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


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
    CONTENT_MGR = "CONTENT_MGR"  # Platform-wide content manager


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


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class RelationshipType(str, enum.Enum):
    FATHER = "father"
    MOTHER = "mother"
    GUARDIAN = "guardian"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class User(TimestampMixin, SchoolScopedMixin, Base):
    """Platform user — one row per person across schools.

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
    # Phase 2B — TOTP two-factor authentication
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    totp_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    backup_codes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase 2B — Email verification
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Session.user_id",
    )
    login_history: Mapped[list["LoginHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="LoginHistory.user_id",
    )

    __table_args__ = (
        # INV-IAM-EMAIL: unique email per school
        UniqueConstraint("email", "school_id", name="uq_users_email_school"),
        Index("idx_users_school_id", "school_id"),
    )

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE.value

    @property
    def has_2fa(self) -> bool:
        return self.totp_secret is not None

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned:
            raise ValueError(f"Invalid email format: {value}")
        return cleaned

    @validates("phone")
    def validate_phone(self, key: str, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().replace(" ", "").replace("-", "")
        if not cleaned.startswith("+"):
            raise ValueError("Phone must start with country code (+)")
        return cleaned

    def __repr__(self) -> str:
        return f"<User id={_short_id(self.id)} email={self.email} status={self.status}>"


class Membership(TimestampMixin, SchoolScopedMixin, Base):
    """Role assignment — links a user to a school with a specific role.

    Partial unique index ensures only one active membership per (user, school, role).
    """

    __tablename__ = "memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_code: Mapped[str] = mapped_column(String(20), nullable=False)
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

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE.value

    def __repr__(self) -> str:
        return (
            f"<Membership id={_short_id(self.id)} user_id={_short_id(self.user_id)} "
            f"role_code={self.role_code}>"
        )


class Session(TimestampMixin, SchoolScopedMixin, Base):
    """Auth session — tracks JWT refresh sessions with revocation.

    revoke_at IS NULL means the session is still active.
    Phase 2A: Added user_agent, ip_address, device_name for session management.
    """

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    revoke_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    # Phase 2A — device fingerprint columns
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    impersonator_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="sessions",
        foreign_keys=[user_id],
    )
    impersonator: Mapped["User | None"] = relationship(foreign_keys=[impersonator_id])

    __table_args__ = (
        # idx_sessions_school_user_active — active sessions per user in school
        Index(
            "idx_sessions_school_user_active",
            "school_id",
            "user_id",
            postgresql_where="revoke_at IS NULL",
        ),
        Index("idx_sessions_correlation_id", "correlation_id"),
        Index("idx_sessions_impersonator_id", "impersonator_id"),
    )

    @property
    def is_expired(self) -> bool:
        expires_at = getattr(self, "expires_at", None)
        return expires_at is not None and expires_at < datetime.now(timezone.utc)

    @property
    def is_impersonated(self) -> bool:
        return self.impersonator_id is not None

    @property
    def is_revoked(self) -> bool:
        revoked_at = getattr(self, "revoke_at", None) or getattr(
            self,
            "revoked_at",
            None,
        )
        return revoked_at is not None

    def __repr__(self) -> str:
        return (
            f"<Session id={_short_id(self.id)} user_id={_short_id(self.user_id)} "
            f"impersonated={self.impersonator_id is not None}>"
        )


class LoginHistory(TimestampMixin, SchoolScopedMixin, Base):
    """Historical record of login attempts and successful device usage."""

    __tablename__ = "login_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failure_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_new_device: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="login_history",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        Index("idx_login_history_user_created", "user_id", "created_at"),
        Index("idx_login_history_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<LoginHistory id={_short_id(self.id)} user_id={_short_id(self.user_id)} "
            f"success={self.success}>"
        )


class InvitationCode(TimestampMixin, SchoolScopedMixin, Base):
    """Invitation code — one-time codes for user onboarding.

    code_hash is a bcrypt or SHA-256 hash of the actual code sent to the user.
    """

    __tablename__ = "invitation_codes"

    issuer_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role_target: Mapped[str] = mapped_column(String(20), nullable=False)
    consumed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Phase 1B — optional pre-linked student for parent invitations
    target_student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    issuer: Mapped["User | None"] = relationship(foreign_keys=[issuer_user_id])
    consumer: Mapped["User | None"] = relationship(foreign_keys=[consumed_by])
    target_student: Mapped["User | None"] = relationship(
        foreign_keys=[target_student_id]
    )

    __table_args__ = (
        Index("idx_invitation_codes_hash", "code_hash", unique=True),
        Index("idx_invitation_codes_school_expires", "school_id", "expires_at"),
    )

    @property
    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(timezone.utc)

    @property
    def is_fully_used(self) -> bool:
        current_uses = getattr(self, "current_uses", None)
        max_uses = getattr(self, "max_uses", None)
        if current_uses is not None and max_uses is not None:
            return current_uses >= max_uses
        return self.consumed_at is not None or self.consumed_by is not None

    def __repr__(self) -> str:
        return (
            f"<InvitationCode id={_short_id(self.id)} role_target={self.role_target} "
            f"consumed={self.consumed_at is not None}>"
        )


class AccountRecoveryRequest(TimestampMixin, SchoolScopedMixin, Base):
    """Account recovery — password reset flow with OTP and attempt tracking."""

    __tablename__ = "account_recovery_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
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

    __table_args__ = (Index("idx_recovery_user_status", "user_id", "status"),)

    @property
    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<AccountRecoveryRequest id={_short_id(self.id)} "
            f"user_id={_short_id(self.user_id)} status={self.status}>"
        )


class ParentChildLink(TimestampMixin, SchoolScopedMixin, Base):
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
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=LinkStatus.ACTIVE.value
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    linked_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    parent: Mapped["User"] = relationship(foreign_keys=[parent_user_id])
    child: Mapped["User"] = relationship(foreign_keys=[child_user_id])
    linker: Mapped["User | None"] = relationship(foreign_keys=[linked_by])

    __table_args__ = (
        UniqueConstraint(
            "parent_user_id",
            "child_user_id",
            "school_id",
            name="uq_parent_child_links_parent_child_school",
        ),
        Index("idx_parent_child_links_parent", "parent_user_id", "school_id"),
        Index("idx_parent_child_links_child", "child_user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ParentChildLink id={_short_id(self.id)} "
            f"parent_id={_short_id(self.parent_user_id)} "
            f"child_id={_short_id(self.child_user_id)}>"
        )


# ---------------------------------------------------------------------------
# Phase 1B — Role-Specific Profile Tables
# ---------------------------------------------------------------------------


class StudentProfile(TimestampMixin, SchoolScopedMixin, Base):
    """Extended profile for students (STD role).

    One-to-one with User. student_number is unique per school.
    """

    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    student_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    class_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guardian_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint(
            "student_number",
            "school_id",
            name="uq_student_profiles_number_school",
        ),
        Index("idx_student_profiles_user", "user_id"),
        Index("idx_student_profiles_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentProfile id={_short_id(self.id)} "
            f"student_number={self.student_number}>"
        )


class ParentProfile(TimestampMixin, SchoolScopedMixin, Base):
    """Extended profile for parents (PAR role).

    One-to-one with User. Stores Moroccan-specific fields (CIN).
    """

    __tablename__ = "parent_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    relationship_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cin_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    profession: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_parent_profiles_user", "user_id"),
        Index("idx_parent_profiles_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ParentProfile id={_short_id(self.id)} "
            f"user_id={_short_id(self.user_id)}>"
        )


class TeacherProfile(TimestampMixin, SchoolScopedMixin, Base):
    """Extended profile for teachers (TCH role).

    One-to-one with User. Stores employment and qualification info.
    """

    __tablename__ = "teacher_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    employee_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_specialty: Mapped[str | None] = mapped_column(String(200), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hire_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_teacher_profiles_user", "user_id"),
        Index("idx_teacher_profiles_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TeacherProfile id={_short_id(self.id)} "
            f"employee_id={self.employee_id}>"
        )


class AdminProfile(TimestampMixin, SchoolScopedMixin, Base):
    """Extended profile for ADM/DIR roles."""

    __tablename__ = "admin_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    management_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    can_approve_budgets: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_admin_profiles_user", "user_id"),
        Index("idx_admin_profiles_school", "school_id"),
    )

    def __repr__(self) -> str:
        return f"<AdminProfile id={_short_id(self.id)} department={self.department}>"


class ContentManagerProfile(TimestampMixin, SchoolScopedMixin, Base):
    """Extended profile for CONTENT_MGR role."""

    __tablename__ = "content_manager_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    specialization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    languages_managed: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_subjects: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_content_manager_profiles_user", "user_id"),
        Index("idx_content_manager_profiles_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContentManagerProfile id={_short_id(self.id)} "
            f"specialization={self.specialization}>"
        )
