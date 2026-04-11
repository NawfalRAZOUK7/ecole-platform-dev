/// Attendance marking screen — mark attendance per class session.
///
/// Reference: Phase 5B (from 4B)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

const _slots = ['slot_1', 'slot_2', 'slot_3', 'slot_4', 'slot_5', 'slot_6'];
const _slotLabels = {
  'slot_1': 'Créneau 1',
  'slot_2': 'Créneau 2',
  'slot_3': 'Créneau 3',
  'slot_4': 'Créneau 4',
  'slot_5': 'Créneau 5',
  'slot_6': 'Créneau 6',
};

const _statusOptions = [
  ('present', 'Présent'),
  ('absent', 'Absent'),
  ('late', 'Retard'),
  ('excused', 'Excusé'),
];

class AttendanceScreen extends ConsumerStatefulWidget {
  const AttendanceScreen({super.key});

  @override
  ConsumerState<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends ConsumerState<AttendanceScreen> {
  List<ClassInfo> _classes = [];
  List<Period> _periods = [];
  List<StudentInfo> _students = [];

  String? _selectedClassId;
  String? _selectedPeriodId;
  DateTime _sessionDate = DateTime.now();
  String _selectedSlot = 'slot_1';

  List<AttendanceRecord> _records = [];
  bool _loadingInit = true;
  bool _loadingStudents = false;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadInitData();
  }

  Future<void> _loadInitData() async {
    try {
      final repo = ref.read(teacherRepositoryProvider);
      final classes = await repo.getClasses();
      final periods = await repo.getPeriods();
      setState(() {
        _classes = classes;
        _periods = periods;
        _loadingInit = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loadingInit = false;
      });
    }
  }

  Future<void> _loadStudents(String classId) async {
    setState(() {
      _loadingStudents = true;
      _error = null;
    });
    try {
      final repo = ref.read(teacherRepositoryProvider);
      final students = await repo.getClassStudents(classId);
      setState(() {
        _students = students;
        _records =
            students.map((s) => AttendanceRecord(studentId: s.id)).toList();
        _loadingStudents = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loadingStudents = false;
      });
    }
  }

