"""Billing fee management API endpoints — Phase 11B.

Reference: Phase 11B — Billing Enhancements
Endpoints:
  POST   /billing/fee-structures           — Create fee structure (ADM)
  GET    /billing/fee-structures           — List fee structures
  PUT    /billing/fee-structures/{id}      — Update fee structure (ADM)
  POST   /billing/fee-assignments          — Assign fee to student (ADM)
  POST   /billing/fee-assignments/bulk     — Bulk assign fee (ADM)
  GET    /billing/fee-assignments          — List fee assignments
  POST   /billing/generate-invoices        — Generate invoices from fee structure (ADM)
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_parent_child_ids,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.response import list_response, success_response
from app.models.billing import FeeAssignment, FeeStructure, Invoice, InvoiceItem
from app.models.erp import AcademicYear, Class, Enrollment
from app.models.iam import ParentChildLink, User
from app.schemas.billing import (
    FeeAssignmentBulkCreateRequest,
    FeeAssignmentCreateRequest,
    FeeAssignmentResponse,
    FeeStructureCreateRequest,
    FeeStructureResponse,
    FeeStructureUpdateRequest,
    InvoiceGenerateRequest,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/billing", tags=["billing-fees"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _fee_structure_to_response(fs: FeeStructure) -> dict:
    return FeeStructureResponse(
        id=str(fs.id),
        school_id=str(fs.school_id),
        academic_year_id=str(fs.academic_year_id),
        name=fs.name,
        amount=float(fs.amount),
        currency=fs.currency,
        frequency=fs.frequency,
        due_day=fs.due_day,
        applies_to_level=fs.applies_to_level,
        status=fs.status,
        created_at=fs.created_at.isoformat(),
        updated_at=fs.updated_at.isoformat() if fs.updated_at else None,
    ).model_dump()


def _fee_assignment_to_response(fa: FeeAssignment) -> dict:
    return FeeAssignmentResponse(
        id=str(fa.id),
        fee_structure_id=str(fa.fee_structure_id),
        student_id=str(fa.student_id),
        school_id=str(fa.school_id),
        discount_percent=float(fa.discount_percent) if fa.discount_percent is not None else None,
        discount_reason=fa.discount_reason,
        status=fa.status,
        created_at=fa.created_at.isoformat(),
    ).model_dump()


# ---------------------------------------------------------------------------
# POST /billing/fee-structures — Create fee structure (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-structures",
    status_code=201,
    summary="Create fee structure",
    response_description="Created fee structure",
)
async def create_fee_structure(
    body: FeeStructureCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a fee structure for the school.

    Validates:
    1. Academic year exists and belongs to the same school
    """
    audit = AuditService(db)

    # Validate academic year
    ay_result = await db.execute(
        select(AcademicYear).where(AcademicYear.id == body.academic_year_id)
    )
    ay = ay_result.scalar_one_or_none()
    if ay is None:
        raise NotFoundError("Academic year not found", error_code="ERR-BIL-404")
    verify_school_boundary(ay.school_id, auth)

    fs = FeeStructure(
        school_id=auth.school_id,
        academic_year_id=body.academic_year_id,
        name=body.name,
        amount=body.amount,
        currency=body.currency,
        frequency=body.frequency,
        due_day=body.due_day,
        applies_to_level=body.applies_to_level,
        status="ACTIVE",
    )
    db.add(fs)
    await db.flush()

    resp = _fee_structure_to_response(fs)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="fee_structure.create",
        target_type="fee_structure",
        target_id=fs.id,
        outcome="success",
        entity_after=resp,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(resp)


# ---------------------------------------------------------------------------
# GET /billing/fee-structures — List fee structures
# ---------------------------------------------------------------------------
@router.get(
    "/fee-structures",
    summary="List fee structures",
    response_description="List of fee structures",
)
async def list_fee_structures(
    academic_year_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(ACTIVE|ARCHIVED)$"),
    applies_to_level: str | None = Query(None),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:read")),
    db: AsyncSession = Depends(get_db),
):
    """List fee structures with optional filters.

    Always scoped to the user's school.
    """
    query = select(FeeStructure).where(FeeStructure.school_id == auth.school_id)

    if academic_year_id:
        query = query.where(FeeStructure.academic_year_id == academic_year_id)
    if status:
        query = query.where(FeeStructure.status == status)
    if applies_to_level:
        query = query.where(FeeStructure.applies_to_level == applies_to_level)

    query = query.order_by(FeeStructure.created_at.desc())
    result = await db.execute(query)
    structures = result.scalars().all()

    return list_response([_fee_structure_to_response(fs) for fs in structures])


