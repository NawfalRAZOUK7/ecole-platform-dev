/// Shell screen — bottom navigation bar for main app sections.
///
/// Reference: DEC-E2-010 — Navigation with role-based tabs
/// Phase 5B: Added admin + teacher tabs.
/// Phase 10C: Added content library, student content, quiz player tabs.
/// Shows tabs based on user role.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/notifications/notifications_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class _NavItem {
  final String route;
  final IconData icon;
  final String labelKey;
  final List<String> roles;

  const _NavItem({
    required this.route,
    required this.icon,
    required this.labelKey,
    required this.roles,
  });
}

const _allNavItems = [
  // Admin tabs
  _NavItem(
      route: '/admin/dashboard',
      icon: Icons.dashboard,
      labelKey: 'shell.dashboard',
      roles: ['ADM', 'DIR']),
  _NavItem(
      route: '/admin/users',
      icon: Icons.people,
      labelKey: 'shell.users',
      roles: ['ADM', 'DIR']),
  _NavItem(
      route: '/analytics',
      icon: Icons.insights,
      labelKey: 'shell.analytics',
      roles: ['ADM', 'DIR']),
  _NavItem(
      route: '/budgets',
      icon: Icons.account_balance_wallet_outlined,
      labelKey: 'shell.budgets',
      roles: ['ADM', 'DIR']),
  _NavItem(
      route: '/micro-schools',
      icon: Icons.location_city_outlined,
      labelKey: 'shell.microSchools',
      roles: ['ADM', 'DIR', 'PAR']),
  // Teacher tabs
  _NavItem(
      route: '/teacher/classes',
      icon: Icons.class_,
      labelKey: 'shell.classes',
      roles: ['TCH']),
  _NavItem(
      route: '/teacher/content-library',
      icon: Icons.library_books,
      labelKey: 'shell.library',
      roles: ['TCH']),
  _NavItem(
      route: '/teacher/submissions',
      icon: Icons.grading,
      labelKey: 'shell.grading',
      roles: ['TCH']),
  _NavItem(
      route: '/teacher/quizzes',
      icon: Icons.quiz,
      labelKey: 'shell.teacherQuizzes',
      roles: ['TCH']),
  _NavItem(
      route: '/rubrics',
      icon: Icons.fact_check_outlined,
      labelKey: 'shell.rubrics',
      roles: ['TCH']),
  // Parent tabs
  _NavItem(
      route: '/family',
      icon: Icons.family_restroom,
      labelKey: 'shell.children',
      roles: ['PAR']),
  _NavItem(
      route: '/justification',
      icon: Icons.assignment_late,
      labelKey: 'shell.justification',
      roles: ['PAR']),
  // Student tabs (Phase 10C)
  _NavItem(
      route: '/student/content',
      icon: Icons.library_books,
      labelKey: 'shell.content',
      roles: ['STD']),
  _NavItem(
      route: '/student/quizzes',
      icon: Icons.quiz,
      labelKey: 'shell.quiz',
      roles: ['STD']),
  _NavItem(
      route: '/leaderboard',
      icon: Icons.emoji_events,
      labelKey: 'shell.leaderboard',
      roles: ['STD']),
  // Phase 12B tabs
  _NavItem(
      route: '/timetable',
      icon: Icons.calendar_view_week,
      labelKey: 'shell.timetable',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  _NavItem(
      route: '/calendar',
      icon: Icons.event_note,
      labelKey: 'shell.calendar',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  _NavItem(
      route: '/messages',
      icon: Icons.chat,
      labelKey: 'shell.messages',
      roles: ['PAR', 'TCH', 'ADM', 'DIR']),
  _NavItem(
      route: '/announcements',
      icon: Icons.campaign,
      labelKey: 'shell.announcements',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  // Common tabs
  _NavItem(
      route: '/feed',
      icon: Icons.newspaper,
      labelKey: 'shell.feed',
      roles: ['PAR']),
  _NavItem(
      route: '/notifications',
      icon: Icons.notifications,
      labelKey: 'shell.notifications',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  _NavItem(
      route: '/reports',
      icon: Icons.picture_as_pdf_outlined,
      labelKey: 'shell.reports',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  _NavItem(
      route: '/documents',
      icon: Icons.folder_open_outlined,
      labelKey: 'shell.documents',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  _NavItem(
      route: '/content',
      icon: Icons.library_books,
      labelKey: 'shell.content',
      roles: ['PAR', 'ADM']),
  _NavItem(
      route: '/results',
      icon: Icons.assessment,
      labelKey: 'shell.results',
      roles: ['STD', 'PAR']),
  // Phase 12C tabs
  _NavItem(
      route: '/progress',
      icon: Icons.trending_up,
      labelKey: 'shell.progress',
      roles: ['STD']),
  _NavItem(
      route: '/parent/progress',
      icon: Icons.trending_up,
      labelKey: 'shell.progress',
      roles: ['PAR']),
  _NavItem(
      route: '/invoices',
      icon: Icons.receipt_long,
      labelKey: 'shell.invoices',
      roles: ['PAR', 'ADM']),
  _NavItem(
      route: '/profile',
      icon: Icons.person,
      labelKey: 'shell.profile',
      roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP']),
];

class ShellScreen extends ConsumerWidget {
  final Widget child;

  const ShellScreen({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final notificationsState = ref.watch(notificationsProvider);
    final t = AppLocalizations.of(ref);
    final userRole = authState.user?.role ?? '';
    final visibleItems =
        _allNavItems.where((item) => item.roles.contains(userRole)).toList();
    final syncState = ref.watch(syncIndicatorProvider).value ??
        ref.watch(connectivityServiceProvider).indicator;

    final currentLocation = GoRouterState.of(context).matchedLocation;
    final currentIndex = visibleItems.indexWhere(
      (item) => currentLocation.startsWith(item.route),
    );

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 44,
        title: const Text('École Platform'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Row(
              children: [
                Icon(
                  syncState.online
                      ? Icons.cloud_done_outlined
                      : Icons.cloud_off_outlined,
                  color: syncState.online ? Colors.green : Colors.red,
                ),
                if (syncState.pendingCount > 0) ...[
                  const SizedBox(width: 6),
                  Text(
                    '${syncState.pendingCount}',
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex >= 0 ? currentIndex : 0,
        onDestinationSelected: (index) {
          context.go(visibleItems[index].route);
        },
        destinations: visibleItems
            .map((item) => NavigationDestination(
                  icon: _buildIcon(item, notificationsState.unreadCount),
                  label: t.t(item.labelKey),
                ))
            .toList(),
      ),
    );
  }

  Widget _buildIcon(_NavItem item, int unreadCount) {
    if (item.route != '/notifications' || unreadCount <= 0) {
      return Icon(item.icon);
    }

    return Stack(
      clipBehavior: Clip.none,
      children: [
        Icon(item.icon),
        Positioned(
          right: -6,
          top: -6,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: Colors.red,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              unreadCount > 99 ? '99+' : '$unreadCount',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
