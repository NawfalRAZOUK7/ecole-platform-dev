part of 'content_library_screen.dart';

class _BrowseTab extends ConsumerWidget {
  const _BrowseTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_libraryProvider);
    final theme = Theme.of(context);

    return Column(
      children: [
        _ContentFilters(state: state),
        Expanded(child: _LibraryGrid(state: state, theme: theme)),
      ],
    );
  }
}

class _ContentFilters extends ConsumerWidget {
  final _LibraryState state;

  const _ContentFilters({
    required this.state,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SearchFilterBar(
      searchHint: 'Rechercher du contenu...',
      searchValue: '',
      onSearchChanged: (_) {},
      filters: {
        'Type': const [
          FilterOption(label: 'Tous', value: null),
          FilterOption(label: 'Vidéo', value: 'VIDEO'),
          FilterOption(label: 'Audio', value: 'AUDIO'),
          FilterOption(label: 'Document', value: 'DOCUMENT'),
          FilterOption(label: 'Interactif', value: 'INTERACTIVE'),
        ],
        'Origine': const [
          FilterOption(label: 'Tous', value: null),
          FilterOption(label: 'Plateforme', value: 'platform'),
          FilterOption(label: 'École', value: 'school'),
        ],
      },
      filterValues: {
        'Type': state.typeFilter,
        'Origine': state.originFilter,
      },
      onFilterChanged: (key, value) {
        if (key == 'Type') {
          ref.read(_libraryProvider.notifier).setTypeFilter(value);
        } else {
          ref.read(_libraryProvider.notifier).setOriginFilter(value);
        }
      },
    );
  }
}
