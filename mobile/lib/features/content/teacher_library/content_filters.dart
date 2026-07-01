part of 'content_library_screen.dart';

class _BrowseTab extends ConsumerWidget {
  const _BrowseTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_libraryProvider);

    return Column(
      children: [
        // Bridge card: CMS editing is web-only
        const Padding(
          padding: EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: PlatformBridgeCard(
            targetPlatform: BridgePlatform.web,
            title: 'Création de contenu et de quiz',
            description:
                'Pour créer des quiz, modifier le contenu et valider les soumissions, utilisez la version web.',
            icon: Icons.edit_note_rounded,
          ),
        ),
        _ContentFilters(state: state),
        Expanded(child: _LibraryGrid(state: state)),
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
    final t = AppLocalizations.of(ref);
    return SearchFilterBar(
      searchHint: t.t('contentLibrary.searchHint'),
      searchValue: '',
      onSearchChanged: (_) {},
      filters: [
        FilterGroup(
          id: 'type',
          label: t.t('content.filter.type'),
          options: [
            FilterOption(label: t.t('common.all'), value: null),
            FilterOption(label: t.t('content.type.video'), value: 'VIDEO'),
            FilterOption(label: t.t('content.type.audio'), value: 'AUDIO'),
            FilterOption(
              label: t.t('content.type.document'),
              value: 'DOCUMENT',
            ),
            FilterOption(
              label: t.t('content.type.interactive'),
              value: 'INTERACTIVE',
            ),
          ],
        ),
        FilterGroup(
          id: 'origin',
          label: t.t('content.filter.origin'),
          options: [
            FilterOption(label: t.t('common.all'), value: null),
            FilterOption(
              label: t.t('contentLibrary.filterPlatform'),
              value: 'platform',
            ),
            FilterOption(
              label: t.t('contentLibrary.filterSchool'),
              value: 'school',
            ),
          ],
        ),
      ],
      filterValues: {
        'type': state.typeFilter,
        'origin': state.originFilter,
      },
      onFilterChanged: (id, value) {
        if (id == 'type') {
          ref.read(_libraryProvider.notifier).setTypeFilter(value);
        } else {
          ref.read(_libraryProvider.notifier).setOriginFilter(value);
        }
      },
    );
  }
}
