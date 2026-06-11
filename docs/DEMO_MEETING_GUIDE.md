# Guide de demonstration meeting - Ecole Platform

Ce fichier sert de checklist pour presenter le projet devant un parrain industriel. Il donne les comptes de demo issus du seed, les fenetres a ouvrir, les boutons a cliquer, et l'ordre conseille pour montrer les features sans perdre du temps.

Source des comptes: `seed-report.md`, genere par `make seed`.

---

## 0. Objectif de la demo

Montrer que le projet n'est pas seulement une interface, mais une plateforme scolaire complete:

- Backend FastAPI avec API REST, auth JWT, roles et permissions.
- Frontend web React pour admin, direction et enseignants.
- Application mobile Flutter pour eleves et parents.
- PostgreSQL, Redis, MinIO/S3, Docker, monitoring et CI/CD.
- Modules metier: IAM, ERP scolaire, LMS, communication, facturation, gamification, reporting, conformite.

Duree conseillee: 20 a 30 minutes.

---

## 1. Fenetres a preparer avant le meeting

### Fenetre 1 - Terminal projet

Ouvrir un terminal dans:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
```

Si le projet n'est pas lance:

```bash
make up
make migrate
make seed
make health
make status
```

Si le projet est deja lance:

```bash
make health
make status
```

A montrer rapidement:

- `make health`: prouve que le backend repond.
- `make status`: prouve que les services Docker sont actifs.
- `seed-report.md`: prouve que la base demo contient des comptes, ecoles, classes, factures, messages, contenu, rewards, etc.

### Fenetre 2 - Navigateur web principal

Ouvrir:

```text
http://localhost:5173/login
```

Cette fenetre sert pour la demo principale.

### Fenetre 3 - API Swagger

Ouvrir dans un deuxieme onglet:

```text
http://localhost:8000/docs
```

Ne pas passer trop de temps ici. L'objectif est de montrer que les modules visibles dans l'UI sont exposes par une API documentee.

### Fenetre 4 - Mobile Flutter, optionnel

Seulement si l'emulateur ou Chrome est pret:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
flutter pub get
flutter run
```

ou:

```bash
flutter run -d chrome
```

---

## 2. Identifiants reels de demo

School ID a utiliser dans le champ `School ID` si la page le demande:

```text
00000000-0000-4000-8000-000000000001
```

### Comptes principaux pour la presentation

| Role | Email | Mot de passe | A utiliser pour montrer |
| --- | --- | --- | --- |
| Admin | `admin@ecole-benani.ma` | `admin123` | Dashboard, users, billing, settings, reports, audit |
| Direction | `directeur@ecole-benani.ma` | `director123` | Analytics, reports, attendance analytics |
| Prof maths | `prof.math@ecole-benani.ma` | `teacher123` | Classes, attendance, courses, assignments, quizzes, rubrics |
| Prof francais | `prof.francais@ecole-benani.ma` | `teacher123` | Deuxieme enseignant, contenu francais |
| Parent Alaoui | `parent.alaoui@gmail.com` | `parent123` | Enfants, feed, factures, messages, justifications |
| Eleve Yassine | `yassine.alaoui@ecole-benani.ma` | `student123` | Home eleve, contenu, quiz, jeux, rewards, progress |
| Content manager | `cms@ecole-platform.ma` | `content123` | CMS, upload contenu, review, quiz builder |
| Superadmin | `superadmin@ecole-platform.ma` | `superadmin123` | Plateforme globale, a garder en reserve |
| Micro-school educator | `educateur.micro@ecole-benani.ma` | `teacher123` | Micro-school / educator context |
| Atlas admin | `admin@ecole-atlas.ma` | `admin123` | Multi-tenant second school |
| Atlas teacher | `prof@ecole-atlas.ma` | `teacher123` | Multi-tenant second school |
| Atlas parent | `parent@ecole-atlas.ma` | `parent123` | Multi-tenant second school |
| Atlas student | `enfant@ecole-atlas.ma` | `student123` | Multi-tenant second school |

### Autres comptes seed disponibles

| Role | Email | Mot de passe |
| --- | --- | --- |
| Parent Idrissi | `parent.idrissi@gmail.com` | `parent123` |
| Parent Tazi | `parent.tazi@gmail.com` | `parent123` |
| Parent Fassi | `parent.fassi@gmail.com` | `parent123` |
| Eleve Salma | `salma.idrissi@ecole-benani.ma` | `student123` |
| Eleve Omar | `omar.benali@ecole-benani.ma` | `student123` |
| Eleve Amina CP | `amina.cp@ecole-benani.ma` | `student123` |
| Eleve Karim CE2 | `karim.ce2@ecole-benani.ma` | `student123` |
| Eleve Leila CM2 | `leila.cm2@ecole-benani.ma` | `student123` |
| Eleve Mehdi 3eme | `mehdi.3eme@ecole-benani.ma` | `student123` |
| Eleve Sara Terminale | `sara.terminale@ecole-benani.ma` | `student123` |

Important: ces mots de passe sont des comptes locaux de demo, pas des secrets de production.

---

## 3. Ordre general conseille

