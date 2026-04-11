import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/offline_queue.dart';
import 'package:ecole_platform/domain/entities/attendance.dart';
import 'package:ecole_platform/domain/entities/child_link.dart';
import 'package:ecole_platform/domain/entities/feed_item.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';
import 'package:ecole_platform/domain/entities/notification_settings.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/domain/entities/user.dart';
import 'package:ecole_platform/domain/repositories/attendance_repository.dart';
import 'package:ecole_platform/domain/repositories/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/teacher_repository.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/shared/secure_storage.dart';

class FakeAppEnvironment {
  FakeAppEnvironment()
      : storage = InMemorySecureTokenStorage(),
        cacheStore = InMemoryCacheStore(),
        offlineQueue = InMemoryOfflineQueue(),
        biometricService = FakeBiometricService() {
    authRepository = FakeAuthRepository(this);
    feedRepository = FakeFeedRepository(this);
    notificationRepository = FakeNotificationRepository(this);
    teacherRepository = FakeTeacherRepository(this);
    attendanceRepository = FakeAttendanceRepository(this);
  }

  final InMemorySecureTokenStorage storage;
  final InMemoryCacheStore cacheStore;
  final InMemoryOfflineQueue offlineQueue;
  final FakeBiometricService biometricService;

  late final FakeAuthRepository authRepository;
  late final FakeFeedRepository feedRepository;
  late final FakeNotificationRepository notificationRepository;
  late final FakeTeacherRepository teacherRepository;
  late final FakeAttendanceRepository attendanceRepository;

  final User parentUser = const User(
    id: 'parent-1',
    email: 'parent@ecole.test',
    fullName: 'Parent Example',
    role: 'PAR',
    schoolId: _schoolId,
    permissions: ['feed:read', 'notifications:read'],
    memberships: [
      Membership(
        schoolId: _schoolId,
        role: 'PAR',
        status: 'active',
      ),
    ],
  );

  final User teacherUser = const User(
    id: 'teacher-1',
    email: 'teacher@ecole.test',
    fullName: 'Teacher Example',
    role: 'TCH',
    schoolId: _schoolId,
    permissions: ['attendance:write', 'attendance:read'],
    memberships: [
      Membership(
        schoolId: _schoolId,
        role: 'TCH',
        status: 'active',
      ),
    ],
  );

  final ClassInfo classInfo = const ClassInfo(
    id: 'class-1',
    code: '6A',
    name: 'Class 6A',
    studentCount: 1,
    courseCount: 4,
  );

  final StudentInfo studentInfo = const StudentInfo(
    id: 'student-1',
    fullName: 'Student Example',
    email: 'student@ecole.test',
    enrollmentStatus: 'active',
  );

  final Period period = const Period(
    id: 'period-1',
    name: 'Morning',
  );

  User? currentUser;

  final List<FeedItem> feedItems = [
    FeedItem(
      id: 'feed-1',
      schoolId: _schoolId,
      parentId: 'parent-1',
      studentId: 'student-1',
      sourceType: 'announcement',
      sourceRef: 'news-1',
      title: 'Weekly digest',
      body: 'New attendance and classroom updates are available.',
      createdAt: '2026-04-11T08:00:00Z',
    ),
  ];

  final List<NotificationItem> notifications = [
    const NotificationItem(
      id: 'notification-1',
      schoolId: _schoolId,
      userId: 'parent-1',
      title: 'Attendance update',
      body: 'Student Example has a new attendance event.',
      category: 'attendance',
      priority: 'normal',
      actionUrl: '/attendance/history?classId=class-1&studentId=student-1',
      createdAt: '2026-04-11T08:30:00Z',
      channels: ['in_app'],
    ),
  ];

  final Map<String, List<AttendanceEntry>> attendanceHistory = {
    'student-1': <AttendanceEntry>[],
  };

