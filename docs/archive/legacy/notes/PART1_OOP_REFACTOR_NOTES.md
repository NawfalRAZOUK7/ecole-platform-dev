# Part 1 OOP Refactor Notes

This document summarizes the completed Part 1 OOP refactor work for the Ecole Platform backend.

It covers:
- what was implemented across OOP prompts `A1` through `F1`;
- the major code areas changed;
- implementation decisions that were taken during execution but were not stated explicitly in the prompts or checklist;
- environment notes that matter before starting Part 2 enhancements.

## Status

Part 1 is complete through:
- `OOP-A1` Value Objects
- `OOP-A2` UnitOfWork for core services
- `OOP-A3` UnitOfWork rollout across write services
- `OOP-B1` Profile models + G26 migration
- `OOP-B2` ProfileLoader
- `OOP-C1` Domain event classes
- `OOP-C2` Delivery strategies + dispatcher
- `OOP-C3` Event wiring into services
- `OOP-D1` Evaluatable protocol + grading strategies
- `OOP-D2` StudentWork service + routes
- `OOP-E1` LMS service split
- `OOP-F1` validation

## What Was Implemented

### 1. Domain Layer

Created `backend/app/domain/` with:
- `value_objects/`
- `events/`
- `protocols/`

Implemented value objects:
- `MoroccanGrade`
- `Money`
- `TypedId`
- `RoleSet`

Implemented domain event modules:
- `base.py`
- `lms.py`
- `calendar.py`
- `billing.py`
- `documents.py`
- `auth.py`

Implemented protocol layer:
- `Evaluatable`
- `GradingStrategy`
- `QuizAutoGradeStrategy`
- `ManualGradeStrategy`

### 2. Unit of Work Rollout

Introduced `backend/app/core/unit_of_work.py`.

Migrated service-layer writes away from direct `db.commit()` / `db.rollback()` usage toward:

```python
async with UnitOfWork(self.db) as uow:
    ...
    await uow.commit()
```

This was applied to write-heavy services including LMS, auth, billing, ERP, notifications, documents, content library, communication, reports, admin, profile-related services, and supporting delivery services.

### 3. Profile System

Added profile models for:
- `AdminProfile`
- `ContentManagerProfile`

Added G26 migration:
- creates `admin_profiles`
- creates `content_manager_profiles`

Implemented:
- `backend/app/repositories/profile_loader.py`
- `backend/app/services/profile_loader.py`

### 4. Domain Event Delivery

Implemented delivery infrastructure:
- `backend/app/services/event_dispatcher.py`
- `backend/app/services/delivery/base.py`
- `backend/app/services/delivery/push.py`
- `backend/app/services/delivery/email_delivery.py`
- `backend/app/services/delivery/sms_delivery.py`
- `backend/app/services/delivery/in_app.py`

Updated notification repository support for domain-delivery workflows, including idempotency support and delivery persistence.

### 5. Event Wiring

Services now emit domain events after successful commits.

Confirmed emitting services include:
- auth
- billing
- calendar
- student documents
- resource library
- LMS

### 6. Evaluatable + Unified Student Work

Repositories aligned to the `Evaluatable` protocol:
- `QuizRepository`
- `AssignmentRepository`
- `AssessmentRepository`

Implemented:
- `backend/app/services/student_work.py`
- `backend/app/schemas/student_work.py`

Added routes:
- `GET /student-work`
- `GET /student-work/class/{class_id}`

### 7. LMS Split

Replaced monolithic `backend/app/services/lms.py` with:
- `backend/app/services/lms/course_service.py`
- `backend/app/services/lms/assignment_service.py`
- `backend/app/services/lms/quiz_service.py`
- `backend/app/services/lms/content_service.py`
- `backend/app/services/lms/progress_service.py`
- `backend/app/services/lms/_helpers.py`
- `backend/app/services/lms/__init__.py`

Updated routers to use specific sub-services instead of the old monolith:
- `courses.py`
- `assignments.py`
- `submissions.py`
- `quizzes.py`
- `content.py`
- `content_library.py`
- `results.py`
- `progress.py`
- `assessments.py`
- `activities.py`

## Decisions Taken During Implementation

These were important execution decisions that were not spelled out clearly in the prompts/checklist.

### 1. The existing 3-tier architecture was preserved

The OOP refactor was implemented inside the existing `Router -> Service -> Repository` structure.

It did not replace the architecture with a domain-first application layer. Instead:
- routers still call services;
- services still coordinate repositories;
- OOP additions were layered into the service/domain boundary.

### 2. `DIR` shares the admin profile type

`ProfileLoader` maps:
- `ADM -> admin`
- `DIR -> admin`

This means director users use the admin-profile shape rather than a separate director profile model.

This was chosen because:
- prompts required 5 role-profile types for the loader;
- no separate director profile model was specified;
- existing role system already groups director/admin behavior in multiple places.

### 3. Nested UnitOfWork compatibility was handled with `_uow_depth`

`UnitOfWork` stores transaction depth in `session.info["_uow_depth"]`.

Some helper services now detect that flag and reuse the current transaction instead of opening a new write boundary.

This matters for:
- profile creation helpers;
- notifications and reminders;
- document workflows;
- resource library flows;
- other nested service-to-service writes.

The goal was to avoid accidental nested write conflicts while keeping existing method signatures unchanged.

