# Guide de demonstration - Ecole Platform

Objectif: presenter le projet devant un parrain industriel en montrant le travail reel: backend FastAPI, frontend React, mobile Flutter, seed data, securite/RBAC, LMS, ERP scolaire, facturation, gamification, communication, documents, reporting et observabilite.

Ce guide est base sur:
- `README.md`
- `docs/INSTALLATION.md`
- `web/README.md`
- `seed-report.md`
- `seed-friend-report.md`
- `Makefile`
- `web/src/app/App.tsx`
- `web/src/widgets/layout/Layout.tsx`

Important: les identifiants ci-dessous sont des comptes de demo/dev issus du seed. Ne pas les utiliser en production.

---

## 1. Fenetres a preparer avant le meeting

Ouvrir ces fenetres dans cet ordre.

### Fenetre 1 - Terminal projet

Repertoire:

```bash
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
```

Commandes a lancer avant la demo:

```bash
make up
make migrate
make seed
make health
```

Resultat attendu pour `make health`:

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

Si tu veux montrer le monitoring:

```bash
make monitoring-up
```

### Fenetre 2 - Web app

URL:

```text
http://localhost:5173
```

Si le conteneur web n'est pas lance, ouvrir un deuxieme terminal:

```bash
cd web
npm install
npm run dev
```

### Fenetre 3 - API Swagger

URL:

```text
http://localhost:8000/docs
```

A montrer rapidement pour prouver que le backend expose une API REST documentee.

### Fenetre 4 - Monitoring optionnel

Lancer:

```bash
make monitoring-up
```

URLs:

```text
Grafana:      http://localhost:3000
Prometheus:  http://localhost:9090
Alertmanager http://localhost:9093
```

Credentials Grafana dans ce repo:

```text
User:     admin
Password: change-me-grafana-admin
```

Si `.env` contient `GRAFANA_ADMIN_PASSWORD`, utiliser cette valeur. Certains anciens docs indiquent `admin/admin`, mais le compose actuel utilise `change-me-grafana-admin` par defaut.

### Fenetre 5 - Fichiers preuve

Garder ouverts dans ton editeur:

```text
README.md
seed-report.md
seed-friend-report.md
web/README.md
backend/docs/API-REFERENCE.md
docs/SECURITY.md
docs/ARCHITECTURE.md
```

---

## 2. Comptes reels de demonstration

School ID par defaut:

```text
00000000-0000-4000-8000-000000000001
```

Le champ "Identifiant ecole" du login est normalement deja rempli avec cette valeur.

### Seed principal Ecole Benani

| Role | Email | Password | A utiliser pour |
|---|---|---|---|
| Admin | `admin@ecole-benani.ma` | `admin123` | Admin, users, facturation, audit, badges, settings |
| Director | `directeur@ecole-benani.ma` | `director123` | Analytics, reports, pilotage |
| Teacher Math | `prof.math@ecole-benani.ma` | `teacher123` | Classes, presence, quiz, LMS, jeux |
| Teacher French | `prof.francais@ecole-benani.ma` | `teacher123` | Deuxieme enseignant |
| Parent Alaoui | `parent.alaoui@gmail.com` | `parent123` | Enfants, paiement, feed, progression |
| Parent Idrissi | `parent.idrissi@gmail.com` | `parent123` | Parent alternatif |
| Parent Tazi | `parent.tazi@gmail.com` | `parent123` | Parent CP |
| Parent Fassi | `parent.fassi@gmail.com` | `parent123` | Parent CE2 |
| Student Yassine | `yassine.alaoui@ecole-benani.ma` | `student123` | Eleve 6eme, rewards riches |
| Student Salma | `salma.idrissi@ecole-benani.ma` | `student123` | Eleve 6eme |
| Student Omar | `omar.benali@ecole-benani.ma` | `student123` | Eleve 6eme |
| Student Amina CP | `amina.cp@ecole-benani.ma` | `student123` | Jeune eleve, contenu age-banded |
| Student Karim CE2 | `karim.ce2@ecole-benani.ma` | `student123` | Eleve primaire |
| Student Leila CM2 | `leila.cm2@ecole-benani.ma` | `student123` | Eleve primaire avance |
| Student Mehdi 3eme | `mehdi.3eme@ecole-benani.ma` | `student123` | College |
| Student Sara Terminale | `sara.terminale@ecole-benani.ma` | `student123` | Lycee |
| Superadmin | `superadmin@ecole-platform.ma` | `superadmin123` | Plateforme globale |
| Content Manager | `cms@ecole-platform.ma` | `content123` | CMS, contenus, banque de questions |

