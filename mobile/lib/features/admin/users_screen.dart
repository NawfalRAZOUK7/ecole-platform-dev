/// Admin users screen — user list with search, role change, suspend/activate.
///
/// Reference: Phase 5B (from 4A)

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/admin/admin.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/motion.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/widgets/animated_entrance.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/search_filter_bar.dart';

// ── State ──

class _UsersState {
  final List<ManagedUser> items;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String search;
  final String? roleFilter;
  final String? statusFilter;
  final Set<String> actionLoading;

  const _UsersState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.search = '',
    this.roleFilter,
    this.statusFilter,
    this.actionLoading = const {},
  });

  _UsersState copyWith({
    List<ManagedUser>? items,
    bool? isLoading,
    bool? isLoadingMore,
    String? error,
    bool clearError = false,
    String? nextCursor,
    bool? hasMore,
    String? search,
    String? roleFilter,
    bool clearRoleFilter = false,
    String? statusFilter,
    bool clearStatusFilter = false,
    Set<String>? actionLoading,
  }) {
    return _UsersState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      error: clearError ? null : (error ?? this.error),
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
      search: search ?? this.search,
      roleFilter: clearRoleFilter ? null : (roleFilter ?? this.roleFilter),
      statusFilter:
          clearStatusFilter ? null : (statusFilter ?? this.statusFilter),
      actionLoading: actionLoading ?? this.actionLoading,
    );
  }
}

class _UsersNotifier extends StateNotifier<_UsersState> {
  final Ref _ref;
  Timer? _debounce;

  _UsersNotifier(this._ref) : super(const _UsersState(isLoading: true)) {
    load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true, items: []);
    try {
      final repo = _ref.read(adminRepositoryProvider);
      final result = await repo.getUsers(
        search: state.search.isNotEmpty ? state.search : null,
        role: state.roleFilter,
        status: state.statusFilter,
      );
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

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    state = state.copyWith(isLoadingMore: true);
    try {
      final repo = _ref.read(adminRepositoryProvider);
      final result = await repo.getUsers(
        cursor: state.nextCursor,
        search: state.search.isNotEmpty ? state.search : null,
        role: state.roleFilter,
        status: state.statusFilter,
      );
      state = state.copyWith(
        items: [...state.items, ...result.items],
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: e.toString());
    }
  }

  void setSearch(String value) {
    state = state.copyWith(search: value);
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), load);
  }

  void setRoleFilter(String? value) {
    state = value == null
        ? state.copyWith(clearRoleFilter: true)
        : state.copyWith(roleFilter: value);
    load();
  }

  void setStatusFilter(String? value) {
    state = value == null
        ? state.copyWith(clearStatusFilter: true)
        : state.copyWith(statusFilter: value);
    load();
  }

  Future<void> suspendUser(String userId) async {
    state = state.copyWith(actionLoading: {...state.actionLoading, userId});
    try {
      final repo = _ref.read(adminRepositoryProvider);
      await repo.suspendUser(userId);
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state = state.copyWith(
        actionLoading: {...state.actionLoading}..remove(userId),
      );
    }
  }

  Future<void> activateUser(String userId) async {
    state = state.copyWith(actionLoading: {...state.actionLoading, userId});
    try {
      final repo = _ref.read(adminRepositoryProvider);
      await repo.activateUser(userId);
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state = state.copyWith(
        actionLoading: {...state.actionLoading}..remove(userId),
      );
    }
  }

  Future<void> changeRole(String userId, String newRole) async {
    state = state.copyWith(actionLoading: {...state.actionLoading, userId});
    try {
      final repo = _ref.read(adminRepositoryProvider);
      await repo.changeUserRole(userId, newRole);
      await load();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    } finally {
      state = state.copyWith(
        actionLoading: {...state.actionLoading}..remove(userId),
      );
    }
  }

  Future<void> refresh() async => load();
}

final _usersProvider =
    StateNotifierProvider.autoDispose<_UsersNotifier, _UsersState>((ref) {
  return _UsersNotifier(ref);
});

// ── Screen ──

