# Integration & E2E Tests

Manual API testing collections and load test scripts. Complements automated pytest suite with human-driven testing and realistic usage pattern validation.

## Overview

- **Approach**: Postman collections for API exploration, k6 scripts for load simulation
- **Audience**: QA testers, developers, performance engineers
- **Execution**: Manual via Postman UI or automated via CLI/CI
- **Data**: Use the disposable API-test stack by default. Do not point these collections or k6 scenarios at `localhost:8000` unless you intentionally want to mutate your normal dev database.

## Safe Execution

Start an isolated backend on `localhost:8010`, run the API/load checks, then remove the stack and its volumes:

```bash
make api-test-up
make test-postman
make test-load
make api-test-down
```

Or run the same API/system checks inside the Dockerized test matrix:

```bash
make docker-test-postman
make docker-test-load
```

Reports are written under `artifacts/test-runs/<run-id>/`.

The Postman runner and k6 config refuse `localhost:8000` by default. Override only for an intentional dirty-dev-DB run:

```bash
system-tests/run_tests.sh --all --allow-dev-db
cd system-tests/load && K6_ALLOW_DEV_DB=1 k6 run baseline/01_logins.js
```

## Postman Collections

### Full Smoke Collection

| Collection | Endpoints | Purpose |
|------------|-----------|---------|
| `ecole_platform_full.postman_collection.json` | All major endpoints | Full platform smoke test |

### Domain Scenarios

| Collection | Purpose |
|------------|---------|
| `scenario_academic_year_lifecycle.json` | Academic year CRUD |
| `scenario_student_lifecycle.json` | Enrollment, grades, progress |
| `scenario_teacher_workflow.json` | Assignments, grading |
| `scenario_parent_journey.json` | Feed, notifications, payments |
| `scenario_admin_operations.json` | User management, invitations |
| `scenario_billing_cycle.json` | Invoices, payments, fees |
| `scenario_quiz_assessment_flow.json` | Quiz creation, attempt, results |
| `scenario_content_management.json` | CMS content, assignments |
| `scenario_error_handling.json` | Error paths and validation |
| `scenario_rbac_matrix.json` | Role-based access control |
| `scenario_abac_policies.json` | Attribute-based access control |
| `scenario_security_hardening.json` | Security boundaries |
| `scenario_direct_upload_flow.json` | Signed upload → scan → download |
| `scenario_invoice_pdf_flow.json` | Invoice → PDF generation → redirect |
| `scenario_program_enrollment_flow.json` | Program → version → eligibility → enroll |

### run_tests.sh — Test Execution Script

Bash script to run Postman collections via CLI.

```bash
POSTMAN_BASE_URL=http://localhost:8010/api/v1 system-tests/run_tests.sh --all
POSTMAN_BASE_URL=http://localhost:8010/api/v1 system-tests/run_tests.sh --include-scenarios
POSTMAN_BASE_URL=http://localhost:8010/api/v1 system-tests/run_tests.sh --full-collection
```

## Load Tests (k6)

Location: `system-tests/load/`

### Directory Structure

```
system-tests/load/
├── config.js                 # Shared configuration
├── smoke/
│   └── healthcheck.js        # 1 VU, 10s — verify API alive
├── baseline/
│   ├── 01_logins.js          # 20 concurrent logins
│   ├── 02_get_requests.js    # 50 concurrent read-heavy users
│   ├── 03_file_uploads.js    # 10 concurrent uploads
│   └── 04_websocket.js       # 20 concurrent WS connections
├── stress/
│   ├── peak_school_morning.js   # 500 VU peak login + dashboard
│   └── upload_burst.js          # 50 VU concurrent 5MB uploads
└── soak/
    └── 24h_steady_traffic.js    # 24h low constant load
```

### Run Examples

```bash
# Smoke
k6 run system-tests/load/smoke/healthcheck.js

# Baseline
k6 run system-tests/load/baseline/01_logins.js
k6 run system-tests/load/baseline/02_get_requests.js

# Stress
k6 run system-tests/load/stress/peak_school_morning.js

# Soak (long duration — run intentionally)
k6 run system-tests/load/soak/24h_steady_traffic.js
```

## Integration with CI/CD

```yaml
# Postman smoke
- name: Run Postman Tests
  run: system-tests/run_tests.sh --all

# k6 baseline
- name: Run Load Tests
  run: k6 run system-tests/load/baseline/01_logins.js
```

## Related Documentation

- Backend tests: `backend/tests/README.md`
- Test execution guide: `TEST_GUIDE.md`
- k6 docs: https://k6.io/docs/
- Newman docs: https://learning.postman.com/docs/collections/using-newman-cli/command-line-integration-with-newman/
