/// Content library screen — browse content with search, filters, sort.
///
/// Reference: S-098, UI-STD-003
/// Phase 5B: Added search bar + sort toggle.

import 'package:flutter/material.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/widgets/search_filter_bar.dart';
import 'content_provider.dart';

class ContentScreen extends ConsumerWidget {
  const ContentScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(contentProvider);
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('nav.contentLibrary'))),
      body: Column(
        children: [
          // Search + filter bar
          SearchFilterBar(
            searchHint: t.t('contentLibrary.searchHint'),
            searchValue: state.search,
            onSearchChanged: (v) =>
                ref.read(contentProvider.notifier).setSearch(v),
            filters: [
              FilterGroup(
                id: 'type',
                label: t.t('content.filter.type'),
                options: [
                  FilterOption(label: t.t('common.all'), value: null),
                  FilterOption(
                    label: t.t('content.type.video'),
                    value: 'video',
                  ),
                  FilterOption(
                    label: t.t('content.type.document'),
                    value: 'document',
                  ),
                  FilterOption(label: t.t('content.type.quiz'), value: 'quiz'),
                ],
              ),
              FilterGroup(
                id: 'level',
                label: t.t('content.filter.level'),
                options: [
                  FilterOption(label: t.t('common.all'), value: null),
                  FilterOption(
                    label: t.t('content.level.beginner'),
                    value: 'beginner',
                  ),
                  FilterOption(
                    label: t.t('content.level.intermediate'),
                    value: 'intermediate',
                  ),
                  FilterOption(
                    label: t.t('content.level.advanced'),
                    value: 'advanced',
                  ),
                ],
              ),
            ],
            filterValues: {
              'type': state.typeFilter,
              'level': state.levelFilter,
            },
            onFilterChanged: (id, value) {
              if (id == 'type') {
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
    final t = AppLocalizations.of(ref);
    if (state.isLoading) {
      return const MobileListSkeleton();
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
              child: Text(t.t('common.retry')),
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
            Text(t.t('contentLibrary.noContent')),
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