class UsersScreen extends ConsumerWidget {
  const UsersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(_usersProvider);
    final currentUserId = ref.watch(authProvider).user?.id;
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('shell.users'))),
      body: Column(
        children: [
          SearchFilterBar(
            searchHint: t.t('users.searchHint'),
            searchValue: state.search,
            onSearchChanged: (v) =>
                ref.read(_usersProvider.notifier).setSearch(v),
            filters: [
              FilterGroup(
                id: 'role',
                label: t.t('users.filter.role'),
                options: [
                  FilterOption(label: t.t('common.all'), value: null),
                  FilterOption(label: t.t('roles.ADM'), value: 'ADM'),
                  FilterOption(label: t.t('roles.DIR'), value: 'DIR'),
                  FilterOption(label: t.t('roles.TCH'), value: 'TCH'),
                  FilterOption(label: t.t('roles.PAR'), value: 'PAR'),
                  FilterOption(label: t.t('roles.STD'), value: 'STD'),
                ],
              ),
              FilterGroup(
                id: 'status',
                label: t.t('users.filter.status'),
                options: [
                  FilterOption(label: t.t('common.all'), value: null),
                  FilterOption(
                    label: t.t('users.status.active'),
                    value: 'active',
                  ),
                  FilterOption(
                    label: t.t('users.status.suspended'),
                    value: 'suspended',
                  ),
                  FilterOption(
                    label: t.t('users.status.inactive'),
                    value: 'inactive',
                  ),
                ],
              ),
            ],
            filterValues: {
              'role': state.roleFilter,
              'status': state.statusFilter,
            },
            onFilterChanged: (id, value) {
              if (id == 'role') {
                ref.read(_usersProvider.notifier).setRoleFilter(value);
              } else {
                ref.read(_usersProvider.notifier).setStatusFilter(value);
              }
            },
          ),
          Expanded(
            child: _buildList(context, ref, state, theme, currentUserId),
          ),
        ],
      ),
    );
  }

  Widget _buildList(
    BuildContext context,
    WidgetRef ref,
    _UsersState state,
    ThemeData theme,
    String? currentUserId,
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
              onPressed: () => ref.read(_usersProvider.notifier).load(),
              child: Text(t.t('common.retry')),
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
            Icon(
              Icons.people_outline,
              size: 48,
              color: theme.colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(t.t('users.empty')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(_usersProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length + (state.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == state.items.length) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Center(
                child: state.isLoadingMore
                    ? const CircularProgressIndicator()
                    : TextButton(
                        onPressed: () =>
                            ref.read(_usersProvider.notifier).loadMore(),
                        child: Text(t.t('common.loadMore')),
                      ),
              ),
            );
          }

          final user = state.items[index];
          final isSelf = user.id == currentUserId;
          final isActionLoading = state.actionLoading.contains(user.id);

          return AnimatedEntrance(
            delay: AnimatedEntrance.stagger(index),
            child: Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 20,
                        backgroundColor: theme.colorScheme.primaryContainer,
                        child: Text(
                          user.fullName.isNotEmpty
                              ? user.fullName[0].toUpperCase()
                              : '?',
                          style: TextStyle(
                            color: theme.colorScheme.primary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Flexible(
                                  child: Text(
                                    user.fullName,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                    ),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                if (user.emailVerified) ...[
                                  const SizedBox(width: 4),
                                  Icon(
                                    Icons.verified,
                                    size: 14,
                                    color: theme.colorScheme.primary,
                                  ),
                                ],
                                if (user.totpEnabled) ...[
                                  const SizedBox(width: 4),
                                  Icon(
                                    Icons.lock,
                                    size: 14,
                                    color: theme.semanticPalette.warning,
                                  ),
                                ],
                              ],
                            ),
                            Text(
                              user.email,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ),
                      _StatusBadge(status: user.status),
                    ],
                  ),
                  if (!isSelf) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        // Role selector
                        DropdownButton<String>(
                          value: user.role,
                          isDense: true,
                          underline: const SizedBox.shrink(),
                          items: [
                            DropdownMenuItem(
                              value: 'ADM',
                              child: Text(t.t('roles.ADM')),
                            ),
                            DropdownMenuItem(
                              value: 'DIR',
                              child: Text(t.t('roles.DIR')),
                            ),
                            DropdownMenuItem(
                              value: 'TCH',
                              child: Text(t.t('roles.TCH')),
                            ),
                            DropdownMenuItem(
                              value: 'PAR',
                              child: Text(t.t('roles.PAR')),
                            ),
                            DropdownMenuItem(
                              value: 'STD',
                              child: Text(t.t('roles.STD')),
                            ),
                          ],
                          onChanged: isActionLoading
                              ? null
                              : (v) {
                                  if (v != null && v != user.role) {
                                    ref
                                        .read(_usersProvider.notifier)
                                        .changeRole(user.id, v);
                                  }
                                },
                        ),
                        const Spacer(),
                        if (isActionLoading)
                          const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        else if (user.status == 'active')
                          TextButton(
                            onPressed: () => ref
                                .read(_usersProvider.notifier)
                                .suspendUser(user.id),
                            child: Text(
                              t.t('users.suspend'),
                              style: TextStyle(color: theme.colorScheme.error),
                            ),
                          )
                        else
                          TextButton(
                            onPressed: () => ref
                                .read(_usersProvider.notifier)
                                .activateUser(user.id),
                            child: Text(t.t('users.activate')),
                          ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            ),
          );
        },
      ),
    );
  }
}

class _StatusBadge extends ConsumerWidget {
  final String status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);
    Color color;
    switch (status) {
      case 'active':
        color = theme.semanticPalette.success;
        break;
      case 'suspended':
        color = theme.colorScheme.error;
        break;
      default:
        color = theme.colorScheme.outline;
    }
    final label = t.t('users.status.$status');
    return AnimatedSwitcher(
      duration: AppMotion.standard,
      transitionBuilder: (child, animation) =>
          FadeTransition(opacity: animation, child: child),
      child: Container(
        key: ValueKey<String>(status),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(
          border: Border.all(color: color),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            color: color,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
