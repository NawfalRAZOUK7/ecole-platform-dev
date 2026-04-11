# Web Coverage Fix — 13 Partial + 25 Oversight Endpoints

> Run this BEFORE starting mobile development.
> Fixes web coverage from 81.3% → ~95%+ (excluding 8 system + 4 AI endpoints intentionally)

---

### WEB-FIX-1 — Fix 13 HTTP Method Mismatches (Partial Endpoints)

```
CONTEXT
-------
Project: ecole-platform-dev/web
The coverage report (docs/WEB-BACKEND-ENDPOINT-COVERAGE.md) identified 13 endpoints
where the frontend calls the correct PATH but uses the WRONG HTTP method.
These are real bugs — the API call will fail at runtime.

TASK
----
Fix each method mismatch. For every item below, find the matching call in the
frontend service file and change the HTTP method to match the backend.

1. web/src/features/teacher/ or web/src/features/submissions/ (assignments):
   FIX: POST /assignments/{id}/exercise-pdf → the frontend uses api.get()
   Change to api.post() — this endpoint GENERATES a PDF, it's not a simple download.

2. web/src/features/budgets/budgets.service.ts:
   FIX: GET /budgets/allocations/{id} → frontend uses api.put()
   ADD a new GET method: getAllocation(allocationId) and keep the PUT as updateAllocation.
   FIX: GET /budgets/allocations/{id}/requests → frontend uses api.post()
   ADD a new GET method: getAllocationRequests(allocationId) and keep the POST as createRequest.

3. web/src/features/documents/documents.service.ts:
   FIX: GET /documents/{id} → frontend uses api.delete()
   ADD a new GET method: getDocument(documentId) and keep the DELETE as deleteDocument.
   FIX: POST /students/{id}/documents → frontend uses api.get()
   ADD a new POST method: uploadStudentDocument(studentId, payload) and keep the GET.
   FIX: POST /resources → frontend uses api.get()
   ADD a new POST method: createResource(payload) and keep the GET as listResources.
   FIX: PUT /resources/{id} → frontend uses api.get()
   ADD a new PUT method: updateResource(resourceId, payload) and keep the GET.
   FIX: DELETE /resources/{id} → frontend uses api.get()
   ADD a new DELETE method: deleteResource(resourceId) and keep the GET.

4. web/src/features/ (enrollments):
   FIX: POST /enrollments → frontend uses api.get()
   ADD: createEnrollment(payload): api.post('/enrollments', payload)
   Find the right service file (could be admin, teacher, or create new enrollments.service.ts)

5. web/src/features/notifications/notifications.service.ts or similar:
   FIX: PUT /notifications/preferences → frontend uses GET and POST
   ADD: updateNotificationPreferences(payload): api.put('/notifications/preferences', payload)

6. web/src/features/ (schools):
   FIX: DELETE /schools/{id} → frontend uses GET and PATCH
   ADD: deleteSchool(schoolId): api.delete(`/schools/${schoolId}`)

7. web/src/features/timetable/timetable.service.ts:
   FIX: GET /timetable/slots → frontend uses api.post()
   ADD: listSlots(params): api.get('/timetable/slots', params) and keep POST as createSlot.
   FIX: GET /timetable/exceptions → frontend uses api.post()
   ADD: listExceptions(params): api.get('/timetable/exceptions', params) and keep POST as createException.

For each fix:
- Add the missing HTTP method as a NEW function in the service
- Do NOT remove existing functions (they may be correct for their use case)
- Update the corresponding hook file to expose the new method
- Update types if needed

CONSTRAINTS
-----------
- Do NOT change any page component — only services, hooks, and types
- Each new service method must be fully typed

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
npm run test

GIT (Codex only)
---
git add web/src/features/
git commit -m "fix(web): resolve 13 HTTP method mismatches in API service layer"
```

---

### WEB-FIX-2 — Add 25 Oversight Endpoints

