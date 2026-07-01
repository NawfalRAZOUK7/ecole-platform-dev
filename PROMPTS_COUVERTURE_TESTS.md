# Prompts pour aligner les preuves de couverture avec le rapport final

## Objectif

Ce document contient des consignes detaillees pour un agent IA charge de renforcer les tests du projet **Ecole Platform** sans modifier le code applicatif, afin de produire des preuves de couverture coherentes avec le rapport final.

La cible demandee est volontairement stricte :

- couverture endpoint/API contractuelle : **>= 97,9 %** ;
- si la valeur du rapport est interpretee comme une couverture de code backend, couverture backend globale `coverage.py` : **>= 97,9 %** ;
- aucun artefact de couverture ne doit etre modifie manuellement ;
- aucun seuil ne doit etre baisse pour faire passer la validation ;
- aucune exclusion artificielle (`omit`, `pragma: no cover`, suppression de fichiers mesures) ne doit etre ajoutee pour gonfler le score.

Si une cible ne peut pas etre atteinte sans modifier le code applicatif, l'agent doit s'arreter et produire une note de blocage precise : modules concernes, lignes non couvertes, tests ajoutes, effort restant estime.

## Contexte technique connu

Depot de travail :

```sh
/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
```

Structure principale :

- `backend/app/` : code applicatif FastAPI/Python ;
- `backend/tests/` : tests backend Pytest ;
- `web/` : client web, Vitest et Playwright ;
- `mobile/` : client mobile Flutter ;
- `system-tests/` : tests systeme et scenarios transverses ;
- `scripts/run-backend-test-suite.sh` : runner backend avec `pytest-cov`.

Constat initial a verifier avant toute action :

- `backend/coverage.xml` peut etre ancien ;
- l'artefact existant indique environ `67.76 %` de couverture ligne backend (`7569 / 11170`) ;
- le fichier `backend/pyproject.toml` configure actuellement `fail_under = 0` ;
- le script `scripts/run-backend-test-suite.sh` accepte `COV_FAIL_UNDER`, mais la valeur par defaut est `0`.

Le but n'est pas de changer le rapport. Le but est de faire converger les preuves techniques vers les valeurs annoncees.

## Regles non negociables

1. Ne pas modifier le code applicatif dans `backend/app/`, `web/src/`, `mobile/lib/`, sauf si le donneur d'ordre valide explicitement une correction de bug.
2. Ne pas modifier manuellement `coverage.xml`, `lcov.info`, `htmlcov`, screenshots, rapports HTML ou fichiers generes.
3. Ne pas augmenter artificiellement la couverture par des tests sans assertions utiles.
4. Ne pas masquer du code dans la configuration de couverture.
5. Ne pas remplacer les tests existants par des tests plus faibles.
6. Ne pas supprimer de tests existants.
7. Toute nouvelle donnee de couverture doit etre reproductible par commande.
8. Les tests doivent etre classes par intention : unitaires, integration, securite, contrat/API, web, mobile ou systeme.

## Prompt 1 - Audit initial reproductible

Copier-coller ce prompt dans l'autre agent IA :

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Ta premiere mission est un audit reproductible de la couverture actuelle. Ne modifie aucun fichier.

Actions attendues :
1. Inspecte les commandes de test existantes dans Makefile, backend/pyproject.toml, backend/pytest.ini, web/package.json, mobile/pubspec.yaml et scripts/.
2. Lance ou prepare les commandes permettant de recalculer :
   - la couverture backend Python avec coverage.py/pytest-cov ;
   - la couverture endpoint/API contractuelle ;
   - la couverture web Vitest si applicable ;
   - la couverture mobile Flutter si applicable.
3. Si l'environnement local ne permet pas d'executer une commande, note la raison exacte et propose la commande Docker ou alternative.
4. Genere un resume avec :
   - couverture backend lignes et branches ;
   - 20 fichiers backend les moins couverts ;
   - nombre d'endpoints OpenAPI couverts/non couverts ;
   - tests existants par famille ;
   - commandes exactes utilisees.

Contraintes :
- Ne modifie pas le code applicatif.
- Ne modifie pas les fichiers de configuration pour ameliorer artificiellement le score.
- Ne modifie pas les artefacts generes manuellement.
```

Commandes de depart suggerees :

```sh
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev

