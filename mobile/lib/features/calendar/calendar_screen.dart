import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/calendar_event.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/calendar/event_detail_screen.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

const _eventTypes = [
  'holiday',
  'exam',
  'meeting',
  'excursion',
  'ceremony',
  'custom'
];

class CalendarScreen extends ConsumerStatefulWidget {
  const CalendarScreen({super.key});

  @override
  ConsumerState<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends ConsumerState<CalendarScreen> {
  bool _loading = true;
  String? _error;
  CalendarOptions _options = const CalendarOptions();
  List<CalendarEvent> _events = [];
  DateTime _focusedDay = DateTime.now();
  DateTime _selectedDay = DateTime.now();
  String _selectedClassId = '';
  final Set<String> _selectedTypes = {..._eventTypes};

  bool get _canCreate =>
      ['ADM', 'DIR', 'TCH'].contains(ref.read(authProvider).user?.role ?? '');

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadForMonth(_focusedDay);
    });
  }

  Future<void> _loadForMonth(DateTime day, {bool refresh = false}) async {
    final from = DateTime(day.year, day.month, 1);
    final to = DateTime(day.year, day.month + 1, 0);

    setState(() {
      _loading = !refresh;
      _error = null;
    });

    try {
      final repository = ref.read(calendarRepositoryProvider);
      final results = await Future.wait([
        repository.getCalendarOptions(),
        repository.getEvents(
          fromDate: DateFormat('yyyy-MM-dd').format(from),
          toDate: DateFormat('yyyy-MM-dd').format(to),
          classId: _selectedClassId.isEmpty ? null : _selectedClassId,
        ),
      ]);
      if (!mounted) return;
      final options = results[0] as CalendarOptions;
      setState(() {
        _options = options;
        _events = (results[1] as List<CalendarEvent>)
            .where((event) => _selectedTypes.contains(event.type))
            .toList();
        _selectedClassId =
            _selectedClassId.isEmpty && options.classes.isNotEmpty
                ? _selectedClassId
                : _selectedClassId;
        _focusedDay = day;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  List<CalendarEvent> _eventsForDay(DateTime day) {
    final dayStart = DateTime(day.year, day.month, day.day);
    final dayEnd = dayStart
        .add(const Duration(days: 1))
        .subtract(const Duration(milliseconds: 1));
    return _events.where((event) {
      final start = DateTime.parse(event.startAt).toLocal();
      final end = DateTime.parse(event.endAt).toLocal();
      return !start.isAfter(dayEnd) && !end.isBefore(dayStart);
    }).toList();
  }

  Future<void> _openEvent(CalendarEvent event) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) => FractionallySizedBox(
        heightFactor: 0.88,
        child: EventDetailSheet(
          eventId: event.source == 'event' ? event.id : null,
          initialEvent: event,
        ),
      ),
    );
    await _loadForMonth(_focusedDay, refresh: true);
  }

  Future<void> _createEvent() async {
    final created = await context.push<CalendarEvent?>('/events/create');
    if (created != null) {
      await _loadForMonth(_focusedDay, refresh: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final dayEvents = _eventsForDay(_selectedDay);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('calendar.title')),
        actions: [
          if (_canCreate)
            IconButton(
              icon: const Icon(Icons.add_circle_outline),
              onPressed: _createEvent,
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () => _loadForMonth(_focusedDay, refresh: true),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_error != null) ...[
                    Card(
                      color: Colors.red.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(
                          _error!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _eventTypes
                        .map(
                          (type) => FilterChip(
                            label: Text(t.t('calendar.types.$type')),
                            selected: _selectedTypes.contains(type),
                            onSelected: (selected) {
                              setState(() {
                                if (selected) {
                                  _selectedTypes.add(type);
                                } else {
                                  _selectedTypes.remove(type);
                                }
                              });
                              _loadForMonth(_focusedDay, refresh: true);
                            },
                          ),
                        )
                        .toList(),
                  ),
                  if (_options.classes.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      key: ValueKey(_selectedClassId),
                      initialValue:
                          _selectedClassId.isEmpty ? '' : _selectedClassId,
                      decoration: InputDecoration(
                          labelText: t.t('calendar.fields.class')),
                      items: [
                        DropdownMenuItem<String>(
                          value: '',
                          child: Text(t.t('calendar.classAll')),
                        ),
                        ..._options.classes.map(
                          (item) => DropdownMenuItem<String>(
                            value: item.id,
                            child: Text(item.label),
                          ),
                        ),
                      ],
                      onChanged: (value) {
                        setState(() => _selectedClassId = value ?? '');
                        _loadForMonth(_focusedDay, refresh: true);
                      },
                    ),
                  ],
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: TableCalendar<CalendarEvent>(
                        firstDay: DateTime.utc(2020, 1, 1),
                        lastDay: DateTime.utc(2100, 12, 31),
                        focusedDay: _focusedDay,
                        selectedDayPredicate: (day) =>
                            isSameDay(day, _selectedDay),
                        calendarFormat: CalendarFormat.month,
                        eventLoader: _eventsForDay,
                        startingDayOfWeek: StartingDayOfWeek.monday,
                        onDaySelected: (selectedDay, focusedDay) {
                          setState(() {
                            _selectedDay = selectedDay;
                            _focusedDay = focusedDay;
                          });
                        },
                        onPageChanged: (focusedDay) {
                          _focusedDay = focusedDay;
                          _loadForMonth(focusedDay, refresh: true);
                        },
                        calendarBuilders: CalendarBuilders(
                          markerBuilder: (context, day, events) {
                            if (events.isEmpty) return const SizedBox.shrink();
                            return Align(
                              alignment: Alignment.bottomCenter,
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: events.take(3).map((event) {
                                  return Container(
                                    width: 6,
                                    height: 6,
                                    margin: const EdgeInsets.symmetric(
                                        horizontal: 1),
                                    decoration: BoxDecoration(
                                      color: _eventColor(event.type),
                                      shape: BoxShape.circle,
                                    ),
                                  );
                                }).toList(),
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    t.t('calendar.dayEvents'),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  if (dayEvents.isEmpty)
                    Center(child: Text(t.t('calendar.noDayEvents')))
                  else
                    ...dayEvents.map(
                      (event) => Card(
                        child: ListTile(
                          onTap: () => _openEvent(event),
                          leading: CircleAvatar(
                            backgroundColor:
                                _eventColor(event.type).withValues(alpha: 0.18),
                            child: Icon(
                              Icons.event_note_outlined,
                              color: _eventColor(event.type),
                            ),
                          ),
                          title: Text(_localizedTitle(event)),
                          subtitle: Text(
                            event.isAllDay
                                ? t.t('calendar.allDay')
                                : DateFormat.Hm().format(
                                    DateTime.parse(event.startAt).toLocal(),
                                  ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
    );
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

  Color _eventColor(String type) {
    switch (type) {
      case 'holiday':
        return Colors.red;
      case 'exam':
        return Colors.orange;
      case 'meeting':
        return Colors.blue;
      case 'excursion':
        return Colors.teal;
      case 'ceremony':
        return Colors.pink;
      default:
        return Colors.green;
    }
  }
}
