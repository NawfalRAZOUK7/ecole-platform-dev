/// Timetable screen — weekly grid view, swipe days on phone, color-coded by subject.
///
/// Reference: Phase 12B — Timetable mobile screen

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/domain/entities/academic/timetable.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'timetable_provider.dart';

Color _getSubjectColor(ThemeData theme, String subject) {
  final key = subject.toLowerCase().replaceAll(' ', '_');
  return theme.semanticPalette.subjectColors[key] ??
      theme.semanticPalette.subjectColors['default']!;
}

class TimetableScreen extends ConsumerWidget {
  const TimetableScreen({super.key});

  static const _days = [1, 2, 3, 4, 5, 6];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(timetableProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('timetable.title')),
        actions: [
          IconButton(
            onPressed: () => context.push('/timetable/constraints'),
            icon: const Icon(Icons.tune_outlined),
            tooltip: 'Constraints',
          ),
          IconButton(
            onPressed: () => context.push('/timetable/generate'),
            icon: const Icon(Icons.auto_awesome_outlined),
            tooltip: 'Generate',
          ),
        ],
      ),
      body: _buildBody(context, ref, state, t),
    );
  }

  Widget _buildBody(
    BuildContext context,
    WidgetRef ref,
    TimetableState state,
    AppLocalizations t,
  ) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: colors.error),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(timetableProvider.notifier).load(),
              child: Text(t.t('common.retry')),
            ),
          ],
        ),
      );
    }

    final schedule = state.schedule;
    if (schedule == null || schedule.slots.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.calendar_today, size: 48, color: colors.outline),
            const SizedBox(height: 16),
            Text(t.t('timetable.empty')),
          ],
        ),
      );
    }

    // Group by day
    final byDay = <int, List<TimetableSlot>>{};
    for (final d in _days) {
      byDay[d] = [];
    }
    for (final slot in schedule.slots) {
      byDay[slot.dayOfWeek]?.add(slot);
    }
    for (final list in byDay.values) {
      list.sort((a, b) => a.startTime.compareTo(b.startTime));
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(timetableProvider.notifier).refresh(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Text(
              '${t.t('timetable.weekOf')} ${schedule.weekStart} — ${schedule.weekEnd}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          Expanded(
            child: MediaQuery.of(context).size.width > 600
                ? _buildTabletGrid(byDay, t)
                : PageView.builder(
                    itemCount: _days.length,
                    controller: PageController(
                      initialPage: _todayIndex(),
                    ),
                    itemBuilder: (context, index) {
                      final day = _days[index];
                      final slots = byDay[day] ?? [];
                      return _DayColumn(
                        day: day,
                        slots: slots,
                        t: t,
                        shrinkWrap: false,
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabletGrid(
    Map<int, List<TimetableSlot>> byDay,
    AppLocalizations t,
  ) {
    return SingleChildScrollView(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: _days.map((day) {
          final slots = byDay[day] ?? [];
          return Expanded(
            child: _DayColumn(
              day: day,
              slots: slots,
              t: t,
              shrinkWrap: true,
            ),
          );
        }).toList(),
      ),
    );
  }

  int _todayIndex() {
    final weekday = DateTime.now().weekday; // 1=Mon, 7=Sun
    final idx = _days.indexOf(weekday);
    return idx >= 0 ? idx : 0;
  }
}

class _DayColumn extends StatelessWidget {
  final int day;
  final List<TimetableSlot> slots;
  final AppLocalizations t;
  final bool shrinkWrap;

  const _DayColumn({
    required this.day,
    required this.slots,
    required this.t,
    required this.shrinkWrap,
  });

  @override
  Widget build(BuildContext context) {
    final dayLabel = t.t('timetable.days.$day');
    final theme = Theme.of(context);

    return ListView(
      shrinkWrap: shrinkWrap,
      physics: shrinkWrap ? const NeverScrollableScrollPhysics() : null,
      padding: const EdgeInsets.all(16),
      children: [
        Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              dayLabel,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (slots.isEmpty)
          Center(
            child: Padding(
              padding: const EdgeInsets.only(top: 40),
              child: Text(
                '—',
                style: theme.textTheme.headlineMedium
                    ?.copyWith(color: theme.colorScheme.outline),
              ),
            ),
          )
        else
          ...slots.map((slot) => _SlotCard(slot: slot, t: t)),
      ],
    );
  }
}

class _SlotCard extends StatelessWidget {
  final TimetableSlot slot;
  final AppLocalizations t;

  const _SlotCard({required this.slot, required this.t});

  @override
  Widget build(BuildContext context) {
    final isCanceled = slot.exception?.exceptionType == 'CANCELED';
    final isSubstituted = slot.exception?.exceptionType == 'SUBSTITUTED';
    final isRoomChanged = slot.exception?.exceptionType == 'ROOM_CHANGED';
    final theme = Theme.of(context);
    final exceptionChips = [
      if (isCanceled)
        _exceptionChip(t.t('timetable.canceled'), theme.colorScheme.error),
      if (isSubstituted)
        _exceptionChip(
          t.t('timetable.substituted'),
          theme.semanticPalette.warning,
        ),
      if (isRoomChanged && slot.exception?.newRoom != null)
        _exceptionChip(
          '→ ${slot.exception!.newRoom}',
          theme.colorScheme.primary,
        ),
    ];

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: isCanceled
          ? theme.colorScheme.errorContainer
          : _getSubjectColor(theme, slot.subject),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${slot.startTime.substring(0, 5)} – ${slot.endTime.substring(0, 5)}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                      decoration:
                          isCanceled ? TextDecoration.lineThrough : null,
                    ),
                  ),
                ),
                if (exceptionChips.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Flexible(
                    child: Align(
                      alignment: Alignment.centerRight,
                      child: Wrap(
                        spacing: 4,
                        runSpacing: 4,
                        alignment: WrapAlignment.end,
                        children: exceptionChips,
                      ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 4),
            Text(
              slot.subject,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                decoration: isCanceled ? TextDecoration.lineThrough : null,
              ),
            ),
            if (slot.room != null) ...[
              const SizedBox(height: 2),
              Wrap(
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 4,
                children: [
                  Icon(
                    Icons.room,
                    size: 14,
                    color: theme.colorScheme.outline,
                  ),
                  Text(slot.room!, style: theme.textTheme.bodySmall),
                ],
              ),
            ],
            if (slot.className != null) ...[
              const SizedBox(height: 2),
              Text(
                slot.className!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _exceptionChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 0.5),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