### 4. Domain event idempotency intentionally ignores `event_id` and `occurred_at`

In `services/delivery/base.py`, the event fingerprint used for notification idempotency excludes:
- `event_id`
- `occurred_at`

This was deliberate.

Reason:
- those two fields are generated per event instance;
- including them would make logically identical redeliveries look unique;
- excluding them makes retries/double-dispatch protection stable.

### 5. Event-driven delivery did not remove all safety fallbacks

For a few flows, legacy fallbacks were intentionally kept after event wiring.

Examples:
- grade-published fallback email path in LMS grading;
- limited fallback notification behavior in document-related flows.

Reason:
- prompts required event wiring, but removing every old path in one pass would have raised regression risk;
- fallback behavior was kept only where it materially reduced delivery risk during transition.

### 6. Document-expiring delivery is emitted once per document, not once per recipient

The document expiration workflow was normalized so one domain event represents one document-expiry occurrence.

Recipients are resolved by the dispatcher/delivery layer.

Reason:
- prevents duplicate domain notifications;
- matches the event model better;
- works correctly with idempotency keys.

### 7. Nested document events are buffered when invoked inside outer write flows

Document-related nested operations can stash pending domain events in session info and let the outer service dispatch them after the final commit.

This was used to avoid:
- dispatching before the outer transaction is durable;
- partial nested side effects;
- double sends in library/document orchestration.

### 8. `StudentWork` lives in the existing content router module

The `student_work_router` was added to `backend/app/api/v1/content.py` instead of creating a separate router file.

Reason:
- prompt allowed “add endpoints to `content.py` (or create a new router)”;
- this kept LMS content-related routing consolidated;
- reduced router churn while still registering a distinct `/student-work` prefix.

### 9. `StudentWork` uses direct response models, not the standard envelope

The new student-work endpoints return `StudentWorkListResponse` directly, not `success_response(...)` or `list_response(...)`.

Reason:
- the prompt explicitly required both endpoints to return `StudentWorkListResponse`;
- changing that shape back into the global response envelope would have violated the prompt more than it would help consistency.

### 10. Teacher ownership for `/student-work/class/{class_id}` is enforced in the router

The class ownership check was done with:
- `get_teacher_class_ids(...)`
- `verify_teacher_assignment(...)`

at the router boundary before calling `StudentWorkService`.

Reason:
- keeps `StudentWorkService` repository-driven and free of direct auth-specific DB lookups;
- matches the prompt’s requirement without expanding service responsibilities.

### 11. Existing dashboard progress logic was not reimplemented inside LMS

There was already an existing `backend/app/services/progress.py` service before the LMS split.

Instead of duplicating that logic, the new `backend/app/services/lms/progress_service.py`:
- owns LMS assessment/result responsibilities from the old monolith;
- delegates dashboard-style progress methods to the existing `app.services.progress.ProgressService`.

Reason:
- prompt required an LMS split, but the project already had a dedicated progress service;
- duplicating progress logic would have created divergence risk;
- delegation preserved behavior and kept the new LMS split coherent.

### 12. A backward-compatible `LMSService` facade was retained

`backend/app/services/lms/__init__.py` exports:
- `CourseService`
- `AssignmentService`
- `QuizService`
- `ContentService`
- `ProgressService`
- `LMSService`

`LMSService` is now a facade that delegates via `__getattr__`.

Reason:
- routers were moved to specific services as required;
- retaining the facade avoids breaking any non-router imports or future transitional references.

### 13. The “under 500 lines” constraint was applied to sub-service files, not `_helpers.py`

The five public LMS sub-services were kept under 500 lines.

Shared behavior was moved into `_helpers.py`, which is larger than 500 lines.

Reason:
- the prompt specifically constrained sub-services;
- centralizing repeated serializer/read/dispatch helper logic prevented duplicate code and kept the public service files within the requested limit.

## Validation Outcome

Part 1 validation passed for:
- UnitOfWork usage
- value object presence and runtime validation
- profile models + G26 migration
- ProfileLoader role coverage
- domain event presence
- dispatcher registry presence
- multi-service event emission
- Evaluatable compatibility
- StudentWork presence and route registration
- LMS split and router rewiring

## Environment / Dependency Note

No changes were required to:
- `backend/requirements.txt`
- `backend/requirements-dev.txt`

Reason:
- the needed packages were already declared there;
- the import-health failure came from using the global interpreter instead of the project virtual environment.

Confirmed present in `backend/.venv`:
- `sqlalchemy`
- `fastapi`
- `pydantic`

### Correct backend interpreter for verification

Use:

```bash
cd backend
.venv/bin/python -c "..."
```

or activate the venv first.

Do not rely on the system `python3` for backend verification unless that interpreter is explicitly the same environment.

## Recommended Operating Notes Before Part 2

1. Keep using `backend/.venv/bin/python` for all import checks, scripts, and targeted verification.
2. Preserve the current response shapes of existing endpoints; Part 2 should not accidentally re-envelope or reshape existing APIs.
3. Continue using `UnitOfWork` for every write path added in enhancements.
4. When new features trigger notifications, prefer domain events + dispatcher instead of direct notification creation unless a prompt explicitly requires otherwise.
5. If a new enhancement touches LMS, work against the split package in `backend/app/services/lms/`, not against a recreated monolithic service.