### Comptes generiques alternatifs

Si l'environnement a ete seed avec le README classique plutot qu'avec `seed-report.md`:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ecole.test` | `Admin123!` |
| Teacher | `teacher@ecole.test` | `Teacher123!` |
| Parent | `parent@ecole.test` | `Parent123!` |
| Student | `student@ecole.test` | `Student123!` |

---

## 3. Donnees importantes a citer pendant la demo

Ces chiffres viennent de `seed-report.md` et du README.

- 2 ecoles: Ecole Benani, Ecole Atlas.
- Classes: 6eme A, 6eme B, 5eme A, CP A, CE2 A, CM2 A, 3eme A, Terminale A.
- Annee academique 2025-2026 avec deux periodes.
- 18 factures avec statuts pending, paid, failed, canceled.
- Plans de paiement, preuves de paiement et webhooks PSP.
- Gamification: etoiles, XP, niveaux, badges, streaks et leaderboard.
- Skill Passport: 5 dimensions, 3 niveaux.
- LMS: cours, quiz, devoirs, soumissions, rubriques, banque de questions.
- Communication: conversations, annonces, notifications, calendrier, feed parent.
- Documents: bulletins, certificats, ressources, versions, preview.
- Reporting: schedules et jobs.
- Multi-tenant: Ecole Benani riche, Ecole Atlas minimal.
- Feature toggles actives: gamification, rewards, skill_passport, difficulty_adaptation, parent_dashboard_v2.

Si `seed-friend-content` a tourne:

- 4 stories interactives.
- 33 pages de coloriage.
- 10 narrations audio.
- 5 PDFs.
- 2 videos.
- 6 images mascotte.
- 1 quiz QCM.

---

## 4. Script oral d'introduction

Phrase courte:

```text
J'ai construit une plateforme SaaS scolaire K-12 pour les ecoles marocaines. Elle couvre l'administration, le LMS, les parents, les eleves, la facturation, la gamification, les documents, la communication et l'observabilite. La demo utilise un seed realiste, avec plusieurs roles et une ecole fictive complete: Ecole Benani.
```

Ensuite ouvrir la Fenetre 3 Swagger et dire:

```text
Le backend est une API FastAPI documentee. Le frontend React consomme ces endpoints, et le mobile Flutter partage les memes domaines metier.
```

---

## 5. Parcours de demonstration complet par ordre

Temps conseille: 18 a 25 minutes.

### Etape 1 - Login Admin

Fenetre: Web app `http://localhost:5173`.

1. Cliquer dans le champ `Adresse e-mail`.
2. Saisir:

```text
admin@ecole-benani.ma
```

3. Cliquer dans le champ `Mot de passe`.
4. Saisir:

```text
admin123
```

5. Verifier le champ `Identifiant ecole`:

```text
00000000-0000-4000-8000-000000000001
```

6. Cliquer sur le bouton `Se connecter`.

Ce que tu expliques:

```text
La connexion utilise JWT, RBAC et un school_id pour separer les tenants. Apres connexion, la racine redirige automatiquement vers le dashboard selon le role.
```

### Etape 2 - Dashboard Admin

Fenetre: Web app, sidebar gauche.

1. Cliquer `Tableau de bord`.
2. Montrer les KPIs.
3. Cliquer `Utilisateurs`.
4. Montrer la liste multi-role.
5. Dans `Utilisateurs`, utiliser la recherche si disponible et chercher `Yassine` ou `prof`.
6. Montrer les actions de statut:
   - bouton `Suspendre` si un utilisateur est actif.
   - bouton `Activer` si un utilisateur est suspendu.

Ce que tu expliques:

```text
L'administration gere les utilisateurs, les roles, les profils et les memberships par ecole. Chaque ecran est protege par role.
```

### Etape 3 - Invitations et inscription en masse

Fenetre: Web app, sidebar gauche.

