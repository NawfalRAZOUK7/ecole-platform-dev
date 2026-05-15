# École Platform — Mobile App

Flutter mobile application for iOS and Android.

## Architecture (Pack E2)

```
lib/
├── presentation/  # Screens, widgets, navigation, view-models
├── domain/        # Use-cases, business rules, repository interfaces
├── data/          # API client, DTOs, persistence, cache
└── shared/
    └── ui/
        └── tokens/  # Design tokens from E5
```

Feature code is grouped by backend bounded context under `lib/features/<domain>/...`:

```
features/
├── academic/       # attendance, gradebook, progress, skills, timetable, academic student/teacher flows
├── admin/          # dashboard, users, invitations, feature toggles, compliance
├── ai/             # games and rewards
├── auth/
├── billing/        # billing policies, budgets, invoices
├── communication/  # calendar, messages, notifications
├── content/        # content catalog, coloring, documents, feed, teacher/student content
├── lms/            # quizzes, question bank, rubrics, submissions, LMS student/teacher flows
├── reports/        # analytics, reports, financial health
├── school/         # micro-schools and school settings
├── sync/
└── user/           # profile, family, student home
```

Domain entities, repository interfaces, and repository implementations use the same context folders under `domain/entities/`, `domain/repositories/`, and `data/repositories_impl/`. Shared infrastructure remains flat in `data/api/`, `data/local_store/`, `data/dto/`, `data/services/`, `app/`, `presentation/`, `shared/`, and `l10n/`.

`third_party/` contains vendored Flutter packages required by the current mobile build. Prefer normal `pub.dev` dependencies for new packages; only vendor when the package is intentionally patched or unavailable through the public registry, and document the upgrade path with the dependency change.

## Setup

```bash
flutter pub get
flutter run
```

## Kid-Facing Content & Gamification

The mobile app is the primary interactive experience for early-learning content, games, and rewards.

### UI foundations

- **Cairo font** is the default display and body typeface for the kid-facing experience.
- **`KidsContentColors`** defines the shared palette for stories, rewards, coloring, mini-games, and the Sami mascot.
- **Animated guide widget** is implemented through `AnimatedGuide` and the `SamiMascot` family of widgets for story, coloring, and game coaching.

### Arabic TTS

- **`TtsService`** wraps `flutter_tts` with Arabic defaults (`ar-SA`), letter examples, praise phrases, and instruction playback.
- Used in story reading, vocabulary cards, memory prompts, and the animated guide's speech bubble interactions.

### Routes

- Story reader: `/student/content/:id/read`
- Rewards hub: `/rewards`
- Games:
  - `/games/memory`
  - `/games/sorting`
  - `/games/vocabulary`
- Coloring list: `/coloring`
- Coloring page: `/coloring/:id`

### Feature summary

- **Story reader** supports ordered page assets, narration, Arabic letter themes, and reward completion.
- **Rewards** exposes stars, XP, levels, streaks, badges, and celebration/confetti widgets.
- **Games** includes memory match, sorting, and vocabulary cards backed by configurable game payloads.
- **Coloring** provides interactive drawing, save/export, and reward submission flows.

## Key Dependencies

- **State Management:** flutter_riverpod
- **Navigation:** go_router
- **HTTP Client:** dio
- **Offline Cache:** sqflite (TTL policies per E2)
- **Secure Storage:** flutter_secure_storage (token storage)
- **Push Notifications:** firebase_messaging + firebase_core
- **Text-to-Speech:** flutter_tts
