# 🔐 Sécurité

## Authentification

### JWT (JSON Web Tokens)

- **Access token** : expire après 30 min
- **Refresh token** : expire après 2 jours
- **Algorithme** : HS256 (configurable)
- **Rotation de clés** : support `jwt_previous_key` pour rotation sans interruption
- **Sessions** : max 5 sessions simultanées par utilisateur

### 2FA / TOTP

- Authentification à deux facteurs optionnelle via TOTP (Time-based One-Time Password)
- Compatible avec Google Authenticator, Authy, etc.
- Codes de récupération générés à l'activation
- Endpoint dédié : `POST /auth/verify-2fa`

### Flux d'authentification

```
Client                    API                    Redis
  │                        │                      │
  ├── POST /auth/login ──→ │                      │
  │   (email + password)   ├── Vérif password ──→ │
  │                        ├── Créer session ────→ │
  │  ←── access_token ─────┤                      │
  │      refresh_token     │                      │
  │                        │                      │
  ├── GET /api/v1/... ───→ │                      │
  │   (Bearer token)       ├── Vérif JWT          │
  │                        ├── Check session ────→ │
  │  ←── 200 OK ───────────┤                      │
```

---

## RBAC (Role-Based Access Control)

### Rôles

| Code | Rôle | Niveau d'accès |
|------|------|---------------|
| `ADM` | Administrateur | Accès complet école |
| `DIR` | Directeur | Lecture + rapports + gestion pédagogique |
| `TCH` | Enseignant | Ses classes + élèves + notes + contenu |
| `PAR` | Parent | Ses enfants + bulletins + messages + paiements |
| `STD` | Élève | Son contenu + quiz + progression + récompenses |

### Implémentation

Chaque endpoint est protégé par `RequiresPermission` :

```python
@router.get("/admin/dashboard")
async def get_dashboard(
    auth: AuthContext = Depends(RequiresPermission("admin:dashboard:read"))
):
    ...
```

Les permissions sont résolues via les memberships école-utilisateur. Un utilisateur peut avoir plusieurs memberships dans différentes écoles.

### Matrice de permissions

| Ressource | ADM | DIR | TCH | PAR | STD |
|-----------|-----|-----|-----|-----|-----|
| Dashboard admin | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gestion utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Notes (lecture) | ✅ | ✅ | ✅ (ses classes) | ✅ (ses enfants) | ✅ (les siennes) |
| Notes (écriture) | ✅ | ❌ | ✅ (ses classes) | ❌ | ❌ |
| Présence | ✅ | ✅ | ✅ (ses classes) | ✅ (ses enfants) | ❌ |
| Factures | ✅ | ✅ | ❌ | ✅ (les siennes) | ❌ |
| Contenu (création) | ✅ | ❌ | ✅ | ❌ | ❌ |
| Récompenses (attribuer) | ✅ | ❌ | ✅ | ❌ | ❌ |
| Récompenses (consulter) | ✅ | ✅ | ✅ | ✅ (ses enfants) | ✅ (les siennes) |
| Feature toggles | ✅ | ❌ | ❌ | ❌ | ❌ |
| Audit trail | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## Protection API

| Mesure | Implémentation |
|--------|---------------|
| **Rate Limiting** | Par IP (100/min) et par utilisateur (300/min) via Redis |
| **CORS** | Origines autorisées configurées par environnement |
| **Input Validation** | Pydantic v2 pour toute entrée utilisateur |
| **SQL Injection** | SQLAlchemy ORM avec requêtes paramétrées |
| **XSS** | Pas de rendu HTML côté serveur, API JSON uniquement |
| **CSRF** | SameSite cookies + Bearer tokens |
| **Secrets** | Docker Secrets en production, `.env` en dev |
| **Pre-commit** | `detect-secrets` + hooks pour empêcher les fuites |

---

## Audit Trail

Toutes les actions sensibles sont logguées dans la table `audit_events` :

- Connexion / déconnexion
- Modification de profil
- Changement de rôle / permissions
- Opérations CRUD sur les données sensibles
- Exports de données
- Accès admin

Chaque événement contient : `user_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `user_agent`, `timestamp`, `metadata`.

---

## GDPR / Protection des données

- **Export** : `GET /gdpr/export` — téléchargement de toutes les données personnelles
- **Suppression** : `DELETE /gdpr/delete` — anonymisation et suppression du compte
- **Consentements** : `GET/POST /consents` — gestion des consentements utilisateur
- **Data minimization** : seules les données nécessaires sont collectées
- **Retention** : politique de rétention configurable par type de données
