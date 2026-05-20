/// Teacher-facing class progress providers.
///
/// Phase I (Web/Mobile parity) — I10.
///
/// Mirrors the web `ClassProgressPage` data shape:
///   * [teacherClassesListProvider] — teacher's assigned classes.
///   * [classProgressProvider]      — per-class progress summary
///     (GET /progress/class/{class_id}) with averages + per-student rows
///     + pre-built grade/attendance comparison chart data.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/lms/teacher.dart';

class StudentProgressRow {
  final String studentId;
  final String studentName;
  final double? gradeAverage;
  final double? attendanceRate;
  final double? contentCompletionRate;

  const StudentProgressRow({
    required this.studentId,
    required this.studentName,
    required this.gradeAverage,
    required this.attendanceRate,
    required this.contentCompletionRate,
  });

  factory StudentProgressRow.fromJson(Map<String, dynamic> json) {
    return StudentProgressRow(
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? '',
      gradeAverage: (json['grade_average'] as num?)?.toDouble(),
      attendanceRate: (json['attendance_rate'] as num?)?.toDouble(),
      contentCompletionRate:
          (json['content_completion_rate'] as num?)?.toDouble(),
    );
  }
}

class ClassAverages {
  final double? gradeAverage;
  final double? attendanceRate;
  final double? contentCompletionRate;

  const ClassAverages({
    required this.gradeAverage,
    required this.attendanceRate,
    required this.contentCompletionRate,
  });

  factory ClassAverages.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const ClassAverages(
        gradeAverage: null,
        attendanceRate: null,
        contentCompletionRate: null,
      );
    }
    return ClassAverages(
      gradeAverage: (json['grade_average'] as num?)?.toDouble(),
      attendanceRate: (json['attendance_rate'] as num?)?.toDouble(),
      contentCompletionRate:
          (json['content_completion_rate'] as num?)?.toDouble(),
    );
  }
}

class ChartSeries {
  final List<String> labels;
  final String datasetLabel;
  final List<double?> values;

  const ChartSeries({
    required this.labels,
    required this.datasetLabel,
    required this.values,
  });

  factory ChartSeries.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const ChartSeries(labels: [], datasetLabel: '', values: []);
    }
    final labels = (json['labels'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList(growable: false);
    final datasets =
        (json['datasets'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    if (datasets.isEmpty) {
      return ChartSeries(labels: labels, datasetLabel: '', values: const []);
    }
    final first = datasets.first;
    final values = (first['data'] as List<dynamic>? ?? [])
        .map((e) => (e as num?)?.toDouble())
        .toList(growable: false);
    return ChartSeries(
      labels: labels,
      datasetLabel: first['label'] as String? ?? '',
      values: values,
    );
  }
}

class ClassProgressData {
  final String classId;
  final String className;
  final int studentCount;
  final List<StudentProgressRow> students;
  final ClassAverages classAverages;
  final ChartSeries gradeComparison;
  final ChartSeries attendanceComparison;

  const ClassProgressData({
    required this.classId,
    required this.className,
    required this.studentCount,
    required this.students,
    required this.classAverages,
    required this.gradeComparison,
    required this.attendanceComparison,
  });

  factory ClassProgressData.fromJson(Map<String, dynamic> json) {
    final charts = json['charts'] as Map<String, dynamic>?;
    final students = (json['students'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map(StudentProgressRow.fromJson)
        .toList(growable: false);
    return ClassProgressData(
      classId: json['class_id'] as String? ?? '',
      className: json['class_name'] as String? ?? '',
      studentCount: (json['student_count'] as num?)?.toInt() ?? students.length,
      students: students,
      classAverages: ClassAverages.fromJson(
        json['class_averages'] as Map<String, dynamic>?,
      ),
      gradeComparison: ChartSeries.fromJson(
        charts?['grade_comparison'] as Map<String, dynamic>?,
      ),
      attendanceComparison: ChartSeries.fromJson(
        charts?['attendance_comparison'] as Map<String, dynamic>?,
      ),
    );
  }
}

/// Teacher's assigned classes (mirrors `/teacher/classes`).
final teacherClassesListProvider =
    FutureProvider.autoDispose<List<ClassInfo>>((ref) async {
  return ref.read(teacherRepositoryProvider).getClasses();
});

/// Per-class progress data (GET /progress/class/{classId}).
final classProgressProvider =
    FutureProvider.autoDispose.family<ClassProgressData, String>(
  (ref, classId) async {
    final api = ref.read(apiClientProvider);
    final resp = await api.get('/progress/class/$classId');
    return ClassProgressData.fromJson(resp.data);
  },
);
