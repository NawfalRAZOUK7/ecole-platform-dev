/// Admin domain entities — dashboard stats, managed users, invitations, justifications.
///
/// Reference: Phase 5B (from 4A)

class DashboardStats {
  final int totalUsers;
  final int activeSessions;
  final int activeInvitations;
  final int auditEvents24h;
  final int pendingJustifications;
  final Map<String, int> usersByRole;

  const DashboardStats({
    required this.totalUsers,
    required this.activeSessions,
    required this.activeInvitations,
    required this.auditEvents24h,
    required this.pendingJustifications,
    required this.usersByRole,
  });
}

class ManagedUser {
  final String id;
  final String email;
  final String fullName;
  final String status;
  final String role;
  final String createdAt;
  final bool emailVerified;
  final bool totpEnabled;

  const ManagedUser({
    required this.id,
    required this.email,
    required this.fullName,
    required this.status,
    required this.role,
    required this.createdAt,
    required this.emailVerified,
    required this.totpEnabled,
  });
}

class Invitation {
  final String id;
  final String roleTarget;
  final String status;
  final String expiresAt;
  final String createdAt;
  final String? issuerUserId;
  final String? consumedAt;
  final String? consumedBy;

  const Invitation({
    required this.id,
    required this.roleTarget,
    required this.status,
    required this.expiresAt,
    required this.createdAt,
    this.issuerUserId,
    this.consumedAt,
    this.consumedBy,
  });
}

class Justification {
  final String id;
  final String attendanceRecordId;
  final String parentId;
  final String status;
  final String reason;
  final String? rejectionReason;
  final String createdAt;

  const Justification({
    required this.id,
    required this.attendanceRecordId,
    required this.parentId,
    required this.status,
    required this.reason,
    this.rejectionReason,
    required this.createdAt,
  });
}
