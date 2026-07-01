/// Sentry Debug Button — triggers a test error to verify Sentry integration.
///
/// Add this widget temporarily to any screen to confirm errors are captured.

import 'package:flutter/material.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

class SentryDebugButton extends StatelessWidget {
  const SentryDebugButton({super.key});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {
        Sentry.addBreadcrumb(
          Breadcrumb(
            message: 'User triggered test error',
            category: 'test',
            level: SentryLevel.info,
          ),
        );
        throw StateError('This is a Sentry test exception from Flutter!');
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
      ),
      child: const Text('Break the world (Sentry test)'),
    );
  }
}
