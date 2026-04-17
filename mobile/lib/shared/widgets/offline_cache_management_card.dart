/// Offline cache management card.
///
/// Displays total offline cache size, lists downloaded content items,
/// and lets the user delete individual items or clear all cached content.
/// Drop this card into any settings or profile screen.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class OfflineCacheManagementCard extends ConsumerStatefulWidget {
  const OfflineCacheManagementCard({super.key});

  @override
  ConsumerState<OfflineCacheManagementCard> createState() =>
      _OfflineCacheManagementCardState();
}

class _OfflineCacheManagementCardState
    extends ConsumerState<OfflineCacheManagementCard> {
  List<String>? _downloadedIds;
  int? _totalBytes;
  bool _isLoading = true;
  bool _isClearing = false;

  @override
  void initState() {
    super.initState();
    _loadCacheInfo();
  }

  Future<void> _loadCacheInfo() async {
    if (!mounted) return;
    setState(() => _isLoading = true);

    final manager = ref.read(offlineContentManagerProvider);
    final ids = await manager.getOfflineContentIds();
    final bytes = await manager.getTotalCacheSize();

    if (!mounted) return;
    setState(() {
      _downloadedIds = ids;
      _totalBytes = bytes;
      _isLoading = false;
    });
  }

  Future<void> _removeItem(String contentItemId) async {
    final manager = ref.read(offlineContentManagerProvider);
    await manager.removeOfflineContent(contentItemId);
    await _loadCacheInfo();
  }

  Future<void> _clearAll() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('مسح جميع المحتوى المحفوظ؟'),
        content: const Text(
          'سيتم حذف جميع الدروس والقصص المحفوظة للاستخدام بدون إنترنت.',
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('إلغاء'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(ctx).colorScheme.error,
            ),
            child: const Text('مسح الكل'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() => _isClearing = true);
    final manager = ref.read(offlineContentManagerProvider);
    for (final id in List<String>.from(_downloadedIds ?? <String>[])) {
      await manager.removeOfflineContent(id);
    }

    if (!mounted) return;
    setState(() => _isClearing = false);
    await _loadCacheInfo();
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            // ── Header ─────────────────────────────────────────────────────────
            Row(
              children: <Widget>[
                Icon(Icons.download_done_rounded,
                    color: colorScheme.primary, size: 22),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    'المحتوى المحفوظ بدون إنترنت',
                    style: textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                ),
                if (!_isLoading)
                  IconButton(
                    onPressed: _loadCacheInfo,
                    icon: const Icon(Icons.refresh_rounded),
                    tooltip: 'تحديث',
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),

            // ── Cache size summary ─────────────────────────────────────────────
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                child: Center(child: CircularProgressIndicator()),
              )
            else ...<Widget>[
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.base,
                  vertical: AppSpacing.sm,
                ),
                decoration: BoxDecoration(
                  color: colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: <Widget>[
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          '${_downloadedIds?.length ?? 0} عناصر محفوظة',
                          style: textTheme.bodyMedium
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                        Text(
                          _formatBytes(_totalBytes ?? 0),
                          style: textTheme.bodySmall?.copyWith(
                              color: colorScheme.onSurfaceVariant),
                        ),
                      ],
                    ),
                    const Spacer(),
                    if ((_downloadedIds?.isNotEmpty ?? false))
                      TextButton.icon(
                        onPressed: _isClearing ? null : _clearAll,
                        icon: _isClearing
                            ? const SizedBox(
                                width: 14,
                                height: 14,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.delete_sweep_rounded, size: 18),
                        label: const Text('مسح الكل'),
                        style: TextButton.styleFrom(
                          foregroundColor: colorScheme.error,
                        ),
                      ),
                  ],
                ),
              ),

              // ── Item list ───────────────────────────────────────────────────
              if (_downloadedIds?.isEmpty ?? true)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                  child: Center(
                    child: Text(
                      'لا يوجد محتوى محفوظ حتى الآن',
                      style: textTheme.bodySmall
                          ?.copyWith(color: colorScheme.onSurfaceVariant),
                    ),
                  ),
                )
              else ...<Widget>[
                const SizedBox(height: AppSpacing.sm),
                ...(_downloadedIds ?? <String>[]).map(
                  (id) => _OfflineCacheItemTile(
                    contentItemId: id,
                    onRemove: () => _removeItem(id),
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class _OfflineCacheItemTile extends StatelessWidget {
  final String contentItemId;
  final VoidCallback onRemove;

  const _OfflineCacheItemTile({
    required this.contentItemId,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(
          Icons.auto_stories_outlined,
          size: 20,
          color: Theme.of(context).colorScheme.onPrimaryContainer,
        ),
      ),
      title: Text(
        contentItemId,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: Theme.of(context).textTheme.bodyMedium,
      ),
      subtitle: Text(
        'متاح بدون إنترنت',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.green.shade700,
            ),
      ),
      trailing: IconButton(
        onPressed: onRemove,
        icon: const Icon(Icons.delete_outline_rounded),
        tooltip: 'حذف',
        color: Theme.of(context).colorScheme.error,
        visualDensity: VisualDensity.compact,
      ),
    );
  }
}
