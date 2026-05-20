/// ChildLink entity — parent-child family link.
///
/// Maps to GET /me/children response items.
class ChildLink {
  final String userId;
  final String fullName;
  final String? email;
  final String linkId;
  final String? linkedAt;
  final Map<String, dynamic>? studentProfile;

  const ChildLink({
    required this.userId,
    required this.fullName,
    this.email,
    required this.linkId,
    this.linkedAt,
    this.studentProfile,
  });

  String? get classLevel => studentProfile?['class_level'] as String?;
}
