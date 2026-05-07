# Postman Collections

API scenario collections for manual and automated testing.

## Files

### Full Smoke
- `ecole_platform_full.postman_collection.json` — Covers all major endpoints

### Domain Scenarios
- `scenario_academic_year_lifecycle.json` — Academic year CRUD
- `scenario_student_lifecycle.json` — Student enrollment and progress
- `scenario_teacher_workflow.json` — Teacher assignments and grading
- `scenario_parent_journey.json` — Parent feed, notifications, billing
- `scenario_admin_operations.json` — User and school management
- `scenario_billing_cycle.json` — Invoices, payments, fee structures
- `scenario_quiz_assessment_flow.json` — Quiz lifecycle
- `scenario_content_management.json` — CMS content operations
- `scenario_error_handling.json` — Error paths and validation
- `scenario_rbac_matrix.json` — Role permission boundaries
- `scenario_abac_policies.json` — Attribute-based policies
- `scenario_security_hardening.json` — Security boundary tests
- `scenario_direct_upload_flow.json` — Signed upload → scan → download
- `scenario_invoice_pdf_flow.json` — Invoice → PDF → redirect
- `scenario_program_enrollment_flow.json` — Program → eligibility → enrollment

### Environment Files
- `env_local.json` — Local development
- `env_staging.json` — Staging environment

### Fixtures
- `fixtures/sample-document.pdf` — Sample upload file

## Usage

```bash
# Full smoke
newman run ecole_platform_full.postman_collection.json -e env_local.json

# Single scenario
newman run scenario_billing_cycle.postman_collection.json -e env_local.json
```
