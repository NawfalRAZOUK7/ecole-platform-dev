# Spec — Puzzle de lettres & Quiz audio automatique

> Spécification de conception (avant code). Basée sur le code réel
> (`ecole-platform-dev/`), 2026-06-05. Décisions actées avec l'utilisateur :
> puzzle **config-driven, 2-3 exemples par lettre, Arabe d'abord → Français →
> Anglais** ; audio **hybride** (réutiliser un fichier audio existant, sinon TTS
> runtime : `flutter_tts` mobile / Web Speech API web) ; quiz **pipeline fusionné
> IA + template + enseignant**, l'enseignant valide avant publication.

---

## 0. Principe directeur : on étend, on ne reconstruit pas

Tout existe déjà ; chaque fonctionnalité est une **extension**.

| Brique nécessaire | Existe déjà ? | Où |
|---|---|---|
| Système de jeux config-driven | ✅ | `models/games.py` (`GameType` enum + `GameConfig.config` JSONB) |
| Players de jeux (web + mobile) | ✅ | `web/src/features/ai/games/ui/*` ; jeux mobiles |
| TTS arabe + map lettre→mot | ✅ | `mobile/lib/shared/services/tts_service.dart` (`_letterExamples`) |
| Champ `letter` sur le contenu | ✅ | `models/lms.py ContentItem.letter` |
| Narration par page (texte à lire) | ✅ | `ContentItemAsset.narration_text`, `asset_type`, `page_number` |
| Modèle Quiz + audio par question | ✅ | `Quiz`, `QuizQuestion.question_media_path`, `options`/`correct_answer` JSONB |
| Lien quiz → contenu source | ✅ | `ContentItem.original_content_id` |
| Génération IA (Claude) | ✅ | `services/ai/ai_service.py`, `claude_provider.py`, `provider_factory.py` |
| Génération de quiz | ✅ (partielle) | `api/v1/lms/question_bank.py` `/question-bank/generate-quiz` |
| Récompenses (étoiles/XP) | ✅ | `GameConfig.reward_stars/reward_xp` ; domaine rewards |

**Conséquence** : aucune nouvelle table n'est strictement nécessaire. On ajoute
une valeur d'enum, des schémas de config, des players, et un service de
génération de quiz.

---

## 1. Fonctionnalité A — Puzzle de lettres

### 1.1 Idée
Une lettre s'affiche comme un **puzzle à assembler**. Chaque pièce porte un
**mot-exemple commençant par cette lettre** + un **emoji/illustration** (animal,
objet…). Au survol/clic d'une pièce, le TTS **lit la lettre puis le mot**
(« أ … أرنب »). 2-3 exemples par lettre.

