# Guide de présentation vidéo — Ecole Platform

Ce document est un script pas-à-pas pour enregistrer une vidéo de démonstration complète du projet Ecole Platform, depuis la connexion jusqu'à l'ensemble des fonctionnalités implémentées.

---

## Prérequis avant l'enregistrement

1. **Démarrer la stack** : `docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d`
2. **Vérifier que tous les services sont UP** : `docker ps` (attendre que backend, web, worker, postgres, redis, minio soient healthy)
3. **Ensemencer les données de démo** : `docker compose exec backend python -m scripts.seed_demo_data` (si ce script existe, sinon utiliser les fixtures de test)
4. **Comptes de démo disponibles** :
   - Admin : `admin@ecole.test` / `DemoPass123!`
   - Enseignant : `teacher@ecole.test` / `DemoPass123!`
   - Parent : `parent@ecole.test` / `DemoPass123!`
   - Élève : `student@ecole.test` / `DemoPass123!`
5. **Navigateur** : Chrome en mode fenêtré (pas plein écran), zoom à 100 %, DevTools fermés
6. **Outils** : OBS ou QuickTime Player pour la capture, micro activé pour la voix off

---

## Scène 1 — Connexion et rôles (durée estimée : 2 min)

**Objectif** : Montrer la page de connexion, le MFA, et la redirection basée sur le rôle.

