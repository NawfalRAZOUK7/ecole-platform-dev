part of 'content_library_screen.dart';

class _LibraryGrid extends ConsumerWidget {
  final _LibraryState state;
  final ThemeData theme;

  const _LibraryGrid({
    required this.state,
    required this.theme,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
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
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.library_books, size: 48, color: Colors.grey),
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
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _typeColor(item.contentType).withAlpha(30),
          child: Icon(
            _typeIcon(item.contentType),
            color: _typeColor(item.contentType),
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
                  color: item.origin == 'platform' ? Colors.blue : Colors.green,
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
        SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
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
          backgroundColor: Colors.green,
        ),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
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
        const SnackBar(
          content: Text('Soumis pour révision'),
          backgroundColor: Colors.green,
        ),
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
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

Color _typeColor(String type) {
  switch (type.toUpperCase()) {
    case 'VIDEO':
      return Colors.red;
    case 'AUDIO':
      return Colors.purple;
    case 'DOCUMENT':
      return Colors.blue;
    case 'INTERACTIVE':
      return Colors.orange;
    default:
      return Colors.grey;
  }
}
