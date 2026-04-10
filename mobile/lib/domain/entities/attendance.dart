class AttendanceEntry {
  final String id;
  final String studentId;
  final String? studentName;
  final String? classId;
  final String date;
  final String status;
  final String? slot;
  final String? absenceReason;
  final String? justificationStatus;

  const AttendanceEntry({
    required this.id,
    required this.studentId,
    required this.date,
    required this.status,
    this.studentName,
    this.classId,
    this.slot,
    this.absenceReason,
    this.justificationStatus,
  });

  factory AttendanceEntry.fromJson(Map<String, dynamic> json) {
    return AttendanceEntry(
      id: json['id']?.toString() ??
          json['attendance_record_id']?.toString() ??
          '${json['student_id']}-${json['date']}',
      studentId: json['student_id']?.toString() ?? '',
      studentName: json['student_name']?.toString() ?? json['full_name']?.toString(),
      classId: json['class_id']?.toString(),
      date: json['date']?.toString() ??
          json['session_date']?.toString() ??
          DateTime.now().toIso8601String(),
      status: json['status']?.toString() ?? 'present',
      slot: json['slot']?.toString(),
      absenceReason: json['absence_reason']?.toString(),
      justificationStatus: json['justification_status']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'student_id': studentId,
      if (studentName != null) 'student_name': studentName,
      if (classId != null) 'class_id': classId,
      'date': date,
      'status': status,
      if (slot != null) 'slot': slot,
      if (absenceReason != null) 'absence_reason': absenceReason,
      if (justificationStatus != null)
        'justification_status': justificationStatus,
    };
  }

  @override
  bool operator ==(Object other) {
    return other is AttendanceEntry &&
        other.id == id &&
        other.studentId == studentId &&
        other.studentName == studentName &&
        other.classId == classId &&
        other.date == date &&
        other.status == status &&
        other.slot == slot &&
        other.absenceReason == absenceReason &&
        other.justificationStatus == justificationStatus;
  }

  @override
  int get hashCode => Object.hash(
        id,
        studentId,
        studentName,
        classId,
        date,
        status,
        slot,
        absenceReason,
        justificationStatus,
      );
}

class AttendanceBulkRecord {
  final String studentId;
  final String status;
  final String? absenceReason;

  const AttendanceBulkRecord({
    required this.studentId,
    required this.status,
    this.absenceReason,
  });

  Map<String, dynamic> toJson() {
    return {
      'student_id': studentId,
      'status': status,
      if (absenceReason != null) 'absence_reason': absenceReason,
    };
  }
}

class AttendanceJustification {
  final String id;
  final String attendanceRecordId;
  final String reason;
  final String status;
  final String? reviewedAt;
  final String? reviewComment;

  const AttendanceJustification({
    required this.id,
    required this.attendanceRecordId,
    required this.reason,
    required this.status,
    this.reviewedAt,
    this.reviewComment,
  });

  factory AttendanceJustification.fromJson(Map<String, dynamic> json) {
    return AttendanceJustification(
      id: json['id']?.toString() ?? '',
      attendanceRecordId: json['attendance_record_id']?.toString() ?? '',
      reason: json['reason']?.toString() ?? '',
      status: json['status']?.toString() ?? 'pending',
      reviewedAt: json['reviewed_at']?.toString(),
      reviewComment: json['review_comment']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'attendance_record_id': attendanceRecordId,
      'reason': reason,
      'status': status,
      if (reviewedAt != null) 'reviewed_at': reviewedAt,
      if (reviewComment != null) 'review_comment': reviewComment,
    };
  }
}

class AttendanceTrendPoint {
  final String label;
  final double attendanceRate;
  final int presentCount;
  final int absentCount;
  final int lateCount;

  const AttendanceTrendPoint({
    required this.label,
    required this.attendanceRate,
    required this.presentCount,
    required this.absentCount,
    required this.lateCount,
  });

