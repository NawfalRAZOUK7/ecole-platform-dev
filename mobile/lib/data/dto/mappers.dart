/// DTO mappers — convert API JSON to domain entities.
///
/// Reference: DEC-E2-001 — Data layer handles API DTOs,
/// presentation layer only sees domain entities.

import 'package:ecole_platform/domain/entities/user.dart';
import 'package:ecole_platform/domain/entities/feed_item.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';
import 'package:ecole_platform/domain/entities/result.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';

// ── User ──

User userFromJson(Map<String, dynamic> json) {
  return User(
    id: json['id'] as String,
    email: json['email'] as String,
    fullName: json['full_name'] as String,
    role: json['role'] as String,
    schoolId: json['school_id'] as String,
    permissions: (json['permissions'] as List<dynamic>).cast<String>(),
    memberships: (json['memberships'] as List<dynamic>)
        .map((m) => membershipFromJson(m as Map<String, dynamic>))
        .toList(),
  );
}

Membership membershipFromJson(Map<String, dynamic> json) {
  return Membership(
    schoolId: json['school_id'] as String,
    role: json['role'] as String,
    status: json['status'] as String,
  );
}

// ── Feed ──

FeedItem feedItemFromJson(Map<String, dynamic> json) {
  return FeedItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String,
    parentId: json['parent_id'] as String,
    studentId: json['student_id'] as String?,
    sourceType: json['source_type'] as String,
    sourceRef: json['source_ref'] as String?,
    title: json['title'] as String,
    body: json['body'] as String?,
    createdAt: json['created_at'] as String,
  );
}

// ── Notification ──

NotificationItem notificationFromJson(Map<String, dynamic> json) {
  return NotificationItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String,
    parentId: json['parent_id'] as String,
    eventRef: json['event_ref'] as String?,
    title: json['title'] as String,
    body: json['body'] as String?,
    createdAt: json['created_at'] as String,
  );
}

// ── Content ──

ContentItem contentItemFromJson(Map<String, dynamic> json) {
  return ContentItem(
    id: json['id'] as String,
    schoolId: json['school_id'] as String?,
    title: json['title'] as String,
    contentType: json['content_type'] as String,
    levelBand: json['level_band'] as String?,
    language: json['language'] as String?,
    status: json['status'] as String,
  );
}

// ── Result ──

Result resultFromJson(Map<String, dynamic> json) {
  return Result(
    assignmentId: json['assignment_id'] as String,
    assignmentTitle: json['assignment_title'] as String,
    courseTitle: json['course_title'] as String,
    submissionId: json['submission_id'] as String?,
    status: json['status'] as String?,
    score: (json['score'] as num?)?.toDouble(),
    feedbackText: json['feedback_text'] as String?,
    totalPoints: json['total_points'] as int,
    dueAt: json['due_at'] as String?,
  );
}

// ── Invoice ──

Invoice invoiceFromJson(Map<String, dynamic> json) {
  return Invoice(
    id: json['id'] as String,
    schoolId: json['school_id'] as String,
    parentId: json['parent_id'] as String,
    periodId: json['period_id'] as String?,
    status: json['status'] as String,
    totalAmount: (json['total_amount'] as num).toDouble(),
    currency: json['currency'] as String,
    issuedDate: json['issued_date'] as String,
    dueDate: json['due_date'] as String,
    items: (json['items'] as List<dynamic>?)
            ?.map((i) => invoiceItemFromJson(i as Map<String, dynamic>))
            .toList() ??
        [],
  );
}

InvoiceItem invoiceItemFromJson(Map<String, dynamic> json) {
  return InvoiceItem(
    id: json['id'] as String,
    description: json['description'] as String,
    amount: (json['amount'] as num).toDouble(),
    unitPrice: (json['unit_price'] as num).toDouble(),
    quantity: json['quantity'] as int,
  );
}
