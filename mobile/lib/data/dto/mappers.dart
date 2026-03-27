/// DTO mappers — convert API JSON to domain entities.
///
/// Reference: DEC-E2-001 — Data layer handles API DTOs,
/// presentation layer only sees domain entities.

import 'package:ecole_platform/domain/entities/user.dart';
import 'package:ecole_platform/domain/entities/feed_item.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';
import 'package:ecole_platform/domain/entities/notification_settings.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';
import 'package:ecole_platform/domain/entities/result.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/domain/entities/admin.dart';
import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/domain/entities/calendar_event.dart';

// ── User ──

User userFromJson(Map<String, dynamic> json) {
  return User(
    id: json['id'] as String,
    email: json['email'] as String,
    fullName: json['full_name'] as String,
    role: json['role'] as String,
    schoolId: json['school_id'] as String,
    permissions: (json['permissions'] as List<dynamic>).cast<String>(),
    memberships: (json['memberships'] as List<dynamic>)
        .map((m) => membershipFromJson(m as Map<String, dynamic>))
        .toList(),
  );
}

Membership membershipFromJson(Map<String, dynamic> json) {
  return Membership(
    schoolId: json['school_id'] as String,
    role: json['role'] as String,
    status: json['status'] as String,
  );
}

// ── Feed ──

FeedItem feedItemFromJson(Map<String, dynamic> json) {
  return FeedItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String,
    parentId: json['parent_id'] as String,
    studentId: json['student_id'] as String?,
    sourceType: json['source_type'] as String,
    sourceRef: json['source_ref'] as String?,
    title: json['title'] as String,
    body: json['body'] as String?,
    createdAt: json['created_at'] as String,
  );
}

// ── Notification ──

NotificationItem notificationFromJson(Map<String, dynamic> json) {
  return NotificationItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String,
    userId: (json['user_id'] ?? json['parent_id']) as String,
    eventRef: json['event_ref'] as String?,
    title: json['title'] as String,
    body: json['body'] as String?,
    category: json['category'] as String? ?? 'system',
    priority: json['priority'] as String? ?? 'normal',
    actionUrl: json['action_url'] as String?,
    actionPayload: json['action_payload'] as Map<String, dynamic>?,
    isRead: json['is_read'] as bool? ?? false,
    readAt: json['read_at'] as String?,
    createdAt: json['created_at'] as String,
    channels: (json['channels'] as List<dynamic>? ?? const [])
        .map((item) => item.toString())
        .toList(),
  );
}

NotificationPreferenceItem notificationPreferenceFromJson(
    Map<String, dynamic> json) {
  return NotificationPreferenceItem(
    channel: json['channel'] as String,
    category: json['category'] as String,
    enabled: json['enabled'] as bool? ?? true,
    digestFrequency: json['digest_frequency'] as String? ?? 'off',
  );
}

RegisteredDevice registeredDeviceFromJson(Map<String, dynamic> json) {
  return RegisteredDevice(
    id: json['id'] as String,
    platform: json['platform'] as String,
    deviceName: json['device_name'] as String?,
    tokenPreview: json['token_preview'] as String? ?? '',
    lastActiveAt: json['last_active_at'] as String? ?? '',
  );
}

// ── Calendar ──

CalendarClassOption calendarClassOptionFromJson(Map<String, dynamic> json) {
  final code = json['code']?.toString();
  final name = json['name']?.toString();
  return CalendarClassOption(
    id: json['id'] as String,
    label: [code, name]
        .whereType<String>()
        .where((item) => item.isNotEmpty)
        .join(' · '),
  );
}

ReminderPreference reminderPreferenceFromJson(Map<String, dynamic> json) {
  return ReminderPreference(
    eventType: json['event_type'] as String? ?? 'custom',
    enabled: json['enabled'] as bool? ?? true,
  );
}

