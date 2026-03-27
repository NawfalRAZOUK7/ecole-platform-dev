import 'dart:io';

import 'package:ecole_platform/domain/entities/document_management.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

abstract class DocumentRepository {
  Future<DocumentOptions> getDocumentOptions();

  Future<List<ManagedDocument>> getMyDocuments();

  Future<List<ManagedDocument>> getStudentDocuments(String studentId);

  Future<List<StudentDocumentChecklistItem>> getStudentChecklist(
    String studentId,
  );

  Future<ManagedDocument> uploadDocument({
    required File file,
    required String category,
    String? linkedStudentId,
    String? expiresAt,
    void Function(int sent, int total)? onProgress,
  });

  Future<void> deleteDocument(
    String documentId, {
    bool hardDelete = false,
  });

  Future<PaginatedList<ResourceLibraryItem>> getResources({
    String? cursor,
    String? query,
    String? subject,
    String? level,
    String? type,
    double? minRating,
  });

  Future<ResourceLibraryItem> uploadResource({
    required File file,
    required String title,
    String? description,
    String? subject,
    String? level,
    required String type,
    List<String> tags,
    String visibility,
    String? classId,
    void Function(int sent, int total)? onProgress,
  });

  Future<void> deleteResource(String resourceId);

  Future<ResourceRatingSummary> rateResource(String resourceId, int rating);

  Future<File> downloadDocumentFile(ManagedDocument document);

  Future<File> downloadResourceFile(ResourceLibraryItem resource);
}
