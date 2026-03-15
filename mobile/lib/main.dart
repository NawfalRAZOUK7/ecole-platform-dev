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

import 'dart:developer' as dev;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/router.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';

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

class EcolePlatformApp extends ConsumerWidget {
  const EcolePlatformApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

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
