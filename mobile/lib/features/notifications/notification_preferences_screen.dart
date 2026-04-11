/// Phase 13 notification preferences screen.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/notification_settings.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class NotificationPreferencesScreen extends ConsumerStatefulWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  ConsumerState<NotificationPreferencesScreen> createState() =>
      _NotificationPreferencesScreenState();
}

class _NotificationPreferencesScreenState
    extends ConsumerState<NotificationPreferencesScreen> {
  bool _loading = true;
  bool _saving = false;
  String? _error;
  String _digestFrequency = 'off';
  List<NotificationPreferenceItem> _preferences = [];
  List<RegisteredDevice> _devices = [];

  static const _categories = <String>[
    'academic',
    'billing',
    'attendance',
    'system',
    'announcement',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(notificationRepositoryProvider);
      final prefs = await repo.getPreferences();
      final devices = await repo.getDevices();
      final digest = await repo.getDigestFrequency();
      setState(() {
        _preferences = prefs;
        _devices = devices;
        _digestFrequency = digest;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final repo = ref.read(notificationRepositoryProvider);
      await repo.updatePreferences(_preferences);
      await repo.updateDigestFrequency(_digestFrequency);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  void _togglePreference(String category, String channel, bool value) {
    setState(() {
      _preferences = _preferences.map((preference) {
        if (preference.category == category && preference.channel == channel) {
          return preference.copyWith(enabled: value);
        }
        return preference;
      }).toList();
    });
  }

  Future<void> _removeDevice(String deviceId) async {
    try {
      await ref.read(notificationRepositoryProvider).removeDevice(deviceId);
      setState(() {
        _devices = _devices.where((device) => device.id != deviceId).toList();
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(t.t('notifications.settingsTitle'))),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final channels = _preferences.map((item) => item.channel).toSet().toList()
      ..sort();

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('notifications.settingsTitle')),
        actions: [
          TextButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(t.t('common.save')),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_error != null) ...[
              Text(_error!, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 12),
            ],
            Text(
              t.t('notifications.preferenceMatrixTitle'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            ..._categories.map((category) {
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _categoryLabel(category, t),
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 8),
                      ...channels.map((channel) {
                        final preference = _preferences.firstWhere(
                          (item) =>
                              item.category == category &&
                              item.channel == channel,
                        );
                        return SwitchListTile(
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          title: Text(_channelLabel(channel, t)),
                          value: preference.enabled,
                          onChanged: (value) =>
                              _togglePreference(category, channel, value),
                        );
                      }),
                    ],
                  ),
                ),
              );
            }),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _digestFrequency,
              decoration: InputDecoration(
                labelText: t.t('notifications.digestTitle'),
              ),
              items: [
                DropdownMenuItem(
                  value: 'off',
                  child: Text(t.t('notifications.digestOff')),
                ),
                DropdownMenuItem(
                  value: 'daily',
                  child: Text(t.t('notifications.digestDaily')),
                ),
                DropdownMenuItem(
                  value: 'weekly',
                  child: Text(t.t('notifications.digestWeekly')),
                ),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() => _digestFrequency = value);
                }
              },
            ),
            const SizedBox(height: 24),
            Text(
              t.t('notifications.devicesTitle'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (_devices.isEmpty)
              Text(t.t('notifications.noDevices'))
            else
              ..._devices.map((device) {
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    title: Text(device.deviceName ??
                        t.t('notifications.unknownDevice')),
                    subtitle: Text(
                      '${_platformLabel(device.platform, t)}\n'
                      '${device.tokenPreview}\n'
                      '${t.t('notifications.lastSeen')}: ${_formatDate(device.lastActiveAt)}',
                    ),
                    isThreeLine: true,
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline),
                      onPressed: () => _removeDevice(device.id),
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  String _categoryLabel(String category, AppLocalizations t) {
    switch (category) {
      case 'academic':
        return t.t('notifications.categoryAcademic');
      case 'billing':
        return t.t('notifications.categoryBilling');
      case 'attendance':
        return t.t('notifications.categoryAttendance');
      case 'system':
        return t.t('notifications.categorySystem');
      case 'announcement':
        return t.t('notifications.categoryAnnouncement');
      default:
        return category;
    }
  }

  String _channelLabel(String channel, AppLocalizations t) {
    switch (channel) {
      case 'in_app':
        return t.t('notifications.channelInApp');
      case 'push':
        return t.t('notifications.channelPush');
      case 'email':
        return t.t('notifications.channelEmail');
      case 'sms':
        return t.t('notifications.channelSms');
      default:
        return channel;
    }
  }

  String _platformLabel(String platform, AppLocalizations t) {
    switch (platform) {
      case 'android':
        return t.t('notifications.platformAndroid');
      case 'ios':
        return t.t('notifications.platformIos');
      default:
        return t.t('notifications.platformWeb');
    }
  }

  String _formatDate(String input) {
    try {
      return DateFormat.yMMMd().add_Hm().format(DateTime.parse(input));
    } catch (_) {
      return input;
    }
  }
}
