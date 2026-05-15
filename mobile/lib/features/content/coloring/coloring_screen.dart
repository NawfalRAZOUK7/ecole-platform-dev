import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/content/coloring/coloring_provider.dart';
import 'package:ecole_platform/features/ai/rewards/rewards_provider.dart';
import 'package:ecole_platform/shared/ui/widgets/animated_guide.dart';
import 'package:ecole_platform/shared/ui/widgets/color_picker_palette.dart';
import 'package:ecole_platform/shared/ui/widgets/drawing_overlay.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';
import 'package:ecole_platform/shared/widgets/signed_network_image.dart';

const List<Color> _extendedColoringPalette = <Color>[
  ...kidFriendlyColorPalette,
  Color(0xFFFF6B6B),
  Color(0xFFFF9F1C),
  Color(0xFFFFD166),
  Color(0xFF06D6A0),
  Color(0xFF118AB2),
  Color(0xFF073B4C),
  Color(0xFF9B5DE5),
  Color(0xFFF15BB5),
  Color(0xFF00BBF9),
  Color(0xFF00F5D4),
];

enum _ExitChoice {
  save,
  discard,
  cancel,
}

class ColoringScreen extends ConsumerStatefulWidget {
  const ColoringScreen({
    super.key,
    required this.pageId,
  });

  final String pageId;

  @override
  ConsumerState<ColoringScreen> createState() => _ColoringScreenState();
}

class _ColoringScreenState extends ConsumerState<ColoringScreen> {
  final GlobalKey _canvasKey = GlobalKey();
  bool _hasUnsavedChanges = false;
  bool _saving = false;
  bool _rewardAwarded = false;
  bool _forcePop = false;
  double _uploadProgress = 0;
  String? _lastSavedDocumentId;

