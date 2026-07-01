"""Cross-cutting platform services (audit, security signals)."""

from app.services.platform.audit import AuditService

__all__ = ["AuditService"]
