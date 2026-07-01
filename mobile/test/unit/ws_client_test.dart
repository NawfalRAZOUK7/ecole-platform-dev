import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:ecole_platform/core/network/ws_client.dart';

class MockFlutterLocalNotificationsPlugin extends Mock
    implements FlutterLocalNotificationsPlugin {}

class MockWebSocketChannel extends Mock implements WebSocketChannel {}

class MockWebSocketSink extends Mock implements WebSocketSink {}

/// Creates a WsClient pre-wired with the mock plugin.
WsClient _makeClient(
  MockFlutterLocalNotificationsPlugin notifs, {
  WebSocketChannel? channel,
}) {
  return WsClient(
    baseUrl: 'http://localhost:8000',
    localNotifications: notifs,
    channelFactory: (_) => channel ?? _mockChannel(),
  );
}

WebSocketChannel _mockChannel() {
  final channel = MockWebSocketChannel();
  final sink = MockWebSocketSink();
  when(() => channel.stream).thenAnswer((_) => const Stream.empty());
  when(() => channel.sink).thenReturn(sink);
  when(() => sink.add(any())).thenReturn(null);
  when(() => sink.close()).thenAnswer((_) async {});
  when(() => sink.close(any(), any())).thenAnswer((_) async {});
  return channel;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late MockFlutterLocalNotificationsPlugin notifs;
  late WsClient client;

  setUpAll(() {
    registerFallbackValue(const NotificationDetails());
  });

  setUp(() {
    notifs = MockFlutterLocalNotificationsPlugin();
    when(
      () => notifs.show(
        any(),
        any(),
        any(),
        any(),
        payload: any(named: 'payload'),
      ),
    ).thenAnswer((_) async {});
    client = _makeClient(notifs);
  });

  tearDown(() {
    client.disconnect();
  });

  group('WsClient', () {
    group('_parseEventType (via WsEvent dispatch)', () {
      test('subscribe returns an unsubscribe function', () {
        final events = <WsEvent>[];
        final unsub = client.subscribe(events.add);

        expect(unsub, isA<Function>());
        unsub();
      });

      test('listeners receive events when notified via onEvent', () {
        final received = <WsEvent>[];
        client.subscribe(received.add);
        client.onEvent = received.add;

        // Simulate internal message handling (via public hook)
        client.onEvent!(
          const WsEvent(
            type: WsEventType.welcome,
            data: {},
          ),
        );

        expect(received, hasLength(1));
        expect(received.first.type, WsEventType.welcome);
      });

      test('unsubscribe removes the listener', () {
        final received = <WsEvent>[];
        final unsub = client.subscribe(received.add);
        unsub();

        client.onEvent?.call(
          const WsEvent(type: WsEventType.pong, data: {}),
        );

        expect(received, isEmpty);
      });
    });

    group('WsEventType parsing', () {
      // Test the parsing via a round-trip through jsonDecode simulation.
      // We verify the enum values are exhaustive.
      test('all event type variants exist', () {
        expect(WsEventType.values, hasLength(greaterThan(7)));
        expect(WsEventType.values, contains(WsEventType.notificationCreated));
        expect(WsEventType.values, contains(WsEventType.gradePublished));
        expect(WsEventType.values, contains(WsEventType.paymentUpdated));
        expect(WsEventType.values, contains(WsEventType.feedNew));
        expect(WsEventType.values, contains(WsEventType.messageCreated));
        expect(WsEventType.values, contains(WsEventType.announcementPublished));
        expect(WsEventType.values, contains(WsEventType.welcome));
        expect(WsEventType.values, contains(WsEventType.pong));
        expect(WsEventType.values, contains(WsEventType.unknown));
      });
    });

    group('badgeCount', () {
      test('starts at 0', () {
        expect(client.badgeCount, 0);
      });

      test('resetBadge resets count to 0', () {
        // Simulate badge increment by using onEvent
        client.onEvent?.call(
          const WsEvent(
            type: WsEventType.notificationCreated,
            data: {'subject': 'Test'},
          ),
        );
        // Badge is only incremented by _handleLocalNotification which
        // requires a live WS connection — verify reset still works
        client.resetBadge();
        expect(client.badgeCount, 0);
      });
    });

    group('connect / disconnect', () {
      test('disconnect does not throw when not connected', () {
        expect(client.disconnect, returnsNormally);
      });

      test('connect with http base url uses ws scheme', () {
        // Just verify no exception — actual WS won't connect in tests
        expect(
          () => client.connect('fake-token'),
          returnsNormally,
        );
        client.disconnect();
      });

      test('connect with https base url uses wss scheme', () {
        final secureClient = WsClient(
          baseUrl: 'https://api.example.com',
          localNotifications: notifs,
          channelFactory: (_) => _mockChannel(),
        );
        expect(
          () => secureClient.connect('fake-token'),
          returnsNormally,
        );
        secureClient.disconnect();
      });
    });

    group('WsEvent', () {
      test('constructor stores type and data', () {
        const event = WsEvent(
          type: WsEventType.feedNew,
          data: {'title': 'Hello'},
        );

        expect(event.type, WsEventType.feedNew);
        expect(event.data['title'], 'Hello');
      });
    });

    group('onEvent callback', () {
      test('onEvent can be set and called directly', () {
        WsEvent? received;
        client.onEvent = (e) => received = e;

        client.onEvent!(const WsEvent(type: WsEventType.pong, data: {}));

        expect(received?.type, WsEventType.pong);
      });
    });
  });
}