1. Cliquer `Invitations`.
2. Cliquer le bouton `Creer` ou le bouton principal en haut de page.
3. Montrer le formulaire de creation d'invitation.
4. Ne pas forcement valider pendant le meeting si tu veux eviter de modifier les donnees.
5. Cliquer `Inscription en masse`.
6. Montrer l'import CSV et expliquer les colonnes:

```text
email, full_name, role, phone, class_code
```

Ce que tu expliques:

```text
L'onboarding peut etre fait individuellement avec invitation, ou massivement par CSV pour une rentree scolaire.
```

### Etape 4 - Programmes academiques et inscriptions

Fenetre: Web app, sidebar gauche.

1. Cliquer `Filieres`.
2. Montrer la creation/edition de programme.
3. Cliquer `Inscriptions`.
4. Montrer l'affectation des eleves.
5. Cliquer `Equivalences`.
6. Cliquer `Regles d'eligibilite`.

Ce que tu expliques:

```text
Le module academique gere les programmes, versions, equivalences et regles d'eligibilite. C'est important pour garder un historique scolaire propre et auditable.
```

### Etape 5 - Facturation scolaire

Fenetre: Web app, sidebar gauche.

1. Cliquer `Frais scolaires`.
2. Montrer les frais seedes:
   - Scolarite: 3500 MAD mensuel.
   - Transport: 800 MAD mensuel.
   - Cantine: 1200 MAD mensuel.
   - Inscription: 500 MAD annuel.
   - Parascolaire: 300 MAD annuel.
3. Cliquer `Attribution des frais`.
4. Cliquer le bouton principal d'attribution si tu veux montrer le modal.
5. Cliquer `Generer des factures`.
6. Montrer le bouton `Generer les factures`.
7. Cliquer `Politique fratrie`.
8. Cliquer `Penalites de retard`.
9. Cliquer `Plans de paiement`.
10. Cliquer une ligne de plan pour ouvrir le detail.
11. Cliquer `Factures`.
12. Cliquer une facture dans le tableau.
13. Dans la page detail facture, montrer:
    - bouton `Telecharger PDF`.
    - bouton de paiement si visible.
    - upload de preuve si visible.
    - bouton de recu si visible.

Ce que tu expliques:

```text
Le module billing couvre la structure des frais, l'affectation, la generation de factures, les plans de paiement, les preuves de paiement et les recus. Le seed contient 18 factures avec plusieurs statuts pour montrer les cas reels.
```

### Etape 6 - Audit, conformite et feature toggles

Fenetre: Web app, sidebar gauche.

1. Cliquer `Journal d'audit`.
2. Montrer que les actions sensibles sont tracees.
3. Cliquer `Justificatifs`.
4. Montrer le workflow de validation des absences.
5. Cliquer `Conformite MEN`.
6. Cliquer ensuite, si besoin via URL directe:

```text
http://localhost:5173/compliance/mapping
http://localhost:5173/compliance/reports
```

7. Cliquer ou ouvrir:

```text
http://localhost:5173/admin/features
```

8. Montrer les toggles:
   - gamification.
   - rewards.
   - skill_passport.
   - difficulty_adaptation.
   - parent_dashboard_v2.

Ce que tu expliques:

```text
La plateforme n'est pas seulement un CRUD. Elle integre audit trail, conformite et feature flags pour activer progressivement des modules.
```

### Etape 7 - Gamification Admin

Fenetre: Web app, sidebar gauche.

1. Cliquer `Badges`.
2. Montrer le catalogue.
3. Cliquer `Creer un badge` si tu veux montrer le formulaire.
4. Cliquer `Recompenses`.
5. Montrer l'annuaire ou le centre de recompenses.
6. Si un champ demande un student id, utiliser:

```text
10000000-0000-4000-8000-000000000007
```

7. Ouvrir directement si besoin:

```text
http://localhost:5173/students/10000000-0000-4000-8000-000000000007/rewards
```

8. Montrer Yassine:
   - 25 etoiles.
   - 350 XP.
   - niveau 3.
   - badges `first_login`, `streak_7`, `xp_250`.

Ce que tu expliques:

```text
La gamification est connectee aux actions d'apprentissage: contenus termines, quiz reussis, jeux gagnes et bonus de connexion.
```

