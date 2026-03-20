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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// import 'package:firebase_core/firebase_core.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/app/router.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase for push notifications
  // Note: Firebase requires google-services.json (Android) / GoogleService-Info.plist (iOS)
  // Uncomment when Firebase is configured:
  // await Firebase.initializeApp();

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
  bool _biometricLocked = false;

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
    // Initialize push notifications (requires Firebase.initializeApp() first)
    // Uncomment when Firebase is configured:
    // try {
    //   await ref.read(pushNotificationProvider).initialize();
    // } catch (e) {
    //   dev.log('Push notification init failed: $e', name: 'Main');
    // }
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
  }

  /// Called when app goes to background.
  void _onAppPaused() {
    // No-op for now; WS stays connected for a while
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(routerProvider);
    final authState = ref.watch(authProvider);

    // Connect/disconnect WebSocket based on auth state
    final wsClient = ref.read(wsClientProvider);
    if (authState.isAuthenticated) {
      final api = ref.read(apiClientProvider);
      if (api.accessToken != null) {
        wsClient.connect(api.accessToken!);
      }
    } else {
      wsClient.disconnect();
    }

    return MaterialApp.router(
      title: 'École Platform',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF2563EB),
        useMaterial3: true,
        fontFamily: 'Inter',
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: const BorderSide(color: Color(0xFFE5E7EB)),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          filled: true,
          fillColor: const Color(0xFFF9FAFB),
        ),
      ),
      routerConfig: router,
    );
  }
}
