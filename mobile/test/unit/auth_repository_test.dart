import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/auth_repository_impl.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';

import '../helpers/api_responses.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  test('login stores refresh token on success', () async {
    final api = MockApiClient();
    final storage = MockSecureTokenStorage();
    final repository = AuthRepositoryImpl(api: api, tokenStorage: storage);

    when(
      () => api.post(
        '/auth/login',
        body: any(named: 'body'),
        skipAuth: true,
      ),
    ).thenAnswer(
      (_) async => response(
        const {
          'access_token': 'access-1',
          'refresh_token': 'refresh-1',
        },
      ),
    );
    when(() => api.setAccessToken(any())).thenReturn(null);
    when(() => storage.saveRefreshToken('refresh-1')).thenAnswer((_) async {});

    final result = await repository.login(
      'parent@ecole.test',
      'secret',
      'school-1',
    );

    expect(result.accessToken, 'access-1');
    verify(() => api.setAccessToken('access-1')).called(1);
    verify(() => storage.saveRefreshToken('refresh-1')).called(1);
  });

  test('login surfaces API failures', () async {
    final api = MockApiClient();
    final storage = MockSecureTokenStorage();
    final repository = AuthRepositoryImpl(api: api, tokenStorage: storage);

    when(
      () => api.post(
        '/auth/login',
        body: any(named: 'body'),
        skipAuth: true,
      ),
    ).thenThrow(offlineError('No network'));

    expect(
      () => repository.login('parent@ecole.test', 'secret', 'school-1'),
      throwsA(isA<ApiClientError>()),
    );
  });

  test('refreshToken returns the current access token', () async {
    final api = MockApiClient();
    final storage = MockSecureTokenStorage();
    final repository = AuthRepositoryImpl(api: api, tokenStorage: storage);

    when(() => api.accessToken).thenReturn('access-123');

    final token = await repository.refreshToken();

    expect(token, 'access-123');
  });

  test('AuthNotifier performs biometric unlock when enabled', () async {
    final biometric = MockBiometricService();
    final storage = MockSecureTokenStorage();
    final authRepository = MockAuthRepository();
    final container = ProviderContainer(
      overrides: [
        biometricServiceProvider.overrideWithValue(biometric),
        secureStorageProvider.overrideWithValue(storage),
        authRepositoryProvider.overrideWithValue(authRepository),
      ],
    );
    addTearDown(container.dispose);

    when(() => biometric.isAvailable()).thenAnswer((_) async => true);
    when(() => biometric.isEnabled()).thenAnswer((_) async => true);
    when(() => biometric.shouldFallbackToPassword).thenReturn(false);
    when(
      () => biometric.authenticate(reason: any(named: 'reason')),
    ).thenAnswer((_) async => true);
    when(() => storage.getRefreshToken()).thenAnswer((_) async => null);

    container.read(authProvider);
    await _flushAsync();

    final unlocked =
        await container.read(authProvider.notifier).biometricUnlock();

    expect(unlocked, isTrue);
    verify(
      () => biometric.authenticate(reason: any(named: 'reason')),
    ).called(1);
  });
}

Future<void> _flushAsync() async {
  await Future<void>.delayed(Duration.zero);
  await Future<void>.delayed(Duration.zero);
}