1. Terminal: montrer que l'environnement tourne.
2. Swagger: montrer l'API documentee.
3. Admin: montrer back-office, users, school management, billing, reports.
4. Teacher: montrer workflow pedagogique.
5. Student: montrer apprentissage, contenu, jeux, rewards.
6. Parent: montrer suivi enfant, factures, communication.
7. CMS: montrer contenu educatif et review.
8. Optionnel: mobile, monitoring, infra.

Phrase d'intro courte:

```text
Le projet est une plateforme SaaS pour ecoles K-12 au Maroc. J'ai implemente une architecture backend FastAPI, web React et mobile Flutter, avec des modules metier complets: administration, pedagogie, facturation, communication, gamification, reporting et conformite.
```

---

## 3.1 Checklist exhaustive des features a presenter

Utiliser cette section comme anti-oubli. Pendant le meeting, annoncer clairement si une feature est:

- `Seeded real`: vraie donnee creee par `make seed`.
- `Live action`: action que tu peux faire en direct, mais qui modifie la base demo.
- `Mock/conditional`: feature implementee ou documentee, mais depend d'un provider externe, d'un device, ou d'un asset optionnel.

### Auth, IAM, securite

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Login email/password | Seeded real | `/login`, compte admin/teacher/parent/student |
| School scoping | Seeded real | Champ `School ID`, Benani vs Atlas |
| Register avec invitation | Live action | `/register`, code `TCHDMO02` ou `PARDMO01` |
| Invitation codes | Seeded real | Admin -> `Invitations` |
| Email verification | Live action | Apres register, OTP retourne en dev/non-prod |
| Forgot password | Live action | `/forgot-password`, demande OTP reset |
| Reset password | Live action | `/reset-password`, via token/OTP selon flow |
| Logout | Seeded real | Bouton `Logout` en bas sidebar |
| Sessions | Seeded real | `Profile` -> `Sessions` |
| Login history | Seeded real | `Profile` -> `Login History` |
| Change password | Live action | `Profile`, a eviter si tu ne veux pas changer les creds demo |
| TOTP 2FA | Live action | `Profile` -> `2FA`, setup QR puis verify |
| SMS 2FA | Mock/conditional | API Swagger `auth/sms_2fa`, depend provider SMS |
| WebAuthn/passkeys | Mock/conditional | API Swagger `auth/webauthn`, mock row seedee pour UI/security context |
| OAuth social login | Mock/conditional | API Swagger `auth/oauth`, depend Google/Microsoft/Apple config |
| Known devices/locations | Seeded real | Donnees seed auth/security, visible si ecran expose |
| Failed login/account lockout | Seeded real | Donnee seedee + API login en cas mauvais password |
| Password history | Seeded real | Utilisee par change-password/reset-password |
| GDPR / privacy | Seeded real | `/settings/privacy`, consent history/API |

### Admin et gouvernance ecole

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Admin dashboard KPI | Seeded real | `Dashboard` |
| Users and roles | Seeded real | `Users` |
| Director role | Seeded real | Login `directeur@ecole-benani.ma` |
| Audit log | Seeded real | `Audit Log` |
| Feature toggles | Seeded real | `/admin/features` |
| School settings | Seeded real | `School Settings` |
| Batch register | Seeded real/form | `Batch Register` |
| Family links | Seeded real | `Family Links`, parent-child links |
| Multi-tenant | Seeded real | Benani + Atlas accounts |
| Superadmin | Seeded real | `superadmin@ecole-platform.ma`, a garder en reserve |

### Academic / ERP

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Schools | Seeded real | Admin settings + seed report |
| Classes | Seeded real | Teacher `My Classes` |
| Academic year / periods | Seeded real | Seed report, programs/enrollments |
| Enrollments | Seeded real | `Enrollments` |
| Programs | Seeded real | `Programs` |
| Program versions | Seeded real | Ouvrir versions depuis program row |
| Equivalences | Seeded real | `Program Equivalences` |
| Eligibility rules | Seeded real | `Eligibility Rules` |
| Student academic history | Seeded real | Lien detail student si visible |
| Timetable | Seeded real | `Timetable` |
| Timetable constraints | Seeded real | `/timetable/constraints` |
| Timetable generation | Mock/seeded job | `/timetable/generate` |
| Attendance taking | Live action | Teacher -> `Attendance` |
| Attendance history | Seeded real | `/attendance/history` |
| Attendance analytics | Seeded real | `/attendance/analytics` |
| Absence justification | Seeded real/live form | Parent -> `Justification`, Admin -> `Justifications` |
| Gradebook | Seeded real | `/gradebook` |
| Student grades/transcript | Seeded real | Detail depuis gradebook |
| Results | Seeded real | Parent/Student -> `Results` |
| Progress | Seeded real | Student -> `Progress`, Parent -> `Parent Progress` |
| Skill passport | Seeded real | `Skills`, passport, analytics |

