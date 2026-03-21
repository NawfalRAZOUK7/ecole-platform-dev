/// Admin repository implementation — data layer.
///
/// Reference: Phase 5B (from 4A)

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/domain/entities/admin.dart';
import 'package:ecole_platform/domain/repositories/admin_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

class AdminRepositoryImpl implements AdminRepository {
  final ApiClient _api;

  AdminRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<DashboardStats> getDashboard() async {
    final resp = await _api.get('/admin/dashboard');
    return dashboardStatsFromJson(resp.data);
  }

  @override
  Future<PaginatedList<ManagedUser>> getUsers({
    String? cursor,
    String? search,
    String? role,
    String? status,
  }) async {
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (search != null && search.isNotEmpty) params['search'] = search;
    if (role != null) params['role'] = role;
    if (status != null) params['status'] = status;

    final resp = await _api.list('/admin/users', params: params);
    return PaginatedList(
      items: resp.data.map(managedUserFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<void> suspendUser(String userId) async {
    await _api.put('/admin/users/$userId/suspend');
  }

  @override
  Future<void> activateUser(String userId) async {
    await _api.put('/admin/users/$userId/activate');
  }

  @override
  Future<void> changeUserRole(String userId, String newRole) async {
    await _api.put('/admin/users/$userId/role', body: {'role': newRole});
  }

  @override
  Future<PaginatedList<Invitation>> getInvitations({
    String? cursor,
    String? status,
  }) async {
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (status != null) params['status'] = status;

    final resp = await _api.list('/admin/invitations', params: params);
    return PaginatedList(
      items: resp.data.map(invitationFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<Invitation> createInvitation(
      String roleTarget, int expiresInHours) async {
    final resp = await _api.post('/invites/create', body: {
      'role_target': roleTarget,
      'expires_in_hours': expiresInHours,
    });
    return invitationFromJson(resp.data);
  }

  @override
  Future<void> revokeInvitation(String inviteId) async {
    await _api.post('/invites/revoke', body: {'invite_id': inviteId});
  }

  @override
  Future<PaginatedList<Justification>> getJustifications({
    String? cursor,
    String? status,
  }) async {
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (status != null) params['status'] = status;

    final resp =
        await _api.list('/admin/justifications', params: params);
    return PaginatedList(
      items: resp.data.map(justificationFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<void> reviewJustification(
    String justificationId,
    String decision, {
    String? rejectionReason,
  }) async {
    final body = <String, dynamic>{'decision': decision};
    if (rejectionReason != null) body['rejection_reason'] = rejectionReason;
    await _api.post(
      '/attendance/justifications/$justificationId/review',
      body: body,
    );
  }
}
