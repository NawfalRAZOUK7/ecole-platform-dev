import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/domain/entities/academic/attendance.dart';
import 'package:ecole_platform/domain/entities/billing/budget.dart';
import 'package:ecole_platform/domain/entities/admin/compliance.dart';
import 'package:ecole_platform/domain/entities/communication/conversation.dart';
import 'package:ecole_platform/domain/entities/reports/financial_health.dart';
import 'package:ecole_platform/domain/entities/academic/gradebook.dart';
import 'package:ecole_platform/domain/entities/school/micro_school.dart';
import 'package:ecole_platform/domain/entities/communication/notification_settings.dart';
import 'package:ecole_platform/domain/entities/reports/reporting.dart';
import 'package:ecole_platform/domain/entities/academic/skills.dart';
import 'package:ecole_platform/domain/entities/sync/sync.dart';
import 'package:ecole_platform/domain/entities/academic/timetable.dart';

import '../helpers/factories.dart';

void main() {
  group('Domain entity coverage', () {
    test('attendance entities map alerts, stats, and thresholds', () {
      final entry = AttendanceEntry.fromJson({
        'attendance_record_id': 'attendance-1',
        'student_id': 'student-1',
        'full_name': 'Student Example',
        'class_id': 'class-1',
        'session_date': '2026-04-11',
        'status': 'late',
        'slot': 'morning',
        'absence_reason': 'Traffic',
        'justification_status': 'pending',
      });
      const bulk = AttendanceBulkRecord(
        studentId: 'student-1',
        status: 'absent',
        absenceReason: 'Medical appointment',
      );
      final justification = AttendanceJustification.fromJson({
        'id': 'justification-1',
        'attendance_record_id': 'attendance-1',
        'reason': 'Medical appointment',
        'status': 'approved',
        'reviewed_at': '2026-04-11T09:00:00Z',
        'review_comment': 'Accepted',
      });
      final trend = AttendanceTrendPoint.fromJson({
        'bucket': 'Week 1',
        'rate': 95.0,
        'present': 19,
        'absent': 1,
        'late': 0,
      });
      final alert = AttendanceAlertItem.fromJson({
        'class_id': 'class-1',
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'reason': 'Attendance threshold reached',
        'attendance_rate': 72.5,
        'threshold': 75.0,
      });
      final stats = AttendanceClassStats.fromJson({
        'class_id': 'class-1',
        'attendance_rate': 91.5,
        'session_count': 40,
        'present': 36,
        'absent': 2,
        'late': 1,
        'excused': 1,
      });
      const export = AttendanceExportResult(
        downloadUrl: '/exports/attendance.csv',
        fileName: 'attendance.csv',
      );
      final threshold = AttendanceThresholdResult.fromJson({
        'class_id': 'class-1',
        'student_id': 'student-1',
        'attendance_rate': 72.5,
        'threshold': 75.0,
        'triggered': true,
      });
      final snapshot = AttendanceAnalyticsSnapshot(
        stats: stats,
        trends: [trend],
        alerts: [alert],
      );

      expect(entry.studentName, 'Student Example');
      expect(bulk.toJson()['absence_reason'], 'Medical appointment');
      expect(justification.toJson()['review_comment'], 'Accepted');
      expect(trend.toJson()['attendance_rate'], 95.0);
      expect(alert.title, 'Alert: Student Example');
      expect(stats.toJson()['total_sessions'], 40);
      expect(export.fileName, 'attendance.csv');
      expect(threshold.triggered, isTrue);
      expect(snapshot.trends.single.label, 'Week 1');
    });

    test('calendar, conversation, and notification entities expose helpers',
        () {
      final event = createCalendarEvent().copyWith(
        myRsvp: 'maybe',
        attendeeCount: 13,
        maybeCount: 3,
        declinedCount: 2,
        rsvps: [
          createEventRsvpRecord(status: 'maybe'),
        ],
      );
      final conversation = Conversation.fromJson({
        'id': 'conversation-1',
        'school_id': 'school-1',
        'type': 'group',
        'created_by': 'user-1',
        'subject': 'Progress update',
        'participants': [
          {
            'user_id': 'user-1',
            'role_in_conversation': 'member',
            'joined_at': '2026-04-01T08:00:00Z',
            'muted': false,
          },
        ],
        'last_message_at': '2026-04-10T10:00:00Z',
        'last_message_body': 'Thanks for the update',
        'unread_count': 1,
        'created_at': '2026-04-01T08:00:00Z',
      });
      final message = Message.fromJson({
        'id': 'message-1',
        'conversation_id': 'conversation-1',
        'sender_id': 'user-1',
        'body': 'Hello from the school app.',
        'sent_at': '2026-04-10T09:30:00Z',
        'edited_at': '2026-04-10T09:45:00Z',
      });
      final announcement = Announcement.fromJson({
        'id': 'announcement-1',
        'school_id': 'school-1',
        'author_id': 'admin-1',
        'title': 'Open day',
        'body': 'Families are welcome on Friday.',
        'target_roles': ['PAR', 'STD'],
        'published_at': '2026-04-10T09:00:00Z',
        'status': 'published',
        'created_at': '2026-04-09T18:00:00Z',
      });
      final notification = createNotificationItem().copyWith(
        isRead: true,
        readAt: '2026-04-10T08:50:00Z',
        channels: const ['in_app'],
      );

      expect(event.myRsvp, 'maybe');
      expect(event.rsvps.single.status, 'maybe');
      expect(conversation.participants.single.userId, 'user-1');
      expect(message.editedAt, '2026-04-10T09:45:00Z');
      expect(announcement.targetRoles, contains('STD'));
      expect(notification.isRead, isTrue);
      expect(notification.channels, ['in_app']);
    });

    test('document entities expose offline getters and copy helpers', () {
      final document = createManagedDocument().copyWith(
        localFilePath: '/tmp/bulletin.pdf',
        downloadCount: 3,
        deduplicated: true,
      );
      final resource = createResourceLibraryItem().copyWith(
        localFilePath: '/tmp/algebra-pack.pdf',
        downloadCount: 13,
        avgRating: 4.8,
        ratingCount: 5,
      );

      expect(document.isPdf, isTrue);
      expect(document.availableOffline, isTrue);
      expect(document.downloadCount, 3);
      expect(document.deduplicated, isTrue);
      expect(resource.availableOffline, isTrue);
      expect(resource.downloadCount, 13);
      expect(resource.avgRating, 4.8);
      expect(resource.ratingCount, 5);
    });

    test('skill entities map analytics payloads', () {
      final dimension = SkillDimension.fromJson({
        'id': 'skill-1',
        'name': 'Creativity',
        'description': 'Original thinking',
        'is_active': true,
      });
      final milestone = SkillMilestone.fromJson({
        'id': 'milestone-1',
        'dimension_id': 'skill-1',
        'title': 'Builds new ideas',
        'level': 'advanced',
        'is_active': true,
      });
      final score = SkillScoreItem.fromJson({
        'dimension_id': 'skill-1',
        'dimension_name': 'Creativity',
        'value': 90.0,
      });
      final progress = SkillProgressItem.fromJson({
        'dimension_id': 'skill-1',
        'dimension_name': 'Creativity',
        'progress_rate': 82.5,
        'milestone_label': 'Advanced',
      });
      final evaluation = SkillEvaluation.fromJson({
        'student_id': 'student-1',
        'overall_score': 88.0,
        'summary': 'Strong creative progress',
        'dimensions': [
          {'id': 'skill-1', 'label': 'Creativity', 'score': 90.0},
        ],
      });
      final passport = SkillPassport.fromJson({
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'academic_year_id': 'year-1',
        'overall_score': 88.0,
        'issued_at': '2026-04-11',
        'dimensions': [
          {'id': 'skill-1', 'label': 'Creativity', 'score': 90.0},
        ],
      });
      final classAnalytics = SkillClassAnalytics.fromJson({
        'class_id': 'class-1',
        'average_score': 82.0,
        'student_count': 24,
        'dimensions': [
          {'id': 'skill-1', 'label': 'Creativity', 'score': 90.0},
        ],
      });
      final schoolAnalytics = SkillSchoolAnalytics.fromJson({
        'average_score': 84.0,
        'dimensions': [
          {'id': 'skill-1', 'label': 'Creativity', 'score': 90.0},
        ],
      });
      final leaderboard = SkillLeaderboardEntry.fromJson({
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'score': 95.0,
      });
      final bundle = SkillAnalyticsBundle(
        analytics: classAnalytics,
        leaderboard: [leaderboard],
      );

      expect(dimension.title, 'Creativity');
      expect(milestone.level, 'advanced');
      expect(score.score, 90.0);
      expect(progress.levelLabel, 'Advanced');
      expect(evaluation.dimensions.single.label, 'Creativity');
      expect(passport.issuedAt, '2026-04-11');
      expect(classAnalytics.studentCount, 24);
      expect(schoolAnalytics.overallScore, 84.0);
      expect(bundle.leaderboard.single.studentName, 'Student Example');
    });

    test('financial and compliance entities map fallback keys', () {
      final retention = RetentionMetric.fromJson({
        'month': 'April',
        'retention_rate': 93.0,
      });
      final cashflow = CashflowForecast.fromJson({
        'month': 'April',
        'inflow': 20000.0,
        'outflow': 8000.0,
      });
      final cost = CostPerStudentAnalysis.fromJson({
        'cost_per_student': 850.0,
        'cost_total': 20400.0,
        'student_count': 24,
      });
      final snapshot = FinancialSnapshot.fromJson({
        'date': '2026-04-01',
        'revenue': 20000.0,
        'expenses': 8000.0,
      });
      final dashboard = FinancialHealthDashboard.fromJson({
        'retention_rate': 93.0,
        'net_cashflow': 12000.0,
        'cost_per_student': 850.0,
        'snapshot': {
          'snapshot_date': '2026-04-01',
          'revenue': 20000.0,
          'expenses': 8000.0,
          'net_position': 12000.0,
        },
      });
      final curriculum = MenCurriculum.fromJson({
        'id': 'curriculum-1',
        'name': 'Arabic',
        'subject': 'Arabic',
        'level': 'middle',
        'grade': '6A',
      });
      final objective = MenObjective.fromJson({
        'id': 'objective-1',
        'curriculum_id': 'curriculum-1',
        'title': 'Read fluently',
        'trimester': 2,
      });
      final mapping = CurriculumMapping.fromJson({
        'id': 'mapping-1',
        'curriculum_id': 'curriculum-1',
        'objective_id': 'objective-1',
        'course_id': 'course-1',
        'content_item_id': 'content-1',
      });
      final metric = ComplianceMetric.fromJson({
        'label': 'Arabic',
        'value': 95.0,
      });
      final compliance = ComplianceDashboardData.fromJson({
        'coverage': 91.5,
        'objectives_rate': 88.2,
        'missing_rate': 11.8,
        'metrics': [
          {'label': 'Arabic', 'value': 95.0},
        ],
      });
      final report = ComplianceReport.fromJson({
        'id': 'report-1',
        'name': 'Coverage report',
        'status': 'ready',
        'created_at': '2026-04-11T09:00:00Z',
        'download_url': '/reports/report-1.pdf',
      });
      final bundle = FinancialHealthDashboardBundle(
        dashboard: dashboard,
        retention: [retention],
        cashflow: [cashflow],
      );

      expect(retention.label, 'April');
      expect(cashflow.net, 12000.0);
      expect(cost.totalCost, 20400.0);
      expect(snapshot.netPosition, 12000.0);
      expect(bundle.dashboard.snapshot.snapshotDate, '2026-04-01');
      expect(curriculum.title, 'Arabic');
      expect(objective.trimester, 2);
      expect(mapping.contentItemId, 'content-1');
      expect(metric.value, 95.0);
      expect(compliance.coverageRate, 91.5);
      expect(report.title, 'Coverage report');
    });

    test('micro school entities map progress bundles', () {
      final school = MicroSchool.fromJson({
        'id': 'micro-1',
        'name': 'Casablanca Hub',
        'description': 'Neighborhood school',
        'location': 'Maarif',
        'city': 'Casablanca',
        'capacity': 20,
        'student_count': 10,
        'status': 'active',
      });
      final enrollment = MicroEnrollment.fromJson({
        'id': 'enrollment-1',
        'micro_school_id': 'micro-1',
        'child_name': 'Student Example',
        'status': 'active',
      });
      final payment = MicroPayment.fromJson({
        'id': 'payment-1',
        'micro_school_id': 'micro-1',
        'amount': 500.0,
        'currency': 'MAD',
        'status': 'pending',
      });
      final resource = MicroResource.fromJson({
        'id': 'resource-1',
        'micro_school_id': 'micro-1',
        'title': 'Story cards',
        'description': 'Reading prompts',
        'resource_type': 'worksheet',
        'language': 'ar',
      });
      final point = MicroMetricPoint.fromJson({
        'label': 'Week 1',
        'value': 80.0,
      });
      final overview = MicroProgressOverview.fromJson({
        'average_progress': 82.5,
        'active_students': 10,
        'completion_rate': 76.0,
        'series': [
          {'label': 'Week 1', 'value': 80.0},
        ],
      });
      final studentProgress = MicroStudentProgress.fromJson({
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'milestones_completed': 5,
        'progress_rate': 90.0,
        'series': [
          {'label': 'Week 1', 'value': 80.0},
        ],
      });
      final bundle = MicroSchoolDetailBundle(
        school: school,
        enrollments: [enrollment],
        resources: [resource],
        payments: [payment],
        progress: overview,
      );

      expect(school.capacityRatio, 0.5);
      expect(enrollment.childName, 'Student Example');
      expect(payment.currency, 'MAD');
      expect(resource.language, 'ar');
      expect(point.value, 80.0);
      expect(studentProgress.progressRate, 90.0);
      expect(bundle.progress.activeStudents, 10);
    });

    test('timetable entities map constraints and generation payloads', () {
      final exception = TimetableException.fromJson({
        'exception_type': 'substituted',
        'substitute_teacher_id': 'teacher-2',
        'new_room': 'Lab 1',
        'reason': 'Teacher absence',
      });
      final slot = TimetableSlot.fromJson({
        'id': 'slot-1',
        'day_of_week': 1,
        'start_time': '08:00',
        'end_time': '09:00',
        'subject': 'Mathematics',
        'teacher_id': 'teacher-1',
        'room': 'Room 5',
        'is_recurring': true,
        'class_id': 'class-1',
        'class_name': '6A',
        'exception': {
          'exception_type': 'substituted',
          'substitute_teacher_id': 'teacher-2',
          'new_room': 'Lab 1',
          'reason': 'Teacher absence',
        },
      });
      final schedule = WeeklySchedule.fromJson({
        'academic_year_id': '2025-2026',
        'week_start': '2026-04-06',
        'week_end': '2026-04-12',
        'slots': [
          {
            'id': 'slot-1',
            'day_of_week': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject': 'Mathematics',
            'teacher_id': 'teacher-1',
            'room': 'Room 5',
            'is_recurring': true,
            'class_id': 'class-1',
          },
        ],
      });
      final availability = TeacherAvailability.fromJson({
        'teacher_id': 'teacher-1',
        'day_of_week': 1,
        'available_from': '08:00',
        'available_until': '17:00',
      });
      final room = RoomConstraint.fromJson({
        'room_name': 'Room 5',
        'capacity': 30,
      });
      final constraints = TimetableConstraints.fromJson({
        'academic_year_id': '2025-2026',
        'max_consecutive_classes': 3,
        'teacher_availability': [
          {
            'teacher_id': 'teacher-1',
            'day_of_week': 1,
            'available_from': '08:00',
            'available_until': '17:00',
          },
        ],
        'room_constraints': [
          {'room_name': 'Room 5', 'capacity': 30},
        ],
      });
      final job = GenerationJob.fromJson({
        'job_id': 'job-1',
        'status': 'running',
        'progress': 65,
        'error': null,
        'created_at': '2026-04-11T09:00:00Z',
      });
      final generatedSlot = GeneratedSlot.fromJson({
        'day_of_week': 2,
        'start_time': '10:00',
        'end_time': '11:00',
        'subject': 'Science',
        'teacher_id': 'teacher-3',
        'room': 'Lab 2',
        'class_id': 'class-2',
      });
      final preview = GenerationPreview.fromJson({
        'job_id': 'job-1',
        'slots': [
          {
            'day_of_week': 2,
            'start_time': '10:00',
            'end_time': '11:00',
            'subject': 'Science',
            'teacher_id': 'teacher-3',
            'room': 'Lab 2',
            'class_id': 'class-2',
          },
        ],
        'warnings': ['Room conflict resolved'],
      });
      final apply = ApplyGenerationResult.fromJson({
        'applied': 18,
        'skipped': 2,
      });

      expect(exception.newRoom, 'Lab 1');
      expect(slot.exception?.reason, 'Teacher absence');
      expect(schedule.slots.single.subject, 'Mathematics');
      expect(availability.availableUntil, '17:00');
      expect(room.capacity, 30);
      expect(constraints.teacherAvailability.single.teacherId, 'teacher-1');
      expect(job.progress, 65);
      expect(generatedSlot.classId, 'class-2');
      expect(preview.warnings.single, contains('Room conflict'));
      expect(apply.applied, 18);
    });

    test('reporting entities expose report job helpers and schedules', () {
      const schedule = ReportSchedule(
        id: 'schedule-1',
        name: 'Weekly billing',
        reportType: 'billing',
        cronExpression: '0 7 * * 1',
        parameters: {'period': 'week'},
        isActive: true,
        createdAt: '2026-04-01T08:00:00Z',
        lastRunAt: '2026-04-08T07:00:00Z',
        nextRunAt: '2026-04-15T07:00:00Z',
      );
      final job = createReportJob().copyWith(
        status: 'generating',
        cacheHit: true,
        localFilePath: '/tmp/report.pdf',
      );
      const options = ReportOptions(
        classes: [ReportOptionItem(id: 'class-1', label: '6A')],
        periods: [ReportOptionItem(id: 'period-1', label: 'Term 1')],
        students: [ReportOptionItem(id: 'student-1', label: 'Student Example')],
        parents: [ReportOptionItem(id: 'parent-1', label: 'Parent Example')],
      );

      expect(schedule.cronExpression, '0 7 * * 1');
      expect(job.isPending, isTrue);
      expect(job.isReady, isFalse);
      expect(job.cacheHit, isTrue);
      expect(job.localFilePath, '/tmp/report.pdf');
      expect(options.parents.single.label, 'Parent Example');
    });

    test('sync entities map devices, conflicts, and health fallbacks', () {
      final device = SyncDevice.fromJson({
        'id': 'device-1',
        'name': 'Parent Phone',
        'device_type': 'tablet',
        'is_active': false,
      });
      final conflict = SyncConflict.fromJson({
        'id': 'conflict-1',
        'entity_type': 'attendance',
        'entity_id': 'attendance-1',
        'message': 'Version mismatch',
      });
      final checkpoint = SyncCheckpoint.fromJson({
        'id': 'checkpoint-1',
        'checkpoint': 'cp-1',
      });
      final health = SyncHealth.fromJson({
        'healthy': true,
        'queue_depth': 2,
        'latency_ms': 120.0,
      });
      const indicator = SyncIndicatorState(
        online: true,
        syncing: false,
        pendingCount: 2,
        failedCount: 1,
        lastSyncAt: '2026-04-11T09:00:00Z',
      );
      final bundle = SyncStatusBundle(
        status: SyncStatus.fromJson({
          'pending_count': 2,
          'last_sync_at': '2026-04-11T09:00:00Z',
          'last_checkpoint': 'cp-1',
          'online': true,
        }),
        health: health,
        devices: [device],
        checkpoints: [checkpoint],
        indicator: indicator,
      );

      expect(device.deviceName, 'Parent Phone');
      expect(conflict.summary, 'Version mismatch');
      expect(checkpoint.checkpoint, 'cp-1');
      expect(health.queueDepth, 2);
      expect(bundle.indicator.failedCount, 1);
    });

    test('budget entities map fallback fields and nested bundles', () {
      final budget = BudgetEnvelope.fromJson({
        'id': 'budget-1',
        'title': 'STEM',
        'budget_code': 'B-1',
        'status': 'active',
        'budget_amount': 1000.0,
        'committed_amount': 600.0,
        'actual_spend': 300.0,
        'currency': 'MAD',
        'owner_role': 'teacher',
        'updated_at': '2026-04-11T09:00:00Z',
      });
      final allocation = BudgetAllocation.fromJson({
        'id': 'allocation-1',
        'budget_id': 'budget-1',
        'category': 'Supplies',
        'amount': 500.0,
        'committed_amount': 120.0,
        'spent_amount': 50.0,
        'currency': 'MAD',
      });
      final request = BudgetRequest.fromJson({
        'id': 'request-1',
        'allocation_id': 'allocation-1',
        'budget_id': 'budget-1',
        'status': 'pending',
        'amount': 80.0,
        'currency': 'MAD',
        'description': 'Markers',
        'justification': 'Workshop',
        'requester': 'Teacher Example',
        'created_at': '2026-04-11T10:00:00Z',
      });
      final transaction = BudgetTransaction.fromJson({
        'id': 'transaction-1',
        'allocation_id': 'allocation-1',
        'amount': 50.0,
        'currency': 'MAD',
        'direction': 'outflow',
        'description': 'Purchased markers',
        'created_at': '2026-04-11T11:00:00Z',
      });
      final analytics = BudgetAnalytics.fromJson({
        'budget_total': 1000.0,
        'allocated_amount': 600.0,
        'spent_amount': 300.0,
        'remaining_amount': 700.0,
        'request_count': 1,
      });
      final bundle = BudgetDetailBundle(
        budget: budget,
        allocations: [allocation],
        transactions: [transaction],
        requests: [request],
        analytics: analytics,
      );

      expect(budget.availableAmount, 700.0);
      expect(allocation.label, 'Supplies');
      expect(request.requesterName, 'Teacher Example');
      expect(transaction.direction, 'outflow');
      expect(analytics.availableAmount, 700.0);
      expect(bundle.requests.single.justification, 'Workshop');
    });

    test('notification settings and gradebook entities preserve updates', () {
      final preference = createNotificationPreferenceItem().copyWith(
        enabled: false,
        digestFrequency: 'weekly',
      );
      const summary = WeightedSummary(
        classId: 'class-1',
        periodId: 'period-1',
        averages: [
          WeightedAverageItem(studentId: 'student-1', avg: 17.5),
        ],
      );
      const detail = StudentGradeDetail(
        studentId: 'student-1',
        studentName: 'Student Example',
        classId: 'class-1',
        className: '6A',
        assessments: [
          StudentAssessmentGrade(
            assessmentId: 'assessment-1',
            title: 'Quiz 1',
            type: 'quiz',
            date: '2026-04-10',
            weight: 0.4,
            score: 18.0,
          ),
        ],
        weightedAverage: 17.5,
      );
      const transcript = GradeTranscript(
        studentId: 'student-1',
        studentName: 'Student Example',
        periods: [
          TranscriptPeriod(
            periodId: 'period-1',
            label: 'Term 1',
            weightedAverage: 17.5,
            subjects: [
              TranscriptSubject(
                subjectId: 'math',
                subjectName: 'Mathematics',
                average: 17.5,
                grades: [
                  StudentAssessmentGrade(
                    assessmentId: 'assessment-1',
                    title: 'Quiz 1',
                    type: 'quiz',
                    date: '2026-04-10',
                    weight: 0.4,
                    score: 18.0,
                  ),
                ],
              ),
            ],
          ),
        ],
      );
      const device = RegisteredDevice(
        id: 'device-1',
        platform: 'ios',
        deviceName: 'Parent iPhone',
        tokenPreview: 'abcd...1234',
        lastActiveAt: '2026-04-10T09:00:00Z',
      );

      expect(preference.enabled, isFalse);
      expect(preference.digestFrequency, 'weekly');
      expect(summary.averages.single.avg, 17.5);
      expect(detail.assessments.single.maxScore, 20.0);
      expect(
        transcript.periods.single.subjects.single.grades.single.score,
        18.0,
      );
      expect(device.platform, 'ios');
    });
  });
}