### LMS, pedagogie, contenu eleve

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Courses | Seeded real | Teacher -> `Courses` |
| Assignments | Seeded real/form | Teacher -> `Assignments` |
| Submissions | Seeded real | Teacher -> `Submissions`, Student -> `Submissions` |
| Assessment form | Seeded real/form | Teacher -> `Assessments` |
| Quizzes | Seeded real | Teacher -> `Quizzes`, Student -> `Quizzes` |
| Quiz analytics/results | Seeded real | Quiz row analytics, results route |
| Question bank | Seeded real | `Question Bank` |
| Quiz generator | Mock/live form | `/question-bank/generate` |
| Question import | Live form | `/question-bank/import` |
| Rubrics | Seeded real | `Rubrics`, edit/grade routes |
| Writing workspace | Live action | Student -> `Writing` |
| Student content library | Seeded real | Student -> `My Content` |
| Story reader | Seeded real/optional assets | Open content card |
| Coloring viewer | Optional friend assets | Friend content seed, `/student/content/:id/color` |
| Content player video/audio/pdf | Seeded/optional | `/content`, open `Play` |

### AI, gamification, games, rewards

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Student rewards | Seeded real | Student -> `My Rewards` |
| Stars / XP / level / streak | Seeded real | Topbar + rewards page |
| Badges admin | Seeded real | Admin -> `Badges` |
| Leaderboard | Seeded real | Rewards -> class leaderboard |
| Game configs | Seeded real | Teacher/Admin -> `Games` |
| Memory game | Seeded real | Student -> `Games` |
| Sorting game | Seeded real | Student -> `Games` |
| Vocabulary cards | Seeded real | Student -> `Games` |
| Activities | Seeded real | `Activities` |
| Difficulty adaptation | Seeded real | Seed report + progress context |
| AI preferences | Seeded real | Seed extensions, mention in architecture |

### Parent portal

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| My children | Seeded real | Parent -> `My Children` |
| Shared review | Seeded real | Child review/detail if visible |
| Parent feed | Seeded real | Parent -> `Feed` |
| Children progress | Seeded real | Parent -> `Parent Progress` |
| Invoices | Seeded real | Parent -> `Invoices` |
| Payment plans | Seeded real | Parent/Admin -> `Payment Plans` |
| Absence justification | Live form | Parent -> `Justification` |
| Parent documents | Seeded real | Parent -> `Documents` |
| Parent messaging | Seeded real/live | Parent -> `Messages` |

### Billing, finance, reports

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Fee structures | Seeded real | Admin -> `Fee Structures` |
| Fee assignments | Seeded real | Admin -> `Fee Assignments` |
| Invoice generation | Live form | Admin -> `Generate Invoices` |
| Invoices | Seeded real | `Invoices` |
| PDF invoice/receipt | Seeded/conditional | Invoice detail download |
| Payment proofs | Seeded real | Invoice/payment detail if visible |
| Provider webhook events | Seeded real | Mention billing backend/API |
| Sibling discount policy | Seeded real | `Sibling Policy` |
| Late fee policy | Seeded real | `Late Fees` |
| Payment plans/installments | Seeded real | `Payment Plans` |
| Budgets | Seeded real | `Budgets` |
| Budget requests | Seeded real | `/budgets/requests` |
| Budget analytics | Seeded real | `/budgets/analytics` |
| Financial health | Seeded real | `/financial-health` |
| Financial snapshots/export | Seeded real | `/financial-health/snapshots`, `/financial-health/export` |
| Report schedules/jobs | Seeded real | `Reports` |
| Analytics dashboard | Seeded real | `/analytics` |

### Communication, documents, CMS

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Announcements | Seeded real/live form | `Announcements` |
| Calendar events | Seeded real | `Calendar` |
| Event detail / RSVP | Seeded real | Click event |
| Holiday manager | Seeded real | `/calendar/holidays` |
| Messages/chat | Seeded real/live | `Messages` |
| Read receipts | Seeded real | Existing conversation |
| Notifications | Seeded real | Bell + `Notifications` |
| Notification preferences | Seeded real | `Notification Settings` |
| Push device tokens | Seeded real | Seeded backend/device records |
| Documents | Seeded real | `Documents` |
| Document versions | Seeded real | Document detail versions |
| Document preview | Seeded/conditional | Preview route |
| Resources | Seeded real | `/resources` |
| CMS content list | Seeded real | `/cms` |
| CMS upload | Live form | `/cms/upload` |
| CMS edit | Seeded real | Content row edit |
| CMS review queue | Seeded real | `/cms/review` |
| CMS quiz builder | Seeded real/form | `/cms/quizzes` |
| CMS analytics | Seeded real | `/cms/analytics` |
| Friend Arabic content | Optional real assets | `make seed-friend-content`, stories/coloring/audio/video |

### Sync, mobile, infra

| Feature | Type demo | Ou cliquer / montrer |
| --- | --- | --- |
| Offline/sync status | Seeded real | `/sync` for ADM/DIR |
| Sync conflicts | Seeded real | `/sync/conflicts` |
| Sync settings | Seeded real/form | `/sync/settings` |
| Upload sessions | Seeded real | Backend upload lifecycle, mention MinIO |
| Direct S3/MinIO upload | Conditional | MinIO + signed URLs |
| Flutter mobile | Conditional | Run `flutter run` |
| Browser/web app | Seeded real | React app |
| Swagger API docs | Real | `http://localhost:8000/docs` |
| Docker compose | Real | `make status` |
| PostgreSQL/Redis | Real | `make status`, architecture |
| MinIO object storage | Conditional | `http://localhost:9001` |
| Monitoring Grafana/Prometheus/Loki/Tempo | Conditional | `make monitoring-up`, `http://localhost:3000` |
| Kubernetes/Helm/CI-CD | Code/docs real | `infra/`, `.github/workflows`, deployment docs |

