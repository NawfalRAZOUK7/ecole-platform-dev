import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';
import 'package:ecole_platform/features/rewards/rewards_widgets.dart';
import 'package:ecole_platform/features/student/story_reader_provider.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/widgets/drawing_overlay.dart';

class StoryReaderScreen extends ConsumerStatefulWidget {
  final String contentItemId;
  final String? initialProgressStatus;

  const StoryReaderScreen({
    super.key,
    required this.contentItemId,
    this.initialProgressStatus,
  });

  @override
  ConsumerState<StoryReaderScreen> createState() => _StoryReaderScreenState();
}

class _StoryReaderScreenState extends ConsumerState<StoryReaderScreen> {
  final PageController _pageController = PageController();
  final Map<String, List<DrawingPath>> _drawingsByPage =
      <String, List<DrawingPath>>{};

  bool _showCelebration = false;
  bool _hasShownCelebration = false;
  int _lastNarratedPageIndex = -1;
  int _audioRequestId = 0;

  StoryReaderRequest get _request => StoryReaderRequest(
        contentItemId: widget.contentItemId,
        initialProgressStatus: widget.initialProgressStatus,
      );

  @override
  void dispose() {
    _pageController.dispose();
    unawaited(ref.read(ttsServiceProvider).stop());
    super.dispose();
  }

  Map<String, String> get _imageHeaders {
    final token = ref.read(apiClientProvider).accessToken;
    if (token == null || token.isEmpty) {
      return const <String, String>{};
    }
    return <String, String>{'Authorization': 'Bearer $token'};
  }

  Future<void> _handlePageChanged(int index) async {
    await _stopNarration();
    await ref
        .read(storyReaderProvider(_request).notifier)
        .setCurrentPageIndex(index);
  }

  Future<void> _toggleNarration(StoryReaderState storyState) async {
    if (storyState.isAudioPlaying) {
      await _stopNarration();
      return;
    }

    final page = storyState.currentPage;
    final narrationText = page?.narrationText?.trim();
    if (narrationText == null || narrationText.isEmpty) {
      return;
    }

    final requestId = ++_audioRequestId;
    final notifier = ref.read(storyReaderProvider(_request).notifier);
    notifier.setAudioPlaying(true);

    try {
      await ref.read(ttsServiceProvider).speakInstruction(narrationText);
    } finally {
      if (!mounted || requestId != _audioRequestId) {
        return;
      }
      notifier.setAudioPlaying(false);
    }
  }

  Future<void> _stopNarration() async {
    _audioRequestId++;
    await ref.read(ttsServiceProvider).stop();
    if (!mounted) {
      return;
    }
    ref.read(storyReaderProvider(_request).notifier).setAudioPlaying(false);
  }

  Future<void> _finishStory() async {
    await _stopNarration();
    await ref.read(storyReaderProvider(_request).notifier).completeStory();
    if (!mounted) {
      return;
    }
    setState(() {
      _showCelebration = true;
      _hasShownCelebration = true;
    });
  }

  Future<void> _closeReader() async {
    await _stopNarration();
    if (!mounted) {
      return;
    }
    context.pop();
  }

