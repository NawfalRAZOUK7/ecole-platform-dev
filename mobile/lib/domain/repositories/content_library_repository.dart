/// Content library repository interface — domain layer contract.
///
/// Phase 10C: Teacher content library + student assigned content.
import 'dart:io';

import '../entities/quiz.dart';
import '../entities/teacher.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class ContentLibraryRepository {
  // ── Teacher: browse platform + school content ──

  /// Browse content library with filters.
  Future<PaginatedList<LibraryItem>> browseLibrary({
    String? cursor,
    String? contentType,
    String? level,
    String? subject,
    String? origin,
  });

  /// Assign a content item to a class.
  Future<void> assignContent({
    required String contentItemId,
    required String classId,
  });

  /// Upload school-scoped content from device.
  Future<void> uploadContent({
    required String title,
    required String contentType,
    String? description,
    String? level,
    String? subject,
    String? language,
    required File file,
    void Function(int sent, int total)? onProgress,
  });

  /// Submit own content for platform review.
  Future<void> submitForReview(String contentItemId);

  /// Get teacher's submissions for review.
  Future<List<ContentSubmission>> getMySubmissions({String? status});

  // ── Student: view assigned content ──

  /// Get content assigned to a class.
  Future<List<AssignedContent>> getClassContent(String classId);

  /// Update progress on a content item.
  Future<void> updateProgress(String contentItemId, String progress);

  // ── Teacher: classes for assignment ──

  /// Get teacher's classes (for assign modal).
  Future<List<ClassInfo>> getTeacherClasses();
}
