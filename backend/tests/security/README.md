# Security Tests

**105 tests** validating RBAC (Role-Based Access Control) matrices and ABAC (Attribute-Based Access Control) policies. Tests enforce authorization rules across 10 roles and complex permission scenarios.

## Overview

- **RBAC**: 8 system roles with 166+ permissions
- **ABAC**: Context-aware policies based on relationships and attributes
- **Coverage**: Permission matrix validation, policy enforcement, escalation prevention
- **Framework**: pytest with async fixtures

## Roles Tested (8 total)

| Role | Level | Permissions | Purpose |
|------|-------|-----------|---------|
| **SYS_ADMIN** | System | All (unrestricted) | System configuration, global operations |
| **SUPER_ADMIN** | Organization | Most permissions | Multi-school administration |
| **ADMIN** | School | School-level management | Single school administration |
| **DIRECTOR** | School | Curriculum, staff, finance | School leadership |
| **TEACHER** | Class | Class management, grading | Classroom instruction |
| **PARENT** | Family | Child viewing, communication | Guardian access |
| **STUDENT** | Individual | Own work, grades, announcements | Student access |
| **CONTENT_MGR** | Global | Content creation, template mgmt | Curriculum content management |

## Test Files

### conftest.py - Security Test Fixtures
Shared fixtures for security tests.

**Key Fixtures:**
- `sys_admin`, `super_admin`, `admin`, `director`, `teacher`, `parent`, `student` - User instances with roles
- `test_school` - Pre-populated school with all user types
- `test_class` - Class with teacher and students
- `test_assignment` - Assignment for testing permissions
- `rbac_engine` - RBAC evaluator
- `abac_engine` - ABAC evaluator

### test_rbac_matrix.py - Role-Permission Matrix
Validates that each role has correct permissions.

**Test Pattern:**
```python
async def test_teacher_permissions(teacher_user):
    # Teacher should have these
    assert teacher.has_permission("LMS_GRADE_WRITE")
    assert teacher.has_permission("CLASS_VIEW")

    # Teacher should NOT have these
    assert not teacher.has_permission("SCHOOL_MANAGE")
    assert not teacher.has_permission("BILLING_MANAGE")
    assert not teacher.has_permission("USER_DELETE")
```

**Coverage:**
- All 10 roles × 166+ permissions
- Permission inheritance (DIRECTOR ⊃ TEACHER permissions)
- Negative assertions (role lacks restricted permissions)
- Cross-role comparisons

### test_abac_parent_child.py - Parent-Child ABAC
Relationship-based access control for guardians.

**Scenarios Tested:**
- Parent CAN view own child's grades
- Parent CANNOT view other students' grades
- Parent can communicate with child's teacher
- Parent cannot modify school settings
- Multiple children (parent can view all)
- Relationship revocation (unlinked parent loses access)

**Example Test Pattern:**
```python
async def test_parent_view_child_grades(parent_user, student, grades):
    context = ABACContext(
        actor=parent_user,
        action="READ:GRADES",
        resource=student,
        relationship="PARENT_OF"
    )
    assert await abac_engine.evaluate(context) == Allow()

async def test_parent_cannot_view_unrelated_student():
    context = ABACContext(
        actor=parent_user,
        action="READ:GRADES",
        resource=other_student,
        relationship=None  # Not related
    )
    assert await abac_engine.evaluate(context) == Deny()
```

### test_abac_student_teacher.py - Student-Teacher ABAC
Class enrollment-based access control.

**Scenarios Tested:**
- Student CAN view own grades
- Student CAN submit assignments in enrolled class
- Student CANNOT view other students' grades
- Student CANNOT grade assignments
- Student CANNOT modify class schedule
- Enrollment state (active, dropped, graduated)

**Example Test Pattern:**
```python
async def test_student_view_own_grades(student_user, grade):
    context = ABACContext(
        actor=student_user,
        action="READ:GRADES",
        resource=grade,
        ownership="SELF"
    )
    assert await abac_engine.evaluate(context) == Allow()

async def test_student_cannot_grade_assignments(student_user, assignment):
    context = ABACContext(
        actor=student_user,
        action="WRITE:GRADES",
        resource=assignment,
        role="STUDENT"
    )
    assert await abac_engine.evaluate(context) == Deny()
```

### test_abac_teacher_class.py - Teacher-Class ABAC
Class assignment and curriculum access control.

**Scenarios Tested:**
- Teacher CAN manage assigned class
- Teacher CAN enter grades for assigned class
- Teacher CANNOT manage other classes
- Teacher CANNOT change school settings
- Teacher can view curriculum materials
- Substitute teacher temporary access

**Example Test Pattern:**
```python
async def test_teacher_manage_assigned_class(teacher_user, class_obj):
    context = ABACContext(
        actor=teacher_user,
        action="MANAGE:CLASS",
        resource=class_obj,
        assignment_type="PRIMARY"
    )
    assert await abac_engine.evaluate(context) == Allow()

async def test_teacher_cannot_manage_other_class():
    context = ABACContext(
        actor=teacher_user,
        action="MANAGE:CLASS",
        resource=other_class,
        assignment_type=None
    )
    assert await abac_engine.evaluate(context) == Deny()
```

