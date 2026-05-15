import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/domain/entities/academic/attendance.dart';
import 'package:ecole_platform/domain/entities/billing/budget.dart';
import 'package:ecole_platform/domain/entities/admin/compliance.dart';
import 'package:ecole_platform/domain/entities/reports/financial_health.dart';
import 'package:ecole_platform/domain/entities/academic/gradebook.dart';
import 'package:ecole_platform/domain/entities/school/micro_school.dart';
import 'package:ecole_platform/domain/entities/lms/question_bank.dart';
import 'package:ecole_platform/domain/entities/lms/rubric.dart';
import 'package:ecole_platform/domain/entities/academic/skills.dart';
import 'package:ecole_platform/domain/entities/sync/sync.dart';
import 'package:ecole_platform/domain/entities/academic/timetable.dart';
import 'package:ecole_platform/domain/entities/user/user.dart';

import '../helpers/factories.dart';

void main() {
  group('Domain entities', () {
    test('admin entities preserve constructor data', () {
      final stats = createDashboardStats();
      final user = createManagedUser();

      expect(stats.totalUsers, 120);
      expect(stats.usersByRole['PAR'], 60);
      expect(user.emailVerified, isTrue);
      expect(createInvitation(), equals(createInvitation()));
      expect(createJustification().status, 'pending');
    });

    test('attendance entities round-trip JSON and equality', () {
      const json = {
        'id': 'attendance-1',
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'date': '2026-04-11',
        'status': 'present',
      };

      final entry = AttendanceEntry.fromJson(json);
      final trend = AttendanceTrendPoint.fromJson(
        const {
          'label': 'Week 1',
          'attendance_rate': 95.0,
          'present_count': 19,
          'absent_count': 1,
          'late_count': 0,
        },
      );

      expect(entry, AttendanceEntry.fromJson(json));
      expect(entry.toJson(), json);
      expect(trend.toJson()['attendance_rate'], 95.0);
    });

    test('budget entities compute available amounts and nest cleanly', () {
      final envelope = BudgetEnvelope.fromJson(
        const {
          'id': 'budget-1',
          'name': 'STEM',
          'code': 'B-1',
          'status': 'active',
          'total_amount': 1000.0,
          'allocated_amount': 600.0,
          'spent_amount': 300.0,
          'currency': 'MAD',
        },
      );
      const bundle = BudgetDetailBundle(
        budget: BudgetEnvelope(
          id: 'budget-1',
          name: 'STEM',
          code: 'B-1',
          status: 'active',
          totalAmount: 1000,
          allocatedAmount: 600,
          spentAmount: 300,
          currency: 'MAD',
        ),
        allocations: [
          BudgetAllocation(
            id: 'allocation-1',
            budgetId: 'budget-1',
            label: 'Supplies',
            amount: 500,
            committedAmount: 100,
            spentAmount: 50,
            currency: 'MAD',
          ),
        ],
        transactions: [],
        requests: [],
        analytics: BudgetAnalytics(
          totalBudget: 1000,
          allocatedAmount: 600,
          spentAmount: 300,
          availableAmount: 700,
          openRequests: 1,
        ),
      );

      expect(envelope.availableAmount, 700);
      expect(bundle.allocations.single.label, 'Supplies');
    });

    test('calendar entities expose options and event metadata', () {
      final options = createCalendarOptions();
      final event = createCalendarEvent();

      expect(options.classes.single.label, '6A');
      expect(options.reminderPreferences.single.enabled, isTrue);
      expect(event.titleAr, isNotEmpty);
      expect(event.rsvps.single.status, 'attending');
    });

    test('child link entities preserve linked student data', () {
      final child = createChildLink();

      expect(child.linkId, 'link-1');
      expect(child.studentProfile?['class_level'], '6A');
      expect(createChildLink(), equals(createChildLink()));
    });

    test('compliance entities map dashboards and reports', () {
      final dashboard = ComplianceDashboardData.fromJson(
        const {
          'coverage_rate': 91.5,
          'objectives_covered_rate': 88.2,
          'missing_coverage_rate': 11.8,
          'metrics': [
            {'label': 'Arabic', 'value': 95.0},
          ],
        },
      );
      final report = ComplianceReport.fromJson(
        const {
          'id': 'report-1',
          'title': 'Coverage report',
          'status': 'ready',
          'download_url': '/reports/report-1.pdf',
        },
      );

      expect(dashboard.metrics.single.value, 95.0);
      expect(report.downloadUrl, '/reports/report-1.pdf');
    });

    test('content item entities preserve metadata', () {
      final content = createContentItem();

      expect(content.title, 'Math Worksheet');
      expect(content.language, 'fr');
      expect(createContentItem(), equals(createContentItem()));
    });

    test('conversation entities preserve participants and messages', () {
      final conversation = createConversation();
      final message = createMessage();
      final announcement = createAnnouncement();

      expect(conversation.participants.single.roleInConversation, 'member');
      expect(message.body, contains('school app'));
      expect(announcement.targetRoles, containsAll(['PAR', 'STD']));
    });

    test('document management entities keep checklist and resource state', () {
      final options = createDocumentOptions();
      final document = createManagedDocument();
      final checklist = createStudentDocumentChecklistItem();
      final resource = createResourceLibraryItem();

      expect(options.categories, contains('certificate'));
      expect(document.downloadUrl, contains('bulletin.pdf'));
      expect(checklist.document?.id, 'document-1');
      expect(resource.avgRating, 4.5);
      expect(createResourceRatingSummary().myRating, 5);
    });

    test('feed item entities retain feed attributes', () {
      final item = createFeedItem();

      expect(item.sourceType, 'announcement');
      expect(item.body, contains('School closes early'));
    });

    test('financial health entities map dashboard bundles', () {
      final dashboard = FinancialHealthDashboard.fromJson(
        const {
          'retention_rate': 93.0,
          'net_cashflow': 12000.0,
          'cost_per_student': 850.0,
          'snapshot': {
            'snapshot_date': '2026-04-01',
            'revenue': 20000.0,
            'expenses': 8000.0,
            'net_position': 12000.0,
          },
        },
      );
      const bundle = FinancialHealthDashboardBundle(
        dashboard: FinancialHealthDashboard(
          retentionRate: 93.0,
          netCashflow: 12000.0,
          costPerStudent: 850.0,
          snapshot: FinancialSnapshot(
            snapshotDate: '2026-04-01',
            revenue: 20000.0,
            expenses: 8000.0,
            netPosition: 12000.0,
          ),
        ),
        retention: [
          RetentionMetric(label: 'Apr', rate: 93.0),
        ],
        cashflow: [
          CashflowForecast(
            label: 'Apr',
            inflow: 20000.0,
            outflow: 8000.0,
            net: 12000.0,
          ),
        ],
      );

      expect(dashboard.snapshot.netPosition, 12000.0);
      expect(bundle.retention.single.label, 'Apr');
    });

    test('gradebook entities preserve nested grade structures', () {
      const grid = GradebookGrid(
        classId: 'class-1',
        className: '6A',
        columns: [
          GradebookColumn(
            assessmentId: 'assessment-1',
            title: 'Quiz 1',
            weight: 0.4,
            date: '2026-04-10',
            type: 'quiz',
          ),
        ],
        entries: [
          GradebookEntry(
            studentId: 'student-1',
            studentName: 'Student Example',
            grades: {'assessment-1': 18.0},
            weightedAverage: 18.0,
          ),
        ],
      );

      expect(
        const GradeValueUpdate(
          studentId: 'student-1',
          assessmentId: 'assessment-1',
          value: 18.0,
        ),
        const GradeValueUpdate(
          studentId: 'student-1',
          assessmentId: 'assessment-1',
          value: 18.0,
        ),
      );
      expect(grid.entries.single.grades['assessment-1'], 18.0);
    });

    test('invoice entities preserve money and item details', () {
      final invoice = createInvoice();
      final item = createInvoiceItem();

      expect(invoice.totalAmount, 1200.0);
      expect(invoice.items.single.description, 'Monthly tuition');
      expect(item.unitPrice, 1200.0);
    });

    test('micro school entities map ratios and progress series', () {
      final school = MicroSchool.fromJson(
        const {
          'id': 'micro-1',
          'name': 'Casablanca Hub',
          'description': 'Neighborhood school',
          'location': 'Maarif',
          'city': 'Casablanca',
          'capacity': 20,
          'student_count': 10,
          'status': 'active',
        },
      );
      final progress = MicroProgressOverview.fromJson(
        const {
          'average_progress': 82.5,
          'active_students': 10,
          'completion_rate': 76.0,
          'series': [
            {'label': 'Week 1', 'value': 80.0},
          ],
        },
      );

      expect(school.capacityRatio, 0.5);
      expect(progress.series.single.label, 'Week 1');
    });

    test('notification entities retain delivery preferences', () {
      final item = createNotificationItem();
      final preference = createNotificationPreferenceItem();
      final device = createRegisteredDevice();

      expect(item.channels, contains('push'));
      expect(preference.digestFrequency, 'daily');
      expect(device.platform, 'ios');
    });

    test('question bank entities preserve generated quiz composition', () {
      const choice = QuestionBankChoice(
        id: 'choice-1',
        text: '4',
        isCorrect: true,
      );
      const question = QuestionBankQuestion(
        id: 'question-1',
        subject: 'math',
        type: 'mcq',
        difficulty: 'easy',
        text: 'What is 2 + 2?',
        choices: [choice],
        correctAnswer: '4',
        tags: ['arithmetic'],
        createdBy: 'teacher-1',
        createdAt: '2026-04-10T08:00:00Z',
      );
      const generated = GeneratedQuestionQuiz(
        questions: [question],
        total: 1,
      );

      expect(generated.questions.single.choices.single.isCorrect, isTrue);
      expect(
        const QuestionBankStats(
          total: 1,
          bySubject: {'math': 1},
          byType: {'mcq': 1},
          byDifficulty: {'easy': 1},
        ),
        const QuestionBankStats(
          total: 1,
          bySubject: {'math': 1},
          byType: {'mcq': 1},
          byDifficulty: {'easy': 1},
        ),
      );
    });

    test('quiz entities preserve attempts and result summaries', () {
      final quiz = createQuiz();
      final question = createQuestion();
      final attempt = createQuizAttempt();
      final result = createAttemptResult();

      expect(quiz.questionCount, 10);
      expect(question.options?['B'], '4');
      expect(attempt.status, 'completed');
      expect(result.responses.single.pointsEarned, 5.0);
      expect(createQuizResultSummary().status, 'completed');
    });

    test('reporting entities preserve analytics collections', () {
      final options = createReportOptions();
      final job = createReportJob();
      final engagement = createEngagementAnalytics();

      expect(options.classes.single.label, '6A');
      expect(job.downloadUrl, contains('report.pdf'));
      expect(engagement.featureAdoption.single.feature, 'messages');
      expect(createAnalyticsOverview().metrics['attendance']?.trend, 'up');
    });

    test('result entities preserve grading outcomes', () {
      final result = createResult();

      expect(result.assignmentTitle, 'Essay');
      expect(result.score, 16.0);
      expect(createResult(), equals(createResult()));
    });

    test('rubric entities preserve grading structures', () {
      const rubric = Rubric(
        id: 'rubric-1',
        title: 'Writing rubric',
        description: 'Essay scoring',
        subject: 'French',
        criteria: [
          RubricCriterion(
            id: 'criterion-1',
            name: 'Clarity',
            weight: 0.5,
            levels: [
              RubricLevel(
                id: 'level-1',
                label: 'Excellent',
                score: 5,
                description: 'Clear and precise',
              ),
            ],
          ),
        ],
        maxScore: 10,
        createdBy: 'teacher-1',
        createdAt: '2026-04-10T08:00:00Z',
        updatedAt: '2026-04-10T08:00:00Z',
      );
      const results = RubricResultsResponse(
        rubricId: 'rubric-1',
        results: [
          RubricGradeResult(
            studentId: 'student-1',
            rubricId: 'rubric-1',
            totalScore: 9,
            maxScore: 10,
            percentage: 90.0,
            entries: [
              RubricGradeEntry(
                studentId: 'student-1',
                criterionId: 'criterion-1',
                levelId: 'level-1',
                score: 4.5,
              ),
            ],
          ),
        ],
      );

      expect(rubric.criteria.single.levels.single.label, 'Excellent');
      expect(results.results.single.percentage, 90.0);
    });

    test('skills entities map passports and analytics bundles', () {
      final passport = SkillPassport.fromJson(
        const {
          'student_id': 'student-1',
          'student_name': 'Student Example',
          'academic_year_id': 'year-1',
          'overall_score': 88.0,
          'dimensions': [
            {'id': 'skill-1', 'label': 'Creativity', 'score': 90.0},
          ],
        },
      );
      const bundle = SkillAnalyticsBundle(
        analytics: SkillClassAnalytics(
          classId: 'class-1',
          averageScore: 82.0,
          studentCount: 24,
          dimensions: [
            SkillScoreItem(id: 'skill-1', label: 'Creativity', score: 90.0),
          ],
        ),
        leaderboard: [
          SkillLeaderboardEntry(
            studentId: 'student-1',
            studentName: 'Student Example',
            score: 95.0,
          ),
        ],
      );

      expect(passport.dimensions.single.label, 'Creativity');
      expect(bundle.leaderboard.single.score, 95.0);
    });

    test('sync entities map status and health payloads', () {
      final status = SyncStatus.fromJson(
        const {
          'pending_operations': 3,
          'last_sync_at': '2026-04-10T09:00:00Z',
          'last_checkpoint': 'cp-1',
          'online': true,
        },
      );
      const bundle = SyncStatusBundle(
        status: SyncStatus(
          pendingOperations: 3,
          online: true,
          lastSyncAt: '2026-04-10T09:00:00Z',
          lastCheckpoint: 'cp-1',
        ),
        health: SyncHealth(healthy: true, queueDepth: 1, latencyMs: 120.0),
        devices: [
          SyncDevice(
            id: 'device-1',
            deviceName: 'Parent Phone',
            deviceType: 'mobile',
            isActive: true,
          ),
        ],
        checkpoints: [
          SyncCheckpoint(id: 'checkpoint-1', checkpoint: 'cp-1'),
        ],
        indicator: SyncIndicatorState(
          online: true,
          syncing: false,
          pendingCount: 1,
          failedCount: 0,
        ),
      );

      expect(status.pendingOperations, 3);
      expect(bundle.devices.single.deviceName, 'Parent Phone');
    });

    test('teacher entities preserve roster and coursework data', () {
      final classInfo = createClassInfo();
      final student = createStudentInfo();
      final course = createCourse();
      final assignment = createAssignment();
      final submission = createSubmission();

      expect(classInfo.courseCount, 8);
      expect(student.enrollmentStatus, 'active');
      expect(course.title, 'Mathematics');
      expect(assignment.totalPoints, 20);
      expect(submission.feedbackText, contains('Great'));
      expect(createPeriod().name, 'Term 1');
      expect(createAttendanceRecord().status, 'present');
    });

    test('timetable entities preserve schedules and exceptions', () {
      final slot = createTimetableSlot();
      final schedule = createWeeklySchedule();
      final preview = GenerationPreview.fromJson(
        const {
          'job_id': 'job-1',
          'slots': [
            {
              'day_of_week': 1,
              'start_time': '08:00',
              'end_time': '09:00',
              'subject': 'Math',
              'teacher_id': 'teacher-1',
              'room': 'Room 5',
            },
          ],
          'warnings': ['Room conflict resolved'],
        },
      );

      expect(slot.exception?.reason, 'Teacher absence');
      expect(schedule.slots.single.subject, 'Mathematics');
      expect(preview.warnings.single, contains('Room conflict'));
    });

    test('user entities preserve memberships and permissions', () {
      final user = createUser();

      expect(user.permissions, contains('feed:read'));
      expect(user.memberships.single.schoolId, 'school-1');
      expect(
        const Membership(
          schoolId: 'school-1',
          role: 'PAR',
          status: 'active',
        ),
        const Membership(
          schoolId: 'school-1',
          role: 'PAR',
          status: 'active',
        ),
      );
    });
  });
}
