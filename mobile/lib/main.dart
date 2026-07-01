/// École Platform — Mobile App Entry Point
///
/// 3-layer architecture per Pack E2:
/// - presentation/ — Screens, widgets, navigation, view-models
/// - domain/ — Use-cases, business rules, repository interfaces
/// - data/ — API client, DTOs, persistence, cache
///
/// State management: Riverpod (DEC-E2-002)
/// Navigation: go_router (DEC-E2-010)
/// Offline: SQLite with TTL policies (DEC-E2-020)
/// Phase 5A: Firebase push init, biometric lock on app resume, WS connect.

import 'dart:async';
import 'dart:developer' as dev;

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/app/router/app_router.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/communication/notifications/notifications_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/app_theme.dart';
import 'package:ecole_platform/shared/ui/app_theme_dark.dart';
import 'package:ecole_platform/shared/ui/widgets/app_splash_screen.dart';

const bool _demoMobileVideo =
    bool.fromEnvironment('DEMO_MOBILE_VIDEO', defaultValue: false);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env', isOptional: true);

  // Mobile uses MOBILE_SENTRY_DSN (separate from backend SENTRY_DSN in Doppler).
  // Falls back to legacy SENTRY_DSN env var for backward compatibility.
  final sentryDsn =
      dotenv.env['MOBILE_SENTRY_DSN'] ?? dotenv.env['SENTRY_DSN'] ?? '';
  final appEnv = dotenv.env['APP_ENV'] ?? 'development';
  final isProd = appEnv == 'production';

  if (sentryDsn.isEmpty) {
    // No Sentry DSN configured — start app without Sentry instrumentation.
    runApp(
      ProviderScope(
        child: EcolePlatformApp(initFuture: _runStartupInit()),
      ),
    );
    return;
  }

  await SentryFlutter.init(
    (options) {
      options.dsn = sentryDsn;
      options.environment = appEnv;
      options.tracesSampleRate = isProd ? 0.1 : 1.0;
      options.profilesSampleRate = isProd ? 0.1 : 1.0;
      options.sendDefaultPii = !isProd;
    },
    appRunner: () async {
      // Run heavy init work in parallel with the splash screen.
      final initFuture = _runStartupInit();

      runApp(
        ProviderScope(
          child: EcolePlatformApp(initFuture: initFuture),
        ),
      );
    },
  );
}

Future<void> _runStartupInit() async {
  try {
    await Firebase.initializeApp();
  } catch (e) {
    dev.log('Firebase init skipped: $e', name: 'Main');
  }

  // Prune expired cache entries on startup
  try {
    await CacheStore().pruneExpired();
  } catch (e) {
    dev.log('Cache prune on startup failed: $e', name: 'Main');
  }
}

class EcolePlatformApp extends ConsumerStatefulWidget {
  final Future<void> initFuture;

  const EcolePlatformApp({super.key, required this.initFuture});

  @override
  ConsumerState<EcolePlatformApp> createState() => _EcolePlatformAppState();
}

