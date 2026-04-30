/// Compact card showing the student's current academic program.
///
/// Embeddable into the StudentHomeScreen dashboard or used standalone
/// at the top of the program-history screen. Reads the
/// [currentProgramProvider] family for the given studentId.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/features/student/program_history_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class CurrentProgramCard extends ConsumerWidget {
  final String studentId;

  /// When `true` (the default) the card is tappable and pushes
  /// `/students/:id/academic-history`. Set to `false` when used
  /// inside the academic-history screen itself.
  final bool linkToHistory;

  const CurrentProgramCard({
    super.key,
    required this.studentId,
    this.linkToHistory = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);
    final state = ref.watch(currentProgramProvider(studentId));

    final card = Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: _buildBody(context, state, t),
      ),
    );

    if (!linkToHistory) {
      return card;
    }
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => context.push('/students/$studentId/academic-history'),
      child: card,
    );
  }

  Widget _buildBody(
    BuildContext context,
    CurrentProgramState state,
    AppLocalizations t,
  ) {
    final theme = Theme.of(context);

    if (state.isLoading) {
      return const SizedBox(
        height: 56,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (state.error != null) {
      return Row(
        children: [
          Icon(Icons.error_outline, color: theme.colorScheme.error),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              t.t('program.current.error'),
              style: theme.textTheme.bodyMedium,
            ),
          ),
        ],
      );
    }

    final program = state.program?.program;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.t('program.current.title'),
          style: theme.textTheme.labelLarge?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: AppSpacing.xs),
        if (program == null)
          Text(
            t.t('program.current.empty'),
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          )
        else ...[
          Text(
            program.name,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '${program.code} · v${program.versionLabel}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ],
    );
  }
}
