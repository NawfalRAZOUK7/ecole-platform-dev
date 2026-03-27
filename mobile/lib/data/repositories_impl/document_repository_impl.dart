import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/documents_store.dart';
import 'package:ecole_platform/domain/entities/document_management.dart';
import 'package:ecole_platform/domain/repositories/document_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

const _defaultDocumentCategories = <String>[
  'certificate',
  'report_card',
  'medical',
  'identity',
  'transcript',
  'other',
];

class DocumentRepositoryImpl implements DocumentRepository {
  final ApiClient _api;
  final DocumentsStore _documentsStore;

  DocumentRepositoryImpl({
    required ApiClient api,
    required DocumentsStore documentsStore,
  })  : _api = api,
        _documentsStore = documentsStore;

  @override
  Future<DocumentOptions> getDocumentOptions() async {
    try {
      final response = await _api.get('/documents/options');
      final payload = response.data;
      return DocumentOptions(
        students: (payload['students'] as List<dynamic>? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(documentOptionStudentFromJson)
            .toList(),
        categories: (payload['categories'] as List<dynamic>? ?? const [])
            .map((item) => item.toString())
            .toList(),
      );
    } on ApiClientError {
      return const DocumentOptions(categories: _defaultDocumentCategories);
    }
  }

  @override
  Future<List<ManagedDocument>> getMyDocuments() async {
    const scopeKey = 'documents:mine';
    try {
      final response = await _api.list(
        '/documents',
        params: {
          'owner': 'me',
          'limit': 100,
        },
      );
      await _documentsStore.replaceDocuments(scopeKey, response.data);
      return response.data.map(managedDocumentFromJson).toList();
    } on ApiClientError {
      final cached = await _documentsStore.readDocuments(scopeKey);
      return cached.map(managedDocumentFromJson).toList();
    }
  }

  @override
  Future<List<ManagedDocument>> getStudentDocuments(String studentId) async {
    final scopeKey = 'documents:student:$studentId';
    try {
      final response = await _api.list('/students/$studentId/documents');
      await _documentsStore.replaceDocuments(scopeKey, response.data);
      return response.data.map(managedDocumentFromJson).toList();
    } on ApiClientError {
      final cached = await _documentsStore.readDocuments(scopeKey);
      return cached.map(managedDocumentFromJson).toList();
    }
  }

  @override
  Future<List<StudentDocumentChecklistItem>> getStudentChecklist(
    String studentId,
  ) async {
    try {
      final response =
          await _api.list('/students/$studentId/documents/checklist');
      await _documentsStore.replaceChecklist(studentId, response.data);
      return response.data.map(studentChecklistItemFromJson).toList();
    } on ApiClientError {
      final cached = await _documentsStore.readChecklist(studentId);
      return cached.map(studentChecklistItemFromJson).toList();
    }
  }

  @override
  Future<ManagedDocument> uploadDocument({
    required File file,
    required String category,
    String? linkedStudentId,
    String? expiresAt,
    void Function(int sent, int total)? onProgress,
  }) async {
    final response = await _api.uploadFile(
      '/documents/upload',
      file: file,
      fields: {
        'category': category,
        if (linkedStudentId != null && linkedStudentId.isNotEmpty)
          'linked_student_id': linkedStudentId,
        if (expiresAt != null && expiresAt.isNotEmpty) 'expires_at': expiresAt,
      },
      onProgress: onProgress,
    );
    return managedDocumentFromJson(response.data);
  }

  @override
  Future<void> deleteDocument(
    String documentId, {
    bool hardDelete = false,
  }) async {
    await _api.delete(
      hardDelete
          ? '/documents/$documentId?hard=true'
          : '/documents/$documentId',
    );
  }

  @override
  Future<PaginatedList<ResourceLibraryItem>> getResources({
    String? cursor,
    String? query,
    String? subject,
    String? level,
    String? type,
    double? minRating,
  }) async {
    final scopeKey = _resourceScopeKey(
      query: query,
      subject: subject,
      level: level,
      type: type,
      minRating: minRating,
    );
    try {
      final response = await _api.list(
        '/resources',
        params: {
          if (cursor != null && cursor.isNotEmpty) 'cursor': cursor,
          if (query != null && query.isNotEmpty) 'q': query,
          if (subject != null && subject.isNotEmpty) 'subject': subject,
          if (level != null && level.isNotEmpty) 'level': level,
          if (type != null && type.isNotEmpty) 'type': type,
          if (minRating != null) 'rating': minRating,
          'limit': 24,
        },
      );
      if (cursor == null || cursor.isEmpty) {
        await _documentsStore.replaceResources(scopeKey, response.data);
      }
      return PaginatedList(
        items: response.data.map(resourceLibraryItemFromJson).toList(),
        nextCursor: response.nextCursor,
        hasMore: response.hasMore,
      );
    } on ApiClientError {
      if (cursor != null && cursor.isNotEmpty) rethrow;
      final cached = await _documentsStore.readResources(scopeKey);
      return PaginatedList(
        items: cached.map(resourceLibraryItemFromJson).toList(),
        hasMore: false,
      );
    }
  }

  @override
  Future<ResourceLibraryItem> uploadResource({
    required File file,
    required String title,
    String? description,
    String? subject,
    String? level,
    required String type,
    List<String> tags = const [],
    String visibility = 'school',
    String? classId,
    void Function(int sent, int total)? onProgress,
  }) async {
    final response = await _api.uploadFile(
      '/resources',
      file: file,
      fields: {
        'title': title,
        if (description != null && description.isNotEmpty)
          'description': description,
        if (subject != null && subject.isNotEmpty) 'subject': subject,
        if (level != null && level.isNotEmpty) 'level': level,
        'type': type,
        'visibility': visibility,
        if (classId != null && classId.isNotEmpty) 'class_id': classId,
        if (tags.isNotEmpty) 'tags': tags.join(','),
      },
      onProgress: onProgress,
    );
    return resourceLibraryItemFromJson(response.data);
  }

  @override
  Future<void> deleteResource(String resourceId) async {
    await _api.delete('/resources/$resourceId');
  }

  @override
  Future<ResourceRatingSummary> rateResource(
      String resourceId, int rating) async {
    final response = await _api.post(
      '/resources/$resourceId/rate',
      body: {'rating': rating},
    );
    return resourceRatingSummaryFromJson(response.data);
  }

  @override
  Future<File> downloadDocumentFile(ManagedDocument document) async {
    if (document.availableOffline) {
      final cachedFile = File(document.localFilePath!);
      if (await cachedFile.exists()) {
        return cachedFile;
      }
    }

    if (document.downloadUrl == null || document.downloadUrl!.isEmpty) {
      throw const FileSystemException('Missing document download URL');
    }

    final directory = await getApplicationDocumentsDirectory();
    final documentsDir = Directory(
      '${directory.path}${Platform.pathSeparator}documents',
    );
    if (!await documentsDir.exists()) {
      await documentsDir.create(recursive: true);
    }

    final savePath =
        '${documentsDir.path}${Platform.pathSeparator}${document.id}${_fileExtension(document.originalFilename)}';
    final file = await _api.download(
      _normalizeDownloadPath(document.downloadUrl!),
      savePath: savePath,
    );
    await _documentsStore.attachDocumentFile(document.id, file.path);
    return file;
  }

  @override
  Future<File> downloadResourceFile(ResourceLibraryItem resource) async {
    if (resource.availableOffline) {
      final cachedFile = File(resource.localFilePath!);
      if (await cachedFile.exists()) {
        return cachedFile;
      }
    }

    if (resource.downloadUrl == null || resource.downloadUrl!.isEmpty) {
      throw const FileSystemException('Missing resource download URL');
    }

    final directory = await getApplicationDocumentsDirectory();
    final resourcesDir = Directory(
      '${directory.path}${Platform.pathSeparator}resources',
    );
    if (!await resourcesDir.exists()) {
      await resourcesDir.create(recursive: true);
    }

    final originalName = resource.document?.originalFilename.isNotEmpty == true
        ? resource.document!.originalFilename
        : resource.title;
    final savePath =
        '${resourcesDir.path}${Platform.pathSeparator}${resource.id}${_fileExtension(originalName)}';
    final file = await _api.download(
      _normalizeDownloadPath(resource.downloadUrl!),
      savePath: savePath,
    );
    await _documentsStore.attachResourceFile(resource.id, file.path);
    return file;
  }

  String _resourceScopeKey({
    String? query,
    String? subject,
    String? level,
    String? type,
    double? minRating,
  }) {
    return [
      'resources',
      query ?? '',
      subject ?? '',
      level ?? '',
      type ?? '',
      minRating?.toString() ?? '',
    ].join('|');
  }

  String _normalizeDownloadPath(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    if (path.startsWith('/api/v1/')) {
      return path.substring('/api/v1'.length);
    }
    return path;
  }

  String _fileExtension(String fileName) {
    final index = fileName.lastIndexOf('.');
    if (index <= 0 || index == fileName.length - 1) {
      return '';
    }
    return fileName.substring(index);
  }
}
