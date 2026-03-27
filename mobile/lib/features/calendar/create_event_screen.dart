import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/calendar_event.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

const _roleOptions = ['ADM', 'DIR', 'TCH', 'PAR', 'STD'];
const _typeOptions = [
  'holiday',
  'exam',
  'meeting',
  'excursion',
  'ceremony',
  'custom'
];

class CreateEventScreen extends ConsumerStatefulWidget {
  final CalendarEvent? initialEvent;

  const CreateEventScreen({
    super.key,
    this.initialEvent,
  });

  @override
  ConsumerState<CreateEventScreen> createState() => _CreateEventScreenState();
}

class _CreateEventScreenState extends ConsumerState<CreateEventScreen> {
  final _titleFrController = TextEditingController();
  final _titleArController = TextEditingController();
  final _titleEnController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _locationController = TextEditingController();
  final _capacityController = TextEditingController();

  CalendarOptions _options = const CalendarOptions();
  String _type = 'meeting';
  String _visibility = 'school';
  String _classId = '';
  final Set<String> _roleCodes = {};
  String _recurrenceFrequency = '';
  DateTime _startAt = DateTime.now().add(const Duration(hours: 1));
  DateTime _endAt = DateTime.now().add(const Duration(hours: 2));
  DateTime? _recurrenceUntil;
  bool _isAllDay = false;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  bool get _isTeacher => (ref.read(authProvider).user?.role ?? '') == 'TCH';
  bool get _isEditing => widget.initialEvent != null;