  @override
  Widget build(BuildContext context) {
    final pageAsync = ref.watch(coloringPageProvider(widget.pageId));

    return PopScope(
      canPop: _forcePop || (!_saving && !_hasUnsavedChanges),
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) {
          return;
        }
        final shouldLeave = await _handleBackNavigation();
        if (!shouldLeave || !context.mounted) {
          return;
        }
        setState(() => _forcePop = true);
        Navigator.of(context).pop(result);
      },
      child: Scaffold(
        appBar: AppBar(
          title: pageAsync.when(
            data: (page) => Text(page?.title ?? 'Coloring'),
            loading: () => const Text('Coloring'),
            error: (_, __) => const Text('Coloring'),
          ),
          actions: <Widget>[
            if (_saving)
              Padding(
                padding: const EdgeInsets.all(AppSpacing.base),
                child: Center(
                  child: Text(
                    '${(_uploadProgress * 100).round()}%',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                ),
              )
            else
              IconButton(
                onPressed: () => _saveColoring(),
                tooltip: 'Save drawing',
                icon: Icon(
                  _hasUnsavedChanges ? Icons.save_outlined : Icons.check_circle,
                  color:
                      _hasUnsavedChanges ? null : KidsContentColors.gameGreen,
                ),
              ),
          ],
        ),
        body: pageAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => AppErrorWidget(
            message: '$error',
            onRetry: () => ref.invalidate(coloringPageProvider(widget.pageId)),
          ),
          data: (page) {
            if (page == null) {
              return AppErrorWidget(
                message: 'Coloring page not found.',
                onRetry: () async {
                  await ref.read(coloringProvider.notifier).refresh();
                  ref.invalidate(coloringPageProvider(widget.pageId));
                },
              );
            }

            final guideState = _lastSavedDocumentId == null
                ? AnimatedGuideState.happy
                : AnimatedGuideState.celebrating;
            final guideMessage =
                _lastSavedDocumentId == null ? 'لون كما تحب!' : 'لوحة جميلة!';
            final guideImageUrl = ref.watch(samiGuideImageProvider(guideState));

            return Column(
              children: <Widget>[
                if (_saving)
                  LinearProgressIndicator(
                    value: _uploadProgress > 0 ? _uploadProgress : null,
                    minHeight: 4,
                    color: KidsContentColors.storyPageTurn,
                    backgroundColor:
                        KidsContentColors.storyPageTurn.withAlpha(28),
                  ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.base,
                    AppSpacing.base,
                    AppSpacing.base,
                    0,
                  ),
                  child: AnimatedGuide(
                    message: guideMessage,
                    state: guideState,
                    imageUrl: guideImageUrl,
                    size: 72,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.base,
                    AppSpacing.sm,
                    AppSpacing.base,
                    AppSpacing.sm,
                  ),
                  child: _HeaderCard(
                    title: page.contentTitle,
                    pageLabel: page.asset.pageNumber == null
                        ? 'Coloring page'
                        : 'Page ${page.asset.pageNumber}',
                    hasUnsavedChanges: _hasUnsavedChanges,
                    lastSavedDocumentId: _lastSavedDocumentId,
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(
                      AppSpacing.base,
                      0,
                      AppSpacing.base,
                      AppSpacing.base,
                    ),
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(28),
                        boxShadow: <BoxShadow>[
                          BoxShadow(
                            color: Colors.black.withAlpha(18),
                            blurRadius: 24,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(28),
                        child: RepaintBoundary(
                          key: _canvasKey,
                          child: Stack(
                            fit: StackFit.expand,
                            children: <Widget>[
                              Container(
                                color: KidsContentColors.canvasBackground,
                              ),
                              SignedNetworkImage(
                                path: page.imageUrl,
                                fit: BoxFit.contain,
                                errorBuilder: (_, __, ___) =>
                                    const _TemplateUnavailable(),
                                loadingBuilder:
                                    (context, child, loadingProgress) {
                                  if (loadingProgress == null) {
                                    return child;
                                  }
                                  return const Center(
                                    child: CircularProgressIndicator(),
                                  );
                                },
                              ),
                              Positioned.fill(
                                child: DrawingOverlay(
                                  backgroundColor: Colors.transparent,
                                  colorPalette: _extendedColoringPalette,
                                  initialColor: _extendedColoringPalette.first,
                                  onDrawingChanged: (paths) {
                                    if (!mounted) {
                                      return;
                                    }
                                    final changed = paths.isNotEmpty;
                                    if (changed == _hasUnsavedChanges) {
                                      return;
                                    }
                                    setState(
                                      () => _hasUnsavedChanges = changed,
                                    );
                                  },
                                  child: const SizedBox.expand(),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Future<bool> _handleBackNavigation() async {
    if (_saving) {
      return false;
    }
    if (!_hasUnsavedChanges) {
      return true;
    }

    final choice = await showDialog<_ExitChoice>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Save changes?'),
          content: const Text(
            'Your drawing has unsaved changes. Save it before leaving?',
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(_ExitChoice.cancel),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(_ExitChoice.discard),
              child: const Text('Discard'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(_ExitChoice.save),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    switch (choice) {
      case _ExitChoice.save:
        return _saveColoring(showSavedMessage: true);
      case _ExitChoice.discard:
        return true;
      case _ExitChoice.cancel:
      case null:
        return false;
    }
  }

  Future<bool> _saveColoring({bool showSavedMessage = true}) async {
    if (_saving) {
      return false;
    }

    final page = await ref.read(coloringPageProvider(widget.pageId).future);
    if (page == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Coloring page not found.')),
        );
      }
      return false;
    }

    setState(() {
      _saving = true;
      _uploadProgress = 0;
    });

    try {
      final bytes = await _captureCanvasImage();
      if (bytes == null) {
        throw StateError('Unable to export coloring image.');
      }

      final file = await _writeTempImage(bytes, page.id);
      final currentUser = ref.read(authProvider).user;
      final studentId = currentUser?.role == 'STD' ? currentUser?.id : null;
      final uploaded =
          await ref.read(documentRepositoryProvider).uploadDocument(
                file: file,
                category: 'other',
                linkedStudentId: studentId,
                onProgress: (sent, total) {
                  if (!mounted || total <= 0) {
                    return;
                  }
                  setState(() {
                    _uploadProgress = sent / total;
                  });
                },
              );

      if (!_rewardAwarded && studentId != null) {
        await ref.read(rewardsProvider.notifier).awardEvent(
              eventType: 'coloring_completed',
              starsEarned: 5,
              xpEarned: 50,
              sourceType: 'coloring',
              sourceId: page.id,
            );
        _rewardAwarded = true;
      }

      if (!mounted) {
        return false;
      }
      setState(() {
        _hasUnsavedChanges = false;
        _saving = false;
        _uploadProgress = 0;
        _lastSavedDocumentId = uploaded.id;
      });
      if (showSavedMessage) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Coloring saved and rewarded.')),
        );
      }
      return true;
    } catch (error) {
      if (!mounted) {
        return false;
      }
      setState(() {
        _saving = false;
        _uploadProgress = 0;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
      return false;
    }
  }

  Future<Uint8List?> _captureCanvasImage() async {
    final boundaryContext = _canvasKey.currentContext;
    if (boundaryContext == null) {
      return null;
    }

    final boundary =
        boundaryContext.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) {
      return null;
    }

    final image = await boundary.toImage(pixelRatio: 3);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    return bytes?.buffer.asUint8List();
  }

  Future<File> _writeTempImage(Uint8List bytes, String pageId) async {
    final directory = await getTemporaryDirectory();
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final file = File('${directory.path}/coloring-$pageId-$timestamp.png');
    await file.writeAsBytes(bytes, flush: true);
    return file;
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({
    required this.title,
    required this.pageLabel,
    required this.hasUnsavedChanges,
    required this.lastSavedDocumentId,
  });

  final String title;
  final String pageLabel;
  final bool hasUnsavedChanges;
  final String? lastSavedDocumentId;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Row(
          children: <Widget>[
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: KidsContentColors.storyBackground,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.palette_outlined),
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
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    pageLabel,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.sm,
                vertical: AppSpacing.xs,
              ),
              decoration: BoxDecoration(
                color: hasUnsavedChanges
                    ? KidsContentColors.gameYellow.withAlpha(36)
                    : KidsContentColors.gameGreen.withAlpha(20),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                hasUnsavedChanges
                    ? 'Unsaved'
                    : lastSavedDocumentId == null
                        ? 'Ready'
                        : 'Saved',
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TemplateUnavailable extends StatelessWidget {
  const _TemplateUnavailable();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          Icon(
            Icons.image_not_supported_outlined,
            size: 56,
            color: KidsContentColors.storyPageTurn.withAlpha(120),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            'Template unavailable',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}
