import 'dart:async';

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
import 'package:ecole_platform/shared/widgets/signed_network_image.dart';

class VocabularyCardsScreen extends ConsumerStatefulWidget {
  const VocabularyCardsScreen({super.key});

  @override
  ConsumerState<VocabularyCardsScreen> createState() =>
      _VocabularyCardsScreenState();
}

class _VocabularyCardsScreenState extends ConsumerState<VocabularyCardsScreen> {
  bool _rewardAwarded = false;
  bool _showCelebration = false;

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<GameSessionState>>(
      gameProvider(GameType.vocabulary),
      (previous, next) {
        final nextState = next.valueOrNull;
        final wasCompleted = previous?.valueOrNull?.isCompleted ?? false;
        if (nextState != null && nextState.isCompleted && !wasCompleted) {
          unawaited(_handleCompleted(nextState));
        }
      },
    );

    final sessionAsync = ref.watch(gameProvider(GameType.vocabulary));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Vocabulary Cards'),
      ),
      body: sessionAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(
          message: '$error',
          onRetry: () =>
              ref.read(gameProvider(GameType.vocabulary).notifier).resetGame(),
        ),
        data: (session) {
          final current = session.currentVocabularyItem;
          if (current == null) {
            return const SizedBox.shrink();
          }

          return Stack(
            children: <Widget>[
              Column(
                children: <Widget>[
                  Padding(
                    padding: const EdgeInsets.all(AppSpacing.base),
                    child: Row(
                      children: <Widget>[
                        _InfoPill(
                          icon: Icons.visibility_outlined,
                          label:
                              '${session.vocabularyIndex + 1}/${session.config.items.length}',
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        _InfoPill(
                          icon: Icons.thumb_up_alt_outlined,
                          label: '${session.knownCount} known',
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        _InfoPill(
                          icon: Icons.help_outline_rounded,
                          label: '${session.unknownCount} review',
                        ),
                      ],
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: AppSpacing.base),
                    child: Text(
                      'Tap the card to flip it. Swipe right if you know it, left if you do not.',
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.base),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(AppSpacing.base),
                      child: Dismissible(
                        key: ValueKey<String>(
                            '${current.id}:${session.vocabularyShowingBack}'),
                        direction: DismissDirection.horizontal,
                        background: const _SwipeBackground(
                          alignment: Alignment.centerLeft,
                          color: KidsContentColors.gameGreen,
                          icon: Icons.check_circle_outline_rounded,
                          label: 'Known',
                        ),
                        secondaryBackground: const _SwipeBackground(
                          alignment: Alignment.centerRight,
                          color: KidsContentColors.gameRed,
                          icon: Icons.refresh_rounded,
                          label: 'Unknown',
                        ),
                        onDismissed: (direction) {
                          ref
                              .read(gameProvider(GameType.vocabulary).notifier)
                              .classifyVocabularyCard(
                                direction == DismissDirection.startToEnd,
                              );
                        },
                        child: _VocabularyCard(
                          item: current,
                          showBack: session.vocabularyShowingBack,
                          onFlip: () {
                            ref
                                .read(
                                    gameProvider(GameType.vocabulary).notifier)
                                .flipVocabularyCard();
                            if (!session.vocabularyShowingBack) {
                              unawaited(_speak(current.ttsText));
                            }
                          },
                          onSpeak: () => _speak(current.ttsText),
                        ),
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(
                      AppSpacing.base,
                      0,
                      AppSpacing.base,
                      AppSpacing.base,
                    ),
                    child: Row(
                      children: <Widget>[
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () => ref
                                .read(
                                    gameProvider(GameType.vocabulary).notifier)
                                .classifyVocabularyCard(false),
                            icon: const Icon(Icons.arrow_back_rounded),
                            label: const Text('Unknown'),
                          ),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: FilledButton.icon(
                            onPressed: () => ref
                                .read(
                                    gameProvider(GameType.vocabulary).notifier)
                                .classifyVocabularyCard(true),
                            icon: const Icon(Icons.arrow_forward_rounded),
                            label: const Text('Known'),
                          ),
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

  Future<void> _speak(String text) async {
    if (text.runes.length == 1) {
      await ref.read(ttsServiceProvider).speakLetter(text);
      return;
    }
    await ref.read(ttsServiceProvider).speakText(text);
  }
}

class _InfoPill extends StatelessWidget {
  const _InfoPill({
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

class _SwipeBackground extends StatelessWidget {
  const _SwipeBackground({
    required this.alignment,
    required this.color,
    required this.icon,
    required this.label,
  });

  final Alignment alignment;
  final Color color;
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      alignment: alignment,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
      decoration: BoxDecoration(
        color: color.withAlpha(24),
        borderRadius: BorderRadius.circular(32),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, color: color),
          const SizedBox(width: AppSpacing.xs),
          Text(label, style: TextStyle(color: color)),
        ],
      ),
    );
  }
}

class _VocabularyCard extends StatelessWidget {
  const _VocabularyCard({
    required this.item,
    required this.showBack,
    required this.onFlip,
    required this.onSpeak,
  });

  final GameItem item;
  final bool showBack;
  final VoidCallback onFlip;
  final VoidCallback onSpeak;

  @override
  Widget build(BuildContext context) {
    final accent = _accentColor(item.accentHex);
    return GestureDetector(
      onTap: onFlip,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 280),
        switchInCurve: Curves.easeOutBack,
        switchOutCurve: Curves.easeIn,
        child: showBack
            ? Container(
                key: ValueKey<String>('back:${item.id}'),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(32),
                  border: Border.all(color: accent, width: 2),
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: accent.withAlpha(24),
                      blurRadius: 16,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: <Widget>[
                      Expanded(
                        child: item.imageUrl != null
                            ? ClipRRect(
                                borderRadius: BorderRadius.circular(24),
                                child: SignedNetworkImage(
                                  path: item.imageUrl!,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) =>
                                      _ImageFallback(label: item.answer),
                                ),
                              )
                            : _ImageFallback(label: item.answer),
                      ),
                      const SizedBox(height: AppSpacing.base),
                      Text(
                        item.answer,
                        textAlign: TextAlign.center,
                        style:
                            Theme.of(context).textTheme.headlineSmall?.copyWith(
                                  fontWeight: FontWeight.w900,
                                ),
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      OutlinedButton.icon(
                        onPressed: onSpeak,
                        icon: const Icon(Icons.volume_up_outlined),
                        label: const Text('Listen'),
                      ),
                    ],
                  ),
                ),
              )
            : Container(
                key: ValueKey<String>('front:${item.id}'),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: <Color>[
                      accent,
                      KidsContentColors.gameBlue,
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(32),
                ),
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.xl),
                    child: Text(
                      item.prompt,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.displaySmall?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                  ),
                ),
              ),
      ),
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

class _ImageFallback extends StatelessWidget {
  const _ImageFallback({
    required this.label,
  });

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: KidsContentColors.storyBackground,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Center(
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w900,
                color: KidsContentColors.storyText,
              ),
        ),
      ),
    );
  }
}
