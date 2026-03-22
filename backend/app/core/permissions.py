"""RBAC permission catalog — data-driven mapping of PERM-* codes to roles.

Reference: S-034 — RBAC permission middleware, Pack C6 — complete permission catalog.
Format: PERM-{DOMAIN}:{resource}:{action}
Roles: ADM, DIR, TCH, PAR, STD, SUP, SYS, PUBLIC

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
PAR = "PAR"
STD = "STD"
SUP = "SUP"
SYS = "SYS"
PUBLIC = "PUBLIC"  # pseudo-role for unauthenticated entry endpoints

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

# ERP
PERM_ERP_CLASS_READ = "PERM-ERP:class:read"
PERM_ERP_ENROLLMENT_ASSIGN = "PERM-ERP:enrollment:assign"
PERM_ERP_ASSIGNMENT_UPDATE = "PERM-ERP:assignment:update"
PERM_ERP_ATTENDANCE_MARK = "PERM-ERP:attendance:mark"
PERM_ERP_ABSENCE_JUSTIFY = "PERM-ERP:absence:justify"
PERM_ERP_ABSENCE_REVIEW = "PERM-ERP:absence:review"

# LMS
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

# Billing
PERM_BIL_INVOICE_READ = "PERM-BIL:invoice:read"
PERM_BIL_PAYMENT_INITIATE = "PERM-BIL:payment:initiate"
PERM_BIL_PAYMENT_READ = "PERM-BIL:payment:read"
PERM_BIL_PAYMENT_RECONCILE = "PERM-BIL:payment:reconcile"
PERM_BIL_PROOF_READ = "PERM-BIL:proof:read"

# COM
PERM_COM_CONSENT_UPDATE = "PERM-COM:consent:update"
PERM_COM_NOTIFICATION_READ = "PERM-COM:notification:read"
PERM_COM_MESSAGE_SEND = "PERM-COM:message:send"

# IA (P1 — included for completeness)
PERM_IA_REQUEST_CREATE = "PERM-IA:request:create"
PERM_IA_REQUEST_READ = "PERM-IA:request:read"
PERM_IA_PREFERENCE_UPDATE = "PERM-IA:preference:update"
PERM_IA_REQUEST_OVERRIDE = "PERM-IA:request:override"
PERM_IA_WRITING_ATTEMPT_CREATE = "PERM-IA:writing-attempt:create"
PERM_IA_WRITING_ATTEMPT_REVIEW = "PERM-IA:writing-attempt:review"
PERM_IA_RECOMMENDATION_READ = "PERM-IA:recommendation:read"

# Support
PERM_SUP_GRANT_REQUEST = "PERM-SUP:grant:request"
PERM_SUP_GRANT_APPROVE = "PERM-SUP:grant:approve"
PERM_SUP_GRANT_REVOKE = "PERM-SUP:grant:revoke"
PERM_SUP_AUDIT_READ = "PERM-SUP:audit:read"

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
        # IAM — full admin
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_INVITE_CREATE,
        PERM_IAM_INVITE_REVOKE,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        PERM_IAM_PARENT_LINK_CREATE,
        PERM_IAM_PARENT_LINK_READ,
        PERM_IAM_PARENT_LINK_DELETE,
        # ERP — full admin
        PERM_ERP_CLASS_READ,
        PERM_ERP_ENROLLMENT_ASSIGN,
        PERM_ERP_ASSIGNMENT_UPDATE,
        PERM_ERP_ABSENCE_REVIEW,
        # LMS — read + supervision + file management
        PERM_LMS_SUBMISSION_FILE_READ,
        PERM_LMS_CONTENT_ASSET_UPLOAD,
        PERM_LMS_CONTENT_ASSET_READ,
        PERM_LMS_CONTENT_ASSET_DELETE,
        PERM_LMS_ASSESSMENT_CREATE,
        PERM_LMS_ASSESSMENT_READ,
        PERM_LMS_ASSESSMENT_PUBLISH,
        # Billing — read global
        PERM_BIL_INVOICE_READ,
        PERM_BIL_PAYMENT_READ,
        PERM_BIL_PROOF_READ,
        # COM — config
        PERM_COM_CONSENT_UPDATE,
        PERM_COM_NOTIFICATION_READ,
        # Support
        PERM_SUP_GRANT_APPROVE,
        PERM_SUP_GRANT_REVOKE,
    },
    DIR: {
        # IAM — read/validate
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        PERM_IAM_PARENT_LINK_READ,
        # ERP — validate periods
        PERM_ERP_CLASS_READ,
        # LMS — read analytics
        PERM_LMS_ASSESSMENT_READ,
        # COM — read
        PERM_COM_NOTIFICATION_READ,
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
        # COM — messaging (P1)
        PERM_COM_NOTIFICATION_READ,
        PERM_COM_MESSAGE_SEND,
        # IA (P1)
        PERM_IA_REQUEST_CREATE,
        PERM_IA_REQUEST_READ,
        PERM_IA_REQUEST_OVERRIDE,
    },
    PAR: {
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
        # LMS — read child results + content assets
        PERM_LMS_RESULT_READ,
        PERM_LMS_CONTENT_READ,
        PERM_LMS_CONTENT_ASSET_READ,
        # Billing — invoice/payment
        PERM_BIL_INVOICE_READ,
        PERM_BIL_PAYMENT_INITIATE,
        PERM_BIL_PAYMENT_READ,
        PERM_BIL_PROOF_READ,
        # COM — consent + feed
        PERM_COM_CONSENT_UPDATE,
        PERM_COM_NOTIFICATION_READ,
        PERM_COM_MESSAGE_SEND,
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
        # LMS — submit + read progress + files
        PERM_LMS_SUBMISSION_CREATE,
        PERM_LMS_SUBMISSION_FILE_UPLOAD,
        PERM_LMS_SUBMISSION_FILE_READ,
        PERM_LMS_RESULT_READ,
        PERM_LMS_CONTENT_READ,
        PERM_LMS_CONTENT_ASSET_READ,
        PERM_LMS_CONTENT_PROGRESS_WRITE,
        PERM_LMS_ACTIVITY_SESSION_CREATE,
        PERM_LMS_ACTIVITY_SESSION_COMPLETE,
        PERM_LMS_ASSESSMENT_READ,
        PERM_LMS_ASSESSMENT_SUBMIT,
        # COM — read notifications
        PERM_COM_NOTIFICATION_READ,
        # IA (P1)
        PERM_IA_WRITING_ATTEMPT_CREATE,
        PERM_IA_WRITING_ATTEMPT_REVIEW,
        PERM_IA_RECOMMENDATION_READ,
    },
    SUP: {
        # IAM
        PERM_IAM_SESSION_CREATE,
        PERM_IAM_SESSION_REFRESH,
        PERM_IAM_SESSION_REVOKE,
        PERM_IAM_SESSION_LIST,
        PERM_IAM_PASSWORD_CHANGE,
        PERM_IAM_RECOVERY_REQUEST,
        PERM_IAM_RECOVERY_VERIFY,
        PERM_IAM_RECOVERY_RESET,
        # Support — grant lifecycle
        PERM_SUP_GRANT_REQUEST,
        PERM_SUP_GRANT_REVOKE,
        PERM_SUP_AUDIT_READ,
    },
    SYS: {
        # Service account — jobs + webhooks
        PERM_BIL_PAYMENT_RECONCILE,
        PERM_IA_WRITING_ATTEMPT_REVIEW,
    },
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------
def get_permissions_for_role(role_code: str) -> set[str]:
    """Return the set of permissions for a given role code."""
    return ROLE_PERMISSIONS.get(role_code, set())


def role_has_permission(role_code: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role_code, set())
