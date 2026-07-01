/// Notification preferences and registered device entities.

class NotificationPreferenceItem {
  final String channel;
  final String category;
  final bool enabled;
  final String digestFrequency;

  const NotificationPreferenceItem({
    required this.channel,
    required this.category,
    required this.enabled,
    required this.digestFrequency,
  });

  NotificationPreferenceItem copyWith({
    String? channel,
    String? category,
    bool? enabled,
    String? digestFrequency,
  }) {
    return NotificationPreferenceItem(
      channel: channel ?? this.channel,
      category: category ?? this.category,
      enabled: enabled ?? this.enabled,
      digestFrequency: digestFrequency ?? this.digestFrequency,
    );
  }
}

class RegisteredDevice {
  final String id;
  final String platform;
  final String? deviceName;
  final String tokenPreview;
  final String lastActiveAt;

  const RegisteredDevice({
    required this.id,
    required this.platform,
    this.deviceName,
    required this.tokenPreview,
    required this.lastActiveAt,
  });
}
