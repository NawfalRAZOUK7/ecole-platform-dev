# OOP Refactor Checklist — Ecole Platform

> Track progress as you execute OOP_REFACTOR_PROMPTS.md.
> Mark items [x] as you complete each prompt.

---

## Phase OOP-A: Foundation Layer

### OOP-A1: Value Objects
- [ ] Created backend/app/domain/ directory
- [ ] Created backend/app/domain/value_objects/ directory
- [ ] Created backend/app/domain/events/ directory
- [ ] Created backend/app/domain/protocols/ directory
- [ ] Created __init__.py files in all domain directories
- [ ] Created MoroccanGrade (grade.py) — validates 0-20, has mention property
- [ ] Created Money (money.py) — validates non-negative, MAD currency
- [ ] Created UserId + SchoolId (typed_id.py)
- [ ] Created RoleSet (role_set.py) — validates 8 roles
- [ ] **Review & commit myself**

### OOP-A2: UnitOfWork (Core Services)
- [ ] Created backend/app/core/unit_of_work.py
- [ ] Updated auth.py — register() uses UoW
- [ ] Updated auth.py — login() uses UoW
- [ ] Updated billing.py — create_invoice uses UoW
- [ ] Updated billing.py — process_payment uses UoW
- [ ] Updated erp.py — create_enrollment uses UoW
- [ ] Updated erp.py — batch_attendance uses UoW
- [ ] Verified no direct db.commit() in updated methods
- [ ] **Review & commit myself**

### OOP-A3: UnitOfWork (All Services)
- [ ] Updated admin.py with UoW
- [ ] Updated ai.py with UoW
- [ ] Updated audit.py with UoW
- [ ] Updated calendar.py with UoW
- [ ] Updated cms.py with UoW
- [ ] Updated communication.py with UoW
- [ ] Updated data_export.py with UoW
- [ ] Updated email_digest.py with UoW
- [ ] Updated feature.py with UoW
- [ ] Updated gdpr.py with UoW
- [ ] Updated lms.py with UoW
- [ ] Updated notification_hub.py with UoW
- [ ] Updated overdue_reminders.py with UoW
- [ ] Updated payment_retry.py with UoW
- [ ] Updated profile.py with UoW
- [ ] Updated progress.py with UoW
- [ ] Updated push_config.py with UoW
- [ ] Updated quiz_grading.py with UoW
- [ ] Updated realtime.py with UoW
- [ ] Updated reminders.py with UoW
- [ ] Updated reports.py with UoW
- [ ] Updated resource_library.py with UoW
- [ ] Updated rsvp.py with UoW
- [ ] Updated student_documents.py with UoW
- [ ] Zero db.commit() calls remain in services (only uow.commit)
- [ ] **Review & commit myself**

---

## Phase OOP-B: Profile System

### OOP-B1: Profile Models + Migration
- [ ] Added AdminProfile model to iam.py
- [ ] Added ContentManagerProfile model to iam.py
- [ ] Updated models/__init__.py with new exports
- [ ] Created Alembic migration g26_oop_profiles
- [ ] Migration creates admin_profiles table
- [ ] Migration creates content_manager_profiles table
- [ ] Migration adds correct indexes
- [ ] **Review & commit myself**

### OOP-B2: ProfileLoader
- [ ] Created repositories/profile_loader.py
- [ ] Created services/profile_loader.py
- [ ] Updated auth.py to use ProfileLoader on register
- [ ] Updated auth.py to use ProfileLoader on /me
- [ ] Updated profile.py to use ProfileLoader
- [ ] Updated repositories/__init__.py
- [ ] **Review & commit myself**

---

## Phase OOP-C: Domain Events

### OOP-C1: Event Classes
- [ ] Created domain/events/base.py (DomainEvent)
- [ ] Created domain/events/lms.py (5 events)
- [ ] Created domain/events/calendar.py (4 events)
- [ ] Created domain/events/billing.py (3 events)
- [ ] Created domain/events/documents.py (3 events)
- [ ] Created domain/events/auth.py (3 events)
- [ ] Updated domain/events/__init__.py with all exports
- [ ] **Review & commit myself**

