import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/secure_storage.dart';
import 'package:ecole_platform/shared/ui/app_theme.dart';
import 'package:ecole_platform/shared/ui/app_theme_dark.dart';

class _TestLocaleStorage implements SecureTokenStorage {
  _TestLocaleStorage(this.localeCode);

  final String localeCode;

  @override
  Future<void> clearAll() async {}

  @override
  Future<String?> getCsrfToken() async {
    return null;
  }

  @override
  Future<String?> getLocaleCode() async {
    return localeCode;
  }

  @override
  Future<String?> getRefreshToken() async {
    return null;
  }

  @override
  Future<String?> getThemeMode() async {
    return null;
  }

  @override
  Future<void> saveCsrfToken(String token) async {}

  @override
  Future<void> saveLocaleCode(String localeCode) async {}

  @override
  Future<void> saveRefreshToken(String token) async {}

  @override
  Future<void> saveThemeMode(String mode) async {}
}

Future<void> pumpApp(
  WidgetTester tester,
  Widget child, {
  List<Override> overrides = const [],
  GoRouter? router,
  String localeCode = 'fr',
}) async {
  final testRouter = router ??
      GoRouter(
        initialLocation: '/',
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => Scaffold(body: child),
          ),
        ],
      );

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        localeProvider.overrideWith(
          (ref) => LocaleNotifier(_TestLocaleStorage(localeCode)),
        ),
        ...overrides,
      ],
      child: MaterialApp.router(
        locale: Locale(localeCode),
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
        theme: appLightTheme,
        darkTheme: appDarkTheme,
        routerConfig: testRouter,
        builder: (context, routedChild) {
          return Directionality(
            textDirection:
                localeCode == 'ar' ? TextDirection.rtl : TextDirection.ltr,
            child: routedChild ?? const SizedBox.shrink(),
          );
        },
      ),
    ),
  );

  await tester.pump();
}
