/// Student content screen — view assigned content by class/subject.
/// In-app video player, PDF viewer, audio player, progress tracking.
///
/// Phase 10C: Mirrors web ContentViewPage.tsx (Phase 10B).
/// API: GET /classes/{classId}/content, POST /content-items/{id}/progress

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/quiz.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/widgets/animated_guide.dart';
import 'package:ecole_platform/shared/ui/widgets/kids_skeleton_layouts.dart';
import 'package:ecole_platform/shared/widgets/app_empty_state.dart';

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
          .map((json) => AssignedContent(
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
              ))
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
      return AppEmptyState(
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
                ...entry.value.map((item) => _ContentCard(
                      item: item,
                      onTap: () async {
                        if (item.progress == null ||
                            item.progress == 'not_started') {
                          await _updateProgress(
                              item.contentItemId, 'in_progress');
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
                    )),
                const SizedBox(height: 8),
              ],
            );
          }),
        ],
      ),
    );
  }
}

class _ContentCard extends StatelessWidget {
  final AssignedContent item;
  final VoidCallback onTap;

  const _ContentCard({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = _typeColor(theme, item.contentType);

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
                    child: Icon(_typeIcon(item.contentType),
                        color: color, size: 24),
                  ),
                ),
                const SizedBox(width: 16),
                // Title + description
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item.title,
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                      if (item.description != null) ...[
                        const SizedBox(height: 4),
                        Text(item.description!,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: theme.textTheme.bodySmall),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                // Progress indicator
                _ProgressBadge(progress: item.progress),
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

// ── Content Player ──

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
          // Mark as completed
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
          // Player area
          Expanded(child: _buildPlayer(context, type)),

          // Info bar
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
                      label: Text(item.contentType,
                          style: const TextStyle(fontSize: 11)),
                      padding: EdgeInsets.zero,
                      visualDensity: VisualDensity.compact,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    if (item.subject != null) ...[
                      const SizedBox(width: 6),
                      Chip(
                        label: Text(item.subject!,
                            style: const TextStyle(fontSize: 11)),
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

  Widget _buildPlayer(BuildContext context, String type) {
    final theme = Theme.of(context);
    final playerBackground = theme.brightness == Brightness.dark
        ? theme.colorScheme.surfaceContainerHighest
        : theme.colorScheme.onSurface;
    final onPlayerBackground = theme.brightness == Brightness.dark
        ? theme.colorScheme.onSurface
        : theme.colorScheme.surface;

    switch (type) {
      case 'VIDEO':
        // Use platform video player via URL launch or show placeholder
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: double.infinity,
                height: 220,
                margin: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: playerBackground,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.play_circle_fill,
                        size: 64, color: onPlayerBackground),
                    const SizedBox(height: 12),
                    Text(item.title,
                        style: TextStyle(color: onPlayerBackground),
                        textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: () {
                        final url = item.streamUrl;
                        if (url != null) {
                          _showExternalLink(context, url);
                        }
                        onProgress('in_progress');
                      },
                      icon: const Icon(Icons.play_arrow),
                      label: const Text('Lire la vidéo'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );

      case 'AUDIO':
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.audiotrack,
                  size: 80, color: theme.colorScheme.secondary),
              const SizedBox(height: 24),
              Text(item.title,
                  style: theme.textTheme.titleMedium,
                  textAlign: TextAlign.center),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () {
                  final url = item.streamUrl;
                  if (url != null) {
                    _showExternalLink(context, url);
                  }
                  onProgress('in_progress');
                },
                icon: const Icon(Icons.play_arrow),
                label: const Text('Écouter'),
                style: FilledButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
              ),
            ],
          ),
        );

      case 'DOCUMENT':
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.picture_as_pdf,
                  size: 80, color: theme.colorScheme.primary),
              const SizedBox(height: 24),
              Text(item.title,
                  style: theme.textTheme.titleMedium,
                  textAlign: TextAlign.center),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () {
                  final url = item.streamUrl;
                  if (url != null) {
                    _showExternalLink(context, url);
                  }
                  onProgress('in_progress');
                },
                icon: const Icon(Icons.open_in_new),
                label: const Text('Ouvrir le document'),
                style: FilledButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
              ),
            ],
          ),
        );

      case 'INTERACTIVE':
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.touch_app,
                  size: 80, color: theme.semanticPalette.warning),
              const SizedBox(height: 24),
              Text(item.title,
                  style: theme.textTheme.titleMedium,
                  textAlign: TextAlign.center),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () {
                  final url = item.streamUrl;
                  if (url != null) {
                    _showExternalLink(context, url);
                  }
                  onProgress('in_progress');
                },
                icon: const Icon(Icons.launch),
                label: const Text('Ouvrir'),
                style: FilledButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
              ),
            ],
          ),
        );

      default:
        return const Center(child: Text('Type de contenu non supporté'));
    }
  }

  void _showExternalLink(BuildContext context, String url) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Lien externe: $url'),
      ),
    );
  }
}
