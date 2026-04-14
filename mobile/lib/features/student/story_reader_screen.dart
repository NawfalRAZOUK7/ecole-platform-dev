/// Immersive story reader — page-turn UI for STORY content items.
///
/// Loads ordered pages from GET /content-items/{id}/pages, renders each page
/// as a full-screen image, and auto-narrates using TTS. Integrates with the
/// existing content progress system and exposes an [onComplete] callback.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/shared/services/tts_service.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

// ---------------------------------------------------------------------------
// Data model
// ---------------------------------------------------------------------------

class _StoryPage {
  final String assetId;
  final String? fileUrl;   // resolved from GET /content-items/{id}/assets/{assetId}
  final int pageNumber;
  final String? narrationText;
  final bool hasActivity;

  const _StoryPage({
    required this.assetId,
    required this.pageNumber,
    this.fileUrl,
    this.narrationText,
    this.hasActivity = false,
  });

  factory _StoryPage.fromJson(Map<String, dynamic> json) => _StoryPage(
        assetId: json['id'] as String,
        pageNumber: (json['page_number'] as num?)?.toInt() ?? 1,
        fileUrl: json['file_url'] as String?,
        narrationText: json['narration_text'] as String?,
        hasActivity: (json['has_activity'] as bool?) ?? false,
      );
}

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

class StoryReaderScreen extends ConsumerStatefulWidget {
  final String contentItemId;
  final String title;
  final String? themeColor;
  final VoidCallback? onComplete;

  const StoryReaderScreen({
    super.key,
    required this.contentItemId,
    required this.title,
    this.themeColor,
    this.onComplete,
  });

  @override
  ConsumerState<StoryReaderScreen> createState() => _StoryReaderScreenState();
}

class _StoryReaderScreenState extends ConsumerState<StoryReaderScreen> {
  final PageController _pageController = PageController();
  List<_StoryPage> _pages = [];
  bool _loading = true;
  String? _error;
  int _currentPage = 0;
  bool _showUi = true; // auto-hide chrome after a moment