---

## 3.2 Scene auth obligatoire - Register, Login, Recovery, 2FA

Cette scene doit etre faite avant le login admin si tu veux prouver tout le flow d'auth.

### Register avec invitation

1. Ouvrir:

   ```text
   http://localhost:5173/register
   ```

2. Montrer le formulaire.
3. Pour une demo sans modifier la base, remplir mais ne pas soumettre:

   ```text
   Code: TCHDMO02
   Email: demo.teacher.meeting@ecole-benani.ma
   Full name: Demo Teacher Meeting
   Phone: +212600000001
   Password: DemoTeacher123!
   ```

4. Si tu veux prouver le flow reel, cliquer `Register` / `S'inscrire`. Attention: le code est single-use. Pour refaire la demo proprement, relancer `make seed`.
5. Apres register, montrer que l'OTP email est retourne en environnement dev/non-prod si visible.

Codes disponibles apres seed:

| Code | Role | Usage |
| --- | --- | --- |
| `TCHDMO02` | Teacher | Demo register teacher |
| `PARDMO01` | Parent | Demo register parent |
| `USEDPAR3` | Parent | Code deja consomme, pour montrer l'erreur |

### Login

1. Ouvrir:

   ```text
   http://localhost:5173/login
   ```

2. Montrer les champs `Email`, `Password`, `School ID`.
3. Faire un login reel avec admin ou teacher.
4. Dire que la navigation depend du role renvoye par le backend.

### Forgot / reset password

1. Sur la page login, cliquer `Forgot password` / `Mot de passe oublie`.
2. Saisir:

   ```text
   parent.alaoui@gmail.com
   ```

3. Montrer que le flow cree une demande de recovery sans exposer si l'email existe.
4. Ne pas changer le mot de passe principal pendant le meeting sauf si tu comptes relancer `make seed` apres.

### 2FA, WebAuthn, OAuth

1. Connecte admin, cliquer `Profile`.
2. Cliquer `2FA`.
3. Montrer setup TOTP QR/provisioning.
4. Mentionner:
   - TOTP est live dans l'app.
   - SMS 2FA depend du provider SMS.
   - WebAuthn/passkeys depend du navigateur/device.
   - OAuth depend des credentials Google/Microsoft/Apple.
5. Ouvrir Swagger si le parrain veut voir les endpoints `auth/webauthn`, `auth/oauth`, `auth/sms_2fa`.

---

## 4. Scene 1 - Demarrage technique

### Fenetre a utiliser

Fenetre 1: terminal projet.

### Actions

1. Cliquer dans le terminal.
2. Executer:

   ```bash
   make health
   ```

3. Executer:

   ```bash
   make status
   ```

4. Ouvrir le fichier:

   ```bash
   less seed-report.md
   ```

5. Montrer rapidement les sections `Login Credentials`, `Classes`, `Billing`, `Gamification`, `Messaging`, `Documents`.

### Ce qu'il faut dire

```text
Avant de montrer l'interface, je montre que l'environnement est lance avec Docker, que le backend est healthy, et que la base demo est seedee avec des donnees realistes: ecole, classes, eleves, parents, factures, paiements, absences, messages, contenus et recompenses.
```

---

## 5. Scene 2 - API documentee

### Fenetre a utiliser

Fenetre 3: onglet Swagger.

### Actions

1. Cliquer l'onglet `http://localhost:8000/docs`.
2. Montrer les groupes d'endpoints.
3. Cliquer/ouvrir visuellement ces sections si elles apparaissent:
   - `auth`
   - `admin`
   - `academic`
   - `lms`
   - `billing`
   - `communication`
   - `content`
   - `reports`

### Ce qu'il faut dire

```text
Toutes les features UI reposent sur une API REST documentee. L'API est structuree par domaines: auth, admin, academic, LMS, billing, communication, content et reports.
```

---

## 6. Scene 3 - Login admin et back-office

### Fenetre a utiliser

Fenetre 2: navigateur web principal.

### Login

1. Aller a:

   ```text
   http://localhost:5173/login
   ```

2. Dans `Email`, saisir:

   ```text
   admin@ecole-benani.ma
   ```

3. Dans `Password`, saisir:

   ```text
   admin123
   ```

4. Dans `School ID`, saisir:

   ```text
   00000000-0000-4000-8000-000000000001
   ```

5. Cliquer sur `Sign In` ou `Se connecter`.

### Clics a faire dans l'ordre

1. Cliquer menu lateral `Tableau de bord` / `Dashboard`.
   - Montrer les KPI admin: utilisateurs, sessions, invitations, audit events, justifications.
   - Dire: `Le dashboard donne une vue de pilotage de l'ecole.`

