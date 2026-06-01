"""Unit tests for app/services/communication/overdue_reminders.py.

All DB/session/enqueue calls are patched — no real I/O.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.communication.overdue_reminders import (
    MAX_REMINDERS,
    MIN_DAYS_BETWEEN_REMINDERS,
    OVERDUE_THRESHOLD_DAYS,
    send_overdue_reminders,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _invoice(
    *,
    id=None,
    school_id=None,
    parent_id=None,
    due_date=None,
    total_amount="150.00",
    currency="MAD",
    reminder_count=0,
    reminder_sent_at=None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id or uuid.uuid4(),
        school_id=school_id or uuid.uuid4(),
        parent_id=parent_id or uuid.uuid4(),
        due_date=due_date or date(2024, 1, 1),
        total_amount=total_amount,
        currency=currency,
        reminder_count=reminder_count,
        reminder_sent_at=reminder_sent_at,
    )


def _parent(*, email: str | None = "parent@test.ma", first_name="Ahmed"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=email,
        first_name=first_name,
        full_name="Ahmed Benali",
    )


def _consent(status: str = "active"):
    return SimpleNamespace(status=status)


def _make_fake_repo(
    *,
    invoices=None,
    parent=None,
    consent=None,
) -> MagicMock:
    repo = MagicMock()
    repo.get_overdue_invoices = AsyncMock(return_value=invoices or [])
    repo.get_user_by_id = AsyncMock(return_value=parent)
    repo.get_billing_email_consent = AsyncMock(return_value=consent)
    repo.save_invoice = AsyncMock()
    return repo


class _FakeUoW:
    def __init__(self, session=None) -> None:
        self.session = session or AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def commit(self) -> None:
        self.committed = True


def _session_factory(db_mock=None):
    db = db_mock or AsyncMock()

    @asynccontextmanager
    async def _cm():
        yield db

    return _cm, db


# ---------------------------------------------------------------------------
# send_overdue_reminders — empty invoice list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_invoices_returns_zero():
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[])
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
    ):
        result = await send_overdue_reminders()

    assert result == 0
    fake_repo.get_overdue_invoices.assert_awaited_once()


# ---------------------------------------------------------------------------
# send_overdue_reminders — happy path: reminder sent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sends_reminder_for_overdue_invoice():
    inv = _invoice()
    parent = _parent()
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=parent, consent=None)
    fake_uow = _FakeUoW(session=db)
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        result = await send_overdue_reminders()

    assert result == 1
    mock_enqueue.assert_awaited_once()
    enqueue_kwargs = mock_enqueue.call_args.kwargs
    assert enqueue_kwargs["to"] == parent.email
    assert enqueue_kwargs["template_name"] == "invoice_reminder"
    assert enqueue_kwargs["invoice_id"] == str(inv.id)

    assert inv.reminder_count == 1
    assert inv.reminder_sent_at is not None
    fake_repo.save_invoice.assert_awaited_once_with(inv)


# ---------------------------------------------------------------------------
# send_overdue_reminders — parent not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_skips_when_parent_not_found():
    inv = _invoice()
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=None)
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=AsyncMock()),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        result = await send_overdue_reminders()

    assert result == 0
    mock_enqueue.assert_not_awaited()


# ---------------------------------------------------------------------------
# send_overdue_reminders — parent has no email
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_skips_when_parent_has_no_email():
    inv = _invoice()
    parent = _parent(email=None)
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=parent)
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=AsyncMock()),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        result = await send_overdue_reminders()

    assert result == 0
    mock_enqueue.assert_not_awaited()


# ---------------------------------------------------------------------------
# send_overdue_reminders — parent opted out of billing emails
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_skips_when_parent_opted_out():
    inv = _invoice()
    parent = _parent()
    consent = _consent(status="opted_out")
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=parent, consent=consent)
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=AsyncMock()),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        result = await send_overdue_reminders()

    assert result == 0
    mock_enqueue.assert_not_awaited()


# ---------------------------------------------------------------------------
# send_overdue_reminders — consent exists but not opted_out → send
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sends_when_consent_is_active():
    inv = _invoice()
    parent = _parent()
    consent = _consent(status="active")
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=parent, consent=consent)
    fake_uow = _FakeUoW(session=db)
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        result = await send_overdue_reminders()

    assert result == 1
    mock_enqueue.assert_awaited_once()


# ---------------------------------------------------------------------------
# send_overdue_reminders — parent.first_name is None → uses full_name
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_uses_full_name_when_first_name_none():
    inv = _invoice()
    parent = SimpleNamespace(
        id=uuid.uuid4(),
        email="parent@test.ma",
        first_name=None,
        full_name="Ahmed Benali",
    )
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=parent)
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=AsyncMock()),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        await send_overdue_reminders()

    enqueue_kwargs = mock_enqueue.call_args.kwargs
    assert enqueue_kwargs["parent_name"] == "Ahmed Benali"


# ---------------------------------------------------------------------------
# send_overdue_reminders — exception per invoice is caught
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exception_in_loop_continues_other_invoices():
    inv1 = _invoice()
    inv2 = _invoice()
    parent = _parent()
    session_cm, db = _session_factory()

    call_count = 0

    async def _get_user(user_id):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("DB blip")
        return parent

    fake_repo = _make_fake_repo(invoices=[inv1, inv2], parent=parent)
    fake_repo.get_user_by_id = _get_user
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=AsyncMock()),
        patch("app.core.tasks.enqueue_email", AsyncMock()),
    ):
        result = await send_overdue_reminders()

    assert result == 1  # second invoice processed


# ---------------------------------------------------------------------------
# send_overdue_reminders — audit log called correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_log_called_with_correct_data():
    inv = _invoice()
    parent = _parent()
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[inv], parent=parent)
    fake_uow = _FakeUoW(session=db)
    mock_audit = AsyncMock()
    mock_audit.log_event = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()),
    ):
        await send_overdue_reminders()

    mock_audit.log_event.assert_awaited_once()
    call_kwargs = mock_audit.log_event.call_args.kwargs
    assert call_kwargs["action_type"] == "invoice.overdue_reminder_sent"
    assert call_kwargs["target_type"] == "invoice"
    assert call_kwargs["outcome"] == "success"


# ---------------------------------------------------------------------------
# send_overdue_reminders — uow committed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_uow_committed_after_processing():
    session_cm, db = _session_factory()
    fake_repo = _make_fake_repo(invoices=[])
    fake_uow = _FakeUoW(session=db)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
    ):
        await send_overdue_reminders()

    assert fake_uow.committed is True


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_constants():
    assert MAX_REMINDERS == 3
    assert OVERDUE_THRESHOLD_DAYS == 7
    assert MIN_DAYS_BETWEEN_REMINDERS == 3
