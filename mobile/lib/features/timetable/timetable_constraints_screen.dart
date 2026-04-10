import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/timetable.dart';

class TimetableConstraintsScreen extends ConsumerStatefulWidget {
  const TimetableConstraintsScreen({super.key});

  @override
  ConsumerState<TimetableConstraintsScreen> createState() =>
      _TimetableConstraintsScreenState();
}

class _TimetableConstraintsScreenState
    extends ConsumerState<TimetableConstraintsScreen> {
  final _academicYearController = TextEditingController();
  final _maxConsecutiveController = TextEditingController();
  final _availabilityController = TextEditingController();
  final _roomsController = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _academicYearController.dispose();
    _maxConsecutiveController.dispose();
    _availabilityController.dispose();
    _roomsController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final response =
          await ref.read(apiClientProvider).get('/timetable/constraints');
      final constraints = TimetableConstraints.fromJson(response.data);
      _academicYearController.text = constraints.academicYearId;
      _maxConsecutiveController.text =
          constraints.maxConsecutiveClasses.toString();
      _availabilityController.text =
          const JsonEncoder.withIndent('  ').convert(
        constraints.teacherAvailability
            .map(
              (item) => {
                'teacher_id': item.teacherId,
                'day_of_week': item.dayOfWeek,
                'available_from': item.availableFrom,
                'available_until': item.availableUntil,
              },
            )
            .toList(),
      );
      _roomsController.text = const JsonEncoder.withIndent('  ').convert(
        constraints.roomConstraints
            .map(
              (item) => {
                'room_name': item.roomName,
                'capacity': item.capacity,
              },
            )
            .toList(),
      );
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref.read(apiClientProvider).post(
            '/timetable/constraints',
            body: {
              'academic_year_id': _academicYearController.text.trim(),
              'max_consecutive_classes':
                  int.tryParse(_maxConsecutiveController.text) ?? 0,
              'teacher_availability':
                  (jsonDecode(_availabilityController.text) as List<dynamic>)
                      .cast<Map<String, dynamic>>(),
              'room_constraints':
                  (jsonDecode(_roomsController.text) as List<dynamic>)
                      .cast<Map<String, dynamic>>(),
            },
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Constraints saved')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Timetable constraints')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _academicYearController,
            decoration: const InputDecoration(labelText: 'Academic year ID'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _maxConsecutiveController,
            keyboardType: TextInputType.number,
            decoration:
                const InputDecoration(labelText: 'Max consecutive classes'),
          ),
          const SizedBox(height: 16),
          Text(
            'Teacher availability JSON',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _availabilityController,
            maxLines: 10,
            decoration: const InputDecoration(border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          Text(
            'Room constraints JSON',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _roomsController,
            maxLines: 8,
            decoration: const InputDecoration(border: OutlineInputBorder()),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.all(16),
        child: FilledButton.icon(
          onPressed: _saving ? null : _save,
          icon: _saving
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.save_outlined),
          label: const Text('Save constraints'),
        ),
      ),
    );
  }
}