2. Cliquer `Utilisateurs` / `Users`.
   - Montrer la table des comptes seedes.
   - Dans le champ recherche, taper `prof`.
   - Effacer la recherche.
   - Dire: `Ici l'admin gere les comptes et roles.`

3. Cliquer `Invitations`.
   - Montrer la liste.
   - Si bouton `Create`, `New`, `Nouvelle invitation` ou equivalent existe, cliquer dessus.
   - Remplir seulement pour montrer le formulaire:

     ```text
     Email: demo.teacher.meeting@ecole-benani.ma
     Role: Teacher / TCH
     ```

   - Cliquer `Cancel` / `Annuler`.
   - Dire: `Le systeme supporte l'onboarding par invitation.`

4. Cliquer `Journal d'audit` / `Audit Log`.
   - Montrer les evenements.
   - Dire: `Les actions sensibles sont tracables pour la securite et la conformite.`

5. Ouvrir directement:

   ```text
   http://localhost:5173/admin/features
   ```

   - Montrer les feature toggles: gamification, rewards, skill passport, difficulty adaptation, parent dashboard.
   - Ne pas desactiver de toggle.
   - Dire: `Les features peuvent etre activees par role ou par ecole.`

6. Cliquer `Programmes` / `Programs`.
   - Montrer les programmes academiques.
   - Cliquer ensuite `Inscriptions` / `Enrollments`.
   - Cliquer `Equivalences` / `Program Equivalences`.
   - Cliquer `Eligibility Rules` / `Regles d'eligibilite`.
   - Dire: `Cette partie gere le parcours academique, les inscriptions et les regles d'eligibilite.`

7. Cliquer `Compliance` / `Conformite`.
   - Montrer le dashboard MEN/GDPR si charge.
   - Ouvrir aussi:

     ```text
     http://localhost:5173/compliance/mapping
     ```

   - Dire: `Le module conformite relie programmes, objectifs et preuves de couverture.`

---

## 7. Scene 4 - Facturation, finance et rapports admin

### Fenetre a utiliser

Fenetre 2, toujours connecte admin.

### Clics a faire dans l'ordre

1. Cliquer `Fee Structures` / `Frais scolaires`.
   - Montrer les frais seedes: scolarite, transport, cantine, inscription, parascolaire.
   - Si bouton creation visible, cliquer puis annuler apres avoir montre les champs.

2. Cliquer `Fee Assignments` / `Attribution des frais`.
   - Montrer affectation des frais aux eleves/classes.

3. Cliquer `Generate Invoices` / `Generer des factures`.
   - Montrer les filtres periode/classe/eleve.
   - Ne pas generer de nouvelles factures pendant la demo sauf si necessaire.

4. Cliquer `Invoices` / `Factures`.
   - Ouvrir une facture.
   - Si un bouton `Download PDF`, `Receipt`, `Invoice PDF` ou `Telecharger` existe, cliquer pour montrer la generation PDF bilingue.

5. Cliquer `Sibling Policy` / `Politique fratrie`.
   - Montrer reduction fratrie.

6. Cliquer `Late Fees` / `Penalites de retard`.
   - Montrer regles de retard.

7. Cliquer `Payment Plans` / `Plans de paiement`.
   - Montrer echeances et statut.

8. Cliquer `Budgets`.
   - Montrer le micro-budget seed: 50 000 MAD, allocations, demandes, transactions.
   - Ouvrir:

     ```text
     http://localhost:5173/budgets/requests
     http://localhost:5173/budgets/analytics
     ```

9. Cliquer `Financial Health` / `Sante financiere`, ou ouvrir:

   ```text
   http://localhost:5173/financial-health
   ```

   - Montrer retention rate, cost/student, margin, cashflow forecasts.

10. Cliquer `Reports` / `Rapports`.
    - Montrer les report schedules et jobs.

### Ce qu'il faut dire

```text
La partie finance couvre toute la chaine: configuration des frais, affectation, generation de factures, paiements, plans de paiement, politiques de remise/retard, budgets et indicateurs financiers.
```

---

## 8. Scene 5 - Enseignant et workflow pedagogique

### Changer de compte

1. Cliquer `Logout` / `Deconnexion` en bas du menu lateral.
2. Se reconnecter avec:

   ```text
   Email: prof.math@ecole-benani.ma
   Password: teacher123
   School ID: 00000000-0000-4000-8000-000000000001
   ```

### Clics a faire dans l'ordre

1. Cliquer `My Classes` / `Mes classes`.
   - Montrer les classes affectees, par exemple `6eme A`.
   - Dire: `Le professeur voit seulement ses classes.`

2. Cliquer `Attendance` / `Presence`.
   - Selectionner une classe si un select apparait.
   - Montrer la prise de presence.
   - Si des boutons de statut existent, cliquer une fois sur `Present` ou `Absent`, puis remettre l'etat initial si possible.
   - Cliquer `Save` / `Enregistrer` uniquement si tu acceptes de modifier la demo.

3. Cliquer `Courses` / `Cours`.
   - Montrer les cours existants.
   - Si bouton `New` / `Create` existe, cliquer puis annuler apres avoir montre les champs:

     ```text
     Title: Demo fractions
     Subject: Mathematics
     Class: 6eme A
     ```

