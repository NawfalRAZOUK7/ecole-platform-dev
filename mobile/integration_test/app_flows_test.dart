import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ecole_platform/app/router.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';

import 'helpers/fake_app_environment.dart';
import 'helpers/integration_app.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('App flows', () {
    testWidgets('login, feed, notifications, and logout flow', (tester) async {
      final environment = FakeAppEnvironment();
      final container = await pumpIntegrationApp(
        tester,
        overrides: environment.overrides(),
      );

      await _loginAs(tester, container, 'parent@ecole.test');

      expect(find.text('Mes enfants'), findsOneWidget);

      container.read(routerProvider).go('/notifications');
      await tester.pumpAndSettle();

      expect(find.text('Attendance update'), findsOneWidget);

      container.read(routerProvider).go('/profile');
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Déconnexion'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.text('Déconnexion'));
      await tester.pumpAndSettle();

      expect(container.read(authProvider).isAuthenticated, isFalse);
      expect(find.text('Connexion'), findsOneWidget);
    });

    testWidgets('teacher marks attendance and parent sees history',
        (tester) async {
      final environment = FakeAppEnvironment();
      final container = await pumpIntegrationApp(
        tester,
        overrides: environment.overrides(),
      );

      await _loginAs(tester, container, 'teacher@ecole.test');

      container.read(routerProvider).go('/teacher/attendance');
      await tester.pumpAndSettle();
      await _waitForWidget(tester, find.text('Classe *'));

      await tester.tap(
        find.widgetWithText(DropdownButtonFormField<String>, 'Classe *'),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Class 6A').last);
      await tester.pumpAndSettle();

      await tester.tap(
        find.widgetWithText(DropdownButtonFormField<String>, 'Période *'),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Morning').last);
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(
        find.text('Enregistrer'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.tap(find.text('Enregistrer'));
      await tester.pumpAndSettle();

      expect(find.text('Présences enregistrées avec succès'), findsOneWidget);

      await container.read(authProvider.notifier).logout();
      await tester.pumpAndSettle();

      await _loginAs(tester, container, 'parent@ecole.test');

      container.read(routerProvider).go(
            '/attendance/history?classId=class-1&studentId=student-1',
          );
      await tester.pumpAndSettle();

      expect(find.text('Recent sessions'), findsOneWidget);
      expect(find.text('present'), findsWidgets);
    });

    testWidgets('dark mode preference persists across restart', (tester) async {
      final environment = FakeAppEnvironment();
      var container = await pumpIntegrationApp(
        tester,
        overrides: environment.overrides(),
      );

      await _loginAs(tester, container, 'parent@ecole.test');
      container.read(routerProvider).go('/profile');
      await tester.pumpAndSettle();
      await _scrollUntilVisible(
        tester,
        find.byKey(const Key('profile.theme.mode')),
      );

      await _selectDropdownValue(
        tester,
        fieldKey: const Key('profile.theme.mode'),
        optionText: 'Sombre',
      );

      expect(container.read(themeModeProvider), ThemeMode.dark);

      container = await pumpIntegrationApp(
        tester,
        overrides: environment.overrides(),
      );

      expect(container.read(themeModeProvider), ThemeMode.dark);
      final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
      expect(app.themeMode, ThemeMode.dark);
    });

    testWidgets('language switch applies RTL layout', (tester) async {
      final environment = FakeAppEnvironment();
      final container = await pumpIntegrationApp(
        tester,
        overrides: environment.overrides(),
      );

      await _loginAs(tester, container, 'parent@ecole.test');
      container.read(routerProvider).go('/profile');
      await tester.pumpAndSettle();
      await _scrollUntilVisible(
        tester,
        find.byKey(const Key('profile.locale.code')),
      );

      await _selectDropdownValue(
        tester,
        fieldKey: const Key('profile.locale.code'),
        optionText: 'العربية',
      );

      expect(container.read(localeProvider), 'ar');
      final directionality = tester.widget<Directionality>(
        find.byType(Directionality).first,
      );
      expect(directionality.textDirection, TextDirection.rtl);
    });
  });
}

Future<void> _loginAs(
  WidgetTester tester,
  ProviderContainer container,
  String email,
) async {
  await container.read(authProvider.notifier).login(
        email,
        'password123',
        '00000000-0000-4000-8000-000000000001',
      );
  await tester.pumpAndSettle();
}

Future<void> _selectDropdownValue(
  WidgetTester tester, {
  required Key fieldKey,
  required String optionText,
}) async {
  await _scrollUntilVisible(tester, find.byKey(fieldKey));
  await tester.tap(find.byKey(fieldKey));
  await tester.pumpAndSettle();
  await tester.tap(find.text(optionText).last);
  await tester.pumpAndSettle();
}

Future<void> _waitForWidget(
  WidgetTester tester,
  Finder finder, {
  int attempts = 20,
}) async {
  for (var i = 0; i < attempts; i += 1) {
    if (finder.evaluate().isNotEmpty) return;
    await tester.pump(const Duration(milliseconds: 100));
  }
  expect(finder, findsWidgets);
}

Future<void> _scrollUntilVisible(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isNotEmpty) return;
  final scrollables = find.byType(Scrollable);
  expect(scrollables, findsWidgets);
  await tester.scrollUntilVisible(
    finder,
    300,
    scrollable: scrollables.first,
  );
  await tester.pumpAndSettle();
}