class _EcolePlatformAppState extends ConsumerState<EcolePlatformApp>
    with WidgetsBindingObserver {
  final GlobalKey<ScaffoldMessengerState> _scaffoldMessengerKey =
      GlobalKey<ScaffoldMessengerState>();
  bool _biometricLocked = false;
  String? _connectedAccessToken;
  bool _splashDone = false;
  late final ProviderSubscription<AuthState> _authSubscription;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initServices();
    // Listen to auth state changes to force WS reconnect with fresh token
    _authSubscription = ref.listenManual<AuthState>(authProvider, (prev, next) {
      if (next.isAuthenticated && (prev == null || !prev.isAuthenticated)) {
        _connectedAccessToken = null;
      }
    });
  }

  @override
  void dispose() {
    _authSubscription.close();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _initServices() async {
    try {
      await widget.initFuture;
      final push = ref.read(pushNotificationProvider);
      push.onForegroundMessage = (message) {
        final t = AppLocalizations.of(ref);
        final title = message.notification?.title ?? 'Notification';
        final body = message.notification?.body ?? '';
        _scaffoldMessengerKey.currentState
          ?..clearMaterialBanners()
          ..showMaterialBanner(
            MaterialBanner(
              content: Text(body.isEmpty ? title : '$title\n$body'),
              leading: const Icon(Icons.notifications_active_outlined),
              actions: [
                TextButton(
                  onPressed: () {
                    _scaffoldMessengerKey.currentState
                        ?.hideCurrentMaterialBanner();
                  },
                  child: Text(t.t('notifications.dismiss')),
                ),
              ],
            ),
          );
      };
      await push.initialize();
    } catch (e) {
      dev.log('Push notification init failed: $e', name: 'Main');
    }

    try {
      await ref.read(connectivityServiceProvider).initialize();
    } catch (e) {
      dev.log('Connectivity service init failed: $e', name: 'Main');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);

    if (state == AppLifecycleState.resumed) {
      _onAppResumed();
    } else if (state == AppLifecycleState.paused) {
      _onAppPaused();
    }
  }

  /// Called when app returns to foreground — check biometric lock.
  Future<void> _onAppResumed() async {
    final authState = ref.read(authProvider);
    if (!authState.isAuthenticated) return;

    // Attempt biometric unlock if enabled
    if (authState.biometricEnabled && !_biometricLocked) {
      _biometricLocked = true;
      final success = await ref.read(authProvider.notifier).biometricUnlock();
      _biometricLocked = false;

      if (!success) {
        dev.log('Biometric unlock failed — forcing logout', name: 'Main');
        await ref.read(authProvider.notifier).logout();
      }
    }

    // Reset push badge when user opens app
    ref.read(pushNotificationProvider).resetBadge();
    ref.read(notificationsProvider.notifier).refreshBadge();
  }

  /// Called when app goes to background.
  void _onAppPaused() {
    // No-op for now; WS stays connected for a while
  }

  @override
  Widget build(BuildContext context) {
    if (!_splashDone) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: appLightTheme,
        home: AppSplashScreen(
          initFuture: widget.initFuture,
          onComplete: () => setState(() => _splashDone = true),
        ),
      );
    }

    final router = ref.watch(routerProvider);
    final authState = ref.watch(authProvider);
    final themeMode = ref.watch(themeModeProvider);
    final localeCode = ref.watch(localeProvider);
    final locale = Locale(localeCode);
    ref.read(apiClientProvider).setLocale(localeCode);

    // Connect/disconnect WebSocket based on auth state
    final wsClient = ref.read(wsClientProvider);
    wsClient.onEvent = (event) {
      if (event.type.name == 'notificationCreated') {
        ref.read(notificationsProvider.notifier).refreshBadge();
      }
    };
    final pushService = ref.read(pushNotificationProvider);
    if (authState.isAuthenticated) {
      final api = ref.read(apiClientProvider);
      if (api.accessToken != null && api.accessToken != _connectedAccessToken) {
        _connectedAccessToken = api.accessToken;
        wsClient.connect(api.accessToken!);
        pushService.syncTokenRegistration();
        ref.read(notificationsProvider.notifier).refreshBadge();
      }
    } else {
      _connectedAccessToken = null;
      wsClient.disconnect();
    }

    final pendingDeepLink = pushService.pendingDeepLink;
    if (pendingDeepLink != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        router.go(pendingDeepLink.route);
        pushService.clearDeepLink();
      });
    }

    return MaterialApp.router(
      title: 'École Platform',
      debugShowCheckedModeBanner: false,
      scaffoldMessengerKey: _scaffoldMessengerKey,
      locale: locale,
      supportedLocales: const [
        Locale('fr'),
        Locale('ar'),
        Locale('en'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) {
        return Directionality(
          textDirection:
              localeCode == 'ar' ? TextDirection.rtl : TextDirection.ltr,
          child: _DemoMobileAutopilot(
            enabled: _demoMobileVideo,
            router: router,
            child: child ?? const SizedBox.shrink(),
          ),
        );
      },
      theme: appLightTheme,
      darkTheme: appDarkTheme,
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}

class _DemoStep {
  final String route;
  final String caption;

  const _DemoStep(
    this.route,
    this.caption,
  );
}

class _DemoMobileAutopilot extends ConsumerStatefulWidget {
  final bool enabled;
  final GoRouter router;
  final Widget child;

  const _DemoMobileAutopilot({
    required this.enabled,
    required this.router,
    required this.child,
  });

  @override
  ConsumerState<_DemoMobileAutopilot> createState() =>
      _DemoMobileAutopilotState();
}

class _DemoMobileAutopilotState extends ConsumerState<_DemoMobileAutopilot> {
  bool _started = false;
  String _caption = 'Connexion mobile : accès élève et parent sécurisé';

  static const _schoolId = '00000000-0000-4000-8000-000000000001';

  @override
  void didUpdateWidget(covariant _DemoMobileAutopilot oldWidget) {
    super.didUpdateWidget(oldWidget);
    _startIfNeeded();
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _startIfNeeded());
  }

  void _startIfNeeded() {
    if (!widget.enabled || _started || !mounted) return;
    _started = true;
    unawaited(_run());
  }

  Future<void> _run() async {
    await _show(
      'Écran de connexion mobile : aucune saisie filmée',
      const Duration(seconds: 3),
    );

    await _login(
      email: 'yassine.alaoui@ecole-benani.ma',
      password: 'student123',
      expectedRole: 'STD',
      caption: 'Connexion élève préparée hors champ',
    );

    await _walk(const [
      _DemoStep(
        '/student/home',
        'Accueil élève : progression, badges et dernières activités',
      ),
      _DemoStep(
        '/student/quizzes',
        'Quiz : exercices et correction immédiate',
      ),
      _DemoStep(
        '/student/writing',
        'Écriture créative : consigne et éditeur guidé',
      ),
      _DemoStep(
        '/student/content',
        'Mon contenu : histoires, coloriages et ressources',
      ),
      _DemoStep(
        '/student/games',
        'Jeux éducatifs trilingues : activités courtes et ludiques',
      ),
      _DemoStep(
        '/games/memory',
        'Memory : une activité rapide liée à la gamification',
      ),
      _DemoStep(
        '/rewards',
        'Récompenses : étoiles, XP, niveaux et badges',
      ),
      _DemoStep(
        '/leaderboard',
        'Classement : engagement et progression visibles',
      ),
      _DemoStep(
        '/skills',
        'Passeport de compétences : dimensions et niveaux',
      ),
      _DemoStep(
        '/announcements',
        'Annonces : communication école-famille',
      ),
      _DemoStep(
        '/notifications',
        'Notifications : suivi des événements importants',
      ),
      _DemoStep(
        '/student/content',
        'Mode hors-ligne : contenus accessibles, puis synchronisation au retour réseau',
      ),
    ]);

    await _show(
      'Transition vers le compte parent, sans filmer les identifiants',
      const Duration(seconds: 2),
    );
    await ref.read(authProvider.notifier).logout();
    await Future<void>.delayed(const Duration(milliseconds: 900));

    await _login(
      email: 'parent.alaoui@gmail.com',
      password: 'parent123',
      expectedRole: 'PAR',
      caption: 'Connexion parent préparée hors champ',
    );

    await _walk(const [
      _DemoStep(
        '/family',
        'Vue parent : enfants rattachés et suivi familial',
      ),
      _DemoStep(
        '/parent/progress',
        'Progression : notes, compétences et assiduité',
      ),
      _DemoStep(
        '/feed',
        "Fil d'actualité : nouvelles de l'école",
      ),
      _DemoStep(
        '/profile',
        'Profil et sécurité : préférences, 2FA et sessions',
      ),
    ]);

    await _show(
      'Ecole Platform mobile : apprentissage, famille et synchronisation réunis',
      const Duration(seconds: 4),
    );
  }

  Future<void> _login({
    required String email,
    required String password,
    required String expectedRole,
    required String caption,
  }) async {
    await _show(caption, const Duration(milliseconds: 800));
    await ref.read(authProvider.notifier).login(email, password, _schoolId);
    await _waitForRole(expectedRole);
  }

  Future<void> _waitForRole(String role) async {
    final deadline = DateTime.now().add(const Duration(seconds: 18));
    while (mounted && DateTime.now().isBefore(deadline)) {
      final state = ref.read(authProvider);
      if (state.isAuthenticated && state.user?.role == role) return;
      await Future<void>.delayed(const Duration(milliseconds: 250));
    }
  }

  Future<void> _walk(List<_DemoStep> steps) async {
    for (final step in steps) {
      if (!mounted) return;
      widget.router.go(step.route);
      await _show(step.caption, const Duration(seconds: 4));
    }
  }

  Future<void> _show(String caption, Duration duration) async {
    if (!mounted) return;
    setState(() => _caption = caption);
    await Future<void>.delayed(duration);
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.enabled) return widget.child;

    return Stack(
      children: [
        widget.child,
        Positioned(
          left: 18,
          right: 18,
          bottom: 22,
          child: IgnorePointer(
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xDD0F172A),
                borderRadius: BorderRadius.circular(999),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x330F172A),
                    blurRadius: 24,
                    offset: Offset(0, 10),
                  ),
                ],
              ),
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                child: Text(
                  _caption,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    decoration: TextDecoration.none,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    height: 1.25,
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
