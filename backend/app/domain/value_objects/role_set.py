"""Type-safe role set with validation."""

from __future__ import annotations

from dataclasses import dataclass

VALID_ROLES = {"STD", "PAR", "TCH", "ADM", "DIR", "SYS", "CONTENT_MGR", "SUP"}

ROLE_COMPATIBILITY = {
    # Roles that can coexist on the same user
    "TCH": {"PAR", "CONTENT_MGR"},
    "ADM": {"DIR"},
    "DIR": {"ADM"},
    "PAR": {"TCH"},
    "CONTENT_MGR": {"TCH"},
}


@dataclass(frozen=True, slots=True)
class RoleSet:
    """Immutable set of validated roles for a user."""

    roles: frozenset[str]

    def __post_init__(self) -> None:
        invalid = self.roles - VALID_ROLES
        if invalid:
            raise ValueError(f"Invalid roles: {invalid}")

    def has(self, role: str) -> bool:
        return role in self.roles

    def has_any(self, *roles: str) -> bool:
        return bool(self.roles & set(roles))

    @property
    def is_staff(self) -> bool:
        return self.has_any("ADM", "DIR", "SYS", "SUP")

    @property
    def is_educator(self) -> bool:
        return self.has_any("TCH", "CONTENT_MGR")

    @property
    def primary_role(self) -> str:
        """Highest-priority role for display purposes."""
        priority = ["SUP", "SYS", "DIR", "ADM", "CONTENT_MGR", "TCH", "PAR", "STD"]
        for role in priority:
            if role in self.roles:
                return role
        return "STD"
