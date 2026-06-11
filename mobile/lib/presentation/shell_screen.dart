/// Shell screen — bottom navigation bar for main app sections.
///
/// Reference: DEC-E2-010 — Navigation with role-based tabs
/// Phase 5B: Added admin + teacher tabs.
/// Phase 10C: Added content library, student content, quiz player tabs.
/// Shows tabs based on user role.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/communication/notifications/notifications_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/age_theme.dart';
import 'package:ecole_platform/shared/ui/design_context.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

class _NavItem {
  final String route;
  final IconData icon;
  final String labelKey;
  final List<String> roles;
  final String groupKey;

  const _NavItem({
    required this.route,
    required this.icon,
    required this.labelKey,
    required this.roles,
    this.groupKey = 'shell.group.academic',
  });
}

const _allNavItems = [
  // Admin tabs
  _NavItem(
    route: '/admin/dashboard',
    icon: Icons.dashboard,
    labelKey: 'shell.dashboard',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.administration',
  ),
  _NavItem(
    route: '/admin/users',
    icon: Icons.people,
    labelKey: 'shell.users',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.administration',
  ),
  _NavItem(
    route: '/admin/invitations',
    icon: Icons.mark_email_unread_outlined,
    labelKey: 'admin.invitations',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.administration',
  ),
  _NavItem(
    route: '/admin/justifications',
    icon: Icons.pending_actions_outlined,
    labelKey: 'admin.approvals',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.administration',
  ),
  _NavItem(
    route: '/admin/features',
    icon: Icons.toggle_on_outlined,
    labelKey: 'admin.featureToggles',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.administration',
  ),
  _NavItem(
    route: '/admin/school',
    icon: Icons.school_outlined,
    labelKey: 'admin.schoolSettings',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.administration',
  ),
  _NavItem(
    route: '/analytics',
    icon: Icons.insights,
    labelKey: 'shell.analytics',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.analytics',
  ),
  _NavItem(
    route: '/budgets',
    icon: Icons.account_balance_wallet_outlined,
    labelKey: 'shell.budgets',
    roles: ['ADM', 'DIR'],
    groupKey: 'shell.group.finance',
  ),
  _NavItem(
    route: '/micro-schools',
    icon: Icons.location_city_outlined,
    labelKey: 'shell.microSchools',
    roles: ['EDUCATOR', 'ADM', 'DIR', 'PAR'],
    groupKey: 'shell.group.administration',
  ),
  // Teacher tabs
  _NavItem(
    route: '/teacher/classes',
    icon: Icons.class_,
    labelKey: 'shell.classes',
    roles: ['TCH'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/teacher/content-library',
    icon: Icons.library_books,
    labelKey: 'shell.library',
    roles: ['TCH'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/teacher/submissions',
    icon: Icons.grading,
    labelKey: 'shell.grading',
    roles: ['TCH'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/teacher/quizzes',
    icon: Icons.quiz,
    labelKey: 'shell.teacherQuizzes',
    roles: ['TCH'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/rubrics',
    icon: Icons.fact_check_outlined,
    labelKey: 'shell.rubrics',
    roles: ['TCH'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/question-bank',
    icon: Icons.menu_book_outlined,
    labelKey: 'shell.questionBank',
    roles: ['TCH'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/teacher/class-progress',
    icon: Icons.analytics_outlined,
    labelKey: 'shell.classProgress',
    roles: ['TCH'],
    groupKey: 'shell.group.analytics',
  ),
  // Parent tabs
  _NavItem(
    route: '/family',
    icon: Icons.family_restroom,
    labelKey: 'shell.children',
    roles: ['PAR'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/justification',
    icon: Icons.assignment_late,
    labelKey: 'shell.justification',
    roles: ['PAR'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/student/home',
    icon: Icons.home_outlined,
    labelKey: 'shell.home',
    roles: ['STD'],
    groupKey: 'shell.group.academic',
  ),
  // Student tabs (Phase 10C)
  _NavItem(
    route: '/student/content',
    icon: Icons.library_books,
    labelKey: 'shell.content',
    roles: ['STD'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/student/quizzes',
    icon: Icons.quiz,
    labelKey: 'shell.quiz',
    roles: ['STD'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/leaderboard',
    icon: Icons.emoji_events,
    labelKey: 'shell.leaderboard',
    roles: ['STD'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/rewards',
    icon: Icons.workspace_premium_outlined,
    labelKey: 'shell.rewards',
    roles: ['STD'],
    groupKey: 'shell.group.academic',
  ),
  // Phase 12B tabs
  _NavItem(
    route: '/timetable',
    icon: Icons.calendar_view_week,
    labelKey: 'shell.timetable',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/calendar',
    icon: Icons.event_note,
    labelKey: 'shell.calendar',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR'],
    groupKey: 'shell.group.communication',
  ),
  _NavItem(
    route: '/messages',
    icon: Icons.chat,
    labelKey: 'shell.messages',
    roles: ['PAR', 'TCH', 'ADM', 'DIR'],
    groupKey: 'shell.group.communication',
  ),
  _NavItem(
    route: '/announcements',
    icon: Icons.campaign,
    labelKey: 'shell.announcements',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR'],
    groupKey: 'shell.group.communication',
  ),
  // Common tabs
  _NavItem(
    route: '/feed',
    icon: Icons.newspaper,
    labelKey: 'shell.feed',
    roles: ['PAR'],
    groupKey: 'shell.group.communication',
  ),
  _NavItem(
    route: '/notifications',
    icon: Icons.notifications,
    labelKey: 'shell.notifications',
    roles: ['PAR', 'STD', 'TCH', 'EDUCATOR', 'ADM', 'DIR'],
    groupKey: 'shell.group.communication',
  ),
  _NavItem(
    route: '/reports',
    icon: Icons.picture_as_pdf_outlined,
    labelKey: 'shell.reports',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR'],
    groupKey: 'shell.group.analytics',
  ),
  _NavItem(
    route: '/documents',
    icon: Icons.folder_open_outlined,
    labelKey: 'shell.documents',
    roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/content',
    icon: Icons.library_books,
    labelKey: 'shell.content',
    roles: ['PAR', 'ADM'],
    groupKey: 'shell.group.academic',
  ),
  _NavItem(
    route: '/results',
    icon: Icons.assessment,
    labelKey: 'shell.results',
    roles: ['STD', 'PAR'],
    groupKey: 'shell.group.academic',
  ),
  // Phase 12C tabs
  _NavItem(
    route: '/progress',
    icon: Icons.trending_up,
    labelKey: 'shell.progress',
    roles: ['STD'],
    groupKey: 'shell.group.analytics',
  ),
  _NavItem(
    route: '/parent/progress',
    icon: Icons.trending_up,
    labelKey: 'shell.progress',
    roles: ['PAR'],
    groupKey: 'shell.group.analytics',
  ),
  _NavItem(
    route: '/invoices',
    icon: Icons.receipt_long,
    labelKey: 'shell.invoices',
    roles: ['PAR', 'ADM'],
    groupKey: 'shell.group.finance',
  ),
  _NavItem(
    route: '/profile',
    icon: Icons.person,
    labelKey: 'shell.profile',
    roles: ['PAR', 'STD', 'TCH', 'EDUCATOR', 'ADM', 'DIR', 'SUP'],
    groupKey: 'shell.group.account',
  ),
];

const _primaryRoutesByRole = <String, List<String>>{
  'ADM': ['/admin/dashboard', '/admin/users', '/analytics', '/budgets'],
  'DIR': ['/admin/dashboard', '/analytics', '/budgets', '/reports'],
  'TCH': [
    '/teacher/classes',
    '/teacher/content-library',
    '/teacher/submissions',
    '/teacher/class-progress',
  ],
  'PAR': ['/family', '/results', '/invoices', '/messages'],
  'STD': ['/student/home', '/student/content', '/student/quizzes', '/progress'],
  'EDUCATOR': ['/micro-schools', '/notifications', '/profile'],
  'SUP': ['/notifications', '/profile'],
};

const _groupOrder = [
  'shell.group.academic',
  'shell.group.communication',
  'shell.group.analytics',
  'shell.group.finance',
  'shell.group.administration',
  'shell.group.account',
];

final shellStudentAgeTierProvider =
    FutureProvider.family<AgeTier, String?>((ref, userId) async {
  if (userId == null) return AgeTier.primaire;
  final repo = ref.read(authRepositoryProvider);
  try {
    final profile = await repo.getProfile();
    final student = profile['student_profile'] as Map<String, dynamic>?;
    return resolveAgeTier(
      niveau: student?['class_level'] as String?,
      dob: student?['date_of_birth'] as String?,
    );
  } catch (_) {
    return AgeTier.primaire;
  }
});

@visibleForTesting
List<String> primaryNavigationRoutesForRole(String role) {
  return List.unmodifiable(_primaryRoutesByRole[role] ?? const <String>[]);
}

@visibleForTesting
List<String> secondaryNavigationRoutesForRole(String role) {
  final primaryRoutes = _primaryRoutesByRole[role] ?? const <String>[];
  return _allNavItems
      .where((item) => item.roles.contains(role))
      .where((item) => !primaryRoutes.contains(item.route))
      .map((item) => item.route)
      .toList(growable: false);
}

class ShellScreen extends ConsumerWidget {
  final Widget child;

  const ShellScreen({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final notificationsState = ref.watch(notificationsProvider);
    final t = AppLocalizations.of(ref);
    final userRole = authState.user?.role ?? '';
    final user = authState.user;
    final roleAccent = AppColors.roleAccentFor(userRole);
    final isStudent = userRole == 'STD';
    final ageTier = isStudent
        ? ref.watch(shellStudentAgeTierProvider(user?.id)).value ??
            AgeTier.primaire
        : AgeTier.primaire;
    final kidsPalette = Theme.of(context).brightness == Brightness.dark
        ? KidsThemeColors.dark
        : KidsThemeColors.light;
    final visibleItems =
        _allNavItems.where((item) => item.roles.contains(userRole)).toList();
    final primaryRoutes = _primaryRoutesByRole[userRole] ?? const <String>[];
    final primaryItems = primaryRoutes
        .map((route) => _itemForRoute(visibleItems, route))
        .whereType<_NavItem>()
        .toList();
    final secondaryItems = visibleItems
        .where((item) => !primaryRoutes.contains(item.route))
        .toList();
    final syncState = ref.watch(syncIndicatorProvider).value ??
        ref.watch(connectivityServiceProvider).indicator;

    final currentLocation = GoRouterState.of(context).matchedLocation;
    final designMode = resolveSchoolDesignMode(
      role: userRole,
      route: currentLocation,
      schoolType: user?.schoolType,
      designMode: user?.designMode,
      schoolSettings: user?.schoolSettings,
    );
    final currentPrimaryIndex = primaryItems.indexWhere(
      (item) => _matchesRoute(currentLocation, item.route),
    );
    final currentSecondaryIndex = secondaryItems.indexWhere(
      (item) => _matchesRoute(currentLocation, item.route),
    );
    final showMoreDestination = secondaryItems.isNotEmpty;
    final selectedIndex = currentPrimaryIndex >= 0
        ? currentPrimaryIndex
        : currentSecondaryIndex >= 0 && showMoreDestination
            ? primaryItems.length
            : 0;

    final scaffold = Scaffold(
      appBar: AppBar(
        toolbarHeight: 44,
        title: const Text('École Platform'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(3),
          child: Container(
            height: 3,
            color: roleAccent,
          ),
        ),
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
      bottomNavigationBar: NavigationBarTheme(
        data: Theme.of(context).navigationBarTheme.copyWith(
              backgroundColor: isStudent ? kidsPalette.surface : null,
              indicatorColor: roleAccent.withValues(alpha: 0.18),
              labelTextStyle: WidgetStateProperty.resolveWith(
                (states) => Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: states.contains(WidgetState.selected)
                          ? roleAccent
                          : Theme.of(context).colorScheme.onSurfaceVariant,
                      fontSize: 11,
                      fontWeight: states.contains(WidgetState.selected)
                          ? FontWeight.w700
                          : FontWeight.w500,
                    ),
              ),
            ),
        child: NavigationBar(
          selectedIndex: selectedIndex,
          onDestinationSelected: (index) {
            HapticFeedback.lightImpact();
            if (index < primaryItems.length) {
              context.go(primaryItems[index].route);
              return;
            }
            _showMoreSheet(
              context,
              t,
              secondaryItems,
              notificationsState.unreadCount,
              roleAccent,
            );
          },
          destinations: [
            ...primaryItems.map(
              (item) => NavigationDestination(
                icon: _buildIcon(item, notificationsState.unreadCount),
                label: t.t(item.labelKey),
              ),
            ),
            if (showMoreDestination)
              NavigationDestination(
                icon: _buildMoreIcon(
                  secondaryItems,
                  notificationsState.unreadCount,
                ),
                label: t.t('shell.more'),
              ),
          ],
        ),
      ),
    );

    if (isStudent) {
      return AgeThemedView(
        tier: ageTier,
        useKidsColors: true,
        child: scaffold,
      );
    }

    if (designMode == SchoolDesignMode.informal) {
      return Theme(
        data: applyInformalSchoolTheme(Theme.of(context)),
        child: scaffold,
      );
    }

    return scaffold;
  }

  bool _matchesRoute(String currentLocation, String route) {
    return currentLocation == route || currentLocation.startsWith('$route/');
  }

  _NavItem? _itemForRoute(List<_NavItem> items, String route) {
    for (final item in items) {
      if (item.route == route) {
        return item;
      }
    }
    return null;
  }

  Widget _buildMoreIcon(List<_NavItem> items, int unreadCount) {
    final hasUnread =
        unreadCount > 0 && items.any((item) => item.route == '/notifications');
    if (!hasUnread) {
      return const Icon(Icons.more_horiz);
    }
    return Stack(
      clipBehavior: Clip.none,
      children: [
        const Icon(Icons.more_horiz),
        Positioned(
          right: -6,
          top: -6,
          child: _Badge(count: unreadCount),
        ),
      ],
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
          child: _Badge(count: unreadCount),
        ),
      ],
    );
  }

  void _showMoreSheet(
    BuildContext context,
    AppLocalizations t,
    List<_NavItem> items,
    int unreadCount,
    Color roleAccent,
  ) {
    final groupedItems = <String, List<_NavItem>>{};
    for (final groupKey in _groupOrder) {
      final groupItems =
          items.where((item) => item.groupKey == groupKey).toList();
      if (groupItems.isNotEmpty) {
        groupedItems[groupKey] = groupItems;
      }
    }

    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) {
        final theme = Theme.of(sheetContext);
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
            children: [
              Text(
                t.t('shell.moreFeatures'),
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              for (final entry in groupedItems.entries) ...[
                Padding(
                  padding: const EdgeInsets.only(top: 12, bottom: 6),
                  child: Text(
                    t.t(entry.key),
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: roleAccent,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                ...entry.value.map(
                  (item) => ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(item.icon, color: roleAccent),
                    title: Text(t.t(item.labelKey)),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.of(sheetContext).pop();
                      context.go(item.route);
                    },
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _Badge extends StatelessWidget {
  final int count;

  const _Badge({required this.count});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
      decoration: BoxDecoration(
        color: Colors.red,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        count > 99 ? '99+' : '$count',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