  Map<String, dynamic> profileFor(User user) {
    return switch (user.role) {
      'PAR' => {
          'parent_profile': {
            'relationship_type': 'father',
            'cin_number': 'AB123456',
            'emergency_phone': '+212600000000',
          },
        },
      'TCH' => {
          'teacher_profile': {
            'subject_specialty': 'Mathematics',
            'qualification': 'M.Ed',
          },
        },
      _ => <String, dynamic>{},
    };
  }

  List<Override> overrides() {
    return [
      secureStorageProvider.overrideWithValue(storage),
      cacheStoreProvider.overrideWithValue(cacheStore),
      offlineQueueProvider.overrideWithValue(offlineQueue),
      biometricServiceProvider.overrideWithValue(biometricService),
      authRepositoryProvider.overrideWithValue(authRepository),
      feedRepositoryProvider.overrideWithValue(feedRepository),
      notificationRepositoryProvider.overrideWithValue(notificationRepository),
      teacherRepositoryProvider.overrideWithValue(teacherRepository),
      attendanceRepositoryProvider.overrideWithValue(attendanceRepository),
    ];
  }
}

class InMemorySecureTokenStorage extends SecureTokenStorage {
  String? _refreshToken;
  String? _csrfToken;
  String? _themeMode;
  String? _localeCode;

  @override
  Future<void> saveRefreshToken(String token) async {
    _refreshToken = token;
  }

  @override
  Future<String?> getRefreshToken() async {
    return _refreshToken;
  }

  @override
  Future<void> saveCsrfToken(String token) async {
    _csrfToken = token;
  }

  @override
  Future<String?> getCsrfToken() async {
    return _csrfToken;
  }

  @override
  Future<void> clearAll() async {
    _refreshToken = null;
    _csrfToken = null;
  }

  @override
  Future<void> saveThemeMode(String mode) async {
    _themeMode = mode;
  }

  @override
  Future<String?> getThemeMode() async {
    return _themeMode;
  }

  @override
  Future<void> saveLocaleCode(String localeCode) async {
    _localeCode = localeCode;
  }

  @override
  Future<String?> getLocaleCode() async {
    return _localeCode;
  }
}

class InMemoryCacheStore extends CacheStore {
  final Map<String, List<Map<String, dynamic>>> _entries = {};

  @override
  Future<List<Map<String, dynamic>>?> get(String key) async {
    return _entries[key];
  }

  @override
  Future<void> put(
    String key,
    List<Map<String, dynamic>> data,
    int ttlSeconds,
  ) async {
    _entries[key] = data;
  }

  @override
  Future<void> invalidate(String key) async {
    _entries.remove(key);
  }

  @override
  Future<void> invalidatePrefix(String prefix) async {
    _entries.removeWhere((key, _) => key.startsWith(prefix));
  }

  @override
  Future<void> clearAll() async {
    _entries.clear();
  }

  @override
  Future<void> pruneExpired() async {}
}

class InMemoryOfflineQueue extends OfflineQueue {
  @override
  Future<List<QueuedCommand>> getPending() async {
    return const [];
  }

  @override
  Future<int> pendingCount() async {
    return 0;
  }

  @override
  Future<int> failedCount() async {
    return 0;
  }

  @override
  Future<void> clearAll() async {}
}

class FakeBiometricService extends BiometricService {
  bool _enabled = false;

  @override
  Future<bool> isAvailable() async {
    return false;
  }

  @override
  Future<bool> isEnabled() async {
    return _enabled;
  }

  @override
  Future<void> setEnabled(bool enabled) async {
    _enabled = enabled;
  }

  @override
  Future<bool> authenticate(
      {String reason = 'Veuillez vous authentifier'}) async {
    return false;
  }

  @override
  Future<void> clear() async {
    _enabled = false;
  }
}

class FakeAuthRepository implements AuthRepository {
  FakeAuthRepository(this.environment);

  final FakeAppEnvironment environment;

