/// Teacher classes screen — assigned classes with expandable student roster.
///
/// Reference: Phase 5B (from 4B)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/shared/widgets/search_filter_bar.dart';

// ── State ──

class _ClassesState {
  final List<ClassInfo> classes;
  final bool isLoading;
  final String? error;
  final String search;
  final String? expandedClassId;
  final List<StudentInfo> students;
  final bool loadingStudents;

  const _ClassesState({
    this.classes = const [],
    this.isLoading = false,
    this.error,
    this.search = '',
    this.expandedClassId,
    this.students = const [],
    this.loadingStudents = false,
  });

  _ClassesState copyWith({
    List<ClassInfo>? classes,
    bool? isLoading,
    String? error,
    bool clearError = false,
    String? search,
    String? expandedClassId,
    bool clearExpanded = false,
    List<StudentInfo>? students,
    bool? loadingStudents,
  }) {
    return _ClassesState(
      classes: classes ?? this.classes,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      search: search ?? this.search,
      expandedClassId:
          clearExpanded ? null : (expandedClassId ?? this.expandedClassId),
      students: students ?? this.students,
      loadingStudents: loadingStudents ?? this.loadingStudents,
    );
  }

  List<ClassInfo> get filteredClasses {
    if (search.isEmpty) return classes;
    final q = search.toLowerCase();
    return classes
        .where((c) =>
            c.name.toLowerCase().contains(q) ||
            c.code.toLowerCase().contains(q))
        .toList();
  }
}

class _ClassesNotifier extends StateNotifier<_ClassesState> {
  final Ref _ref;

  _ClassesNotifier(this._ref)
      : super(const _ClassesState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      final classes = await repo.getClasses();
      state = state.copyWith(classes: classes, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setSearch(String v) {
    state = state.copyWith(search: v);
  }

  Future<void> toggleExpand(String classId) async {
    if (state.expandedClassId == classId) {
      state = state.copyWith(clearExpanded: true, students: []);
      return;
    }
    state = state.copyWith(
        expandedClassId: classId, loadingStudents: true, students: []);
    try {
      final repo = _ref.read(teacherRepositoryProvider);
      final students = await repo.getClassStudents(classId);
      state = state.copyWith(students: students, loadingStudents: false);
    } catch (e) {
      state = state.copyWith(
          loadingStudents: false, error: e.toString());
    }
  }

  Future<void> refresh() async => load();
}

final _classesProvider =
    StateNotifierProvider.autoDispose<_ClassesNotifier, _ClassesState>((ref) {
  return _ClassesNotifier(ref);
});

// ── Screen ──

class ClassesScreen extends ConsumerWidget {
  const ClassesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_classesProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Mes classes')),
      body: Column(
        children: [
          SearchFilterBar(
            searchHint: 'Rechercher une classe...',
            searchValue: state.search,
            onSearchChanged: (v) =>
                ref.read(_classesProvider.notifier).setSearch(v),
          ),
          Expanded(child: _buildBody(context, ref, state, theme)),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, _ClassesState state,
      ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null && state.classes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(_classesProvider.notifier).load(),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }

    final classes = state.filteredClasses;
    if (classes.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.class_outlined, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Aucune classe assignée'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_classesProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: classes.length,
        itemBuilder: (context, index) {
          final cls = classes[index];
          final isExpanded = state.expandedClassId == cls.id;

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Column(
              children: [
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor: theme.colorScheme.primaryContainer,
                    child: Text(cls.code.isNotEmpty ? cls.code[0] : '?',
                        style: TextStyle(
                            color: theme.colorScheme.primary,
                            fontWeight: FontWeight.bold)),
                  ),
                  title: Text(cls.name,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Text(
                      '${cls.studentCount} élèves · ${cls.courseCount} cours'),
                  trailing: Icon(
                    isExpanded
                        ? Icons.expand_less
                        : Icons.expand_more,
                  ),
                  onTap: () =>
                      ref.read(_classesProvider.notifier).toggleExpand(cls.id),
                ),
                if (isExpanded) ...[
                  const Divider(height: 1),
                  if (state.loadingStudents)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Center(
                          child: CircularProgressIndicator(strokeWidth: 2)),
                    )
                  else if (state.students.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Aucun élève inscrit'),
                    )
                  else
                    ...state.students.map((s) => ListTile(
                          dense: true,
                          leading: CircleAvatar(
                            radius: 16,
                            child: Text(
                              s.fullName.isNotEmpty
                                  ? s.fullName[0].toUpperCase()
                                  : '?',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                          title: Text(s.fullName,
                              style: const TextStyle(fontSize: 14)),
                          subtitle: Text(s.email,
                              style: theme.textTheme.bodySmall),
                          trailing: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(
                              border: Border.all(
                                  color: s.enrollmentStatus == 'active'
                                      ? Colors.green
                                      : Colors.grey),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              s.enrollmentStatus == 'active'
                                  ? 'Inscrit'
                                  : s.enrollmentStatus,
                              style: TextStyle(
                                fontSize: 10,
                                color: s.enrollmentStatus == 'active'
                                    ? Colors.green
                                    : Colors.grey,
                              ),
                            ),
                          ),
                        )),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}
