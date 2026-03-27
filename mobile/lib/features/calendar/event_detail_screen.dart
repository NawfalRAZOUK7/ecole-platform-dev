import 'package:device_calendar/device_calendar.dart' as device_calendar;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/calendar_event.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class EventDetailScreen extends ConsumerWidget {
  final String eventId;

  const EventDetailScreen({
    super.key,
    required this.eventId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('calendar.eventDetailTitle')),
      ),
      body: EventDetailSheet(eventId: eventId),
    );
  }
}

class EventDetailSheet extends ConsumerStatefulWidget {
  final String? eventId;
  final CalendarEvent? initialEvent;
  final bool embedded;

  const EventDetailSheet({
    super.key,
    this.eventId,
    this.initialEvent,
    this.embedded = false,
  });

  @override
  ConsumerState<EventDetailSheet> createState() => _EventDetailSheetState();
}

class _EventDetailSheetState extends ConsumerState<EventDetailSheet> {
  CalendarEvent? _event;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _event = widget.initialEvent;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _load();
    });
  }

  Future<void> _load() async {
    final eventId = widget.eventId ?? widget.initialEvent?.id;
    if (eventId == null) {
      setState(() {
        _loading = false;
        _error = 'Missing event id';
      });
      return;
    }

    if ((widget.initialEvent?.source ?? 'event') != 'event') {
      setState(() {
        _loading = false;
        _event = widget.initialEvent;
      });
      return;
    }

    try {
      final event =
          await ref.read(calendarRepositoryProvider).getEvent(eventId);
      if (!mounted) return;
      setState(() {
        _event = event;
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _respond(String status) async {
    final eventId = _event?.id;
    if (eventId == null) return;
    try {
      final updated = await ref
          .read(calendarRepositoryProvider)
          .respondToEvent(eventId, status);
      if (!mounted) return;
      setState(() => _event = updated);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _share(CalendarEvent event) async {
    final t = AppLocalizations.of(ref);
    final when = _formatRange(event);
    final message = [
      _localizedTitle(event),
      when,
      if (event.location != null && event.location!.isNotEmpty) event.location!,
      if (event.description != null && event.description!.isNotEmpty)
        event.description!,
    ].join('\n');
    await Share.share('${t.t('calendar.shareLabel')}\n$message');
  }

  Future<void> _addToDeviceCalendar(CalendarEvent event) async {
    final t = AppLocalizations.of(ref);
    try {
      final plugin = device_calendar.DeviceCalendarPlugin();
      final permissionResult = await plugin.hasPermissions();
      final hasPermission = permissionResult.data ??
          (await plugin.requestPermissions()).data ??
          false;
      if (!hasPermission) {
        throw Exception(t.t('calendar.deviceCalendarDenied'));
      }

      final calendars = await plugin.retrieveCalendars();
      final targetCalendar = calendars.data?.firstWhere(
        (item) => !(item.isReadOnly ?? false),
        orElse: () => calendars.data!.first,
      );
      if (targetCalendar?.id == null) {
        throw Exception(t.t('calendar.deviceCalendarUnavailable'));
      }

      tzdata.initializeTimeZones();
      final startAt = DateTime.parse(event.startAt).toLocal();
      final endAt = DateTime.parse(event.endAt).toLocal();
      final deviceEvent = device_calendar.Event(
        targetCalendar!.id,
        title: _localizedTitle(event),
        description: event.description,
        location: event.location,
        start: tz.TZDateTime.from(startAt, tz.local),
        end: tz.TZDateTime.from(endAt, tz.local),
        allDay: event.isAllDay,
      );
      await plugin.createOrUpdateEvent(deviceEvent);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t.t('calendar.addedToDeviceCalendar'))),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _editEvent(CalendarEvent event) async {
    final updated =
        await context.push<CalendarEvent?>('/events/create', extra: event);
    if (updated != null) {
      setState(() => _event = updated);
      await _load();
    }
  }

  Future<void> _deleteEvent(CalendarEvent event) async {
    final t = AppLocalizations.of(ref);
    final confirmed = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(t.t('calendar.delete')),
            content: Text(t.t('calendar.confirmDelete')),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: Text(t.t('common.cancel')),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: Text(t.t('calendar.delete')),
              ),
            ],
          ),
        ) ??
        false;
    if (!confirmed) return;

    try {
      await ref.read(calendarRepositoryProvider).deleteEvent(event.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t.t('calendar.deleted'))),
      );
      if (widget.embedded || !Navigator.of(context).canPop()) {
        context.go('/calendar');
      } else {
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  String _localizedTitle(CalendarEvent event) {
    final locale = ref.read(localeProvider);
    if (locale == 'ar' && event.titleAr != null && event.titleAr!.isNotEmpty) {
      return event.titleAr!;
    }
    if (locale == 'en' && event.titleEn != null && event.titleEn!.isNotEmpty) {
      return event.titleEn!;
    }
    return event.titleFr;
  }

  String _formatRange(CalendarEvent event) {
    final start = DateTime.parse(event.startAt).toLocal();
    final end = DateTime.parse(event.endAt).toLocal();
    if (event.isAllDay) {
      return DateFormat.yMMMMEEEEd(ref.read(localeProvider)).format(start);
    }
    final sameDay = start.year == end.year &&
        start.month == end.month &&
        start.day == end.day;
    if (sameDay) {
      return '${DateFormat.yMMMMEEEEd(ref.read(localeProvider)).format(start)} • ${DateFormat.Hm(ref.read(localeProvider)).format(start)} - ${DateFormat.Hm(ref.read(localeProvider)).format(end)}';
    }
    return '${DateFormat.yMMMd(ref.read(localeProvider)).add_Hm().format(start)} → ${DateFormat.yMMMd(ref.read(localeProvider)).add_Hm().format(end)}';
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final event = _event;

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(child: Text(_error!));
    }

    if (event == null) {
      return Center(child: Text(t.t('calendar.empty')));
    }

    final content = ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            Chip(label: Text(t.t('calendar.types.${event.type}'))),
            if (event.isRecurring) Chip(label: Text(t.t('calendar.recurring'))),
            if (event.isAllDay) Chip(label: Text(t.t('calendar.allDay'))),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          _localizedTitle(event),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        Text(
          _formatRange(event),
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        if (event.location != null && event.location!.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(event.location!),
        ],
        if (event.description != null && event.description!.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(event.description!),
        ],
        const SizedBox(height: 20),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ActionChip(
              label: Text(t.t('calendar.rsvp.attending')),
              onPressed: event.canRsvp ? () => _respond('attending') : null,
            ),
            ActionChip(
              label: Text(t.t('calendar.rsvp.maybe')),
              onPressed: event.canRsvp ? () => _respond('maybe') : null,
            ),
            ActionChip(
              label: Text(t.t('calendar.rsvp.declined')),
              onPressed: event.canRsvp ? () => _respond('declined') : null,
            ),
          ],
        ),
        const SizedBox(height: 16),
        Text(
          '${t.t('calendar.attendees')}: ${event.attendeeCount} · ${event.maybeCount} · ${event.declinedCount}',
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            OutlinedButton.icon(
              onPressed: () => _share(event),
              icon: const Icon(Icons.share_outlined),
              label: Text(t.t('calendar.share')),
            ),
            OutlinedButton.icon(
              onPressed: () => _addToDeviceCalendar(event),
              icon: const Icon(Icons.event_available_outlined),
              label: Text(t.t('calendar.addToDeviceCalendar')),
            ),
            if (event.canEdit)
              OutlinedButton.icon(
                onPressed: () => _editEvent(event),
                icon: const Icon(Icons.edit_outlined),
                label: Text(t.t('calendar.editTitle')),
              ),
            if (event.canDelete)
              OutlinedButton.icon(
                onPressed: () => _deleteEvent(event),
                icon: const Icon(Icons.delete_outline),
                label: Text(t.t('calendar.delete')),
              ),
          ],
        ),
        if (event.rsvps.isNotEmpty) ...[
          const SizedBox(height: 24),
          Text(
            t.t('calendar.attendees'),
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          ...event.rsvps.map(
            (item) => ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(item.fullName),
              subtitle: Text(item.role),
              trailing: Text(t.t('calendar.rsvp.${item.status}')),
            ),
          ),
        ],
      ],
    );

    if (widget.embedded) {
      return content;
    }
    return SafeArea(child: content);
  }
}
