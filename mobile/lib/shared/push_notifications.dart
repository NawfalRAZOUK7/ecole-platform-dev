/// Push notification service — FCM + APNs with deep-linking.
///
/// Reference: DEC-E2-040 — Push integration enabled
/// DEC-E2-041 — Deep-links from push target authorized screens
/// Mode: both (push + in-app)

import 'dart:developer' as dev;
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

/// Background message handler — must be top-level function.
@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  dev.log('BG push: ${message.messageId}', name: 'PushNotifications');
}

class PushNotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  /// Route name extracted from the latest push notification (deep-link).
  String? _pendingDeepLink;

  String? get pendingDeepLink => _pendingDeepLink;
  void clearDeepLink() => _pendingDeepLink = null;

  /// Initialize push notifications.
  Future<void> initialize() async {
    // Register background handler
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);

    // Request permissions (iOS)
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    dev.log(
      'Push permission: ${settings.authorizationStatus}',
      name: 'PushNotifications',
    );

    // Get FCM token
    final token = await _messaging.getToken();
    dev.log('FCM token: $token', name: 'PushNotifications');

    // Listen for token refresh
    _messaging.onTokenRefresh.listen((newToken) {
      dev.log('FCM token refreshed: $newToken', name: 'PushNotifications');
      // TODO: Send new token to backend when endpoint is available
    });

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle notification taps (app was in background)
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);

    // Check if app was opened from a terminated state via notification
    final initialMessage = await _messaging.getInitialMessage();
    if (initialMessage != null) {
      _extractDeepLink(initialMessage);
    }
  }

  void _handleForegroundMessage(RemoteMessage message) {
    dev.log(
      'FG push: ${message.notification?.title}',
      name: 'PushNotifications',
    );
    // In-app notification will be handled by the notification list screen
  }

  void _handleNotificationTap(RemoteMessage message) {
    _extractDeepLink(message);
  }

  /// Extract deep-link route from push notification data.
  void _extractDeepLink(RemoteMessage message) {
    final data = message.data;
    // Expected data format: { "route": "/notifications", "id": "..." }
    final route = data['route'] as String?;
    if (route != null) {
      _pendingDeepLink = route;
    }
  }
}