CalendarEvent calendarEventFromJson(Map<String, dynamic> json) {
  return CalendarEvent(
    id: json['id'] as String,
    instanceId: json['instance_id'] as String? ?? json['id'] as String,
    source: json['source'] as String? ?? 'event',
    titleFr: json['title_fr'] as String? ?? '',
    titleAr: json['title_ar'] as String?,
    titleEn: json['title_en'] as String?,
    description: json['description'] as String?,
    type: json['type'] as String? ?? 'custom',
    visibility: json['visibility'] as String? ?? 'school',
    startAt: json['start_at'] as String,
    endAt: json['end_at'] as String,
    location: json['location'] as String?,
    latitude: (json['latitude'] as num?)?.toDouble(),
    longitude: (json['longitude'] as num?)?.toDouble(),
    classId: json['class_id'] as String?,
    roleCodes: (json['role_codes'] as List<dynamic>? ?? const [])
        .map((item) => item.toString())
        .toList(),
    capacity: json['capacity'] as int?,
    rsvpDeadline: json['rsvp_deadline'] as String?,
    attendeeCount: json['attendee_count'] as int? ?? 0,
    maybeCount: json['maybe_count'] as int? ?? 0,
    declinedCount: json['declined_count'] as int? ?? 0,
    myRsvp: json['my_rsvp'] as String?,
    isAllDay: json['is_all_day'] as bool? ?? false,
    isRecurring: json['is_recurring'] as bool? ?? false,
    recurrenceRule: json['recurrence_rule'] as Map<String, dynamic>?,
    canEdit: json['can_edit'] as bool? ?? false,
    canDelete: json['can_delete'] as bool? ?? false,
    canRsvp: json['can_rsvp'] as bool? ?? false,
    isHoliday: json['is_holiday'] as bool? ?? false,
    rsvps: (json['rsvps'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(eventRsvpRecordFromJson)
        .toList(),
  );
}

EventRsvpRecord eventRsvpRecordFromJson(Map<String, dynamic> json) {
  return EventRsvpRecord(
    userId: json['user_id'] as String,
    fullName: json['full_name'] as String? ?? '',
    role: json['role'] as String? ?? '',
    status: json['status'] as String? ?? 'maybe',
    respondedAt: json['responded_at'] as String? ?? '',
  );
}

// ── Reporting ──

ReportOptionItem reportOptionFromJson(
  Map<String, dynamic> json, {
  String primaryKey = 'label',
  List<String> secondaryKeys = const ['name', 'code', 'email'],
}) {
  String? secondary;
  for (final key in secondaryKeys) {
    final value = json[key]?.toString();
    if (value != null &&
        value.isNotEmpty &&
        value != json[primaryKey]?.toString()) {
      secondary = value;
      break;
    }
  }

  return ReportOptionItem(
    id: json['id'] as String,
    label: json[primaryKey]?.toString() ??
        json['full_name']?.toString() ??
        json['name']?.toString() ??
        json['code']?.toString() ??
        json['email']?.toString() ??
        json['id'].toString(),
    secondary: secondary,
  );
}

ReportJob reportJobFromJson(Map<String, dynamic> json) {
  return ReportJob(
    id: json['id'] as String,
    type: json['type'] as String,
    status: json['status'] as String,
    parameters: Map<String, dynamic>.from(
      json['parameters'] as Map<String, dynamic>? ?? const {},
    ),
    createdAt: json['created_at'] as String,
    completedAt: json['completed_at'] as String?,
    expiresAt: json['expires_at'] as String?,
    errorMessage: json['error_message'] as String?,
    downloadUrl: json['download_url'] as String?,
    cacheHit: json['cache_hit'] as bool? ?? false,
    localFilePath: json['local_file_path'] as String?,
  );
}

AnalyticsMetric analyticsMetricFromJson(Map<String, dynamic> json) {
  return AnalyticsMetric(
    current: (json['current'] as num?)?.toDouble() ?? 0,
    previous: (json['previous'] as num?)?.toDouble(),
    changePercent: (json['change_percent'] as num?)?.toDouble(),
    trend: json['trend'] as String? ?? 'flat',
  );
}

AnalyticsSeriesPoint analyticsSeriesPointFromJson(Map<String, dynamic> json) {
  return AnalyticsSeriesPoint(
    label: json['label'] as String? ?? '',
    value: (json['value'] as num?)?.toDouble() ?? 0,
    extra: Map<String, dynamic>.from(
      json['extra'] as Map<String, dynamic>? ?? const {},
    ),
  );
}

AnalyticsOverview analyticsOverviewFromJson(Map<String, dynamic> json) {
  final metrics = <String, AnalyticsMetric>{};
  final items = (json['metrics'] as List<dynamic>? ?? const [])
      .cast<Map<String, dynamic>>();
  for (final item in items) {
    metrics[item['key'] as String] =
        analyticsMetricFromJson(item['value'] as Map<String, dynamic>);
  }
  return AnalyticsOverview(metrics: metrics);
}

AttendanceAnalytics attendanceAnalyticsFromJson(Map<String, dynamic> json) {
  final summary = json['summary'] as Map<String, dynamic>? ?? const {};
  return AttendanceAnalytics(
    rate: analyticsMetricFromJson(
      summary['rate'] as Map<String, dynamic>? ?? const {},
    ),
    totalRecords: summary['total_records'] as int? ?? 0,
    series: (json['series'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(analyticsSeriesPointFromJson)
        .toList(),
  );
}

GradesAnalytics gradesAnalyticsFromJson(Map<String, dynamic> json) {
  final summary = json['summary'] as Map<String, dynamic>? ?? const {};
  return GradesAnalytics(
    average: analyticsMetricFromJson(
      summary['average'] as Map<String, dynamic>? ?? const {},
    ),
    count: summary['count'] as int? ?? 0,
    distribution: (json['distribution'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map((item) => AnalyticsBucket(
              label: item['label'] as String? ?? '',
              count: item['count'] as int? ?? 0,
            ))
        .toList(),
  );
}

BillingAnalytics billingAnalyticsFromJson(Map<String, dynamic> json) {
  final summary = json['summary'] as Map<String, dynamic>? ?? const {};
  return BillingAnalytics(
    invoiced: (summary['invoiced'] as num?)?.toDouble() ?? 0,
    paid: (summary['paid'] as num?)?.toDouble() ?? 0,
    outstanding: (summary['outstanding'] as num?)?.toDouble() ?? 0,
    collectionRate: analyticsMetricFromJson(
      summary['collection_rate'] as Map<String, dynamic>? ?? const {},
    ),
    series: (json['series'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(analyticsSeriesPointFromJson)
        .toList(),
  );
}

EngagementAnalytics engagementAnalyticsFromJson(Map<String, dynamic> json) {
  final summary = json['summary'] as Map<String, dynamic>? ?? const {};
  return EngagementAnalytics(
    registeredUsers: summary['registered_users'] as int? ?? 0,
    dau: summary['dau'] as int? ?? 0,
    mau: summary['mau'] as int? ?? 0,
    activeUsers: analyticsMetricFromJson(
      summary['active_users'] as Map<String, dynamic>? ?? const {},
    ),
    engagedUsers: summary['engaged_users'] as int? ?? 0,
    funnel: (json['funnel'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map((item) => FunnelStage(
              label: item['label'] as String? ?? '',
              value: item['value'] as int? ?? 0,
            ))
        .toList(),
    featureAdoption: (json['feature_adoption'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map((item) => FeatureAdoptionMetric(
              feature: item['feature'] as String? ?? '',
              users: item['users'] as int? ?? 0,
              adoptionRate: (item['adoption_rate'] as num?)?.toDouble() ?? 0,
            ))
        .toList(),
  );
}

// ── Content ──

ContentItem contentItemFromJson(Map<String, dynamic> json) {
  return ContentItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String?,
    title: json['title'] as String,
    contentType: json['content_type'] as String,
    levelBand: json['level_band'] as String?,
    language: json['language'] as String?,
    status: json['status'] as String,
  );
}

// ── Result ──

Result resultFromJson(Map<String, dynamic> json) {
  return Result(
    assignmentId: json['assignment_id'] as String,
    assignmentTitle: json['assignment_title'] as String,
    courseTitle: json['course_title'] as String,
    submissionId: json['submission_id'] as String?,
    status: json['status'] as String?,
    score: (json['score'] as num?)?.toDouble(),
    feedbackText: json['feedback_text'] as String?,
    totalPoints: json['total_points'] as int,
    dueAt: json['due_at'] as String?,
  );
}

// ── Invoice ──

Invoice invoiceFromJson(Map<String, dynamic> json) {
  return Invoice(
    id: json['id'] as String,
    schoolId: json['school_id'] as String,
    parentId: json['parent_id'] as String,
    periodId: json['period_id'] as String?,
    status: json['status'] as String,
    totalAmount: (json['total_amount'] as num).toDouble(),
    currency: json['currency'] as String,
    issuedDate: json['issued_date'] as String,
    dueDate: json['due_date'] as String,
    items: (json['items'] as List<dynamic>?)
            ?.map((i) => invoiceItemFromJson(i as Map<String, dynamic>))
            .toList() ??
        [],
  );
}

InvoiceItem invoiceItemFromJson(Map<String, dynamic> json) {
  return InvoiceItem(
    id: json['id'] as String,
    description: json['description'] as String,
    amount: (json['amount'] as num).toDouble(),
    unitPrice: (json['unit_price'] as num).toDouble(),
    quantity: json['quantity'] as int,
  );
}

// ── Admin ──

DashboardStats dashboardStatsFromJson(Map<String, dynamic> json) {
  final rolesMap = <String, int>{};
  final roles = json['users_by_role'] as Map<String, dynamic>? ?? {};
  for (final entry in roles.entries) {
    rolesMap[entry.key] = (entry.value as num).toInt();
  }
  return DashboardStats(
    totalUsers: json['total_users'] as int? ?? 0,
    activeSessions: json['active_sessions'] as int? ?? 0,
    activeInvitations: json['active_invitations'] as int? ?? 0,
    auditEvents24h: json['audit_events_24h'] as int? ?? 0,
    pendingJustifications: json['pending_justifications'] as int? ?? 0,
    usersByRole: rolesMap,
  );
}

ManagedUser managedUserFromJson(Map<String, dynamic> json) {
  return ManagedUser(
    id: json['id'] as String,
    email: json['email'] as String,
    fullName: json['full_name'] as String,
    status: json['status'] as String? ?? 'active',
    role: json['role'] as String,
    createdAt: json['created_at'] as String,
    emailVerified: json['email_verified'] as bool? ?? false,
    totpEnabled: json['totp_enabled'] as bool? ?? false,
  );
}

Invitation invitationFromJson(Map<String, dynamic> json) {
  return Invitation(
    id: json['id'] as String,
    roleTarget: json['role_target'] as String,
    status: json['status'] as String,
    expiresAt: json['expires_at'] as String,
    createdAt: json['created_at'] as String,
    issuerUserId: json['issuer_user_id'] as String?,
    consumedAt: json['consumed_at'] as String?,
    consumedBy: json['consumed_by'] as String?,
  );
}

Justification justificationFromJson(Map<String, dynamic> json) {
  return Justification(
    id: json['id'] as String,
    attendanceRecordId: json['attendance_record_id'] as String,
    parentId: json['parent_id'] as String,
    status: json['status'] as String,
    reason: json['reason'] as String? ?? '',
    rejectionReason: json['rejection_reason'] as String?,
    createdAt: json['created_at'] as String,
  );
}

// ── Teacher ──

ClassInfo classInfoFromJson(Map<String, dynamic> json) {
  return ClassInfo(
    id: json['id'] as String,
    code: json['code'] as String? ?? '',
    name: json['name'] as String,
    studentCount: json['student_count'] as int? ?? 0,
    courseCount: json['course_count'] as int? ?? 0,
  );
}

StudentInfo studentInfoFromJson(Map<String, dynamic> json) {
  return StudentInfo(
    id: json['id'] as String,
    fullName: json['full_name'] as String,
    email: json['email'] as String,
    enrollmentStatus: json['enrollment_status'] as String? ?? 'active',
  );
}

Course courseFromJson(Map<String, dynamic> json) {
  return Course(
    id: json['id'] as String,
    classId: json['class_id'] as String,
    title: json['title'] as String,
    description: json['description'] as String?,
    status: json['status'] as String? ?? 'draft',
  );
}

Assignment assignmentFromJson(Map<String, dynamic> json) {
  return Assignment(
    id: json['id'] as String,
    courseId: json['course_id'] as String,
    title: json['title'] as String,
    description: json['description'] as String?,
    dueAt: json['due_at'] as String?,
    totalPoints: json['total_points'] as int? ?? 20,
  );
}

Submission submissionFromJson(Map<String, dynamic> json) {
  final grade = json['grade'] as Map<String, dynamic>?;
  return Submission(
    id: json['id'] as String,
    assignmentId: json['assignment_id'] as String,
    assignmentTitle: json['assignment_title'] as String?,
    assignmentTotalPoints: json['assignment_total_points'] as int?,
    studentId: json['student_id'] as String,
    studentName: json['student_name'] as String?,
    status: json['status'] as String? ?? 'submitted',
    submittedAt: json['submitted_at'] as String?,
    score: (grade?['score'] as num?)?.toDouble() ??
        (json['score'] as num?)?.toDouble(),
    feedbackText:
        grade?['feedback_text'] as String? ?? json['feedback_text'] as String?,
    publishedAt:
        grade?['published_at'] as String? ?? json['published_at'] as String?,
  );
}

Period periodFromJson(Map<String, dynamic> json) {
  return Period(
    id: json['id'] as String,
    name: json['name'] as String? ?? json['id'] as String,
  );
}
