/// Content item entity — content library entry.
///
/// Maps to GET /content-items response (ContentItemResponse schema).
enum ContentType {
  video('video'),
  audio('audio'),
  document('document'),
  interactive('interactive'),
  story('story'),
  coloringBook('coloring_book'),
  unknown('unknown');

  const ContentType(this.apiValue);

  final String apiValue;

  static ContentType fromValue(String rawValue) {
    switch (rawValue.trim().toLowerCase()) {
      case 'video':
        return ContentType.video;
      case 'audio':
        return ContentType.audio;
      case 'document':
      case 'pdf':
      case 'printable_pdf':
        return ContentType.document;
      case 'interactive':
        return ContentType.interactive;
      case 'story':
        return ContentType.story;
      case 'coloring_book':
        return ContentType.coloringBook;
      default:
        return ContentType.unknown;
    }
  }
}

class ContentItem {
  final String id;
  final String? schoolId;
  final String title;
  final String contentType;
  final String? levelBand;
  final String? language;
  final int? pageCount;
  final String? letter;
  final int? targetAgeMin;
  final int? targetAgeMax;
  final String? themeColor;
  final String status;

  const ContentItem({
    required this.id,
    this.schoolId,
    required this.title,
    required this.contentType,
    this.levelBand,
    this.language,
    this.pageCount,
    this.letter,
    this.targetAgeMin,
    this.targetAgeMax,
    this.themeColor,
    required this.status,
  });

  ContentType get type => ContentType.fromValue(contentType);
}

class ContentItemAsset {
  final String id;
  final String contentItemId;
  final String filePath;
  final String downloadUrl;
  final String? checksum;
  final String? mimeType;
  final int? fileSize;
  final int? pageNumber;
  final String? narrationText;
  final bool hasActivity;
  final String? assetType;

  const ContentItemAsset({
    required this.id,
    required this.contentItemId,
    required this.filePath,
    required this.downloadUrl,
    this.checksum,
    this.mimeType,
    this.fileSize,
    this.pageNumber,
    this.narrationText,
    required this.hasActivity,
    this.assetType,
  });
}
