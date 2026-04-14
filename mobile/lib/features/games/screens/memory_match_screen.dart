import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/games/game_provider.dart';
import 'package:ecole_platform/features/games/models/game_config.dart';
import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/rewards/rewards_widgets.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';

class MemoryMatchScreen extends ConsumerStatefulWidget {
  const MemoryMatchScreen({super.key});

  @override
  ConsumerState<MemoryMatchScreen> createState() => _MemoryMatchScreenState();
}

class _MemoryMatchScreenState extends ConsumerState<MemoryMatchScreen> {
  bool _rewardAwarded = false;
  bool _showCelebration = false;

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<GameSessionState>>(
      gameProvider(GameType.memoryMatch),
      (previous, next) {
        final nextState = next.valueOrNull;
        final wasCompleted = previous?.valueOrNull?.isCompleted ?? false;
        if (nextState != null && nextState.isCompleted && !wasCompleted) {
          unawaited(_handleCompleted(nextState));
        }
      },
    );

    final sessionAsync = ref.watch(gameProvider(GameType.memoryMatch));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Memory Match'),
      ),
      body: sessionAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(
          message: '$error',
          onRetry: () =>
              ref.read(gameProvider(GameType.memoryMatch).notifier).resetGame(),
        ),
        data: (session) {
          final crossAxisCount =
              session.visibleMemoryCards.length <= 12 ? 3 : 4;
          return Stack(
            children: <Widget>[
              Column(
                children: <Widget>[
                  Padding(
                    padding: const EdgeInsets.all(AppSpacing.base),
                    child: _GameStatsRow(
                      elapsedSeconds: session.elapsedSeconds,
                      moveCount: session.moveCount,
                      progressLabel:
                          '${session.matchedPairCount}/${session.config.items.length} pairs',
                      onReplay: _reset,
                    ),
                  ),
                  Expanded(
                    child: GridView.builder(
                      padding: const EdgeInsets.fromLTRB(
                        AppSpacing.base,
                        0,
                        AppSpacing.base,
                        AppSpacing.base,
                      ),
                      itemCount: session.visibleMemoryCards.length,
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: crossAxisCount,
                        crossAxisSpacing: AppSpacing.md,
                        mainAxisSpacing: AppSpacing.md,
                        childAspectRatio: crossAxisCount == 3 ? 0.78 : 0.88,
                      ),
                      itemBuilder: (context, index) {
                        final card = session.visibleMemoryCards[index];
                        return _MemoryFlipCard(
                          card: card,
                          imageHeaders: _imageHeaders,
                          onTap: () => _flipCard(card),
                        );
                      },
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

  Map<String, String> get _imageHeaders {
    final token = ref.read(apiClientProvider).accessToken;
    if (token == null || token.isEmpty) {
      return const <String, String>{};
    }
    return <String, String>{'Authorization': 'Bearer $token'};
  }

  Future<void> _handleCompleted(GameSessionState session) async {
    if (_rewardAwarded) {
      return;
    }
    _rewardAwarded = true;
    if (mounted) {
      setState(() => _showCelebration = true);
    }
    unawaited(ref.read(ttsServiceProvider).speakPraise());
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
    ref.read(gameProvider(GameType.memoryMatch).notifier).resetGame();
  }

  void _flipCard(MemoryCardState card) {
    if (!card.isFaceUp && !card.isMatched) {
      if (card.ttsText.runes.length == 1) {
        unawaited(ref.read(ttsServiceProvider).speakLetter(card.ttsText));
      } else {
        unawaited(ref.read(ttsServiceProvider).speakText(card.ttsText));
      }
    }
    ref
        .read(gameProvider(GameType.memoryMatch).notifier)
        .flipMemoryCard(card.id);
  }
}

class _GameStatsRow extends StatelessWidget {
  const _GameStatsRow({
    required this.elapsedSeconds,
    required this.moveCount,
    required this.progressLabel,
    required this.onReplay,
  });

  final int elapsedSeconds;
  final int moveCount;
  final String progressLabel;
  final VoidCallback onReplay;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        _MetricChip(
          icon: Icons.timer_outlined,
          label: _formatDuration(elapsedSeconds),
        ),
        const SizedBox(width: AppSpacing.sm),
        _MetricChip(
          icon: Icons.swipe_outlined,
          label: '$moveCount moves',
        ),
        const SizedBox(width: AppSpacing.sm),
        _MetricChip(
          icon: Icons.auto_awesome_rounded,
          label: progressLabel,
        ),
        const Spacer(),
        FilledButton.tonalIcon(
          onPressed: onReplay,
          icon: const Icon(Icons.replay),
          label: const Text('Replay'),
        ),
      ],
    );
  }

  static String _formatDuration(int seconds) {
    final minutes = seconds ~/ 60;
    final remaining = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${remaining.toString().padLeft(2, '0')}';
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip({
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

class _MemoryFlipCard extends StatefulWidget {
  const _MemoryFlipCard({
    required this.card,
    required this.imageHeaders,
    required this.onTap,
  });

  final MemoryCardState card;
  final Map<String, String> imageHeaders;
  final VoidCallback onTap;

  @override
  State<_MemoryFlipCard> createState() => _MemoryFlipCardState();
}

class _MemoryFlipCardState extends State<_MemoryFlipCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 380),
      value: widget.card.isFaceUp || widget.card.isMatched ? 1 : 0,
    );
  }

  @override
  void didUpdateWidget(covariant _MemoryFlipCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    final shouldShowFront = widget.card.isFaceUp || widget.card.isMatched;
    if (shouldShowFront) {
      _controller.forward();
    } else {
      _controller.reverse();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          final angle = _controller.value * pi;
          final showFront = angle > pi / 2;
          return Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.001)
              ..rotateY(angle),
            child: showFront
                ? Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()..rotateY(pi),
                    child: _CardFaceFront(
                      card: widget.card,
                      imageHeaders: widget.imageHeaders,
                    ),
                  )
                : const _CardFaceBack(),
          );
        },
      ),
    );
  }
}

class _CardFaceBack extends StatelessWidget {
  const _CardFaceBack();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: <Color>[
            KidsContentColors.gameCardBack,
            KidsContentColors.gameBlue,
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: BorderRadius.circular(22),
      ),
      child: const Center(
        child: Icon(
          Icons.question_mark_rounded,
          color: Colors.white,
          size: 42,
        ),
      ),
    );
  }
}

class _CardFaceFront extends StatelessWidget {
  const _CardFaceFront({
    required this.card,
    required this.imageHeaders,
  });

  final MemoryCardState card;
  final Map<String, String> imageHeaders;

  @override
  Widget build(BuildContext context) {
    final accent = _parseColor(card.accentHex);
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(
          color: card.isMatched ? KidsContentColors.gameGreen : accent,
          width: 2,
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: accent.withAlpha(25),
            blurRadius: 14,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: card.faceKind == MemoryCardFaceKind.answer &&
                card.imageUrl != null &&
                card.imageUrl!.isNotEmpty
            ? ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.network(
                  card.imageUrl!,
                  fit: BoxFit.cover,
                  headers: imageHeaders,
                  errorBuilder: (_, __, ___) => _FrontLabel(label: card.label),
                ),
              )
            : _FrontLabel(label: card.label),
      ),
    );
  }

  static Color _parseColor(String? hex) {
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

class _FrontLabel extends StatelessWidget {
  const _FrontLabel({
    required this.label,
  });

  final String label;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        label,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w900,
              color: KidsContentColors.storyText,
            ),
      ),
    );
  }
}
