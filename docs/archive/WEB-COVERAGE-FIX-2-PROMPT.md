# Web Coverage Fix Round 2 — 1 Partial + 2 Uncovered Endpoints

> Post-fix cleanup. Brings coverage from 96.6% → ~97.7%
> After this, the only uncovered endpoints are intentionally excluded (AI, system, webhook, email tracking).

---

### WEB-FIX-R2-1 — Fix Assignments exercise-pdf + Add Student-Work Endpoints

```
CONTEXT
-------
Project: ecole-platform-dev/web
Three remaining actionable endpoints need attention:

1. PARTIAL: POST /api/v1/assignments/{assignment_id}/exercise-pdf
   Backend has TWO distinct endpoints:
     - POST = upload_exercise_pdf (multipart file upload — teachers upload PDF)
     - GET  = download_exercise_pdf (download existing PDF)
   Frontend (web/src/features/submissions/submissions.service.ts) has:
     - generateExercisePdf() which tries POST (empty body, no file!) then falls back to GET
     - This POST call will always fail because the backend expects a multipart form upload
   The coverage tool reports this as a method mismatch because the POST is not a real upload.

2. UNCOVERED: GET /api/v1/student-work
   Backend returns unified list of student assignments + quizzes + assessments for the
   current student (role: STD). Response schema: StudentWorkListResponse { items: StudentWorkItem[], total: number }
   StudentWorkItem = { id, type, title, due_at, status, total_points, grading_type }

3. UNCOVERED: GET /api/v1/student-work/class/{class_id}
   Same as above but filtered by class. Used by teachers to view class work.

TASK
----

=== FIX 1: Assignments exercise-pdf ===

File: web/src/features/submissions/submissions.service.ts

a) Replace the broken generateExercisePdf() with two clear methods:

   uploadExercisePdf(assignmentId: string, file: File):
     - Use XMLHttpRequest or FormData + fetch
     - POST /api/v1/assignments/{assignmentId}/exercise-pdf
     - Content-Type: multipart/form-data
     - Body: FormData with field 'file' containing the PDF
     - Return: { id: string; exercise_pdf_path: string; checksum: string; file_size: number }

   downloadExercisePdf(assignmentId: string):
     - GET /api/v1/assignments/{assignmentId}/exercise-pdf
     - Return: Blob (the PDF file)
     - Use fetch with credentials, same auth header pattern as existing downloadExercisePdf

b) Remove the old generateExercisePdf() and the fetchExercisePdfResponse() helper.
   Keep downloadExercisePdf() but rewrite it to just do a clean GET (no POST fallback).

c) Update web/src/features/submissions/useSubmissions.ts:
   - Add useUploadExercisePdf() mutation hook
   - Ensure useDownloadExercisePdf() uses the cleaned-up service method

=== FIX 2: Student-Work Endpoints ===

File: web/src/features/student/student.service.ts

a) Add StudentWorkItem interface:
   interface StudentWorkItem {
     id: string;
     type: 'assignment' | 'quiz' | 'assessment';
     title: string;
     due_at: string | null;
     status: string;
     total_points: number | null;
     grading_type: string | null;
   }

   interface StudentWorkListResponse {
     items: StudentWorkItem[];
     total: number;
   }

b) Add two service methods:

   listStudentWork():
     return api.get<StudentWorkListResponse>('/student-work');

   listClassStudentWork(classId: string):
     return api.get<StudentWorkListResponse>(`/student-work/class/${classId}`);

c) Update web/src/features/student/useStudent.ts:
   - Add useStudentWork() query hook
   - Add useClassStudentWork(classId) query hook
   - Both use standard React Query useQuery pattern

CONSTRAINTS
-----------
- Do NOT modify page components — only service, hook, and type files
- Do NOT remove the existing uploadSubmissionFile() method — it's for student submissions, not exercise PDFs
- The uploadExercisePdf is for TEACHERS uploading exercise PDF templates, while uploadSubmissionFile
  is for STUDENTS uploading their work — keep both, they are different endpoints
- Match existing code patterns (use getAccessToken(), api client, etc.)

VERIFY
------
cd web
npx tsc --noEmit                    # 0 errors
npm run lint                         # 0 errors
npm run build                        # successful
npm run test                         # all pass

# Quick coverage check:
grep -n "exercise-pdf\|student-work" src/features/**/*.service.ts
# Should show:
#   submissions.service.ts: uploadExercisePdf (POST), downloadExercisePdf (GET)
#   student.service.ts: listStudentWork (GET), listClassStudentWork (GET)

GIT (Codex only)
---
git add web/src/features/submissions/ web/src/features/student/
git commit -m "fix(web): fix exercise-pdf upload + add student-work endpoints — coverage 97.7%"
```

---

### WEB-FIX-R2-2 — Update Coverage Report

```
CONTEXT
-------
After WEB-FIX-R2-1, update the coverage report to reflect final state.

TASK
----
1. Re-run coverage analysis comparing backend endpoints vs frontend services.
2. Update docs/WEB-BACKEND-ENDPOINT-COVERAGE.md with:
   - New total: ~340/350 covered
   - Coverage: ~97.1-97.7%
   - Partial: 0 (exercise-pdf method mismatch resolved)
   - Uncovered: ~9 (all intentionally excluded)

3. The only endpoints remaining UNCOVERED should be:
   - ai (4): writing-attempts, preferences opt-out, recommendations, events schema → AI module not active
   - notifications (2): unsubscribe, email-open → email tracking links, not SPA calls
   - payments (1): webhook/provider → backend-to-backend callback
   - router (2): health, readiness → infrastructure endpoints, not frontend

4. Add a "Final Notes" section stating these 9 are intentionally excluded with reasons.

VERIFY
------
cd web
npx tsc --noEmit && npm run build

GIT (Codex only)
---
git add docs/WEB-BACKEND-ENDPOINT-COVERAGE.md
git commit -m "docs: final coverage report — 97.7% with 9 intentionally excluded endpoints"
```