4. Cliquer `Assignments` / `Devoirs`.
   - Montrer formulaire/liste de devoirs.
   - Si creation visible, saisir comme exemple puis annuler:

     ```text
     Title: Devoir demo fractions
     Instructions: Resoudre l'exercice 1 et deposer la reponse.
     Points: 20
     ```

5. Cliquer `Assessments` / `Evaluations`.
   - Montrer saisie des notes/evaluations.

6. Ouvrir directement:

   ```text
   http://localhost:5173/gradebook
   ```

   - Montrer carnet de notes, detail eleve, moyenne et publication des resultats.

7. Cliquer `Content Library` / `Bibliotheque de contenu`.
   - Montrer contenus disponibles et affectation a une classe.

8. Cliquer `Quizzes`.
   - Montrer `Quiz Fractions` si visible.
   - Ouvrir un quiz ou ses analytics si l'action est visible.

9. Cliquer `Question Bank` / `Banque de questions`.
   - Montrer filtres par matiere, niveau, difficulte.
   - Cliquer `Generate Quiz` / `Generer un quiz` si visible.
   - Revenir en arriere.

10. Cliquer `Rubrics` / `Grilles d'evaluation`.
    - Ouvrir une rubric existante.
    - Montrer criteres, niveaux et notation.

11. Cliquer `Class Progress` / `Progression classe`.
    - Montrer suivi de progression.

### Ce qu'il faut dire

```text
Cote enseignant, j'ai implemente le cycle pedagogique complet: classes, presence, cours, devoirs, quiz, banque de questions, rubrics, notes et progression.
```

---

## 9. Scene 6 - Eleve: experience learning, jeux et rewards

### Changer de compte

1. Cliquer `Logout` / `Deconnexion`.
2. Se connecter avec:

   ```text
   Email: yassine.alaoui@ecole-benani.ma
   Password: student123
   School ID: 00000000-0000-4000-8000-000000000001
   ```

### Clics a faire dans l'ordre

1. Cliquer `Student Home` / `Accueil eleve`.
   - Montrer l'interface simplifiee pour eleve.
   - Montrer les stats en haut si visibles: stars, XP, streak.

2. Cliquer `My Content` / `Mon contenu`.
   - Ouvrir une carte de contenu.
   - Si bouton `Read`, `Lire`, `Play` ou `Commencer` existe, cliquer.
   - Revenir a la liste avec le bouton retour.

3. Cliquer `Quizzes`.
   - Ouvrir un quiz.
   - Selectionner une ou deux reponses.
   - Ne soumettre que si tu acceptes de modifier l'historique.

4. Cliquer `Games` / `Jeux`.
   - Ouvrir un jeu.
   - Demonstration rapide:
     - Memory: cliquer deux cartes.
     - Sorting: deplacer ou choisir un item.
     - Vocabulary: passer a la carte suivante.

5. Cliquer `Writing` / `Ecriture`.
   - Taper:

     ```text
     Aujourd'hui je revise les fractions avec mon professeur.
     ```

   - Ne pas soumettre si tu veux garder la base propre.

6. Cliquer `My Rewards` / `Mes recompenses`.
   - Montrer stars, XP, level, badges, streak et historique.
   - Seed attendu pour Yassine: 25 stars, 350 XP, niveau 3, badges `first_login`, `streak_7`, `xp_250`.

7. Cliquer `My Progress` / `Mon progres`.
   - Montrer graphiques ou cartes.

8. Cliquer `Skills` / `Competences`.
   - Montrer les dimensions: Mathematiques, Lecture, Sciences, Creativite, Communication.

### Ce qu'il faut dire

```text
L'interface eleve est plus simple et plus engageante. Elle combine contenu, quiz, jeux, ecriture, progression et gamification pour motiver l'apprentissage.
```

---

## 10. Scene 7 - Parent: suivi enfant, paiement et communication

### Changer de compte

1. Cliquer `Logout` / `Deconnexion`.
2. Se connecter avec:

   ```text
   Email: parent.alaoui@gmail.com
   Password: parent123
   School ID: 00000000-0000-4000-8000-000000000001
   ```

### Clics a faire dans l'ordre

1. Cliquer `My Children` / `Mes enfants`.
   - Montrer Yassine Alaoui et Omar Benali.
   - Ouvrir un detail ou review si le bouton est visible.

2. Cliquer `Feed` / `Fil d'actualite`.
   - Montrer les nouvelles: notes, absence, facturation, annonces.
   - Si filtre visible, filtrer par categorie puis revenir a `All`.

3. Cliquer `Children Progress` / `Progression des enfants`.
   - Montrer suivi academic parent.

4. Cliquer `Invoices` / `Factures`.
   - Ouvrir une facture.
   - Montrer status, montant, paiement.

5. Cliquer `Payment Plans` / `Plans de paiement`.
   - Montrer echeances.

6. Cliquer `Justify Absence` / `Justification`.
   - Montrer le formulaire.
   - Exemple a saisir sans soumettre:

     ```text
     Reason: Medical appointment
     Comment: Demo justification pour la presentation.
     ```