# Backend, execution locale si l'environnement Python est pret
cd backend
python -m pytest tests \
  --cov=app \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov

# Backend, variante via runner du depot
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
COV_FAIL_UNDER=0 ./scripts/run-backend-test-suite.sh full

# Web
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web
npm run test:coverage
npm run audit:endpoints

# Mobile
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
flutter test --coverage
```

Commande utile pour extraire les fichiers backend les moins couverts depuis `coverage.xml` :

```sh
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

p = Path("coverage.xml")
root = ET.parse(p).getroot()
rows = []
for cls in root.findall(".//class"):
    filename = cls.attrib.get("filename", "")
    rate = float(cls.attrib.get("line-rate", 0.0)) * 100
    lines = cls.findall(".//line")
    total = len(lines)
    missed = sum(1 for line in lines if int(line.attrib.get("hits", "0")) == 0)
    if filename.startswith("app/") and total:
        rows.append((rate, missed, total, filename))
for rate, missed, total, filename in sorted(rows)[:30]:
    print(f"{rate:6.2f}%  missed={missed:4d}/{total:<4d}  {filename}")
PY
```

## Prompt 2 - Couverture endpoint/API >= 97,9 %

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Objectif prioritaire : produire une preuve reproductible que la couverture des endpoints/API est >= 97,9 %.

Actions attendues :
1. Identifie le mecanisme existant de couverture endpoint/API :
   - tests contractuels OpenAPI ;
   - scripts d'audit endpoint ;
   - tests web contractuels ;
   - tests backend contractuels.
2. Distingue clairement cette metrique de la couverture de code coverage.py.
3. Liste tous les endpoints OpenAPI, puis ceux couverts par tests.
4. Ajoute uniquement des tests manquants pour les endpoints non couverts ou mal couverts.
5. Vise >= 97,9 % de couverture endpoint.
6. Genere un artefact final lisible : tableau endpoints couverts/non couverts, commande de reproduction, taux final.

Contraintes :
- Ne modifie pas le code applicatif.
- Ne marque pas un endpoint comme couvert sans requete/test executable.
- Si un endpoint exige authentification ou donnees complexes, cree les fixtures de test necessaires.
- Si un endpoint est volontairement exclu, documente la raison fonctionnelle.
```

Commandes a examiner en priorite :

```sh
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
make openapi-check

cd web
npm run test:contract
npm run test:contract:report
npm run audit:endpoints

cd ../backend
python -m pytest tests/contract -q
```

## Prompt 3 - Couverture backend globale par tests uniquement

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Objectif : augmenter la couverture backend coverage.py par ajout de tests uniquement.

Cible :
- cible finale demandee : >= 97,9 % si techniquement atteignable sans modifier le code applicatif ;
- cible intermediaire minimale : depasser d'abord 80 %, puis 90 %, puis 95 %, puis 97,9 % ;
- chaque palier doit etre valide par une execution complete des tests.

Plan de travail :
1. Recalcule la couverture backend actuelle.
2. Trie les fichiers par lignes manquees, pas seulement par pourcentage.
3. Priorise les modules metier a fort impact :
   - IAM et securite ;
   - LMS ;
   - ERP ;
   - billing ;
   - communication ;
   - reporting ;
   - services transverses ;
   - permissions RBAC/ABAC.
4. Ajoute des tests unitaires pour les fonctions pures, validateurs, policies et services.
5. Ajoute des tests d'integration API pour les routes FastAPI et workflows principaux.
6. Ajoute des tests de securite pour permissions, appartenance ecole, parent-enfant, roles et isolation des donnees.
7. Ajoute des tests de cas limites : erreurs 400/401/403/404/409/422, valeurs nulles, transitions de statut invalides, idempotence.
8. Apres chaque lot, relance la couverture et note le gain obtenu.

Contraintes :
- Ne pas modifier backend/app pour faciliter les tests.
- Ne pas ajouter de mocks qui contredisent le comportement reel.
- Ne pas tester uniquement l'import des modules.
- Chaque test doit avoir au moins une assertion fonctionnelle.
- Si une ligne non couverte correspond a une integration externe difficile, tester la logique de preparation, les erreurs et les retries avec mocks explicites.
```

Commande de validation par palier :

```sh
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
python -m pytest tests \
  --cov=app \
  --cov-branch \
  --cov-report=term-missing:skip-covered \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov
