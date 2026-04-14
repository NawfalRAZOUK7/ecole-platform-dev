/// Content item entity — content library entry.
///
/// Maps to GET /content-items response (ContentItemResponse schema).
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
}
