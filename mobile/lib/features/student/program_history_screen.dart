/// Academic history screen — G49 Phase 3.
///
/// Read-only view of:
///   1. Current program card (top).
///   2. Year-grouped academic timeline.
///   3. Program-history event log (newest first).
///
/// Authorization is enforced by the backend's `_authorize_student_read`:
///   - STD: own data only.
///   - PAR: linked children only (via parent_child_links).
///   - ADM/DIR/TCH: school-scoped.
///
/// The mobile app passes the `studentId` from the route, so an STD viewing
/// themselves uses their own `auth.user.id` (the route can be entered via
/// `/students/<auth.user.id>/academic-history`).

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/program.dart';
import 'package:ecole_platform/features/student/program_history_provider.dart';
import 'package:ecole_platform/features/student/transcript_pdf_screen.dart';
import 'package:ecole_platform/features/student/widgets/current_program_card.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class AcademicHistoryScreen extends ConsumerStatefulWidget {
  final String studentId;

  const AcademicHistoryScreen({super.key, required this.studentId});

  @override
  ConsumerState<AcademicHistoryScreen> createState() =>
      _AcademicHistoryScreenState();
}

class _AcademicHistoryScreenState extends ConsumerState<AcademicHistoryScreen> {
  String? _activeActionKey;

  _ResolvedAcademicYear? _resolveTranscriptYear({
    CurrentProgramState? currentState,
    AcademicTimelineState? timelineState,
  }) {
    final resolvedCurrentState =
        currentState ?? ref.read(currentProgramProvider(widget.studentId));
    final resolvedTimelineState =
        timelineState ?? ref.read(academicTimelineProvider(widget.studentId));
    final current = resolvedCurrentState?.program;
    final timeline =
        resolvedTimelineState?.items ?? const <AcademicTimelineEntry>[];
    final currentYearId = current?.academicYearId;

    if (currentYearId != null && currentYearId.isNotEmpty) {
      for (final entry in timeline) {
        if (entry.academicYearId == currentYearId) {
          return _ResolvedAcademicYear(
            id: currentYearId,
            label: entry.academicYearLabel ?? entry.academicYearStart,
          );
        }
      }
      return _ResolvedAcademicYear(id: currentYearId, label: currentYearId);
    }

    if (timeline.isEmpty) {
      return null;
    }

    final latest = timeline.last;
    return _ResolvedAcademicYear(
      id: latest.academicYearId,
      label: latest.academicYearLabel ?? latest.academicYearStart,
    );
  }

  bool _isBusy(String key) => _activeActionKey == key;

