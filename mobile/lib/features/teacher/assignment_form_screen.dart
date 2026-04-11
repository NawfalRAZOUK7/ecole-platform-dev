/// Assignment form screen — create assignments for a course.
///
/// Reference: Phase 5B (from 4B)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';

// ── State ──

class _AssignmentFormState {
  final List<Course> courses;
  final List<Assignment> assignments;
  final bool isLoading;
  final String? error;
  final String? courseFilter;
  final bool creating;
  final String? nextCursor;
  final bool hasMore;

  const _AssignmentFormState({
    this.courses = const [],
    this.assignments = const [],
    this.isLoading = false,
    this.error,
    this.courseFilter,
    this.creating = false,
    this.nextCursor,
    this.hasMore = false,
  });

  _AssignmentFormState copyWith({
    List<Course>? courses,
    List<Assignment>? assignments,
    bool? isLoading,
    String? error,
    bool clearError = false,
    String? courseFilter,
    bool clearCourseFilter = false,
    bool? creating,
    String? nextCursor,
    bool? hasMore,
  }) {
    return _AssignmentFormState(
      courses: courses ?? this.courses,
      assignments: assignments ?? this.assignments,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      courseFilter:
          clearCourseFilter ? null : (courseFilter ?? this.courseFilter),
      creating: creating ?? this.creating,
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}

class _AssignmentFormNotifier extends StateNotifier<_AssignmentFormState> {
  final Ref _ref;

  _AssignmentFormNotifier(this._ref)
      : super(const _AssignmentFormState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      final courses = await repo.getCourses();
      final assignments =
          await repo.getAssignments(courseId: state.courseFilter);
      state = state.copyWith(
        courses: courses,
        assignments: assignments.items,
        nextCursor: assignments.nextCursor,
        hasMore: assignments.hasMore,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setCourseFilter(String? value) {
    state = value == null
        ? state.copyWith(clearCourseFilter: true)
        : state.copyWith(courseFilter: value);
    load();
  }

  Future<void> createAssignment({
    required String courseId,
    required String title,
    String? description,
    String? dueAt,
    int totalPoints = 20,
  }) async {
    state = state.copyWith(creating: true, clearError: true);
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      await repo.createAssignment(
        courseId: courseId,
        title: title,
        description: description,
        dueAt: dueAt,
        totalPoints: totalPoints,
      );
      state = state.copyWith(creating: false);
      await load();
    } catch (e) {
      state = state.copyWith(creating: false, error: e.toString());
    }
  }

  Future<void> refresh() async => load();
}

final _assignmentFormProvider = StateNotifierProvider.autoDispose<
    _AssignmentFormNotifier, _AssignmentFormState>((ref) {
  return _AssignmentFormNotifier(ref);
});

// ── Screen ──

class AssignmentFormScreen extends ConsumerStatefulWidget {
  const AssignmentFormScreen({super.key});

  @override
  ConsumerState<AssignmentFormScreen> createState() =>
      _AssignmentFormScreenState();
}

class _AssignmentFormScreenState extends ConsumerState<AssignmentFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _pointsController = TextEditingController(text: '20');
  String? _selectedCourseId;
  DateTime? _dueAt;
  bool _showForm = false;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _pointsController.dispose();
    super.dispose();
  }

  Future<void> _pickDueDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 7)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date != null && mounted) {
      final time = await showTimePicker(
        context: context,
        initialTime: const TimeOfDay(hour: 23, minute: 59),
      );
      setState(() {
        _dueAt = DateTime(
          date.year,
          date.month,
          date.day,
          time?.hour ?? 23,
          time?.minute ?? 59,
        );
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedCourseId == null) return;
    await ref.read(_assignmentFormProvider.notifier).createAssignment(
          courseId: _selectedCourseId!,
          title: _titleController.text.trim(),
          description: _descriptionController.text.trim().isNotEmpty
              ? _descriptionController.text.trim()
              : null,
          dueAt: _dueAt?.toIso8601String(),
          totalPoints: int.tryParse(_pointsController.text) ?? 20,
        );
    if (mounted) {
      _titleController.clear();
      _descriptionController.clear();
      _pointsController.text = '20';
      setState(() {
        _dueAt = null;
        _showForm = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Devoir créé avec succès')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(_assignmentFormProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Devoirs')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => setState(() => _showForm = !_showForm),
        child: Icon(_showForm ? Icons.close : Icons.add),
      ),
      body: Column(
        children: [
          // Course filter
          if (state.courses.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: DropdownButtonFormField<String>(
                initialValue: state.courseFilter,
                decoration: const InputDecoration(
                  labelText: 'Filtrer par cours',
                  border: OutlineInputBorder(),
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                ),
                items: [
                  const DropdownMenuItem(
                      value: null, child: Text('Tous les cours')),
                  ...state.courses.map((c) => DropdownMenuItem(
                        value: c.id,
                        child: Text(c.title),
                      )),
                ],
                onChanged: (v) => ref
                    .read(_assignmentFormProvider.notifier)
                    .setCourseFilter(v),
              ),
            ),

          // Create form
          if (_showForm)
            Card(
              margin: const EdgeInsets.symmetric(horizontal: 16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Nouveau devoir',
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: _selectedCourseId,
                        decoration: const InputDecoration(
                          labelText: 'Cours *',
                          border: OutlineInputBorder(),
                        ),
                        items: state.courses
                            .map((c) => DropdownMenuItem(
                                  value: c.id,
                                  child: Text(c.title),
                                ))
                            .toList(),
                        validator: (v) => v == null ? 'Cours requis' : null,
                        onChanged: (v) => setState(() => _selectedCourseId = v),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _titleController,
                        decoration: const InputDecoration(
                          labelText: 'Titre *',
                          border: OutlineInputBorder(),
                        ),
                        validator: (v) =>
                            (v == null || v.isEmpty) ? 'Titre requis' : null,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _descriptionController,
                        maxLines: 2,
                        decoration: const InputDecoration(
                          labelText: 'Description',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: _pointsController,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: 'Points',
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: InkWell(
                              onTap: _pickDueDate,
                              child: InputDecorator(
                                decoration: const InputDecoration(
                                  labelText: 'Date limite',
                                  border: OutlineInputBorder(),
                                  suffixIcon: Icon(Icons.calendar_today),
                                ),
                                child: Text(
                                  _dueAt != null
                                      ? DateFormat.yMd('fr')
                                          .add_Hm()
                                          .format(_dueAt!)
                                      : 'Aucune',
                                  style: theme.textTheme.bodyMedium,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: state.creating ? null : _submit,
                        child: state.creating
                            ? SizedBox(
                                height: 16,
                                width: 16,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: theme.colorScheme.onPrimary))
                            : const Text('Créer le devoir'),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          if (state.error != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(state.error!,
                    style:
                        TextStyle(color: theme.colorScheme.onErrorContainer)),
              ),
            ),

          // Assignment list
          Expanded(child: _buildList(context, ref, state, theme)),
        ],
      ),
    );
  }

  Widget _buildList(BuildContext context, WidgetRef ref,
      _AssignmentFormState state, ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.assignments.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assignment_outlined,
                size: 48, color: theme.colorScheme.outline),
            SizedBox(height: 16),
            Text('Aucun devoir'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_assignmentFormProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.assignments.length,
        itemBuilder: (context, index) {
          final a = state.assignments[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: theme.colorScheme.primaryContainer,
                child: Icon(Icons.assignment,
                    color: theme.colorScheme.primary, size: 20),
              ),
              title: Text(a.title,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text(
                '${a.totalPoints} pts${a.dueAt != null ? ' · ${_formatDate(a.dueAt!)}' : ''}',
                style: theme.textTheme.bodySmall,
              ),
            ),
          );
        },
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat.yMMMd('fr').format(date);
    } catch (_) {
      return dateStr;
    }
  }
}
