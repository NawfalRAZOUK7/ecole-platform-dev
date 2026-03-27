/// Shell screen — bottom navigation bar for main app sections.
///
/// Reference: DEC-E2-010 — Navigation with role-based tabs
/// Phase 5B: Added admin + teacher tabs.
/// Phase 10C: Added content library, student content, quiz player tabs.
/// Shows tabs based on user role.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/features/auth/auth_provider.dart';

class _NavItem {
  final String route;
  final IconData icon;
  final String label;
  final List<String> roles;

  const _NavItem({
    required this.route,
    required this.icon,
    required this.label,
    required this.roles,
  });
}

const _allNavItems = [
  // Admin tabs
  _NavItem(route: '/admin/dashboard', icon: Icons.dashboard, label: 'Dashboard', roles: ['ADM', 'DIR']),
  _NavItem(route: '/admin/users', icon: Icons.people, label: 'Utilisateurs', roles: ['ADM']),
  // Teacher tabs
  _NavItem(route: '/teacher/classes', icon: Icons.class_, label: 'Classes', roles: ['TCH']),
  _NavItem(route: '/teacher/content-library', icon: Icons.library_books, label: 'Bibliothèque', roles: ['TCH']),
  _NavItem(route: '/teacher/submissions', icon: Icons.grading, label: 'Notes', roles: ['TCH']),
  // Parent tabs
  _NavItem(route: '/family', icon: Icons.family_restroom, label: 'Enfants', roles: ['PAR']),
  // Student tabs (Phase 10C)
  _NavItem(route: '/student/content', icon: Icons.library_books, label: 'Contenu', roles: ['STD']),
  _NavItem(route: '/student/quizzes', icon: Icons.quiz, label: 'Quiz', roles: ['STD']),
  // Phase 12B tabs
  _NavItem(route: '/timetable', icon: Icons.calendar_view_week, label: 'Emploi du temps', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  _NavItem(route: '/messages', icon: Icons.chat, label: 'Messages', roles: ['PAR', 'TCH', 'ADM', 'DIR']),
  _NavItem(route: '/announcements', icon: Icons.campaign, label: 'Annonces', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR']),
  // Common tabs
  _NavItem(route: '/feed', icon: Icons.newspaper, label: 'Feed', roles: ['PAR']),
  _NavItem(route: '/notifications', icon: Icons.notifications, label: 'Notifs', roles: ['PAR', 'TCH', 'ADM', 'DIR']),
  _NavItem(route: '/content', icon: Icons.library_books, label: 'Contenu', roles: ['PAR', 'ADM']),
  _NavItem(route: '/results', icon: Icons.assessment, label: 'Résultats', roles: ['STD', 'PAR']),
  _NavItem(route: '/invoices', icon: Icons.receipt_long, label: 'Factures', roles: ['PAR', 'ADM']),
  _NavItem(route: '/profile', icon: Icons.person, label: 'Profil', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP']),
];

class ShellScreen extends ConsumerWidget {
  final Widget child;

  const ShellScreen({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final userRole = authState.user?.role ?? '';
    final visibleItems = _allNavItems
        .where((item) => item.roles.contains(userRole))
        .toList();

    final currentLocation = GoRouterState.of(context).matchedLocation;
    final currentIndex = visibleItems.indexWhere(
      (item) => currentLocation.startsWith(item.route),
    );

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex >= 0 ? currentIndex : 0,
        onDestinationSelected: (index) {
          context.go(visibleItems[index].route);
        },
        destinations: visibleItems
            .map((item) => NavigationDestination(
                  icon: Icon(item.icon),
                  label: item.label,
                ))
            .toList(),
      ),
    );
  }
}
