/// Content library screen — browse content with search, filters, sort.
///
/// Reference: S-098, UI-STD-003
/// Phase 5B: Added search bar + sort toggle.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/widgets/search_filter_bar.dart';
import 'content_provider.dart';

class ContentScreen extends ConsumerWidget {
  const ContentScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(contentProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Bibliothèque')),
      body: Column(
        children: [
          // Search + filter bar
          SearchFilterBar(
            searchHint: 'Rechercher du contenu...',
            searchValue: state.search,
            onSearchChanged: (v) =>
                ref.read(contentProvider.notifier).setSearch(v),
            filters: {
              'Type': const [
                FilterOption(label: 'Tous', value: null),
                FilterOption(label: 'Vidéo', value: 'video'),
                FilterOption(label: 'Document', value: 'document'),
                FilterOption(label: 'Quiz', value: 'quiz'),
              ],
              'Niveau': const [
                FilterOption(label: 'Tous', value: null),
                FilterOption(label: 'Débutant', value: 'beginner'),
                FilterOption(label: 'Intermédiaire', value: 'intermediate'),
                FilterOption(label: 'Avancé', value: 'advanced'),
              ],
            },
            filterValues: {
              'Type': state.typeFilter,
              'Niveau': state.levelFilter,
            },
            onFilterChanged: (key, value) {
              if (key == 'Type') {
                ref.read(contentProvider.notifier).setTypeFilter(value);
              } else {
                ref.read(contentProvider.notifier).setLevelFilter(value);
              }
            },
            showSort: true,
            sortAscending: state.sortAscending,
            onSortToggle: () => ref.read(contentProvider.notifier).toggleSort(),
          ),

          // Content list
          Expanded(child: _buildList(context, ref, state, theme)),
        ],
      ),
    );
  }

  Widget _buildList(
    BuildContext context,
    WidgetRef ref,
    ContentState state,
    ThemeData theme,
  ) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(contentProvider.notifier).load(),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }

    final items = state.filteredItems;
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.library_books,
              size: 48,
              color: theme.colorScheme.outline,
            ),
            const SizedBox(height: 16),
            const Text('Aucun contenu disponible'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(contentProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: items.length,
        itemBuilder: (context, index) {
          final item = items[index];
          final typeColor = _typeColor(theme, item.contentType);
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: typeColor.withAlpha(30),
                child: Icon(_typeIcon(item.contentType), color: typeColor),
              ),
              title: Text(
                item.title,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: Row(
                children: [
                  Chip(
                    label: Text(
                      item.contentType,
                      style: const TextStyle(fontSize: 10),
                    ),
                    padding: EdgeInsets.zero,
                    visualDensity: VisualDensity.compact,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  if (item.levelBand != null) ...[
                    const SizedBox(width: 4),
                    Chip(
                      label: Text(
                        item.levelBand!,
                        style: const TextStyle(fontSize: 10),
                      ),
                      padding: EdgeInsets.zero,
                      visualDensity: VisualDensity.compact,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ],
                ],
              ),
              trailing: const Icon(Icons.chevron_right),
            ),
          );
        },
      ),
    );
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'video':
        return Icons.play_circle_outline;
      case 'document':
        return Icons.description;
      case 'quiz':
        return Icons.quiz;
      default:
        return Icons.article;
    }
  }

  Color _typeColor(ThemeData theme, String type) {
    switch (type) {
      case 'video':
        return theme.colorScheme.error;
      case 'document':
        return theme.colorScheme.primary;
      case 'quiz':
        return theme.semanticPalette.warning;
      default:
        return theme.colorScheme.outline;
    }
  }
}