1. Ouvrir `http://localhost:3000/login`
2. Saisir `admin@ecole.test` / `DemoPass123!`
3. Si MFA activé : saisir le code TOTP (ou montrer l'écran QR de configuration 2FA)
4. Observer le tableau de bord admin (stats, cartes récapitulatives)
5. Se déconnecter, se reconnecter avec `teacher@ecole.test`
6. Montrer le tableau de bord enseignant (cours, classes, devoirs)
7. Se déconnecter, se reconnecter avec `parent@ecole.test`
8. Montrer le tableau de bord parent (enfants, factures, messages)
9. Se déconnecter, se reconnecter avec `student@ecole.test`
10. Montrer le tableau de bord élève (cours, devoirs, notes)

---

## Scène 2 — Gestion des utilisateurs et permissions (IAM) (2 min)

**Objectif** : Démontrer la création d'utilisateurs, l'assignation de rôles et la matrice de permissions.

1. Connexion en tant qu'admin
2. Naviguer vers **Paramètres → Utilisateurs → Ajouter un utilisateur**
3. Créer un nouvel enseignant (nom, email, rôle `TEACHER`, classe assignée)
4. Montrer la matrice RBAC : **Paramètres → Permissions**
5. Désactiver une permission sur le rôle enseignant, vérifier que l'enseignant n'y a plus accès
6. Montrer l'historique d'audit : **Paramètres → Journal d'audit**

---

## Scène 3 — ERP : classes, élèves, absences, emploi du temps (3 min)

**Objectif** : Parcourir le cycle administratif scolaire.

1. **Classes** : Admin → Classes → voir la liste → ouvrir une classe → voir les élèves inscrits
2. **Inscription** : Admin → Inscriptions → formulaire d'inscription d'un nouvel élève → sélectionner la classe → confirmer
3. **Absences** : Enseignant → Ma classe → Appel → marquer présent/absent → sauvegarder
4. **Emploi du temps** : Admin → Emploi du temps → vue hebdomadaire → drag-and-drop d'un cours → sauvegarder
5. **Notes** : Enseignant → Carnet de notes → sélectionner une classe → saisir une note → sauvegarder
6. **Bulletins** : Admin → Bulletins → générer un bulletin PDF pour un trimestre

---

## Scène 4 — LMS : cours, devoirs, soumissions (3 min)

**Objectif** : Montrer le cycle pédagogique complet.

1. **Créer un cours** : Enseignant → Cours → Nouveau cours → titre, description, matière, classe cible → publier
2. **Ajouter du contenu** : ouvrir le cours → Ajouter une leçon → texte + vidéo embed + pièce jointe
3. **Créer un devoir** : Cours → Devoirs → Nouveau devoir → consignes, date de rendu, barème
4. **Soumission élève** : Se reconnecter en tant qu'élève → Mes cours → ouvrir le devoir → Télécharger le modèle → Remplir → Soumettre
5. **Correction** : Reconnecter enseignant → Devoirs → Ouvrir la soumission → annoter (commentaires + note) → publier la note
6. **Résultat** : Reconnecter élève → voir la note et le feedback

---

## Scène 5 — Facturation et paiements (2 min)

**Objectif** : Démontrer la génération de factures, les paiements et le suivi.

1. **Structure tarifaire** : Admin (ou comptable) → Facturation → Structures → créer une structure de frais (inscription, scolarité, transport)
2. **Générer une facture** : Facturation → Factures → Nouvelle facture → sélectionner un parent → appliquer la structure → générer
3. **Télécharger le PDF** : ouvrir la facture → Télécharger PDF → montrer le document bilingue (français/arabe)
4. **Vue parent** : Reconnecter parent → Mes factures → voir la facture → marquer comme payée (ou montrer l'intégration Stripe/CMI si configurée)
5. **Reçu** : télécharger le reçu de paiement avec QR-code

---

## Scène 6 — Communication : annonces, messagerie, notifications (2 min)

**Objectif** : Montrer les canaux de communication unifiés.

1. **Annonce** : Admin → Communications → Nouvelle annonce → cibler toutes les classes → publier
2. **Vue élève/parent** : montrer la notification push reçue et l'annonce dans le fil
3. **Messagerie** : Parent → Messages → Nouveau message → destinataire : enseignant → envoyer
4. **Vue enseignant** : Reconnecter enseignant → Messages → lire et répondre
5. **Notifications** : montrer le panneau de notifications (cloche) avec l'historique

---

## Scène 7 — Micro-école et Micro-budget (2 min)

**Objectif** : Démontrer les fonctionnalités pour l'éducation informelle.

1. **Créer une micro-école** : Admin → Micro-Écoles → Nouvelle → nom, type (garderie, cours de soutien), adresse, capacité
2. **Assigner un éducateur** : sélectionner un utilisateur avec le rôle Éducateur
3. **Inscrire un enfant** : Micro-École → Inscriptions → ajouter un enfant (sans numéro d'élève formel)
4. **Micro-budget** : Éducateur → Micro-budgets → Nouvelle demande → montant, motif → soumettre
5. **Approuver** : Admin → Micro-budgets → Approuver → montrer le workflow de validation

---

## Scène 8 — Uploads, documents et téléchargements signés (2 min)

**Objectif** : Démontrer le téléversement direct et les téléchargements sécurisés.

1. **Upload** : Enseignant → Cours → Ajouter une ressource → sélectionner un fichier PDF (10 Mo max) → voir la barre de progression → upload direct vers MinIO
2. **Statut** : montrer le statut `scanning` puis `available` dans la liste des ressources
3. **Téléchargement** : Élève → ouvrir la ressource → Télécharger → montrer l'URL signée dans la barre d'adresse (paramètre `?token=`)
4. **Documents administratifs** : Admin → Documents → Téléverser un document officiel → catégoriser → partager avec les parents concernés

---

## Scène 9 — Mobile et synchronisation offline (2 min)

**Objectif** : Montrer l'application mobile et le fonctionnement hors-ligne.

1. **Lancer l'app mobile** (émulateur ou vrai device)
2. **Login** : saisir les identifiants élève → montrer le tableau de bord mobile
3. **Mode hors-ligne** : couper le WiFi/4G → tenter d'accéder à un cours → montrer le message "Mode hors-ligne"
4. **File de synchronisation** : faire une action (ex. : soumettre un devoir) → voir la file locale (badge sur l'icône Sync)
5. **Reconnecter** : réactiver le WiFi → voir la synchronisation automatique → confirmation du devoir soumis
6. **Conflits** (si possible) : montrer un écran de résolution de conflit de synchronisation

---

## Scène 10 — Observabilité : Grafana, Prometheus, Loki (2 min)

**Objectif** : Montrer la pile de supervision.

1. Ouvrir `http://localhost:3001` (Grafana)
2. **Dashboard API Overview** : montrer les panels de taux de requêtes, latence p95, taux d'erreur
3. **Dashboard Base de données** : montrer les connexions, temps de requête
4. **Explorer de logs** : Loki → filtrer par `correlation_id` → montrer les logs structurés JSON
5. **Traces** : Tempo → chercher une trace par `trace_id` → montrer la carte de services
6. **Alertes** : Alertmanager → montrer les règles configurées (SEV-1, SEV-2, SEV-3)

---

## Scène 11 — CI/CD, Docker et Kubernetes (2 min)

**Objectif** : Montrer la chaîne de déploiement et d'intégration continue.

1. **GitHub Actions** : ouvrir le repo GitHub → onglet Actions → montrer un run réussi de `ci.yml` avec les 6 niveaux
2. **Docker** : terminal → `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` → montrer tous les conteneurs en cours d'exécution
3. **Helm / Kubernetes** : terminal → `kubectl get pods -n ecole-platform` → montrer tous les pods Running
4. **Helm lint** : terminal → `helm lint infra/k8s/` → montrer le succès
5. **Rollback** : expliquer `helm rollback` en cas d'échec de déploiement

---

## Checklist finale avant publication

- [ ] Durée totale < 25 minutes
- [ ] Chaque scène est enregistrée en un seul plan (pas de coupes visibles)
- [ ] Le curseur est visible et mis en évidence si possible
- [ ] La voix off explique ce qui est fait et pourquoi
- [ ] Pas de données personnelles réelles dans la démo
- [ ] Le logo Ecole Platform est visible sur le tableau de bord
- [ ] Les captures d'écran sont en 1080p minimum
