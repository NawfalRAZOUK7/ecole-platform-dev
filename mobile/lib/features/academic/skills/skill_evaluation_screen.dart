import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/academic/skills.dart';
import 'package:ecole_platform/domain/entities/lms/teacher.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'skills_provider.dart';

class SkillEvaluationScreen extends ConsumerStatefulWidget {
  const SkillEvaluationScreen({super.key});

  @override
  ConsumerState<SkillEvaluationScreen> createState() =>
      _SkillEvaluationScreenState();
}

class _SkillEvaluationScreenState extends ConsumerState<SkillEvaluationScreen> {
  String? _classId;
  String? _studentId;
  SkillEvaluation? _result;
  bool _loading = false;

  Future<void> _evaluate() async {
    if (_studentId == null) return;
    setState(() => _loading = true);
    try {
      final result = await ref.read(skillsRepositoryProvider).evaluateStudent(
            _studentId!,
            academicYearId: ref.read(academicYearIdProvider),
          );
      setState(() => _result = result);
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final classesAsync = ref.watch(skillsClassesProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('skills.evaluate'))),
      body: classesAsync.when(
        data: (classes) {
          _classId ??= classes.isEmpty ? null : classes.first.id;
          final studentsAsync = _classId == null
              ? const AsyncValue<List<StudentInfo>>.data([])
              : ref.watch(skillsStudentsProvider(_classId!));
          return studentsAsync.when(
            data: (students) {
              _studentId ??= students.isEmpty ? null : students.first.id;
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          DropdownButtonFormField<String>(
                            initialValue: _classId,
                            decoration: InputDecoration(
                              labelText: t.t('skills.class'),
                              border: const OutlineInputBorder(),
                            ),
                            items: classes
                                .map(
                                  (item) => DropdownMenuItem<String>(
                                    value: item.id,
                                    child: Text(item.name),
                                  ),
                                )
                                .toList(),
                            onChanged: (value) {
                              setState(() {
                                _classId = value;
                                _studentId = null;
                              });
                            },
                          ),
                          const SizedBox(height: 12),
                          DropdownButtonFormField<String>(
                            initialValue: _studentId,
                            decoration: InputDecoration(
                              labelText: t.t('skills.student'),
                              border: const OutlineInputBorder(),
                            ),
                            items: students
                                .map(
                                  (item) => DropdownMenuItem<String>(
                                    value: item.id,
                                    child: Text(item.fullName),
                                  ),
                                )
                                .toList(),
                            onChanged: (value) {
                              setState(() => _studentId = value);
                            },
                          ),
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed: _loading ? null : _evaluate,
                              icon: _loading
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Icon(Icons.fact_check_outlined),
                              label: Text(t.t('skills.evaluateNow')),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_result != null) ...[
                    const SizedBox(height: 16),
                    AppStatCard(
                      label: t.t('skills.overallScore'),
                      value: _result!.overallScore.toStringAsFixed(1),
                      icon: Icons.workspace_premium_outlined,
                    ),
                    const SizedBox(height: 12),
                    ..._result!.dimensions.map(
                      (item) => Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          title: Text(item.label),
                          trailing: Text(item.score.toStringAsFixed(1)),
                        ),
                      ),
                    ),
                  ],
                ],
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => AppErrorWidget(message: error.toString()),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}
