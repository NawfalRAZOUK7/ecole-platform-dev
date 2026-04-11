import 'package:flutter/material.dart';
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

      await _loginAs(tester, 'parent@ecole.test');

      expect(find.text('Weekly digest'), findsOneWidget);

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

      await _loginAs(tester, 'teacher@ecole.test');

      container.read(routerProvider).go('/teacher/attendance');
      await tester.pumpAndSettle();

      await tester.tap(find.widgetWithText(DropdownButtonFormField<String>, 'Classe *'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Class 6A').last);
      await tester.pumpAndSettle();

      await tester.tap(find.widgetWithText(DropdownButtonFormField<String>, 'Période *'));
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

      await _loginAs(tester, 'parent@ecole.test');

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

      await _loginAs(tester, 'parent@ecole.test');
      container.read(routerProvider).go('/profile');
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.byKey(const Key('profile.theme.mode')),
        300,
        scrollable: find.byType(Scrollable).first,
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

      await _loginAs(tester, 'parent@ecole.test');
      container.read(routerProvider).go('/profile');
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.byKey(const Key('profile.locale.code')),
        300,
        scrollable: find.byType(Scrollable).first,
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

Future<void> _loginAs(WidgetTester tester, String email) async {
  await tester.enterText(find.byType(TextFormField).at(0), email);
  await tester.enterText(find.byType(TextFormField).at(1), 'password123');
  await tester.tap(find.text('Se connecter'));
  await tester.pumpAndSettle();
}

Future<void> _selectDropdownValue(
  WidgetTester tester, {
  required Key fieldKey,
  required String optionText,
}) async {
  await tester.tap(find.byKey(fieldKey));
  await tester.pumpAndSettle();
  await tester.tap(find.text(optionText).last);
  await tester.pumpAndSettle();
}
