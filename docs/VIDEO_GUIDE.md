# Ecole Platform recording guide

This guide is a step-by-step script for recording a project demo video. It tells you what to run, what URL to open, what to type, what to click, and what feature to explain.

Use it as a checklist while filming. You do not need to show every screen if your video has a strict time limit. The recommended main recording is the web app, then optional mobile, monitoring, and API sections.

---

## 1. Before Recording

### 1.1 Prepare your screen

1. Close private tabs, chat apps, and notifications.
2. Open one browser window only.
3. Set browser zoom to `100%`.
4. Use a clean window size such as `1440 x 900` or record full HD.
5. Keep the terminal font large enough to read.
6. Start OBS, QuickTime, or your recording tool.
7. Record system/browser audio only if you plan to play mobile TTS or notification sounds.

### 1.2 Start the project

Open a terminal and run:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
test -f .env || cp .env.example .env
make up
make migrate
make seed
make health
make status
```

What to show in the recording:

1. Show the terminal after `make health`.
2. Expected health result: backend returns a JSON status such as `healthy`.
3. Show `make status` briefly so viewers see `ecole-backend`, `ecole-web`, `ecole-postgres`, `ecole-redis`, and `ecole-minio`.

If the app is already running and seeded, you can use only:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make status
make health
```

### 1.3 Open the web app

Open:

```text
http://localhost:5173/login
```

Important: the login page has a `School ID` field. Replace any prefilled value with:

```text
00000000-0000-4000-8000-000000000001
```

### 1.4 Demo accounts

Use these seeded accounts:

| Role | Email | Password | Main screens to show |
| --- | --- | --- | --- |
| Admin | `admin@ecole-benani.ma` | `admin123` | Dashboard, users, billing, settings, reports |
| Director | `directeur@ecole-benani.ma` | `director123` | Analytics, attendance analytics, reports |
| Teacher | `prof.math@ecole-benani.ma` | `teacher123` | Classes, courses, attendance, quizzes, rubrics |
| Parent | `parent.alaoui@gmail.com` | `parent123` | Children, feed, invoices, messages |
| Student | `yassine.alaoui@ecole-benani.ma` | `student123` | Student home, content, quizzes, games, rewards |
| CMS manager | `cms@ecole-platform.ma` | `content123` | CMS library, upload, review, quiz builder |

For each login:

1. Type the email.
2. Type the password.
3. Replace `School ID` with `00000000-0000-4000-8000-000000000001`.
4. Click `Sign In` or `Se connecter`.
5. After the scene, click `Logout` or `Deconnexion` before switching accounts.

---

## 2. Recommended Video Structure

Recommended duration: `18 to 25 minutes`.

| Scene | Duration | Account |
| --- | ---: | --- |
| Intro, stack, and startup | 1-2 min | Terminal/browser |
| Login and role-based navigation | 2 min | Admin, Teacher, Parent, Student |
| Admin and school management | 3 min | Admin |
| Academic and LMS teacher workflows | 4 min | Teacher |
| Student learning experience | 4 min | Student |
| Parent portal | 3 min | Parent |
| Billing, finance, reports | 3 min | Admin |
| Communication and documents | 2 min | Admin or Teacher |
| CMS content management | 2 min | CMS manager |
| Optional mobile, monitoring, API | 3-5 min | Optional |

---

## 3. Scene 1 - Intro, Startup, and Architecture

### What to run

In the terminal:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make status
make health
```

Optional, to show the app version:

```bash
make version
```

### What to click

1. Open `http://localhost:5173/login`.
2. Open another tab with `http://localhost:8000/docs`.
3. Briefly show the Swagger/OpenAPI page.

### What to say

Explain that Ecole Platform is a SaaS school platform for K-12 schools with:

- FastAPI backend.
- React web app.
- Flutter mobile app.
- PostgreSQL, Redis, and MinIO.
- Modules for IAM, ERP, LMS, communication, billing, gamification, reports, and compliance.

---

## 4. Scene 2 - Login and Role-Based Navigation

### Admin login

1. Go to `http://localhost:5173/login`.
2. In `Email address`, type:

   ```text
   admin@ecole-benani.ma
   ```

3. In `Password`, type:

   ```text
   admin123
   ```

4. In `School ID`, type:

   ```text
   00000000-0000-4000-8000-000000000001
   ```