  Future<void> _submit() async {
    if (_selectedClassId == null || _selectedPeriodId == null) {
      setState(
          () => _error = 'Veuillez sélectionner une classe et une période');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final repo = ref.read(teacherRepositoryProvider);
      await repo.createAttendanceSession(
        classId: _selectedClassId!,
        periodId: _selectedPeriodId!,
        sessionDate: DateFormat('yyyy-MM-dd').format(_sessionDate),
        slot: _selectedSlot,
        records: _records,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Présences enregistrées avec succès'),
            backgroundColor: Theme.of(context).semanticPalette.success,
          ),
        );
        // Reset student statuses
        setState(() {
          _records =
              _students.map((s) => AttendanceRecord(studentId: s.id)).toList();
        });
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _pickDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _sessionDate,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now(),
    );
    if (date != null) setState(() => _sessionDate = date);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Présences')),
      body: Semantics(
        container: true,
        label: 'Écran de gestion des présences',
        child: _loadingInit
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Error
                  if (_error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.errorContainer,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(_error!,
                          style: TextStyle(
                              color: theme.colorScheme.onErrorContainer)),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Session setup
                  Semantics(
                    label: 'Configuration de la session de cours',
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Session de cours',
                                style: theme.textTheme.titleMedium
                                    ?.copyWith(fontWeight: FontWeight.bold)),
                            const SizedBox(height: 12),
                            DropdownButtonFormField<String>(
                              initialValue: _selectedClassId,
                              decoration: const InputDecoration(
                                labelText: 'Classe *',
                                border: OutlineInputBorder(),
                              ),
                              items: _classes
                                  .map((c) => DropdownMenuItem(
                                        value: c.id,
                                        child: Text(c.name),
                                      ))
                                  .toList(),
                              onChanged: (v) {
                                setState(() => _selectedClassId = v);
                                if (v != null) _loadStudents(v);
                              },
                            ),
                            const SizedBox(height: 12),
                            DropdownButtonFormField<String>(
                              initialValue: _selectedPeriodId,
                              decoration: const InputDecoration(
                                labelText: 'Période *',
                                border: OutlineInputBorder(),
                              ),
                              items: _periods
                                  .map((p) => DropdownMenuItem(
                                        value: p.id,
                                        child: Text(p.name),
                                      ))
                                  .toList(),
                              onChanged: (v) =>
                                  setState(() => _selectedPeriodId = v),
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Expanded(
                                  child: Semantics(
                                    button: true,
                                    label: 'Choisir la date de la session',
                                    child: InkWell(
                                      onTap: _pickDate,
                                      child: InputDecorator(
                                        decoration: const InputDecoration(
                                          labelText: 'Date',
                                          border: OutlineInputBorder(),
                                          suffixIcon:
                                              Icon(Icons.calendar_today),
                                        ),
                                        child: Text(
                                          DateFormat.yMMMd('fr')
                                              .format(_sessionDate),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: DropdownButtonFormField<String>(
                                    initialValue: _selectedSlot,
                                    decoration: const InputDecoration(
                                      labelText: 'Créneau',
                                      border: OutlineInputBorder(),
                                    ),
                                    items: _slots
                                        .map((s) => DropdownMenuItem(
                                              value: s,
                                              child: Text(_slotLabels[s] ?? s),
                                            ))
                                        .toList(),
                                    onChanged: (v) {
                                      if (v != null) {
                                        setState(() => _selectedSlot = v);
                                      }
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Student list
                  if (_loadingStudents)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(32),
                        child: CircularProgressIndicator(),
                      ),
                    )
                  else if (_students.isNotEmpty) ...[
                    Row(
                      children: [
                        Text('Élèves (${_students.length})',
                            style: theme.textTheme.titleSmall
                                ?.copyWith(fontWeight: FontWeight.w600)),
                        const Spacer(),
                        // Quick actions
                        Semantics(
                          button: true,
                          label: 'Marquer tous les élèves présents',
                          child: TextButton(
                            onPressed: () {
                              setState(() {
                                for (final r in _records) {
                                  r.status = 'present';
                                  r.absenceReason = null;
                                }
                              });
                            },
                            child: const Text('Tous présents'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ...List.generate(_students.length, (i) {
                      final student = _students[i];
                      final record = _records[i];

                      return Semantics(
                        label:
                            'Présence de ${student.fullName}, statut ${record.status}',
                        child: Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    CircleAvatar(
                                      radius: 16,
                                      child: Text(
                                        student.fullName.isNotEmpty
                                            ? student.fullName[0].toUpperCase()
                                            : '?',
                                        style: const TextStyle(fontSize: 12),
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Text(student.fullName,
                                          style: const TextStyle(
                                              fontWeight: FontWeight.w500)),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                SegmentedButton<String>(
                                  segments: _statusOptions
                                      .map((opt) => ButtonSegment<String>(
                                            value: opt.$1,
                                            label: Text(opt.$2,
                                                style: const TextStyle(
                                                    fontSize: 11)),
                                          ))
                                      .toList(),
                                  selected: {record.status},
                                  onSelectionChanged: (v) {
                                    setState(() {
                                      record.status = v.first;
                                      if (record.status != 'absent') {
                                        record.absenceReason = null;
                                      }
                                    });
                                  },
                                  showSelectedIcon: false,
                                  style: ButtonStyle(
                                    visualDensity: VisualDensity.compact,
                                    tapTargetSize:
                                        MaterialTapTargetSize.shrinkWrap,
                                  ),
                                ),
                                if (record.status == 'absent') ...[
                                  const SizedBox(height: 8),
                                  TextField(
                                    decoration: const InputDecoration(
                                      labelText: 'Motif d\'absence',
                                      border: OutlineInputBorder(),
                                      isDense: true,
                                      contentPadding: EdgeInsets.symmetric(
                                          horizontal: 12, vertical: 8),
                                    ),
                                    onChanged: (v) => record.absenceReason = v,
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                      );
                    }),
                    const SizedBox(height: 16),
                    Semantics(
                      button: true,
                      label: 'Enregistrer les présences',
                      child: FilledButton.icon(
                        onPressed: _submitting ? null : _submit,
                        icon: _submitting
                            ? SizedBox(
                                height: 16,
                                width: 16,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: theme.colorScheme.onPrimary))
                            : const Icon(Icons.check),
                        label: Text(
                            _submitting ? 'Enregistrement...' : 'Enregistrer'),
                        style: FilledButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          minimumSize: const Size(double.infinity, 0),
                        ),
                      ),
                    ),
                  ] else if (_selectedClassId != null)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(32),
                        child: Text('Aucun élève dans cette classe'),
                      ),
                    ),
                ],
              ),
      ),
    );
  }
}
