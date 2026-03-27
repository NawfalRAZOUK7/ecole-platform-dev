/// Messaging entities — conversation, message, read receipt.
///
/// Maps to GET /messages/conversations and /messages/conversations/{id}/messages.

class Conversation {
  final String id;
  final String schoolId;
  final String type;
  final String createdBy;
  final String? subject;
  final List<Participant> participants;
  final String? lastMessageAt;
  final String createdAt;

  const Conversation({
    required this.id,
    required this.schoolId,
    required this.type,
    required this.createdBy,
    this.subject,
    required this.participants,
    this.lastMessageAt,
    required this.createdAt,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id'] as String,
      schoolId: json['school_id'] as String,
      type: json['type'] as String,
      createdBy: json['created_by'] as String,
      subject: json['subject'] as String?,
      participants: (json['participants'] as List<dynamic>?)
              ?.map((p) => Participant.fromJson(p as Map<String, dynamic>))
              .toList() ??
          [],
      lastMessageAt: json['last_message_at'] as String?,
      createdAt: json['created_at'] as String,
    );
  }
}

class Participant {
  final String userId;
  final String roleInConversation;
  final String joinedAt;
  final bool muted;

  const Participant({
    required this.userId,
    required this.roleInConversation,
    required this.joinedAt,
    required this.muted,
  });

  factory Participant.fromJson(Map<String, dynamic> json) {
    return Participant(
      userId: json['user_id'] as String,
      roleInConversation: json['role_in_conversation'] as String,
      joinedAt: json['joined_at'] as String,
      muted: json['muted'] as bool? ?? false,
    );
  }
}

class Message {
  final String id;
  final String conversationId;
  final String senderId;
  final String body;
  final String sentAt;
  final String? editedAt;

  const Message({
    required this.id,
    required this.conversationId,
    required this.senderId,
    required this.body,
    required this.sentAt,
    this.editedAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as String,
      conversationId: json['conversation_id'] as String,
      senderId: json['sender_id'] as String,
      body: json['body'] as String,
      sentAt: json['sent_at'] as String,
      editedAt: json['edited_at'] as String?,
    );
  }
}

class Announcement {
  final String id;
  final String schoolId;
  final String authorId;
  final String title;
  final String body;
  final List<String> targetRoles;
  final String? publishedAt;
  final String status;
  final String createdAt;

  const Announcement({
    required this.id,
    required this.schoolId,
    required this.authorId,
    required this.title,
    required this.body,
    required this.targetRoles,
    this.publishedAt,
    required this.status,
    required this.createdAt,
  });

  factory Announcement.fromJson(Map<String, dynamic> json) {
    return Announcement(
      id: json['id'] as String,
      schoolId: json['school_id'] as String,
      authorId: json['author_id'] as String,
      title: json['title'] as String,
      body: json['body'] as String,
      targetRoles: (json['target_roles'] as List<dynamic>?)
              ?.map((r) => r as String)
              .toList() ??
          [],
      publishedAt: json['published_at'] as String?,
      status: json['status'] as String,
      createdAt: json['created_at'] as String,
    );
  }
}
