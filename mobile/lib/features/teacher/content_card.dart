part of 'content_library_screen.dart';

class _LibraryGrid extends ConsumerWidget {
  final _LibraryState state;

  const _LibraryGrid({
    required this.state,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(_libraryProvider.notifier).load(),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }
    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.library_books,
                size: 48, color: theme.colorScheme.outline),
            SizedBox(height: 16),
            Text('Aucun contenu disponible'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_libraryProvider.notifier).load(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final item = state.items[index];
          return ContentCard(item: item);
        },
      ),
    );
  }
}

class ContentCard extends ConsumerWidget {
  final LibraryItem item;

  const ContentCard({
    super.key,
    required this.item,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final typeColor = _typeColor(theme, item.contentType);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: typeColor.withAlpha(30),
          child: Icon(
            _typeIcon(item.contentType),
            color: typeColor,
          ),
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
            const SizedBox(width: 4),
            Chip(
              label: Text(
                item.origin == 'platform' ? 'Plateforme' : 'École',
                style: TextStyle(
                  fontSize: 10,
                  color: item.origin == 'platform'
                      ? theme.colorScheme.primary
                      : theme.semanticPalette.success,
                ),
              ),
              padding: EdgeInsets.zero,
              visualDensity: VisualDensity.compact,
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.assignment_add, size: 20),
              tooltip: 'Assigner à une classe',
              onPressed: () => _showAssignDialog(context, ref, item),
            ),
            if (item.origin == 'school')
              IconButton(
                icon: const Icon(Icons.publish, size: 20),
                tooltip: 'Soumettre pour révision',
                onPressed: () => _submitForReview(context, ref, item.id),
              ),
          ],
        ),
      ),
    );
  }
}

Future<void> _showAssignDialog(
  BuildContext context,
  WidgetRef ref,
  LibraryItem item,
) async {
  final repo = ref.read(contentLibraryRepositoryProvider);
  late final List<ClassInfo> classes;
  try {
    classes = await repo.getTeacherClasses();
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
    return;
  }

  if (!context.mounted || classes.isEmpty) return;

  final selectedClass = await showDialog<ClassInfo>(
    context: context,
    builder: (ctx) => SimpleDialog(
      title: Text('Assigner "${item.title}"'),
      children: classes
          .map(
            (schoolClass) => SimpleDialogOption(
              onPressed: () => Navigator.pop(ctx, schoolClass),
              child: ListTile(
                title: Text(schoolClass.name),
                subtitle: Text('${schoolClass.studentCount} élèves'),
                leading: const Icon(Icons.class_),
              ),
            ),
          )
          .toList(),
    ),
  );

  if (selectedClass == null || !context.mounted) return;

  try {
    await repo.assignContent(
      contentItemId: item.id,
      classId: selectedClass.id,
    );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Contenu assigné à ${selectedClass.name}'),
          backgroundColor: Theme.of(context).semanticPalette.success,
        ),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }
}

Future<void> _submitForReview(
  BuildContext context,
  WidgetRef ref,
  String contentId,
) async {
  try {
    await ref.read(contentLibraryRepositoryProvider).submitForReview(contentId);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Soumis pour révision'),
          backgroundColor: Theme.of(context).semanticPalette.success,
        ),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }
}

IconData _typeIcon(String type) {
  switch (type.toUpperCase()) {
    case 'VIDEO':
      return Icons.play_circle_outline;
    case 'AUDIO':
      return Icons.audiotrack;
    case 'DOCUMENT':
      return Icons.description;
    case 'INTERACTIVE':
      return Icons.touch_app;
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
    default:
      return theme.colorScheme.outline;
  }
}
