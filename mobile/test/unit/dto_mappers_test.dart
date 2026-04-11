import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/data/dto/mappers.dart';

void main() {
  group('DTO mappers', () {
    test(
      'map user, notification, calendar, and document payloads',
      () {
        final user = userFromJson({
          'id': 'user-1',
          'email': 'parent@ecole.test',
          'full_name': 'Parent Example',
          'role': 'PAR',
          'school_id': 'school-1',
          'permissions': ['feed:read', 'notifications:read'],
          'memberships': [
            {
              'school_id': 'school-1',
              'role': 'PAR',
              'status': 'active',
            },
          ],
        });
        final feed = feedItemFromJson({
          'id': 'feed-1',
          'school_id': 'school-1',
          'parent_id': 'parent-1',
          'student_id': 'student-1',
          'source_type': 'announcement',
          'source_ref': 'announcement-1',
          'title': 'Important update',
          'body': 'School closes early tomorrow.',
          'created_at': '2026-04-10T08:00:00Z',
        });
        final notification = notificationFromJson({
          'id': 'notification-1',
          'school_id': 'school-1',
          'parent_id': 'parent-1',
          'title': 'New assignment posted',
          'body': 'Check the latest math task.',
          'category': 'academic',
          'priority': 'high',
          'action_url': '/notifications/1',
          'action_payload': {'tab': 'unread'},
          'is_read': true,
          'read_at': '2026-04-10T08:45:00Z',
          'created_at': '2026-04-10T08:30:00Z',
          'channels': ['in_app', 'push'],
        });
        final preference = notificationPreferenceFromJson({
          'channel': 'push',
          'category': 'academic',
          'enabled': false,
          'digest_frequency': 'daily',
        });
        final device = registeredDeviceFromJson({
          'id': 'device-1',
          'platform': 'ios',
          'device_name': 'Parent iPhone',
          'token_preview': 'abcd...1234',
          'last_active_at': '2026-04-10T09:00:00Z',
        });
        final classOption = calendarClassOptionFromJson({
          'id': 'class-1',
          'code': '6A',
          'name': 'Class 6A',
        });
        final reminder = reminderPreferenceFromJson({
          'event_type': 'meeting',
          'enabled': false,
        });
        final event = calendarEventFromJson({
          'id': 'event-1',
          'instance_id': 'instance-1',
          'source': 'calendar',
          'title_fr': 'Reunion',
          'title_ar': 'اجتماع',
          'title_en': 'Meeting',
          'description': 'Quarterly review',
          'type': 'meeting',
          'visibility': 'school',
          'start_at': '2026-04-10T10:00:00Z',
          'end_at': '2026-04-10T11:00:00Z',
          'location': 'Campus A',
          'latitude': 33.5,
          'longitude': -7.6,
          'class_id': 'class-1',
          'role_codes': ['PAR', 'TCH'],
          'capacity': 25,
          'rsvp_deadline': '2026-04-09T10:00:00Z',
          'attendee_count': 12,
          'maybe_count': 2,
          'declined_count': 1,
          'my_rsvp': 'attending',
          'is_all_day': false,
          'is_recurring': true,
          'recurrence_rule': {'freq': 'weekly'},
          'can_edit': true,
          'can_delete': true,
          'can_rsvp': true,
          'is_holiday': false,
          'rsvps': [
            {
              'user_id': 'user-1',
              'full_name': 'Parent Example',
              'role': 'PAR',
              'status': 'attending',
              'responded_at': '2026-04-09T09:00:00Z',
            },
          ],
        });
        final student = documentOptionStudentFromJson({
          'id': 'student-1',
          'full_name': 'Student Example',
          'email': 'student@ecole.test',
        });
        final document = managedDocumentFromJson({
          'id': 'document-1',
          'original_filename': 'bulletin.pdf',
          'filename': 'bulletin_2026.pdf',
          'mime_type': 'application/pdf',
          'size_bytes': 2048,
          'category': 'report_card',
          'sha256': 'abc123',
          'linked_student_id': 'student-1',
          'linked_student_name': 'Student Example',
          'uploader_id': 'admin-1',
          'uploader_name': 'Admin Example',
          'expires_at': '2026-12-31',
          'is_expired': false,
          'is_expiring_soon': true,
          'download_count': 2,
          'thumbnail_url': 'https://files.ecole.test/thumb.png',
          'preview_url': 'https://files.ecole.test/preview.pdf',
          'download_url': 'https://files.ecole.test/bulletin.pdf',
          'created_at': '2026-04-10T09:00:00Z',
          'deleted_at': null,
          'deduplicated': true,
          'can_delete': true,
          'can_hard_delete': false,
          'local_file_path': '/tmp/bulletin.pdf',
        });
        final checklist = studentChecklistItemFromJson({
          'category': 'report_card',
          'required': true,
          'description': 'Quarterly report card',
          'status': 'uploaded',
          'expires_at': '2026-12-31',
          'document': {
            'id': 'document-1',
            'original_filename': 'bulletin.pdf',
            'filename': 'bulletin_2026.pdf',
            'mime_type': 'application/pdf',
            'size_bytes': 2048,
            'category': 'report_card',
            'sha256': 'abc123',
            'uploader_id': 'admin-1',
            'created_at': '2026-04-10T09:00:00Z',
          },
        });
        final resource = resourceLibraryItemFromJson({
          'id': 'resource-1',
          'title': 'Algebra Pack',
          'description': 'Printable practice sheets',
          'subject': 'Mathematics',
          'level': '6A',
          'type': 'worksheet',
          'tags': ['math', 'revision'],
          'visibility': 'school',
          'class_id': 'class-1',
          'download_count': 12,
          'avg_rating': 4.5,
          'rating_count': 4,
          'download_url': 'https://files.ecole.test/algebra-pack.pdf',
          'preview_url': 'https://files.ecole.test/algebra-pack-preview.pdf',
          'thumbnail_url': 'https://files.ecole.test/algebra-pack.png',
          'document': {
            'id': 'document-1',
            'original_filename': 'bulletin.pdf',
            'filename': 'bulletin_2026.pdf',
            'mime_type': 'application/pdf',
            'size_bytes': 2048,
            'category': 'report_card',
            'sha256': 'abc123',
            'uploader_id': 'admin-1',
            'created_at': '2026-04-10T09:00:00Z',
          },
          'my_rating': 5,
          'created_at': '2026-04-01T10:00:00Z',
          'updated_at': '2026-04-10T10:00:00Z',
          'can_edit': true,
          'can_delete': false,
          'can_rate': true,
          'local_file_path': '/tmp/algebra-pack.pdf',
        });
        final ratingSummary = resourceRatingSummaryFromJson({
          'resource_id': 'resource-1',
          'avg_rating': 4.5,
          'rating_count': 4,
          'rating': 5,
        });

        expect(user.memberships.single.schoolId, 'school-1');
        expect(feed.sourceRef, 'announcement-1');
        expect(notification.userId, 'parent-1');
        expect(notification.channels, containsAll(['in_app', 'push']));
        expect(preference.enabled, isFalse);
        expect(device.deviceName, 'Parent iPhone');
        expect(classOption.label, '6A · Class 6A');
        expect(reminder.enabled, isFalse);
        expect(event.rsvps.single.status, 'attending');
        expect(student.email, 'student@ecole.test');
        expect(document.availableOffline, isTrue);
        expect(checklist.document?.category, 'report_card');
        expect(resource.document?.mimeType, 'application/pdf');
        expect(ratingSummary.myRating, 5);
      },
    );

    test('map reporting and analytics payloads', () {
      final option = reportOptionFromJson(
        {
          'id': 'student-1',
          'full_name': 'Student Example',
          'email': 'student@ecole.test',
        },
        primaryKey: 'full_name',
        secondaryKeys: const ['email'],
      );
      final job = reportJobFromJson({
        'id': 'report-1',
        'type': 'student_report_card',
        'status': 'ready',
        'parameters': {'student_id': 'student-1'},
        'created_at': '2026-04-10T08:00:00Z',
        'completed_at': '2026-04-10T08:05:00Z',
        'expires_at': '2026-05-10T08:05:00Z',
        'error_message': null,
        'download_url': '/reports/report-1.pdf',
        'cache_hit': true,
        'local_file_path': '/tmp/report-1.pdf',
      });
      final metric = analyticsMetricFromJson({
        'current': 91.5,
        'previous': 88.0,
        'change_percent': 4.0,
        'trend': 'up',
      });
      final point = analyticsSeriesPointFromJson({
        'label': 'Week 1',
        'value': 91.5,
        'extra': {'count': 24},
      });
      final overview = analyticsOverviewFromJson({
        'metrics': [
          {
            'key': 'attendance',
            'value': {
              'current': 91.5,
              'previous': 88.0,
              'change_percent': 4.0,
              'trend': 'up',
            },
          },
        ],
      });
      final attendance = attendanceAnalyticsFromJson({
        'summary': {
          'rate': {
            'current': 91.5,
            'previous': 88.0,
            'change_percent': 4.0,
            'trend': 'up',
          },
          'total_records': 120,
        },
        'series': [
          {
            'label': 'Week 1',
            'value': 91.5,
            'extra': {'count': 24},
          },
        ],
      });
      final grades = gradesAnalyticsFromJson({
        'summary': {
          'average': {
            'current': 14.2,
            'previous': 13.5,
            'change_percent': 5.2,
            'trend': 'up',
          },
          'count': 30,
        },
        'distribution': [
          {'label': '10-12', 'count': 8},
        ],
      });
      final billing = billingAnalyticsFromJson({
        'summary': {
          'invoiced': 10000,
          'paid': 8000,
          'outstanding': 2000,
          'collection_rate': {
            'current': 80.0,
            'previous': 75.0,
            'change_percent': 6.7,
            'trend': 'up',
          },
        },
        'series': [
          {
            'label': 'April',
            'value': 8000,
            'extra': {'invoiced': 10000},
          },
        ],
      });
      final engagement = engagementAnalyticsFromJson({
        'summary': {
          'registered_users': 120,
          'dau': 42,
          'mau': 90,
          'active_users': {
            'current': 58.0,
            'previous': 50.0,
            'change_percent': 16.0,
            'trend': 'up',
          },
          'engaged_users': 58,
        },
        'funnel': [
          {'label': 'Registered', 'value': 120},
        ],
        'feature_adoption': [
          {
            'feature': 'messages',
            'users': 80,
            'adoption_rate': 66.7,
          },
        ],
      });

      expect(option.secondary, 'student@ecole.test');
      expect(job.cacheHit, isTrue);
      expect(metric.changePercent, 4.0);
      expect(point.extra['count'], 24);
      expect(overview.metrics['attendance']?.trend, 'up');
      expect(attendance.totalRecords, 120);
      expect(grades.distribution.single.count, 8);
      expect(billing.collectionRate.current, 80.0);
      expect(engagement.featureAdoption.single.feature, 'messages');
    });

    test('map content, result, invoice, and billing policy payloads', () {
      final content = contentItemFromJson({
        'id': 'content-1',
        'school_id': 'school-1',
        'title': 'Math Worksheet',
        'content_type': 'worksheet',
        'level_band': 'middle-school',
        'language': 'fr',
        'status': 'published',
      });
      final result = resultFromJson({
        'assignment_id': 'assignment-1',
        'assignment_title': 'Essay',
        'course_title': 'French',
        'submission_id': 'submission-1',
        'status': 'graded',
        'score': 16,
        'feedback_text': 'Solid work',
        'total_points': 20,
        'due_at': '2026-04-10T12:00:00Z',
      });
      final invoice = invoiceFromJson({
        'id': 'invoice-1',
        'school_id': 'school-1',
        'parent_id': 'parent-1',
        'period_id': 'period-1',
        'invoice_number': 'INV-2026-001',
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'label': 'Tuition',
        'status': 'pending',
        'total_amount': 1200.0,
        'currency': 'MAD',
        'issued_date': '2026-04-01',
        'due_date': '2026-04-15',
        'balance_due': 600.0,
        'items': [
          {
            'id': 'invoice-item-1',
            'description': 'Monthly tuition',
            'amount': 1200.0,
            'unit_price': 1200.0,
            'quantity': 1,
          },
        ],
      });
      final payment = invoicePaymentFromJson({
        'id': 'payment-1',
        'invoice_id': 'invoice-1',
        'amount': 600.0,
        'method': 'bank_transfer',
        'status': 'pending',
        'created_at': '2026-04-10T09:00:00Z',
        'finalized_at': null,
        'proof_url': '/proofs/payment-1.png',
      });
      final siblingPolicy = siblingPolicyFromJson({
        'id': 'policy-1',
        'discounts': [
          {'sibling_rank': 2, 'discount_percent': 10.0},
        ],
        'max_siblings_covered': 3,
      });
      final lateFee = lateFeePolicyFromJson({
        'id': 'late-fee-1',
        'grace_period_days': 5,
        'fee_percent': 2.5,
        'max_fee_cap': 200.0,
      });
      final plan = paymentPlanFromJson({
        'id': 'plan-1',
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'name': 'Installments',
        'total_amount': 1200.0,
        'start_date': '2026-04-01',
        'status': 'active',
        'created_at': '2026-04-01T08:00:00Z',
        'installments': [
          {
            'id': 'installment-1',
            'plan_id': 'plan-1',
            'due_date': '2026-04-15',
            'amount': 600.0,
            'status': 'pending',
            'paid_at': null,
          },
        ],
      });

      expect(content.contentType, 'worksheet');
      expect(result.feedbackText, 'Solid work');
      expect(invoice.items.single.description, 'Monthly tuition');
      expect(payment.proofUrl, '/proofs/payment-1.png');
      expect(siblingPolicy.discounts.single.discountPercent, 10.0);
      expect(lateFee.maxFeeCap, 200.0);
      expect(plan.installments.single.amount, 600.0);
    });

    test('map admin and teacher payloads', () {
      final stats = dashboardStatsFromJson({
        'total_users': 120,
        'active_sessions': 18,
        'active_invitations': 4,
        'audit_events_24h': 26,
        'pending_justifications': 3,
        'users_by_role': {
          'PAR': 60,
          'STD': 40,
        },
      });
      final user = managedUserFromJson({
        'id': 'managed-user-1',
        'email': 'user@ecole.test',
        'full_name': 'Managed User',
        'status': 'active',
        'role': 'TCH',
        'created_at': '2026-04-01T09:00:00Z',
        'email_verified': true,
        'totp_enabled': false,
      });
      final invitation = invitationFromJson({
        'id': 'invite-1',
        'role_target': 'PAR',
        'status': 'pending',
        'expires_at': '2026-05-01T00:00:00Z',
        'created_at': '2026-04-01T00:00:00Z',
        'issuer_user_id': 'admin-1',
        'consumed_at': null,
        'consumed_by': null,
      });
      final justification = justificationFromJson({
        'id': 'justification-1',
        'attendance_record_id': 'attendance-1',
        'parent_id': 'parent-1',
        'status': 'pending',
        'reason': 'Medical appointment',
        'rejection_reason': null,
        'created_at': '2026-04-10T08:15:00Z',
      });
      final classInfo = classInfoFromJson({
        'id': 'class-1',
        'code': '6A',
        'name': 'Class 6A',
        'student_count': 28,
        'course_count': 8,
      });
      final student = studentInfoFromJson({
        'id': 'student-1',
        'full_name': 'Student Example',
        'email': 'student@ecole.test',
        'enrollment_status': 'active',
      });
      final course = courseFromJson({
        'id': 'course-1',
        'class_id': 'class-1',
        'title': 'Mathematics',
        'description': 'Core math class',
        'status': 'active',
      });
      final assignment = assignmentFromJson({
        'id': 'assignment-1',
        'course_id': 'course-1',
        'title': 'Homework 1',
        'description': 'Complete the worksheet',
        'due_at': '2026-04-12T18:00:00Z',
        'total_points': 20,
      });
      final submission = submissionFromJson({
        'id': 'submission-1',
        'assignment_id': 'assignment-1',
        'assignment_title': 'Homework 1',
        'assignment_total_points': 20,
        'student_id': 'student-1',
        'student_name': 'Student Example',
        'status': 'submitted',
        'submitted_at': '2026-04-11T10:00:00Z',
        'grade': {
          'score': 18.0,
          'feedback_text': 'Great effort',
          'published_at': '2026-04-11T12:00:00Z',
        },
      });
      final period = periodFromJson({
        'id': 'period-1',
        'name': 'Term 1',
      });

      expect(stats.usersByRole['PAR'], 60);
      expect(user.emailVerified, isTrue);
      expect(invitation.roleTarget, 'PAR');
      expect(justification.reason, 'Medical appointment');
      expect(classInfo.courseCount, 8);
      expect(student.enrollmentStatus, 'active');
      expect(course.status, 'active');
      expect(assignment.totalPoints, 20);
      expect(submission.feedbackText, 'Great effort');
      expect(period.name, 'Term 1');
    });
  });
}
