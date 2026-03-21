/// Admin repository interface — domain layer contract.
///
/// Reference: Phase 5B (from 4A)
import '../entities/admin.dart';
import 'feed_repository.dart';

abstract class AdminRepository {
  Future<DashboardStats> getDashboard();

  Future<PaginatedList<ManagedUser>> getUsers({
    String? cursor,
    String? search,
    String? role,
    String? status,
  });

  Future<void> suspendUser(String userId);
  Future<void> activateUser(String userId);
  Future<void> changeUserRole(String userId, String newRole);

  Future<PaginatedList<Invitation>> getInvitations({
    String? cursor,
    String? status,
  });

  Future<Invitation> createInvitation(String roleTarget, int expiresInHours);
  Future<void> revokeInvitation(String inviteId);

  Future<PaginatedList<Justification>> getJustifications({
    String? cursor,
    String? status,
  });

  Future<void> reviewJustification(
    String justificationId,
    String decision, {
    String? rejectionReason,
  });
}
