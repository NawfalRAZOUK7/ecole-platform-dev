import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/main.dart';

void main() {
  testWidgets('App starts without crash', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: EcolePlatformApp(),
      ),
    );

    expect(find.byType(EcolePlatformApp), findsOneWidget);
  });
}