5. Click `Sign In` or `Se connecter`.
6. Show that the admin lands on `Dashboard` / `Tableau de bord`.
7. Point at summary cards: users, sessions, invitations, audit events, justifications.

### Switch to teacher

1. Click `Logout` / `Deconnexion`.
2. Log in with:

   ```text
   prof.math@ecole-benani.ma
   teacher123
   ```

3. Click `Sign In`.
4. Show the teacher sidebar: `My Classes`, `Courses`, `Assignments`, `Attendance`, `Assessments`, `Content Library`, `Quizzes`, `Question Bank`, `Rubrics`.

### Switch to parent

1. Click `Logout`.
2. Log in with:

   ```text
   parent.alaoui@gmail.com
   parent123
   ```

3. Show parent navigation: `My Children`, `Feed`, `Children's Progress`, `Invoices`, `Messages`, `Payment Plans`.

### Switch to student

1. Click `Logout`.
2. Log in with:

   ```text
   yassine.alaoui@ecole-benani.ma
   student123
   ```

3. Show student navigation: `Student Home`, `My Content`, `Quizzes`, `Games`, `Writing`, `My Rewards`, `My Progress`.

What to say: each account has a different landing page and sidebar because the backend returns the role and permissions after login.

---

## 5. Scene 3 - Admin and School Management

Account: Admin.

If needed, log in again:

```text
admin@ecole-benani.ma
admin123
School ID: 00000000-0000-4000-8000-000000000001
```

### 5.1 Dashboard

1. Click `Dashboard` / `Tableau de bord`.
2. Show user count, active sessions, active invitations, audit events, and pending justifications.
3. Scroll to the users-by-role area if visible.

### 5.2 Users

1. Click `Users` / `Utilisateurs`.
2. Show the table of seeded users.
3. Use the search/filter input if present and type:

   ```text
   prof
   ```

4. Clear the search.
5. Click one row or action button if the page offers details.

### 5.3 Invitations

1. Click `Invitations`.
2. Show invitation list and status.
3. If there is a create button, click it and use demo values:

   ```text
   Email: demo.teacher.recording@ecole-benani.ma
   Role: Teacher / TCH
   Expires: leave default or choose next month
   ```

4. Click `Cancel` if you do not want to create data, or `Save` if you want to demonstrate creation.

### 5.4 Audit log

1. Click `Audit Log` / `Journal d'audit`.
2. Show filters and recent audit events.
3. Explain that admin actions are recorded for traceability and compliance.

### 5.5 Feature toggles

1. Open direct URL:

   ```text
   http://localhost:5173/admin/features
   ```

2. Show enabled features such as gamification, rewards, skill passport, difficulty adaptation, and parent dashboard.
3. Do not disable anything during the recording unless you plan to re-enable it immediately.

### 5.6 Academic programs

1. Click `Programs` / `Filieres`.
2. Show the programs list.
3. Click `Enrollments` / `Inscriptions`.
4. Show the current student enrollments.
5. Click `Equivalences` and `Eligibility rules` if you want to show advanced academic setup.

What to say: the admin can manage school structure, identities, auditability, feature flags, and academic program rules from one back-office.

---

## 6. Scene 4 - Academic and LMS Teacher Workflow

Account: Teacher.

Log in with:

```text
prof.math@ecole-benani.ma
teacher123
School ID: 00000000-0000-4000-8000-000000000001
```

### 6.1 My classes

1. Click `My Classes` / `Mes classes`.
2. Show assigned classes such as `6eme A`.
3. Open a class if the page has detail actions.

### 6.2 Attendance

1. Click `Attendance` / `Presence`.
2. Select a class if a class selector appears.
3. Select today or a visible date.
4. Mark one student as present and one as absent if the UI allows editing.
5. Click `Save` / `Enregistrer`.
6. Explain that attendance is available to admin analytics and parent absence workflows.

### 6.3 Courses

1. Click `Courses` / `Cours`.
2. Show existing courses such as mathematics.
3. If you want to create a demo item, click `New` / `Create` and use:

   ```text
   Title: Demo fractions course
   Description: Short review lesson for recording
   Subject: Mathematics
   Class: 6eme A
   ```

4. Click `Cancel` if you only want to show the form.

### 6.4 Assignments

1. Click `Assignments` / `Devoirs`.
2. Show assignment list.
3. If you create one, use:

   ```text
   Title: Recording demo assignment
   Instructions: Solve exercise 1 and upload your answer.
   Points: 20
   Due date: choose a date next week
   ```

