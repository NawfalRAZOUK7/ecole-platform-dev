"""Domain event dispatcher for delivery strategies."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import (
    AssignmentCreated,
    ContentPublished,
    DocumentExpiring,
    DocumentUploaded,
    DomainEvent,
    EventCreated,
    EventRSVPReceived,
    EventUpdated,
    GradePublished,
    HolidayAdded,
    InvoiceGenerated,
    NewDeviceLogin,
    PasswordChanged,
    PaymentFailed,
    PaymentReceived,
    QuizCompleted,
    ResourceShared,
    SubmissionReceived,
    TwoFactorEnabled,
    UserRegistered,
)
from app.models.com import NotificationCategory, NotificationPriority
from app.repositories.billing import BillingRepository
from app.repositories.calendar import CalendarRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.notifications import NotificationRepository
from app.services.delivery.email_delivery import EmailDeliveryStrategy
from app.services.delivery.in_app import InAppDeliveryStrategy
from app.services.delivery.push import PushDeliveryStrategy

logger = logging.getLogger(__name__)

EVENT_HANDLERS: dict[type[DomainEvent], list[dict[str, Any]]] = {
    GradePublished: [
        {"strategy": PushDeliveryStrategy, "template": "grade_published"},
        {"strategy": EmailDeliveryStrategy, "template": "grade_published"},
        {"strategy": InAppDeliveryStrategy, "template": "grade_published"},
    ],
    AssignmentCreated: [
        {"strategy": PushDeliveryStrategy, "template": "assignment_created"},
        {"strategy": InAppDeliveryStrategy, "template": "assignment_created"},
    ],
    QuizCompleted: [
        {"strategy": InAppDeliveryStrategy, "template": "quiz_completed"},
    ],
    SubmissionReceived: [
        {"strategy": InAppDeliveryStrategy, "template": "submission_received"},
    ],
    ContentPublished: [
        {"strategy": InAppDeliveryStrategy, "template": "content_published"},
    ],
    EventCreated: [
        {"strategy": InAppDeliveryStrategy, "template": "event_created"},
    ],
    EventUpdated: [
        {"strategy": InAppDeliveryStrategy, "template": "event_updated"},
    ],
    HolidayAdded: [
        {"strategy": InAppDeliveryStrategy, "template": "holiday_added"},
    ],
    EventRSVPReceived: [
        {"strategy": InAppDeliveryStrategy, "template": "event_rsvp_received"},
    ],
    InvoiceGenerated: [
        {"strategy": PushDeliveryStrategy, "template": "invoice_generated"},
        {"strategy": EmailDeliveryStrategy, "template": "invoice_generated"},
    ],
    PaymentReceived: [
        {"strategy": PushDeliveryStrategy, "template": "payment_received"},
        {"strategy": InAppDeliveryStrategy, "template": "payment_received"},
    ],
    PaymentFailed: [
        {"strategy": InAppDeliveryStrategy, "template": "payment_failed"},
    ],
    DocumentUploaded: [
        {"strategy": InAppDeliveryStrategy, "template": "document_uploaded"},
    ],
    DocumentExpiring: [
        {"strategy": PushDeliveryStrategy, "template": "document_expiring"},
        {"strategy": EmailDeliveryStrategy, "template": "document_expiring"},
    ],
    ResourceShared: [
        {"strategy": InAppDeliveryStrategy, "template": "resource_shared"},
    ],
    UserRegistered: [
        {"strategy": EmailDeliveryStrategy, "template": "user_registered"},
    ],
    NewDeviceLogin: [
        {"strategy": EmailDeliveryStrategy, "template": "new_device_login"},
    ],
    PasswordChanged: [
        {"strategy": InAppDeliveryStrategy, "template": "password_changed"},
    ],
    TwoFactorEnabled: [
        {"strategy": InAppDeliveryStrategy, "template": "two_factor_enabled"},
    ],
}


class EventDispatcher:
    """Routes domain events to delivery strategies."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._notification_repo = NotificationRepository(db)
        self._billing_repo = BillingRepository(db)
        self._calendar_repo = CalendarRepository(db)
        self._documents_repo = DocumentsRepository(db)

    async def dispatch(self, event: DomainEvent) -> None:
        handlers = EVENT_HANDLERS.get(type(event), [])
        if not handlers:
            logger.debug("No delivery handlers registered for %s", type(event).__name__)
            return

        recipients = await self._resolve_recipients(event)
        if not recipients:
            logger.info("No recipients resolved for %s", type(event).__name__)
            return

        context = self._build_context(event)
        for handler in handlers:
            strategy = handler["strategy"](self._db)
            try:
                await strategy.deliver(
                    event=event,
                    recipients=recipients,
                    template_key=handler["template"],
                    context=context,
                )
            except Exception:
                logger.exception(
                    "Delivery strategy %s failed for %s",
                    handler["strategy"].__name__,
                    type(event).__name__,
                )

    async def _resolve_recipients(self, event: DomainEvent) -> list[uuid.UUID]:
        recipients: set[uuid.UUID] = set()
        school_id = getattr(event, "school_id", None)

        if isinstance(event, GradePublished):
            recipients.update(
                await self._student_and_parent_recipients(
                    school_id=school_id,
                    student_id=event.student_id,
                )
            )
        elif isinstance(event, AssignmentCreated | ContentPublished | EventCreated):
            recipients.update(
                await self._class_recipients(
                    school_id=school_id,
                    class_id=getattr(event, "class_id", None),
                )
            )
            if not recipients and school_id is not None:
                recipients.update(
                    await self._notification_repo.list_school_member_ids(
                        school_id=school_id,
                    )
                )
        elif isinstance(event, QuizCompleted):
            recipients.update(
                await self._student_and_parent_recipients(
                    school_id=school_id,
                    student_id=event.student_id,
                )
            )
        elif isinstance(event, SubmissionReceived):
            self._add_uuid_if_present(recipients, event.teacher_id)
        elif isinstance(event, EventUpdated):
            calendar_event = (
                await self._calendar_repo.get_event(event.event_id)
                if event.event_id is not None
                else None
            )
            recipients.update(
                await self._class_recipients(
                    school_id=school_id,
                    class_id=getattr(calendar_event, "class_id", None),
                )
            )
            if not recipients and school_id is not None:
                recipients.update(
                    await self._notification_repo.list_school_member_ids(
                        school_id=school_id,
                    )
                )
        elif isinstance(event, HolidayAdded):
            if school_id is not None:
                recipients.update(
                    await self._notification_repo.list_school_member_ids(
                        school_id=school_id,
                    )
                )
        elif isinstance(event, EventRSVPReceived):
            self._add_uuid_if_present(recipients, event.user_id)
            calendar_event = (
                await self._calendar_repo.get_event(event.event_id)
                if event.event_id is not None
                else None
            )
            recipients.update(
                await self._class_recipients(
                    school_id=school_id,
                    class_id=getattr(calendar_event, "class_id", None),
                )
            )
        elif isinstance(event, InvoiceGenerated):
            invoice = (
                await self._billing_repo.get_invoice_by_id(event.invoice_id)
                if event.invoice_id is not None
                else None
            )
            if invoice is not None:
                recipients.add(invoice.parent_id)
            if not recipients:
                recipients.update(
                    await self._parent_recipients_for_student(
                        school_id=school_id,
                        student_id=event.student_id,
                    )
                )
        elif isinstance(event, (PaymentReceived, PaymentFailed)):
            payment = (
                await self._billing_repo.get_payment_by_id(event.payment_id)
                if event.payment_id is not None
                else None
            )
            if payment is not None:
                recipients.add(payment.parent_id)
            elif getattr(event, "invoice_id", None) is not None:
                invoice = await self._billing_repo.get_invoice_by_id(event.invoice_id)
                if invoice is not None:
                    recipients.add(invoice.parent_id)
        elif isinstance(event, (DocumentUploaded, DocumentExpiring)):
            document = (
                await self._documents_repo.get_document(event.document_id)
                if event.document_id is not None
                else None
            )
            if document is not None:
                recipients.add(document.uploader_id)
                recipients.update(
                    await self._student_and_parent_recipients(
                        school_id=document.school_id,
                        student_id=document.linked_student_id,
                    )
                )
            elif getattr(event, "student_id", None) is not None:
                recipients.update(
                    await self._student_and_parent_recipients(
                        school_id=school_id,
                        student_id=event.student_id,
                    )
                )
        elif isinstance(event, ResourceShared):
            resource = (
                await self._documents_repo.get_resource(event.resource_id)
                if event.resource_id is not None
                else None
            )
            if resource is not None:
                recipients.add(resource.uploader_id)
                recipients.update(
                    await self._class_recipients(
                        school_id=resource.school_id,
                        class_id=resource.class_id,
                    )
                )
                if not recipients and resource.school_id is not None:
                    recipients.update(
                        await self._notification_repo.list_school_member_ids(
                            school_id=resource.school_id,
                        )
                    )
            elif school_id is not None:
                recipients.update(
                    await self._notification_repo.list_school_member_ids(
                        school_id=school_id,
                    )
                )
        elif isinstance(
            event,
            (UserRegistered, NewDeviceLogin, PasswordChanged, TwoFactorEnabled),
        ):
            self._add_uuid_if_present(recipients, event.user_id)

        return sorted(recipients, key=str)

    async def _class_recipients(
        self,
        *,
        school_id: uuid.UUID | None,
        class_id: uuid.UUID | None,
    ) -> set[uuid.UUID]:
        if school_id is None or class_id is None:
            return set()

        student_ids = await self._notification_repo.list_students_for_classes(
            school_id=school_id,
            class_ids=[class_id],
        )
        parent_ids = await self._notification_repo.list_parents_for_students(
            school_id=school_id,
            student_ids=list(student_ids),
        )
        teacher_ids = await self._notification_repo.list_teachers_for_classes(
            school_id=school_id,
            class_ids=[class_id],
        )
        return set(student_ids) | set(parent_ids) | set(teacher_ids)

    async def _student_and_parent_recipients(
        self,
        *,
        school_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
    ) -> set[uuid.UUID]:
        recipients = await self._parent_recipients_for_student(
            school_id=school_id,
            student_id=student_id,
        )
        if student_id is not None:
            recipients.add(student_id)
        return recipients

    async def _parent_recipients_for_student(
        self,
        *,
        school_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
    ) -> set[uuid.UUID]:
        if school_id is None or student_id is None:
            return set()
        return await self._documents_repo.list_parent_ids_for_student(
            student_id=student_id,
            school_id=school_id,
        )

    def _build_context(self, event: DomainEvent) -> dict[str, Any]:
        context = asdict(event)
        title, body = self._message_for_event(event)
        context["event_ref"] = self._event_ref(event)
        context["title"] = title
        context["body"] = body
        context["category"] = self._category_for_event(event)
        context["priority"] = self._priority_for_event(event)
        context["action_url"] = self._action_url_for_event(event)
        context["currency"] = context.get("currency", "MAD")
        context["locale"] = context.get("locale", "fr")
        context["school_name"] = context.get("school_name", "Ecole Platform")
        return context

    def _message_for_event(self, event: DomainEvent) -> tuple[str, str | None]:
        if isinstance(event, GradePublished):
            return (
                "New grade published",
                f"{event.teacher_name or 'A teacher'} published {event.score} in "
                f"{event.course_title or 'your course'}.",
            )
        if isinstance(event, AssignmentCreated):
            due = f" due {event.due_at}" if event.due_at else ""
            return (
                "New assignment available",
                f"{event.course_title or 'A class'} has a new assignment{due}.",
            )
        if isinstance(event, QuizCompleted):
            return (
                "Quiz completed",
                f"{event.quiz_title or 'Quiz'} completed with score {event.score_percent}%.",
            )
        if isinstance(event, SubmissionReceived):
            return (
                "New submission received",
                f"{event.student_name or 'A student'} submitted "
                f"{event.assignment_title or 'an assignment'}.",
            )
        if isinstance(event, ContentPublished):
            return (
                "New content published",
                event.title or "New class content is available.",
            )
        if isinstance(event, EventCreated):
            return (
                f"Calendar event: {event.title or 'New event'}",
                f"Starts at {event.start_at}." if event.start_at else None,
            )
        if isinstance(event, EventUpdated):
            change_keys = ", ".join(sorted(event.changes.keys())) if event.changes else None
            return (
                f"Calendar updated: {event.title or 'Event'}",
                f"Updated fields: {change_keys}" if change_keys else "Event details changed.",
            )
        if isinstance(event, HolidayAdded):
            return (
                f"Holiday added: {event.holiday_name or 'School holiday'}",
                f"From {event.start_date} to {event.end_date}.",
            )
        if isinstance(event, EventRSVPReceived):
            return (
                "Event RSVP received",
                f"RSVP status updated to {event.status}.",
            )
        if isinstance(event, InvoiceGenerated):
            return (
                "Invoice generated",
                f"Invoice {event.invoice_id} for {event.amount} MAD is due on {event.due_date}.",
            )
        if isinstance(event, PaymentReceived):
            return (
                "Payment received",
                f"Payment of {event.amount} via {event.method or 'recorded method'} was received.",
            )
        if isinstance(event, PaymentFailed):
            return (
                "Payment failed",
                event.reason or "A payment attempt failed.",
            )
        if isinstance(event, DocumentUploaded):
            return (
                "Document uploaded",
                f"{event.filename or 'A document'} was uploaded.",
            )
        if isinstance(event, DocumentExpiring):
            return (
                "Document expiring",
                f"{event.document_name or 'A document'} expires at {event.expires_at}.",
            )
        if isinstance(event, ResourceShared):
            return (
                "New resource shared",
                event.title or "A new learning resource is available.",
            )
        if isinstance(event, UserRegistered):
            return (
                "Welcome to Ecole Platform",
                "Your account has been created successfully.",
            )
        if isinstance(event, NewDeviceLogin):
            device_name = event.device_name or "a new device"
            location = f" from {event.ip_address}" if event.ip_address else ""
            return (
                "New device login detected",
                f"We noticed a login from {device_name}{location}.",
            )
        if isinstance(event, PasswordChanged):
            return (
                "Password updated",
                "Your password was changed successfully.",
            )
        if isinstance(event, TwoFactorEnabled):
            return (
                "Two-factor authentication enabled",
                "Two-factor authentication is now active on your account.",
            )
        return (type(event).__name__, None)

    def _category_for_event(self, event: DomainEvent) -> str:
        if isinstance(
            event,
            (
                GradePublished,
                AssignmentCreated,
                QuizCompleted,
                SubmissionReceived,
                ContentPublished,
                ResourceShared,
            ),
        ):
            return NotificationCategory.ACADEMIC.value
        if isinstance(event, (InvoiceGenerated, PaymentReceived, PaymentFailed)):
            return NotificationCategory.BILLING.value
        if isinstance(event, (EventCreated, EventUpdated, HolidayAdded, EventRSVPReceived)):
            return NotificationCategory.ANNOUNCEMENT.value
        return NotificationCategory.SYSTEM.value

    def _priority_for_event(self, event: DomainEvent) -> str:
        if isinstance(
            event,
            (InvoiceGenerated, DocumentExpiring, NewDeviceLogin, PaymentFailed),
        ):
            return NotificationPriority.HIGH.value
        if isinstance(event, PaymentReceived):
            return NotificationPriority.NORMAL.value
        return NotificationPriority.NORMAL.value

    def _action_url_for_event(self, event: DomainEvent) -> str | None:
        if isinstance(
            event,
            (
                GradePublished,
                AssignmentCreated,
                QuizCompleted,
                SubmissionReceived,
                ContentPublished,
            ),
        ):
            return "/lms"
        if isinstance(event, (EventCreated, EventUpdated, HolidayAdded, EventRSVPReceived)):
            return "/calendar"
        if isinstance(event, (InvoiceGenerated, PaymentReceived, PaymentFailed)):
            return "/billing"
        if isinstance(event, (DocumentUploaded, DocumentExpiring, ResourceShared)):
            return "/documents"
        if isinstance(
            event,
            (UserRegistered, NewDeviceLogin, PasswordChanged, TwoFactorEnabled),
        ):
            return "/profile"
        return None

    def _event_ref(self, event: DomainEvent) -> str:
        name = type(event).__name__
        return "".join(
            [
                f"_{char.lower()}" if char.isupper() and index > 0 else char.lower()
                for index, char in enumerate(name)
            ]
        )

    def _add_uuid_if_present(
        self,
        recipients: set[uuid.UUID],
        value: uuid.UUID | None,
    ) -> None:
        if value is not None:
            recipients.add(value)