### OOP-C2: Delivery Strategies
- [ ] Created services/delivery/ directory
- [ ] Created delivery/base.py (DeliveryStrategy ABC)
- [ ] Created delivery/push.py (PushDeliveryStrategy)
- [ ] Created delivery/email_delivery.py (EmailDeliveryStrategy)
- [ ] Created delivery/sms_delivery.py (SMSDeliveryStrategy)
- [ ] Created delivery/in_app.py (InAppDeliveryStrategy)
- [ ] Created services/event_dispatcher.py
- [ ] Registered all events in EVENT_HANDLERS
- [ ] **Review & commit myself**

### OOP-C3: Wire Events into Services
- [ ] lms.py emits GradePublished
- [ ] lms.py emits AssignmentCreated
- [ ] lms.py emits QuizCompleted
- [ ] lms.py emits SubmissionReceived
- [ ] calendar.py emits EventCreated
- [ ] calendar.py emits EventUpdated
- [ ] billing.py emits InvoiceGenerated
- [ ] billing.py emits PaymentReceived/Failed
- [ ] student_documents.py emits DocumentExpiring
- [ ] resource_library.py emits ResourceShared
- [ ] auth.py emits UserRegistered
- [ ] Existing notification calls kept as fallback (marked TODO)
- [ ] **Review & commit myself**

---

## Phase OOP-D: Evaluatable Protocol

### OOP-D1: Protocols + Strategies
- [ ] Created domain/protocols/evaluatable.py
- [ ] Created domain/protocols/grading.py
- [ ] QuizAutoGradeStrategy implemented
- [ ] ManualGradeStrategy implemented
- [ ] QuizRepository satisfies Evaluatable
- [ ] Assignment repo methods satisfy Evaluatable
- [ ] Assessment repo methods satisfy Evaluatable
- [ ] **Review & commit myself**

### OOP-D2: StudentWork Service
- [ ] Created services/student_work.py
- [ ] Created schemas/student_work.py
- [ ] Added GET /student-work endpoint
- [ ] Added GET /student-work/class/{class_id} endpoint
- [ ] Registered in router.py
- [ ] Added permissions
- [ ] **Review & commit myself**

---

## Phase OOP-E: LMS Split

### OOP-E1: Split lms.py
- [ ] Created services/lms/ directory
- [ ] Created lms/course_service.py
- [ ] Created lms/assignment_service.py
- [ ] Created lms/quiz_service.py
- [ ] Created lms/content_service.py
- [ ] Created lms/progress_service.py
- [ ] Created lms/_helpers.py (shared functions)
- [ ] Created lms/__init__.py (re-exports)
- [ ] Updated courses.py router
- [ ] Updated assignments.py router
- [ ] Updated submissions.py router
- [ ] Updated quizzes.py router
- [ ] Updated content.py router
- [ ] Updated content_library.py router
- [ ] Updated results.py router
- [ ] Updated progress.py router
- [ ] Updated assessments.py router
- [ ] Updated activities.py router
- [ ] Deleted original services/lms.py
- [ ] Each sub-service under 500 lines
- [ ] **Review & commit myself**

---

## Phase OOP-F: Validation

### OOP-F1: Full Validation
- [ ] Zero db.commit() in services (only uow.commit)
- [ ] All value objects validate correctly
- [ ] Both new profile tables exist in migration
- [ ] ProfileLoader works for 5 role types
- [ ] All domain event files exist
- [ ] EventDispatcher has all events registered
- [ ] 5+ services emit events
- [ ] All 3 repos satisfy Evaluatable protocol
- [ ] StudentWorkService combines all types
- [ ] /student-work endpoint registered
- [ ] LMS split into 5 sub-services
- [ ] All router imports resolve
- [ ] All import health checks pass
- [ ] **Review & commit myself**
