import 'package:ecole_platform/domain/entities/ai/rewards.dart';

abstract class RewardsRepository {
  Future<StudentRewards> getMyRewards();

  Future<StudentRewards> getStudentRewards(String studentId);

  Future<List<RewardsLeaderboardEntry>> getLeaderboard(
    String classId, {
    int limit = 10,
  });

  Future<StudentRewards> award({
    required String studentId,
    required String eventType,
    int stars = 0,
    int xp = 0,
    String? sourceType,
    String? sourceId,
  });
}