4. Click `Save` or `Cancel`.

### 6.5 Assessments and gradebook

1. Click `Assessments` / `Evaluations`.
2. Show the assessment form or list.
3. Open direct URL for gradebook:

   ```text
   http://localhost:5173/gradebook
   ```

4. Show class grades and explain publication of results to students and parents.

### 6.6 Quizzes

1. Click `Quizzes`.
2. Show existing quizzes such as `Quiz Fractions`.
3. Open a quiz if possible.
4. Click analytics if available, or use a direct route from a quiz row if present.

### 6.7 Question bank

1. Click `Question Bank` / `Banque de questions`.
2. Show filters for subject, type, and difficulty.
3. Click `Generate Quiz` / `Generer un quiz`.
4. Use sample inputs:

   ```text
   Subject: Mathematics
   Difficulty: Medium
   Number of questions: 5
   ```

5. Click `Cancel` or go back after showing the generator.

### 6.8 Rubrics

1. Click `Rubrics` / `Grilles d'evaluation`.
2. Show rubric list.
3. Open an existing rubric or click create.
4. Explain criteria, levels, weights, and grading workflow.

What to say: teachers can manage the full pedagogy cycle: classes, attendance, courses, assignments, quizzes, grading, rubrics, and content.

---

## 7. Scene 5 - Student Learning Experience

Account: Student.

Log in with:

```text
yassine.alaoui@ecole-benani.ma
student123
School ID: 00000000-0000-4000-8000-000000000001
```

### 7.1 Student home

1. Click `Student Home` / `Accueil eleve`.
2. Show cards for learning, progress, rewards, or recent activity.
3. Explain that the student interface is simplified compared with admin and teacher screens.

### 7.2 My content

1. Click `My Content` / `Mon contenu`.
2. Open a story or learning content card.
3. If a `Read` action appears, click it.
4. Use direct route only if you know the content id from the list. Otherwise, stay on the list and show available content.

### 7.3 Quizzes

1. Click `Quizzes`.
2. Open an available quiz.
3. Select answers for a few questions if the quiz is playable.
4. Submit only if you are okay modifying demo data.
5. Show results or feedback if available.

### 7.4 Games

1. Click `Games` / `Jeux`.
2. Open a game.
3. Demonstrate one interaction:
   - memory game: click two cards.
   - sorting game: drag or select an item into a category.
   - vocabulary game: flip or move to the next card.
4. Explain that games can award stars and XP.

### 7.5 Writing

1. Click `Writing` / `Ecriture`.
2. Show the writing workspace.
3. Type a short demo text:

   ```text
   Aujourd'hui je revise les fractions avec mon professeur.
   ```

4. Do not submit unless the page clearly supports safe draft saving.

### 7.6 Rewards

1. Click `My Rewards` / `Mes recompenses`.
2. Show stars, XP, level, streaks, badges, and reward history.
3. Explain the seeded example: Yassine has stars, XP, level, and badges.

### 7.7 Progress and skills

1. Click `My Progress` / `Mon progres`.
2. Show charts or progress cards.
3. Click `Skills Passport` / `Passeport de competences`.
4. Show skill dimensions such as mathematics, reading, sciences, creativity, and communication.

What to say: the student side focuses on learning, play, progress, rewards, and simple navigation.

---

## 8. Scene 6 - Parent Portal

Account: Parent.

Log in with:

```text
parent.alaoui@gmail.com
parent123
School ID: 00000000-0000-4000-8000-000000000001
```

### 8.1 Children

1. Click `My Children` / `Mes enfants`.
2. Show linked children: Yassine Alaoui and Omar Benali.
3. Open one child if the page offers a review/detail action.

### 8.2 Feed

1. Click `Feed` / `Fil d'actualite`.
2. Show announcements, grades, attendance alerts, and payment updates.
3. Click a filter and choose one type if available.
4. Click `Mark as read` on a non-critical item if you want to show interaction.

### 8.3 Children's progress

1. Click `Children's Progress` / `Progres des enfants`.
2. Show progress overview.
3. Explain that parents can follow academic evolution without admin access.

### 8.4 Invoices and payment plans

1. Click `Invoices` / `Factures`.
2. Show invoice list with statuses.
3. Open one invoice.
4. Click back, then click `Payment Plans` / `Plans de paiement`.
5. Show installments and plan status.