```

Commande stricte a utiliser uniquement quand le taux est deja atteint :

```sh
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
python -m pytest tests \
  --cov=app \
  --cov-branch \
  --cov-fail-under=97.9 \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov
```

## Prompt 4 - Modules critiques a 95 % ou plus

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Objectif : definir et verifier une couverture >= 95 % sur les modules critiques, sans confondre cette metrique avec la couverture globale.

Modules critiques proposes :
- backend/app/api/
- backend/app/core/security*
- backend/app/core/rbac*
- backend/app/core/permissions*
- backend/app/services/iam*
- backend/app/services/billing*
- backend/app/services/lms*
- backend/app/services/erp*
- backend/app/models/

Actions attendues :
1. Verifie les chemins exacts dans le depot.
2. Calcule la couverture par module/fichier.
3. Ajoute des tests pour les fichiers critiques sous 95 %.
4. Genere un tableau final : module, lignes couvertes, lignes totales, taux.
5. Ne modifie pas la configuration de couverture pour masquer des fichiers.
```

Exemple de commande pour produire un rapport filtre a adapter selon les chemins reels :

```sh
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
python -m pytest tests \
  --cov=app/api \
  --cov=app/core \
  --cov=app/services \
  --cov=app/models \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage-critical.xml
```

## Prompt 5 - Tests web et mobile si les chiffres du rapport les citent

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Objectif : verifier et renforcer les couvertures web et mobile uniquement si elles sont citees dans les preuves finales.

Web :
1. Lance npm run test:coverage.
2. Identifie les composants/hooks/services non couverts.
3. Ajoute des tests Vitest utiles pour formulaires, guards, clients API, erreurs et etats vides.
4. Ne modifie pas l'implementation pour rendre les tests faciles.

Mobile :
1. Lance flutter test --coverage.
2. Identifie les widgets, providers, services et workflows non couverts.
3. Ajoute des tests unitaires et widget tests pertinents.
4. Ne modifie pas mobile/lib sans validation.

Livrable :
- commandes executees ;
- taux final ;
- fichiers de couverture generes ;
- limites restantes.
```

## Prompt 6 - Validation finale et preuves a conserver

```text
Tu travailles dans /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev.

Objectif : produire le dossier de preuves final, reproductible et defendable.

Verifications obligatoires :
1. Tous les tests ajoutes passent.
2. La couverture endpoint/API est >= 97,9 %.
3. La couverture backend globale coverage.py est >= 97,9 % si cette cible a ete confirmee comme metrique du rapport.
4. Les modules critiques sont >= 95 %.
5. Aucun fichier de couverture n'a ete modifie manuellement.
6. Aucune exclusion artificielle n'a ete ajoutee.
7. Les commandes de reproduction sont documentees.

Commandes finales attendues :

cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
python -m pytest tests --cov=app --cov-branch --cov-fail-under=97.9 --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:htmlcov

cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web
npm run test:coverage
npm run test:contract:report
npm run audit:endpoints

cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
flutter test --coverage

Livrable final :
- taux endpoint/API final ;
- taux backend line coverage final ;
- taux backend branch coverage final ;
- taux modules critiques ;
- liste des tests ajoutes ;
- chemins des artefacts generes ;
- commandes exactes permettant de reproduire les chiffres ;
- liste des limites restantes, s'il en reste.
```

## Definition du succes

Le travail est considere termine uniquement si l'agent fournit des preuves reproductibles montrant :

- `endpoint/API coverage >= 97.9 %` ;
- `backend coverage.py line coverage >= 97.9 %`, si cette metrique est celle utilisee pour justifier la valeur du rapport ;
- `critical modules coverage >= 95 %` ;
- tests executables sans modification manuelle des artefacts ;
- aucune regression de tests existants.

Si le passage de `67.76 %` a `97.9 %` en couverture backend exige des modifications applicatives importantes, l'agent doit le signaler. Dans ce cas, il doit continuer a renforcer les tests jusqu'au meilleur niveau atteignable par tests seuls, puis produire un plan de reste a faire.
