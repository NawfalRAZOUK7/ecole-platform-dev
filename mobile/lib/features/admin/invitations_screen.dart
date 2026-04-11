/// Admin invitations screen — issue/revoke invitation codes.
///
/// Reference: Phase 5B (from 4A)

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/admin.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

// ── State ──

class _InvitationsState {
  final List<Invitation> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String? statusFilter;
  final bool creating;
  final String? createdCode;
  final Set<String> revoking;

  const _InvitationsState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.statusFilter,
    this.creating = false,
    this.createdCode,
    this.revoking = const {},
  });

  _InvitationsState copyWith({
    List<Invitation>? items,
    bool? isLoading,
    String? error,
    bool clearError = false,
    String? nextCursor,
    bool? hasMore,
    String? statusFilter,
    bool clearStatusFilter = false,
    bool? creating,
    String? createdCode,
    bool clearCreatedCode = false,
    Set<String>? revoking,
  }) {
    return _InvitationsState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
      statusFilter:
          clearStatusFilter ? null : (statusFilter ?? this.statusFilter),
      creating: creating ?? this.creating,
      createdCode: clearCreatedCode ? null : (createdCode ?? this.createdCode),
      revoking: revoking ?? this.revoking,
    );
  }
}

class _InvitationsNotifier extends StateNotifier<_InvitationsState> {
  final Ref _ref;

  _InvitationsNotifier(this._ref)
      : super(const _InvitationsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final repo = _ref.read(adminRepositoryProvider);
      final result = await repo.getInvitations(status: state.statusFilter);
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

  Future<void> createInvitation(String roleTarget, int expiresInHours) async {
    state = state.copyWith(
        creating: true, clearError: true, clearCreatedCode: true);
    try {
      final repo = _ref.read(adminRepositoryProvider);
      final invite = await repo.createInvitation(roleTarget, expiresInHours);
      state = state.copyWith(creating: false, createdCode: invite.id);
      await load();
    } catch (e) {
      state = state.copyWith(creating: false, error: e.toString());
    }
  }

  Future<void> revoke(String inviteId) async {
    state = state.copyWith(revoking: {...state.revoking, inviteId});
    try {
      final repo = _ref.read(adminRepositoryProvider);
      await repo.revokeInvitation(inviteId);
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state = state.copyWith(revoking: {...state.revoking}..remove(inviteId));
    }
  }

  Future<void> refresh() async => load();
}

final _invitationsProvider =
    StateNotifierProvider.autoDispose<_InvitationsNotifier, _InvitationsState>(
        (ref) {
  return _InvitationsNotifier(ref);
});

// ── Screen ──

class InvitationsScreen extends ConsumerStatefulWidget {
  const InvitationsScreen({super.key});

  @override
  ConsumerState<InvitationsScreen> createState() => _InvitationsScreenState();
}

class _InvitationsScreenState extends ConsumerState<InvitationsScreen> {
  String _roleTarget = 'STD';
  int _expiresInHours = 48;
  bool _showForm = false;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(_invitationsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Invitations')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => setState(() => _showForm = !_showForm),
        child: Icon(_showForm ? Icons.close : Icons.add),
      ),
      body: Semantics(
        container: true,
        label: 'Gestion des invitations',
        child: Column(
          children: [
            // Filter
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  const Icon(Icons.filter_list, size: 20),
                  const SizedBox(width: 8),
                  ...['active', 'consumed', 'expired'].map((s) {
                    final selected = state.statusFilter == s;
                    return Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: FilterChip(
                        label: Text(_statusLabel(s),
                            style: const TextStyle(fontSize: 12)),
                        selected: selected,
                        onSelected: (v) => ref
                            .read(_invitationsProvider.notifier)
                            .setStatusFilter(v ? s : null),
                        visualDensity: VisualDensity.compact,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    );
                  }),
                ],
              ),
            ),

