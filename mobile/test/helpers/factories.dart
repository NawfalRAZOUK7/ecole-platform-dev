import 'package:ecole_platform/domain/entities/admin/admin.dart';
import 'package:ecole_platform/domain/entities/communication/calendar_event.dart';
import 'package:ecole_platform/domain/entities/user/child_link.dart';
import 'package:ecole_platform/domain/entities/content/content_item.dart';
import 'package:ecole_platform/domain/entities/communication/conversation.dart';
import 'package:ecole_platform/domain/entities/content/document_management.dart';
import 'package:ecole_platform/domain/entities/content/feed_item.dart';
import 'package:ecole_platform/domain/entities/billing/invoice.dart';
import 'package:ecole_platform/domain/entities/communication/notification_item.dart';
import 'package:ecole_platform/domain/entities/communication/notification_settings.dart';
import 'package:ecole_platform/domain/entities/lms/quiz.dart';
import 'package:ecole_platform/domain/entities/reports/reporting.dart';
import 'package:ecole_platform/domain/entities/academic/result.dart';
import 'package:ecole_platform/domain/entities/lms/teacher.dart';
import 'package:ecole_platform/domain/entities/academic/timetable.dart';
import 'package:ecole_platform/domain/entities/user/user.dart';

Membership createMembership({
  String schoolId = 'school-1',
  String role = 'PAR',
  String status = 'active',
}) {
  return Membership(
    schoolId: schoolId,
    role: role,
    status: status,
  );
}

User createUser({
  String id = 'user-1',
  String email = 'parent@ecole.test',
  String fullName = 'Parent Example',
  String role = 'PAR',
  String schoolId = 'school-1',
  List<String> permissions = const ['feed:read'],
  List<Membership>? memberships,
}) {
  return User(
    id: id,
    email: email,
    fullName: fullName,
    role: role,
    schoolId: schoolId,
    permissions: permissions,
    memberships:
        memberships ?? [createMembership(schoolId: schoolId, role: role)],
  );
}

FeedItem createFeedItem({
  String id = 'feed-1',
  String schoolId = 'school-1',
  String parentId = 'parent-1',
  String? studentId = 'student-1',
  String sourceType = 'announcement',
  String? sourceRef = 'announcement-1',
  String title = 'Important update',
  String? body = 'School closes early tomorrow.',
  String createdAt = '2026-04-10T08:00:00Z',
}) {
  return FeedItem(
    id: id,
    schoolId: schoolId,
    parentId: parentId,
    studentId: studentId,
    sourceType: sourceType,
    sourceRef: sourceRef,
    title: title,
    body: body,
    createdAt: createdAt,
  );
}

CalendarClassOption createCalendarClassOption({
  String id = 'class-1',
  String label = '6A',
}) {
  return CalendarClassOption(id: id, label: label);
}

ReminderPreference createReminderPreference({
  String eventType = 'meeting',
  bool enabled = true,
}) {
  return ReminderPreference(eventType: eventType, enabled: enabled);
}

CalendarOptions createCalendarOptions() {
  return CalendarOptions(
    classes: [createCalendarClassOption()],
    icalUrl: 'https://calendar.ecole.test/feed.ics',
    reminderPreferences: [createReminderPreference()],
  );
}

EventRsvpRecord createEventRsvpRecord({
  String userId = 'user-1',
  String fullName = 'Parent Example',
  String role = 'PAR',
  String status = 'attending',
  String respondedAt = '2026-04-10T10:00:00Z',
}) {
  return EventRsvpRecord(
    userId: userId,
    fullName: fullName,
    role: role,
    status: status,
    respondedAt: respondedAt,
  );
}

