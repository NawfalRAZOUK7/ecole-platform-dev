import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

class ReportScheduleManager extends ConsumerStatefulWidget {
  final String reportType;
  final Map<String, dynamic> defaultParameters;

  const ReportScheduleManager({
    super.key,
    required this.reportType,
    required this.defaultParameters,
  });

  @override
  ConsumerState<ReportScheduleManager> createState() =>
      _ReportScheduleManagerState();
}

class _ReportScheduleManagerState extends ConsumerState<ReportScheduleManager> {
  bool _loading = true;
  List<ReportSchedule> _schedules = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final schedules = await ref.read(reportingRepositoryProvider).listSchedules();
      setState(() => _schedules = schedules);
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _createSchedule() async {
    final nameController = TextEditingController();
    final cronController = TextEditingController(text: '0 7 * * 1');
    bool isActive = true;

    final shouldCreate = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) => AlertDialog(
            title: Text(AppLocalizations.of(ref).t('reports.scheduleCreate')),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(labelText: 'Schedule name'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: cronController,
                  decoration: const InputDecoration(
                    labelText: 'Cron expression',
                    helperText: 'Example: 0 7 * * 1',
                  ),
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  value: isActive,
                  title: const Text('Active'),
                  contentPadding: EdgeInsets.zero,
                  onChanged: (value) {
                    setStateDialog(() => isActive = value);
                  },
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: Text(AppLocalizations.of(ref).t('common.cancel')),
              ),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Create'),
              ),
            ],
          ),
        );
      },
    );

    if (shouldCreate == true) {
      await ref.read(reportingRepositoryProvider).createSchedule(
            name: nameController.text.trim(),
            reportType: widget.reportType,
            cronExpression: cronController.text.trim(),
            parameters: widget.defaultParameters,
            isActive: isActive,
          );
      await _load();
    }

    nameController.dispose();
    cronController.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                t.t('reports.schedule'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            FilledButton.tonalIcon(
              onPressed: _createSchedule,
              icon: const Icon(Icons.add_alarm_outlined),
              label: Text(t.t('reports.scheduleCreate')),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (_loading)
          const Center(child: CircularProgressIndicator())
        else if (_schedules.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(t.t('reports.scheduleEmpty')),
            ),
          )
        else
          ..._schedules.map(
            (schedule) => Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: ListTile(
                title: Text(schedule.name),
                subtitle: Text(
                  '${schedule.reportType} · ${schedule.cronExpression}',
                ),
                leading: AppBadge(
                  label: schedule.isActive ? 'active' : 'paused',
                  variant: schedule.isActive
                      ? AppBadgeVariant.success
                      : AppBadgeVariant.neutral,
                ),
                trailing: Wrap(
                  spacing: 8,
                  children: [
                    IconButton(
                      onPressed: () async {
                        await ref
                            .read(reportingRepositoryProvider)
                            .runSchedule(schedule.id);
                        await _load();
                      },
                      icon: const Icon(Icons.play_arrow_outlined),
                    ),
                    IconButton(
                      onPressed: () async {
                        await ref
                            .read(reportingRepositoryProvider)
                            .updateSchedule(
                              id: schedule.id,
                              isActive: !schedule.isActive,
                            );
                        await _load();
                      },
                      icon: Icon(
                        schedule.isActive
                            ? Icons.pause_circle_outline
                            : Icons.play_circle_outline,
                      ),
                    ),
                    IconButton(
                      onPressed: () async {
                        await ref
                            .read(reportingRepositoryProvider)
                            .deleteSchedule(schedule.id);
                        await _load();
                      },
                      icon: const Icon(Icons.delete_outline),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}
