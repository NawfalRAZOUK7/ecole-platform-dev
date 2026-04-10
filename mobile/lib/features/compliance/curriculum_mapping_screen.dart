import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'compliance_provider.dart';

class CurriculumMappingScreen extends ConsumerStatefulWidget {
  const CurriculumMappingScreen({super.key});

  @override
  ConsumerState<CurriculumMappingScreen> createState() =>
      _CurriculumMappingScreenState();
}

class _CurriculumMappingScreenState
    extends ConsumerState<CurriculumMappingScreen> {
  final _courseController = TextEditingController();
  String? _curriculumId;

  @override
  void dispose() {
    _courseController.dispose();
    super.dispose();
  }

  Future<void> _createMapping() async {
    if (_curriculumId == null || _courseController.text.trim().isEmpty) {
      return;
    }
    await ref.read(complianceRepositoryProvider).createMapping({
      'curriculum_id': _curriculumId,
      'course_id': _courseController.text.trim(),
    });
    ref.invalidate(complianceMappingsProvider);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Mapping created')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final curriculaAsync = ref.watch(complianceCurriculaProvider);
    final mappingsAsync = ref.watch(complianceMappingsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('compliance.mapping'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          curriculaAsync.when(
            data: (curricula) {
              _curriculumId ??= curricula.isEmpty ? null : curricula.first.id;
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      DropdownButtonFormField<String>(
                        initialValue: _curriculumId,
                        decoration: const InputDecoration(
                          labelText: 'Curriculum',
                          border: OutlineInputBorder(),
                        ),
                        items: curricula
                            .map(
                              (item) => DropdownMenuItem<String>(
                                value: item.id,
                                child: Text(item.title),
                              ),
                            )
                            .toList(),
                        onChanged: (value) {
                          setState(() => _curriculumId = value);
                        },
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _courseController,
                        decoration: const InputDecoration(
                          labelText: 'Course ID',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: _createMapping,
                          icon: const Icon(Icons.link_outlined),
                          label: Text(t.t('compliance.createMapping')),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => AppErrorWidget(message: error.toString()),
          ),
          const SizedBox(height: 16),
          mappingsAsync.when(
            data: (mappings) {
              if (mappings.isEmpty) {
                return AppEmptyState(
                  icon: Icons.account_tree_outlined,
                  title: t.t('compliance.noMappings'),
                );
              }
              return Column(
                children: mappings
                    .map(
                      (mapping) => Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          title: Text(mapping.curriculumId),
                          subtitle: Text(mapping.courseId ?? mapping.id),
                        ),
                      ),
                    )
                    .toList(),
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => AppErrorWidget(message: error.toString()),
          ),
        ],
      ),
    );
  }
}
