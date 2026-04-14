import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/features/games/game_provider.dart';
import 'package:ecole_platform/features/games/models/game_config.dart';
import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/rewards/rewards_widgets.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';

class SortingGameScreen extends ConsumerStatefulWidget {
  const SortingGameScreen({super.key});

  @override
  ConsumerState<SortingGameScreen> createState() => _SortingGameScreenState();
}

class _SortingGameScreenState extends ConsumerState<SortingGameScreen> {
  bool _rewardAwarded = false;
  bool _showCelebration = false;

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<GameSessionState>>(
      gameProvider(GameType.sorting),
      (previous, next) {
        final nextState = next.valueOrNull;
        final wasCompleted = previous?.valueOrNull?.isCompleted ?? false;
        if (nextState != null && nextState.isCompleted && !wasCompleted) {
          unawaited(_handleCompleted(nextState));
        }
      },
    );

    final sessionAsync = ref.watch(gameProvider(GameType.sorting));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sorting Game'),
      ),
      body: sessionAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(
          message: '$error',
          onRetry: () =>
              ref.read(gameProvider(GameType.sorting).notifier).resetGame(),
        ),
        data: (session) {
          final categories = session.config.items
              .map((item) => item.category ?? 'General')
              .toSet()
              .toList();
          final hasIncorrectFeedback = session.sortingFeedback.values
              .any((feedback) => feedback == false);
          final unplacedItems = session.config.items.where((item) {
            final feedback = session.sortingFeedback[item.id];
            if (feedback == false) {
              return true;
            }
            return session.sortingPlacements[item.id] == null;
          }).toList();

          return Stack(
            children: <Widget>[
              Column(
                children: <Widget>[
                  Padding(
                    padding: const EdgeInsets.all(AppSpacing.base),
                    child: Row(
                      children: <Widget>[
                        _MetricBadge(
                          icon: Icons.timer_outlined,
                          label: _formatDuration(session.elapsedSeconds),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        _MetricBadge(
                          icon: Icons.done_all_rounded,
                          label:
                              '${session.placedSortingCount}/${session.config.items.length}',
                        ),
                        const Spacer(),
                        FilledButton.tonalIcon(
                          onPressed: _reset,
                          icon: const Icon(Icons.replay),
                          label: const Text('Replay'),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: categories
                          .map(
                            (category) => Expanded(
                              child: _SortingCategoryZone(
                                category: category,
                                showIncorrectFeedback:
                                    session.sortingPlacements.entries.any(
                                  (entry) =>
                                      entry.value == category &&
                                      session.sortingFeedback[entry.key] ==
                                          false,
                                ),
                                items: session.config.items
                                    .where((item) =>
                                        session.sortingPlacements[item.id] ==
                                            category &&
                                        session.sortingFeedback[item.id] ==
                                            true)
                                    .toList(),
                                onAccept: (item) {
                                  ref
                                      .read(gameProvider(GameType.sorting)
                                          .notifier)
                                      .dropSortingItem(item.id, category);
                                },
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppSpacing.base),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      border: Border(
                        top: BorderSide(color: Colors.black12),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Text(
                          hasIncorrectFeedback
                              ? 'Try again: the red card belongs in another zone.'
                              : 'Press and hold a card, then drag it into the matching zone.',
                          style:
                              Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: hasIncorrectFeedback
                                        ? KidsContentColors.gameRed
                                        : Colors.black.withAlpha(160),
                                    fontWeight: hasIncorrectFeedback
                                        ? FontWeight.w700
                                        : FontWeight.w500,
                                  ),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        Wrap(
                          spacing: AppSpacing.sm,
                          runSpacing: AppSpacing.sm,
                          children: unplacedItems
                              .map(
                                (item) => _SortingDraggableCard(
                                  item: item,
                                  isIncorrect:
                                      session.sortingFeedback[item.id] == false,
                                ),
                              )
                              .toList(),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (_showCelebration)
                ConfettiOverlay(
                  starsEarned:
                      sessionAsync.valueOrNull?.config.rewardStars ?? 0,
                  xpEarned:
                      (sessionAsync.valueOrNull?.config.rewardStars ?? 0) * 10,
                  onDismiss: () {
                    setState(() => _showCelebration = false);
                  },
                ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _handleCompleted(GameSessionState session) async {
    if (_rewardAwarded) {
      return;
    }
    _rewardAwarded = true;
    if (mounted) {
      setState(() => _showCelebration = true);
    }
    await ref.read(rewardsProvider.notifier).awardEvent(
          eventType: 'game_completed',
          starsEarned: session.config.rewardStars,
          xpEarned: session.config.rewardStars * 10,
          sourceType: 'game',
          sourceId: session.config.type.slug,
        );
  }

  void _reset() {
    _rewardAwarded = false;
    setState(() => _showCelebration = false);
    ref.read(gameProvider(GameType.sorting).notifier).resetGame();
  }

  static String _formatDuration(int seconds) {
    final minutes = seconds ~/ 60;
    final remaining = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${remaining.toString().padLeft(2, '0')}';
  }
}

class _MetricBadge extends StatelessWidget {
  const _MetricBadge({
    required this.icon,
    required this.label,
  });

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.black12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 16),
          const SizedBox(width: 6),
          Text(label),
        ],
      ),
    );
  }
}

class _SortingCategoryZone extends StatelessWidget {
  const _SortingCategoryZone({
    required this.category,
    required this.items,
    required this.onAccept,
    required this.showIncorrectFeedback,
  });

  final String category;
  final List<GameItem> items;
  final void Function(GameItem item) onAccept;
  final bool showIncorrectFeedback;

  @override
  Widget build(BuildContext context) {
    return DragTarget<GameItem>(
      onAcceptWithDetails: (details) => onAccept(details.data),
      builder: (context, candidateData, rejectedData) {
        final hovering = candidateData.isNotEmpty;
        final borderColor = showIncorrectFeedback
            ? KidsContentColors.gameRed
            : hovering
                ? KidsContentColors.gameBlue
                : Colors.black.withAlpha(30);
        final backgroundColor = showIncorrectFeedback
            ? KidsContentColors.gameRed.withAlpha(18)
            : hovering
                ? KidsContentColors.gameBlue.withAlpha(20)
                : Colors.white;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          margin: const EdgeInsets.all(AppSpacing.sm),
          padding: const EdgeInsets.all(AppSpacing.base),
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: borderColor,
              width: hovering || showIncorrectFeedback ? 2 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                category,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              if (showIncorrectFeedback) ...<Widget>[
                const SizedBox(height: AppSpacing.xs),
                Text(
                  'Wrong zone',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: KidsContentColors.gameRed,
                        fontWeight: FontWeight.w700,
                      ),
                ),
              ],
              const SizedBox(height: AppSpacing.base),
              Expanded(
                child: SingleChildScrollView(
                  child: Wrap(
                    spacing: AppSpacing.sm,
                    runSpacing: AppSpacing.sm,
                    children: items
                        .map(
                          (item) => Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.sm,
                              vertical: AppSpacing.xs,
                            ),
                            decoration: BoxDecoration(
                              color: KidsContentColors.gameGreen.withAlpha(20),
                              borderRadius: BorderRadius.circular(999),
                              border: Border.all(
                                color: KidsContentColors.gameGreen,
                              ),
                            ),
                            child: Text(item.prompt),
                          ),
                        )
                        .toList(),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _SortingDraggableCard extends StatelessWidget {
  const _SortingDraggableCard({
    required this.item,
    this.isIncorrect = false,
  });

  final GameItem item;
  final bool isIncorrect;

  @override
  Widget build(BuildContext context) {
    final accent = _accentColor(item.accentHex);
    final child = Container(
      width: 112,
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: isIncorrect
            ? KidsContentColors.gameRed.withAlpha(12)
            : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: isIncorrect ? KidsContentColors.gameRed : Colors.black12,
          width: isIncorrect ? 2 : 1,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(
            isIncorrect ? Icons.close_rounded : Icons.drag_indicator_rounded,
            color: isIncorrect ? KidsContentColors.gameRed : accent,
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            item.prompt,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: isIncorrect ? KidsContentColors.gameRed : null,
                ),
          ),
        ],
      ),
    );

    return LongPressDraggable<GameItem>(
      data: item,
      feedback: Material(
        color: Colors.transparent,
        child: SizedBox(
          width: 120,
          child: child,
        ),
      ),
      childWhenDragging: Opacity(
        opacity: 0.35,
        child: child,
      ),
      child: child,
    );
  }

  static Color _accentColor(String? hex) {
    if (hex == null || hex.isEmpty) {
      return KidsContentColors.storyPageTurn;
    }
    final normalized = hex.replaceAll('#', '');
    try {
      return Color(int.parse('FF$normalized', radix: 16));
    } catch (_) {
      return KidsContentColors.storyPageTurn;
    }
  }
}
