/// Shell screen — bottom navigation bar for main app sections.
///
/// Reference: DEC-E2-010 — Navigation with role-based tabs
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
  _NavItem(route: '/feed', icon: Icons.newspaper, label: 'Feed', roles: ['PAR']),
  _NavItem(route: '/notifications', icon: Icons.notifications, label: 'Notifications', roles: ['PAR', 'TCH', 'ADM', 'DIR']),
  _NavItem(route: '/content', icon: Icons.library_books, label: 'Content', roles: ['STD', 'PAR', 'TCH', 'ADM']),
  _NavItem(route: '/results', icon: Icons.assessment, label: 'Results', roles: ['STD', 'PAR']),
  _NavItem(route: '/invoices', icon: Icons.receipt_long, label: 'Invoices', roles: ['PAR', 'ADM']),
  _NavItem(route: '/profile', icon: Icons.person, label: 'Profile', roles: ['PAR', 'STD', 'TCH', 'ADM', 'DIR', 'SUP']),
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
