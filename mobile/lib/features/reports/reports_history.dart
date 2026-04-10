part of 'reports_screen.dart';

extension _ReportsHistorySection on _ReportsScreenState {
  Widget _buildHistorySection(AppLocalizations t) {
    final pendingCount = _jobs.where((item) => item.isPending).length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                t.t('reports.historyTitle'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            if (pendingCount > 0)
              Chip(
                avatar: const Icon(Icons.schedule, size: 16),
                label: Text('$pendingCount ${t.t('reports.pending')}'),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (_jobs.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(t.t('reports.empty')),
            ),
          )
        else
          ..._jobs.map((job) => _buildHistoryCard(job, t)),
        if (_hasMore) ...[
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: _loadingMore ? null : _loadMore,
            child: _loadingMore
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(t.t('reports.loadMore')),
          ),
        ],
      ],
    );
  }

  Widget _buildCachedSection(AppLocalizations t) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.t('reports.cachedTitle'),
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        ..._cachedReports.map((job) => _buildHistoryCard(job, t, cached: true)),
      ],
    );
  }

  Widget _buildHistoryCard(
    ReportJob job,
    AppLocalizations t, {
    bool cached = false,
  }) {
    final fileExists =
        job.localFilePath != null && File(job.localFilePath!).existsSync();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _typeLabel(job.type, t),
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _describeScope(job, t),
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                _StatusChip(
                  label: _statusLabel(job.status, t),
                  status: job.status,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.schedule, size: 14),
                const SizedBox(width: 6),
                Text(
                  _formatDateTime(job.createdAt, t.locale),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
            if (cached || fileExists) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.offline_pin_outlined, size: 14),
                  const SizedBox(width: 6),
                  Text(
                    t.t('reports.availableOffline'),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
            if (job.errorMessage != null && job.errorMessage!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                job.errorMessage!,
                style: const TextStyle(color: Colors.red),
              ),
            ],
            if (job.isReady || fileExists) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton.tonalIcon(
                    onPressed: () => _downloadAndOpen(job),
                    icon: const Icon(Icons.open_in_new),
                    label: Text(t.t('reports.open')),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _shareReport(job),
                    icon: const Icon(Icons.share_outlined),
                    label: Text(t.t('reports.share')),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final String status;

  const _StatusChip({
    required this.label,
    required this.status,
  });

  @override
  Widget build(BuildContext context) {
    final (color, background) = switch (status) {
      'ready' => (Colors.green.shade800, Colors.green.shade50),
      'failed' => (Colors.red.shade800, Colors.red.shade50),
      'generating' => (Colors.orange.shade800, Colors.orange.shade50),
      _ => (Colors.blue.shade800, Colors.blue.shade50),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
    );
  }
}