### test_permission_escalation.py - Escalation Prevention
Validates that users cannot escalate privileges.

**Scenarios Tested:**
- Student cannot self-assign admin role
- Teacher cannot modify school budget
- Parent cannot change children's grades
- Impersonation attempts blocked
- Session hijacking prevented
- Token expiration enforced
- API key rotation required

**Example Test Pattern:**
```python
async def test_student_cannot_grant_self_admin(student_user, admin_role):
    with pytest.raises(AuthorizationError):
        await role_service.assign_role(
            actor=student_user,
            target=student_user,
            role=admin_role
        )
    # Verify role not assigned
    assert not student_user.has_role(admin_role)

async def test_api_key_expiration():
    # Old token should fail
    response = await test_client.get(
        "/api/grades",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
```

## Permission Categories (166 total)

### Authentication (AUTH_*)
- LOGIN, REGISTER, LOGOUT
- PASSWORD_RESET, MFA_SETUP
- TOKEN_REFRESH, TOKEN_REVOKE

### User Management (USER_*)
- READ, CREATE, UPDATE, DELETE
- EXPORT, IMPORT, DEACTIVATE
- RESET_PASSWORD, UNLOCK

### School Operations (SCHOOL_*)
- READ, CREATE, UPDATE, DELETE
- MANAGE_STAFF, MANAGE_BUDGET
- VIEW_ANALYTICS, PUBLISH_CALENDAR

### Learning Management (LMS_*)
- COURSE_READ, COURSE_CREATE, COURSE_UPDATE
- ASSIGNMENT_READ, ASSIGNMENT_SUBMIT, ASSIGNMENT_GRADE
- GRADE_READ, GRADE_WRITE, GRADE_PUBLISH
- QUIZ_READ, QUIZ_ATTEMPT, QUIZ_REVIEW

### Billing (BILLING_*)
- INVOICE_READ, INVOICE_CREATE
- PAYMENT_PROCESS, PAYMENT_VERIFY
- SUBSCRIPTION_MANAGE, REFUND_REQUEST

### Communication (COMMUNICATION_*)
- MESSAGE_SEND, MESSAGE_READ
- ANNOUNCEMENT_CREATE, ANNOUNCEMENT_PUBLISH
- NOTIFICATION_RECEIVE

### Document Management (DOCUMENTS_*)
- DOCUMENT_READ, DOCUMENT_UPLOAD
- DOCUMENT_SHARE, DOCUMENT_DELETE

### Reporting (REPORTS_*)
- REPORT_READ, REPORT_CREATE
- REPORT_EXPORT, REPORT_SCHEDULE

## Running Tests

```bash
# All security tests
pytest backend/tests/security/

# By test file
pytest backend/tests/security/test_rbac_matrix.py
pytest backend/tests/security/test_abac_parent_child.py -v

# By role
pytest backend/tests/security/ -k "teacher" -v
pytest backend/tests/security/ -k "parent" -v

# By permission
pytest backend/tests/security/ -k "GRADE_WRITE" -v

# Verbose with coverage
pytest backend/tests/security/ -vv --cov=backend.security --cov-report=html
```

## Test Isolation

- Each test gets fresh database
- User roles and permissions isolated
- No cross-test permission leakage
- Automatic cleanup after test

## Key Testing Principles

1. **Negative Testing** - Test denials as much as permissions
2. **Role Isolation** - One role's permissions don't leak to another
3. **Relationship Validation** - Verify relationships before granting access
4. **State Machine** - Respect role state transitions
5. **Audit Trail** - Permission checks are logged
6. **Performance** - Permission checks cached appropriately

## Moroccan Context

- Schools use hierarchical structure (system → region → school → class)
- Arabic role names supported in UI
- Bilingual permission messages (Fr/Ar)
- Academic year cycles (Sept-June)
- Family relationships (multi-generational guardianship)

## Common Failure Patterns

**Pattern**: User has unexpected permission
**Diagnosis**: Check role inheritance, ABAC context, relationship state

**Pattern**: Valid action denied
**Diagnosis**: Check relationship type (PARENT_OF vs. GUARDIAN_OF), enrollment status

**Pattern**: Escalation possible
**Diagnosis**: Check permission grant logic, role modification guards

## Coverage Goals

- **RBAC**: 100% of role-permission combinations tested
- **ABAC**: All relationship types and state transitions
- **Escalation**: All identified escalation paths blocked
- **Audit**: Permission failures logged and traceable

## Related Documentation

- Parent: `backend/tests/README.md`
- Core: `backend/tests/unit/core/` for permission definitions
- Unit: `backend/tests/unit/services/test_auth_service.py`
- Integration: `backend/tests/integration/api/` for end-to-end auth