### 1.2 Modèle de données — réutilise `GameConfig`
- **Backend** : ajouter une valeur à l'enum `GameType` dans `models/games.py` :
  ```python
  LETTER_PUZZLE = "letter_puzzle"
  ```
  (le validateur `validate_game_type` l'accepte automatiquement). Aucune autre
  colonne : tout vit dans `GameConfig.config` (JSONB), comme `memory_match`.
- **Schéma `config` proposé** (même style que `MemoryMatchConfig` /
  `VocabularyCardsConfig`) :
  ```jsonc
  {
    "letter": "أ",
    "language": "ar",          // "ar" | "fr" | "en"
    "letter_audio_url": null,    // si null → TTS runtime
    "pieces": [
      { "word": "أرنب", "emoji": "🐰", "image_url": null, "audio_url": null },
      { "word": "أسد",  "emoji": "🦁", "image_url": null, "audio_url": null },
      { "word": "أناناس","emoji": "🍍", "image_url": null, "audio_url": null }
    ]
  }
  ```
- **Réutilisation directe** : la map `_letterExamples` de `tts_service.dart`
  fournit déjà un mot par lettre arabe → seed initial. On l'étend à 2-3 mots +
  emoji, puis on ajoute les maps `fr` et `en`.

### 1.3 Langues & niveau (config-driven)
- **Ordre de livraison** : Arabe → Français → Anglais. Chaque langue = des
  `GameConfig` avec `language` + `target_age_min/max` (déjà sur `GameConfig`).
- **Gating par niveau** : l'Anglais n'apparaît qu'au-delà d'un niveau ; on filtre
  les configs par `target_age_min/max` (et/ou un `level_band`) côté requête,
  cohérent avec `resolveAgeTier`/`useAgeTheme` déjà en place.
- **Pas de logique en dur** : on livre juste **les configurations** (2-3 exemples
  chacune), l'UI est générique.

### 1.4 UI — players
- **Web** : `web/src/features/ai/games/ui/LetterPuzzleGame.tsx` (à côté de
  `MemoryMatchGame.tsx`). Drag-drop des pièces (réutiliser la lib d'interaction
  des jeux existants), grande lettre cible, pièces avec emoji + mot, halo de
  succès (`CelebrationOverlay` existe déjà).
- **Mobile** : nouveau widget sous la feature jeux, même contrat de `config`.
- **Lecture guidée** : au tap d'une pièce → `tts.speak(word)` ; au lancement →
  `tts.speak(letter)`. Voir §3 (hybride).
- **Récompenses** : à la complétion → attribuer `reward_stars`/`reward_xp` via le
  domaine rewards existant.

### 1.5 Changements backend (résumé)
1. `models/games.py` : `GameType.LETTER_PUZZLE`.
2. `schemas` jeux : un `LetterPuzzleConfig` (validation des pièces : ≥3, ≤6).
3. `seed` : quelques `GameConfig` arabes d'exemple (depuis `_letterExamples`).
4. Endpoint de liste de jeux : filtrage par `language` + tranche d'âge (souvent
   déjà supporté par les filtres existants).

---

## 2. Fonctionnalité B — Quiz audio automatique après PDF+audio

### 2.1 Idée
Après un **contenu PDF + audio**, proposer automatiquement un **quiz parlé** :
chaque question peut être lue à voix haute. Le quiz est lié au contenu source.

### 2.2 Déclencheur & lien
- Un « PDF avec audio » = un `ContentItem` (`content_type` PDF) avec des
  `ContentItemAsset` dont `asset_type` audio, et `narration_text` par page.
- À la **publication** d'un tel contenu (ou à la demande), créer un `Quiz`
  (`status='draft'`) **lié via `original_content_id`** au `ContentItem`.
- Le `narration_text` des pages = la **source textuelle** des questions.

### 2.3 Pipeline de génération FUSIONNÉ (IA + template + enseignant)

> Décision utilisateur : « merger entre toutes ». Les trois sources alimentent le
> **même** `Quiz` brouillon ; l'enseignant valide avant publication.

```
ContentItem (PDF+audio, narration_text par page)
        │
        ├─ Source IA      : ai_service/claude_provider génère N questions
        │                   depuis narration_text (origin="ai")
        ├─ Source TEMPLATE : stems déterministes depuis métadonnées
        │                   (lettre, sujet, phrases de narration) (origin="template")
        └─ Source ENSEIGNANT: l'enseignant ajoute/édite (origin="teacher")
                          │
                          ▼
                 Quiz (status=draft, original_content_id=…)
                 chaque QuizQuestion porte une étiquette de source
                          │
                 Revue enseignant (éditeur quiz existant)
                          │
                          ▼
                 Quiz publié → visible élève
```

- **Étiquette de source** : stocker l'origine par question (p.ex. dans
  `QuizQuestion.options`/un champ meta ou `explanation` préfixé) pour que
  l'enseignant voie d'où vient chaque question. *(Décision §5.)*
- **Réutilisation** : `services/ai/ai_service.py` + `claude_provider.py` pour
  l'IA ; le flux `generate-quiz` de `question_bank.py` comme patron d'API.
- **Garde-fou** : rien n'est montré à l'élève avant publication (statut draft +
  revue) — cohérent avec le workflow de contenu existant.

### 2.4 Audio par question (hybride)
Pour chaque `QuizQuestion` :
1. Si un **fichier audio** est disponible (`question_media_path`, ou un asset
   audio de la page source) → **le jouer**.
