/// Justification review screen — approve/deny parent justifications.
///
/// Reference: Phase 5B (from 4A)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/admin.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

// ── State ──

class _JustificationsState {
  final List<Justification> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String? statusFilter;
  final Set<String> actionLoading;

  const _JustificationsState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.statusFilter,
    this.actionLoading = const {},
  });

  _JustificationsState copyWith({
    List<Justification>? items,
    bool? isLoading,
    String? error,
    bool clearError = false,
    String? nextCursor,
    bool? hasMore,
    String? statusFilter,
    bool clearStatusFilter = false,
    Set<String>? actionLoading,
  }) {
    return _JustificationsState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
      statusFilter:
          clearStatusFilter ? null : (statusFilter ?? this.statusFilter),
      actionLoading: actionLoading ?? this.actionLoading,
    );
  }
}

class _JustificationsNotifier extends StateNotifier<_JustificationsState> {
  final Ref _ref;

  _JustificationsNotifier(this._ref)
      : super(const _JustificationsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final repo = _ref.read(adminRepositoryProvider);
      final result = await repo.getJustifications(status: state.statusFilter);
      state = state.copyWith(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setStatusFilter(String? value) {
    state = value == null
        ? state.copyWith(clearStatusFilter: true)
        : state.copyWith(statusFilter: value);
    load();
  }

  Future<void> approve(String id) async {
    state = state.copyWith(actionLoading: {...state.actionLoading, id});
    try {
      final repo = _ref.read(adminRepositoryProvider);
      await repo.reviewJustification(id, 'justified');
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state =
          state.copyWith(actionLoading: {...state.actionLoading}..remove(id));
    }
  }

  Future<void> reject(String id, String reason) async {
    state = state.copyWith(actionLoading: {...state.actionLoading, id});
    try {
      final repo = _ref.read(adminRepositoryProvider);
      await repo.reviewJustification(id, 'rejected', rejectionReason: reason);
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state =
          state.copyWith(actionLoading: {...state.actionLoading}..remove(id));
    }
  }

  Future<void> refresh() async => load();
}

final _justificationsProvider = StateNotifierProvider.autoDispose<
    _JustificationsNotifier, _JustificationsState>((ref) {
  return _JustificationsNotifier(ref);
});

// ── Screen ──

class JustificationReviewScreen extends ConsumerWidget {
  const JustificationReviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_justificationsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Justifications')),
      body: Column(
        children: [
          // Status filter chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                const Icon(Icons.filter_list, size: 20),
                const SizedBox(width: 8),
                ...['pending', 'justified', 'rejected'].map((s) {
                  final selected = state.statusFilter == s;
                  return Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: FilterChip(
                      label: Text(_statusLabel(s),
                          style: const TextStyle(fontSize: 12)),
                      selected: selected,
                      onSelected: (v) => ref
                          .read(_justificationsProvider.notifier)
                          .setStatusFilter(v ? s : null),
                      visualDensity: VisualDensity.compact,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  );
                }),
              ],
            ),
          ),

          if (state.error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(state.error!,
                    style:
                        TextStyle(color: theme.colorScheme.onErrorContainer)),
              ),
            ),

          Expanded(child: _buildList(context, ref, state, theme)),
        ],
      ),
    );
  }

  Widget _buildList(BuildContext context, WidgetRef ref,
      _JustificationsState state, ThemeData theme) {
    final colors = theme.colorScheme;

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle_outline, size: 48, color: colors.outline),
            SizedBox(height: 16),
            Text('Aucune justification'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_justificationsProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final j = state.items[index];
          final isActionLoading = state.actionLoading.contains(j.id);

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        _statusIcon(j.status),
                        color: _statusColor(context, j.status),
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      _JustStatusBadge(status: j.status),
                      const Spacer(),
                      Text(
                        _formatDate(j.createdAt),
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text('Motif :',
                      style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant)),
                  const SizedBox(height: 4),
                  Text(j.reason, style: theme.textTheme.bodyMedium),
                  if (j.rejectionReason != null) ...[
                    const SizedBox(height: 8),
                    Text('Raison du rejet :',
                        style: theme.textTheme.labelSmall
                            ?.copyWith(color: colors.error)),
                    const SizedBox(height: 4),
                    Text(j.rejectionReason!,
                        style: theme.textTheme.bodySmall
                            ?.copyWith(color: colors.error)),
                  ],
                  if (j.status == 'pending') ...[
                    const SizedBox(height: 16),
                    if (isActionLoading)
                      const Center(
                        child: SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    else
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton.icon(
                              onPressed: () => ref
                                  .read(_justificationsProvider.notifier)
                                  .approve(j.id),
                              icon: const Icon(Icons.check, size: 18),
                              label: const Text('Approuver'),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () =>
                                  _showRejectDialog(context, ref, j.id),
                              icon: Icon(Icons.close,
                                  size: 18, color: colors.error),
                              label: Text('Rejeter',
                                  style: TextStyle(color: colors.error)),
                              style: OutlinedButton.styleFrom(
                                side: BorderSide(color: colors.error),
                              ),
                            ),
                          ),
                        ],
                      ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  void _showRejectDialog(BuildContext context, WidgetRef ref, String id) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Rejeter la justification'),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: 'Raison du rejet',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () {
              final reason = controller.text.trim();
              if (reason.isNotEmpty) {
                ref.read(_justificationsProvider.notifier).reject(id, reason);
                Navigator.pop(ctx);
              }
            },
            style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error),
            child: const Text('Rejeter'),
          ),
        ],
      ),
    );
  }

  String _statusLabel(String s) {
    switch (s) {
      case 'pending':
        return 'En attente';
      case 'justified':
        return 'Approuvées';
      case 'rejected':
        return 'Rejetées';
      default:
        return s;
    }
  }

  IconData _statusIcon(String s) {
    switch (s) {
      case 'pending':
        return Icons.hourglass_empty;
      case 'justified':
        return Icons.check_circle;
      case 'rejected':
        return Icons.cancel;
      default:
        return Icons.help_outline;
    }
  }

  Color _statusColor(BuildContext context, String s) {
    final theme = Theme.of(context);

    switch (s) {
      case 'pending':
        return theme.semanticPalette.warning;
      case 'justified':
        return theme.semanticPalette.success;
      case 'rejected':
        return theme.colorScheme.error;
      default:
        return theme.colorScheme.outline;
    }
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat.yMMMd('fr').add_Hm().format(date);
    } catch (_) {
      return dateStr;
    }
  }
}

class _JustStatusBadge extends StatelessWidget {
  final String status;

  const _JustStatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Color color;
    String label;
    switch (status) {
      case 'pending':
        color = theme.semanticPalette.warning;
        label = 'En attente';
        break;
      case 'justified':
        color = theme.semanticPalette.success;
        label = 'Approuvée';
        break;
      case 'rejected':
        color = theme.colorScheme.error;
        label = 'Rejetée';
        break;
      default:
        color = theme.colorScheme.outline;
        label = status;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
      decoration: BoxDecoration(
        border: Border.all(color: color),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(label,
          style: TextStyle(
              fontSize: 10, color: color, fontWeight: FontWeight.w600)),
    );
  }
}