### Etape 8 - Passer au role Teacher

Fenetre: Web app.

1. Cliquer en haut a droite sur le menu utilisateur.
2. Cliquer `Deconnexion`.
3. Login:

```text
Email:    prof.math@ecole-benani.ma
Password: teacher123
School:   00000000-0000-4000-8000-000000000001
```

4. Cliquer `Se connecter`.

### Etape 9 - Teacher: classes, presence, LMS

Fenetre: Web app, sidebar gauche.

1. Cliquer `Mes classes`.
2. Montrer `6eme A` et `6eme B`.
3. Cliquer le bouton `Voir eleves` ou bouton secondaire dans une classe si visible.
4. Cliquer `Voir le classement` pour ouvrir le leaderboard de classe.
5. Cliquer `Presence`.
6. Montrer les statuts de presence.
7. Cliquer `Marquer tous presents`.
8. Ne pas valider si tu veux garder les donnees, ou cliquer `Enregistrer la presence` pour montrer le workflow.
9. Cliquer `Cours`.
10. Cliquer `Devoirs`.
11. Cliquer `Soumissions`.
12. Cliquer `Evaluations`.
13. Cliquer `Quiz`.

Ce que tu expliques:

```text
Le teacher workspace est oriente operations quotidiennes: classes, presence, cours, devoirs, corrections et progression de classe.
```

### Etape 10 - Teacher: banque de questions et rubriques

Fenetre: Web app, sidebar gauche.

1. Cliquer `Banque de questions`.
2. Montrer les filtres par matiere, type et difficulte.
3. Cliquer `Ajouter une question`.
4. Montrer le modal:
   - texte de question.
   - type QCM/Vrai-Faux/reponse courte.
   - choix.
   - difficulte.
   - tags.
5. Fermer le modal avec `Annuler`.
6. Cliquer `Importer depuis un quiz`.
7. Revenir avec le bouton retour si visible.
8. Cliquer `Generer un quiz`.
9. Cliquer `Grilles d'evaluation`.
10. Montrer les rubriques.
11. Cliquer `Creer une grille`.
12. Montrer criteres, niveaux et poids.

Ce que tu expliques:

```text
La banque de questions et les rubriques reduisent le travail repetitif des enseignants et standardisent l'evaluation.
```

### Etape 11 - Teacher: creation de jeux educatifs

Fenetre: Web app, sidebar gauche.

1. Cliquer `Jeux`.
2. Montrer les filtres:
   - type.
   - difficulte.
   - statut.
   - matiere.
3. Cliquer `Nouvelle config`.
4. Dans la page de creation:
   - choisir `Memory match`, `Tri` ou `Cartes de vocabulaire`.
   - remplir rapidement un titre.
   - montrer `Etoiles offertes` et `XP offert`.
   - montrer la section specifique:
     - `Ajouter une paire` pour memory.
     - `Ajouter une categorie` pour tri.
     - `Ajouter une carte` pour vocabulaire.
5. Cliquer `Annuler` si tu veux eviter de modifier les donnees, ou `Creer la config` si tu veux creer une vraie config.

Ce que tu expliques:

```text
Les jeux sont configurables par enseignant/admin, avec recompenses reliees au moteur de gamification.
```

### Etape 12 - Passer au role Student

Fenetre: Web app.

1. Cliquer menu utilisateur.
2. Cliquer `Deconnexion`.
3. Login:

```text
Email:    yassine.alaoui@ecole-benani.ma
Password: student123
School:   00000000-0000-4000-8000-000000000001
```

4. Cliquer `Se connecter`.

### Etape 13 - Student: experience eleve

Fenetre: Web app, sidebar gauche.

1. Cliquer `Accueil eleve`.
2. Montrer les cards d'acces rapides.
3. Cliquer `Mon contenu`.
4. Montrer les contenus assignes.
5. Si friend seed est present, cliquer une story ou un coloriage depuis la liste. Les IDs du contenu friend peuvent changer car ils sont importes depuis les assets.
6. Si aucune story n'apparait, dire simplement que `seed-friend-report.md` prouve l'import et passer au CMS dans l'etape Content Manager.
7. Cliquer `Quiz`.
8. Montrer les quiz disponibles.
9. Cliquer `Jeux`.
10. Cliquer un jeu, puis cliquer le bouton de lancement si visible.
11. Cliquer `Mes recompenses`.
12. Montrer etoiles, XP, niveau, streak, badges.
13. Cliquer `Mon progres`.
14. Cliquer `Passeport de competences`.
15. Cliquer `Calendrier`.
16. Cliquer `Annonces`.
17. Cliquer `Notifications`.

