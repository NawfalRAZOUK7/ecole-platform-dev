class DocumentOptionStudent {
  final String id;
  final String fullName;
  final String? email;

  const DocumentOptionStudent({
    required this.id,
    required this.fullName,
    this.email,
  });
}

class DocumentOptions {
  final List<DocumentOptionStudent> students;
  final List<String> categories;

  const DocumentOptions({
    this.students = const [],
    this.categories = const [],
  });
}

class ManagedDocument {
  final String id;
  final String originalFilename;
  final String filename;
  final String mimeType;
  final int sizeBytes;
  final String category;
  final String sha256;
  final String? linkedStudentId;
  final String? linkedStudentName;
  final String uploaderId;
  final String? uploaderName;
  final String? expiresAt;
  final bool isExpired;
  final bool isExpiringSoon;
  final int downloadCount;
  final String? thumbnailUrl;
  final String? previewUrl;
  final String? downloadUrl;
  final String createdAt;
  final String? deletedAt;
  final bool deduplicated;
  final bool canDelete;
  final bool canHardDelete;
  final String? localFilePath;

  const ManagedDocument({
    required this.id,
    required this.originalFilename,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    required this.category,
    required this.sha256,
    this.linkedStudentId,
    this.linkedStudentName,
    required this.uploaderId,
    this.uploaderName,
    this.expiresAt,
    this.isExpired = false,
    this.isExpiringSoon = false,
    this.downloadCount = 0,
    this.thumbnailUrl,
    this.previewUrl,
    this.downloadUrl,
    required this.createdAt,
    this.deletedAt,
    this.deduplicated = false,
    this.canDelete = false,
    this.canHardDelete = false,
    this.localFilePath,
  });

  bool get isImage => mimeType.startsWith('image/');
  bool get isPdf => mimeType == 'application/pdf';
  bool get isZip => mimeType == 'application/zip';
  bool get availableOffline =>
      localFilePath != null && localFilePath!.trim().isNotEmpty;

  ManagedDocument copyWith({
    String? localFilePath,
    int? downloadCount,
    bool? deduplicated,
  }) {
    return ManagedDocument(
      id: id,
      originalFilename: originalFilename,
      filename: filename,
      mimeType: mimeType,
      sizeBytes: sizeBytes,
      category: category,
      sha256: sha256,
      linkedStudentId: linkedStudentId,
      linkedStudentName: linkedStudentName,
      uploaderId: uploaderId,
      uploaderName: uploaderName,
      expiresAt: expiresAt,
      isExpired: isExpired,
      isExpiringSoon: isExpiringSoon,
      downloadCount: downloadCount ?? this.downloadCount,
      thumbnailUrl: thumbnailUrl,
      previewUrl: previewUrl,
      downloadUrl: downloadUrl,
      createdAt: createdAt,
      deletedAt: deletedAt,
      deduplicated: deduplicated ?? this.deduplicated,
      canDelete: canDelete,
      canHardDelete: canHardDelete,
      localFilePath: localFilePath ?? this.localFilePath,
    );
  }
}

class StudentDocumentChecklistItem {
  final String category;
  final bool required;
  final String? description;
  final String status;
  final String? expiresAt;
  final ManagedDocument? document;

  const StudentDocumentChecklistItem({
    required this.category,
    required this.required,
    this.description,
    required this.status,
    this.expiresAt,
    this.document,
  });
}

class ResourceLibraryItem {
  final String id;
  final String title;
  final String? description;
  final String? subject;
  final String? level;
  final String type;
  final List<String> tags;
  final String visibility;
  final String? classId;
  final int downloadCount;
  final double avgRating;
  final int ratingCount;
  final String? downloadUrl;
  final String? previewUrl;
  final String? thumbnailUrl;
  final ManagedDocument? document;
  final int? myRating;
  final String createdAt;
  final String? updatedAt;
  final bool canEdit;
  final bool canDelete;
  final bool canRate;
  final String? localFilePath;

  const ResourceLibraryItem({
    required this.id,
    required this.title,
    this.description,
    this.subject,
    this.level,
    required this.type,
    this.tags = const [],
    required this.visibility,
    this.classId,
    this.downloadCount = 0,
    this.avgRating = 0,
    this.ratingCount = 0,
    this.downloadUrl,
    this.previewUrl,
    this.thumbnailUrl,
    this.document,
    this.myRating,
    required this.createdAt,
    this.updatedAt,
    this.canEdit = false,
    this.canDelete = false,
    this.canRate = false,
    this.localFilePath,
  });

  bool get availableOffline =>
      localFilePath != null && localFilePath!.trim().isNotEmpty;

  ResourceLibraryItem copyWith({
    ManagedDocument? document,
    int? myRating,
    double? avgRating,
    int? ratingCount,
    String? localFilePath,
    int? downloadCount,
  }) {
    return ResourceLibraryItem(
      id: id,
      title: title,
      description: description,
      subject: subject,
      level: level,
      type: type,
      tags: tags,
      visibility: visibility,
      classId: classId,
      downloadCount: downloadCount ?? this.downloadCount,
      avgRating: avgRating ?? this.avgRating,
      ratingCount: ratingCount ?? this.ratingCount,
      downloadUrl: downloadUrl,
      previewUrl: previewUrl,
      thumbnailUrl: thumbnailUrl,
      document: document ?? this.document,
      myRating: myRating ?? this.myRating,
      createdAt: createdAt,
      updatedAt: updatedAt,
      canEdit: canEdit,
      canDelete: canDelete,
      canRate: canRate,
      localFilePath: localFilePath ?? this.localFilePath,
    );
  }
}

class ResourceRatingSummary {
  final String resourceId;
  final double avgRating;
  final int ratingCount;
  final int? myRating;

  const ResourceRatingSummary({
    required this.resourceId,
    required this.avgRating,
    required this.ratingCount,
    this.myRating,
  });
}
