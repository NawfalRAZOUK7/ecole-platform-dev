/// Student content screen — view assigned content by class/subject.
/// In-app video player, PDF viewer, audio player, progress tracking.
///
/// Phase 10C: Mirrors web ContentViewPage.tsx (Phase 10B).
/// API: GET /classes/{classId}/content, POST /content-items/{id}/progress

import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:just_audio/just_audio.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf_render/pdf_render_widgets.dart';
import 'package:video_player/video_player.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/lms/quiz.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/widgets/animated_guide.dart';
import 'package:ecole_platform/shared/ui/widgets/kids_skeleton_layouts.dart';
import 'package:ecole_platform/shared/widgets/app_empty_state.dart';
import 'package:ecole_platform/shared/services/offline_content_manager.dart';

class StudentContentScreen extends ConsumerStatefulWidget {
  const StudentContentScreen({super.key});

  @override
  ConsumerState<StudentContentScreen> createState() =>
      _StudentContentScreenState();
}

class _StudentContentScreenState extends ConsumerState<StudentContentScreen> {
  List<AssignedContent> _items = [];
  bool _loading = true;
  String? _error;
  AssignedContent? _selectedItem;

  @override
  void initState() {
    super.initState();
    _fetchContent();
  }

  Future<void> _fetchContent() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // Student gets content from their enrolled classes
      // Use a default class endpoint that returns all assigned content
      final api = ref.read(apiClientProvider);
      final resp = await api.list('/student/content');
      _items = resp.data
          .map(
            (json) => AssignedContent(
              id: json['id'] as String,
              contentItemId:
                  json['content_item_id'] as String? ?? json['id'] as String,
              title: json['title'] as String,
              contentType: json['content_type'] as String,
              subject: json['subject'] as String?,
              description: json['description'] as String?,
              progress: json['progress'] as String?,
              streamUrl: json['stream_url'] as String?,
              themeColor: json['theme_color'] as String?,
            ),
          )
          .toList();
      setState(() => _loading = false);
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _updateProgress(String contentItemId, String progress) async {
    try {
      final repo = ref.read(contentLibraryRepositoryProvider);
      await repo.updateProgress(contentItemId, progress);
      // Update local state
      setState(() {
        _items = _items.map((item) {
          if (item.contentItemId == contentItemId) {
            return AssignedContent(
              id: item.id,
              contentItemId: item.contentItemId,
              title: item.title,
              contentType: item.contentType,
              subject: item.subject,
              description: item.description,
              progress: progress,
              streamUrl: item.streamUrl,
              themeColor: item.themeColor,
            );
          }
          return item;
        }).toList();
      });
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    if (_selectedItem != null) {
      return _ContentPlayer(
        item: _selectedItem!,
        onBack: () => setState(() => _selectedItem = null),
        onProgress: (progress) =>
            _updateProgress(_selectedItem!.contentItemId, progress),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mon contenu'),
        actions: [
          IconButton(
            onPressed: () => context.push('/rewards'),
            icon: const Icon(Icons.auto_awesome_rounded),
            tooltip: 'Recompenses',
          ),
        ],
      ),
      body: Semantics(
        container: true,
        label: 'Contenu pédagogique de l’élève',
        child: _buildBody(context),
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    final theme = Theme.of(context);
    final guideImageUrl = ref.watch(
      samiGuideImageProvider(AnimatedGuideState.happy),
    );

    if (_loading) {
      return const ContentListSkeleton();
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: _fetchContent,
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }
    if (_items.isEmpty) {
      return const AppEmptyState(
        icon: Icons.menu_book_outlined,
        title: 'لا توجد دروس بعد',
        subtitle: 'سيضيف معلمك محتوى قريباً',
      );
    }

    // Group by subject
    final grouped = <String, List<AssignedContent>>{};
    for (final item in _items) {
      final key = item.subject ?? 'Général';
      grouped.putIfAbsent(key, () => []);
      grouped[key]!.add(item);
    }

    return RefreshIndicator(
      onRefresh: _fetchContent,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AnimatedGuide(
            message: 'مرحبًا! هيا نتعلم معًا!',
            state: AnimatedGuideState.happy,
            imageUrl: guideImageUrl,
            size: 74,
          ),
          const SizedBox(height: AppSpacing.base),
          ...grouped.entries.map((entry) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    entry.key,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                ...entry.value.map(
                  (item) => _ContentCard(
                    item: item,
                    onTap: () async {
                      if (item.progress == null ||
                          item.progress == 'not_started') {
                        await _updateProgress(
                          item.contentItemId,
                          'in_progress',
                        );
                      }
                      if (!context.mounted) {
                        return;
                      }
                      // STORY content gets its own immersive reader
                      if (item.contentType.toUpperCase() == 'STORY') {
                        final storyRoute = Uri(
                          path: '/student/content/${item.contentItemId}/read',
                          queryParameters: item.progress == null
                              ? null
                              : <String, String>{'progress': item.progress!},
                        ).toString();
                        await context.push(storyRoute);
                        if (mounted) {
                          await _fetchContent();
                        }
                        return;
                      }
                      setState(() => _selectedItem = item);
                    },
                  ),
                ),
                const SizedBox(height: 8),
              ],
            );
          }),
        ],
      ),
    );
  }
}

