"""Unit tests for micro-school services."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.core.dependencies import AuthContext
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
import app.services.school.micro_school_service as micro_module
from app.services.school.micro_school_service import (
    MicroGroupService,
    MicroPaymentService,
    MicroProgressService,
    MicroSchoolService,
)


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_micro_school(
    *,
    educator_id: uuid.UUID,
    school_id: uuid.UUID | None = None,
    status: str = "active",
):
    now = datetime(2026, 4, 3, 10, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=school_id or uuid.uuid4(),
        educator_id=educator_id,
        name="Micro-Ecole Maarif",
        neighborhood="Maarif",
        city="Casablanca",
        phone="+212612345678",
        max_capacity=20,
        status=status,
        created_at=now,
        updated_at=now,
        groups=[],
        payments=[],
    )


def make_micro_group(*, micro_school, group_id: uuid.UUID | None = None):
    now = datetime(2026, 4, 3, 10, 30, tzinfo=UTC)
    return SimpleNamespace(
        id=group_id or uuid.uuid4(),
        micro_school_id=micro_school.id,
        name="Groupe Soleil",
        age_range_min=3,
        age_range_max=5,
        created_at=now,
        updated_at=now,
        micro_school=micro_school,
        enrollments=[],
    )


def make_micro_enrollment(
    *,
    micro_group,
    parent_id: uuid.UUID,
    enrollment_id: uuid.UUID | None = None,
    status: str = "active",
):
    now = datetime(2026, 4, 3, 11, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=enrollment_id or uuid.uuid4(),
        micro_group_id=micro_group.id,
        child_name="Yasmine",
        parent_id=parent_id,
        date_of_birth=date(2022, 5, 1),
        enrolled_at=now,
        status=status,
        created_at=now,
        updated_at=now,
        micro_group=micro_group,
        payments=[],
        progress_logs=[],
    )


def make_micro_payment(
    *,
    micro_school,
    parent_id: uuid.UUID,
    child_enrollment_id: uuid.UUID,
    payment_id: uuid.UUID | None = None,
    amount: float = 400.0,
    status: str = "pending",
    paid_at: datetime | None = None,
):
    now = datetime(2026, 4, 3, 12, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=payment_id or uuid.uuid4(),
        micro_school_id=micro_school.id,
        parent_id=parent_id,
        child_enrollment_id=child_enrollment_id,
        amount=amount,
        currency="MAD",
        period_type="monthly",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        paid_at=paid_at,
        status=status,
        created_at=now,
        updated_at=now,
        micro_school=micro_school,
    )


def make_micro_resource(*, resource_id: uuid.UUID | None = None):
    now = datetime(2026, 4, 3, 12, 30, tzinfo=UTC)
    return SimpleNamespace(
        id=resource_id or uuid.uuid4(),
        title="Jeu de couleurs",
        description="Activite de tri et de couleurs",
        resource_type="game",
        age_group="3-5",
        language="fr",
        file_url="https://cdn.ecole.ma/resource.pdf",
        is_premium=False,
        created_at=now,
        updated_at=now,
    )


def make_micro_progress(
    *,
    micro_enrollment,
    educator_id: uuid.UUID,
    progress_id: uuid.UUID | None = None,
    progress_date: date = date(2026, 4, 3),
    milestone_tag: str | None = "language",
):
    now = datetime(2026, 4, 3, 13, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=progress_id or uuid.uuid4(),
        micro_enrollment_id=micro_enrollment.id,
        educator_id=educator_id,
        date=progress_date,
        note="Belle participation au cercle de lecture.",
        photo_url=None,
        milestone_tag=milestone_tag,
        created_at=now,
        updated_at=now,
        micro_enrollment=micro_enrollment,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch, service_cls):
    service = service_cls(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit_in_uow = AsyncMock()
    dispatcher_in_uow = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(micro_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        micro_module,
        "MicroSchoolRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(micro_module, "AuditService", lambda _session: audit_in_uow)
    monkeypatch.setattr(
        micro_module,
        "EventDispatcher",
        lambda _session: dispatcher_in_uow,
    )

    return service, repo_in_uow, audit_in_uow, dispatcher_in_uow, uow


class TestMicroSchoolService:
    @pytest.mark.asyncio
    async def test_create_micro_school_defaults_educator_to_auth_user(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(
            monkeypatch,
            MicroSchoolService,
        )
        created = make_micro_school(educator_id=auth.user_id)
        service.repo.get_user.return_value = SimpleNamespace(id=auth.user_id)
        service.repo.get_membership_role.return_value = "EDUCATOR"
        repo_in_uow.create_micro_school.return_value = created

        result = await service.create_micro_school(
            body=micro_module.MicroSchoolCreateRequest(
                name="Micro-Ecole Maarif",
                neighborhood="Maarif",
                city="Casablanca",
                phone="+212612345678",
                max_capacity=24,
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["educator_id"] == str(auth.user_id)
        assert repo_in_uow.create_micro_school.await_count == 1
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True
        audit.log_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_micro_school_rejects_foreign_educator_for_non_admin(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, *_ = setup_service(monkeypatch, MicroSchoolService)

        with pytest.raises(AuthorizationError, match="another educator"):
            await service.create_micro_school(
                body=micro_module.MicroSchoolCreateRequest(
                    educator_id=uuid.uuid4(),
                    name="Micro-Ecole",
                    neighborhood="Maarif",
                    city="Casablanca",
                    phone="+212612345678",
                    max_capacity=18,
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_micro_school_rejects_non_educator_target(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        educator_id = uuid.uuid4()
        service, *_ = setup_service(monkeypatch, MicroSchoolService)
        service.repo.get_user.return_value = SimpleNamespace(id=educator_id)
        service.repo.get_membership_role.return_value = "PAR"

        with pytest.raises(ValidationError, match="educator-capable role"):
            await service.create_micro_school(
                body=micro_module.MicroSchoolCreateRequest(
                    educator_id=educator_id,
                    name="Micro-Ecole",
                    neighborhood="Maarif",
                    city="Casablanca",
                    phone="+212612345678",
                    max_capacity=18,
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_list_micro_schools_scopes_educator_to_self(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, *_ = setup_service(monkeypatch, MicroSchoolService)
        service.repo.list_micro_schools.return_value = [
            make_micro_school(educator_id=auth.user_id),
        ]

        items = await service.list_micro_schools(
            auth=auth,
            educator_id=uuid.uuid4(),
            city=None,
            status=None,
        )

        service.repo.list_micro_schools.assert_awaited_once_with(
            school_id=auth.school_id,
            educator_id=auth.user_id,
            city=None,
            status=None,
        )
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_list_micro_schools_filters_parent_visibility(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroSchoolService)
        visible = make_micro_school(educator_id=uuid.uuid4())
        hidden = make_micro_school(educator_id=uuid.uuid4())
        service.repo.list_micro_schools.return_value = [visible, hidden]
        service.repo.parent_has_school_access.side_effect = [True, False]

        items = await service.list_micro_schools(
            auth=auth,
            educator_id=None,
            city=None,
            status=None,
        )

        assert [item["id"] for item in items] == [str(visible.id)]

    @pytest.mark.asyncio
    async def test_update_micro_school_rejects_unrelated_educator(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, *_ = setup_service(monkeypatch, MicroSchoolService)
        service.repo.get_micro_school.return_value = make_micro_school(
            educator_id=uuid.uuid4()
        )

        with pytest.raises(AuthorizationError, match="manage this micro-school"):
            await service.update_micro_school(
                micro_school_id=uuid.uuid4(),
                body=micro_module.MicroSchoolUpdateRequest(city="Rabat"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_resource_rejects_parent_role(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroSchoolService)

        with pytest.raises(AuthorizationError, match="manage micro resources"):
            await service.create_resource(
                body=micro_module.MicroResourceCreateRequest(
                    title="Chanson des couleurs",
                    resource_type="song",
                    age_group="3-5",
                    language="fr",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_update_resource_returns_serialized_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, repo_in_uow, audit, _, uow = setup_service(
            monkeypatch,
            MicroSchoolService,
        )
        resource = make_micro_resource()
        service.repo.get_micro_resource.return_value = resource
        repo_in_uow.get_micro_resource.return_value = resource
        repo_in_uow.save_micro_resource.return_value = resource

        result = await service.update_resource(
            micro_resource_id=resource.id,
            body=micro_module.MicroResourceUpdateRequest(title="Jeu revise"),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["title"] == "Jeu revise"
        assert uow.committed is True
        audit.log_event.assert_awaited_once()


class TestMicroGroupService:
    @pytest.mark.asyncio
    async def test_create_group_dispatches_event(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(
            monkeypatch,
            MicroGroupService,
        )
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        service.repo.get_micro_school.return_value = school
        repo_in_uow.create_micro_group.return_value = group

        result = await service.create_group(
            body=micro_module.MicroGroupCreateRequest(
                micro_school_id=school.id,
                name="Groupe Soleil",
                age_range_min=3,
                age_range_max=5,
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["micro_school_id"] == str(school.id)
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_create_enrollment_parent_can_enroll_own_child(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(
            monkeypatch,
            MicroGroupService,
        )
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        created = make_micro_enrollment(micro_group=group, parent_id=auth.user_id)
        service.repo.get_micro_group.return_value = group
        service.repo.get_user.return_value = SimpleNamespace(id=auth.user_id)
        repo_in_uow.create_micro_enrollment.return_value = created

        result = await service.create_enrollment(
            body=micro_module.MicroEnrollmentCreateRequest(
                micro_group_id=group.id,
                child_name="Yasmine",
                parent_id=auth.user_id,
                date_of_birth=date(2022, 5, 1),
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["parent_id"] == str(auth.user_id)
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_create_enrollment_parent_cannot_enroll_for_other_parent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroGroupService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        service.repo.get_micro_group.return_value = group

        with pytest.raises(AuthorizationError, match="their own child"):
            await service.create_enrollment(
                body=micro_module.MicroEnrollmentCreateRequest(
                    micro_group_id=group.id,
                    child_name="Yasmine",
                    parent_id=uuid.uuid4(),
                    date_of_birth=date(2022, 5, 1),
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_enrollment_rejects_missing_parent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, *_ = setup_service(monkeypatch, MicroGroupService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        service.repo.get_micro_group.return_value = group
        service.repo.get_user.return_value = None

        with pytest.raises(NotFoundError, match="Parent user not found"):
            await service.create_enrollment(
                body=micro_module.MicroEnrollmentCreateRequest(
                    micro_group_id=group.id,
                    child_name="Yasmine",
                    parent_id=uuid.uuid4(),
                    date_of_birth=date(2022, 5, 1),
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_list_enrollments_scopes_parent_to_self(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroGroupService)
        group = make_micro_group(
            micro_school=make_micro_school(educator_id=uuid.uuid4())
        )
        own = make_micro_enrollment(micro_group=group, parent_id=auth.user_id)
        other = make_micro_enrollment(micro_group=group, parent_id=uuid.uuid4())
        service.repo.list_micro_enrollments.return_value = [own, other]

        items = await service.list_enrollments(
            auth=auth,
            micro_group_id=None,
            parent_id=uuid.uuid4(),
            status=None,
        )

        service.repo.list_micro_enrollments.assert_awaited_once_with(
            school_id=auth.school_id,
            micro_group_id=None,
            parent_id=auth.user_id,
            status=None,
        )
        assert [item["id"] for item in items] == [str(own.id)]

    @pytest.mark.asyncio
    async def test_update_enrollment_parent_rejects_disallowed_fields(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroGroupService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=auth.user_id)
        service.repo.get_micro_enrollment.return_value = enrollment

        with pytest.raises(AuthorizationError, match="only update enrollment"):
            await service.update_enrollment(
                micro_enrollment_id=enrollment.id,
                body=micro_module.MicroEnrollmentUpdateRequest(parent_id=uuid.uuid4()),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_delete_group_returns_previous_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, repo_in_uow, audit, _, uow = setup_service(
            monkeypatch, MicroGroupService
        )
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        service.repo.get_micro_group.return_value = group
        repo_in_uow.get_micro_group.return_value = group

        result = await service.delete_group(
            micro_group_id=group.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(group.id)
        repo_in_uow.delete_micro_group.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestMicroPaymentService:
    @pytest.mark.asyncio
    async def test_create_payment_rejects_parent_mismatch(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroPaymentService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=auth.user_id)
        service.repo.get_micro_school.return_value = school
        service.repo.get_micro_enrollment.return_value = enrollment

        with pytest.raises(AuthorizationError, match="their own micro-school payments"):
            await service.create_payment(
                body=micro_module.MicroPaymentCreateRequest(
                    micro_school_id=school.id,
                    parent_id=uuid.uuid4(),
                    child_enrollment_id=enrollment.id,
                    amount=400.0,
                    period_start=date(2026, 4, 1),
                    period_end=date(2026, 4, 30),
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_payment_sets_paid_at_when_status_paid(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(
            monkeypatch,
            MicroPaymentService,
        )
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=auth.user_id)
        created = make_micro_payment(
            micro_school=school,
            parent_id=auth.user_id,
            child_enrollment_id=enrollment.id,
            status="paid",
            paid_at=datetime(2026, 4, 3, 12, 0, tzinfo=UTC),
        )
        service.repo.get_micro_school.return_value = school
        service.repo.get_micro_enrollment.return_value = enrollment
        repo_in_uow.create_micro_payment.return_value = created

        result = await service.create_payment(
            body=micro_module.MicroPaymentCreateRequest(
                micro_school_id=school.id,
                parent_id=auth.user_id,
                child_enrollment_id=enrollment.id,
                amount=400.0,
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
                status="paid",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["status"] == "paid"
        assert result["paid_at"] is not None
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_payments_scopes_parent_to_self(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroPaymentService)
        school = make_micro_school(educator_id=uuid.uuid4())
        own = make_micro_payment(
            micro_school=school,
            parent_id=auth.user_id,
            child_enrollment_id=uuid.uuid4(),
        )
        other = make_micro_payment(
            micro_school=school,
            parent_id=uuid.uuid4(),
            child_enrollment_id=uuid.uuid4(),
        )
        service.repo.list_micro_payments.return_value = [own, other]

        items = await service.list_payments(
            auth=auth,
            micro_school_id=None,
            parent_id=uuid.uuid4(),
            child_enrollment_id=None,
            status=None,
        )

        service.repo.list_micro_payments.assert_awaited_once_with(
            school_id=auth.school_id,
            micro_school_id=None,
            parent_id=auth.user_id,
            child_enrollment_id=None,
            status=None,
        )
        assert [item["id"] for item in items] == [str(own.id)]

    @pytest.mark.asyncio
    async def test_update_payment_sets_paid_at_on_transition(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, repo_in_uow, audit, _, uow = setup_service(
            monkeypatch,
            MicroPaymentService,
        )
        school = make_micro_school(educator_id=uuid.uuid4())
        payment = make_micro_payment(
            micro_school=school,
            parent_id=uuid.uuid4(),
            child_enrollment_id=uuid.uuid4(),
            status="pending",
            paid_at=None,
        )
        service.repo.get_micro_payment.return_value = payment
        repo_in_uow.get_micro_payment.return_value = payment
        repo_in_uow.save_micro_payment.return_value = payment

        result = await service.update_payment(
            micro_payment_id=payment.id,
            body=micro_module.MicroPaymentUpdateRequest(status="paid"),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["status"] == "paid"
        assert result["paid_at"] is not None
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_get_payment_analytics_aggregates_amounts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, *_ = setup_service(monkeypatch, MicroPaymentService)
        school = make_micro_school(educator_id=uuid.uuid4())
        service.repo.list_micro_payments.return_value = [
            make_micro_payment(
                micro_school=school,
                parent_id=uuid.uuid4(),
                child_enrollment_id=uuid.uuid4(),
                amount=300.0,
                status="paid",
                paid_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
            ),
            make_micro_payment(
                micro_school=school,
                parent_id=uuid.uuid4(),
                child_enrollment_id=uuid.uuid4(),
                amount=200.0,
                status="pending",
            ),
            make_micro_payment(
                micro_school=school,
                parent_id=uuid.uuid4(),
                child_enrollment_id=uuid.uuid4(),
                amount=100.0,
                status="overdue",
            ),
        ]

        result = await service.get_payment_analytics(auth=auth, micro_school_id=None)

        assert result == {
            "total_amount": 600.0,
            "collected_amount": 300.0,
            "overdue_amount": 100.0,
            "pending_amount": 200.0,
            "paid_count": 1,
            "overdue_count": 1,
            "pending_count": 1,
            "collection_rate": 50.0,
        }

    @pytest.mark.asyncio
    async def test_delete_payment_requires_manage_access(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, *_ = setup_service(monkeypatch, MicroPaymentService)
        school = make_micro_school(educator_id=uuid.uuid4())
        payment = make_micro_payment(
            micro_school=school,
            parent_id=uuid.uuid4(),
            child_enrollment_id=uuid.uuid4(),
        )
        service.repo.get_micro_payment.return_value = payment

        with pytest.raises(AuthorizationError, match="manage this micro-school"):
            await service.delete_payment(
                micro_payment_id=payment.id,
                auth=auth,
            )


class TestMicroProgressService:
    @pytest.mark.asyncio
    async def test_create_progress_log_dispatches_event(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(
            monkeypatch,
            MicroProgressService,
        )
        school = make_micro_school(educator_id=auth.user_id)
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=uuid.uuid4())
        created = make_micro_progress(
            micro_enrollment=enrollment, educator_id=auth.user_id
        )
        service.repo.get_micro_enrollment.return_value = enrollment
        service.repo.get_user.return_value = SimpleNamespace(id=auth.user_id)
        service.repo.get_membership_role.return_value = "EDUCATOR"
        repo_in_uow.create_micro_progress_log.return_value = created

        result = await service.create_progress_log(
            body=micro_module.MicroProgressLogCreateRequest(
                micro_enrollment_id=enrollment.id,
                date=date(2026, 4, 3),
                note="Participation active au cercle de lecture.",
                milestone_tag="language",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["micro_enrollment_id"] == str(enrollment.id)
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_create_progress_log_rejects_foreign_educator(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, *_ = setup_service(monkeypatch, MicroProgressService)
        school = make_micro_school(educator_id=auth.user_id)
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=uuid.uuid4())
        service.repo.get_micro_enrollment.return_value = enrollment

        with pytest.raises(AuthorizationError, match="another educator"):
            await service.create_progress_log(
                body=micro_module.MicroProgressLogCreateRequest(
                    micro_enrollment_id=enrollment.id,
                    educator_id=uuid.uuid4(),
                    date=date(2026, 4, 3),
                    note="Observation",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_list_progress_logs_scopes_educator_to_self(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, *_ = setup_service(monkeypatch, MicroProgressService)
        enrollment = make_micro_enrollment(
            micro_group=make_micro_group(
                micro_school=make_micro_school(educator_id=auth.user_id)
            ),
            parent_id=uuid.uuid4(),
        )
        own = make_micro_progress(micro_enrollment=enrollment, educator_id=auth.user_id)
        service.repo.list_micro_progress_logs.return_value = [own]

        items = await service.list_progress_logs(
            auth=auth,
            micro_enrollment_id=None,
            educator_id=uuid.uuid4(),
            date_from=None,
            date_to=None,
        )

        service.repo.list_micro_progress_logs.assert_awaited_once_with(
            school_id=auth.school_id,
            micro_enrollment_id=None,
            educator_id=auth.user_id,
            date_from=None,
            date_to=None,
        )
        assert [item["id"] for item in items] == [str(own.id)]

    @pytest.mark.asyncio
    async def test_list_progress_logs_parent_filters_to_owned_enrollment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroProgressService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        own_enrollment = make_micro_enrollment(
            micro_group=group, parent_id=auth.user_id
        )
        other_enrollment = make_micro_enrollment(
            micro_group=group, parent_id=uuid.uuid4()
        )
        own = make_micro_progress(
            micro_enrollment=own_enrollment, educator_id=uuid.uuid4()
        )
        other = make_micro_progress(
            micro_enrollment=other_enrollment, educator_id=uuid.uuid4()
        )
        service.repo.list_micro_progress_logs.return_value = [own, other]
        service.repo.get_micro_enrollment.side_effect = [
            own_enrollment,
            other_enrollment,
        ]

        items = await service.list_progress_logs(
            auth=auth,
            micro_enrollment_id=None,
            educator_id=None,
            date_from=None,
            date_to=None,
        )

        assert [item["id"] for item in items] == [str(own.id)]

    @pytest.mark.asyncio
    async def test_summarize_progress_returns_latest_date_and_tags(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("ADM")
        service, *_ = setup_service(monkeypatch, MicroProgressService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=uuid.uuid4())
        older = make_micro_progress(
            micro_enrollment=enrollment,
            educator_id=uuid.uuid4(),
            progress_date=date(2026, 4, 1),
            milestone_tag="language",
        )
        latest = make_micro_progress(
            micro_enrollment=enrollment,
            educator_id=uuid.uuid4(),
            progress_date=date(2026, 4, 3),
            milestone_tag="social",
        )
        enrollment.progress_logs = [older, latest]
        service.repo.get_micro_enrollment.return_value = enrollment

        result = await service.summarize_progress(
            micro_enrollment_id=enrollment.id,
            auth=auth,
        )

        assert result["latest_log_date"] == "2026-04-03"
        assert result["milestone_tags"] == ["language", "social"]

    @pytest.mark.asyncio
    async def test_summarize_progress_rejects_wrong_parent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("PAR")
        service, *_ = setup_service(monkeypatch, MicroProgressService)
        school = make_micro_school(educator_id=uuid.uuid4())
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=uuid.uuid4())
        service.repo.get_micro_enrollment.return_value = enrollment

        with pytest.raises(AuthorizationError, match="progress summary"):
            await service.summarize_progress(
                micro_enrollment_id=enrollment.id,
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_delete_progress_log_allows_owner_educator(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("EDUCATOR")
        service, repo_in_uow, audit, _, uow = setup_service(
            monkeypatch,
            MicroProgressService,
        )
        school = make_micro_school(educator_id=auth.user_id)
        group = make_micro_group(micro_school=school)
        enrollment = make_micro_enrollment(micro_group=group, parent_id=uuid.uuid4())
        progress = make_micro_progress(
            micro_enrollment=enrollment, educator_id=auth.user_id
        )
        service.repo.get_micro_progress_log.return_value = progress
        repo_in_uow.get_micro_progress_log.return_value = progress

        result = await service.delete_progress_log(
            micro_progress_log_id=progress.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(progress.id)
        repo_in_uow.delete_micro_progress_log.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True