  Future<void> _runAction({
    required String key,
    required Future<void> Function() action,
  }) async {
    setState(() {
      _activeActionKey = key;
    });
    try {
      await action();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) {
        setState(() {
          _activeActionKey = null;
        });
      }
    }
  }

  Future<File?> _downloadCurrentTranscriptPdf(
    AppLocalizations t,
  ) async {
    final year = _resolveTranscriptYear();
    if (year == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t.t('academicHistory.transcriptUnavailable'))),
        );
      }
      return null;
    }

    return ref.read(programRepositoryProvider).downloadTranscriptPdf(
          studentId: widget.studentId,
          academicYearId: year.id,
          lang: t.locale,
        );
  }

  Future<void> _openPdfViewer({
    required String title,
    required File file,
  }) async {
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TranscriptPdfScreen(
          title: title,
          filePath: file.path,
        ),
      ),
    );
  }

  Future<void> _viewCurrentTranscriptPdf(AppLocalizations t) async {
    await _runAction(
      key: 'current-view',
      action: () async {
        final year = _resolveTranscriptYear();
        final file = await _downloadCurrentTranscriptPdf(t);
        if (file == null || year == null) return;
        await _openPdfViewer(
          title: '${t.t('academicHistory.transcriptTitle')} · ${year.label}',
          file: file,
        );
      },
    );
  }

  Future<void> _shareCurrentTranscriptPdf(AppLocalizations t) async {
    await _runAction(
      key: 'current-share',
      action: () async {
        final file = await _downloadCurrentTranscriptPdf(t);
        if (file == null) return;
        await Share.shareXFiles([XFile(file.path)]);
      },
    );
  }

  Future<void> _viewSnapshotTranscriptPdf(
    AcademicSnapshotSummary snapshot,
    AppLocalizations t,
  ) async {
    await _runAction(
      key: 'snapshot-view-${snapshot.id}',
      action: () async {
        final file = await ref
            .read(programRepositoryProvider)
            .downloadSnapshotTranscriptPdf(
              snapshotId: snapshot.id,
              lang: t.locale,
            );
        await _openPdfViewer(
          title:
              '${t.t('academicHistory.snapshotTranscriptTitle')} · ${_snapshotKindLabel(snapshot.snapshotKind)}',
          file: file,
        );
      },
    );
  }

  Future<void> _shareSnapshotTranscriptPdf(
    AcademicSnapshotSummary snapshot,
    AppLocalizations t,
  ) async {
    await _runAction(
      key: 'snapshot-share-${snapshot.id}',
      action: () async {
        final file = await ref
            .read(programRepositoryProvider)
            .downloadSnapshotTranscriptPdf(
              snapshotId: snapshot.id,
              lang: t.locale,
            );
        await Share.shareXFiles([XFile(file.path)]);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final current = ref.watch(currentProgramProvider(widget.studentId));
    final timeline = ref.watch(academicTimelineProvider(widget.studentId));
    final history = ref.watch(programHistoryProvider(widget.studentId));
    final snapshots = ref.watch(studentSnapshotsProvider(widget.studentId));
    final transcriptYear = _resolveTranscriptYear(
      currentState: current,
      timelineState: timeline,
    );
    final snapshotYearLabels = {
      for (final entry in timeline.items)
        entry.academicYearId:
            entry.academicYearLabel ?? entry.academicYearStart,
    };

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('academicHistory.title')),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await Future.wait([
            ref
                .read(currentProgramProvider(widget.studentId).notifier)
                .refresh(),
            ref
                .read(academicTimelineProvider(widget.studentId).notifier)
                .refresh(),
            ref
                .read(programHistoryProvider(widget.studentId).notifier)
                .refresh(),
            ref
                .read(studentSnapshotsProvider(widget.studentId).notifier)
                .refresh(),
          ]);
        },
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.base),
          children: [
            CurrentProgramCard(
              studentId: widget.studentId,
              linkToHistory: false,
            ),
            const SizedBox(height: AppSpacing.lg),
            _TranscriptActionsCard(
              t: t,
              transcriptYearLabel: transcriptYear?.label,
              viewBusy: _isBusy('current-view'),
              shareBusy: _isBusy('current-share'),
              enabled: transcriptYear != null,
              onView: () => _viewCurrentTranscriptPdf(t),
              onShare: () => _shareCurrentTranscriptPdf(t),
            ),
            const SizedBox(height: AppSpacing.lg),
            _SectionHeading(label: t.t('academicHistory.timelineTitle')),
            const SizedBox(height: AppSpacing.sm),
            _TimelineSection(state: timeline, t: t),
            const SizedBox(height: AppSpacing.lg),
            _SectionHeading(label: t.t('academicHistory.historyTitle')),
            const SizedBox(height: AppSpacing.sm),
            _HistorySection(state: history, t: t),
            const SizedBox(height: AppSpacing.lg),
            _SectionHeading(label: t.t('academicHistory.snapshotsTitle')),
            const SizedBox(height: AppSpacing.sm),
            _SnapshotsSection(
              state: snapshots,
              yearLabels: snapshotYearLabels,
              activeActionKey: _activeActionKey,
              t: t,
              onViewSnapshot: (snapshot) =>
                  _viewSnapshotTranscriptPdf(snapshot, t),
              onShareSnapshot: (snapshot) =>
                  _shareSnapshotTranscriptPdf(snapshot, t),
            ),
          ],
        ),
      ),
    );
  }
}

class _ResolvedAcademicYear {
  final String id;
  final String label;

