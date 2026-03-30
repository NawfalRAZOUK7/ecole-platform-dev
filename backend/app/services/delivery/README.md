# Notification Delivery Channels

Strategy pattern implementation for multi-channel notification delivery.

## Files

- **base.py** — Abstract `DeliveryChannel` base class
- **email_delivery.py** — Email delivery via SMTP/SendGrid
- **sms_delivery.py** — SMS delivery via provider API
- **push.py** — Push notification delivery (FCM/APNs)
- **in_app.py** — In-app notification storage and WebSocket broadcast

## Usage

The `NotificationHub` service selects delivery channels based on user preferences and notification type. Multiple channels can fire in parallel for a single notification.
