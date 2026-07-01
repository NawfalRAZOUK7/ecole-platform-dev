class MicroSchool {
  final String id;
  final String name;
  final String description;
  final String location;
  final String city;
  final int capacity;
  final int studentCount;
  final String status;

  const MicroSchool({
    required this.id,
    required this.name,
    required this.description,
    required this.location,
    required this.city,
    required this.capacity,
    required this.studentCount,
    required this.status,
  });

  double get capacityRatio => capacity == 0 ? 0 : studentCount / capacity;

  factory MicroSchool.fromJson(Map<String, dynamic> json) {
    return MicroSchool(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      location: json['location']?.toString() ?? '',
      city: json['city']?.toString() ?? '',
      capacity: (json['capacity'] as num?)?.toInt() ?? 0,
      studentCount: (json['student_count'] as num?)?.toInt() ?? 0,
      status: json['status']?.toString() ?? 'active',
    );
  }
}

class MicroEnrollment {
  final String id;
  final String microSchoolId;
  final String childName;
  final String status;

  const MicroEnrollment({
    required this.id,
    required this.microSchoolId,
    required this.childName,
    required this.status,
  });

  factory MicroEnrollment.fromJson(Map<String, dynamic> json) {
    return MicroEnrollment(
      id: json['id']?.toString() ?? '',
      microSchoolId: json['micro_school_id']?.toString() ?? '',
      childName: json['child_name']?.toString() ?? '',
      status: json['status']?.toString() ?? 'active',
    );
  }
}

class MicroPayment {
  final String id;
  final String microSchoolId;
  final double amount;
  final String currency;
  final String status;

  const MicroPayment({
    required this.id,
    required this.microSchoolId,
    required this.amount,
    required this.currency,
    required this.status,
  });

  factory MicroPayment.fromJson(Map<String, dynamic> json) {
    return MicroPayment(
      id: json['id']?.toString() ?? '',
      microSchoolId: json['micro_school_id']?.toString() ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency']?.toString() ?? 'MAD',
      status: json['status']?.toString() ?? 'pending',
    );
  }
}

class MicroResource {
  final String id;
  final String microSchoolId;
  final String title;
  final String description;
  final String resourceType;
  final String language;

  const MicroResource({
    required this.id,
    required this.microSchoolId,
    required this.title,
    required this.description,
    required this.resourceType,
    required this.language,
  });

  factory MicroResource.fromJson(Map<String, dynamic> json) {
    return MicroResource(
      id: json['id']?.toString() ?? '',
      microSchoolId: json['micro_school_id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      resourceType: json['resource_type']?.toString() ?? '',
      language: json['language']?.toString() ?? 'fr',
    );
  }
}

class MicroMetricPoint {
  final String label;
  final double value;

  const MicroMetricPoint({
    required this.label,
    required this.value,
  });

  factory MicroMetricPoint.fromJson(Map<String, dynamic> json) {
    return MicroMetricPoint(
      label: json['label']?.toString() ?? '',
      value: (json['value'] as num?)?.toDouble() ?? 0,
    );
  }
}

/// A single educator observation for a micro-enrollment — the raw material
/// for the parent/educator activity feed (note + optional photo + milestone).
class MicroProgressLogEntry {
  final String id;
  final String microEnrollmentId;
  final String date;
  final String note;
  final String? photoUrl;
  final String? milestoneTag;

  const MicroProgressLogEntry({
    required this.id,
    required this.microEnrollmentId,
    required this.date,
    required this.note,
    this.photoUrl,
    this.milestoneTag,
  });

  factory MicroProgressLogEntry.fromJson(Map<String, dynamic> json) {
    return MicroProgressLogEntry(
      id: json['id']?.toString() ?? '',
      microEnrollmentId: json['micro_enrollment_id']?.toString() ?? '',
      date: json['date']?.toString() ?? '',
      note: json['note']?.toString() ?? '',
      photoUrl: json['photo_url'] as String?,
      milestoneTag: json['milestone_tag'] as String?,
    );
  }
}

class MicroProgressOverview {
  final double averageProgress;
  final int activeStudents;
  final double completionRate;
  final List<MicroMetricPoint> series;
  final List<MicroProgressLogEntry> logs;

  const MicroProgressOverview({
    required this.averageProgress,
    required this.activeStudents,
    required this.completionRate,
    required this.series,
    this.logs = const [],
  });

  factory MicroProgressOverview.fromJson(Map<String, dynamic> json) {
    final seriesJson = (json['series'] as List<dynamic>? ?? const []);
    final logsJson = (json['logs'] as List<dynamic>? ?? const []);
    return MicroProgressOverview(
      averageProgress: (json['average_progress'] as num?)?.toDouble() ?? 0,
      activeStudents: (json['active_students'] as num?)?.toInt() ?? 0,
      completionRate: (json['completion_rate'] as num?)?.toDouble() ?? 0,
      series: seriesJson
          .map(
            (item) => MicroMetricPoint.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      logs: logsJson
          .map(
            (item) =>
                MicroProgressLogEntry.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }
}

class MicroStudentProgress {
  final String studentId;
  final String studentName;
  final int milestonesCompleted;
  final double progressRate;
  final List<MicroMetricPoint> series;

  const MicroStudentProgress({
    required this.studentId,
    required this.studentName,
    required this.milestonesCompleted,
    required this.progressRate,
    required this.series,
  });

  factory MicroStudentProgress.fromJson(Map<String, dynamic> json) {
    final seriesJson = (json['series'] as List<dynamic>? ?? const []);
    return MicroStudentProgress(
      studentId: json['student_id']?.toString() ?? '',
      studentName: json['student_name']?.toString() ?? '',
      milestonesCompleted: (json['milestones_completed'] as num?)?.toInt() ?? 0,
      progressRate: (json['progress_rate'] as num?)?.toDouble() ?? 0,
      series: seriesJson
          .map(
            (item) => MicroMetricPoint.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }
}

class MicroSchoolDetailBundle {
  final MicroSchool school;
  final List<MicroEnrollment> enrollments;
  final List<MicroResource> resources;
  final List<MicroPayment> payments;
  final MicroProgressOverview progress;

  const MicroSchoolDetailBundle({
    required this.school,
    required this.enrollments,
    required this.resources,
    required this.payments,
    required this.progress,
  });
}