CalendarEvent createCalendarEvent({
  String id = 'event-1',
  String instanceId = 'event-instance-1',
  String source = 'school',
  String titleFr = 'Réunion parents-professeurs',
  String? titleAr = 'اجتماع أولياء الأمور',
  String? titleEn = 'Parent teacher meeting',
  String? description = 'Discussion trimestrielle',
  String type = 'meeting',
  String visibility = 'school',
  String startAt = '2026-04-10T10:00:00Z',
  String endAt = '2026-04-10T11:00:00Z',
}) {
  return CalendarEvent(
    id: id,
    instanceId: instanceId,
    source: source,
    titleFr: titleFr,
    titleAr: titleAr,
    titleEn: titleEn,
    description: description,
    type: type,
    visibility: visibility,
    startAt: startAt,
    endAt: endAt,
    location: 'Campus A',
    classId: 'class-1',
    roleCodes: const ['PAR', 'TCH'],
    attendeeCount: 12,
    maybeCount: 2,
    declinedCount: 1,
    myRsvp: 'attending',
    canEdit: true,
    canDelete: true,
    canRsvp: true,
    rsvps: [createEventRsvpRecord()],
  );
}

DashboardStats createDashboardStats() {
  return const DashboardStats(
    totalUsers: 120,
    activeSessions: 18,
    activeInvitations: 4,
    auditEvents24h: 26,
    pendingJustifications: 3,
    usersByRole: {
      'PAR': 60,
      'STD': 40,
      'TCH': 15,
      'ADM': 5,
    },
  );
}

ManagedUser createManagedUser({
  String id = 'managed-user-1',
  String email = 'user@ecole.test',
  String fullName = 'Managed User',
  String status = 'active',
  String role = 'TCH',
  String createdAt = '2026-04-01T09:00:00Z',
  bool emailVerified = true,
  bool totpEnabled = false,
}) {
  return ManagedUser(
    id: id,
    email: email,
    fullName: fullName,
    status: status,
    role: role,
    createdAt: createdAt,
    emailVerified: emailVerified,
    totpEnabled: totpEnabled,
  );
}

Invitation createInvitation() {
  return const Invitation(
    id: 'invite-1',
    roleTarget: 'PAR',
    status: 'pending',
    expiresAt: '2026-05-01T00:00:00Z',
    createdAt: '2026-04-01T00:00:00Z',
    issuerUserId: 'admin-1',
  );
}

Justification createJustification() {
  return const Justification(
    id: 'justification-1',
    attendanceRecordId: 'attendance-1',
    parentId: 'parent-1',
    status: 'pending',
    reason: 'Medical appointment',
    createdAt: '2026-04-10T08:15:00Z',
  );
}

ChildLink createChildLink() {
  return const ChildLink(
    userId: 'student-1',
    fullName: 'Student Example',
    email: 'student@ecole.test',
    linkId: 'link-1',
    linkedAt: '2026-03-01T08:00:00Z',
    studentProfile: {'class_level': '6A'},
  );
}

ContentItem createContentItem() {
  return const ContentItem(
    id: 'content-1',
    schoolId: 'school-1',
    title: 'Math Worksheet',
    contentType: 'worksheet',
    levelBand: 'middle-school',
    language: 'fr',
    status: 'published',
  );
}

Participant createParticipant() {
  return const Participant(
    userId: 'user-1',
    roleInConversation: 'member',
    joinedAt: '2026-04-01T08:00:00Z',
    muted: false,
  );
}

Conversation createConversation() {
  return Conversation(
    id: 'conversation-1',
    schoolId: 'school-1',
    type: 'direct',
    createdBy: 'user-1',
    subject: 'Progress update',
    participants: [createParticipant()],
    lastMessageAt: '2026-04-10T10:00:00Z',
    lastMessageBody: 'Thanks for the update',
    unreadCount: 1,
    createdAt: '2026-04-01T08:00:00Z',
  );
}

Message createMessage() {
  return const Message(
    id: 'message-1',
    conversationId: 'conversation-1',
    senderId: 'user-1',
    body: 'Hello from the school app.',
    sentAt: '2026-04-10T09:30:00Z',
  );
}

Announcement createAnnouncement() {
  return const Announcement(
    id: 'announcement-1',
    schoolId: 'school-1',
    authorId: 'admin-1',
    title: 'Open day',
    body: 'Families are welcome on Friday.',
    targetRoles: ['PAR', 'STD'],
    publishedAt: '2026-04-10T09:00:00Z',
    status: 'published',
    createdAt: '2026-04-09T18:00:00Z',
  );
}

