/// App router — go_router with auth guards and deep-link support.
///
/// Reference: DEC-E2-010 — Declarative routing with auth guards
/// Routes redirect to /login if not authenticated.
/// Role-based home redirect (PAR→/feed, STD→/content, etc.)

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/auth/login_screen.dart';
import 'package:ecole_platform/features/feed/feed_screen.dart';
import 'package:ecole_platform/features/notifications/notifications_screen.dart';
import 'package:ecole_platform/features/content/content_screen.dart';
import 'package:ecole_platform/features/results/results_screen.dart';
import 'package:ecole_platform/features/invoices/invoices_screen.dart';
import 'package:ecole_platform/features/profile/profile_screen.dart';
import 'package:ecole_platform/presentation/shell_screen.dart';

/// Role-based redirect targets.
const _roleRedirects = <String, String>{
  'PAR': '/feed',
  'STD': '/content',
  'TCH': '/content',
  'ADM': '/notifications',
  'DIR': '/notifications',
  'SUP': '/notifications',
};

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/login',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoading = authState.isLoading;
      final isLoginPage = state.matchedLocation == '/login';

      // Still loading — don't redirect
      if (isLoading) return null;

      // Not authenticated + not on login → go to login
      if (!isAuthenticated && !isLoginPage) return '/login';

      // Authenticated + on login → redirect to role home
      if (isAuthenticated && isLoginPage) {
        final role = authState.user?.role ?? '';
        return _roleRedirects[role] ?? '/profile';
      }

      return null; // no redirect needed
    },
    routes: [
      // Login (no shell)
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),

      // Shell with bottom navigation
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(
            path: '/feed',
            builder: (context, state) => const FeedScreen(),
          ),
          GoRoute(
            path: '/notifications',
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(
            path: '/content',
            builder: (context, state) => const ContentScreen(),
          ),
          GoRoute(
            path: '/results',
            builder: (context, state) => const ResultsScreen(),
          ),
          GoRoute(
            path: '/invoices',
            builder: (context, state) => const InvoicesScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
    ],
  );
});
