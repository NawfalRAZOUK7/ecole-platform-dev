part of 'content_library_screen.dart';

class _SubmissionsTab extends ConsumerStatefulWidget {
  const _SubmissionsTab();

  @override
  ConsumerState<_SubmissionsTab> createState() => _SubmissionsTabState();
}

class _SubmissionsTabState extends ConsumerState<_SubmissionsTab> {
  List<ContentSubmission> _submissions = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = ref.read(contentLibraryRepositoryProvider);
      _submissions = await repo.getMySubmissions();
      setState(() => _loading = false);
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(_error!),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: _fetch,
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }
    if (_submissions.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Aucune soumission'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetch,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _submissions.length,
        itemBuilder: (context, index) {
          final submission = _submissions[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: ListTile(
              title: Text(
                submission.contentTitle,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  _StatusBadge(status: submission.status),
                  if (submission.reviewNotes != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      submission.reviewNotes!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ],
              ),
              trailing: submission.submittedAt != null
                  ? Text(
                      submission.submittedAt!.substring(0, 10),
                      style: theme.textTheme.bodySmall,
                    )
                  : null,
            ),
          );
        },
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (status.toLowerCase()) {
      'pending' => (Colors.orange, 'En attente'),
      'approved' => (Colors.green, 'Approuvé'),
      'rejected' => (Colors.red, 'Rejeté'),
      'promoted' => (Colors.blue, 'Promu'),
      _ => (Colors.grey, status),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
