import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/domain/repositories/rewards_repository.dart';

class RewardsRepositoryImpl implements RewardsRepository {
  final ApiClient _api;

  RewardsRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<StudentRewards> getMyRewards() async {
    final resp = await _api.get('/rewards/me');
    return StudentRewards.fromJson(resp.data);
  }

  @override
  Future<StudentRewards> getStudentRewards(String studentId) async {
    final resp = await _api.get('/rewards/student/$studentId');
    return StudentRewards.fromJson(resp.data);
  }

  @override
  Future<List<RewardsLeaderboardEntry>> getLeaderboard(
    String classId, {
    int limit = 10,
  }) async {
    final resp = await _api.list(
      '/rewards/leaderboard/$classId',
      params: <String, dynamic>{'limit': limit},
    );
    return resp.data.map(RewardsLeaderboardEntry.fromJson).toList();
  }

  @override
  Future<StudentRewards> award({
    required String studentId,
    required String eventType,
    int stars = 0,
    int xp = 0,
    String? sourceType,
    String? sourceId,
  }) async {
    final resp = await _api.post(
      '/rewards/award',
      body: <String, dynamic>{
        'student_id': studentId,
        'event_type': eventType,
        'stars': stars,
        'xp': xp,
        if (sourceType != null) 'source_type': sourceType,
        if (sourceId != null) 'source_id': sourceId,
      },
    );
    return StudentRewards.fromJson(resp.data);
  }
}
