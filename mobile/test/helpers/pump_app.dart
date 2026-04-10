import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/app_theme.dart';
import 'package:ecole_platform/shared/ui/app_theme_dark.dart';

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
        localeProvider.overrideWith((ref) => localeCode),
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
