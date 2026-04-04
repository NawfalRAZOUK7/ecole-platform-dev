"""RBAC permission catalog — data-driven mapping of PERM-* codes to roles.

Reference: S-034 — RBAC permission middleware, Pack C6 — complete permission catalog.
Format: PERM-{DOMAIN}:{resource}:{action}
Roles: ADM, DIR, TCH, EDUCATOR, PAR, STD, SUP, SYS, CONTENT_MGR, PUBLIC

This module is the single source of truth for which roles hold which permissions.
Permissions can be updated without code deployment by modifying the ROLE_PERMISSIONS dict.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Role constants (match RoleCode enum in models/iam.py)
# ---------------------------------------------------------------------------
ADM = "ADM"
DIR = "DIR"
TCH = "TCH"
EDUCATOR = "EDUCATOR"
PAR = "PAR"
STD = "STD"
SUP = "SUP"
SYS = "SYS"
CONTENT_MGR = "CONTENT_MGR"  # Platform-wide content manager (not school-scoped)
PUBLIC = "PUBLIC"  # pseudo-role for unauthenticated entry endpoints

PLATFORM_ROLES: set[str] = {SUP, SYS, CONTENT_MGR}

# ---------------------------------------------------------------------------
# Permission constants — organised by domain
# ---------------------------------------------------------------------------

# IAM
PERM_IAM_SESSION_CREATE = "PERM-IAM:session:create"
PERM_IAM_SESSION_REFRESH = "PERM-IAM:session:refresh"
PERM_IAM_SESSION_REVOKE = "PERM-IAM:session:revoke"
PERM_IAM_SESSION_LIST = "PERM-IAM:session:list"  # Phase 2A
PERM_IAM_PASSWORD_CHANGE = "PERM-IAM:password:change"  # Phase 2A
PERM_IAM_INVITE_CREATE = "PERM-IAM:invite:create"
PERM_IAM_INVITE_CONSUME = "PERM-IAM:invite:consume"
PERM_IAM_INVITE_REVOKE = "PERM-IAM:invite:revoke"
PERM_IAM_RECOVERY_REQUEST = "PERM-IAM:recovery:request"
PERM_IAM_RECOVERY_VERIFY = "PERM-IAM:recovery:verify"
PERM_IAM_RECOVERY_RESET = "PERM-IAM:recovery:reset"
PERM_IAM_PARENT_LINK_CREATE = "PERM-IAM:parent-link:create"
PERM_IAM_PARENT_LINK_READ = "PERM-IAM:parent-link:read"
PERM_IAM_PARENT_LINK_DELETE = "PERM-IAM:parent-link:delete"
PERM_IAM_LOGIN_HISTORY_READ = "PERM-IAM:login-history:read"

# Admin
PERM_ADM_DASHBOARD_READ = "PERM-ADM:dashboard:read"
PERM_ADM_USER_READ = "PERM-ADM:user:read"
PERM_ADM_USER_CREATE = "PERM-ADM:user:create"
PERM_ADM_USER_MANAGE = "PERM-ADM:user:manage"
PERM_ADM_INVITATION_READ = "PERM-ADM:invitation:read"
PERM_ADM_AUDIT_READ = "PERM-ADM:audit:read"
PERM_ADM_IMPERSONATE = "PERM-ADM:impersonation:create"
PERM_ADM_SCHOOL_MANAGE = "PERM-ADM:school:manage"
PERM_ADM_SCHOOL_READ = "PERM-ADM:school:read"
PERM_ADM_SETTINGS_READ = "PERM-ADM:settings:read"
PERM_ADM_SETTINGS_UPDATE = "PERM-ADM:settings:update"
PERM_ADM_ANNOUNCEMENT_MANAGE = "PERM-ADM:announcement:manage"
PERM_ADM_PLATFORM_STATS = "PERM-ADM:platform-stats:read"

# Profiles / GDPR
PERM_PROF_ADMIN_READ = "PERM-PROF:profile-admin:read"
PERM_PROF_CHILD_READ = "PERM-PROF:child:read"
PERM_GDPR_DATA_DELETE = "PERM-GDPR:data-deletion:create"
PERM_GDPR_CONSENT_MANAGE = "PERM-GDPR:consent:manage"

# ERP
PERM_ERP_SCHOOL_READ = "PERM-ERP:school:read"
PERM_ERP_CLASS_READ = "PERM-ERP:class:read"
PERM_ERP_ENROLLMENT_READ = "PERM-ERP:enrollment:read"
PERM_ERP_ENROLLMENT_ASSIGN = "PERM-ERP:enrollment:assign"
PERM_ERP_ASSIGNMENT_UPDATE = "PERM-ERP:assignment:update"
PERM_ERP_ATTENDANCE_READ = "PERM-ERP:attendance:read"
PERM_ERP_ATTENDANCE_MARK = "PERM-ERP:attendance:mark"
PERM_ERP_ABSENCE_JUSTIFY = "PERM-ERP:absence:justify"
PERM_ERP_ABSENCE_REVIEW = "PERM-ERP:absence:review"
PERM_ERP_ATTENDANCE_ANALYTICS_READ = "PERM-ERP:attendance-analytics:read"
PERM_ERP_ATTENDANCE_ALERT_MANAGE = "PERM-ERP:attendance-alert:manage"

# ERP — Timetable (Phase 11A)
PERM_ERP_TIMETABLE_CREATE = "PERM-ERP:timetable:create"
PERM_ERP_TIMETABLE_READ = "PERM-ERP:timetable:read"
PERM_ERP_TIMETABLE_UPDATE = "PERM-ERP:timetable:update"
PERM_ERP_TIMETABLE_DELETE = "PERM-ERP:timetable:delete"
PERM_ERP_TIMETABLE_GENERATE = "PERM-ERP:timetable:generate"
PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE = "PERM-ERP:timetable-constraint:manage"
PERM_ERP_TIMETABLE_EXCEPTION_CREATE = "PERM-ERP:timetable-exception:create"
PERM_ERP_TIMETABLE_EXCEPTION_READ = "PERM-ERP:timetable-exception:read"

# LMS
PERM_LMS_COURSE_READ = "PERM-LMS:course:read"
PERM_LMS_COURSE_PUBLISH = "PERM-LMS:course:publish"
PERM_LMS_ASSIGNMENT_CREATE = "PERM-LMS:assignment:create"
PERM_LMS_SUBMISSION_CREATE = "PERM-LMS:submission:create"
PERM_LMS_SUBMISSION_GRADE = "PERM-LMS:submission:grade"
PERM_LMS_SUBMISSION_FILE_UPLOAD = "PERM-LMS:submission-file:upload"
PERM_LMS_SUBMISSION_FILE_READ = "PERM-LMS:submission-file:read"
PERM_LMS_CONTENT_ASSET_UPLOAD = "PERM-LMS:content-asset:upload"
PERM_LMS_CONTENT_ASSET_READ = "PERM-LMS:content-asset:read"
PERM_LMS_CONTENT_ASSET_DELETE = "PERM-LMS:content-asset:delete"
PERM_LMS_RESULT_READ = "PERM-LMS:result:read"
PERM_LMS_CONTENT_READ = "PERM-LMS:content:read"
PERM_LMS_CONTENT_PROGRESS_WRITE = "PERM-LMS:content-progress:write"
PERM_LMS_ACTIVITY_SESSION_CREATE = "PERM-LMS:activity-session:create"
PERM_LMS_ACTIVITY_SESSION_COMPLETE = "PERM-LMS:activity-session:complete"
PERM_LMS_ASSESSMENT_CREATE = "PERM-LMS:assessment:create"
PERM_LMS_ASSESSMENT_READ = "PERM-LMS:assessment:read"
PERM_LMS_ASSESSMENT_PUBLISH = "PERM-LMS:assessment:publish"
PERM_LMS_ASSESSMENT_SUBMIT = "PERM-LMS:assessment:submit"
PERM_LMS_RUBRIC_CREATE = "PERM-LMS:rubric:create"
PERM_LMS_RUBRIC_READ = "PERM-LMS:rubric:read"
PERM_LMS_GRADEBOOK_MANAGE = "PERM-LMS:gradebook:manage"
PERM_LMS_GRADEBOOK_READ = "PERM-LMS:gradebook:read"
PERM_LMS_QUESTION_BANK_MANAGE = "PERM-LMS:question-bank:manage"
PERM_LMS_QUESTION_BANK_READ = "PERM-LMS:question-bank:read"

# Billing
PERM_BIL_INVOICE_READ = "PERM-BIL:invoice:read"
PERM_BIL_INVOICE_VOID = "PERM-BIL:invoice:void"
PERM_BIL_PAYMENT_INITIATE = "PERM-BIL:payment:initiate"
PERM_BIL_PAYMENT_READ = "PERM-BIL:payment:read"
PERM_BIL_PAYMENT_RECONCILE = "PERM-BIL:payment:reconcile"
PERM_BIL_PROOF_READ = "PERM-BIL:proof:read"

# Billing — Fee Structures (Phase 11B)
PERM_BIL_FEE_CREATE = "PERM-BIL:fee:create"
PERM_BIL_FEE_READ = "PERM-BIL:fee:read"
PERM_BIL_FEE_UPDATE = "PERM-BIL:fee:update"
PERM_BIL_FEE_STRUCTURE_CREATE = PERM_BIL_FEE_CREATE
PERM_BIL_FEE_STRUCTURE_UPDATE = PERM_BIL_FEE_UPDATE
PERM_BIL_FEE_STRUCTURE_DELETE = "PERM-BIL:fee:delete"
PERM_BIL_FEE_ASSIGN = "PERM-BIL:fee:assign"
PERM_BIL_INVOICE_GENERATE = "PERM-BIL:invoice:generate"
PERM_BIL_SIBLING_POLICY_MANAGE = "PERM-BIL:sibling-policy:manage"
PERM_BIL_DISCOUNT_MANAGE = PERM_BIL_SIBLING_POLICY_MANAGE
PERM_BIL_LATE_FEE_MANAGE = "PERM-BIL:late-fee:manage"
PERM_BIL_PAYMENT_PLAN_CREATE = "PERM-BIL:payment-plan:create"
PERM_BIL_PAYMENT_PLAN_READ = "PERM-BIL:payment-plan:read"
PERM_BIL_PAYMENT_PLAN_MANAGE = "PERM-BIL:payment-plan:manage"

# Billing — Enhancement aliases (ENH-C1 architecture naming)
PERM_BILLING_SIBLING_POLICY_MANAGE = PERM_BIL_SIBLING_POLICY_MANAGE
PERM_BILLING_LATE_FEE_MANAGE = PERM_BIL_LATE_FEE_MANAGE
PERM_BILLING_PAYMENT_PLAN_CREATE = PERM_BIL_PAYMENT_PLAN_CREATE
PERM_BILLING_PAYMENT_PLAN_READ = PERM_BIL_PAYMENT_PLAN_READ

# COM
PERM_COM_CONSENT_UPDATE = "PERM-COM:consent:update"
PERM_COM_NOTIFICATION_READ = "PERM-COM:notification:read"
PERM_COM_NOTIFICATION_BATCH_CREATE = "PERM-COM:notification:batch-create"
PERM_COM_MESSAGE_SEND = "PERM-COM:message:send"
PERM_COM_STD_MESSAGE_SEND = "com:std_message:send"
PERM_COM_STD_MESSAGE_READ = "com:std_message:read"

# Progress (Phase 11D)
PERM_PROGRESS_READ = "PERM-LMS:progress:read"
PERM_PROGRESS_CLASS_READ = "PERM-LMS:progress:class-read"

# COM — Messaging & Announcements (Phase 11C)
PERM_COM_CONVERSATION_CREATE = "PERM-COM:conversation:create"
PERM_COM_CONVERSATION_READ = "PERM-COM:conversation:read"
PERM_COM_ANNOUNCEMENT_CREATE = "PERM-COM:announcement:create"
PERM_COM_ANNOUNCEMENT_READ = "PERM-COM:announcement:read"
PERM_COM_ANNOUNCEMENT_PUBLISH = "PERM-COM:announcement:publish"

# IA (P1 — included for completeness)
PERM_IA_REQUEST_CREATE = "PERM-IA:request:create"
PERM_IA_REQUEST_READ = "PERM-IA:request:read"
PERM_IA_PREFERENCE_UPDATE = "PERM-IA:preference:update"
PERM_IA_REQUEST_OVERRIDE = "PERM-IA:request:override"
PERM_IA_WRITING_ATTEMPT_CREATE = "PERM-IA:writing-attempt:create"
PERM_IA_WRITING_ATTEMPT_REVIEW = "PERM-IA:writing-attempt:review"
PERM_IA_RECOMMENDATION_READ = "PERM-IA:recommendation:read"

# CMS (Phase 9A — Content Library)
PERM_CMS_CONTENT_CREATE = "PERM-CMS:content:create"
PERM_CMS_CONTENT_PUBLISH = "PERM-CMS:content:publish"
PERM_CMS_CONTENT_MANAGE = "PERM-CMS:content:manage"
PERM_CMS_CONTENT_DELETE = "PERM-CMS:content:delete"
PERM_CMS_CONTENT_ANALYTICS = "PERM-CMS:content:analytics"
PERM_CMS_CONTENT_REVIEW = "PERM-CMS:content:review"
PERM_CMS_CONTENT_ASSIGN = "PERM-CMS:content:assign"
PERM_CMS_CONTENT_SUBMIT = "PERM-CMS:content:submit"

# Quiz (Phase 9B — Quiz Engine)
PERM_QUIZ_CREATE = "PERM-QUIZ:quiz:create"
PERM_QUIZ_READ = "PERM-QUIZ:quiz:read"
PERM_QUIZ_MANAGE = "PERM-QUIZ:quiz:manage"
PERM_QUIZ_PUBLISH = "PERM-QUIZ:quiz:publish"
PERM_QUIZ_ATTEMPT = "PERM-QUIZ:quiz:attempt"
PERM_QUIZ_ANALYTICS = "PERM-QUIZ:quiz:analytics"

# Feature Toggles (Phase 11E)
PERM_SYS_FEATURE_MANAGE = "PERM-SYS:feature:manage"

# Reporting & Analytics (Phase 14)
PERM_REP_REPORT_GENERATE = "PERM-REP:report:generate"
PERM_REP_REPORT_READ = "PERM-REP:report:read"
PERM_RPT_REPORT_READ = PERM_REP_REPORT_READ
PERM_REP_ANALYTICS_READ = "PERM-REP:analytics:read"
PERM_REP_EXPORT_CREATE = "PERM-REP:export:create"
PERM_RPT_SCHEDULE_MANAGE = "PERM-RPT:schedule:manage"

# Calendar & Events (Phase 15)
PERM_CAL_EVENT_CREATE = "PERM-CAL:event:create"
PERM_CAL_EVENT_READ = "PERM-CAL:event:read"
PERM_CAL_EVENT_UPDATE = "PERM-CAL:event:update"
PERM_CAL_EVENT_DELETE = "PERM-CAL:event:delete"
PERM_CAL_HOLIDAY_MANAGE = "PERM-CAL:holiday:manage"
PERM_CAL_RSVP_RESPOND = "PERM-CAL:event-rsvp:respond"
PERM_CAL_RSVP_READ = "PERM-CAL:event-rsvp:read"

# Document management (Phase 16)
PERM_DOC_DOCUMENT_UPLOAD = "PERM-DOC:document:upload"
PERM_DOC_DOCUMENT_READ = "PERM-DOC:document:read"
PERM_DOC_DOCUMENT_DELETE = "PERM-DOC:document:delete"
PERM_DOC_STUDENT_DOCUMENT_LINK = "PERM-DOC:student-document:link"
PERM_DOC_RESOURCE_CREATE = "PERM-DOC:resource:create"
PERM_DOC_RESOURCE_READ = "PERM-DOC:resource:read"
PERM_DOC_RESOURCE_UPDATE = "PERM-DOC:resource:update"
PERM_DOC_RESOURCE_DELETE = "PERM-DOC:resource:delete"
PERM_DOC_RESOURCE_MANAGE = "PERM-DOC:resource:manage"
PERM_DOC_RESOURCE_RATE = "PERM-DOC:resource:rate"
PERM_DOC_REQUIREMENT_MANAGE = "PERM-DOC:requirement:manage"
PERM_DOC_BULK_DOWNLOAD = "PERM-DOC:document-bulk:download"
PERM_DOC_BULK_DELETE = "PERM-DOC:document-bulk:delete"

# Micro-school
PERM_MICRO_SCHOOL_CREATE = "PERM-MICRO:school:create"
PERM_MICRO_SCHOOL_READ = "PERM-MICRO:school:read"
PERM_MICRO_SCHOOL_MANAGE = "PERM-MICRO:school:manage"
PERM_MICRO_GROUP_CREATE = "PERM-MICRO:group:create"
PERM_MICRO_GROUP_READ = "PERM-MICRO:group:read"
PERM_MICRO_ENROLLMENT_CREATE = "PERM-MICRO:enrollment:create"
PERM_MICRO_ENROLLMENT_READ = "PERM-MICRO:enrollment:read"
PERM_MICRO_PAYMENT_CREATE = "PERM-MICRO:payment:create"
PERM_MICRO_PAYMENT_READ = "PERM-MICRO:payment:read"
PERM_MICRO_RESOURCE_READ = "PERM-MICRO:resource:read"
PERM_MICRO_RESOURCE_MANAGE = "PERM-MICRO:resource:manage"
PERM_MICRO_PROGRESS_CREATE = "PERM-MICRO:progress:create"
PERM_MICRO_PROGRESS_READ = "PERM-MICRO:progress:read"

# Class micro-budget
PERM_BUDGET_CREATE = "PERM-BUDGET:budget:create"
PERM_BUDGET_READ = "PERM-BUDGET:budget:read"
PERM_BUDGET_MANAGE = "PERM-BUDGET:budget:manage"
PERM_BUDGET_ALLOCATE = "PERM-BUDGET:allocation:allocate"
PERM_BUDGET_REQUEST_CREATE = "PERM-BUDGET:request:create"
PERM_BUDGET_REQUEST_READ = "PERM-BUDGET:request:read"
PERM_BUDGET_APPROVE = "PERM-BUDGET:request:approve"
PERM_BUDGET_TRANSACTION_CREATE = "PERM-BUDGET:transaction:create"
PERM_BUDGET_TRANSACTION_READ = "PERM-BUDGET:transaction:read"
PERM_BUDGET_ANALYTICS_READ = "PERM-BUDGET:analytics:read"

# Support
PERM_SUP_GRANT_REQUEST = "PERM-SUP:grant:request"
PERM_SUP_GRANT_APPROVE = "PERM-SUP:grant:approve"
PERM_SUP_GRANT_REVOKE = "PERM-SUP:grant:revoke"
PERM_SUP_AUDIT_READ = "PERM-SUP:audit:read"
PERM_SYS_AUDIT_LOG_READ = "PERM-SYS:audit-log:read"

# ---------------------------------------------------------------------------
# Role → Permissions mapping (C6 complete catalog)
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS: dict[str, set[str]] = {
    PUBLIC: {
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
    },
    ADM: {
        # Admin
        PERM_ADM_USER_MANAGE,
        PERM_ADM_SCHOOL_MANAGE,
        PERM_PROF_ADMIN_READ,
        PERM_GDPR_CONSENT_MANAGE,
        # IAM — admin-only operations
        PERM_IAM_INVITE_CREATE,
        PERM_IAM_PARENT_LINK_CREATE,
        PERM_IAM_PARENT_LINK_DELETE,
        # ERP — admin-only school management
        PERM_ERP_ENROLLMENT_ASSIGN,
        PERM_ERP_ASSIGNMENT_UPDATE,
        PERM_ERP_ABSENCE_REVIEW,
        PERM_ERP_ATTENDANCE_ALERT_MANAGE,
        # ERP — Timetable administration beyond DIR/TCH inherited baseline
        PERM_ERP_TIMETABLE_CREATE,
        PERM_ERP_TIMETABLE_UPDATE,
        PERM_ERP_TIMETABLE_DELETE,
        # Micro-school administration
        PERM_MICRO_SCHOOL_READ,
        PERM_MICRO_SCHOOL_MANAGE,
        # Document management (Phase 16) — destructive bulk action stays ADM-only
        PERM_DOC_BULK_DELETE,
        # COM — config/broadcast operations
        PERM_COM_CONSENT_UPDATE,
        PERM_COM_NOTIFICATION_BATCH_CREATE,
        # Support
        PERM_SUP_GRANT_APPROVE,
        PERM_SUP_GRANT_REVOKE,
    },
    DIR: {
        # Admin
        PERM_ADM_DASHBOARD_READ,
        PERM_ADM_USER_READ,
        PERM_ADM_USER_CREATE,
        PERM_ADM_INVITATION_READ,
        PERM_ADM_AUDIT_READ,
        PERM_ADM_IMPERSONATE,
        PERM_ADM_SCHOOL_READ,
        PERM_ADM_SETTINGS_READ,
        PERM_ADM_SETTINGS_UPDATE,
        PERM_ADM_ANNOUNCEMENT_MANAGE,
        PERM_GDPR_DATA_DELETE,
        # IAM — role-specific oversight
        PERM_IAM_PARENT_LINK_READ,
        PERM_IAM_LOGIN_HISTORY_READ,
        # ERP / LMS oversight
        PERM_ERP_TIMETABLE_GENERATE,
        PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE,
        PERM_LMS_COURSE_READ,
        # Reporting & Analytics (Phase 14)
        PERM_REP_ANALYTICS_READ,
        PERM_REP_EXPORT_CREATE,
        PERM_RPT_SCHEDULE_MANAGE,
        # Billing — school finance management
        PERM_BIL_INVOICE_READ,
        PERM_BIL_INVOICE_VOID,
        PERM_BIL_PAYMENT_READ,
        PERM_BIL_PROOF_READ,
        PERM_BIL_FEE_CREATE,
        PERM_BIL_FEE_READ,
        PERM_BIL_FEE_UPDATE,
        PERM_BIL_FEE_ASSIGN,
        PERM_BIL_FEE_STRUCTURE_CREATE,
        PERM_BIL_FEE_STRUCTURE_UPDATE,
        PERM_BIL_FEE_STRUCTURE_DELETE,
        PERM_BIL_INVOICE_GENERATE,
        PERM_BIL_SIBLING_POLICY_MANAGE,
        PERM_BIL_DISCOUNT_MANAGE,
        PERM_BIL_LATE_FEE_MANAGE,
        PERM_BIL_PAYMENT_PLAN_CREATE,
        PERM_BIL_PAYMENT_PLAN_READ,
        PERM_BIL_PAYMENT_PLAN_MANAGE,
        # Budget — class micro-budget approvals and oversight
        PERM_BUDGET_CREATE,
        PERM_BUDGET_READ,
        PERM_BUDGET_MANAGE,
        PERM_BUDGET_ALLOCATE,
        PERM_BUDGET_REQUEST_READ,
        PERM_BUDGET_APPROVE,
        PERM_BUDGET_TRANSACTION_CREATE,
        PERM_BUDGET_TRANSACTION_READ,
        PERM_BUDGET_ANALYTICS_READ,
        # Calendar & Events (Phase 15)
        PERM_CAL_EVENT_DELETE,
        PERM_CAL_HOLIDAY_MANAGE,
        # Document management (Phase 16)
        PERM_DOC_DOCUMENT_DELETE,
        PERM_DOC_STUDENT_DOCUMENT_LINK,
        PERM_DOC_REQUIREMENT_MANAGE,
        # COM — read + announcements (Phase 11C)
        PERM_COM_ANNOUNCEMENT_CREATE,
        PERM_COM_ANNOUNCEMENT_PUBLISH,
    },
    TCH: {
        # IAM — login/recovery
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_INVITE_CONSUME,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        # ERP — attendance mark
        PERM_ERP_CLASS_READ,
        PERM_ERP_ATTENDANCE_MARK,
        PERM_ERP_ATTENDANCE_ANALYTICS_READ,
        # ERP — Timetable (Phase 11A)
        PERM_ERP_TIMETABLE_READ,
        PERM_ERP_TIMETABLE_EXCEPTION_CREATE,
        PERM_ERP_TIMETABLE_EXCEPTION_READ,
        # LMS — publish + grade + files
        PERM_LMS_COURSE_PUBLISH,
        PERM_LMS_ASSIGNMENT_CREATE,
        PERM_LMS_SUBMISSION_GRADE,
        PERM_LMS_SUBMISSION_FILE_READ,
        PERM_LMS_CONTENT_READ,
        PERM_LMS_CONTENT_ASSET_UPLOAD,
        PERM_LMS_CONTENT_ASSET_READ,
        PERM_LMS_CONTENT_ASSET_DELETE,
        PERM_LMS_ASSESSMENT_CREATE,
        PERM_LMS_ASSESSMENT_READ,
        PERM_LMS_ASSESSMENT_PUBLISH,
        PERM_LMS_RUBRIC_CREATE,
        PERM_LMS_RUBRIC_READ,
        PERM_LMS_GRADEBOOK_MANAGE,
        PERM_LMS_GRADEBOOK_READ,
        PERM_LMS_QUESTION_BANK_MANAGE,
        PERM_LMS_QUESTION_BANK_READ,
        # CMS — assign content to class + submit for review
        PERM_CMS_CONTENT_ASSIGN,
        PERM_CMS_CONTENT_SUBMIT,
        # Quiz — create, manage, publish school-scoped quizzes
        PERM_QUIZ_CREATE,
        PERM_QUIZ_READ,
        PERM_QUIZ_MANAGE,
        PERM_QUIZ_PUBLISH,
        PERM_QUIZ_ANALYTICS,
        # Progress (Phase 11D)
        PERM_PROGRESS_READ,
        PERM_PROGRESS_CLASS_READ,
        # Budget — teachers can inspect scoped allocations and submit requests
        PERM_BUDGET_READ,
        PERM_BUDGET_REQUEST_CREATE,
        PERM_BUDGET_REQUEST_READ,
        PERM_BUDGET_TRANSACTION_READ,
        # Reporting (Phase 14)
        PERM_REP_REPORT_GENERATE,
        PERM_REP_REPORT_READ,
        # Calendar & Events (Phase 15)
        PERM_CAL_EVENT_CREATE,
        PERM_CAL_EVENT_READ,
        PERM_CAL_EVENT_UPDATE,
        PERM_CAL_RSVP_RESPOND,
        PERM_CAL_RSVP_READ,
        # Document management (Phase 16)
        PERM_DOC_DOCUMENT_UPLOAD,
        PERM_DOC_DOCUMENT_READ,
        PERM_DOC_RESOURCE_CREATE,
        PERM_DOC_RESOURCE_READ,
        PERM_DOC_RESOURCE_UPDATE,
        PERM_DOC_RESOURCE_DELETE,
        PERM_DOC_RESOURCE_RATE,
        PERM_DOC_BULK_DOWNLOAD,
        # COM — messaging (P1) + conversations (Phase 11C)
        PERM_COM_NOTIFICATION_READ,
        PERM_COM_MESSAGE_SEND,
        PERM_COM_CONVERSATION_CREATE,
        PERM_COM_CONVERSATION_READ,
        PERM_COM_ANNOUNCEMENT_READ,
        # IA (P1)
        PERM_IA_REQUEST_CREATE,
        PERM_IA_REQUEST_READ,
        PERM_IA_REQUEST_OVERRIDE,
    },
    EDUCATOR: {
        # IAM — login/recovery
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_INVITE_CONSUME,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        # Micro-school operations
        PERM_MICRO_SCHOOL_CREATE,
        PERM_MICRO_SCHOOL_READ,
        PERM_MICRO_SCHOOL_MANAGE,
        PERM_MICRO_GROUP_CREATE,
        PERM_MICRO_GROUP_READ,
        PERM_MICRO_ENROLLMENT_CREATE,
        PERM_MICRO_ENROLLMENT_READ,
        PERM_MICRO_PAYMENT_CREATE,
        PERM_MICRO_PAYMENT_READ,
        PERM_MICRO_RESOURCE_READ,
        PERM_MICRO_RESOURCE_MANAGE,
        PERM_MICRO_PROGRESS_CREATE,
        PERM_MICRO_PROGRESS_READ,
    },
    PAR: {
        # Profiles
        PERM_PROF_CHILD_READ,
        # IAM — login/recovery/invite consume
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_INVITE_CONSUME,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        # ERP — justify absence
        PERM_ERP_ABSENCE_JUSTIFY,
        # ERP — Timetable (Phase 11A)
        PERM_ERP_TIMETABLE_READ,
        PERM_ERP_TIMETABLE_EXCEPTION_READ,
        # LMS — read child results + content assets
        PERM_LMS_RESULT_READ,
        PERM_LMS_GRADEBOOK_READ,
        PERM_LMS_CONTENT_READ,
        PERM_LMS_CONTENT_ASSET_READ,
        # Billing — invoice/payment + fee read (Phase 11B)
        PERM_BIL_INVOICE_READ,
        PERM_BIL_PAYMENT_INITIATE,
        PERM_BIL_PAYMENT_READ,
        PERM_BIL_PROOF_READ,
        PERM_BIL_FEE_READ,
        PERM_BIL_PAYMENT_PLAN_READ,
        # Micro-school parent access
        PERM_MICRO_PAYMENT_READ,
        PERM_MICRO_PROGRESS_READ,
        # Progress (Phase 11D)
        PERM_PROGRESS_READ,
        # Reporting (Phase 14)
        PERM_REP_REPORT_GENERATE,
        PERM_REP_REPORT_READ,
        # Calendar & Events (Phase 15)
        PERM_CAL_EVENT_READ,
        PERM_CAL_RSVP_RESPOND,
        # Document management (Phase 16)
        PERM_DOC_DOCUMENT_UPLOAD,
        PERM_DOC_DOCUMENT_READ,
        PERM_DOC_STUDENT_DOCUMENT_LINK,
        PERM_DOC_RESOURCE_READ,
        PERM_DOC_BULK_DOWNLOAD,
        # COM — consent + feed + messaging + announcements (Phase 11C)
        PERM_COM_CONSENT_UPDATE,
        PERM_COM_NOTIFICATION_READ,
        PERM_COM_MESSAGE_SEND,
        PERM_COM_CONVERSATION_CREATE,
        PERM_COM_CONVERSATION_READ,
        PERM_COM_ANNOUNCEMENT_READ,
        # IA (P1)
        PERM_IA_REQUEST_CREATE,
        PERM_IA_REQUEST_READ,
        PERM_IA_PREFERENCE_UPDATE,
        PERM_IA_REQUEST_OVERRIDE,
        PERM_IA_RECOMMENDATION_READ,
    },
    STD: {
        # IAM — login/recovery/invite consume
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_INVITE_CONSUME,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        # ERP — Timetable (Phase 11A)
        PERM_ERP_TIMETABLE_READ,
        PERM_ERP_TIMETABLE_EXCEPTION_READ,
        # LMS — submit + read progress + files
        PERM_LMS_SUBMISSION_CREATE,
        PERM_LMS_SUBMISSION_FILE_UPLOAD,
        PERM_LMS_SUBMISSION_FILE_READ,
        PERM_LMS_RESULT_READ,
        PERM_LMS_GRADEBOOK_READ,
        PERM_LMS_CONTENT_READ,
        PERM_LMS_CONTENT_ASSET_READ,
        PERM_LMS_CONTENT_PROGRESS_WRITE,
        PERM_LMS_ACTIVITY_SESSION_CREATE,
        PERM_LMS_ACTIVITY_SESSION_COMPLETE,
        PERM_LMS_ASSESSMENT_READ,
        PERM_LMS_ASSESSMENT_SUBMIT,
        # Quiz — attempt + read
        PERM_QUIZ_ATTEMPT,
        PERM_QUIZ_READ,
        # Progress (Phase 11D)
        PERM_PROGRESS_READ,
        # Reporting (Phase 14)
        PERM_REP_REPORT_GENERATE,
        PERM_REP_REPORT_READ,
        # Calendar & Events (Phase 15)
        PERM_CAL_EVENT_READ,
        PERM_CAL_RSVP_RESPOND,
        # Document management (Phase 16)
        PERM_DOC_DOCUMENT_READ,
        PERM_DOC_RESOURCE_READ,
        PERM_DOC_BULK_DOWNLOAD,
        # COM — read notifications + announcements (Phase 11C)
        PERM_COM_NOTIFICATION_READ,
        PERM_COM_STD_MESSAGE_SEND,
        PERM_COM_STD_MESSAGE_READ,
        PERM_COM_ANNOUNCEMENT_READ,
        # IA (P1)
        PERM_IA_WRITING_ATTEMPT_CREATE,
        PERM_IA_WRITING_ATTEMPT_REVIEW,
        PERM_IA_RECOMMENDATION_READ,
    },
    SUP: {
        # Platform-wide read / oversight beyond inherited ADM → DIR → TCH
        PERM_ERP_SCHOOL_READ,
        PERM_ERP_ENROLLMENT_READ,
        PERM_ERP_ATTENDANCE_READ,
        PERM_ADM_PLATFORM_STATS,
        PERM_SYS_AUDIT_LOG_READ,
        # Support — grant lifecycle
        PERM_SUP_GRANT_REQUEST,
        PERM_SUP_AUDIT_READ,
    },
    SYS: {
        # Service account — jobs + webhooks
        PERM_BIL_PAYMENT_RECONCILE,
        PERM_COM_NOTIFICATION_BATCH_CREATE,
        PERM_IA_WRITING_ATTEMPT_REVIEW,
        # Feature toggles (Phase 11E)
        PERM_SYS_FEATURE_MANAGE,
    },
    CONTENT_MGR: {
        # IAM — login/recovery
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        # CMS — full content management + review
        PERM_CMS_CONTENT_CREATE,
        PERM_CMS_CONTENT_PUBLISH,
        PERM_CMS_CONTENT_MANAGE,
        PERM_CMS_CONTENT_DELETE,
        PERM_CMS_CONTENT_ANALYTICS,
        PERM_CMS_CONTENT_REVIEW,
        # LMS — read content
        PERM_LMS_CONTENT_READ,
        PERM_LMS_CONTENT_ASSET_UPLOAD,
        PERM_LMS_CONTENT_ASSET_READ,
        PERM_LMS_CONTENT_ASSET_DELETE,
        # Quiz — full management for platform-wide quizzes
        PERM_QUIZ_CREATE,
        PERM_QUIZ_READ,
        PERM_QUIZ_MANAGE,
        PERM_QUIZ_PUBLISH,
        PERM_QUIZ_ANALYTICS,
        # LMS enhancement permissions
        PERM_LMS_QUESTION_BANK_MANAGE,
        PERM_LMS_QUESTION_BANK_READ,
        # Cross-school resources
        PERM_DOC_RESOURCE_CREATE,
        PERM_DOC_RESOURCE_READ,
        PERM_DOC_RESOURCE_UPDATE,
        PERM_DOC_RESOURCE_DELETE,
        PERM_DOC_RESOURCE_MANAGE,
        # COM — notifications
        PERM_COM_NOTIFICATION_READ,
        # Feature toggles (Phase 11E)
        PERM_SYS_FEATURE_MANAGE,
    },
}

ROLE_HIERARCHY: dict[str, list[str]] = {
    SYS: [SUP],
    SUP: [ADM],
    ADM: [DIR],
    DIR: [TCH],
}

# Direct assignments above intentionally omit inherited permissions after the
# hierarchy cleanup:
# - DIR now inherits the teacher baseline from TCH.
# - ADM now inherits the shared DIR/TCH baseline and keeps only ADM-only extras.
# - SUP now inherits the shared ADM/DIR/TCH baseline and keeps only platform extras.


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def get_effective_permissions(
    role_code: str,
    _stack: set[str] | None = None,
) -> set[str]:
    """Return direct and inherited permissions for a role code."""
    stack = set() if _stack is None else set(_stack)
    if role_code in stack:
        raise ValueError(f"Circular role hierarchy detected at role {role_code}")

    stack.add(role_code)
    permissions = set(ROLE_PERMISSIONS.get(role_code, set()))
    for inherited_role in ROLE_HIERARCHY.get(role_code, []):
        permissions |= get_effective_permissions(inherited_role, stack)
    return permissions


def get_permissions_for_role(role_code: str) -> set[str]:
    """Return the effective permission set for a given role code."""
    return get_effective_permissions(role_code)


def role_has_permission(role_code: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_effective_permissions(role_code)