  void _scheduleNarration(StoryReaderState storyState) {
    if (storyState.pages.isEmpty ||
        _lastNarratedPageIndex == storyState.currentPageIndex) {
      return;
    }

    _lastNarratedPageIndex = storyState.currentPageIndex;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      unawaited(_toggleNarration(storyState));
    });
  }

  Color _accentColor(String? hex) {
    if (hex == null || hex.isEmpty) {
      return KidsContentColors.storyPageTurn;
    }

    try {
      final normalized = hex.replaceAll('#', '');
      return Color(int.parse('FF$normalized', radix: 16));
    } catch (_) {
      return KidsContentColors.storyPageTurn;
    }
  }

  @override
  Widget build(BuildContext context) {
    final storyAsync = ref.watch(storyReaderProvider(_request));

    return storyAsync.when(
      loading: () => const Scaffold(
        backgroundColor: KidsContentColors.storyBackground,
        body: Center(child: CircularProgressIndicator()),
      ),
      error: (error, _) => Scaffold(
        backgroundColor: KidsContentColors.storyBackground,
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.xl),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const Icon(Icons.error_outline, size: 56),
                const SizedBox(height: AppSpacing.base),
                Text(
                  '$error',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.base),
                FilledButton(
                  onPressed: () => ref
                      .read(storyReaderProvider(_request).notifier)
                      .refresh(),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
          ),
        ),
      ),
      data: (storyState) {
        if (storyState.pages.isNotEmpty && !_showCelebration) {
          _scheduleNarration(storyState);
        }

        final accentColor = _accentColor(storyState.contentItem.themeColor);
        final currentPage = storyState.currentPage;

        return Scaffold(
          backgroundColor: KidsContentColors.storyBackground,
          body: Column(
            children: <Widget>[
              _StoryTopBar(
                title: storyState.contentItem.title,
                accentColor: accentColor,
                currentPage: storyState.pages.isEmpty
                    ? 0
                    : storyState.currentPageIndex + 1,
                totalPages: storyState.totalPages,
                isDrawingMode: storyState.isDrawingMode,
                isAudioPlaying: storyState.isAudioPlaying,
                canReplayNarration:
                    ((currentPage?.narrationText ?? '').trim().isNotEmpty),
                onClose: _closeReader,
                onToggleDrawing: () => ref
                    .read(storyReaderProvider(_request).notifier)
                    .toggleDrawingMode(),
                onToggleNarration: () => _toggleNarration(storyState),
              ),
              Expanded(
                child: storyState.pages.isEmpty
                    ? const _EmptyStoryState()
                    : Stack(
                        fit: StackFit.expand,
                        children: <Widget>[
                          PageView.builder(
                            controller: _pageController,
                            itemCount: storyState.totalPages,
                            onPageChanged: (index) {
                              unawaited(_handlePageChanged(index));
                            },
                            itemBuilder: (context, index) {
                              final page = storyState.pages[index];
                              return _StoryPageCanvas(
                                page: page,
                                imageHeaders: _imageHeaders,
                                isDrawingMode: storyState.isDrawingMode,
                                savedPaths:
                                    _drawingsByPage[page.id] ?? const [],
                                onDrawingChanged: (paths) {
                                  _drawingsByPage[page.id] = paths;
                                },
                              );
                            },
                          ),
                          if (_showCelebration)
                            CongratsOverlay(
                              starsEarned: 3,
                              xpEarned: 50,
                              onDismiss: () {
                                setState(() => _showCelebration = false);
                              },
                            ),
                        ],
                      ),
              ),
              if (storyState.pages.isNotEmpty)
                _StoryBottomBar(
                  accentColor: accentColor,
                  progress: storyState.progress,
                  currentPage: storyState.currentPageIndex + 1,
                  totalPages: storyState.totalPages,
                  canGoBack: storyState.currentPageIndex > 0,
                  canGoForward: !storyState.isLastPage,
                  showFinishAction: !_showCelebration &&
                      storyState.isLastPage &&
                      !_hasShownCelebration &&
                      !storyState.isCompleted,
                  showQuizLink: !_showCelebration &&
                      storyState.isLastPage &&
                      storyState.hasAssociatedQuiz,
                  onBack: storyState.currentPageIndex > 0
                      ? () {
                          _pageController.previousPage(
                            duration: const Duration(milliseconds: 260),
                            curve: Curves.easeInOut,
                          );
                        }
                      : null,
                  onForward: !storyState.isLastPage
                      ? () {
                          _pageController.nextPage(
                            duration: const Duration(milliseconds: 260),
                            curve: Curves.easeInOut,
                          );
                        }
                      : null,
                  onFinish: _finishStory,
                  onOpenQuiz: storyState.hasAssociatedQuiz
                      ? () => context.push('/student/quizzes')
                      : null,
                ),
            ],
          ),
        );
      },
    );
  }
}

class _StoryTopBar extends StatelessWidget {
  final String title;
  final Color accentColor;
  final int currentPage;
  final int totalPages;
  final bool isDrawingMode;
  final bool isAudioPlaying;
  final bool canReplayNarration;
  final VoidCallback onClose;
  final VoidCallback onToggleDrawing;
  final VoidCallback onToggleNarration;

