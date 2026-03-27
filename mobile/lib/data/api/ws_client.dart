/// WebSocket client — connect on login, reconnect with backoff, local notifications.
///
/// Reference: Phase 5A (from 3C) — WebSocket real-time notifications
/// Connects to GET /ws?token={access_token}, receives real-time events.
/// Shows local notification on WS event, updates badge count.

import 'dart:async';
import 'dart:convert';
import 'dart:developer' as dev;
import 'dart:math';

import 'package:flutter_app_badger/flutter_app_badger.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// Event types from the backend WebSocket.
enum WsEventType {
  notificationCreated,
  gradePublished,
  paymentUpdated,
  feedNew,
  messageCreated,
  announcementPublished,
  welcome,
  pong,
  unknown,
}

WsEventType _parseEventType(String type) {
  switch (type) {
    case 'notification_created':
      return WsEventType.notificationCreated;
    case 'grade_published':
      return WsEventType.gradePublished;
    case 'payment_updated':
      return WsEventType.paymentUpdated;
    case 'feed_new':
      return WsEventType.feedNew;
    case 'message_created':
      return WsEventType.messageCreated;
    case 'announcement_published':
      return WsEventType.announcementPublished;
    case 'welcome':
      return WsEventType.welcome;
    case 'pong':
      return WsEventType.pong;
    default:
      return WsEventType.unknown;
  }
}

class WsEvent {
  final WsEventType type;
  final Map<String, dynamic> data;

  const WsEvent({required this.type, required this.data});
}

typedef WsListener = void Function(WsEvent event);

class WsClient {
  final String _baseUrl;
  final FlutterLocalNotificationsPlugin _localNotifications;

  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  final Set<WsListener> _listeners = {};
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;
  int _reconnectAttempt = 0;
  bool _shouldConnect = false;
  String? _accessToken;
  int _badgeCount = 0;

  static const _maxReconnectDelay = 30000;
  static const _initialReconnectDelay = 1000;
  static const _heartbeatInterval = Duration(seconds: 25);

  WsClient({
    required String baseUrl,
    required FlutterLocalNotificationsPlugin localNotifications,
  })  : _baseUrl = baseUrl,
        _localNotifications = localNotifications;

  int get badgeCount => _badgeCount;

  /// Subscribe to WS events. Returns unsubscribe function.
  VoidCallback subscribe(WsListener listener) {
    _listeners.add(listener);
    return () => _listeners.remove(listener);
  }

  /// Connect to WebSocket (called after login).
  void connect(String accessToken) {
    _accessToken = accessToken;
    _shouldConnect = true;
    _reconnectAttempt = 0;
    _doConnect();
  }

  /// Disconnect (called on logout).
  void disconnect() {
    _shouldConnect = false;
    _cleanup();
  }

  /// Reset badge count (e.g. when notifications screen is viewed).
  void resetBadge() {
    _badgeCount = 0;
    FlutterAppBadger.removeBadge();
  }

  void _doConnect() {
    if (!_shouldConnect || _accessToken == null) return;

    final wsScheme = _baseUrl.startsWith('https') ? 'wss' : 'ws';
    final host = _baseUrl
        .replaceFirst('http://', '')
        .replaceFirst('https://', '');
    final uri = Uri.parse('$wsScheme://$host/api/v1/ws?token=$_accessToken');

    try {
      _channel = WebSocketChannel.connect(uri);
      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
      );
      _startHeartbeat();
      _reconnectAttempt = 0;
      dev.log('WS connected', name: 'WsClient');
    } catch (e) {
      dev.log('WS connect error: $e', name: 'WsClient');
      _scheduleReconnect();
    }
  }

  void _onMessage(dynamic raw) {
    try {
      final json = jsonDecode(raw as String) as Map<String, dynamic>;
      final eventStr = json['event'] as String? ?? '';

      // Respond to server pings
      if (eventStr == 'ping') {
        _channel?.sink.add(jsonEncode({'event': 'pong'}));
        return;
      }

      final event = WsEvent(
        type: _parseEventType(eventStr),
        data: json['data'] as Map<String, dynamic>? ?? {},
      );

      // Notify listeners
      for (final listener in _listeners) {
        listener(event);
      }

      // Show local notification for important events
      _handleLocalNotification(event);
    } catch (e) {
      dev.log('WS message parse error: $e', name: 'WsClient');
    }
  }

  void _handleLocalNotification(WsEvent event) {
    String? title;
    String? body;

    switch (event.type) {
      case WsEventType.notificationCreated:
        title = 'Nouvelle notification';
        body = event.data['subject'] as String? ?? 'Vous avez une nouvelle notification';
        break;
      case WsEventType.gradePublished:
        title = 'Note publiée';
        body = 'Une nouvelle note a été publiée';
        break;
      case WsEventType.paymentUpdated:
        title = 'Paiement mis à jour';
        body = 'Le statut d\'un paiement a changé';
        break;
      case WsEventType.feedNew:
        title = 'Nouvelle actualité';
        body = event.data['title'] as String? ?? 'Une nouvelle actualité est disponible';
        break;
      case WsEventType.messageCreated:
        title = 'Nouveau message';
        body = event.data['body'] as String? ?? 'Vous avez un nouveau message';
        break;
      case WsEventType.announcementPublished:
        title = 'Nouvelle annonce';
        body = event.data['title'] as String? ?? 'Une nouvelle annonce a été publiée';
        break;
      default:
        return; // Don't show notification for welcome, pong, unknown
    }

    // Update badge count
    _badgeCount++;
    FlutterAppBadger.updateBadgeCount(_badgeCount);

    // Show local notification
    _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'ecole_ws_channel',
          'Notifications en temps réel',
          channelDescription: 'Notifications reçues via WebSocket',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
    );
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(_heartbeatInterval, (_) {
      _channel?.sink.add(jsonEncode({'event': 'pong'}));
    });
  }

  void _scheduleReconnect() {
    if (!_shouldConnect) return;
    _cleanup(keepShouldConnect: true);

    final delay = min(
      _initialReconnectDelay * pow(2, _reconnectAttempt).toInt(),
      _maxReconnectDelay,
    );
    _reconnectAttempt++;

    dev.log('WS reconnecting in ${delay}ms (attempt $_reconnectAttempt)',
        name: 'WsClient');
    _reconnectTimer = Timer(Duration(milliseconds: delay), _doConnect);
  }

  void _cleanup({bool keepShouldConnect = false}) {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    _subscription?.cancel();
    _subscription = null;
    try {
      _channel?.sink.close();
    } catch (_) {}
    _channel = null;
    if (!keepShouldConnect) _shouldConnect = false;
  }
}
