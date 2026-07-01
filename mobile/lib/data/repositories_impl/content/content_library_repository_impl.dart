/// Content library repository implementation — API calls.
///
/// Phase 10C: Teacher content library + student assigned content.

import 'dart:io';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/core/network/upload_client.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/domain/entities/lms/quiz.dart';
import 'package:ecole_platform/domain/entities/lms/teacher.dart';
import 'package:ecole_platform/domain/repositories/content/content_library_repository.dart';
import 'package:ecole_platform/domain/common/pagination.dart';

LibraryItem _libraryItemFromJson(Map<String, dynamic> json) {
  return LibraryItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String?,
    title: json['title'] as String,
    contentType: json['content_type'] as String,
    levelBand: json['level_band'] as String?,
    language: json['language'] as String?,
    subject: json['subject'] as String?,
    description: json['description'] as String?,
    origin: json['origin'] as String? ?? 'platform',
    status: json['status'] as String? ?? 'active',
  );
}

ContentSubmission _submissionFromJson(Map<String, dynamic> json) {
  return ContentSubmission(
    id: json['id'] as String,
    contentItemId: json['content_item_id'] as String,
    contentTitle: json['content_title'] as String? ?? '',
    status: json['status'] as String,
    submittedAt: json['submitted_at'] as String?,
    reviewNotes: json['review_notes'] as String?,
    promotedContentId: json['promoted_content_id'] as String?,
  );
}

AssignedContent _assignedContentFromJson(Map<String, dynamic> json) {
  return AssignedContent(
    id: json['id'] as String,
    contentItemId: json['content_item_id'] as String? ?? json['id'] as String,
    title: json['title'] as String,
    contentType: json['content_type'] as String,
    subject: json['subject'] as String?,
    description: json['description'] as String?,
    progress: json['progress'] as String?,
    streamUrl: json['stream_url'] as String?,
  );
}

class ContentLibraryRepositoryImpl implements ContentLibraryRepository {
  final ApiClient _api;
  final CacheStore _cache;

  ContentLibraryRepositoryImpl({
    required ApiClient api,
    required CacheStore cache,
  })  : _api = api,
        _cache = cache;

  @override
  Future<PaginatedList<LibraryItem>> browseLibrary({
    String? cursor,
    String? contentType,
    String? level,
    String? subject,
    String? origin,
  }) async {
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (contentType != null) params['content_type'] = contentType;
    if (level != null) params['level_band'] = level;
    if (subject != null) params['subject'] = subject;
    if (origin != null) params['origin'] = origin;

    final resp = await _api.list('/content/library', params: params);
    return PaginatedList(
      items: resp.data.map(_libraryItemFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<void> assignContent({
    required String contentItemId,
    required String classId,
  }) async {
    await _api.post(
      '/content/assign',
      body: {
        'content_item_id': contentItemId,
        'class_id': classId,
      },
    );
  }

  @override
  Future<void> uploadContent({
    required String title,
    required String contentType,
    required String schoolId,
    String? description,
    String? level,
    String? subject,
    String? language,
    required File file,
    void Function(int sent, int total)? onProgress,
  }) async {
    // Map content_type string → UploadKind for routing decision.
    final kind = switch (contentType.toLowerCase()) {
      'video' => UploadKind.video,
      'audio' => UploadKind.audio,
      _ => UploadKind.contentAsset,
    };

    if (shouldUseDirect(file, kind)) {
      // Direct-to-MinIO path for video, audio, or files > 10 MB.
      await directUpload(
        api: _api,
        kind: kind,
        scope: UploadScope(schoolId: schoolId),
        file: file,
        onProgress: onProgress,
      );
      return;
    }

    // Legacy multipart path for small, non-streaming files.
    final fields = <String, dynamic>{
      'title': title,
      'content_type': contentType,
      if (description != null) 'description': description,
      if (level != null) 'level_band': level,
      if (subject != null) 'subject': subject,
      if (language != null) 'language': language,
    };

    await _api.uploadFiles(
      '/content-items/upload',
      files: [file],
      fields: fields,
      onProgress: onProgress,
    );
  }

  @override
  Future<void> submitForReview(String contentItemId) async {
    await _api.post(
      '/content/submit-for-review',
      body: {
        'content_item_id': contentItemId,
      },
    );
  }

  @override
  Future<List<ContentSubmission>> getMySubmissions({String? status}) async {
    final params = <String, dynamic>{};
    if (status != null) params['status'] = status;
    final resp = await _api.list('/content/my-submissions', params: params);
    return resp.data.map(_submissionFromJson).toList();
  }

  @override
  Future<List<AssignedContent>> getClassContent(String classId) async {
    final cacheKey = 'class_content:$classId';
    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return cached.map(_assignedContentFromJson).toList();
    }

    final resp = await _api.list('/classes/$classId/content');
    await _cache.put(cacheKey, resp.data, CacheTtl.contentItems);
    return resp.data.map(_assignedContentFromJson).toList();
  }

  @override
  Future<void> updateProgress(String contentItemId, String progress) async {
    await _api.post(
      '/content-items/$contentItemId/progress',
      body: {
        'status': progress,
      },
    );
  }

  @override
  Future<List<ClassInfo>> getTeacherClasses() async {
    final resp = await _api.list('/teacher/classes');
    return resp.data.map(classInfoFromJson).toList();
  }
}