  // Parsed theme color from hex string
  Color get _accentColor {
    final hex = widget.themeColor;
    if (hex == null) return KidsContentColors.storyPageTurn;
    try {
      return Color(int.parse('FF${hex.replaceAll('#', '')}', radix: 16));
    } catch (_) {
      return KidsContentColors.storyPageTurn;
    }
  }

  @override
  void initState() {
    super.initState();
    _loadPages();
  }

  @override
  void dispose() {
    _pageController.dispose();
    ref.read(ttsServiceProvider.notifier).stop();
    super.dispose();
  }

  Future<void> _loadPages() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final resp = await api.list('/content-items/${widget.contentItemId}/pages');
      _pages = (resp.data as List)
          .map((json) => _StoryPage.fromJson(json as Map<String, dynamic>))
          .toList()
        ..sort((a, b) => a.pageNumber.compareTo(b.pageNumber));
      setState(() => _loading = false);
      // Auto-narrate first page
      _narratePage(0);
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  void _narratePage(int index) {
    if (index >= _pages.length) return;
    final text = _pages[index].narrationText;
    if (text != null && text.isNotEmpty) {
      ref.read(ttsServiceProvider.notifier).speak(text);
    }
  }

  void _onPageChanged(int index) {
    setState(() => _currentPage = index);
    _narratePage(index);
    // Mark completed when reaching the last page
    if (index == _pages.length - 1) {
      widget.onComplete?.call();
    }
  }

  void _toggleUi() => setState(() => _showUi = !_showUi);

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        backgroundColor: KidsContentColors.storyBackground,
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.title)),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48),
              const SizedBox(height: 16),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton(onPressed: _loadPages, child: const Text('Réessayer')),
            ],
          ),
        ),
      );
    }
    if (_pages.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.title)),
        body: const Center(child: Text('Aucune page disponible')),
      );
    }

    return Scaffold(
      backgroundColor: KidsContentColors.storyBackground,
      body: GestureDetector(
        onTap: _toggleUi,
        child: Stack(
          children: [
            // Page viewer
            PageView.builder(
              controller: _pageController,
              onPageChanged: _onPageChanged,
              itemCount: _pages.length,
              itemBuilder: (context, index) {
                return _StoryPageView(page: _pages[index]);
              },
            ),

            // Top chrome — back + title
            AnimatedSlide(
              offset: _showUi ? Offset.zero : const Offset(0, -1),
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeInOut,
              child: _TopBar(
                title: widget.title,
                accentColor: _accentColor,
                currentPage: _currentPage,
                totalPages: _pages.length,
              ),
            ),

            // Bottom chrome — TTS + page indicator + prev/next
            AnimatedSlide(
              offset: _showUi ? Offset.zero : const Offset(0, 1),
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeInOut,
              child: Align(
                alignment: Alignment.bottomCenter,
                child: _BottomControls(
                  currentPage: _currentPage,
                  totalPages: _pages.length,
                  accentColor: _accentColor,
                  narrationText: _pages[_currentPage].narrationText,
                  hasActivity: _pages[_currentPage].hasActivity,
                  onPrev: _currentPage > 0
                      ? () {
                          _pageController.previousPage(
                            duration: const Duration(milliseconds: 350),
                            curve: Curves.easeInOut,
                          );
                        }
                      : null,
                  onNext: _currentPage < _pages.length - 1
                      ? () {
                          _pageController.nextPage(
                            duration: const Duration(milliseconds: 350),
                            curve: Curves.easeInOut,
                          );
                        }
                      : null,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Page view widget
// ---------------------------------------------------------------------------

class _StoryPageView extends StatelessWidget {
  final _StoryPage page;
  const _StoryPageView({required this.page});

  @override
  Widget build(BuildContext context) {
    final url = page.fileUrl;
    return Container(
      color: KidsContentColors.storyBackground,
      child: url != null
          ? Image.network(
              url,
              fit: BoxFit.contain,
              errorBuilder: (_, __, ___) => const _PagePlaceholder(),
              loadingBuilder: (_, child, progress) {
                if (progress == null) return child;
                return const Center(child: CircularProgressIndicator());
              },
            )
          : const _PagePlaceholder(),
    );
  }
}

class _PagePlaceholder extends StatelessWidget {
  const _PagePlaceholder();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.auto_stories,
              size: 80, color: KidsContentColors.storyPageTurn.withAlpha(80)),
          const SizedBox(height: 16),
          const Text('Image non disponible'),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Top bar
// ---------------------------------------------------------------------------

class _TopBar extends StatelessWidget {
  final String title;
  final Color accentColor;
  final int currentPage;
  final int totalPages;

  const _TopBar({
    required this.title,
    required this.accentColor,
    required this.currentPage,
    required this.totalPages,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm,
          vertical: AppSpacing.xs,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.black54, Colors.transparent],
          ),
        ),
        child: Row(
          children: [
            IconButton(
              icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
              onPressed: () => Navigator.of(context).pop(),
            ),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: accentColor.withAlpha(200),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${currentPage + 1} / $totalPages',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Bottom controls
// ---------------------------------------------------------------------------

class _BottomControls extends ConsumerWidget {
  final int currentPage;
  final int totalPages;
  final Color accentColor;
  final String? narrationText;
  final bool hasActivity;
  final VoidCallback? onPrev;
  final VoidCallback? onNext;

  const _BottomControls({
    required this.currentPage,
    required this.totalPages,
    required this.accentColor,
    required this.narrationText,
    required this.hasActivity,
    this.onPrev,
    this.onNext,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ttsState = ref.watch(ttsServiceProvider);
    final tts = ref.read(ttsServiceProvider.notifier);

    return Container(
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.sm, AppSpacing.sm, AppSpacing.sm, AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Colors.black54, Colors.transparent],
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Page dots
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              totalPages,
              (i) => AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: const EdgeInsets.symmetric(horizontal: 3),
                width: i == currentPage ? 20 : 8,
                height: 8,
                decoration: BoxDecoration(
                  color: i == currentPage ? accentColor : Colors.white54,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),

          // Controls row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Prev
              IconButton(
                icon: const Icon(Icons.chevron_left, size: 36, color: Colors.white),
                onPressed: onPrev,
                tooltip: 'Page précédente',
              ),

              // TTS toggle
              if (narrationText != null)
                GestureDetector(
                  onTap: () => tts.toggle(narrationText!),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                    decoration: BoxDecoration(
                      color: ttsState == TtsState.playing
                          ? accentColor
                          : Colors.white24,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          ttsState == TtsState.playing
                              ? Icons.pause
                              : Icons.volume_up,
                          color: Colors.white,
                          size: 20,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          ttsState == TtsState.playing ? 'Pause' : 'Écouter',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              else
                const SizedBox.shrink(),

              // Next / Finish
              onNext != null
                  ? IconButton(
                      icon: const Icon(Icons.chevron_right,
                          size: 36, color: Colors.white),
                      onPressed: onNext,
                      tooltip: 'Page suivante',
                    )
                  : IconButton(
                      icon:
                          Icon(Icons.check_circle, size: 36, color: accentColor),
                      onPressed: () => Navigator.of(context).pop(),
                      tooltip: 'Terminer',
                    ),
            ],
          ),
        ],
      ),
    );
  }
}
