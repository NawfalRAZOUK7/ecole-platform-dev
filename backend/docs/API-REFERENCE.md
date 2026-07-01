# 📡 API Reference

Base URL : `http://localhost:8000/api/v1`

Documentation interactive : [Swagger UI](http://localhost:8000/docs) · [ReDoc](http://localhost:8000/redoc)

---

## Authentification

Toutes les routes (sauf `/auth/login` et `/auth/register`) nécessitent un JWT Bearer token :

```
Authorization: Bearer <access_token>
```

Flux d'authentification :

1. `POST /auth/login` → reçoit `access_token` + `refresh_token`
2. Si 2FA activé → `POST /auth/verify-2fa` avec le code TOTP
3. Token expiré → `POST /auth/refresh` avec le `refresh_token`

---

## Format de réponse

### Succès (objet unique)

```json
{
  "data": { ... },
  "meta": { "timestamp": "2026-04-26T10:00:00Z", "version": "0.1.0" }
}
```

### Succès (liste paginée)

```json
{
  "data": [ ... ],
  "meta": { "next_cursor": "abc123", "has_more": true, "timestamp": "...", "version": "..." }
}
```

### Erreur

```json
{
  "error": {
    "code": "ERR-AUTH-401",
    "message": "Token expired",
    "category": "auth",
    "retryable": false,
    "timestamp": "..."
  }
}
```

---

## Groupes d'endpoints

### 🔐 IAM — Identity & Access Management

| Méthode    | Endpoint                      | Description                                |
| ---------- | ----------------------------- | ------------------------------------------ |
| `POST`     | `/auth/login`                 | Connexion (email + mot de passe)           |
| `POST`     | `/auth/register`              | Inscription                                |
| `POST`     | `/auth/refresh`               | Renouveler le token                        |
| `POST`     | `/auth/verify-2fa`            | Vérifier code TOTP                         |
| `POST`     | `/auth/2fa/sms/send`          | Envoyer code SMS 2FA                       |
| `POST`     | `/auth/2fa/sms/verify`        | Vérifier code SMS 2FA                      |
| `POST`     | `/auth/webauthn/register`     | Enregistrer une clé WebAuthn               |
| `POST`     | `/auth/webauthn/authenticate` | Authentifier via WebAuthn                  |
| `POST`     | `/auth/oauth/{provider}`      | Connexion OAuth (google, microsoft, apple) |
| `GET`      | `/auth/me`                    | Profil utilisateur courant                 |
| `POST`     | `/auth/logout`                | Déconnexion (invalide la session)          |
| `GET`      | `/profiles/:id`               | Consulter un profil                        |
| `PUT`      | `/profiles/:id`               | Modifier un profil                         |
| `POST`     | `/invitations`                | Créer une invitation                       |
| `GET`      | `/invitations`                | Lister les invitations                     |
| `POST`     | `/recovery/request`           | Demande de reset mot de passe              |
| `POST`     | `/recovery/reset`             | Reset mot de passe                         |
| `GET`      | `/devices`                    | Lister les appareils enregistrés           |
| `POST`     | `/devices`                    | Enregistrer un appareil (push token)       |
| `GET/POST` | `/consents`                   | Gérer les consentements GDPR               |
| `GET`      | `/gdpr/export`                | Export données personnelles (GDPR)         |
| `DELETE`   | `/gdpr/delete`                | Suppression compte (GDPR)                  |

### 🏫 ERP — Administration scolaire

| Méthode    | Endpoint            | Description                      |
| ---------- | ------------------- | -------------------------------- |
| `GET`      | `/admin/dashboard`  | Statistiques admin (KPIs)        |
| `GET/POST` | `/schools`          | Gestion des écoles               |
| `GET/POST` | `/classes`          | Gestion des classes              |
| `GET/POST` | `/enrollments`      | Inscriptions élèves              |
| `GET/POST` | `/timetable`        | Emploi du temps                  |
| `GET`      | `/teacher/classes`  | Classes de l'enseignant connecté |
| `GET`      | `/teacher/students` | Élèves de l'enseignant connecté  |
| `GET`      | `/levels`           | Niveaux scolaires                |
| `GET/PUT`  | `/features`         | Feature toggles                  |

### 📚 LMS — Apprentissage

| Méthode    | Endpoint                           | Description                               |
| ---------- | ---------------------------------- | ----------------------------------------- |
| `GET/POST` | `/courses`                         | Gestion des cours                         |
| `GET/POST` | `/assignments`                     | Devoirs et travaux                        |
| `GET`      | `/student-work`                    | Vue unifiée du travail élève              |
| `GET/POST` | `/activities`                      | Activités pédagogiques                    |
| `GET`      | `/content/library`                 | Bibliothèque de contenu                   |
| `POST`     | `/content/assign`                  | Assigner du contenu à une classe          |
| `POST`     | `/content/submit-for-review`       | Soumettre du contenu pour révision        |
| `GET/POST` | `/content-items/:id/pages`         | Pages d'un contenu (histoires, coloriage) |
| `POST`     | `/content-items/:id/complete`      | Marquer un contenu comme complété         |
| `POST`     | `/content-items/:id/coloring/save` | Sauvegarder un coloriage                  |
| `GET/POST` | `/quizzes`                         | Gestion des quiz                          |
| `POST`     | `/quizzes/:id/attempt`             | Tenter un quiz                            |
| `GET/POST` | `/question-bank`                   | Banque de questions                       |
| `GET/POST` | `/assessments`                     | Évaluations                               |
| `GET/POST` | `/submissions`                     | Soumissions élèves                        |
| `GET/POST` | `/rubrics`                         | Grilles d'évaluation                      |

### 💬 Communication

| Méthode    | Endpoint                          | Description           |
| ---------- | --------------------------------- | --------------------- |
| `GET/POST` | `/messaging/threads`              | Fils de discussion    |
| `POST`     | `/messaging/threads/:id/messages` | Envoyer un message    |
| `GET`      | `/notifications`                  | Notifications         |
| `GET/POST` | `/announcements`                  | Annonces              |
| `GET`      | `/feed`                           | Fil d'actualité       |
| `GET/POST` | `/events`                         | Événements calendrier |

### 💰 Finance

| Méthode    | Endpoint                  | Description                  |
| ---------- | ------------------------- | ---------------------------- |
| `GET/POST` | `/invoices`               | Factures                     |
| `GET`      | `/invoices/:id`           | Détail facture               |
| `POST`     | `/payments`               | Enregistrer un paiement      |
| `GET/POST` | `/budgets`                | Enveloppes budgétaires       |
| `GET`      | `/financial-health`       | Indicateurs santé financière |
| `GET`      | `/billing/fee-structures` | Structures de frais          |

### 🎮 Gamification

| Méthode    | Endpoint                        | Description                                           |
| ---------- | ------------------------------- | ----------------------------------------------------- |
| `GET`      | `/rewards/me`                   | Mes récompenses (étoiles, XP, niveau, badges, streak) |
| `GET`      | `/rewards/student/:id`          | Récompenses d'un élève                                |
| `GET`      | `/rewards/student/:id/history`  | Historique des récompenses                            |
| `POST`     | `/rewards/award`                | Attribuer étoiles + XP                                |
| `GET`      | `/rewards/leaderboard/:classId` | Classement d'une classe                               |
| `GET/POST` | `/rewards/badges`               | Gestion des badges                                    |
| `GET`      | `/games/configs`                | Configurations de jeux                                |
| `POST`     | `/games/configs`                | Créer un jeu                                          |
| `POST`     | `/games/configs/:id/complete`   | Terminer un jeu (+ récompenses)                       |

### 📊 Analytics & Suivi

| Méthode    | Endpoint                           | Description             |
| ---------- | ---------------------------------- | ----------------------- |
| `GET/POST` | `/attendance/class/:id`            | Présence par classe     |
| `GET`      | `/attendance/analytics`            | Analytiques de présence |
| `GET`      | `/gradebook/:classId/:periodId`    | Carnet de notes         |
| `GET`      | `/gradebook/transcript/:studentId` | Bulletin d'un élève     |
| `GET`      | `/progress/student/:id`            | Progression d'un élève  |
| `GET`      | `/skills`                          | Skill Passport          |
| `GET`      | `/reports`                         | Rapports générés        |
| `GET`      | `/analytics`                       | Analytiques globales    |
| `GET`      | `/compliance`                      | Conformité MEN          |
| `POST`     | `/exports`                         | Export de données       |

### 🔧 Spécialisé

| Méthode    | Endpoint         | Description                     |
| ---------- | ---------------- | ------------------------------- |
| `GET/POST` | `/micro-school`  | Micro-écoles                    |
| `GET/POST` | `/shared-review` | Révision partagée parent-enfant |
| `GET`      | `/sync`          | Synchronisation offline         |
| `WS`       | `/ws`            | WebSocket temps réel            |
| `GET/POST` | `/documents`     | Gestion de documents            |
| `GET/POST` | `/cms`           | Gestion de contenu (CMS)        |

### 🎓 Programmes Académiques (v1.1)

| Méthode  | Endpoint                         | Description                                                   |
| -------- | -------------------------------- | ------------------------------------------------------------- |
| `GET`    | `/programs`                      | Lister les programmes                                         |
| `POST`   | `/programs`                      | Créer un programme                                            |
| `GET`    | `/programs/:id`                  | Détails d'un programme                                        |
| `PUT`    | `/programs/:id`                  | Modifier un programme                                         |
| `GET`    | `/programs/:id/versions`         | Versions d'un programme                                       |
| `POST`   | `/programs/:id/versions`         | Créer une nouvelle version                                    |
| `GET`    | `/program-versions/:id`          | Détails d'une version                                         |
| `GET`    | `/program-equivalences`          | Lister les équivalences                                       |
| `POST`   | `/program-equivalences`          | Déclarer une équivalence entre versions                       |
| `GET`    | `/eligibility-rules?version_id=` | Règles d'éligibilité d'une version                            |
| `POST`   | `/eligibility-rules`             | Créer une règle d'éligibilité                                 |
| `POST`   | `/eligibility/check`             | Évaluer l'éligibilité d'un élève (`{student_id, version_id}`) |
| `GET`    | `/enrollments`                   | Lister les inscriptions (filtres : élève, version, statut)    |
| `POST`   | `/enrollments`                   | Inscrire un élève à une version (déclenche un snapshot)       |
| `DELETE` | `/enrollments/:id`               | Désinscrire un élève                                          |
| `GET`    | `/students/:id/academic-history` | Historique académique complet                                 |

### 💸 Facturation PDF & Reçus de Paiement (v1.1)

| Méthode | Endpoint                            | Description                              |
| ------- | ----------------------------------- | ---------------------------------------- |
| `GET`   | `/invoices/:id/pdf?lang=fr\|ar`     | PDF de facture bilingue (TVA + ICE + RC) |
| `GET`   | `/payments/:id/receipt?lang=fr\|ar` | PDF de reçu de paiement avec QR-code     |
| `GET`   | `/reports/invoice-pdf`              | Rapport PDF inter-factures               |
| `GET`   | `/reports/payment-receipt`          | Rapport PDF inter-reçus                  |

Réponse : redirection HTTP 307 vers une URL S3/MinIO présignée (TTL 5 minutes), `Content-Disposition: attachment`.

### ⬆️ Uploads Directs S3/MinIO (v1.1)

| Méthode | Endpoint                | Description                                                                   |
| ------- | ----------------------- | ----------------------------------------------------------------------------- |
| `POST`  | `/uploads/initiate`     | Demander une URL présignée d'upload (`{filename, size, content_type, scope}`) |
| `POST`  | `/uploads/complete`     | Notifier la fin d'upload, déclenche le scan antivirus                         |
| `GET`   | `/uploads/:id/status`   | Statut du scan antivirus (`scanning`, `clean`, `infected`)                    |
| `GET`   | `/content/:id/download` | Téléchargement signé (redirection 307)                                        |

Le client envoie ensuite les bytes directement sur l'URL présignée S3/MinIO via `PUT`. Taille maximale : 50 MB.

### 🏆 Reward Badges Admin (v1.1)

| Méthode  | Endpoint                    | Description                           |
| -------- | --------------------------- | ------------------------------------- |
| `GET`    | `/admin/reward-badges`      | Lister les badges (admin)             |
| `POST`   | `/admin/reward-badges`      | Créer un badge                        |
| `PUT`    | `/admin/reward-badges/:id`  | Modifier un badge                     |
| `DELETE` | `/admin/reward-badges/:id`  | Supprimer un badge                    |
| `POST`   | `/admin/reward-badges/seed` | Réinitialiser le catalogue par défaut |

### 📅 Timetable v1.1

| Méthode | Endpoint                      | Description                                              |
| ------- | ----------------------------- | -------------------------------------------------------- |
| `POST`  | `/timetable/constraints`      | Ajouter une contrainte (incl. `max_consecutive_classes`) |
| `POST`  | `/timetable/generate/preview` | Génération en mode dry-run (n'enregistre pas)            |
| `POST`  | `/timetable/generate/commit`  | Génération réelle après prévisualisation                 |

---

## Pagination

L'API utilise la pagination par curseur :

```
GET /api/v1/invoices?cursor=abc123&limit=20
```

Réponse :

```json
{
  "data": [...],
  "meta": { "next_cursor": "def456", "has_more": true }
}
```

## Rate Limiting

- **Par IP** : 100 req/min (configurable)
- **Par utilisateur** : 300 req/min
- **Login** : 5 tentatives / 15 min

Headers de réponse :

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1714150800
```
