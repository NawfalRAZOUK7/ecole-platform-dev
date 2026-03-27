/// Phase 13 notifications center screen.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/domain/entities/notification_item.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'notifications_provider.dart';

const _categoryFilters = <String>[
  '',
  'academic',
  'billing',
  'attendance',
  'system',
  'announcement',
];

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});

  @override
  ConsumerState<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController()
      ..addListener(() {
        if (_scrollController.position.pixels >=
            _scrollController.position.maxScrollExtent - 240) {
          ref.read(notificationsProvider.notifier).loadMore();
        }
      });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final state = ref.watch(notificationsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('notifications.title')),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: () => context.push('/settings/notifications'),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _categoryFilters.map((category) {
                  final isSelected = state.selectedCategory == category;
                  return FilterChip(
                    label: Text(_categoryLabel(category, t)),
                    selected: isSelected,
                    onSelected: (_) => ref
                        .read(notificationsProvider.notifier)
                        .setCategory(category),
                  );
                }).toList(),
              ),
            ),
          ),
          Expanded(
            child: _buildBody(context, ref, state, theme, t),
          ),
        ],
      ),
    );
  }

  Widget _buildBody(
    BuildContext context,
    WidgetRef ref,
    NotificationsState state,
    ThemeData theme,
    AppLocalizations t,
  ) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(notificationsProvider.notifier).load(),
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
            const Icon(Icons.notifications_none, size: 48, color: Colors.grey),
            const SizedBox(height: 16),
            Text(t.t('notifications.empty')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(notificationsProvider.notifier).refresh(),
      child: ListView.separated(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length + (state.isLoadingMore ? 1 : 0),
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          if (index >= state.items.length) {
            return const Center(child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ));
          }

          final notification = state.items[index];
          return Dismissible(
            key: ValueKey(notification.id),
            background: _swipeBackground(
              context,
              icon: notification.isRead
                  ? Icons.mark_email_unread_outlined
                  : Icons.mark_email_read_outlined,
              label: notification.isRead
                  ? t.t('notifications.markUnread')
                  : t.t('notifications.markRead'),
              color: theme.colorScheme.primary,
              alignment: Alignment.centerLeft,
            ),
            secondaryBackground: _swipeBackground(
              context,
              icon: Icons.delete_outline,
              label: t.t('notifications.delete'),
              color: theme.colorScheme.error,
              alignment: Alignment.centerRight,
            ),
            confirmDismiss: (direction) async {
              if (direction == DismissDirection.startToEnd) {
                await ref.read(notificationsProvider.notifier).markRead(
                      notification,
                      read: !notification.isRead,
                    );
                return false;
              }

              await ref
                  .read(notificationsProvider.notifier)
                  .deleteNotification(notification);
              return true;
            },
            child: Card(
              child: ListTile(
                onTap: () => _openNotification(context, ref, notification),
                leading: CircleAvatar(
                  backgroundColor: notification.isRead
                      ? theme.colorScheme.surfaceContainerHighest
                      : theme.colorScheme.primaryContainer,
                  child: Icon(
                    _categoryIcon(notification.category),
                    color: notification.isRead
                        ? theme.colorScheme.onSurfaceVariant
                        : theme.colorScheme.primary,
                  ),
                ),
                title: Text(
                  notification.title,
                  style: TextStyle(
                    fontWeight:
                        notification.isRead ? FontWeight.w500 : FontWeight.w700,
                  ),
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 4),
                    Text(
                      _categoryLabel(notification.category, t),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (notification.body != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        notification.body!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    const SizedBox(height: 6),
                    Text(
                      _formatDate(notification.createdAt),
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _openNotification(
    BuildContext context,
    WidgetRef ref,
    NotificationItem notification,
  ) async {
    if (!notification.isRead) {
      await ref
          .read(notificationsProvider.notifier)
          .markRead(notification, read: true);
    }
    final route = notification.actionUrl;
    if (route != null && route.isNotEmpty) {
      context.go(route);
      return;
    }
    context.go('/notifications');
  }

  Widget _swipeBackground(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color color,
    required Alignment alignment,
  }) {
    return Container(
      alignment: alignment,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: alignment == Alignment.centerLeft
            ? MainAxisAlignment.start
            : MainAxisAlignment.end,
        children: [
          if (alignment == Alignment.centerRight) ...[
            Text(label),
            const SizedBox(width: 8),
          ],
          Icon(icon, color: color),
          if (alignment == Alignment.centerLeft) ...[
            const SizedBox(width: 8),
            Text(label),
          ],
        ],
      ),
    );
  }

  String _categoryLabel(String category, AppLocalizations t) {
    switch (category) {
      case 'academic':
        return t.t('notifications.categoryAcademic');
      case 'billing':
        return t.t('notifications.categoryBilling');
      case 'attendance':
        return t.t('notifications.categoryAttendance');
      case 'system':
        return t.t('notifications.categorySystem');
      case 'announcement':
        return t.t('notifications.categoryAnnouncement');
      default:
        return t.t('notifications.categoryAll');
    }
  }

  IconData _categoryIcon(String category) {
    switch (category) {
      case 'academic':
        return Icons.school_outlined;
      case 'billing':
        return Icons.receipt_long_outlined;
      case 'attendance':
        return Icons.fact_check_outlined;
      case 'announcement':
        return Icons.campaign_outlined;
      default:
        return Icons.notifications_none_outlined;
    }
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat.yMMMd().add_Hm().format(date);
    } catch (_) {
      return dateStr;
    }
  }
}