  const _StoryTopBar({
    required this.title,
    required this.accentColor,
    required this.currentPage,
    required this.totalPages,
    required this.isDrawingMode,
    required this.isAudioPlaying,
    required this.canReplayNarration,
    required this.onClose,
    required this.onToggleDrawing,
    required this.onToggleNarration,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.sm,
          AppSpacing.sm,
          AppSpacing.sm,
          AppSpacing.base,
        ),
        child: Row(
          children: <Widget>[
            IconButton.filledTonal(
              onPressed: onClose,
              icon: const Icon(Icons.close),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.sm,
                      vertical: AppSpacing.xs,
                    ),
                    decoration: BoxDecoration(
                      color: accentColor.withAlpha(32),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      '$currentPage/$totalPages',
                      style: TextStyle(
                        color: accentColor,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            IconButton.filledTonal(
              onPressed: canReplayNarration ? onToggleNarration : null,
              icon: Icon(
                isAudioPlaying
                    ? Icons.stop_circle_outlined
                    : Icons.volume_up_outlined,
              ),
            ),
            const SizedBox(width: AppSpacing.xs),
            IconButton.filledTonal(
              onPressed: onToggleDrawing,
              style: IconButton.styleFrom(
                backgroundColor:
                    isDrawingMode ? accentColor.withAlpha(38) : null,
              ),
              icon: Icon(
                isDrawingMode ? Icons.brush : Icons.brush_outlined,
                color: isDrawingMode ? accentColor : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StoryPageCanvas extends StatelessWidget {
  final ContentItemAsset page;
  final Map<String, String> imageHeaders;
  final bool isDrawingMode;
  final List<DrawingPath> savedPaths;
  final ValueChanged<List<DrawingPath>> onDrawingChanged;

  const _StoryPageCanvas({
    required this.page,
    required this.imageHeaders,
    required this.isDrawingMode,
    required this.savedPaths,
    required this.onDrawingChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: KidsContentColors.storyBackground,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.base),
      child: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          Center(
            child: Image.network(
              page.downloadUrl,
              headers: imageHeaders,
              fit: BoxFit.contain,
              errorBuilder: (_, __, ___) => const _PagePlaceholder(),
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) {
                  return child;
                }
                return const Center(child: CircularProgressIndicator());
              },
            ),
          ),
          Positioned.fill(
            child: IgnorePointer(
              ignoring: !isDrawingMode,
              child: DrawingOverlay(
                key: ValueKey<String>('drawing-${page.id}'),
                initialPaths: savedPaths,
                showControls: isDrawingMode,
                backgroundColor: KidsContentColors.storyBackground,
                onDrawingChanged: onDrawingChanged,
                child: const SizedBox.expand(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StoryBottomBar extends StatelessWidget {
  final Color accentColor;
  final double progress;
  final int currentPage;
  final int totalPages;
  final bool canGoBack;
  final bool canGoForward;
  final bool showFinishAction;
  final bool showQuizLink;
  final VoidCallback? onBack;
  final VoidCallback? onForward;
  final VoidCallback onFinish;
  final VoidCallback? onOpenQuiz;

  const _StoryBottomBar({
    required this.accentColor,
    required this.progress,
    required this.currentPage,
    required this.totalPages,
    required this.canGoBack,
    required this.canGoForward,
    required this.showFinishAction,
    required this.showQuizLink,
    this.onBack,
    this.onForward,
    required this.onFinish,
    this.onOpenQuiz,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.base,
          AppSpacing.md,
          AppSpacing.base,
          AppSpacing.base,
        ),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: Colors.black.withAlpha(20),
              blurRadius: 18,
              offset: const Offset(0, -8),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 8,
                    color: accentColor,
                    backgroundColor: accentColor.withAlpha(30),
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  '$currentPage/$totalPages',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.base),
            Row(
              children: <Widget>[
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: canGoBack ? onBack : null,
                    icon: const Icon(Icons.chevron_left),
                    label: const Text('Précédent'),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: showFinishAction ? onFinish : onForward,
                    icon: Icon(
                      showFinishAction
                          ? Icons.celebration_outlined
                          : Icons.chevron_right,
                    ),
                    label: Text(showFinishAction ? 'Terminer' : 'Suivant'),
                  ),
                ),
              ],
            ),
            if (showQuizLink && onOpenQuiz != null) ...<Widget>[
              const SizedBox(height: AppSpacing.sm),
              TextButton.icon(
                onPressed: onOpenQuiz,
                icon: const Icon(Icons.quiz_outlined),
                label: const Text('Passer au quiz'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _PagePlaceholder extends StatelessWidget {
  const _PagePlaceholder();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(
            Icons.auto_stories_outlined,
            size: 72,
            color: KidsContentColors.storyPageTurn.withAlpha(90),
          ),
          const SizedBox(height: AppSpacing.base),
          const Text('Page indisponible'),
        ],
      ),
    );
  }
}

class _EmptyStoryState extends StatelessWidget {
  const _EmptyStoryState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('Aucune page disponible pour cette histoire.'),
    );
  }
}