```
CONTEXT
-------
These endpoints exist in the backend but have NO frontend call at all.
Grouped by priority and service file location.

TASK
----
Add these to the EXISTING service files (do NOT create new pages unless noted):

=== ADMIN (admin.service.ts) ===
  impersonateUser(userId): POST /admin/impersonate/{userId}
  stopImpersonation(): POST /admin/stop-impersonation
  getUserLoginHistory(userId): GET /admin/users/{userId}/login-history

=== ASSESSMENTS (relevant service) ===
  submitAssessmentResults(assessmentId, payload): POST /assessments/{id}/results

=== ATTENDANCE ANALYTICS (attendance.service.ts) ===
  checkThresholds(): POST /analytics/attendance/check-thresholds

=== AUTH (auth.service.ts) ===
  verify2fa(payload): POST /auth/2fa/verify
  (Note: AuthContext may already handle this — add to service for completeness)

=== BUDGETS (budgets.service.ts) ===
  getBudgetRequest(requestId): GET /budgets/requests/{id}
  createTransaction(allocationId, payload): POST /budgets/allocations/{id}/transactions
  getTransactions(allocationId): GET /budgets/allocations/{id}/transactions

=== CLASS ASSIGNMENTS ===
  createClassAssignment(payload): POST /class-assignments
  Add to teacher.service.ts or create class-assignments.service.ts

=== CLASSES ===
  getClass(classId): GET /classes/{id}
  Add to teacher.service.ts or admin.service.ts

=== COMPLIANCE (compliance.service.ts) ===
  downloadReport(reportId): GET /compliance/reports/{id}/download

=== CONTENT (content.service.ts) ===
  streamContent(contentItemId): GET /content-items/{id}/stream
  getAsset(contentItemId, assetId): GET /content-items/{id}/assets/{assetId}
  deleteAsset(contentItemId, assetId): DELETE /content-items/{id}/assets/{assetId}

=== DEVICES (notifications.service.ts or new devices.service.ts) ===
  registerDevice(payload): POST /devices/register

=== DOCUMENTS (documents.service.ts) ===
  uploadDocument(payload): POST /documents/upload

=== FINANCIAL HEALTH (financial-health.service.ts) ===
  exportCsv(params): GET /financial-health/export/csv
  exportPdf(params): GET /financial-health/export/pdf

=== MESSAGING (messages.service.ts) ===
  searchMessages(query): GET /messages/search

=== NOTIFICATIONS (notifications.service.ts) ===
  getUnreadCount(): GET /notifications/unread-count
  batchNotify(payload): POST /notifications/batch
  deleteNotification(notificationId): DELETE /notifications/{id}

=== PROGRESS (progress.service.ts) ===
  getStudentProgress(studentId): GET /progress/student/{id}
  getMyProgress(): GET /progress/me

=== REPORTS (reports.service.ts) ===
  createSchedule(payload): POST /reports/schedules
  listSchedules(): GET /reports/schedules
  updateSchedule(scheduleId, payload): PUT /reports/schedules/{id}
  deleteSchedule(scheduleId): DELETE /reports/schedules/{id}
  runSchedule(scheduleId): POST /reports/schedules/{id}/run
  getJobStatus(jobId): GET /reports/{jobId}/status
  downloadReport(jobId): GET /reports/{jobId}/download

=== SCHOOLS ===
  createSchool(payload): POST /schools
  listSchools(): GET /schools
  (Add to admin.service.ts)

=== SUBMISSIONS (submissions.service.ts) ===
  overridePenalty(submissionId, payload): POST /submissions/{id}/override-penalty
  uploadFiles(submissionId, files): POST /submissions/{id}/files
  getFile(submissionId, fileId): GET /submissions/{id}/files/{fileId}
  previewSubmission(submissionId): GET /submissions/{id}/preview

=== TIMETABLE (timetable.service.ts) ===
  getClassWeekly(classId): GET /timetable/class/{classId}/weekly
  getTeacherWeekly(teacherId): GET /timetable/teacher/{teacherId}/weekly
  getMyWeekly(): GET /timetable/me/weekly

For each addition:
- Add the service method with proper types
- Add corresponding hook method (useQuery for GET, useMutation for POST/PUT/DELETE)
- Add any missing TypeScript types

CONSTRAINTS
-----------
- Do NOT create new page components (service/hook additions only)
- Each method must match the backend endpoint signature
- Keep existing methods unchanged

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
npm run test
# Re-run coverage check:
grep -rn "api\.\(get\|post\|put\|patch\|delete\|list\)(" src/features/ --include="*.service.ts" | wc -l
# Target: >= 300

GIT (Codex only)
---
git add web/src/features/
git commit -m "feat(web): add 25 missing API service methods to reach ~95% backend coverage"
```

---

### WEB-FIX-3 — Verify Updated Coverage

```
CONTEXT
-------
After running WEB-FIX-1 and WEB-FIX-2, verify the coverage improvement.

TASK
----
1. Run the same coverage analysis script that generated docs/WEB-BACKEND-ENDPOINT-COVERAGE.md
2. Compare: old (81.3%) vs new (target ~95%+)
3. Update docs/WEB-BACKEND-ENDPOINT-COVERAGE.md with the new snapshot

The only endpoints that should remain UNCOVERED are:
  - GET /health, GET /readiness (system, no UI)
  - POST /payments/webhook/provider (backend-to-backend)
  - GET /notifications/unsubscribe, GET /notifications/email-open (email links)
  - 4 AI endpoints (future module)
  = ~9 intentionally excluded endpoints

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build && npm run test

GIT (Codex only)
---
git add docs/WEB-BACKEND-ENDPOINT-COVERAGE.md
git commit -m "docs(web): update endpoint coverage report — 95%+ after method fixes and oversight additions"
```