7. Cliquer `Messages`.
   - Ouvrir une conversation.
   - Montrer thread et read receipts si visibles.
   - Ne pas envoyer de message sauf si tu acceptes de modifier les donnees.

8. Cliquer `Documents`.
   - Montrer bulletins, certificats, autorisations ou documents partages.

### Ce qu'il faut dire

```text
Le parent a une vue limitee a ses enfants: progression, factures, absences, messages, documents et actualites. C'est important pour la separation des roles et la confidentialite.
```

---

## 11. Scene 8 - Communication commune

### Compte conseille

Admin ou Teacher.

### Clics a faire

1. Cliquer `Announcements` / `Annonces`.
   - Montrer annonces seed.
   - Si bouton creation visible, cliquer puis annuler.

2. Cliquer `Calendar` / `Calendrier`.
   - Montrer portes ouvertes, examens, excursion, fete de fin d'annee.
   - Cliquer un evenement pour ouvrir le detail.

3. Cliquer l'icone cloche dans la topbar.
   - Montrer quick view notifications.
   - Cliquer `View all` / `Voir tout`.

4. Cliquer `Notification Settings` / `Preferences notifications`.
   - Montrer preferences par canal.

5. Cliquer `Documents`.
   - Ouvrir un document ou preview si disponible.

6. Ouvrir:

   ```text
   http://localhost:5173/resources
   ```

   - Montrer ressources partagees.

### Ce qu'il faut dire

```text
Le module communication regroupe annonces, calendrier, notifications temps reel, messages, documents et ressources, avec des droits differents selon le role.
```

---

## 12. Scene 9 - CMS content manager

### Changer de compte

1. Cliquer `Logout` / `Deconnexion`.
2. Se connecter avec:

   ```text
   Email: cms@ecole-platform.ma
   Password: content123
   School ID: 00000000-0000-4000-8000-000000000001
   ```

### Clics a faire dans l'ordre

1. Ouvrir:

   ```text
   http://localhost:5173/cms
   ```

   - Montrer liste des contenus.

2. Cliquer `Upload`.
   - Montrer formulaire upload.
   - Exemple a saisir sans uploader:

     ```text
     Title: Demo story CP
     Type: Story
     Language: Arabic
     Level: CP
     ```

3. Cliquer `Review`.
   - Montrer queue de validation.

4. Cliquer `Quizzes`.
   - Montrer quiz builder.

5. Cliquer `Analytics`.
   - Montrer analytics CMS si disponible.

### Ce qu'il faut dire

```text
Le CMS separe la creation de contenu educatif du reste de l'administration. Il supporte upload, review, quiz builder et analytics de contenu.
```

### Mentionner le contenu friend seed

Dire:

```text
Le seed friend ajoute aussi du contenu arabe pour les petits niveaux: histoires interactives de Sami, coloriages, audio, PDF, videos et quiz.
```

Details issus de `seed-friend-report.md`:

- 4 stories interactives.
- 33 coloring pages.
- 10 fichiers audio.
- 5 PDF.
- 2 videos.
- 6 images mascot.
- 1 quiz MCQ.

---

## 13. Scene 10 - Mobile Flutter, optionnel

### Fenetre a utiliser

Fenetre 4: mobile ou Chrome Flutter.

### Login conseille

```text
Email: yassine.alaoui@ecole-benani.ma
Password: student123
School ID: 00000000-0000-4000-8000-000000000001
```

### Clics a faire

1. Cliquer `Login`.
2. Ouvrir `Student Home`.
3. Ouvrir `Content`.
4. Ouvrir une story.
5. Ouvrir `Rewards`.
6. Ouvrir `Games` ou un jeu direct si disponible.
7. Ouvrir `Notifications`.
8. Ouvrir `Profile`.

### Ce qu'il faut dire

```text
La strategie cross-platform est volontaire: web-first pour admin/teacher, mobile-first pour student/parent. Le mobile garde les memes domaines metier mais avec une navigation plus adaptee aux usages rapides et aux jeunes eleves.
```

---

## 14. Scene 11 - Monitoring et infra, optionnel

### Monitoring

Dans le terminal:

```bash
make monitoring-up
```

Ouvrir:

```text
http://localhost:3000
```

Compte Grafana monitoring:

```text
Username: admin
Password: change-me-grafana-admin
```

Si `.env` surcharge `GRAFANA_ADMIN_USER` ou `GRAFANA_ADMIN_PASSWORD`, utiliser les valeurs de `.env`. Si une instance ancienne a ete lancee avec la doc historique, essayer aussi `admin` / `admin`.

Clics:

1. Cliquer `Dashboards`.
2. Ouvrir un dashboard API ou education/business.
3. Cliquer `Explore`.
4. Montrer Prometheus ou Loki si configure.

### MinIO

Ouvrir si utile:

```text
http://localhost:9001
```

Identifiants dev par defaut:

```text
Username: minioadmin
Password: minioadmin123
```

Dire:

```text
Le stockage objet sert aux documents, uploads, PDFs, contenus et assets. En dev c'est MinIO, en production ca peut etre S3 compatible.
```

---

## 15. Cheat sheet URLs rapides