2. Sinon → **TTS runtime** dans la langue du contenu (`ContentItem.language`) :
   `flutter_tts` (mobile) / Web Speech API (web).

### 2.5 UI — players de quiz
- **Web** : étendre le quiz player (`features/lms/student/ui/QuizPlayerPage.tsx`)
  avec un bouton « 🔊 Écouter » par question (audio sinon Web Speech).
- **Mobile** : idem dans le quiz player mobile, via `TtsService`.
- **Élève** : à la fin d'un contenu PDF+audio, CTA « Quiz » si un quiz publié est
  lié (`original_content_id`).

### 2.6 Changements backend (résumé)
1. `services/lms/quiz_service.py` (ou nouveau `quiz_from_content.py`) :
   `generate_quiz_from_content(content_id, sources=[ai|template|teacher])`.
2. Endpoint : `POST /lms/quizzes/from-content/{content_id}` (brouillon).
3. Brancher la génération IA sur `ai_service` ; templates déterministes en
   fallback/complément.
4. Lien `original_content_id` + statut draft + revue.

---

## 3. Architecture TTS partagée (hybride)

| Plateforme | Moteur | État |
|---|---|---|
| Mobile | **`flutter_tts`** via `TtsService` (`shared/services/tts_service.dart`) | ✅ existe (arabe `ar-SA`, vitesse/pitch, praise) — étendre fr/en |
| Web | **Web Speech API** (`window.speechSynthesis` + `SpeechSynthesisUtterance`) | ❌ à créer : petit hook `useSpeech()` dans `shared/hooks/` |

**Règle hybride unique (puzzle ET quiz)** :
```
parler(texte, {audioUrl?, lang}):
  si audioUrl existe  → jouer le fichier
  sinon               → TTS(lang)  // flutter_tts | speechSynthesis
```
- **Langues** : `ar`, `fr`, `en`. Web Speech choisit la voix selon `lang`
  (disponibilité dépend de l'OS/navigateur — prévoir un fallback gracieux).
- **Accessibilité** : bouton « écouter » explicite + auto-lecture optionnelle pour
  maternelle (cohérent avec les tiers d'âge).

---

## 4. Séquencement proposé (phases)

| Phase | Contenu | Dépend de |
|---|---|---|
| 1 | Web Speech `useSpeech()` + extension `TtsService` (fr/en) | — |
| 2 | Puzzle de lettres **arabe** : enum + config + players web/mobile + seed | Phase 1 |
| 3 | Puzzle **français** puis **anglais** (gating niveau) = nouvelles configs | Phase 2 |
| 4 | Quiz depuis contenu : service + endpoint + lien + statut draft | — |
| 5 | Pipeline fusionné (IA + template + enseignant) + revue | Phase 4 |
| 6 | Audio par question (hybride) dans les players quiz web/mobile | Phases 1,4 |
| 7 | Récompenses + branchement élève (CTA après contenu) | Phases 2,4 |

---

## 5. Décisions ouvertes (à trancher avant code)

1. **Emoji vs illustrations** pour les pièces : emoji seul (rapide, gratuit) ou
   prévoir `image_url` optionnel (plus joli, plus d'assets) ? *(le schéma
   supporte déjà les deux)*
2. **Stockage de l'origine** des questions (IA/template/enseignant) : nouveau
   champ `source` sur `QuizQuestion`, ou réutiliser un champ meta JSONB ?
3. **Auto-génération** du quiz : automatique à la publication du contenu, ou
   bouton « Générer le quiz » côté enseignant ?
4. **Nombre de questions** par défaut (p.ex. 5) et **types** (QCM audio, vrai/faux,
   association image↔mot) ?
5. **Voix TTS** : se contenter des voix système (gratuit, variable) ou prévoir,
   pour le contenu phare, des fichiers audio pré-générés (voix constante) ?
6. **Anglais** : à partir de quel niveau exactement (seuil `target_age`/`level_band`) ?

---

_Spec rédigée contre le code réel ; chaque brique citée existe et est extensible._
