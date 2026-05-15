/// User entity — represents the authenticated user profile.
///
/// Maps to GET /auth/me response (MeData schema).
class User {
  final String id;
  final String email;
  final String fullName;
  final String role;
  final String schoolId;
  final List<String> permissions;
  final List<Membership> memberships;

  const User({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.schoolId,
    required this.permissions,
    required this.memberships,
  });
}

class Membership {
  final String schoolId;
  final String role;
  final String status;

  const Membership({
    required this.schoolId,
    required this.role,
    required this.status,
  });
}
