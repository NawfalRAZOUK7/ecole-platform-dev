import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/main.dart';
import 'package:ecole_platform/shared/connectivity_service.dart';
import 'package:ecole_platform/shared/push_notifications.dart';
import 'package:ecole_platform/shared/secure_storage.dart';
import 'package:ecole_platform/data/api/ws_client.dart';

import 'helpers/test_services.dart';

void main() {
  testWidgets('App starts without crash', (tester) async {
    final pushService = TestPushNotificationService();
    final connectivityService = TestConnectivityService();
    final secureStorage = TestSecureTokenStorage();
    final biometricService = TestBiometricService();
    final wsClient = TestWsClient();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          pushNotificationProvider.overrideWithValue(
            pushService as PushNotificationService,
          ),
          connectivityServiceProvider.overrideWithValue(
            connectivityService as ConnectivityService,
          ),
          secureStorageProvider.overrideWithValue(
            secureStorage as SecureTokenStorage,
          ),
          biometricServiceProvider.overrideWithValue(
            biometricService as BiometricService,
          ),
          wsClientProvider.overrideWithValue(
            wsClient as WsClient,
          ),
        ],
        child: EcolePlatformApp(),
      ),
    );

    await tester.pump();
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