### 8.5 Absence justification

1. Click `Justify Absence` / `Justifier une absence`.
2. Use demo values if you show the form:

   ```text
   Reason: Medical appointment
   Comment: Demo justification for recording
   ```

3. Attach a file only if you have a safe sample file.
4. Click `Cancel` or leave without submitting if you do not want to change data.

### 8.6 Messages

1. Click `Messages`.
2. Open an existing conversation.
3. Type:

   ```text
   Bonjour, merci pour le suivi de Yassine.
   ```

4. Do not send unless you are comfortable changing demo data.

What to say: the parent portal centralizes children, communication, attendance, progress, billing, and documents.

---

## 9. Scene 7 - Billing, Finance, and Reports

Account: Admin.

Log in with:

```text
admin@ecole-benani.ma
admin123
School ID: 00000000-0000-4000-8000-000000000001
```

### 9.1 Fee structures

1. Click `Fee Structures` / `Frais scolaires`.
2. Show seeded fees such as schooling, transport, canteen, registration.
3. If you open a create form, use:

   ```text
   Name: Recording demo fee
   Amount: 100
   Frequency: Monthly
   ```

4. Click `Cancel` unless you want to save.

### 9.2 Fee assignments and invoice generation

1. Click `Fee Assignments` / `Attribution des frais`.
2. Show which students or classes have fees assigned.
3. Click `Generate Invoices` / `Generer des factures`.
4. Show period/class/student filters.
5. Do not generate new invoices during the video unless you want new demo records.

### 9.3 Invoices

1. Click `Invoices` / `Factures`.
2. Show invoice list.
3. Open one invoice.
4. If there is a PDF or download action, click it and show the bilingual invoice/receipt preview.

### 9.4 Sibling and late-fee policies

1. Click `Sibling Policy` / `Politique fratrie`.
2. Show discount configuration.
3. Click `Late Fees` / `Penalites de retard`.
4. Show delay rules and penalty setup.

### 9.5 Budgets

1. Click `Budgets`.
2. Show the micro-budget.
3. Click `Budget Requests` using direct URL if not visible:

   ```text
   http://localhost:5173/budgets/requests
   ```

4. Show approval workflow.
5. Open analytics:

   ```text
   http://localhost:5173/budgets/analytics
   ```

### 9.6 Financial health

1. Click `Financial Health` / `Sante financiere`, or open:

   ```text
   http://localhost:5173/financial-health
   ```

2. Show retention rate, cost per student, margin, forecasts, and snapshots.

### 9.7 Reports

1. Click `Reports` / `Rapports`.
2. Show report schedules and report jobs.
3. Explain that reports can cover attendance, grades, and finance.

What to say: billing covers fee setup, invoice generation, parent invoices, payment plans, policies, budgets, and financial dashboards.

---

## 10. Scene 8 - Communication, Calendar, Notifications, Documents

Use Admin or Teacher.

### 10.1 Announcements

1. Click `Announcements` / `Annonces`.
2. Show list of seeded announcements.
3. If creating a demo announcement, use:

   ```text
   Title: Recording demo announcement
   Body: This is a demo announcement for the project presentation.
   Audience: All school or 6eme A
   ```

4. Click `Cancel` or `Publish`.

### 10.2 Calendar

1. Click `Calendar` / `Calendrier`.
2. Show events such as open day, exams, excursion, or end-of-year celebration.
3. Click one event to open details.
4. Admin/director only: click `Holidays` / `Jours feries` to show holiday management.

### 10.3 Messages

1. Click `Messages`.
2. Open a conversation.
3. Show the thread and read receipts if visible.
4. Type a demo message only if you do not mind leaving it in the seeded data.

### 10.4 Notifications

1. Click the notification bell in the top bar if visible.
2. Then click `Notifications` in the sidebar.
3. Show categories such as academic, billing, attendance, system, and announcement.
4. Click `Notification Settings` / `Preferences notifications`.
5. Show channel preferences.

### 10.5 Documents and resources

1. Click `Documents`.
2. Show official documents, versions, preview/download actions.
3. Click `Resources` if present, or open:

   ```text
   http://localhost:5173/resources
   ```

4. Show shared lesson plans, worksheets, or exam templates.

What to say: the platform unifies school communication through announcements, calendar, messages, notifications, documents, and resources.

---

