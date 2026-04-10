import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/timetable.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'timetable_provider.dart';

class TimetableGenerateScreen extends ConsumerStatefulWidget {
  const TimetableGenerateScreen({super.key});

  @override
  ConsumerState<TimetableGenerateScreen> createState() =>
      _TimetableGenerateScreenState();
}

class _TimetableGenerateScreenState
    extends ConsumerState<TimetableGenerateScreen> {
  final _academicYearController =
      TextEditingController(text: DateTime.now().year.toString());
  GenerationJob? _job;
  GenerationPreview? _preview;
  ApplyGenerationResult? _applyResult;
  bool _loading = false;

  @override
  void dispose() {
    _academicYearController.dispose();
    super.dispose();
  }

  Future<void> _triggerGeneration() async {
    setState(() => _loading = true);
    try {
      final response = await ref.read(apiClientProvider).post(
            '/timetable/generate',
            body: {
              'academic_year_id': _academicYearController.text.trim(),
            },
          );
      final job = GenerationJob.fromJson(response.data);
      setState(() {
        _job = job;
        _applyResult = null;
      });
      await _refreshGeneration();
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _refreshGeneration() async {
    final job = _job;
    if (job == null) return;

    setState(() => _loading = true);
    try {
      final api = ref.read(apiClientProvider);
      final jobResponse = await api.get('/timetable/generate/${job.jobId}');
      final refreshedJob = GenerationJob.fromJson(jobResponse.data);
      GenerationPreview? preview;
      try {
        final previewResponse =
            await api.get('/timetable/generate/${job.jobId}/preview');
        preview = GenerationPreview.fromJson(previewResponse.data);
      } catch (_) {
        preview = null;
      }
      setState(() {
        _job = refreshedJob;
        _preview = preview;
      });
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _applyGeneration() async {
    final job = _job;
    if (job == null) return;

    setState(() => _loading = true);
    try {
      final response = await ref
          .read(apiClientProvider)
          .post('/timetable/generate/${job.jobId}/apply', body: {});
      final result = ApplyGenerationResult.fromJson(response.data);
      ref.invalidate(timetableProvider);
      setState(() => _applyResult = result);
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Generate timetable')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _academicYearController,
            decoration: const InputDecoration(labelText: 'Academic year ID'),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _loading ? null : _triggerGeneration,
            icon: _loading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.auto_awesome_outlined),
            label: const Text('Generate preview'),
          ),
          if (_job != null) ...[
            const SizedBox(height: 24),
            AppStatCard(
              label: 'Generation status',
              value: '${_job!.status} (${_job!.progress}%)',
              icon: Icons.sync_outlined,
            ),
            if (_job!.error != null && _job!.error!.isNotEmpty) ...[
              const SizedBox(height: 12),
              AppErrorWidget(message: _job!.error!),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.tonal(
                    onPressed: _loading ? null : _refreshGeneration,
                    child: const Text('Refresh'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.tonal(
                    onPressed: _loading || _preview == null ? null : _applyGeneration,
                    child: const Text('Apply'),
                  ),
                ),
              ],
            ),
          ],
          if (_applyResult != null) ...[
            const SizedBox(height: 16),
            AppDataTable<Map<String, String>>(
              columns: const [
                AppColumn<Map<String, String>>(
                  header: 'Applied',
                  cellBuilder: _appliedCell,
                ),
                AppColumn<Map<String, String>>(
                  header: 'Skipped',
                  cellBuilder: _skippedCell,
                ),
              ],
              rows: [
                {
                  'applied': '${_applyResult!.applied}',
                  'skipped': '${_applyResult!.skipped}',
                },
              ],
            ),
          ],
          if (_preview != null) ...[
            const SizedBox(height: 24),
            Text(
              'Preview slots',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 12),
            if (_preview!.warnings.isNotEmpty) ...[
              ..._preview!.warnings.map(
                (warning) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppBadge(
                    label: warning,
                    variant: AppBadgeVariant.warning,
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],
            ..._preview!.slots.map(
              (slot) => Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  title: Text(slot.subject),
                  subtitle: Text(
                    'Day ${slot.dayOfWeek} · ${slot.startTime} - ${slot.endTime}\nClass ${slot.classId} · ${slot.room ?? 'No room'}',
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

Widget _appliedCell(Map<String, String> row) => Text(row['applied'] ?? '0');

Widget _skippedCell(Map<String, String> row) => Text(row['skipped'] ?? '0');
