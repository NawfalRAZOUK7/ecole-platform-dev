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

## Setup

```bash
flutter pub get
flutter run
```

## Key Dependencies

- **State Management:** flutter_riverpod
- **Navigation:** go_router
- **HTTP Client:** dio
- **Offline Cache:** sqflite (TTL policies per E2)
- **Secure Storage:** flutter_secure_storage (token storage)
- **Push Notifications:** firebase_messaging + firebase_core