Ce que tu expliques:

```text
L'eleve a une experience plus simple et engageante: contenus, quiz, jeux, recompenses, progression et calendrier.
```

### Etape 14 - Passer au role Parent

Fenetre: Web app.

1. Cliquer menu utilisateur.
2. Cliquer `Deconnexion`.
3. Login:

```text
Email:    parent.alaoui@gmail.com
Password: parent123
School:   00000000-0000-4000-8000-000000000001
```

4. Cliquer `Se connecter`.

### Etape 15 - Parent: suivi enfant, paiements, communication

Fenetre: Web app, sidebar gauche.

1. Cliquer `Mes enfants`.
2. Montrer Yassine Alaoui et Omar Benali.
3. Sur la carte enfant, cliquer:
   - `Progres`.
   - `Resultats`.
   - `Emploi du temps`.
   - `Revision partagee` si visible.
4. Cliquer `Progres des enfants`.
5. Cliquer `Fil d'actualite`.
6. Montrer les items:
   - annonce.
   - alerte absence.
   - paiement.
   - note publiee.
7. Cliquer `Factures`.
8. Cliquer une facture.
9. Montrer:
   - detail facture.
   - telechargement PDF.
   - paiement/preuve si visible.
10. Cliquer `Justifier une absence`.
11. Montrer le formulaire de justificatif.
12. Cliquer `Messages`.
13. Cliquer une conversation.
14. Ecrire un court message seulement si tu veux montrer le temps reel:

```text
Bonjour, merci pour le suivi.
```

15. Cliquer `Annonces`.
16. Cliquer `Calendrier`.
17. Cliquer `Documents`.

Ce que tu expliques:

```text
Le parent a une vue consolidee: progression, absences, notes, factures, documents, annonces et messages avec l'ecole.
```

### Etape 16 - Content Manager / CMS

Fenetre: Web app.

1. Deconnexion.
2. Login:

```text
Email:    cms@ecole-platform.ma
Password: content123
School:   00000000-0000-4000-8000-000000000001
```

3. Apres login, ouvrir directement:

```text
http://localhost:5173/cms
```

4. Cliquer `Upload` ou le bouton principal d'ajout.
5. Montrer les types de contenu:
   - document.
   - story.
   - coloring_book.
   - quiz.
   - video.
6. Revenir a:

```text
http://localhost:5173/cms
```

7. Cliquer une ligne de contenu puis `Modifier` si visible.
8. Ouvrir:

```text
http://localhost:5173/cms/review
http://localhost:5173/cms/quizzes
http://localhost:5173/cms/analytics
```

Ce que tu expliques:

```text
Le CMS permet de gerer les contenus pedagogiques, notamment les stories et coloriages pour les jeunes niveaux. Avec le seed friend, on a aussi du contenu arabe importe.
```

### Etape 17 - Analytics, reporting, financial health

Fenetre: Web app.

1. Revenir avec Admin ou Director.
2. Cliquer `Analytique`.
3. Montrer les graphiques.
4. Cliquer les presets de periode si visibles.
5. Cliquer un bouton d'export chart si visible.
6. Cliquer `Rapports`.
7. Montrer les schedules/jobs.
8. Cliquer `Sante financiere`.
9. Ouvrir aussi:

```text
http://localhost:5173/financial-health/snapshots
http://localhost:5173/financial-health/export
```

10. Cliquer `Exporter` dans la page export si tu veux montrer la generation.

Ce que tu expliques:

```text
La direction peut suivre l'assiduite, les notes, l'engagement, la facturation et la sante financiere.
```

### Etape 18 - Infrastructure et observabilite

Fenetre: Swagger puis Grafana/Prometheus.

1. Ouvrir:

```text
http://localhost:8000/docs
```

2. Montrer les groupes d'endpoints:
   - auth.
   - admin.
   - teacher.
   - billing.
   - rewards.
   - content.
   - gradebook.