DocumentOptionStudent createDocumentOptionStudent() {
  return const DocumentOptionStudent(
    id: 'student-1',
    fullName: 'Student Example',
    email: 'student@ecole.test',
  );
}

DocumentOptions createDocumentOptions() {
  return DocumentOptions(
    students: [createDocumentOptionStudent()],
    categories: const ['certificate', 'report_card'],
  );
}

ManagedDocument createManagedDocument() {
  return const ManagedDocument(
    id: 'document-1',
    originalFilename: 'bulletin.pdf',
    filename: 'bulletin_2026.pdf',
    mimeType: 'application/pdf',
    sizeBytes: 2048,
    category: 'report_card',
    sha256: 'abc123',
    linkedStudentId: 'student-1',
    linkedStudentName: 'Student Example',
    uploaderId: 'admin-1',
    uploaderName: 'Admin Example',
    downloadUrl: 'https://files.ecole.test/bulletin.pdf',
    previewUrl: 'https://files.ecole.test/bulletin-preview.pdf',
    createdAt: '2026-04-10T09:00:00Z',
    canDelete: true,
  );
}

StudentDocumentChecklistItem createStudentDocumentChecklistItem() {
  return StudentDocumentChecklistItem(
    category: 'report_card',
    required: true,
    description: 'Quarterly report card',
    status: 'uploaded',
    document: createManagedDocument(),
  );
}

ResourceLibraryItem createResourceLibraryItem() {
  return ResourceLibraryItem(
    id: 'resource-1',
    title: 'Algebra Pack',
    description: 'Printable practice sheets',
    subject: 'Mathematics',
    level: '6A',
    type: 'worksheet',
    tags: const ['math', 'revision'],
    visibility: 'school',
    downloadCount: 12,
    avgRating: 4.5,
    ratingCount: 4,
    downloadUrl: 'https://files.ecole.test/algebra-pack.pdf',
    document: createManagedDocument(),
    myRating: 5,
    createdAt: '2026-04-01T10:00:00Z',
    canRate: true,
  );
}

ResourceRatingSummary createResourceRatingSummary() {
  return const ResourceRatingSummary(
    resourceId: 'resource-1',
    avgRating: 4.5,
    ratingCount: 4,
    myRating: 5,
  );
}

InvoiceItem createInvoiceItem() {
  return const InvoiceItem(
    id: 'invoice-item-1',
    description: 'Monthly tuition',
    amount: 1200,
    unitPrice: 1200,
    quantity: 1,
  );
}

Invoice createInvoice() {
  return Invoice(
    id: 'invoice-1',
    schoolId: 'school-1',
    parentId: 'parent-1',
    periodId: 'period-1',
    status: 'pending',
    totalAmount: 1200,
    currency: 'MAD',
    issuedDate: '2026-04-01',
    dueDate: '2026-04-15',
    items: [createInvoiceItem()],
  );
}

NotificationItem createNotificationItem() {
  return const NotificationItem(
    id: 'notification-1',
    schoolId: 'school-1',
    userId: 'user-1',
    eventRef: 'feed-1',
    title: 'New assignment posted',
    body: 'Check the latest math task.',
    category: 'academic',
    priority: 'normal',
    createdAt: '2026-04-10T08:45:00Z',
    channels: ['in_app', 'push'],
  );
}

NotificationPreferenceItem createNotificationPreferenceItem() {
  return const NotificationPreferenceItem(
    channel: 'push',
    category: 'academic',
    enabled: true,
    digestFrequency: 'daily',
  );
}

RegisteredDevice createRegisteredDevice() {
  return const RegisteredDevice(
    id: 'device-1',
    platform: 'ios',
    deviceName: 'Parent iPhone',
    tokenPreview: 'abcd...1234',
    lastActiveAt: '2026-04-10T09:00:00Z',
  );
}

Question createQuestion() {
  return const Question(
    id: 'question-1',
    questionType: 'MCQ',
    questionText: 'What is 2 + 2?',
    options: {'A': '3', 'B': '4'},
    points: 5,
    order: 1,
  );
}