## 11. Scene 9 - CMS Content Management

Account: CMS manager.

Log in with:

```text
cms@ecole-platform.ma
content123
School ID: 00000000-0000-4000-8000-000000000001
```

### 11.1 CMS library

1. Open:

   ```text
   http://localhost:5173/cms
   ```

2. Show content library items, statuses, content types, and filters.

### 11.2 Upload content

1. Click `Upload`, or open:

   ```text
   http://localhost:5173/cms/upload
   ```

2. Use sample values if showing the form:

   ```text
   Title: Recording demo story
   Type: Story
   Language: French or Arabic
   Level: CP or 6eme
   ```

3. Do not upload private files. Use only a safe PDF/image from `backend/app/templates/fixtures/` if needed.

### 11.3 Review queue

1. Click `Review`, or open:

   ```text
   http://localhost:5173/cms/review
   ```

2. Show draft/review status workflow.

### 11.4 Quiz builder

1. Click `Quizzes`, or open:

   ```text
   http://localhost:5173/cms/quizzes
   ```

2. Show quiz builder fields and question editing.

What to say: the CMS manager controls educational content, story/coloring assets, review workflow, and quiz authoring.

---

## 12. Scene 10 - Optional Mobile Demo

Only include this if Flutter and an emulator/device are ready.

### What to run

In a new terminal:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
flutter pub get
flutter devices
flutter run
```

If you want to run on Chrome:

```bash
flutter run -d chrome
```

### What to input

Use the student account:

```text
Email: yassine.alaoui@ecole-benani.ma
Password: student123
School ID: 00000000-0000-4000-8000-000000000001
```

### What to click

1. Login.
2. Open the student home screen.
3. Open story reader.
4. Open rewards.
5. Open one game: memory, sorting, or vocabulary.
6. Open coloring if available.
7. Optional: turn Wi-Fi off, show offline state, then turn Wi-Fi back on and show sync.

What to say: mobile is the primary interactive experience for younger students, with stories, games, rewards, coloring, TTS, and offline support.

---

## 13. Scene 11 - Optional Monitoring and Infrastructure

### 13.1 Monitoring

Run:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make monitoring-up
```

Open:

```text
http://localhost:3000
```

Login:

```text
Username: admin
Password: change-me-grafana-admin
```

If your `.env` overrides `GRAFANA_ADMIN_PASSWORD`, use that value instead.

What to click:

1. Click `Dashboards`.
2. Open API overview.
3. Open auth sessions or business education dashboard.
4. Click `Explore`.
5. Choose Loki to show logs, or Prometheus to show metrics.

### 13.2 Docker services

Run:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Show backend, web, PostgreSQL, Redis, MinIO, and optional monitoring services.

### 13.3 API docs

Open:

```text
http://localhost:8000/docs
```

Click these API groups if visible:

1. `auth`
2. `admin`
3. `academic`
4. `lms`
5. `billing`
6. `communication`
7. `content`
8. `reports`

What to say: the project includes API documentation, Dockerized services, monitoring dashboards, logs, metrics, and deployment-ready infrastructure.

---

## 14. Direct URL Cheat Sheet

Use these if sidebar navigation is too slow during recording.

### Admin

```text
http://localhost:5173/admin
http://localhost:5173/admin/users
http://localhost:5173/admin/invitations
http://localhost:5173/admin/audit
http://localhost:5173/admin/features
http://localhost:5173/admin/programs
http://localhost:5173/admin/enrollments
http://localhost:5173/admin/eligibility-rules
http://localhost:5173/analytics
http://localhost:5173/compliance
```

### Teacher and LMS

```text
http://localhost:5173/teacher
http://localhost:5173/teacher/courses
http://localhost:5173/teacher/assignments
http://localhost:5173/teacher/submissions
http://localhost:5173/teacher/attendance
http://localhost:5173/teacher/assessments
http://localhost:5173/teacher/content-library
http://localhost:5173/teacher/quizzes
http://localhost:5173/question-bank
http://localhost:5173/rubrics
http://localhost:5173/gradebook
```

### Student

```text
http://localhost:5173/student/home
http://localhost:5173/student/content
http://localhost:5173/student/quizzes
http://localhost:5173/student/games
http://localhost:5173/student/writing
http://localhost:5173/rewards
http://localhost:5173/progress
http://localhost:5173/skills
```

### Parent

