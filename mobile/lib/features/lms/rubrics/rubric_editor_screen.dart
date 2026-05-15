import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/lms/rubric.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'rubrics_provider.dart';

class RubricEditorScreen extends ConsumerStatefulWidget {
  final String rubricId;

  const RubricEditorScreen({
    super.key,
    required this.rubricId,
  });

  @override
  ConsumerState<RubricEditorScreen> createState() => _RubricEditorScreenState();
}

class _RubricEditorScreenState extends ConsumerState<RubricEditorScreen> {
  final _titleController = TextEditingController();
  final _subjectController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _criteriaController = TextEditingController();
  bool _initialized = false;
  bool _saving = false;

  @override
  void dispose() {
    _titleController.dispose();
    _subjectController.dispose();
    _descriptionController.dispose();
    _criteriaController.dispose();
    super.dispose();
  }

  void _hydrate(Rubric rubric) {
    if (_initialized) return;
    _titleController.text = rubric.title;
    _subjectController.text = rubric.subject ?? '';
    _descriptionController.text = rubric.description ?? '';
    _criteriaController.text = const JsonEncoder.withIndent('  ').convert(
      rubric.criteria
          .map(
            (criterion) => {
              'id': criterion.id,
              'name': criterion.name,
              'weight': criterion.weight,
              'levels': criterion.levels
                  .map(
                    (level) => {
                      'id': level.id,
                      'label': level.label,
                      'score': level.score,
                      'description': level.description,
                    },
                  )
                  .toList(),
            },
          )
          .toList(),
    );
    _initialized = true;
  }

  List<RubricCriterion> _parseCriteria(String value) {
    final data = jsonDecode(value) as List<dynamic>;
    return data.map((item) {
      final json = item as Map<String, dynamic>;
      return RubricCriterion(
        id: json['id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        weight: (json['weight'] as num?)?.toDouble() ?? 0,
        levels: (json['levels'] as List<dynamic>? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(
              (level) => RubricLevel(
                id: level['id'] as String? ?? '',
                label: level['label'] as String? ?? '',
                score: (level['score'] as num?)?.toDouble() ?? 0,
                description: level['description'] as String? ?? '',
              ),
            )
            .toList(),
      );
    }).toList();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref.read(rubricRepositoryProvider).updateRubric(
            id: widget.rubricId,
            title: _titleController.text.trim(),
            description: _descriptionController.text.trim(),
            subject: _subjectController.text.trim(),
            criteria: _parseCriteria(_criteriaController.text),
          );
      ref.invalidate(rubricsProvider);
      ref.invalidate(rubricProvider(widget.rubricId));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Rubric updated')),
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
    final rubricAsync = ref.watch(rubricProvider(widget.rubricId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('rubrics.editor'))),
      body: rubricAsync.when(
        data: (rubric) {
          _hydrate(rubric);
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              TextField(
                controller: _titleController,
                decoration: const InputDecoration(labelText: 'Title'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _subjectController,
                decoration: const InputDecoration(labelText: 'Subject'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _descriptionController,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Description'),
              ),
              const SizedBox(height: 12),
              Text(
                'Criteria JSON',
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _criteriaController,
                maxLines: 18,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  helperText: 'Edit criteria, weights and levels directly',
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
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
          label: Text(AppLocalizations.of(ref).t('common.save')),
        ),
      ),
    );
  }
}