Quiz createQuiz() {
  return const Quiz(
    id: 'quiz-1',
    title: 'Math basics',
    description: 'Warm-up questions',
    subject: 'Mathematics',
    difficulty: 'easy',
    timeLimitMinutes: 15,
    maxAttempts: 3,
    questionCount: 10,
    totalPoints: 50,
    status: 'published',
  );
}

QuizAttempt createQuizAttempt() {
  return const QuizAttempt(
    id: 'attempt-1',
    quizId: 'quiz-1',
    attemptNo: 1,
    startedAt: '2026-04-10T08:00:00Z',
    completedAt: '2026-04-10T08:12:00Z',
    score: 42,
    maxScore: 50,
    status: 'completed',
  );
}

QuizResultResponse createQuizResultResponse() {
  return const QuizResultResponse(
    questionId: 'question-1',
    questionType: 'MCQ',
    questionText: 'What is 2 + 2?',
    studentAnswer: 'B',
    correctAnswer: 'B',
    isCorrect: true,
    pointsEarned: 5,
    points: 5,
    explanation: '2 + 2 equals 4',
  );
}

AttemptResult createAttemptResult() {
  return AttemptResult(
    attempt: createQuizAttempt(),
    responses: [createQuizResultResponse()],
  );
}

LibraryItem createLibraryItem() {
  return const LibraryItem(
    id: 'library-item-1',
    schoolId: 'school-1',
    title: 'Science experiment',
    contentType: 'video',
    levelBand: 'middle-school',
    language: 'fr',
    subject: 'Science',
    description: 'Lab safety overview',
    origin: 'platform',
    status: 'published',
  );
}

ContentSubmission createContentSubmission() {
  return const ContentSubmission(
    id: 'submission-1',
    contentItemId: 'content-1',
    contentTitle: 'Math Worksheet',
    status: 'pending',
    submittedAt: '2026-04-10T07:00:00Z',
  );
}

AssignedContent createAssignedContent() {
  return const AssignedContent(
    id: 'assigned-content-1',
    contentItemId: 'content-1',
    title: 'Reading assignment',
    contentType: 'document',
    subject: 'French',
    description: 'Read chapter 2',
    progress: 'started',
    streamUrl: 'https://stream.ecole.test/item/1',
  );
}

QuizResultSummary createQuizResultSummary() {
  return const QuizResultSummary(
    quizTitle: 'Math basics',
    attemptNo: 1,
    score: 42,
    maxScore: 50,
    status: 'completed',
    completedAt: '2026-04-10T08:12:00Z',
  );
}

ReportOptionItem createReportOptionItem({
  String id = 'option-1',
  String label = 'Period 1',
  String? secondary = 'Current',
}) {
  return ReportOptionItem(id: id, label: label, secondary: secondary);
}

ReportOptions createReportOptions() {
  return ReportOptions(
    classes: [createReportOptionItem(id: 'class-1', label: '6A')],
    periods: [createReportOptionItem(id: 'period-1', label: 'Period 1')],
    students: [
      createReportOptionItem(id: 'student-1', label: 'Student Example'),
    ],
    parents: [createReportOptionItem(id: 'parent-1', label: 'Parent Example')],
  );
}

ReportJob createReportJob() {
  return const ReportJob(
    id: 'report-1',
    type: 'student_report_card',
    status: 'ready',
    parameters: {'student_id': 'student-1'},
    createdAt: '2026-04-10T08:00:00Z',
    completedAt: '2026-04-10T08:05:00Z',
    downloadUrl: 'https://files.ecole.test/report.pdf',
  );
}

AnalyticsMetric createAnalyticsMetric() {
  return const AnalyticsMetric(
    current: 91.5,
    previous: 88.0,
    changePercent: 4.0,
    trend: 'up',
  );
}

AnalyticsSeriesPoint createAnalyticsSeriesPoint() {
  return const AnalyticsSeriesPoint(
    label: 'Week 1',
    value: 91.5,
    extra: {'count': 24},
  );
}

AnalyticsBucket createAnalyticsBucket() {
  return const AnalyticsBucket(label: '10-12', count: 8);
}

AnalyticsOverview createAnalyticsOverview() {
  return AnalyticsOverview(
    metrics: {'attendance': createAnalyticsMetric()},
  );
}