  @override
  void initState() {
    super.initState();
    _hydrateInitial();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadOptions();
    });
  }

  @override
  void dispose() {
    _titleFrController.dispose();
    _titleArController.dispose();
    _titleEnController.dispose();
    _descriptionController.dispose();
    _locationController.dispose();
    _capacityController.dispose();
    super.dispose();
  }

  void _hydrateInitial() {
    final event = widget.initialEvent;
    if (event == null) return;
    _titleFrController.text = event.titleFr;
    _titleArController.text = event.titleAr ?? '';
    _titleEnController.text = event.titleEn ?? '';
    _descriptionController.text = event.description ?? '';
    _locationController.text = event.location ?? '';
    _capacityController.text = event.capacity?.toString() ?? '';
    _type = event.type;
    _visibility = event.visibility;
    _classId = event.classId ?? '';
    _roleCodes.addAll(event.roleCodes);
    _startAt = DateTime.parse(event.startAt).toLocal();
    _endAt = DateTime.parse(event.endAt).toLocal();
    _isAllDay = event.isAllDay;
    _recurrenceFrequency = event.recurrenceRule?['frequency'] as String? ?? '';
    final until = event.recurrenceRule?['until'] as String?;
    _recurrenceUntil =
        until != null ? DateTime.tryParse(until)?.toLocal() : null;
  }

  Future<void> _loadOptions() async {
    try {
      final options =
          await ref.read(calendarRepositoryProvider).getCalendarOptions();
      if (!mounted) return;
      setState(() {
        _options = options;
        _classId = _classId.isEmpty && options.classes.isNotEmpty
            ? options.classes.first.id
            : _classId;
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

  Future<void> _pickDateTime({required bool start}) async {
    final current = start ? _startAt : _endAt;
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: current,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (pickedDate == null || !mounted) return;

    final pickedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(current),
    );
    if (pickedTime == null || !mounted) return;

    final next = DateTime(
      pickedDate.year,
      pickedDate.month,
      pickedDate.day,
      pickedTime.hour,
      pickedTime.minute,
    );
    setState(() {
      if (start) {
        _startAt = next;
        if (_endAt.isBefore(next)) {
          _endAt = next.add(const Duration(hours: 1));
        }
      } else {
        _endAt = next;
      }
    });
  }

  Future<void> _pickRecurrenceUntil() async {
    final current = _recurrenceUntil ?? _startAt.add(const Duration(days: 30));
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: current,
      firstDate: _startAt,
      lastDate: DateTime(2100),
    );
    if (pickedDate == null || !mounted) return;
    setState(() => _recurrenceUntil = pickedDate);
  }

  Future<void> _submit() async {
    if (_titleFrController.text.trim().isEmpty) {
      setState(() => _error = 'Missing title');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    final payload = {
      'title_fr': _titleFrController.text.trim(),
      if (_titleArController.text.trim().isNotEmpty)
        'title_ar': _titleArController.text.trim(),
      if (_titleEnController.text.trim().isNotEmpty)
        'title_en': _titleEnController.text.trim(),
      if (_descriptionController.text.trim().isNotEmpty)
        'description': _descriptionController.text.trim(),
      'type': _type,
      'visibility': _isTeacher ? 'class' : _visibility,
      'start_at': _startAt.toUtc().toIso8601String(),
      'end_at': _endAt.toUtc().toIso8601String(),
      if (_locationController.text.trim().isNotEmpty)
        'location': _locationController.text.trim(),
      if (_capacityController.text.trim().isNotEmpty)
        'capacity': int.tryParse(_capacityController.text.trim()),
      if ((_isTeacher || _visibility == 'class') && _classId.isNotEmpty)
        'class_id': _classId,
      if (_visibility == 'role') 'role_codes': _roleCodes.toList(),
      'is_all_day': _isAllDay,
      if (_recurrenceFrequency.isNotEmpty)
        'recurrence_rule': {
          'frequency': _recurrenceFrequency,
          'interval': 1,
          if (_recurrenceUntil != null)
            'until': _recurrenceUntil!.toUtc().toIso8601String(),
        },
      'reminder_offsets_minutes': const [1440, 60],
    };

    try {
      final repository = ref.read(calendarRepositoryProvider);
      final event = _isEditing
          ? await repository.updateEvent(widget.initialEvent!.id, payload)
          : await repository.createEvent(payload);
      if (!mounted) return;
      context.pop(event);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(
          t.t(_isEditing ? 'calendar.editTitle' : 'calendar.createTitle'),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            Card(
              color: Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            ),
            const SizedBox(height: 12),
          ],
          TextField(
            controller: _titleFrController,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.titleFr')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _titleArController,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.titleAr')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _titleEnController,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.titleEn')),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            key: ValueKey(_type),
            initialValue: _type,
            decoration: InputDecoration(labelText: t.t('calendar.fields.type')),
            items: _typeOptions
                .map((item) => DropdownMenuItem(
                      value: item,
                      child: Text(t.t('calendar.types.$item')),
                    ))
                .toList(),
            onChanged: (value) => setState(() => _type = value ?? _type),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            key: ValueKey(_isTeacher ? 'class' : _visibility),
            initialValue: _isTeacher ? 'class' : _visibility,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.visibility')),
            items: const ['school', 'class', 'role']
                .map((item) => DropdownMenuItem(
                      value: item,
                      child: Text(item),
                    ))
                .toList(),
            onChanged: _isTeacher
                ? null
                : (value) => setState(() => _visibility = value ?? _visibility),
          ),
          const SizedBox(height: 12),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(t.t('calendar.fields.start')),
            subtitle: Text(_startAt.toString()),
            trailing: const Icon(Icons.schedule_outlined),
            onTap: () => _pickDateTime(start: true),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(t.t('calendar.fields.end')),
            subtitle: Text(_endAt.toString()),
            trailing: const Icon(Icons.schedule_outlined),
            onTap: () => _pickDateTime(start: false),
          ),
          TextField(
            controller: _locationController,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.location')),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _capacityController,
            keyboardType: TextInputType.number,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.capacity')),
          ),
          const SizedBox(height: 12),
          if (_isTeacher || _visibility == 'class')
            DropdownButtonFormField<String>(
              key: ValueKey(_classId),
              initialValue: _classId.isEmpty && _options.classes.isNotEmpty
                  ? _options.classes.first.id
                  : _classId,
              decoration:
                  InputDecoration(labelText: t.t('calendar.fields.class')),
              items: _options.classes
                  .map((item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(item.label),
                      ))
                  .toList(),
              onChanged: (value) =>
                  setState(() => _classId = value ?? _classId),
            ),
          if (_visibility == 'role') ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _roleOptions
                  .map(
                    (role) => FilterChip(
                      label: Text(role),
                      selected: _roleCodes.contains(role),
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _roleCodes.add(role);
                          } else {
                            _roleCodes.remove(role);
                          }
                        });
                      },
                    ),
                  )
                  .toList(),
            ),
          ],
          const SizedBox(height: 12),
          TextField(
            controller: _descriptionController,
            minLines: 3,
            maxLines: 5,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.description')),
          ),
          const SizedBox(height: 12),
          SwitchListTile(
            value: _isAllDay,
            onChanged: (value) => setState(() => _isAllDay = value),
            title: Text(t.t('calendar.fields.allDay')),
          ),
          DropdownButtonFormField<String>(
            key: ValueKey(_recurrenceFrequency),
            initialValue: _recurrenceFrequency,
            decoration:
                InputDecoration(labelText: t.t('calendar.fields.recurrence')),
            items: const [
              DropdownMenuItem(value: '', child: Text('None')),
              DropdownMenuItem(value: 'weekly', child: Text('Weekly')),
              DropdownMenuItem(value: 'annual', child: Text('Annual')),
            ],
            onChanged: (value) =>
                setState(() => _recurrenceFrequency = value ?? ''),
          ),
          if (_recurrenceFrequency.isNotEmpty)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(t.t('calendar.fields.until')),
              subtitle: Text(
                _recurrenceUntil == null
                    ? '—'
                    : _recurrenceUntil!.toIso8601String(),
              ),
              trailing: const Icon(Icons.event_repeat),
              onTap: _pickRecurrenceUntil,
            ),
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: _saving ? null : _submit,
            icon: const Icon(Icons.save_outlined),
            label: Text(
              _saving
                  ? t.t('calendar.submitting')
                  : t.t(_isEditing ? 'calendar.update' : 'calendar.submit'),
            ),
          ),
        ],
      ),
    );
  }
}
