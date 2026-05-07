# Postman Collections

API test collections for the Ecole Platform. Import into Postman or run via Newman CLI.

## Environments

- **env_local.json** — Seeded local variables. Use it with the disposable API
  test backend (`http://localhost:8010/api/v1`) unless you explicitly want to
  mutate the normal dev DB on `localhost:8000`.
- **env_staging.json** — Staging (https://staging.ecole-platform.ma)

## Main Collection

- **ecole_platform_full.postman_collection.json** — Maintained full API smoke collection across Auth, Admin, Schools, Enrollments, Billing, Reports, Analytics, Teacher, Parent, Student, CMS, and negative authorization checks.

## Scenario Collections

Workflow-based smoke collections that assert current seeded-role behavior:

- **scenario_student_lifecycle** — Student auth, assignments, quizzes, results, and forbidden admin access
- **scenario_teacher_workflow** — Teacher auth, classes, submissions, courses, assignments, quizzes, conversations
- **scenario_admin_operations** — Admin dashboard, users, schools, analytics, export, and parent forbidden access
- **scenario_parent_journey** — Parent profile, children, child progress, invoices, notifications
- **scenario_billing_cycle** — Admin billing reads plus parent invoice access
- **scenario_academic_year_lifecycle** — Admin lifecycle reads: dashboard, enrollments, reports, attendance analytics
- **scenario_quiz_assessment_flow** — Teacher question bank/quizzes plus student quiz/results access
- **scenario_content_management** — CMS content/submissions and teacher submission access
- **scenario_rbac_matrix** — Role validation across 6 roles with expected 200/403 responses
- **scenario_abac_policies** — Attribute-based access: parent/teacher/student data boundaries
- **scenario_error_handling** — Error paths: 401, 403, 404, 422 validation
- **scenario_security_hardening** — Login hardening, auth/me, sessions, login history

`make test-postman` runs phases, scenarios, and the full smoke collection.
Run them only against the disposable API-test stack unless you intentionally
want to mutate the normal dev DB.

## Stats

The maintained runner covers `postman_collection_phase12.json` through
`postman_collection_phase16.json`, all `scenario_*.postman_collection.json`
files, and `ecole_platform_full.postman_collection.json`.

## Usage

Use the repository runner so base URL variables and safety checks are applied:

```bash
make api-test-up
make test-postman
make api-test-down
```

Direct Newman runs are possible, but they bypass the dev-DB guard. If you do use
Newman directly, pass both variable styles used by the older collections:

```bash
newman run ecole_platform_full.postman_collection.json \
  -e env_local.json \
  --env-var baseUrl=http://localhost:8010/api/v1
```