  const _ResolvedAcademicYear({
    required this.id,
    required this.label,
  });
}

class _TranscriptActionsCard extends StatelessWidget {
  final AppLocalizations t;
  final String? transcriptYearLabel;
  final bool enabled;
  final bool viewBusy;
  final bool shareBusy;
  final VoidCallback onView;
  final VoidCallback onShare;

  const _TranscriptActionsCard({
    required this.t,
    required this.transcriptYearLabel,
    required this.enabled,
    required this.viewBusy,
    required this.shareBusy,
    required this.onView,
    required this.onShare,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t.t('academicHistory.transcriptTitle'),
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              transcriptYearLabel == null
                  ? t.t('academicHistory.transcriptUnavailable')
                  : '${t.t('academicHistory.snapshotYear')}: $transcriptYearLabel',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: AppSpacing.base),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                FilledButton.icon(
                  onPressed: enabled && !viewBusy && !shareBusy ? onView : null,
                  icon: viewBusy
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.visibility_outlined),
                  label: Text(
                    viewBusy
                        ? t.t('common.loading')
                        : t.t('academicHistory.transcriptView'),
                  ),
                ),
                OutlinedButton.icon(
                  onPressed:
                      enabled && !viewBusy && !shareBusy ? onShare : null,
                  icon: shareBusy
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.share_outlined),
                  label: Text(
                    shareBusy
                        ? t.t('common.loading')
                        : t.t('academicHistory.transcriptShare'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeading extends StatelessWidget {
  final String label;
  const _SectionHeading({required this.label});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Text(
      label,
      style: theme.textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.w700,
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Timeline (year-grouped)
// ---------------------------------------------------------------------------
class _TimelineSection extends StatelessWidget {
  final AcademicTimelineState state;
  final AppLocalizations t;
  const _TimelineSection({required this.state, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (state.isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (state.error != null) {
      return _ErrorRow(message: t.t('academicHistory.timelineError'));
    }
    if (state.items.isEmpty) {
      return _EmptyRow(message: t.t('academicHistory.timelineEmpty'));
    }

    final grouped = _groupByYear(state.items);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final group in grouped) ...[
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.xs),
            child: Text(
              group.label ?? group.firstStart,
              style: theme.textTheme.titleSmall?.copyWith(
                color: theme.colorScheme.primary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          for (final entry in group.entries) _TimelineRow(entry: entry, t: t),
          const SizedBox(height: AppSpacing.sm),
        ],
      ],
    );
  }

  List<_YearGroup> _groupByYear(List<AcademicTimelineEntry> entries) {
    final map = <String, _YearGroup>{};
    for (final entry in entries) {
      final group = map.putIfAbsent(
        entry.academicYearId,
        () => _YearGroup(
          id: entry.academicYearId,
          label: entry.academicYearLabel,
          firstStart: entry.academicYearStart,
        ),
      );
      group.entries.add(entry);
    }
    return map.values.toList();
  }
}

class _YearGroup {
  final String id;
  final String? label;
  final String firstStart;
  final List<AcademicTimelineEntry> entries = [];
  _YearGroup({required this.id, required this.firstStart, this.label});
}

class _TimelineRow extends StatelessWidget {
  final AcademicTimelineEntry entry;
  final AppLocalizations t;
  const _TimelineRow({required this.entry, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final program = entry.program;
    final isActive = entry.status == 'active';
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: AppSpacing.xs),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.sm),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    entry.periodLabel ??
                        '${entry.periodStart} → ${entry.periodEnd}',
                    style: theme.textTheme.labelLarge,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${entry.classCode} · ${entry.className}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  if (program != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      '${program.code} — ${program.name}',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            _StatusBadge(
              label: t.t('academicHistory.status.${entry.status}'),
              color: isActive
                  ? theme.colorScheme.primary
                  : theme.colorScheme.outline,
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _StatusBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        border: Border.all(color: color),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 11)),
    );
  }
}

// ---------------------------------------------------------------------------
// History (event log)
// ---------------------------------------------------------------------------
class _HistorySection extends StatelessWidget {
  final ProgramHistoryState state;
  final AppLocalizations t;
  const _HistorySection({required this.state, required this.t});

  @override
  Widget build(BuildContext context) {
    if (state.isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (state.error != null) {
      return _ErrorRow(message: t.t('academicHistory.historyError'));
    }
    if (state.events.isEmpty) {
      return _EmptyRow(message: t.t('academicHistory.historyEmpty'));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final event in state.events) _HistoryRow(event: event, t: t),
      ],
    );
  }
}

class _HistoryRow extends StatelessWidget {
  final ProgramAssignmentEvent event;
  final AppLocalizations t;
  const _HistoryRow({required this.event, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final reasonKey = 'academicHistory.reason.${event.reasonCodeWire}';
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: AppSpacing.xs),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  t.t(reasonKey),
                  style: theme.textTheme.labelLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  event.occurredAt.split('T').first,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
            if (event.reasonNote != null && event.reasonNote!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                '“${event.reasonNote!}”',
                style: theme.textTheme.bodySmall?.copyWith(
                  fontStyle: FontStyle.italic,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SnapshotsSection extends StatelessWidget {
  final StudentSnapshotsState state;
  final Map<String, String> yearLabels;
  final String? activeActionKey;
  final AppLocalizations t;
  final Future<void> Function(AcademicSnapshotSummary snapshot) onViewSnapshot;
  final Future<void> Function(AcademicSnapshotSummary snapshot) onShareSnapshot;

  const _SnapshotsSection({
    required this.state,
    required this.yearLabels,
    required this.activeActionKey,
    required this.t,
    required this.onViewSnapshot,
    required this.onShareSnapshot,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (state.isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (state.error != null) {
      return _ErrorRow(message: t.t('academicHistory.snapshotsError'));
    }
    if (state.snapshots.isEmpty) {
      return _EmptyRow(message: t.t('academicHistory.snapshotsEmpty'));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final snapshot in state.snapshots)
          Card(
            elevation: 0,
            margin: const EdgeInsets.only(bottom: AppSpacing.xs),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: BorderSide(color: theme.colorScheme.outlineVariant),
            ),
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.base),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          _snapshotKindLabel(snapshot.snapshotKind),
                          style: theme.textTheme.labelLarge?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      Text(
                        snapshot.takenAt.split('T').first,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    '${t.t('academicHistory.snapshotYear')}: ${yearLabels[snapshot.academicYearId] ?? snapshot.academicYearId}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.base),
                  Wrap(
                    spacing: AppSpacing.sm,
                    runSpacing: AppSpacing.sm,
                    children: [
                      FilledButton.icon(
                        onPressed: activeActionKey == null
                            ? () => onViewSnapshot(snapshot)
                            : null,
                        icon: activeActionKey == 'snapshot-view-${snapshot.id}'
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.visibility_outlined),
                        label: Text(
                          activeActionKey == 'snapshot-view-${snapshot.id}'
                              ? t.t('common.loading')
                              : t.t('academicHistory.snapshotView'),
                        ),
                      ),
                      OutlinedButton.icon(
                        onPressed: activeActionKey == null
                            ? () => onShareSnapshot(snapshot)
                            : null,
                        icon: activeActionKey == 'snapshot-share-${snapshot.id}'
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.share_outlined),
                        label: Text(
                          activeActionKey == 'snapshot-share-${snapshot.id}'
                              ? t.t('common.loading')
                              : t.t('academicHistory.snapshotShare'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

String _snapshotKindLabel(String raw) {
  return raw
      .split('_')
      .where((part) => part.isNotEmpty)
      .map(
        (part) => '${part[0].toUpperCase()}${part.substring(1).toLowerCase()}',
      )
      .join(' ');
}

class _EmptyRow extends StatelessWidget {
  final String message;
  const _EmptyRow({required this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg),
      child: Center(
        child: Text(
          message,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

class _ErrorRow extends StatelessWidget {
  final String message;
  const _ErrorRow({required this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: theme.colorScheme.error),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              message,
              style: theme.textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}
