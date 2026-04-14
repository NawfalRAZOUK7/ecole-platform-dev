class StudentRewards {
  final String id;
  final String studentId;
  final int stars;
  final int xp;
  final int level;
  final int streakDays;
  final List<String> badges;
  final DateTime? lastActivityAt;
  final double? _levelProgressPercent;

  const StudentRewards({
    required this.id,
    required this.studentId,
    required this.stars,
    required this.xp,
    required this.level,
    required this.streakDays,
    required this.badges,
    this.lastActivityAt,
    double? levelProgressPercent,
  }) : _levelProgressPercent = levelProgressPercent;

  factory StudentRewards.fromJson(Map<String, dynamic> json) => StudentRewards(
        id: json['id'] as String? ?? '',
        studentId: json['student_id'] as String? ?? '',
        stars: (json['stars'] as num?)?.toInt() ?? 0,
        xp: (json['xp'] as num?)?.toInt() ?? 0,
        level: (json['level'] as num?)?.toInt() ?? 1,
        streakDays: (json['streak_days'] as num?)?.toInt() ?? 0,
        badges: List<String>.from(json['badges'] as List? ?? const []),
        lastActivityAt: json['last_activity_at'] is String
            ? DateTime.tryParse(json['last_activity_at'] as String)
            : null,
        levelProgressPercent: (json['level_progress'] as num?)?.toDouble(),
      );

  static const empty = StudentRewards(
    id: '',
    studentId: '',
    stars: 0,
    xp: 0,
    level: 1,
    streakDays: 0,
    badges: <String>[],
  );

  static int xpThresholdForLevel(int level) {
    if (level <= 1) {
      return 0;
    }
    return 50 * (level - 1) * level;
  }

  int get currentLevelThreshold => xpThresholdForLevel(level);
  int get nextLevelThreshold => xpThresholdForLevel(level + 1);
  int get xpIntoCurrentLevel => xp - currentLevelThreshold;
  int get xpRangeForCurrentLevel => nextLevelThreshold - currentLevelThreshold;
  int get xpToNextLevel => nextLevelThreshold - xp;

  double get levelProgressPercent {
    if (_levelProgressPercent != null) {
      return _levelProgressPercent.clamp(0, 100).toDouble();
    }
    if (xpRangeForCurrentLevel <= 0) {
      return 100;
    }
    final progress = (xpIntoCurrentLevel / xpRangeForCurrentLevel) * 100;
    return progress.clamp(0, 100).toDouble();
  }

  double get levelProgress => levelProgressPercent / 100;

  StudentRewards copyWith({
    int? stars,
    int? xp,
    int? level,
    int? streakDays,
    List<String>? badges,
    DateTime? lastActivityAt,
    bool clearLastActivityAt = false,
    double? levelProgressPercent,
  }) {
    return StudentRewards(
      id: id,
      studentId: studentId,
      stars: stars ?? this.stars,
      xp: xp ?? this.xp,
      level: level ?? this.level,
      streakDays: streakDays ?? this.streakDays,
      badges: badges ?? this.badges,
      lastActivityAt: clearLastActivityAt
          ? null
          : (lastActivityAt ?? this.lastActivityAt),
      levelProgressPercent:
          levelProgressPercent ?? _levelProgressPercent ?? this.levelProgressPercent,
    );
  }
}

class RewardsLeaderboardEntry {
  final String studentId;
  final String studentName;
  final int stars;
  final int level;
  final int rank;

  const RewardsLeaderboardEntry({
    required this.studentId,
    required this.studentName,
    required this.stars,
    required this.level,
    required this.rank,
  });

  factory RewardsLeaderboardEntry.fromJson(Map<String, dynamic> json) =>
      RewardsLeaderboardEntry(
        studentId: json['student_id'] as String? ?? '',
        studentName: json['student_name'] as String? ?? '',
        stars: (json['stars'] as num?)?.toInt() ?? 0,
        level: (json['level'] as num?)?.toInt() ?? 1,
        rank: (json['rank'] as num?)?.toInt() ?? 0,
      );
}
