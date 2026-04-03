# Postman Collections

API test collections for the Ecole Platform. Import into Postman or run via Newman CLI.

## Environments

- **env_local.json** — Local development (http://localhost:8000)
- **env_staging.json** — Staging (https://staging.ecole-platform.ma)

## Main Collection

- **ecole_platform_full.postman_collection.json** — Complete API coverage with 18 domain folders and 127 requests covering Auth, Schools, Classes, Courses, Assignments, Quizzes, Gradebook, Attendance, Billing, Calendar, Messaging, Reports, Timetable, Profiles, Admin, AI/CMS, GDPR, and Question Bank.

## Scenario Collections

Workflow-based collections that chain requests end-to-end:

- **scenario_student_lifecycle** — Student journey: register → courses → submit → quiz → grades → logout
- **scenario_teacher_workflow** — Teacher daily: create course → assign → grade → attendance → message
- **scenario_admin_operations** — Admin setup: school → users → billing → analytics → features
- **scenario_parent_journey** — Parent experience: children → grades → attendance → payments → messaging
- **scenario_billing_cycle** — Full billing: fees → invoices → parent payment → verification
- **scenario_academic_year_lifecycle** — Year setup: school → classes → enrollments → timetable
- **scenario_quiz_assessment_flow** — Quiz pipeline: question bank → generate → attempt → grade
- **scenario_content_management** — CMS lifecycle: create → submit → review → approve
- **scenario_rbac_matrix** — Role validation across 6 roles with expected 200/403 responses
- **scenario_abac_policies** — Attribute-based access: parent/teacher/student data boundaries
- **scenario_error_handling** — Error paths: 401, 403, 404, 409, 422 validation
- **scenario_security_hardening** — Security: 2FA, sessions, password reset, audit trail

## Stats

312 requests, 1,484 test assertions, 100% test script coverage.

## Usage

Import an environment and a collection into Postman, then run the collection. For CLI:

```bash
newman run ecole_platform_full.postman_collection.json -e env_local.json
```