```text
http://localhost:5173/family
http://localhost:5173/feed
http://localhost:5173/parent/progress
http://localhost:5173/invoices
http://localhost:5173/billing/payment-plans
http://localhost:5173/justification
http://localhost:5173/messages
```

### Billing and finance

```text
http://localhost:5173/admin/fee-structures
http://localhost:5173/admin/fee-assignments
http://localhost:5173/admin/generate-invoices
http://localhost:5173/billing/sibling-policy
http://localhost:5173/billing/late-fees
http://localhost:5173/budgets
http://localhost:5173/budgets/requests
http://localhost:5173/budgets/analytics
http://localhost:5173/financial-health
```

### Communication, content, and CMS

```text
http://localhost:5173/announcements
http://localhost:5173/calendar
http://localhost:5173/messages
http://localhost:5173/notifications
http://localhost:5173/documents
http://localhost:5173/resources
http://localhost:5173/reports
http://localhost:5173/cms
http://localhost:5173/cms/upload
http://localhost:5173/cms/review
http://localhost:5173/cms/quizzes
```

---

## 15. Safe Demo Inputs

Use these values when a form needs sample content.

### User or invitation

```text
Full name: Demo Teacher Recording
Email: demo.teacher.recording@ecole-benani.ma
Role: Teacher / TCH
```

### Announcement

```text
Title: Recording demo announcement
Body: This announcement is used for the project video demonstration.
Audience: All school or 6eme A
```

### Assignment

```text
Title: Recording demo assignment
Instructions: Solve exercise 1 and upload your answer.
Points: 20
Due date: next week
```

### Absence justification

```text
Reason: Medical appointment
Comment: Demo justification for recording.
```

### Message

```text
Bonjour, merci pour le suivi de Yassine.
```

### Fee

```text
Name: Recording demo fee
Amount: 100
Frequency: Monthly
```

### CMS content

```text
Title: Recording demo story
Type: Story
Language: French
Level: CP
Description: Short demo content for the project recording.
```

---

## 16. Final Recording Checklist

Before you stop recording, verify:

- [ ] The terminal shows the app started successfully.
- [ ] The browser shows `http://localhost:5173`.
- [ ] The login scene shows email, password, and school ID.
- [ ] At least four roles are shown: admin, teacher, parent, student.
- [ ] Admin dashboard and users are shown.
- [ ] Teacher LMS flow is shown.
- [ ] Student content, games, rewards, and progress are shown.
- [ ] Parent children, feed, invoices, and messages are shown.
- [ ] Billing and reports are shown.
- [ ] Communication and documents are shown.
- [ ] Optional CMS, mobile, monitoring, and API docs are shown if time allows.
- [ ] No private data, API keys, or personal browser tabs appear.

---

## 17. Quick Reset Commands

Use this only when you want a fresh demo database. It deletes local containers and volumes for the dev stack.

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make clean
make up
make migrate
make seed
make health
```

If only the frontend is stuck, restart without deleting data:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make restart
make health
```

---

## 18. Troubleshooting Login and Make Commands

### Admin login says failed

First check that the app can reach the database:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make health
curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@ecole-benani.ma","password":"admin123","school_id":"00000000-0000-4000-8000-000000000001"}'
```

If the curl command returns `access_token`, the backend account is fine. In the browser, use:

```text
Email: admin@ecole-benani.ma
Password: admin123
School ID: 00000000-0000-4000-8000-000000000001
```

If the curl command returns an internal server error and backend logs show `password authentication failed for user "ecole"`, your existing PostgreSQL Docker volume was created with an older password. Align it with `.env`:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
docker compose --env-file .env -f infra/docker-compose.dev.yml exec -T postgres \
  psql -U ecole -d ecole_platform -c "ALTER USER ecole WITH PASSWORD 'ecole';"
docker compose --env-file .env -f infra/docker-compose.dev.yml restart backend worker
make migrate
make seed
make health
```

### `make migrate` fails

Run:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make status
docker logs --tail 80 ecole-backend
```

Common causes:

- PostgreSQL password mismatch: use the fix above.
- Containers are not running: run `make up`.
- Database was reset but not migrated: run `make migrate`, then `make seed`.

### `make seed` fails

Run:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make migrate
make seed
```

If only the optional friend content step fails, you can still record the main platform after the core seed succeeds. The optional assets come from `../ecole-platform-reference/extraction/assets`.
