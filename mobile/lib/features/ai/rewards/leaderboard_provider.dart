library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/ai/rewards.dart';

class StudentClassOption {
  final String classId;
  final String className;

  const StudentClassOption({required this.classId, required this.className});

  factory StudentClassOption.fromJson(Map<String, dynamic> json) =>
      StudentClassOption(
        classId: json['class_id'] as String? ?? '',
        className: json['class_name'] as String? ?? '',
      );
}

class LeaderboardData {
  final List<StudentClassOption> classes;
  final String selectedClassId;
  final List<RewardsLeaderboardEntry> entries;

  const LeaderboardData({
    required this.classes,
    required this.selectedClassId,
    required this.entries,
  });

  LeaderboardData copyWith({
    List<StudentClassOption>? classes,
    String? selectedClassId,
    List<RewardsLeaderboardEntry>? entries,
  }) =>
      LeaderboardData(
        classes: classes ?? this.classes,
        selectedClassId: selectedClassId ?? this.selectedClassId,
        entries: entries ?? this.entries,
      );
}

class LeaderboardNotifier extends AsyncNotifier<LeaderboardData> {
  @override
  Future<LeaderboardData> build() async {
    final api = ref.read(apiClientProvider);
    final classesResp = await api.list('/enrollments');
    final classes = classesResp.data.map(StudentClassOption.fromJson).toList();

    if (classes.isEmpty) {
      return const LeaderboardData(
        classes: <StudentClassOption>[],
        selectedClassId: '',
        entries: <RewardsLeaderboardEntry>[],
      );
    }

    final selected = classes.first.classId;
    final entries = await _fetchEntries(selected);
    return LeaderboardData(
      classes: classes,
      selectedClassId: selected,
      entries: entries,
    );
  }

  Future<List<RewardsLeaderboardEntry>> _fetchEntries(String classId) async {
    if (classId.isEmpty) return <RewardsLeaderboardEntry>[];
    final repo = ref.read(rewardsRepositoryProvider);
    return repo.getLeaderboard(classId, limit: 50);
  }

  Future<void> refresh() async {
    final current = state.value;
    if (current == null) {
      state = const AsyncLoading();
      state = await AsyncValue.guard(build);
      return;
    }
    state = await AsyncValue.guard(() async {
      final entries = await _fetchEntries(current.selectedClassId);
      return current.copyWith(entries: entries);
    });
  }

  Future<void> selectClass(String classId) async {
    final current = state.value;
    if (current == null || classId == current.selectedClassId) return;
    state = AsyncData(
      current.copyWith(
        selectedClassId: classId,
        entries: const <RewardsLeaderboardEntry>[],
      ),
    );
    state = await AsyncValue.guard(() async {
      final entries = await _fetchEntries(classId);
      return current.copyWith(selectedClassId: classId, entries: entries);
    });
  }
}

final leaderboardProvider =
    AsyncNotifierProvider<LeaderboardNotifier, LeaderboardData>(
  LeaderboardNotifier.new,
);
