import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/app/router.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/app_theme.dart';
import 'package:ecole_platform/shared/ui/app_theme_dark.dart';

Future<ProviderContainer> pumpIntegrationApp(
  WidgetTester tester, {
  required List<Override> overrides,
}) async {
  final container = ProviderContainer(overrides: overrides);
  addTearDown(container.dispose);

  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: const _IntegrationApp(),
    ),
  );
  await tester.pumpAndSettle();

  return container;
}

class _IntegrationApp extends ConsumerWidget {
  const _IntegrationApp();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);
    final localeCode = ref.watch(localeProvider);

    ref.read(apiClientProvider).setLocale(localeCode);

    return MaterialApp.router(
      title: 'École Platform',
      debugShowCheckedModeBanner: false,
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
      builder: (context, child) {
        return Directionality(
          textDirection:
              localeCode == 'ar' ? TextDirection.rtl : TextDirection.ltr,
          child: child ?? const SizedBox.shrink(),
        );
      },
      theme: appLightTheme,
      darkTheme: appDarkTheme,
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}