3. Ouvrir:

```text
http://localhost:3000
```

4. Login Grafana:

```text
admin / change-me-grafana-admin
```

5. Montrer les dashboards provisionnes.
6. Ouvrir:

```text
http://localhost:9090
```

7. Montrer Prometheus.

Ce que tu expliques:

```text
L'infrastructure est dockerisee, avec PostgreSQL, Redis, FastAPI, worker, MinIO, monitoring Prometheus/Grafana/Loki/Tempo et scripts Make.
```

---

## 6. Parcours court si tu as seulement 10 minutes

1. Login Admin.
2. `Tableau de bord`.
3. `Utilisateurs`.
4. `Factures`.
5. `Badges` puis `Recompenses`.
6. Deconnexion.
7. Login Teacher.
8. `Mes classes`.
9. `Presence`.
10. `Banque de questions`.
11. `Jeux` puis `Nouvelle config`.
12. Deconnexion.
13. Login Student Yassine.
14. `Accueil eleve`.
15. `Mon contenu`.
16. `Jeux`.
17. `Mes recompenses`.
18. Deconnexion.
19. Login Parent Alaoui.
20. `Mes enfants`.
21. `Fil d'actualite`.
22. `Factures`.
23. Ouvrir Swagger `http://localhost:8000/docs`.

Phrase de conclusion:

```text
La valeur principale est l'integration: chaque role a son espace, mais les donnees sont reliees. Une absence cree un suivi parent, un quiz alimente les resultats, un jeu alimente les rewards, une facture suit son paiement, et l'administration garde audit, securite et reporting.
```

---

## 7. Routes directes utiles pendant la demo

Utilise ces URLs si le menu est trop long.

### Admin / Director

```text
http://localhost:5173/admin
http://localhost:5173/admin/users
http://localhost:5173/admin/invitations
http://localhost:5173/admin/audit
http://localhost:5173/admin/batch-register
http://localhost:5173/admin/family-links
http://localhost:5173/admin/badges
http://localhost:5173/admin/features
http://localhost:5173/admin/programs
http://localhost:5173/admin/enrollments
http://localhost:5173/admin/program-equivalences
http://localhost:5173/admin/eligibility-rules
http://localhost:5173/analytics
http://localhost:5173/compliance
http://localhost:5173/compliance/mapping
http://localhost:5173/compliance/reports
```

### Billing / Finance

```text
http://localhost:5173/admin/fee-structures
http://localhost:5173/admin/fee-assignments
http://localhost:5173/admin/generate-invoices
http://localhost:5173/billing/sibling-policy
http://localhost:5173/billing/late-fees
http://localhost:5173/billing/payment-plans
http://localhost:5173/invoices
http://localhost:5173/budgets
http://localhost:5173/budgets/requests
http://localhost:5173/budgets/analytics
http://localhost:5173/financial-health
http://localhost:5173/financial-health/snapshots
http://localhost:5173/financial-health/export
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
http://localhost:5173/teacher/games
http://localhost:5173/teacher/games/new
http://localhost:5173/rubrics
http://localhost:5173/question-bank
http://localhost:5173/question-bank/import
http://localhost:5173/question-bank/generate
http://localhost:5173/teacher/class-progress
http://localhost:5173/gradebook
```

### Student

```text
http://localhost:5173/student/home
http://localhost:5173/student/content
http://localhost:5173/student/quizzes
http://localhost:5173/student/games
http://localhost:5173/student/writing
http://localhost:5173/progress
http://localhost:5173/rewards
http://localhost:5173/submissions
http://localhost:5173/results
http://localhost:5173/skills
http://localhost:5173/calendar
http://localhost:5173/announcements
http://localhost:5173/notifications
```

### Parent

```text
http://localhost:5173/family
http://localhost:5173/parent/progress
http://localhost:5173/feed
http://localhost:5173/rewards
http://localhost:5173/invoices
http://localhost:5173/justification
http://localhost:5173/messages
http://localhost:5173/calendar
http://localhost:5173/documents
http://localhost:5173/settings/notifications
```

### CMS

```text
http://localhost:5173/cms
http://localhost:5173/cms/upload
http://localhost:5173/cms/review
http://localhost:5173/cms/quizzes
http://localhost:5173/cms/analytics
```