  @override
  Future<LoginResult> login(
    String email,
    String password,
    String schoolId, {
    String? deviceName,
    String? userAgent,
  }) async {
    environment.currentUser = switch (email) {
      'teacher@ecole.test' => environment.teacherUser,
      _ => environment.parentUser,
    };
    await environment.storage
        .saveRefreshToken('refresh-${environment.currentUser!.id}');
    return const LoginResult(accessToken: 'access-token');
  }

  @override
  Future<void> logout() async {
    environment.currentUser = null;
    await environment.storage.clearAll();
  }

  @override
  Future<User> getMe() async {
    final user = environment.currentUser;
    if (user == null) {
      throw StateError('No authenticated user');
    }
    return user;
  }

  @override
  Future<Map<String, dynamic>> getProfile() async {
    return environment.profileFor(await getMe());
  }

  @override
  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final current = Map<String, dynamic>.from(await getProfile());
    current.addAll(data);
    return current;
  }

  @override
  Future<String> verify2fa(String tempToken, String code) async {
    return 'access-token';
  }

  @override
  Future<String?> refreshToken() async {
    return 'access-token';
  }

  @override
  Future<void> requestRecovery(String email) async {}

  @override
  Future<bool> verifyRecovery(String token, String code) async {
    return true;
  }

  @override
  Future<void> resetPassword(String token, String newPassword) async {}

  @override
  Future<TwoFactorSetupData> setup2fa() async {
    return const TwoFactorSetupData(
      provisioningUri: 'otpauth://totp/ecole',
      secret: 'SECRET',
    );
  }

  @override
  Future<TwoFactorVerifyResult> verifySetup2fa(String code) async {
    return const TwoFactorVerifyResult(
      backupCodes: ['code-1'],
      message: 'ok',
    );
  }

  @override
  Future<void> disable2fa(String code) async {}

  @override
  Future<void> changePassword(
      String currentPassword, String newPassword) async {}

  @override
  Future<List<ChildLink>> getChildren() async {
    return const [];
  }

  @override
  Future<RegisterResult> register({
    required String code,
    required String email,
    required String fullName,
    String? phone,
    required String password,
    Map<String, String> profileData = const {},
  }) async {
    return const RegisterResult(
      accessToken: 'access-token',
      userId: 'user-1',
      schoolId: _schoolId,
      role: 'PAR',
      emailVerificationRequired: false,
    );
  }

  @override
  Future<void> verifyEmail({
    required String userId,
    required String schoolId,
    required String otp,
  }) async {}
}

class FakeFeedRepository implements FeedRepository {
  FakeFeedRepository(this.environment);

  final FakeAppEnvironment environment;

  @override
  Future<PaginatedList<FeedItem>> getFeed({String? cursor}) async {
    return PaginatedList<FeedItem>(
      items: environment.feedItems,
      hasMore: false,
    );
  }
}

class FakeNotificationRepository implements NotificationRepository {
  FakeNotificationRepository(this.environment);

  final FakeAppEnvironment environment;

  @override
  Future<PaginatedList<NotificationItem>> getNotifications({
    String? cursor,
    String? category,
    bool? read,
  }) async {
    final currentUser = environment.currentUser ?? environment.parentUser;
    final items = environment.notifications.where((item) {
      final matchesUser = item.userId == currentUser.id;
      final matchesCategory =
          category == null || category.isEmpty || item.category == category;
      final matchesRead = read == null || item.isRead == read;
      return matchesUser && matchesCategory && matchesRead;
    }).toList();
    return PaginatedList<NotificationItem>(
      items: items,
      hasMore: false,
    );
  }

  @override
  Future<void> markRead(String notificationId, {required bool read}) async {
    final index = environment.notifications.indexWhere(
      (item) => item.id == notificationId,
    );
    if (index >= 0) {
      environment.notifications[index] =
          environment.notifications[index].copyWith(
        isRead: read,
        readAt: read ? DateTime.now().toIso8601String() : null,
      );
    }
  }

  @override
  Future<void> deleteNotification(String notificationId) async {
    environment.notifications.removeWhere((item) => item.id == notificationId);
  }

