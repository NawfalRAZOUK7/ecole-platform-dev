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

import 'dart:developer' as dev;

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/app/router.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/notifications/notifications_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/app_theme.dart';
import 'package:ecole_platform/shared/ui/app_theme_dark.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

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

  runApp(
    const ProviderScope(
      child: EcolePlatformApp(),
    ),
  );
}

class EcolePlatformApp extends ConsumerStatefulWidget {
  const EcolePlatformApp({super.key});

  @override
  ConsumerState<EcolePlatformApp> createState() => _EcolePlatformAppState();
}

class _EcolePlatformAppState extends ConsumerState<EcolePlatformApp>
    with WidgetsBindingObserver {
  final GlobalKey<ScaffoldMessengerState> _scaffoldMessengerKey =
      GlobalKey<ScaffoldMessengerState>();
  bool _biometricLocked = false;
  String? _connectedAccessToken;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initServices();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _initServices() async {
    try {
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
                    _scaffoldMessengerKey.currentState?.hideCurrentMaterialBanner();
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
        dev.log('Biometric unlock failed or skipped', name: 'Main');
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
    final router = ref.watch(routerProvider);
    final authState = ref.watch(authProvider);
    final themeMode = ref.watch(themeModeProvider);

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
      theme: appLightTheme,
      darkTheme: appDarkTheme,
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}