            // Create form
            if (_showForm) ...[
              Card(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Créer une invitation',
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              initialValue: _roleTarget,
                              decoration: const InputDecoration(
                                labelText: 'Rôle',
                                border: OutlineInputBorder(),
                                contentPadding: EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 8),
                              ),
                              items: const [
                                DropdownMenuItem(
                                    value: 'STD', child: Text('Élève')),
                                DropdownMenuItem(
                                    value: 'PAR', child: Text('Parent')),
                                DropdownMenuItem(
                                    value: 'TCH', child: Text('Enseignant')),
                                DropdownMenuItem(
                                    value: 'DIR', child: Text('Directeur')),
                              ],
                              onChanged: (v) {
                                if (v != null) setState(() => _roleTarget = v);
                              },
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: DropdownButtonFormField<int>(
                              initialValue: _expiresInHours,
                              decoration: const InputDecoration(
                                labelText: 'Expiration',
                                border: OutlineInputBorder(),
                                contentPadding: EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 8),
                              ),
                              items: const [
                                DropdownMenuItem(value: 24, child: Text('24h')),
                                DropdownMenuItem(value: 48, child: Text('48h')),
                                DropdownMenuItem(value: 72, child: Text('72h')),
                                DropdownMenuItem(
                                    value: 168, child: Text('7 jours')),
                              ],
                              onChanged: (v) {
                                if (v != null) {
                                  setState(() => _expiresInHours = v);
                                }
                              },
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: state.creating
                            ? null
                            : () => ref
                                .read(_invitationsProvider.notifier)
                                .createInvitation(_roleTarget, _expiresInHours),
                        child: state.creating
                            ? SizedBox(
                                height: 16,
                                width: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: theme.colorScheme.onPrimary,
                                ),
                              )
                            : const Text('Générer'),
                      ),
                      if (state.createdCode != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primaryContainer,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: SelectableText(
                                  state.createdCode!,
                                  style: TextStyle(
                                    fontFamily: 'monospace',
                                    fontWeight: FontWeight.bold,
                                    color: theme.colorScheme.primary,
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.copy, size: 18),
                                onPressed: () {
                                  Clipboard.setData(
                                      ClipboardData(text: state.createdCode!));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Code copié')),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],

            // Error banner
            if (state.error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Container(
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

            // List
            Expanded(child: _buildList(context, ref, state, theme)),
          ],
        ),
      ),
    );
  }

  Widget _buildList(BuildContext context, WidgetRef ref,
      _InvitationsState state, ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.mail_outline,
                size: 48, color: theme.colorScheme.outline),
            SizedBox(height: 16),
            Text('Aucune invitation'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_invitationsProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final inv = state.items[index];
          final isRevoking = state.revoking.contains(inv.id);

          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: _statusColor(theme, inv.status).withAlpha(30),
                child: Icon(Icons.mail, color: _statusColor(theme, inv.status)),
              ),
              title: Row(
                children: [
                  Text(inv.roleTarget,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(width: 8),
                  _InvStatusBadge(status: inv.status),
                ],
              ),
              subtitle: Text(
                'Expire: ${_formatDate(inv.expiresAt)}',
                style: theme.textTheme.bodySmall,
              ),
              trailing: inv.status == 'active'
                  ? isRevoking
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : IconButton(
                          icon: Icon(Icons.cancel_outlined,
                              color: theme.colorScheme.error),
                          onPressed: () => ref
                              .read(_invitationsProvider.notifier)
                              .revoke(inv.id),
                          tooltip: 'Révoquer',
                        )
                  : null,
            ),
          );
        },
      ),
    );
  }

  String _statusLabel(String s) {
    switch (s) {
      case 'active':
        return 'Actives';
      case 'consumed':
        return 'Utilisées';
      case 'expired':
        return 'Expirées';
      default:
        return s;
    }
  }

  Color _statusColor(ThemeData theme, String s) {
    switch (s) {
      case 'active':
        return theme.semanticPalette.success;
      case 'consumed':
        return theme.colorScheme.primary;
      case 'expired':
        return theme.colorScheme.outline;
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

class _InvStatusBadge extends StatelessWidget {
  final String status;

  const _InvStatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Color color;
    String label;
    switch (status) {
      case 'active':
        color = theme.semanticPalette.success;
        label = 'Active';
        break;
      case 'consumed':
        color = theme.colorScheme.primary;
        label = 'Utilisée';
        break;
      default:
        color = theme.colorScheme.outline;
        label = 'Expirée';
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
