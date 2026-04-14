import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

enum AnimatedGuideState {
  happy,
  thinking,
  celebrating,
}

final samiGuideImagesProvider =
    FutureProvider<Map<AnimatedGuideState, String>>((ref) async {
  final repo = ref.read(contentRepositoryProvider);
  final api = ref.read(apiClientProvider);
  final items = <ContentItem>[];
  String? cursor;
  var hasMore = true;

  while (hasMore) {
    final page = await repo.getContentItems(
      cursor: cursor,
      contentType: 'mascot_asset',
    );
    items.addAll(page.items);
    cursor = page.nextCursor;
    hasMore = page.hasMore && cursor != null;
  }

  if (items.isEmpty) {
    return const <AnimatedGuideState, String>{};
  }

  final fallback = items.first;
  return <AnimatedGuideState, String>{
    for (final state in AnimatedGuideState.values)
      state: api.resolveUrl(
        '/content-items/${(_matchGuideItem(items, state) ?? fallback).id}/stream',
      ),
  };
});

final samiGuideImageProvider =
    Provider.family<String, AnimatedGuideState>((ref, state) {
  final images = ref.watch(samiGuideImagesProvider).valueOrNull;
  if (images == null || images.isEmpty) {
    return '';
  }
  return images[state] ?? images.values.first;
});

ContentItem? _matchGuideItem(
  List<ContentItem> items,
  AnimatedGuideState state,
) {
  final keywords = switch (state) {
    AnimatedGuideState.happy => <String>[
        'happy',
        'smile',
        'joy',
        'سعيد',
        'فرح',
      ],
    AnimatedGuideState.thinking => <String>[
        'thinking',
        'think',
        'question',
        'idea',
        'تفكير',
        'فكرة',
      ],
    AnimatedGuideState.celebrating => <String>[
        'celebrate',
        'celebrating',
        'party',
        'confetti',
        'win',
        'احتفال',
        'نجاح',
      ],
  };

  for (final item in items) {
    final title = item.title.toLowerCase();
    if (keywords.any(title.contains)) {
      return item;
    }
  }
  return null;
}

class AnimatedGuide extends StatefulWidget {
  const AnimatedGuide({
    super.key,
    required this.message,
    required this.state,
    required this.imageUrl,
    this.size = 84,
  });

  final String message;
  final AnimatedGuideState state;
  final String imageUrl;
  final double size;

  @override
  State<AnimatedGuide> createState() => _AnimatedGuideState();
}

class _AnimatedGuideState extends State<AnimatedGuide>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _bounce;
  String _lastSpokenMessage = '';

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 720),
    );
    _bounce = CurvedAnimation(
      parent: _controller,
      curve: Curves.elasticOut,
    );
    _controller.forward(from: 0);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(_speakMessage(force: true));
    });
  }

  @override
  void didUpdateWidget(covariant AnimatedGuide oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.state != widget.state ||
        oldWidget.imageUrl != widget.imageUrl) {
      _controller.forward(from: 0);
    }
    if (oldWidget.message != widget.message) {
      unawaited(_speakMessage(force: true));
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _speakMessage({bool force = false}) async {
    final message = widget.message.trim();
    if (message.isEmpty) {
      return;
    }
    if (!force && message == _lastSpokenMessage) {
      return;
    }
    if (!mounted) {
      return;
    }
    _lastSpokenMessage = message;
    final container = ProviderScope.containerOf(context, listen: false);
    await container.read(ttsServiceProvider).speakText(message);
  }

  Color get _bubbleColor => switch (widget.state) {
        AnimatedGuideState.happy => KidsContentColors.samiBubble,
        AnimatedGuideState.thinking => const Color(0xFFFFFBEB),
        AnimatedGuideState.celebrating => const Color(0xFFFFF7CC),
      };

  Color get _bubbleBorderColor => switch (widget.state) {
        AnimatedGuideState.happy => KidsContentColors.samiBubbleBorder,
        AnimatedGuideState.thinking => const Color(0xFFFBBF24),
        AnimatedGuideState.celebrating => const Color(0xFFF59E0B),
      };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        GestureDetector(
          onTap: () => unawaited(_speakMessage(force: true)),
          child: AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              final bounceValue = _bounce.value;
              final baseScale = _lerp(0.8, 1.0, bounceValue);
              final scale = widget.state == AnimatedGuideState.celebrating
                  ? baseScale + (1 - bounceValue) * 0.1
                  : baseScale;
              final rotation = widget.state == AnimatedGuideState.celebrating
                  ? math.sin(bounceValue * math.pi * 3) * 0.08
                  : widget.state == AnimatedGuideState.thinking
                      ? -0.04 * (1 - bounceValue)
                      : 0.0;
              return Transform.translate(
                offset: Offset(0, _lerp(widget.size * 0.18, 0, bounceValue)),
                child: Transform.rotate(
                  angle: rotation,
                  child: Transform.scale(
                    scale: scale,
                    child: child,
                  ),
                ),
              );
            },
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 320),
              switchInCurve: Curves.easeOutBack,
              switchOutCurve: Curves.easeIn,
              child: _GuideImage(
                key:
                    ValueKey<String>('${widget.state.name}:${widget.imageUrl}'),
                imageUrl: widget.imageUrl,
                size: widget.size,
              ),
            ),
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: Stack(
            clipBehavior: Clip.none,
            children: <Widget>[
              Positioned(
                left: -7,
                bottom: 18,
                child: Transform.rotate(
                  angle: math.pi / 4,
                  child: Container(
                    width: 16,
                    height: 16,
                    decoration: BoxDecoration(
                      color: _bubbleColor,
                      border: Border.all(
                        color: _bubbleBorderColor,
                        width: 1.5,
                      ),
                    ),
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.sm,
                ),
                decoration: BoxDecoration(
                  color: _bubbleColor,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: _bubbleBorderColor,
                    width: 1.5,
                  ),
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: KidsContentColors.samiPrimary.withAlpha(24),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Text(
                  widget.message,
                  textAlign: TextAlign.start,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: KidsContentColors.storyText,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  double _lerp(num start, num end, double t) {
    return start + (end - start) * t;
  }
}

class _GuideImage extends StatelessWidget {
  const _GuideImage({
    super.key,
    required this.imageUrl,
    required this.size,
  });

  final String imageUrl;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(size * 0.32),
        border: Border.all(
          color: KidsContentColors.samiBubbleBorder,
          width: 2,
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withAlpha(16),
            blurRadius: 14,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(size * 0.28),
        child: imageUrl.isEmpty
            ? const _GuidePlaceholder()
            : Image.network(
                imageUrl,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const _GuidePlaceholder(),
                loadingBuilder: (context, child, loadingProgress) {
                  if (loadingProgress == null) {
                    return child;
                  }
                  return const Center(
                    child: CircularProgressIndicator(strokeWidth: 2),
                  );
                },
              ),
      ),
    );
  }
}

class _GuidePlaceholder extends StatelessWidget {
  const _GuidePlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: KidsContentColors.storyBackground,
      child: const Center(
        child: Icon(
          Icons.emoji_emotions_outlined,
          color: KidsContentColors.samiPrimary,
          size: 38,
        ),
      ),
    );
  }
}
