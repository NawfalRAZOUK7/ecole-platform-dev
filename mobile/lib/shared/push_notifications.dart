/// Push notification service — FCM + APNs with deep-linking and badge.
///
/// Reference: DEC-E2-040 — Push integration enabled
/// DEC-E2-041 — Deep-links from push target authorized screens
/// Phase 5A: Enhanced deep-link routing, badge count, permission flow.

import 'dart:developer' as dev;
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_app_badger/flutter_app_badger.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Background message handler — must be top-level function.
@pragma('vm:entry-point')
Future<void> _firebaseBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  dev.log('BG push: ${message.messageId}', name: 'PushNotifications');
}

/// Deep-link data extracted from a push notification.
class PushDeepLink {
  final String route;
  final Map<String, String> params;

  const PushDeepLink({required this.route, this.params = const {}});
}

class PushNotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications;

  /// Route extracted from the latest push notification (deep-link).
  PushDeepLink? _pendingDeepLink;
  int _badgeCount = 0;

  /// Callback invoked when a foreground notification is received.
  void Function(RemoteMessage message)? onForegroundMessage;

  PushNotificationService({
    required FlutterLocalNotificationsPlugin localNotifications,
  }) : _localNotifications = localNotifications;

  PushDeepLink? get pendingDeepLink => _pendingDeepLink;
  int get badgeCount => _badgeCount;

  void clearDeepLink() => _pendingDeepLink = null;

  void resetBadge() {
    _badgeCount = 0;
    FlutterAppBadger.removeBadge();
  }

  /// Initialize push notifications — call after Firebase.initializeApp().
  Future<void> initialize() async {
    // Register background handler
    FirebaseMessaging.onBackgroundMessage(_firebaseBackgroundHandler);

    // Request permissions (iOS + Android 13+)
    final settings = await _requestPermission();
    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      dev.log('Push permission denied', name: 'PushNotifications');
      return;
    }

    // Initialize local notifications for foreground display
    await _initLocalNotifications();

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

  /// Request notification permissions with retry logic.
  Future<NotificationSettings> _requestPermission() async {
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    dev.log(
      'Push permission: ${settings.authorizationStatus}',
      name: 'PushNotifications',
    );

    return settings;
  }

  /// Initialize flutter_local_notifications for foreground display.
  Future<void> _initLocalNotifications() async {
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    await _localNotifications.initialize(
      const InitializationSettings(
        android: androidSettings,
        iOS: iosSettings,
      ),
      onDidReceiveNotificationResponse: (response) {
        // Handle notification tap from local notification
        final payload = response.payload;
        if (payload != null) {
          _pendingDeepLink = PushDeepLink(route: payload);
        }
      },
    );
  }

  void _handleForegroundMessage(RemoteMessage message) {
    dev.log(
      'FG push: ${message.notification?.title}',
      name: 'PushNotifications',
    );

    // Update badge count
    _badgeCount++;
    FlutterAppBadger.updateBadgeCount(_badgeCount);

    // Show local notification
    final notification = message.notification;
    if (notification != null) {
      _localNotifications.show(
        DateTime.now().millisecondsSinceEpoch ~/ 1000,
        notification.title ?? '',
        notification.body ?? '',
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'ecole_push_channel',
            'Notifications',
            channelDescription: 'Notifications push École Platform',
            importance: Importance.high,
            priority: Priority.high,
          ),
          iOS: DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        payload: _extractRoute(message),
      );
    }

    // Invoke external callback
    onForegroundMessage?.call(message);
  }

  void _handleNotificationTap(RemoteMessage message) {
    _extractDeepLink(message);
  }

  /// Extract deep-link route from push notification data.
  /// Expected data format: { "route": "/notifications", "id": "...", "type": "..." }
  void _extractDeepLink(RemoteMessage message) {
    final route = _extractRoute(message);
    if (route != null) {
      final data = message.data;
      final params = <String, String>{};
      if (data['id'] != null) params['id'] = data['id'] as String;
      if (data['type'] != null) params['type'] = data['type'] as String;
      _pendingDeepLink = PushDeepLink(route: route, params: params);
    }
  }

  /// Map notification data to the correct app route.
  String? _extractRoute(RemoteMessage message) {
    final data = message.data;

    // Direct route from server
    final route = data['route'] as String?;
    if (route != null) return route;

    // Infer route from notification type
    final type = data['type'] as String?;
    switch (type) {
      case 'grade_published':
        return '/results';
      case 'payment_updated':
        return '/invoices';
      case 'feed_new':
        return '/feed';
      case 'notification_created':
        return '/notifications';
      default:
        return null;
    }
  }
}
