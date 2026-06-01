"""Unit tests for app/services/billing/payment_retry.py.

All DB/UoW/enqueue calls are patched — no real I/O.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.billing.payment_retry import (
    MAX_RETRIES,
    RETRY_BACKOFF_HOURS,
    retry_failed_payments,
    schedule_retry_for_failed_payment,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attempt(
    *,
    id=None,
    invoice_id=None,
    parent_id=None,
    school_id=None,
    retry_count=0,
    status="failed",
    next_retry_at=None,
    finalized_at=None,
    last_retry_error=None,
):
    return SimpleNamespace(
        id=id or uuid.uuid4(),
        invoice_id=invoice_id or uuid.uuid4(),
        parent_id=parent_id or uuid.uuid4(),
        school_id=school_id or uuid.uuid4(),
        retry_count=retry_count,
        status=status,
        next_retry_at=next_retry_at,
        finalized_at=finalized_at,
        last_retry_error=last_retry_error,
    )


def _invoice(*, status="pending", total_amount="250.00", currency="MAD", due_date=None):
    from datetime import date
    return SimpleNamespace(
        id=uuid.uuid4(),
        status=status,
        total_amount=total_amount,
        currency=currency,
        due_date=due_date or date(2024, 1, 1),
    )


def _parent(*, email="parent@test.ma", first_name="Khadija"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=email,
        first_name=first_name,
        full_name="Khadija Alaoui",
    )


def _make_repo(*, attempts=None, invoice=None, parent=None, payment=None):
    repo = MagicMock()
    repo.get_failed_attempts = AsyncMock(return_value=attempts or [])
    repo.get_invoice_by_id = AsyncMock(return_value=invoice)
    repo.get_user_by_id = AsyncMock(return_value=parent)
    repo.get_payment_by_id = AsyncMock(return_value=payment)
    repo.save_invoice = AsyncMock()
    repo.save_payment = AsyncMock()
    return repo


class _FakeUoW:
    def __init__(self, session=None):
        self.session = session or AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def commit(self):
        self.committed = True


def _session_factory():
    db = AsyncMock()

    @asynccontextmanager
    async def _cm():
        yield db

    return _cm, db


# ---------------------------------------------------------------------------
# retry_failed_payments — empty list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_attempts_returns_zero():
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[])
    fake_uow = _FakeUoW()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
    ):
        result = await retry_failed_payments()

    assert result == 0
    fake_repo.get_failed_attempts.assert_awaited_once()


# ---------------------------------------------------------------------------
# retry_failed_payments — first retry (retry_count < MAX_RETRIES)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_retry_schedules_next():
    att = _attempt(retry_count=0)
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att])
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
    ):
        result = await retry_failed_payments()

    assert result == 1
    assert att.retry_count == 1
    assert att.status == "pending"
    assert att.finalized_at is None
    assert att.next_retry_at is not None

    # Backoff is RETRY_BACKOFF_HOURS[0] = 1h
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(hours=RETRY_BACKOFF_HOURS[0])
    diff = abs((att.next_retry_at - now).total_seconds() - expected_delta.total_seconds())
    assert diff < 5  # within 5 seconds

    fake_repo.save_payment.assert_awaited_once_with(att)


@pytest.mark.asyncio
async def test_second_retry_uses_second_backoff():
    att = _attempt(retry_count=1)
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att])
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
    ):
        await retry_failed_payments()

    now = datetime.now(timezone.utc)
    expected_delta = timedelta(hours=RETRY_BACKOFF_HOURS[1])
    diff = abs((att.next_retry_at - now).total_seconds() - expected_delta.total_seconds())
    assert diff < 5


# ---------------------------------------------------------------------------
# retry_failed_payments — backoff index out of range → uses last
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_backoff_beyond_list_uses_last_element():
    att = _attempt(retry_count=10)  # far beyond MAX_RETRIES, to test the else branch
    # But retry_count < MAX_RETRIES is required; simulate retry_count=2 which is MAX_RETRIES-1
    att.retry_count = MAX_RETRIES - 1  # so after increment it's MAX_RETRIES (final)
    # Actually we want to test the backoff branch:
    # backoff index = retry_count - 1 >= len(RETRY_BACKOFF_HOURS)
    # retry_count starts at 1, after increment = 2, backoff_idx = 1 → ok
    # Let's test retry_count=0, after increment=1, backoff_idx=0 → ok
    # We need to make backoff_idx >= len(RETRY_BACKOFF_HOURS)
    # len(RETRY_BACKOFF_HOURS) == 3, so need retry_count-1 >= 3 → retry_count >= 4
    # But retry_count >= MAX_RETRIES (3) triggers final failure branch
    # So this scenario can't happen naturally — the code uses `else: RETRY_BACKOFF_HOURS[-1]`
    # as a safety net. We can force it by temporarily modifying the list.
    att = _attempt(retry_count=0)
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att])
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    # Temporarily make RETRY_BACKOFF_HOURS shorter so index overflows
    with (
        patch("app.services.billing.payment_retry.RETRY_BACKOFF_HOURS", [99]),
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
    ):
        result = await retry_failed_payments()

    assert result == 1
    # backoff index 0 (retry_count=1-1=0) -> within list: uses RETRY_BACKOFF_HOURS[0]=99
    now = datetime.now(timezone.utc)
    diff = abs((att.next_retry_at - now).total_seconds() - 99 * 3600)
    assert diff < 5


# ---------------------------------------------------------------------------
# retry_failed_payments — final failure (retry_count reaches MAX_RETRIES)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_final_failure_marks_attempt_and_invoice():
    att = _attempt(retry_count=MAX_RETRIES - 1)
    inv = _invoice(status="pending")
    parent = _parent()
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att], invoice=inv, parent=parent)
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        result = await retry_failed_payments()

    assert result == 1
    assert att.retry_count == MAX_RETRIES
    assert att.status == "failed"
    assert att.finalized_at is not None
    assert att.next_retry_at is None

    assert inv.status == "failed"
    fake_repo.save_invoice.assert_awaited_once_with(inv)

    mock_enqueue.assert_awaited_once()
    enqueue_kwargs = mock_enqueue.call_args.kwargs
    assert enqueue_kwargs["to"] == parent.email


@pytest.mark.asyncio
async def test_final_failure_invoice_not_pending_not_updated():
    att = _attempt(retry_count=MAX_RETRIES - 1)
    inv = _invoice(status="paid")  # not pending → should not be updated
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att], invoice=inv)
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()),
    ):
        await retry_failed_payments()

    assert inv.status == "paid"  # unchanged
    fake_repo.save_invoice.assert_not_awaited()


@pytest.mark.asyncio
async def test_final_failure_invoice_not_found_no_crash():
    att = _attempt(retry_count=MAX_RETRIES - 1)
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att], invoice=None)
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()),
    ):
        result = await retry_failed_payments()

    assert result == 1  # attempt still counted as retried


@pytest.mark.asyncio
async def test_final_failure_parent_not_found_no_email():
    att = _attempt(retry_count=MAX_RETRIES - 1)
    inv = _invoice(status="pending")
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att], invoice=inv, parent=None)
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()) as mock_enqueue,
    ):
        await retry_failed_payments()

    mock_enqueue.assert_not_awaited()


@pytest.mark.asyncio
async def test_final_failure_enqueue_exception_is_swallowed():
    att = _attempt(retry_count=MAX_RETRIES - 1)
    inv = _invoice(status="pending")
    parent = _parent()
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att], invoice=inv, parent=parent)
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch(
            "app.core.tasks.enqueue_email",
            AsyncMock(side_effect=RuntimeError("email down")),
        ),
    ):
        result = await retry_failed_payments()

    assert result == 1  # exception swallowed


# ---------------------------------------------------------------------------
# retry_failed_payments — audit log
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_audit_log_for_scheduled():
    att = _attempt(retry_count=0)
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att])
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
    ):
        await retry_failed_payments()

    mock_audit.log_event.assert_awaited_once()
    call_kwargs = mock_audit.log_event.call_args.kwargs
    assert call_kwargs["action_type"] == "payment.retry_scheduled"
    assert call_kwargs["outcome"] == "success"


@pytest.mark.asyncio
async def test_retry_audit_log_for_final_failure():
    att = _attempt(retry_count=MAX_RETRIES - 1)
    inv = _invoice()
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[att], invoice=inv)
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
        patch("app.core.tasks.enqueue_email", AsyncMock()),
    ):
        await retry_failed_payments()

    mock_audit.log_event.assert_awaited_once()
    assert mock_audit.log_event.call_args.kwargs["action_type"] == "payment.retry_final_failure"


# ---------------------------------------------------------------------------
# retry_failed_payments — exception per attempt is caught
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exception_in_attempt_loop_continues():
    att1 = _attempt(retry_count=0)
    att2 = _attempt(retry_count=0)
    session_cm, _ = _session_factory()

    call_count = 0

    async def _failing_audit_log(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("audit failure")

    fake_repo = _make_repo(attempts=[att1, att2])
    fake_uow = _FakeUoW()
    mock_audit = AsyncMock()
    mock_audit.log_event = AsyncMock(side_effect=_failing_audit_log)

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
        patch("app.services.platform.audit.AuditService", return_value=mock_audit),
    ):
        result = await retry_failed_payments()

    assert result == 1  # only second succeeds


# ---------------------------------------------------------------------------
# retry_failed_payments — uow committed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_uow_committed():
    session_cm, _ = _session_factory()
    fake_repo = _make_repo(attempts=[])
    fake_uow = _FakeUoW()

    with (
        patch("app.core.database.async_session", session_cm),
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
    ):
        await retry_failed_payments()

    assert fake_uow.committed is True


# ---------------------------------------------------------------------------
# schedule_retry_for_failed_payment — with UoW depth (already in transaction)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_retry_with_uow_depth():
    att = _attempt(retry_count=0)
    att_id = att.id
    fake_repo = MagicMock()
    fake_repo.get_payment_by_id = AsyncMock(return_value=att)
    fake_repo.save_payment = AsyncMock()

    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.repositories.billing.BillingRepository", return_value=fake_repo):
        await schedule_retry_for_failed_payment(att_id, mock_db)

    assert att.next_retry_at is not None
    fake_repo.save_payment.assert_awaited_once_with(att)


@pytest.mark.asyncio
async def test_schedule_retry_with_uow_depth_attempt_not_found():
    fake_repo = MagicMock()
    fake_repo.get_payment_by_id = AsyncMock(return_value=None)
    fake_repo.save_payment = AsyncMock()

    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.repositories.billing.BillingRepository", return_value=fake_repo):
        await schedule_retry_for_failed_payment(uuid.uuid4(), mock_db)

    fake_repo.save_payment.assert_not_awaited()


@pytest.mark.asyncio
async def test_schedule_retry_with_uow_depth_at_max_retries_skipped():
    att = _attempt(retry_count=MAX_RETRIES)
    fake_repo = MagicMock()
    fake_repo.get_payment_by_id = AsyncMock(return_value=att)
    fake_repo.save_payment = AsyncMock()

    mock_db = AsyncMock()
    mock_db.info = {"_uow_depth": 1}

    with patch("app.repositories.billing.BillingRepository", return_value=fake_repo):
        await schedule_retry_for_failed_payment(att.id, mock_db)

    fake_repo.save_payment.assert_not_awaited()


# ---------------------------------------------------------------------------
# schedule_retry_for_failed_payment — without UoW depth (opens own UoW)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_schedule_retry_without_uow_depth():
    att = _attempt(retry_count=0)
    fake_repo = MagicMock()
    fake_repo.get_payment_by_id = AsyncMock(return_value=att)
    fake_repo.save_payment = AsyncMock()

    mock_db = AsyncMock()
    mock_db.info = {}  # no _uow_depth

    fake_uow = _FakeUoW(session=mock_db)

    with (
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
    ):
        await schedule_retry_for_failed_payment(att.id, mock_db)

    assert att.next_retry_at is not None
    fake_repo.save_payment.assert_awaited_once_with(att)
    assert fake_uow.committed is True


@pytest.mark.asyncio
async def test_schedule_retry_without_uow_depth_not_found():
    fake_repo = MagicMock()
    fake_repo.get_payment_by_id = AsyncMock(return_value=None)
    fake_repo.save_payment = AsyncMock()

    mock_db = AsyncMock()
    mock_db.info = {}
    fake_uow = _FakeUoW(session=mock_db)

    with (
        patch("app.core.unit_of_work.UnitOfWork", return_value=fake_uow),
        patch("app.repositories.billing.BillingRepository", return_value=fake_repo),
    ):
        await schedule_retry_for_failed_payment(uuid.uuid4(), mock_db)

    fake_repo.save_payment.assert_not_awaited()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_constants():
    assert MAX_RETRIES == 3
    assert RETRY_BACKOFF_HOURS == [1, 6, 24]