  factory AttendanceTrendPoint.fromJson(Map<String, dynamic> json) {
    return AttendanceTrendPoint(
      label: json['label']?.toString() ??
          json['bucket']?.toString() ??
          json['date']?.toString() ??
          '',
      attendanceRate: (json['attendance_rate'] as num?)?.toDouble() ??
          (json['rate'] as num?)?.toDouble() ??
          0,
      presentCount: (json['present_count'] as num?)?.toInt() ??
          (json['present'] as num?)?.toInt() ??
          0,
      absentCount: (json['absent_count'] as num?)?.toInt() ??
          (json['absent'] as num?)?.toInt() ??
          0,
      lateCount:
          (json['late_count'] as num?)?.toInt() ?? (json['late'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'label': label,
      'attendance_rate': attendanceRate,
      'present_count': presentCount,
      'absent_count': absentCount,
      'late_count': lateCount,
    };
  }
}

class AttendanceAlertItem {
  final String id;
  final String? classId;
  final String? studentId;
  final String title;
  final String message;
  final double attendanceRate;
  final double threshold;
  final bool triggered;

  const AttendanceAlertItem({
    required this.id,
    required this.title,
    required this.message,
    required this.attendanceRate,
    required this.threshold,
    required this.triggered,
    this.classId,
    this.studentId,
  });

  factory AttendanceAlertItem.fromJson(Map<String, dynamic> json) {
    final studentName = json['student_name']?.toString();
    return AttendanceAlertItem(
      id: json['id']?.toString() ??
          '${json['class_id']}-${json['student_id'] ?? json['title'] ?? 'alert'}',
      classId: json['class_id']?.toString(),
      studentId: json['student_id']?.toString(),
      title: json['title']?.toString() ??
          (studentName == null ? 'Attendance alert' : 'Alert: $studentName'),
      message: json['message']?.toString() ??
          json['reason']?.toString() ??
          'Attendance threshold reached',
      attendanceRate: (json['attendance_rate'] as num?)?.toDouble() ?? 0,
      threshold: (json['threshold'] as num?)?.toDouble() ?? 75,
      triggered: json['triggered'] as bool? ?? true,
    );
  }
}

class AttendanceClassStats {
  final String classId;
  final double attendanceRate;
  final int totalSessions;
  final int presentCount;
  final int absentCount;
  final int lateCount;
  final int excusedCount;

  const AttendanceClassStats({
    required this.classId,
    required this.attendanceRate,
    required this.totalSessions,
    required this.presentCount,
    required this.absentCount,
    required this.lateCount,
    required this.excusedCount,
  });

  factory AttendanceClassStats.fromJson(Map<String, dynamic> json) {
    return AttendanceClassStats(
      classId: json['class_id']?.toString() ?? '',
      attendanceRate: (json['attendance_rate'] as num?)?.toDouble() ?? 0,
      totalSessions: (json['total_sessions'] as num?)?.toInt() ??
          (json['session_count'] as num?)?.toInt() ??
          0,
      presentCount:
          (json['present_count'] as num?)?.toInt() ?? (json['present'] as num?)?.toInt() ?? 0,
      absentCount:
          (json['absent_count'] as num?)?.toInt() ?? (json['absent'] as num?)?.toInt() ?? 0,
      lateCount:
          (json['late_count'] as num?)?.toInt() ?? (json['late'] as num?)?.toInt() ?? 0,
      excusedCount: (json['excused_count'] as num?)?.toInt() ??
          (json['excused'] as num?)?.toInt() ??
          0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'class_id': classId,
      'attendance_rate': attendanceRate,
      'total_sessions': totalSessions,
      'present_count': presentCount,
      'absent_count': absentCount,
      'late_count': lateCount,
      'excused_count': excusedCount,
    };
  }
}

class AttendanceExportResult {
  final String downloadUrl;
  final String fileName;

  const AttendanceExportResult({
    required this.downloadUrl,
    required this.fileName,
  });
}

class AttendanceThresholdResult {
  final String classId;
  final String studentId;
  final double attendanceRate;
  final double threshold;
  final bool triggered;

  const AttendanceThresholdResult({
    required this.classId,
    required this.studentId,
    required this.attendanceRate,
    required this.threshold,
    required this.triggered,
  });

  factory AttendanceThresholdResult.fromJson(Map<String, dynamic> json) {
    return AttendanceThresholdResult(
      classId: json['class_id']?.toString() ?? '',
      studentId: json['student_id']?.toString() ?? '',
      attendanceRate: (json['attendance_rate'] as num?)?.toDouble() ?? 0,
      threshold: (json['threshold'] as num?)?.toDouble() ?? 75,
      triggered: json['triggered'] as bool? ?? false,
    );
  }
}

class AttendanceAnalyticsSnapshot {
  final AttendanceClassStats stats;
  final List<AttendanceTrendPoint> trends;
  final List<AttendanceAlertItem> alerts;

  const AttendanceAnalyticsSnapshot({
    required this.stats,
    required this.trends,
    required this.alerts,
  });
}