  @override
  Future<int> getUnreadCount() async {
    final currentUser = environment.currentUser ?? environment.parentUser;
    return environment.notifications
        .where((item) => item.userId == currentUser.id && !item.isRead)
        .length;
  }

  @override
  Future<List<NotificationPreferenceItem>> getPreferences() async {
    return const [];
  }

  @override
  Future<void> updatePreferences(
    List<NotificationPreferenceItem> preferences,
  ) async {}

  @override
  Future<String> getDigestFrequency() async {
    return 'daily';
  }

  @override
  Future<void> updateDigestFrequency(String digestFrequency) async {}

  @override
  Future<List<RegisteredDevice>> getDevices() async {
    return const [];
  }

  @override
  Future<void> removeDevice(String deviceId) async {}
}

class FakeTeacherRepository implements TeacherRepository {
  FakeTeacherRepository(this.environment);

  final FakeAppEnvironment environment;

  @override
  Future<List<ClassInfo>> getClasses() async {
    return [environment.classInfo];
  }

  @override
  Future<List<StudentInfo>> getClassStudents(String classId) async {
    return [environment.studentInfo];
  }

  @override
  Future<List<Period>> getPeriods() async {
    return [environment.period];
  }

  @override
  Future<void> createAttendanceSession({
    required String classId,
    required String periodId,
    required String sessionDate,
    required String slot,
    required List<AttendanceRecord> records,
  }) async {
    for (final record in records) {
      final student = environment.studentInfo;
      final entries = environment.attendanceHistory.putIfAbsent(
        record.studentId,
        () => <AttendanceEntry>[],
      );
      entries.insert(
        0,
        AttendanceEntry(
          id: 'attendance-${entries.length + 1}',
          studentId: record.studentId,
          studentName: student.fullName,
          classId: classId,
          date: sessionDate,
          status: record.status,
          slot: slot,
          absenceReason: record.absenceReason,
        ),
      );
    }
  }

  @override
  Future<List<Course>> getCourses({String? classId}) async {
    throw UnimplementedError();
  }

  @override
  Future<Course> createCourse({
    required String classId,
    required String title,
    String? description,
    String status = 'draft',
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<PaginatedList<Assignment>> getAssignments({
    String? cursor,
    String? courseId,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<Assignment> createAssignment({
    required String courseId,
    required String title,
    String? description,
    String? dueAt,
    int totalPoints = 20,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<PaginatedList<Submission>> getSubmissions({
    String? cursor,
    String? status,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<void> gradeSubmission(
    String submissionId, {
    required double score,
    String? feedbackText,
    bool publish = true,
  }) async {
    throw UnimplementedError();
  }
}

class FakeAttendanceRepository implements AttendanceRepository {
  FakeAttendanceRepository(this.environment);

  final FakeAppEnvironment environment;

  @override
  Future<List<AttendanceEntry>> getStudentHistory(String studentId) async {
    return environment.attendanceHistory[studentId] ?? const [];
  }

  @override
  Future<List<AttendanceEntry>> getClassAttendance(
    String classId, {
    required String date,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<void> markAttendance({
    required String classId,
    required String date,
    required List<AttendanceBulkRecord> records,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<AttendanceJustification> submitJustification({
    required String recordId,
    required String reason,
    String? attachmentName,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<List<AttendanceTrendPoint>> getAttendanceTrends(
    String classId, {
    required String from,
    required String to,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<List<AttendanceAlertItem>> getAttendanceAlerts({
    required String schoolId,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<AttendanceClassStats> getClassStats(
    String classId, {
    bool export = false,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<AttendanceExportResult> exportAttendance(
    String classId, {
    required String format,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<AttendanceJustification> reviewJustification({
    required String justificationId,
    required String status,
    String? reviewComment,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<List<AttendanceThresholdResult>> checkThresholds() async {
    throw UnimplementedError();
  }
}

const _schoolId = '00000000-0000-4000-8000-000000000001';