---

## 8. IDs seed utiles pour les URLs directes

### Users

```text
Admin:        10000000-0000-4000-8000-000000000001
Director:     10000000-0000-4000-8000-000000000002
Teacher Math: 10000000-0000-4000-8000-000000000003
Teacher FR:   10000000-0000-4000-8000-000000000004
Parent 1:     10000000-0000-4000-8000-000000000005
Student 1:    10000000-0000-4000-8000-000000000007
Student CP:   10000000-0000-4000-8000-00000000000c
Content Mgr:  10000000-0000-4000-8000-00000000000b
```

### Classes

```text
6eme A:       20000000-0000-4000-8000-000000000004
6eme B:       20000000-0000-4000-8000-000000000005
CP A:         20000000-0000-4000-8000-000000000010
CE2 A:        20000000-0000-4000-8000-000000000011
CM2 A:        20000000-0000-4000-8000-000000000012
3eme A:       20000000-0000-4000-8000-000000000013
Terminale A:  20000000-0000-4000-8000-000000000014
```

### Direct demos

```text
Yassine rewards:
http://localhost:5173/students/10000000-0000-4000-8000-000000000007/rewards

6eme A leaderboard:
http://localhost:5173/classes/20000000-0000-4000-8000-000000000004/leaderboard

Yassine academic history:
http://localhost:5173/students/10000000-0000-4000-8000-000000000007/academic-history
```

---

## 9. Points techniques a mentionner au parrain industriel

### Architecture

- Backend: FastAPI, Python 3.12, SQLAlchemy async, Pydantic v2, Alembic.
- Frontend: React 18, TypeScript, Vite, React Query, React Router, i18n.
- Mobile: Flutter 3, Riverpod, GoRouter, Dio.
- Database: PostgreSQL 16 avec migrations Alembic.
- Cache/queue: Redis 7.
- Storage: local ou S3/MinIO avec URLs presignees.
- Infra: Docker, Kubernetes/Helm, Nginx, CI/CD GitHub Actions.
- Observabilite: Prometheus, Grafana, Loki, Tempo, Alertmanager.

### Securite

- Auth JWT.
- RBAC multi-role.
- School ID pour multi-tenant.
- 2FA/TOTP/WebAuthn/OAuth prevus dans le module IAM.
- Audit trail.
- Sessions et historique de connexion.
- GDPR/export donnees.

### Modules metier

- IAM: users, roles, invitations, sessions.
- ERP: ecoles, classes, inscriptions, emploi du temps, presence.
- LMS: cours, contenus, quiz, devoirs, corrections, rubriques.
- Billing: frais, factures, paiements, plans, policies.
- Communication: messages, annonces, notifications, calendrier.
- Gamification: XP, etoiles, badges, streaks, jeux.
- Reporting: analytics, financial health, jobs, exports.
- CMS: contenu pedagogique, stories, coloriages, review queue.

---

## 10. Si quelque chose ne marche pas pendant la demo

### Backend down

Fenetre Terminal:

```bash
make status
make logs
make restart
make health
```

### Web down

Fenetre Terminal:

```bash
cd web
npm run dev
```

Puis ouvrir:

```text
http://localhost:5173
```

### Seed absent

Fenetre Terminal:

```bash
make migrate
make seed
```

Si les assets friend ne sont pas disponibles:

```bash
make seed-core
```

Puis utiliser les comptes de `seed-report.md`.

### Login refuse

Verifier:

1. Email exact.
2. Password exact.
3. School ID exact:

```text
00000000-0000-4000-8000-000000000001
```

4. Backend health:

```bash
make health
```

### Grafana refuse

Essayer:

```text
admin / change-me-grafana-admin
```

Sinon lire `.env`:

```bash
rg "GRAFANA_ADMIN" .env infra/.env* docs infra -g '*.env*' -g '*.md'
```

---

## 11. Conclusion a dire

```text
Cette plateforme montre une vision complete d'un SaaS scolaire: chaque acteur a son espace, les donnees sont reliees, les actions sont securisees par role, et l'infrastructure est prete pour un deploiement industriel. La force du projet est d'avoir connecte les modules: administration, apprentissage, paiement, parent, eleve, contenu, reporting et observabilite.
```
