# Postman Collections & Environment Prompt

> Copy-paste this prompt into Claude Code to generate comprehensive Postman test suites.

---

## PROMPT

```
You are working on the Ecole Platform — a K-12 EdTech SaaS for Moroccan schools.
Backend: FastAPI at http://localhost:8000, API prefix: /api/v1
Auth: JWT Bearer tokens (access + refresh), optional TOTP 2FA.
Roles: SYS_ADMIN, SUPER_ADMIN, ADMIN, DIRECTOR, TEACHER, PARENT, STUDENT, CONTENT_MGR
Moroccan context: 0-20 grading scale, MAD currency, +212 phones, Africa/Casablanca timezone, fr/ar/en locales.

DO NOT run any git commands. I handle git manually.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — ANALYZE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read the following files to understand the full API surface:
- backend/app/api/v1/router.py (all registered routes)
- backend/app/api/v1/auth.py (auth flow: register, login, refresh, logout, 2FA)
- backend/app/api/v1/schools.py, classes.py, courses.py
- backend/app/api/v1/assignments.py, quizzes.py, submissions.py, gradebook.py
- backend/app/api/v1/billing.py, invoices.py, payments.py
- backend/app/api/v1/attendance.py, attendance_analytics.py
- backend/app/api/v1/messaging.py, notifications.py
- backend/app/api/v1/reports.py, analytics.py, exports.py
- backend/app/api/v1/timetable.py, timetable_generation.py
- backend/app/api/v1/profiles.py, documents.py, events.py
- backend/app/api/v1/ai.py, cms.py, gdpr.py, features.py
- backend/app/api/v1/rubrics.py, question_bank.py, progress.py
- backend/app/api/v1/admin.py, invitations.py, enrollments.py
- backend/app/core/config.py (environment variables and settings)
- backend/app/schemas/ (all request/response Pydantic schemas)
- backend/app/core/permissions.py (all 166 permission constants)
- docs/openapi.yaml (if exists, for full OpenAPI spec)
- tests/postman_collection_phase*.json (existing Postman collections for reference)

After reading, list every endpoint with method, path, required auth role, and request body shape.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — EXECUTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create the following files in tests/postman/:

### A. Environments (JSON files)

1. **tests/postman/env_local.json** — Postman environment for local dev:
   - `base_url`: http://localhost:8000
   - `api_prefix`: /api/v1
   - `admin_email`: admin@ecole-test.ma
   - `admin_password`: TestPassword123!
   - `teacher_email`: teacher@ecole-test.ma
   - `teacher_password`: TestPassword123!
   - `parent_email`: parent@ecole-test.ma
   - `parent_password`: TestPassword123!
   - `student_email`: student@ecole-test.ma
   - `student_password`: TestPassword123!
   - `access_token`: (empty, set by auth requests)
   - `refresh_token`: (empty, set by auth requests)
   - `school_id`: (empty, set dynamically)
   - `class_id`: (empty, set dynamically)
   - `course_id`: (empty, set dynamically)
   - `student_id`: (empty, set dynamically)
   - `assignment_id`: (empty, set dynamically)
   - `quiz_id`: (empty, set dynamically)
   - `invoice_id`: (empty, set dynamically)

2. **tests/postman/env_staging.json** — Same structure but:
   - `base_url`: https://staging.ecole-platform.ma
   - Different test credentials

### B. Main Collection

3. **tests/postman/ecole_platform_full.postman_collection.json**

   Organize into folders matching API domains. Every request must have:
   - Pre-request script to set Authorization header from {{access_token}}
   - Test script with pm.test() assertions checking:
     - Status code (200, 201, 204, 400, 401, 403, 404 as appropriate)
     - Response time < 500ms
     - Response schema validation (check required fields exist and types match)
     - Business logic validation where applicable
   - Dynamic variable extraction (pm.environment.set) for chaining

   **Folder structure and key requests:**

   **01-Auth:**
   - POST /auth/register (new user, save user_id)
   - POST /auth/login (save access_token, refresh_token)
   - POST /auth/refresh (use refresh_token, save new access_token)
   - POST /auth/logout
   - POST /auth/totp/setup (2FA enrollment)
   - POST /auth/totp/verify
   - POST /auth/password/change
   - POST /auth/password/reset-request
   - GET /auth/me (current user profile)
   - NEGATIVE: login with wrong password → 401
   - NEGATIVE: access protected route without token → 401
   - NEGATIVE: access admin route as student → 403

   **02-Schools:**
   - POST /schools (create, save school_id) — ADMIN+
   - GET /schools (list with pagination)
   - GET /schools/{{school_id}}
   - PATCH /schools/{{school_id}}
   - POST /schools/{{school_id}}/classes (create class, save class_id)
   - GET /schools/{{school_id}}/classes
   - POST /schools/{{school_id}}/academic-years

   **03-Classes & Enrollments:**
   - GET /classes/{{class_id}}
   - POST /enrollments (enroll student, save enrollment_id)
   - GET /classes/{{class_id}}/students
   - POST /class-assignments (assign teacher to class)

   **04-Courses & Content:**
   - POST /courses (create, save course_id) — TEACHER+
   - GET /courses
   - GET /courses/{{course_id}}
   - PATCH /courses/{{course_id}}
   - POST /content (upload lesson content)
   - GET /content-library

   **05-Assignments & Submissions:**
   - POST /assignments (create, save assignment_id)
   - GET /assignments
   - GET /assignments/{{assignment_id}}
   - POST /submissions (student submits, save submission_id)
   - GET /submissions/{{submission_id}}
   - PATCH /submissions/{{submission_id}} (grade submission)
   - NEGATIVE: student grades own submission → 403

   **06-Quizzes:**
   - POST /quizzes (create, save quiz_id)
   - GET /quizzes/{{quiz_id}}
   - POST /quizzes/{{quiz_id}}/attempts (start attempt)
   - POST /quizzes/{{quiz_id}}/attempts/{{attempt_id}}/submit
   - GET /quizzes/{{quiz_id}}/results

   **07-Gradebook:**
   - GET /gradebook/classes/{{class_id}}
   - POST /gradebook/grades (enter grade 0-20)
   - GET /gradebook/students/{{student_id}}
   - GET /gradebook/students/{{student_id}}/report-card
   - TEST: grade value must be 0-20 (Moroccan scale)
   - NEGATIVE: grade = 21 → 422
   - NEGATIVE: grade = -1 → 422

   **08-Attendance:**
   - POST /attendance (mark attendance)
   - GET /attendance/classes/{{class_id}}
   - GET /attendance-analytics/classes/{{class_id}}
   - GET /attendance-analytics/students/{{student_id}}

   **09-Billing & Payments:**
   - POST /billing/invoices (create invoice in MAD)
   - GET /billing/invoices
   - GET /invoices/{{invoice_id}}
   - POST /payments (record payment, save payment_id)
   - GET /payments
   - TEST: currency must be MAD
   - TEST: amounts must be positive

   **10-Calendar & Events:**
   - POST /events (create school event, save event_id)
   - GET /events
   - POST /events/{{event_id}}/rsvp

   **11-Messaging & Notifications:**
   - POST /messaging (send message)
   - GET /messaging
   - GET /messaging/{{thread_id}}
   - GET /notifications
   - PATCH /notifications/{{notification_id}}/read
   - NEGATIVE: parent messages unrelated student's teacher → 403 (ABAC)

   **12-Reports & Analytics:**
   - GET /reports/students/{{student_id}}
   - GET /reports/classes/{{class_id}}
   - GET /analytics/schools/{{school_id}}
   - POST /exports (trigger data export)
   - GET /exports/{{export_id}}

   **13-Timetable:**
   - POST /timetable-generation (generate timetable)
   - GET /timetable/classes/{{class_id}}

   **14-Profiles & Documents:**
   - GET /profiles/me
   - PATCH /profiles/me
   - POST /documents (upload document)
   - GET /documents

   **15-Admin & System:**
   - GET /admin/users (list all users) — SYS_ADMIN only
   - PATCH /admin/users/{{user_id}}/roles
   - GET /features (feature flags)
   - POST /features (toggle feature) — SYS_ADMIN only
   - GET /admin/audit-log

   **16-AI & CMS:**
   - POST /ai/completions (AI-assisted content)
   - GET /cms/pages
   - POST /cms/pages

   **17-GDPR:**
   - GET /gdpr/data-export (request personal data)
   - POST /gdpr/consent
   - DELETE /gdpr/data (right to erasure)

   **18-Question Bank & Rubrics:**
   - POST /question-bank (create question)
   - GET /question-bank
   - POST /rubrics (create rubric)
   - GET /rubrics

### C. Scenario Collections

4. **tests/postman/scenario_student_lifecycle.postman_collection.json**
   Complete student journey:
   Register → Login → View courses → Submit assignment → Take quiz → View grades → View report card → Logout
   Chain all requests with dynamic variables. Validate the grade is on 0-20 scale.

5. **tests/postman/scenario_teacher_workflow.postman_collection.json**
   Teacher daily workflow:
   Login → Create course → Create assignment → Create quiz → Grade submissions → Enter gradebook grades → Generate class report → View attendance analytics → Send message to parents → Logout

6. **tests/postman/scenario_admin_operations.postman_collection.json**
   Admin operations:
   Login as SYS_ADMIN → Create school → Create classes → Invite teachers → Manage enrollments → Configure billing → Generate invoices → View analytics → Export data → Check audit log → Manage feature flags → Logout

7. **tests/postman/scenario_billing_cycle.postman_collection.json**
   Full billing cycle:
   Login as ADMIN → Create invoice (MAD) → Send to parent → Parent logs in → Views invoice → Makes payment → Verify payment recorded → Generate billing statement → Logout

8. **tests/postman/scenario_rbac_matrix.postman_collection.json**
   RBAC validation: For each of the 8 roles, attempt 10 key operations and verify correct 200/403 responses:
   - SYS_ADMIN: full access
   - STUDENT: can only view own data, submit work
   - PARENT: can only view own children's data
   - TEACHER: can manage own classes only
   Include test scripts that explicitly check role boundaries.

9. **tests/postman/scenario_abac_policies.postman_collection.json**
   ABAC boundary tests:
   - Parent A cannot see Parent B's child grades
   - Teacher X cannot grade Teacher Y's class
   - Student cannot view another student's submissions
   - Director can see all classes in their school only

10. **tests/postman/scenario_error_handling.postman_collection.json**
    Error path validation:
    - Invalid JSON body → 422
    - Missing required fields → 422
    - Expired token → 401
    - Resource not found → 404
    - Duplicate creation → 409
    - Rate limit exceeded → 429
    - Grade out of range (>20 or <0) → 422
    - Negative payment amount → 422
    - Invalid phone format (not +212) → 422
    - Invalid email format → 422

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — VERIFY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After creating all files:

1. Validate each JSON file is valid JSON:
   python3 -c "import json, glob; [json.load(open(f)) for f in glob.glob('tests/postman/*.json')]; print('All JSON valid')"

2. Count total requests across all collections:
   python3 -c "
   import json, glob
   total = 0
   for f in sorted(glob.glob('tests/postman/*.json')):
       data = json.load(open(f))
       def count_items(items):
           c = 0
           for item in items:
               if 'item' in item:
                   c += count_items(item['item'])
               else:
                   c += 1
           return c
       n = count_items(data.get('item', []))
       total += n
       print(f'{f}: {n} requests')
   print(f'TOTAL: {total} requests')
   "

3. Verify every collection has test scripts:
   python3 -c "
   import json, glob
   for f in sorted(glob.glob('tests/postman/*.json')):
       data = json.load(open(f))
       def check_tests(items, path=''):
           missing = []
           for item in items:
               name = item.get('name', 'unnamed')
               if 'item' in item:
                   missing.extend(check_tests(item['item'], f'{path}/{name}'))
               elif 'event' not in item or not any(e.get('listen') == 'test' for e in item.get('event', [])):
                   missing.append(f'{path}/{name}')
           return missing
       missing = check_tests(data.get('item', []))
       if missing:
           print(f'WARN: {f} has {len(missing)} requests without test scripts')
       else:
           print(f'OK: {f} — all requests have test scripts')
   "

4. Print summary:
   - Number of environment files
   - Number of collections
   - Total requests
   - Total test assertions
   - Coverage of API endpoints (requests / total endpoints)

TARGET: 200+ requests across all collections, covering all API endpoints, with 500+ test assertions.
```