### Admin

```text
http://localhost:5173/admin
http://localhost:5173/admin/users
http://localhost:5173/admin/invitations
http://localhost:5173/admin/audit
http://localhost:5173/admin/features
http://localhost:5173/admin/programs
http://localhost:5173/admin/enrollments
http://localhost:5173/admin/program-equivalences
http://localhost:5173/admin/eligibility-rules
http://localhost:5173/compliance
```

### Teacher

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
http://localhost:5173/documents
```

### Billing et finance

```text
http://localhost:5173/admin/fee-structures
http://localhost:5173/admin/fee-assignments
http://localhost:5173/admin/generate-invoices
http://localhost:5173/billing/sibling-policy
http://localhost:5173/billing/late-fees
http://localhost:5173/billing/payment-plans
http://localhost:5173/budgets
http://localhost:5173/budgets/requests
http://localhost:5173/budgets/analytics
http://localhost:5173/financial-health
http://localhost:5173/reports
```

### Communication, content, CMS

```text
http://localhost:5173/announcements
http://localhost:5173/calendar
http://localhost:5173/messages
http://localhost:5173/notifications
http://localhost:5173/settings/notifications
http://localhost:5173/documents
http://localhost:5173/resources
http://localhost:5173/content
http://localhost:5173/cms
http://localhost:5173/cms/upload
http://localhost:5173/cms/review
http://localhost:5173/cms/quizzes
http://localhost:5173/cms/analytics
```

---

## 16. Donnees seed a mentionner pendant la demo

Ces chiffres donnent de la credibilite au projet:

- 2 ecoles: Ecole Benani et Ecole Atlas.
- Classes: 6eme A, 6eme B, 5eme A, CP A, CE2 A, CM2 A, 3eme A, Terminale A.
- Parents lies aux enfants: Parent Alaoui -> Yassine et Omar.
- Academic year 2025-2026 avec periode 1 fermee et periode 2 active.
- Courses: Mathematiques 6eme, Francais 6eme.
- Quizzes: Quiz Fractions, Quiz Grammaire.
- Billing: 18 factures, payment proofs, webhook events, 2 payment plans.
- Gamification: stars, XP, levels, badges, streaks.
- Skill passport: 5 dimensions x 3 niveaux.
- Attendance: environ 45 sessions et alertes d'absence.
- Messaging: 5 conversations et read receipts.
- Calendar: 8 events avec RSVPs et reminders.
- Documents: bulletins, certificats, autorisations, ressources partagees.
- Reports: schedules et jobs.
- Feature toggles: gamification, rewards, skill passport, difficulty adaptation, parent dashboard v2.
- Auth/security: invitation codes demo, login history, known devices/locations, failed login, password history, recovery request, mock OAuth/WebAuthn records.

---

## 17. Plan court si le meeting dure seulement 10 minutes

1. Terminal: `make health` et `make status` - 1 min.
2. Auth: ouvrir `Register`, montrer code `TCHDMO02`, puis login admin - 1 min.
3. Swagger: montrer API docs - 1 min.
4. Admin: dashboard, users, audit, billing - 2 min.
5. Teacher: classes, attendance, quizzes, gradebook - 2 min.
6. Student: content, games, rewards - 2 min.
7. Parent: children, invoices, messages - 1 min.

Ne pas ouvrir CMS, mobile, monitoring sauf si le parrain pose des questions.

---

## 18. Questions probables du parrain et reponses rapides

### Est-ce que c'est multi-role?

Oui. Les roles seedes sont Admin, Direction, Teacher, Parent, Student, Content Manager, Superadmin. La navigation et les routes sont protegees par role.

### Est-ce que c'est multi-tenant?

Oui. Le seed contient Ecole Benani avec dataset complet et Ecole Atlas avec dataset minimal. Les donnees sont scopees par `school_id`.

### Est-ce que les parents voient tous les eleves?

Non. Le parent voit seulement ses enfants lies. Exemple: `parent.alaoui@gmail.com` voit Yassine Alaoui et Omar Benali.

### Est-ce que l'application est seulement web?

Non. Web React pour admin/teacher, mobile Flutter pour student/parent, avec backend commun.

### Est-ce qu'il y a de la securite?

Oui. Auth JWT, roles/permissions, 2FA/TOTP/WebAuthn/OAuth documentes, audit log, isolation school_id, gestion sessions et historique login.

### Est-ce que les donnees sont reelles?

Ce sont des donnees de demonstration seedees: classes, parents, eleves, factures, absences, messages, contenu, rewards et historique auth. Les parties qui dependent d'un fournisseur externe ou d'un device, comme OAuth, SMS 2FA, WebAuthn, MinIO assets optionnels ou monitoring, sont clairement presentees comme mock/conditional.

---

## 19. Phrase de conclusion

```text
En conclusion, j'ai construit une plateforme scolaire complete avec un backend structure par domaines, un web app role-based, une app mobile, une base de donnees seedee realiste, des workflows metier complets et une infrastructure Docker/monitoring. La demo montre la chaine complete: admin configure, teacher enseigne, student apprend, parent suit, et le systeme trace, facture, notifie et reporte.
```
