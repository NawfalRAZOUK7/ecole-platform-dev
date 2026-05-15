/// Progress state management — Riverpod providers.
///
/// Reference: Phase 12C — Progress dashboard providers
/// Fetches from GET /progress/me (student), /progress/student/{id} (parent drill-down),
/// /progress/children (parent overview).

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';

// ── Data models ──

/// A single labeled series of numeric data points for chart rendering.
class ChartDataset {
  final String label;
  final List<double> data;
  const ChartDataset({required this.label, required this.data});
  factory ChartDataset.fromJson(Map<String, dynamic> json) => ChartDataset(
        label: json['label'] as String? ?? '',
        data: (json['data'] as List<dynamic>?)
                ?.map((e) => (e as num).toDouble())
                .toList() ??
            [],
      );
}

/// Generic chart payload containing axis labels and one or more [ChartDataset]s.
class ChartData {
  final List<String> labels;
  final List<ChartDataset> datasets;
  const ChartData({required this.labels, required this.datasets});
  factory ChartData.fromJson(Map<String, dynamic> json) => ChartData(
        labels: (json['labels'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        datasets: (json['datasets'] as List<dynamic>?)
                ?.map((e) => ChartDataset.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
      );
}

/// Aggregate attendance statistics: total sessions, present count, and rate.
class AttendanceSummary {
  final int total;
  final int present;
  final double attendanceRate;
  const AttendanceSummary({
    required this.total,
    required this.present,
    required this.attendanceRate,
  });
  factory AttendanceSummary.fromJson(Map<String, dynamic> json) =>
      AttendanceSummary(
        total: json['total'] as int? ?? 0,
        present: json['present'] as int? ?? 0,
        attendanceRate: (json['attendance_rate'] as num?)?.toDouble() ?? 0,
      );
}

/// Aggregate content completion statistics: total items, completed count, and rate.
class ContentSummary {
  final int total;
  final int completed;
  final double completionRate;
  const ContentSummary({
    required this.total,
    required this.completed,
    required this.completionRate,
  });
  factory ContentSummary.fromJson(Map<String, dynamic> json) => ContentSummary(
        total: json['total'] as int? ?? 0,
        completed: json['completed'] as int? ?? 0,
        completionRate: (json['completion_rate'] as num?)?.toDouble() ?? 0,
      );
}

/// Complete progress data for a single student, parsed from the API response.
///
/// Contains chart data for grade trends, content completion, activity scores,
/// and attendance, along with their respective summary statistics.
class StudentProgress {
  final String studentId;
  final String studentName;
  final ChartData gradeTrends;
  final ChartData contentCompletion;
  final ContentSummary contentSummary;
  final ChartData activityScores;
  final ChartData attendanceOverview;
  final AttendanceSummary attendanceSummary;

  const StudentProgress({
    required this.studentId,
    required this.studentName,
    required this.gradeTrends,
    required this.contentCompletion,
    required this.contentSummary,
    required this.activityScores,
    required this.attendanceOverview,
    required this.attendanceSummary,
  });

  factory StudentProgress.fromJson(Map<String, dynamic> json) {
    final contentMap =
        json['content_completion'] as Map<String, dynamic>? ?? {};
    final attendanceMap = json['attendance'] as Map<String, dynamic>? ?? {};
    final overviewMap =
        attendanceMap['overview'] as Map<String, dynamic>? ?? {};

    return StudentProgress(
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? '',
      gradeTrends: ChartData.fromJson(
        json['grade_trends'] as Map<String, dynamic>? ?? {},
      ),
      contentCompletion: ChartData.fromJson(contentMap),
      contentSummary: ContentSummary.fromJson(
        contentMap['summary'] as Map<String, dynamic>? ?? {},
      ),
      activityScores: ChartData.fromJson(
        json['activity_scores'] as Map<String, dynamic>? ?? {},
      ),
      attendanceOverview: ChartData.fromJson(overviewMap),
      attendanceSummary: AttendanceSummary.fromJson(
        overviewMap['summary'] as Map<String, dynamic>? ?? {},
      ),
    );
  }
}

/// Summary metrics for a single child, used in the parent overview screen.
class ChildProgressSummary {
  final String studentId;
  final String studentName;
  final double gradeAverage;
  final double attendanceRate;
  final double contentCompletionRate;

  const ChildProgressSummary({
    required this.studentId,
    required this.studentName,
    required this.gradeAverage,
    required this.attendanceRate,
    required this.contentCompletionRate,
  });

  factory ChildProgressSummary.fromJson(Map<String, dynamic> json) =>
      ChildProgressSummary(
        studentId: json['student_id'] as String? ?? '',
        studentName: json['student_name'] as String? ?? '',
        gradeAverage: (json['grade_average'] as num?)?.toDouble() ?? 0,
        attendanceRate: (json['attendance_rate'] as num?)?.toDouble() ?? 0,
        contentCompletionRate:
            (json['content_completion_rate'] as num?)?.toDouble() ?? 0,
      );
}

// ── States ──

/// Immutable state for the student progress screen (loading, data, or error).
class ProgressState {
  final StudentProgress? progress;
  final bool isLoading;
  final String? error;
  const ProgressState({this.progress, this.isLoading = false, this.error});
}

/// Immutable state for the parent children overview (loading, list, or error).
class ChildrenProgressState {
  final List<ChildProgressSummary> children;
  final bool isLoading;
  final String? error;
  const ChildrenProgressState({
    this.children = const [],
    this.isLoading = false,
    this.error,
  });
}

// ── Notifiers ──

/// Notifier that fetches and holds a single student's progress data.
///
/// API: `GET /progress/me` (when [studentId] is null) or
/// `GET /progress/student/{studentId}` (parent drill-down).
class ProgressNotifier extends StateNotifier<ProgressState> {
  final Ref _ref;
  final String? studentId;

  ProgressNotifier(this._ref, {this.studentId})
      : super(const ProgressState(isLoading: true)) {
    load();
  }

  /// Fetches progress data from the API and updates state.
  Future<void> load() async {
    state = const ProgressState(isLoading: true);
    try {
      final api = _ref.read(apiClientProvider);
      final endpoint =
          studentId != null ? '/progress/student/$studentId' : '/progress/me';
      final resp = await api.get(endpoint);
      final data = resp.data;
      state = ProgressState(progress: StudentProgress.fromJson(data));
    } catch (e) {
      state = ProgressState(error: e.toString());
    }
  }
}

/// Notifier that fetches the parent's children progress overview.
///
/// API: `GET /progress/children`.
class ChildrenProgressNotifier extends StateNotifier<ChildrenProgressState> {
  final Ref _ref;

  ChildrenProgressNotifier(this._ref)
      : super(const ChildrenProgressState(isLoading: true)) {
    load();
  }

  /// Fetches the children summary list from the API and updates state.
  Future<void> load() async {
    state = const ChildrenProgressState(isLoading: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.get('/progress/children');
      final data = resp.data;
      final children = (data['children'] as List<dynamic>)
          .map((j) => ChildProgressSummary.fromJson(j as Map<String, dynamic>))
          .toList();
      state = ChildrenProgressState(children: children);
    } catch (e) {
      state = ChildrenProgressState(error: e.toString());
    }
  }
}

// ── Providers ──

/// Student's own progress (or specific student by ID)
final progressProvider =
    StateNotifierProvider.family<ProgressNotifier, ProgressState, String?>(
  (ref, studentId) => ProgressNotifier(ref, studentId: studentId),
);

/// Parent children overview
final childrenProgressProvider =
    StateNotifierProvider<ChildrenProgressNotifier, ChildrenProgressState>(
  (ref) => ChildrenProgressNotifier(ref),
);
