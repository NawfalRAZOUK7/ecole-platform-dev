import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/messages/chat_screen.dart';
import 'package:ecole_platform/features/messages/conversations_screen.dart';

import '../helpers/api_responses.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';
import '../helpers/test_services.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('ConversationsScreen renders the conversation list',
      (tester) async {
    final api = MockApiClient();
    final cache = MockCacheStore();

    when(() => cache.get('conversations:first')).thenAnswer((_) async => null);
    when(() => cache.put('conversations:first', any(), any()))
        .thenAnswer((_) async {});
    when(
      () => api.list(
        '/messages/conversations',
        params: const {'limit': '20'},
      ),
    ).thenAnswer((_) async => listResponse([_conversationJson()]));

    await pumpApp(
      tester,
      const ConversationsScreen(),
      overrides: _messageOverrides(api, cache),
    );
    await tester.pumpAndSettle();

    expect(find.text('Progress update'), findsOneWidget);
    expect(find.text('Thanks for the update'), findsOneWidget);
  });

  testWidgets('ChatScreen renders existing message bubbles', (tester) async {
    final api = MockApiClient();
    final cache = MockCacheStore();

    when(
      () => api.list(
        '/messages/conversations/conversation-1/messages',
        params: const {'limit': '50'},
      ),
    ).thenAnswer((_) async => listResponse([_messageJson()]));
    when(
      () => api.post(
        '/messages/conversations/conversation-1/read',
        body: const {'message_id': 'message-1'},
      ),
    ).thenAnswer((_) async => response(const {'ok': true}));

    await pumpApp(
      tester,
      const ChatScreen(conversationId: 'conversation-1'),
      overrides: _messageOverrides(api, cache),
    );
    await tester.pumpAndSettle();

    expect(find.text('Hello from the school app.'), findsOneWidget);
  });

  testWidgets('ChatScreen sends a new message from the composer',
      (tester) async {
    final api = MockApiClient();
    final cache = MockCacheStore();

    when(
      () => api.list(
        '/messages/conversations/conversation-1/messages',
        params: const {'limit': '50'},
      ),
    ).thenAnswer((_) async => listResponse(const []));
    when(
      () => api.post(
        '/messages/conversations/conversation-1/messages',
        body: const {'body': 'Hello there'},
      ),
    ).thenAnswer((_) async => response(_messageJson(body: 'Hello there')));

    await pumpApp(
      tester,
      const ChatScreen(conversationId: 'conversation-1'),
      overrides: _messageOverrides(api, cache),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'Hello there');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pumpAndSettle();

    expect(find.text('Hello there'), findsOneWidget);
  });
}

List<Override> _messageOverrides(MockApiClient api, MockCacheStore cache) {
  final authRepository = MockAuthRepository();
  final biometric = MockBiometricService();
  final storage = MockSecureTokenStorage();

  when(() => storage.getRefreshToken()).thenAnswer((_) async => null);
  when(() => biometric.isAvailable()).thenAnswer((_) async => false);
  when(() => biometric.isEnabled()).thenAnswer((_) async => false);

  return [
    ...buildMockRepositoryOverrides(authRepository: authRepository),
    apiClientProvider.overrideWithValue(api),
    cacheStoreProvider.overrideWithValue(cache),
    biometricServiceProvider.overrideWithValue(biometric),
    secureStorageProvider.overrideWithValue(storage),
    wsClientProvider.overrideWithValue(TestWsClient()),
  ];
}

Map<String, dynamic> _conversationJson() {
  return {
    'id': 'conversation-1',
    'school_id': 'school-1',
    'type': 'DIRECT',
    'created_by': 'user-1',
    'subject': 'Progress update',
    'participants': [
      {
        'user_id': 'user-2',
        'role_in_conversation': 'member',
        'joined_at': '2026-04-01T08:00:00Z',
        'muted': false,
      },
    ],
    'last_message_at': '2026-04-10T10:00:00Z',
    'last_message_body': 'Thanks for the update',
    'unread_count': 1,
    'created_at': '2026-04-01T08:00:00Z',
  };
}

Map<String, dynamic> _messageJson(
    {String body = 'Hello from the school app.'}) {
  return {
    'id': 'message-1',
    'conversation_id': 'conversation-1',
    'sender_id': 'user-2',
    'body': body,
    'sent_at': '2026-04-10T09:30:00Z',
  };
}