AttendanceAnalytics createAttendanceAnalytics() {
  return AttendanceAnalytics(
    rate: createAnalyticsMetric(),
    totalRecords: 120,
    series: [createAnalyticsSeriesPoint()],
  );
}

GradesAnalytics createGradesAnalytics() {
  return GradesAnalytics(
    average: createAnalyticsMetric(),
    count: 30,
    distribution: [createAnalyticsBucket()],
  );
}

BillingAnalytics createBillingAnalytics() {
  return BillingAnalytics(
    invoiced: 10000,
    paid: 8000,
    outstanding: 2000,
    collectionRate: createAnalyticsMetric(),
    series: [createAnalyticsSeriesPoint()],
  );
}

FunnelStage createFunnelStage() {
  return const FunnelStage(label: 'Registered', value: 120);
}

FeatureAdoptionMetric createFeatureAdoptionMetric() {
  return const FeatureAdoptionMetric(
    feature: 'messages',
    users: 80,
    adoptionRate: 66.7,
  );
}

EngagementAnalytics createEngagementAnalytics() {
  return EngagementAnalytics(
    registeredUsers: 120,
    dau: 42,
    mau: 90,
    activeUsers: createAnalyticsMetric(),
    engagedUsers: 58,
    funnel: [createFunnelStage()],
    featureAdoption: [createFeatureAdoptionMetric()],
  );
}

Result createResult() {
  return const Result(
    assignmentId: 'assignment-1',
    assignmentTitle: 'Essay',
    courseTitle: 'French',
    submissionId: 'submission-1',
    status: 'graded',
    score: 16,
    feedbackText: 'Solid work',
    totalPoints: 20,
    dueAt: '2026-04-10T12:00:00Z',
  );
}

ClassInfo createClassInfo() {
  return const ClassInfo(
    id: 'class-1',
    code: '6A',
    name: 'Class 6A',
    studentCount: 28,
    courseCount: 8,
  );
}

StudentInfo createStudentInfo() {
  return const StudentInfo(
    id: 'student-1',
    fullName: 'Student Example',
    email: 'student@ecole.test',
    enrollmentStatus: 'active',
  );
}

Course createCourse() {
  return const Course(
    id: 'course-1',
    classId: 'class-1',
    title: 'Mathematics',
    description: 'Core math class',
    status: 'active',
  );
}

Assignment createAssignment() {
  return const Assignment(
    id: 'assignment-1',
    courseId: 'course-1',
    title: 'Homework 1',
    description: 'Complete the worksheet',
    dueAt: '2026-04-12T18:00:00Z',
    totalPoints: 20,
  );
}

Submission createSubmission() {
  return const Submission(
    id: 'submission-1',
    assignmentId: 'assignment-1',
    assignmentTitle: 'Homework 1',
    assignmentTotalPoints: 20,
    studentId: 'student-1',
    studentName: 'Student Example',
    status: 'submitted',
    submittedAt: '2026-04-11T10:00:00Z',
    score: 18,
    feedbackText: 'Great effort',
    publishedAt: '2026-04-11T12:00:00Z',
  );
}

Period createPeriod() {
  return const Period(id: 'period-1', name: 'Term 1');
}

AttendanceRecord createAttendanceRecord() {
  return AttendanceRecord(
    studentId: 'student-1',
    status: 'present',
  );
}

TimetableException createTimetableException() {
  return const TimetableException(
    exceptionType: 'substituted',
    substituteTeacherId: 'teacher-2',
    newRoom: 'Lab 1',
    reason: 'Teacher absence',
  );
}

TimetableSlot createTimetableSlot() {
  return TimetableSlot(
    id: 'slot-1',
    dayOfWeek: 1,
    startTime: '08:00',
    endTime: '09:00',
    subject: 'Mathematics',
    teacherId: 'teacher-1',
    room: 'Room 5',
    isRecurring: true,
    classId: 'class-1',
    className: '6A',
    exception: createTimetableException(),
  );
}

WeeklySchedule createWeeklySchedule() {
  return WeeklySchedule(
    academicYearId: '2025-2026',
    weekStart: '2026-04-06',
    weekEnd: '2026-04-12',
    slots: [createTimetableSlot()],
  );
}