class _ContentCard extends ConsumerWidget {
  final AssignedContent item;
  final VoidCallback onTap;

  const _ContentCard({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final color = _typeColor(theme, item.contentType);
    final offlineManager = ref.watch(offlineContentManagerProvider);

    return Semantics(
      button: true,
      label:
          '${item.title}, ${item.subject ?? 'Général'}, progression ${item.progress ?? 'non commencée'}',
      child: Card(
        margin: const EdgeInsets.only(bottom: 10),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Type icon
                Semantics(
                  excludeSemantics: true,
                  child: CircleAvatar(
                    backgroundColor: color.withAlpha(30),
                    radius: 24,
                    child: Icon(
                      _typeIcon(item.contentType),
                      color: color,
                      size: 24,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // Title + description
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.title,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      if (item.description != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          item.description!,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.bodySmall,
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                // Progress indicator
                _ProgressBadge(progress: item.progress),
                const SizedBox(width: 4),
                // Offline download button
                _DownloadButton(
                  contentItemId: item.contentItemId,
                  offlineManager: offlineManager,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  IconData _typeIcon(String type) {
    switch (type.toUpperCase()) {
      case 'VIDEO':
        return Icons.play_circle_fill;
      case 'AUDIO':
        return Icons.audiotrack;
      case 'DOCUMENT':
        return Icons.picture_as_pdf;
      case 'INTERACTIVE':
        return Icons.touch_app;
      case 'STORY':
        return Icons.auto_stories;
      default:
        return Icons.article;
    }
  }

  Color _typeColor(ThemeData theme, String type) {
    switch (type.toUpperCase()) {
      case 'VIDEO':
        return theme.colorScheme.error;
      case 'AUDIO':
        return theme.colorScheme.secondary;
      case 'DOCUMENT':
        return theme.colorScheme.primary;
      case 'INTERACTIVE':
        return theme.semanticPalette.warning;
      case 'STORY':
        return KidsContentColors.storyPageTurn;
      default:
        return theme.colorScheme.outline;
    }
  }
}

class _ProgressBadge extends StatelessWidget {
  final String? progress;
  const _ProgressBadge({this.progress});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (icon, color, label) = switch (progress) {
      'completed' => (
          Icons.check_circle,
          theme.semanticPalette.success,
          'Terminé'
        ),
      'in_progress' => (
          Icons.play_circle,
          theme.colorScheme.primary,
          'En cours'
        ),
      'started' => (Icons.play_circle, theme.colorScheme.primary, 'En cours'),
      _ => (Icons.circle_outlined, theme.colorScheme.outline, 'Nouveau'),
    };

    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 10, color: color)),
      ],
    );
  }
}

// ── Download Button ──

class _DownloadButton extends StatefulWidget {
  final String contentItemId;
  final OfflineContentManager offlineManager;

  const _DownloadButton({
    required this.contentItemId,
    required this.offlineManager,
  });

  @override
  State<_DownloadButton> createState() => _DownloadButtonState();
}

class _DownloadButtonState extends State<_DownloadButton> {
  late final StreamSubscription<Map<String, DownloadState>> _sub;
  DownloadState _state = const DownloadState();

  @override
  void initState() {
    super.initState();
    _sub = widget.offlineManager.downloadStatesStream.listen((states) {
      if (mounted) {
        setState(() {
          _state = states[widget.contentItemId] ?? const DownloadState();
        });
      }
    });
    // Check initial state from manifest
    widget.offlineManager
        .isAvailableOffline(widget.contentItemId)
        .then((available) {
      if (mounted && available && _state.status == DownloadStatus.idle) {
        setState(() {
          _state =
              const DownloadState(status: DownloadStatus.done, progress: 1);
        });
      }
    });
  }

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return switch (_state.status) {
      DownloadStatus.downloading => SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(
            value: _state.progress > 0 ? _state.progress : null,
            strokeWidth: 2.5,
          ),
        ),
      DownloadStatus.done => Icon(
          Icons.check_circle_rounded,
          size: 24,
          color: theme.semanticPalette.success,
        ),
      DownloadStatus.error => IconButton(
          icon: const Icon(Icons.error_outline, size: 20),
          color: theme.colorScheme.error,
          tooltip: 'Erreur de téléchargement — réessayer',
          onPressed: () =>
              widget.offlineManager.downloadForOffline(widget.contentItemId),
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
        ),
      DownloadStatus.idle => IconButton(
          icon: const Icon(Icons.download_outlined, size: 20),
          color: theme.colorScheme.outline,
          tooltip: 'Télécharger pour utilisation hors ligne',
          onPressed: () =>
              widget.offlineManager.downloadForOffline(widget.contentItemId),
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
        ),
    };
  }
}

// ── Content Player ──

String _streamPath(AssignedContent item) {
  final streamUrl = item.streamUrl?.trim();
  if (streamUrl != null && streamUrl.isNotEmpty) {
    return streamUrl;
  }
  return '/content-items/${item.contentItemId}/stream';
}

class _ContentPlayer extends StatelessWidget {
  final AssignedContent item;
  final VoidCallback onBack;
  final void Function(String progress) onProgress;

  const _ContentPlayer({
    required this.item,
    required this.onBack,
    required this.onProgress,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final type = item.contentType.toUpperCase();

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: onBack,
        ),
        title: Text(item.title, overflow: TextOverflow.ellipsis),
        actions: [
          TextButton.icon(
            onPressed: () {
              onProgress('completed');
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: const Text('Marqué comme terminé'),
                  backgroundColor: theme.semanticPalette.success,
                ),
              );
            },
            icon: const Icon(Icons.check_circle_outline, size: 18),
            label: const Text('Terminé'),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(child: _buildPlayer(type)),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              border: Border(
                top: BorderSide(color: theme.colorScheme.outline.withAlpha(50)),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (item.description != null) ...[
                  Text(item.description!, style: theme.textTheme.bodyMedium),
                  const SizedBox(height: 8),
                ],
                Row(
                  children: [
                    Chip(
                      label: Text(
                        item.contentType,
                        style: const TextStyle(fontSize: 11),
                      ),
                      padding: EdgeInsets.zero,
                      visualDensity: VisualDensity.compact,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    if (item.subject != null) ...[
                      const SizedBox(width: 6),
                      Chip(
                        label: Text(
                          item.subject!,
                          style: const TextStyle(fontSize: 11),
                        ),
                        padding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayer(String type) {
    final path = _streamPath(item);
    switch (type) {
      case 'VIDEO':
        return _SignedVideoPlayer(
          path: path,
          title: item.title,
          onStarted: () => onProgress('in_progress'),
        );
      case 'AUDIO':
        return _SignedAudioPlayer(
          path: path,
          title: item.title,
          onStarted: () => onProgress('in_progress'),
        );
      case 'DOCUMENT':
        return _SignedPdfPlayer(
          path: path,
          title: item.title,
          contentItemId: item.contentItemId,
          onOpened: () => onProgress('in_progress'),
        );
      case 'INTERACTIVE':
        return _SignedOpenFilePanel(
          path: path,
          title: item.title,
          contentItemId: item.contentItemId,
          onOpened: () => onProgress('in_progress'),
        );
      default:
        return const Center(child: Text('Type de contenu non supporté'));
    }
  }
}

class _SignedVideoPlayer extends ConsumerStatefulWidget {
  final String path;
  final String title;
  final VoidCallback onStarted;

  const _SignedVideoPlayer({
    required this.path,
    required this.title,
    required this.onStarted,
  });

  @override
  ConsumerState<_SignedVideoPlayer> createState() => _SignedVideoPlayerState();
}

class _SignedVideoPlayerState extends ConsumerState<_SignedVideoPlayer>
    with WidgetsBindingObserver {
  VideoPlayerController? _controller;
  String? _signedUrl;
  bool _loading = true;
  bool _recovering = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_load());
  }

  @override
  void didUpdateWidget(covariant _SignedVideoPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      unawaited(_load(forceRefresh: true));
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(signedUrlCacheProvider).clearExpired();
      unawaited(_load(preservePosition: true));
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.removeListener(_handleVideoValue);
    unawaited(_controller?.dispose());
    super.dispose();
  }

  Future<void> _load({
    bool forceRefresh = false,
    bool preservePosition = false,
  }) async {
    final previous = _controller;
    final resumePosition = preservePosition ? previous?.value.position : null;
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final url = await ref
          .read(signedUrlCacheProvider)
          .getUrl(widget.path, forceRefresh: forceRefresh);
      if (!forceRefresh && url == _signedUrl && previous != null) {
        if (mounted) setState(() => _loading = false);
        return;
      }

      final controller = VideoPlayerController.networkUrl(Uri.parse(url));
      controller.addListener(_handleVideoValue);
      await controller.initialize();
      if (resumePosition != null && resumePosition > Duration.zero) {
        await controller.seekTo(resumePosition);
      }
      if (!mounted) {
        await controller.dispose();
        return;
      }
      previous?.removeListener(_handleVideoValue);
      await previous?.dispose();
      setState(() {
        _controller = controller;
        _signedUrl = url;
        _loading = false;
        _recovering = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  void _handleVideoValue() {
    final controller = _controller;
    if (controller == null || !controller.value.hasError || _recovering) {
      return;
    }
    _recovering = true;
    ref.read(signedUrlCacheProvider).invalidate(widget.path);
    unawaited(_load(forceRefresh: true, preservePosition: true));
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    if (_loading && controller == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null && controller == null) {
      return _MediaError(
        message: _error!,
        onRetry: () => _load(forceRefresh: true),
      );
    }
    if (controller == null || !controller.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AspectRatio(
              aspectRatio: controller.value.aspectRatio,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: VideoPlayer(controller),
              ),
            ),
            const SizedBox(height: 12),
            VideoProgressIndicator(
              controller,
              allowScrubbing: true,
              padding: const EdgeInsets.symmetric(vertical: 8),
            ),
            Row(
              children: [
                IconButton.filled(
                  onPressed: () {
                    if (controller.value.isPlaying) {
                      unawaited(controller.pause());
                    } else {
                      widget.onStarted();
                      unawaited(controller.play());
                    }
                    setState(() {});
                  },
                  icon: Icon(
                    controller.value.isPlaying ? Icons.pause : Icons.play_arrow,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    widget.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
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

class _SignedAudioPlayer extends ConsumerStatefulWidget {
  final String path;
  final String title;
  final VoidCallback onStarted;

  const _SignedAudioPlayer({
    required this.path,
    required this.title,
    required this.onStarted,
  });

  @override
  ConsumerState<_SignedAudioPlayer> createState() => _SignedAudioPlayerState();
}

class _SignedAudioPlayerState extends ConsumerState<_SignedAudioPlayer>
    with WidgetsBindingObserver {
  final AudioPlayer _player = AudioPlayer();
  StreamSubscription<Duration>? _positionSub;
  StreamSubscription<Duration?>? _durationSub;
  StreamSubscription<PlayerState>? _playerStateSub;
  StreamSubscription<PlaybackEvent>? _playbackEventSub;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _playing = false;
  bool _loading = true;
  bool _recovering = false;
  String? _signedUrl;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _positionSub = _player.positionStream.listen((position) {
      if (mounted) setState(() => _position = position);
    });
    _durationSub = _player.durationStream.listen((duration) {
      if (mounted) setState(() => _duration = duration ?? Duration.zero);
    });
    _playerStateSub = _player.playerStateStream.listen((state) {
      if (mounted) setState(() => _playing = state.playing);
    });
    _playbackEventSub = _player.playbackEventStream.listen(
      (_) {},
      onError: (_, __) => _recoverAfterAudioError(),
    );
    unawaited(_load());
  }

  @override
  void didUpdateWidget(covariant _SignedAudioPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      unawaited(_load(forceRefresh: true));
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(signedUrlCacheProvider).clearExpired();
      unawaited(_load(preservePosition: true));
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_positionSub?.cancel());
    unawaited(_durationSub?.cancel());
    unawaited(_playerStateSub?.cancel());
    unawaited(_playbackEventSub?.cancel());
    unawaited(_player.dispose());
    super.dispose();
  }

  Future<void> _load({
    bool forceRefresh = false,
    bool preservePosition = false,
  }) async {
    final resumePosition = preservePosition ? _position : Duration.zero;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final url = await ref
          .read(signedUrlCacheProvider)
          .getUrl(widget.path, forceRefresh: forceRefresh);
      if (!forceRefresh && url == _signedUrl) {
        if (mounted) setState(() => _loading = false);
        return;
      }
      await _player.setAudioSource(AudioSource.uri(Uri.parse(url)));
      if (resumePosition > Duration.zero) {
        await _player.seek(resumePosition);
      }
      if (!mounted) return;
      setState(() {
        _signedUrl = url;
        _loading = false;
        _recovering = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  void _recoverAfterAudioError() {
    if (_recovering) return;
    _recovering = true;
    ref.read(signedUrlCacheProvider).invalidate(widget.path);
    unawaited(_load(forceRefresh: true, preservePosition: true));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _signedUrl == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null && _signedUrl == null) {
      return _MediaError(
        message: _error!,
        onRetry: () => _load(forceRefresh: true),
      );
    }

    final max = _duration.inMilliseconds <= 0
        ? 1.0
        : _duration.inMilliseconds.toDouble();
    final value = _position.inMilliseconds.clamp(0, max.toInt()).toDouble();

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.audiotrack,
              size: 80,
              color: Theme.of(context).colorScheme.secondary,
            ),
            const SizedBox(height: 16),
            Text(
              widget.title,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            Slider(
              value: value,
              max: max,
              onChanged: (next) =>
                  unawaited(_player.seek(Duration(milliseconds: next.round()))),
            ),
            IconButton.filled(
              iconSize: 36,
              onPressed: () {
                if (_playing) {
                  unawaited(_player.pause());
                } else {
                  widget.onStarted();
                  unawaited(_player.play());
                }
              },
              icon: Icon(_playing ? Icons.pause : Icons.play_arrow),
            ),
          ],
        ),
      ),
    );
  }
}

class _SignedPdfPlayer extends ConsumerStatefulWidget {
  final String path;
  final String title;
  final String contentItemId;
  final VoidCallback onOpened;

  const _SignedPdfPlayer({
    required this.path,
    required this.title,
    required this.contentItemId,
    required this.onOpened,
  });

  @override
  ConsumerState<_SignedPdfPlayer> createState() => _SignedPdfPlayerState();
}

class _SignedPdfPlayerState extends ConsumerState<_SignedPdfPlayer>
    with WidgetsBindingObserver {
  File? _file;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_download());
  }

  @override
  void didUpdateWidget(covariant _SignedPdfPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      unawaited(_download(forceRefresh: true));
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(signedUrlCacheProvider).clearExpired();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _download({bool forceRefresh = false}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      if (forceRefresh) {
        ref.read(signedUrlCacheProvider).invalidate(widget.path);
      }
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/content-${widget.contentItemId}.pdf');
      final downloaded = await ref
          .read(signedUrlCacheProvider)
          .download(widget.path, savePath: file.path);
      widget.onOpened();
      if (!mounted) return;
      setState(() {
        _file = downloaded;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _openExternally() async {
    final file = _file;
    if (file == null) return;
    await OpenFilex.open(file.path);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _file == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null && _file == null) {
      return _MediaError(
        message: _error!,
        onRetry: () => _download(forceRefresh: true),
      );
    }
    final file = _file;
    if (file == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return Column(
      children: [
        Align(
          alignment: Alignment.centerRight,
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: OutlinedButton.icon(
              onPressed: _openExternally,
              icon: const Icon(Icons.open_in_new),
              label: const Text('Ouvrir'),
            ),
          ),
        ),
        Expanded(child: PdfViewer.openFile(file.path)),
      ],
    );
  }
}

class _SignedOpenFilePanel extends ConsumerStatefulWidget {
  final String path;
  final String title;
  final String contentItemId;
  final VoidCallback onOpened;

  const _SignedOpenFilePanel({
    required this.path,
    required this.title,
    required this.contentItemId,
    required this.onOpened,
  });

  @override
  ConsumerState<_SignedOpenFilePanel> createState() =>
      _SignedOpenFilePanelState();
}

class _SignedOpenFilePanelState extends ConsumerState<_SignedOpenFilePanel> {
  bool _opening = false;
  String? _error;

  Future<void> _open() async {
    setState(() {
      _opening = true;
      _error = null;
    });
    try {
      final metadata =
          await ref.read(signedUrlCacheProvider).getMetadata(widget.path);
      final dir = await getTemporaryDirectory();
      final filename = metadata.filename.isEmpty
          ? 'content-${widget.contentItemId}'
          : metadata.filename;
      final file = File('${dir.path}/$filename');
      final downloaded = await ref
          .read(signedUrlCacheProvider)
          .download(widget.path, savePath: file.path);
      widget.onOpened();
      await OpenFilex.open(downloaded.path);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _opening = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.touch_app,
              size: 80,
              color: theme.semanticPalette.warning,
            ),
            const SizedBox(height: 24),
            Text(
              widget.title,
              style: theme.textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, textAlign: TextAlign.center),
            ],
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: _opening ? null : _open,
              icon: _opening
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.open_in_new),
              label: Text(_opening ? 'Ouverture...' : 'Ouvrir'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MediaError extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _MediaError({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton.tonal(
              onPressed: onRetry,
              child: const Text('Réessayer'),
            ),
          ],
        ),
      ),
    );
  }
}