# ---------------------------------------------------------------------------
# PUT /billing/fee-structures/{id} — Update fee structure (ADM)
# ---------------------------------------------------------------------------
@router.put(
    "/fee-structures/{fee_structure_id}",
    summary="Update fee structure",
    response_description="Updated fee structure",
)
async def update_fee_structure(
    fee_structure_id: uuid.UUID,
    body: FeeStructureUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing fee structure."""
    audit = AuditService(db)

    result = await db.execute(
        select(FeeStructure).where(FeeStructure.id == fee_structure_id)
    )
    fs = result.scalar_one_or_none()
    if fs is None:
        raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
    verify_school_boundary(fs.school_id, auth)

    entity_before = _fee_structure_to_response(fs)

    if body.name is not None:
        fs.name = body.name
    if body.amount is not None:
        fs.amount = body.amount
    if body.currency is not None:
        fs.currency = body.currency
    if body.frequency is not None:
        fs.frequency = body.frequency
    if body.due_day is not None:
        fs.due_day = body.due_day
    if body.applies_to_level is not None:
        fs.applies_to_level = body.applies_to_level
    if body.status is not None:
        fs.status = body.status

    await db.flush()
    entity_after = _fee_structure_to_response(fs)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="fee_structure.update",
        target_type="fee_structure",
        target_id=fs.id,
        outcome="success",
        entity_before=entity_before,
        entity_after=entity_after,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(entity_after)


# ---------------------------------------------------------------------------
# POST /billing/fee-assignments — Assign fee to student (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-assignments",
    status_code=201,
    summary="Assign fee to student",
    response_description="Created fee assignment",
)
async def create_fee_assignment(
    body: FeeAssignmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Assign a fee structure to a student.

    Validates:
    1. Fee structure exists and belongs to the same school
    2. Student exists
    3. No duplicate assignment for the same fee + student
    """
    audit = AuditService(db)

    # Validate fee structure
    fs_result = await db.execute(
        select(FeeStructure).where(FeeStructure.id == body.fee_structure_id)
    )
    fs = fs_result.scalar_one_or_none()
    if fs is None:
        raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
    verify_school_boundary(fs.school_id, auth)

    # Validate student exists
    student_result = await db.execute(
        select(User).where(User.id == body.student_id)
    )
    student = student_result.scalar_one_or_none()
    if student is None:
        raise NotFoundError("Student not found", error_code="ERR-BIL-404")

    # Check duplicate
    dup_result = await db.execute(
        select(FeeAssignment).where(
            FeeAssignment.fee_structure_id == body.fee_structure_id,
            FeeAssignment.student_id == body.student_id,
        )
    )
    if dup_result.scalar_one_or_none() is not None:
        raise ConflictError(
            "Fee already assigned to this student",
            error_code="ERR-BIL-409",
        )

    fa = FeeAssignment(
        fee_structure_id=body.fee_structure_id,
        student_id=body.student_id,
        school_id=auth.school_id,
        discount_percent=body.discount_percent,
        discount_reason=body.discount_reason,
        status="ACTIVE",
    )
    db.add(fa)
    await db.flush()

    resp = _fee_assignment_to_response(fa)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="fee_assignment.create",
        target_type="fee_assignment",
        target_id=fa.id,
        outcome="success",
        entity_after=resp,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(resp)


# ---------------------------------------------------------------------------
# POST /billing/fee-assignments/bulk — Bulk assign fee (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/fee-assignments/bulk",
    status_code=201,
    summary="Bulk assign fee to class/level",
    response_description="Bulk assignment results",
)
async def bulk_create_fee_assignments(
    body: FeeAssignmentBulkCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Bulk assign a fee structure to all students in a class or level.

    Provide class_id OR level (not both). Skips students who already have
    this fee assigned.
    """
    audit = AuditService(db)

    if not body.class_id and not body.level:
        raise ValidationError(
            "Either class_id or level must be provided",
            error_code="ERR-BIL-422",
        )

    # Validate fee structure
    fs_result = await db.execute(
        select(FeeStructure).where(FeeStructure.id == body.fee_structure_id)
    )
    fs = fs_result.scalar_one_or_none()
    if fs is None:
        raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
    verify_school_boundary(fs.school_id, auth)

    # Find student IDs
    student_ids: list[uuid.UUID] = []

    if body.class_id:
        # Validate class
        cls_result = await db.execute(select(Class).where(Class.id == body.class_id))
        cls = cls_result.scalar_one_or_none()
        if cls is None:
            raise NotFoundError("Class not found", error_code="ERR-BIL-404")
        verify_school_boundary(cls.school_id, auth)

        # Get enrolled students
        enroll_result = await db.execute(
            select(Enrollment.student_id).where(
                Enrollment.class_id == body.class_id,
                Enrollment.school_id == auth.school_id,
                Enrollment.status == "active",
            )
        )
        student_ids = list(enroll_result.scalars().all())

    elif body.level:
        # Find all classes at this level, then their students
        class_result = await db.execute(
            select(Class.id).where(
                Class.school_id == auth.school_id,
                Class.code.ilike(f"{body.level}%"),
            )
        )
        class_ids = list(class_result.scalars().all())
        if class_ids:
            enroll_result = await db.execute(
                select(Enrollment.student_id).where(
                    Enrollment.class_id.in_(class_ids),
                    Enrollment.school_id == auth.school_id,
                    Enrollment.status == "active",
                )
            )
            student_ids = list(enroll_result.scalars().all())

    if not student_ids:
        return success_response({
            "created": 0,
            "skipped": 0,
            "assignments": [],
        })

    # Get already-assigned student IDs
    existing_result = await db.execute(
        select(FeeAssignment.student_id).where(
            FeeAssignment.fee_structure_id == body.fee_structure_id,
            FeeAssignment.student_id.in_(student_ids),
        )
    )
    existing_ids = set(existing_result.scalars().all())

    # Create assignments for new students
    created = []
    for sid in student_ids:
        if sid in existing_ids:
            continue
        fa = FeeAssignment(
            fee_structure_id=body.fee_structure_id,
            student_id=sid,
            school_id=auth.school_id,
            discount_percent=body.discount_percent,
            discount_reason=body.discount_reason,
            status="ACTIVE",
        )
        db.add(fa)
        created.append(fa)

    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="fee_assignment.bulk_create",
        target_type="fee_assignment",
        outcome="success",
        entity_after={
            "fee_structure_id": str(body.fee_structure_id),
            "created": len(created),
            "skipped": len(existing_ids),
        },
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response({
        "created": len(created),
        "skipped": len(existing_ids),
        "assignments": [_fee_assignment_to_response(fa) for fa in created],
    })


# ---------------------------------------------------------------------------
# GET /billing/fee-assignments — List fee assignments
# ---------------------------------------------------------------------------
@router.get(
    "/fee-assignments",
    summary="List fee assignments",
    response_description="List of fee assignments",
)
async def list_fee_assignments(
    fee_structure_id: uuid.UUID | None = Query(None),
    student_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(ACTIVE|EXEMPTED|ARCHIVED)$"),
    auth: AuthContext = Depends(requires_permission("PERM-BIL:fee:read")),
    db: AsyncSession = Depends(get_db),
):
    """List fee assignments with optional filters.

    PAR can only see assignments for their own children.
    """
    query = select(FeeAssignment).where(FeeAssignment.school_id == auth.school_id)

    if fee_structure_id:
        query = query.where(FeeAssignment.fee_structure_id == fee_structure_id)
    if student_id:
        query = query.where(FeeAssignment.student_id == student_id)
    if status:
        query = query.where(FeeAssignment.status == status)

    # PAR: restrict to their children
    if auth.role == "PAR":
        child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
        if child_ids:
            query = query.where(FeeAssignment.student_id.in_(child_ids))
        else:
            return list_response([])

    query = query.order_by(FeeAssignment.created_at.desc())
    result = await db.execute(query)
    assignments = result.scalars().all()

    return list_response([_fee_assignment_to_response(fa) for fa in assignments])


# ---------------------------------------------------------------------------
# POST /billing/generate-invoices — Generate invoices from fee structure (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/generate-invoices",
    status_code=201,
    summary="Generate invoices from fee structure",
    response_description="Generated invoices summary",
)
async def generate_invoices(
    body: InvoiceGenerateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:generate")),
    db: AsyncSession = Depends(get_db),
):
    """Generate invoices for all active fee assignments of a fee structure.

    For each assigned student:
    1. Find their parent (via parent_child_links)
    2. Calculate amount after discount
    3. Create invoice + line item

    Skips students without a linked parent.
    Due dates must satisfy due_date >= issued_date.
    """
    audit = AuditService(db)

    if body.due_date < body.issued_date:
        raise ValidationError(
            "due_date must be on or after issued_date",
            error_code="ERR-BIL-422",
        )

    # Validate fee structure
    fs_result = await db.execute(
        select(FeeStructure).where(FeeStructure.id == body.fee_structure_id)
    )
    fs = fs_result.scalar_one_or_none()
    if fs is None:
        raise NotFoundError("Fee structure not found", error_code="ERR-BIL-404")
    verify_school_boundary(fs.school_id, auth)

    if fs.status != "ACTIVE":
        raise ValidationError(
            "Fee structure is not active",
            error_code="ERR-BIL-422",
        )

    # Get all active assignments for this fee structure
    assign_result = await db.execute(
        select(FeeAssignment).where(
            FeeAssignment.fee_structure_id == body.fee_structure_id,
            FeeAssignment.school_id == auth.school_id,
            FeeAssignment.status == "ACTIVE",
        )
    )
    assignments = assign_result.scalars().all()

    if not assignments:
        return success_response({
            "generated": 0,
            "skipped": 0,
            "total_amount": 0,
        })

    # Build student_id → parent_id map
    student_ids = [a.student_id for a in assignments]
    parent_link_result = await db.execute(
        select(ParentChildLink).where(
            ParentChildLink.child_user_id.in_(student_ids),
            ParentChildLink.school_id == auth.school_id,
            ParentChildLink.status == "active",
        )
    )
    parent_links = parent_link_result.scalars().all()
    student_to_parent: dict[uuid.UUID, uuid.UUID] = {}
    for link in parent_links:
        # First parent found for each student
        if link.child_user_id not in student_to_parent:
            student_to_parent[link.child_user_id] = link.parent_user_id

    generated = 0
    skipped = 0
    total_generated_amount = 0.0

    for assignment in assignments:
        parent_id = student_to_parent.get(assignment.student_id)
        if parent_id is None:
            skipped += 1
            continue

        # Calculate amount after discount
        base_amount = float(fs.amount)
        if assignment.discount_percent:
            discount = base_amount * float(assignment.discount_percent) / 100
            final_amount = round(base_amount - discount, 2)
        else:
            final_amount = base_amount

        if final_amount <= 0:
            skipped += 1
            continue

        # Create invoice
        invoice = Invoice(
            school_id=auth.school_id,
            parent_id=parent_id,
            period_id=body.period_id,
            status="pending",
            total_amount=final_amount,
            currency=fs.currency,
            issued_date=body.issued_date,
            due_date=body.due_date,
            fee_structure_id=fs.id,
        )
        db.add(invoice)
        await db.flush()

        # Create line item
        description = fs.name
        if assignment.discount_percent:
            description += f" (remise {float(assignment.discount_percent):.0f}%)"

        item = InvoiceItem(
            invoice_id=invoice.id,
            description=description,
            amount=final_amount,
            unit_price=base_amount,
            quantity=1,
        )
        db.add(item)

        generated += 1
        total_generated_amount += final_amount

    await db.flush()

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="invoice.generate_from_fees",
        target_type="fee_structure",
        target_id=fs.id,
        outcome="success",
        entity_after={
            "fee_structure_id": str(fs.id),
            "generated": generated,
            "skipped": skipped,
            "total_amount": total_generated_amount,
        },
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response({
        "generated": generated,
        "skipped": skipped,
        "total_amount": total_generated_amount,
        "currency": fs.currency,
    })
