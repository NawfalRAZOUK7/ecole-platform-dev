/// App router — go_router with auth guards and deep-link support.
///
/// Reference: DEC-E2-010 — Declarative routing with auth guards
/// Routes redirect to /login if not authenticated.
/// Role-based home redirect (PAR→/feed, STD→/content, etc.)
/// Phase 5A: Added 2FA setup, password change, submission upload routes.
/// Phase 5B: Added admin + teacher routes.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/auth/login_screen.dart';
import 'package:ecole_platform/features/auth/register_screen.dart';
import 'package:ecole_platform/features/feed/feed_screen.dart';
import 'package:ecole_platform/features/notifications/notifications_screen.dart';
import 'package:ecole_platform/features/content/content_screen.dart';
import 'package:ecole_platform/features/results/results_screen.dart';
import 'package:ecole_platform/features/invoices/invoices_screen.dart';
import 'package:ecole_platform/features/profile/profile_screen.dart';
import 'package:ecole_platform/features/profile/two_factor_setup_screen.dart';
import 'package:ecole_platform/features/profile/change_password_screen.dart';
import 'package:ecole_platform/features/submissions/submission_upload_screen.dart';
import 'package:ecole_platform/features/admin/admin_dashboard_screen.dart';
import 'package:ecole_platform/features/admin/users_screen.dart';
import 'package:ecole_platform/features/admin/invitations_screen.dart';
import 'package:ecole_platform/features/admin/justification_review_screen.dart';
import 'package:ecole_platform/features/teacher/classes_screen.dart';
import 'package:ecole_platform/features/teacher/assignment_form_screen.dart';
import 'package:ecole_platform/features/teacher/submissions_screen.dart';
import 'package:ecole_platform/features/teacher/attendance_screen.dart';
import 'package:ecole_platform/features/family/my_children_screen.dart';
import 'package:ecole_platform/presentation/shell_screen.dart';

/// Role-based redirect targets.
const _roleRedirects = <String, String>{
  'PAR': '/feed',
  'STD': '/content',
  'TCH': '/teacher/classes',
  'ADM': '/admin/dashboard',
  'DIR': '/admin/dashboard',
  'SUP': '/notifications',
};

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/login',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoading = authState.isLoading;
      final loc = state.matchedLocation;
      final isPublicPage = loc == '/login' || loc == '/register';

      // Still loading — don't redirect
      if (isLoading) return null;

      // Not authenticated + not on public page → go to login
      if (!isAuthenticated && !isPublicPage) return '/login';

      // Authenticated + on public page → redirect to role home
      if (isAuthenticated && isPublicPage) {
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

      // Register (no shell) — Phase 5C
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // Shell with bottom navigation
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          // ── Admin routes ──
          GoRoute(
            path: '/admin/dashboard',
            builder: (context, state) => const AdminDashboardScreen(),
          ),
          GoRoute(
            path: '/admin/users',
            builder: (context, state) => const UsersScreen(),
          ),
          GoRoute(
            path: '/admin/invitations',
            builder: (context, state) => const InvitationsScreen(),
          ),
          GoRoute(
            path: '/admin/justifications',
            builder: (context, state) => const JustificationReviewScreen(),
          ),

          // ── Teacher routes ──
          GoRoute(
            path: '/teacher/classes',
            builder: (context, state) => const ClassesScreen(),
          ),
          GoRoute(
            path: '/teacher/assignments',
            builder: (context, state) => const AssignmentFormScreen(),
          ),
          GoRoute(
            path: '/teacher/submissions',
            builder: (context, state) =>
                const SubmissionsScreen(),
          ),
          GoRoute(
            path: '/teacher/attendance',
            builder: (context, state) => const AttendanceScreen(),
          ),

          // ── Parent routes ──
          GoRoute(
            path: '/family',
            builder: (context, state) => const MyChildrenScreen(),
          ),

          // ── Common routes ──
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
            routes: [
              GoRoute(
                path: '2fa',
                builder: (context, state) => const TwoFactorSetupScreen(),
              ),
              GoRoute(
                path: 'password',
                builder: (context, state) => const ChangePasswordScreen(),
              ),
            ],
          ),
        ],
      ),

      // Submission upload (outside shell — full screen)
      GoRoute(
        path: '/submissions/upload',
        builder: (context, state) {
          final extra = state.extra as Map<String, String>?;
          return SubmissionUploadScreen(
            assignmentId: extra?['assignment_id'],
            assignmentTitle: extra?['assignment_title'],
          );
        },
      ),
    ],
  );
});
