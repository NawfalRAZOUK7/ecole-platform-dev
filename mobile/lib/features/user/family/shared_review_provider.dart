/// Riverpod provider for shared review — parent views child's learning sessions.
///
/// Phase B1: Mirrors web sharedReview.service.ts.
/// API: GET/POST /api/v1/shared-reviews/{childId}/sessions[/{sessionId}]

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';

// ── Models ──

class ReviewSession {
  final String id;
  final String type;
  final String title;
  final double? score;
  final int? maxScore;
  final String status;
  final String? startedAt;
  final String? completedAt;

  const ReviewSession({
    required this.id,
    required this.type,
    required this.title,
    this.score,
    this.maxScore,
    required this.status,
    this.startedAt,
    this.completedAt,
  });

  factory ReviewSession.fromJson(Map<String, dynamic> json) {
    return ReviewSession(
      id: json['id'] as String? ?? '',
      type: json['type'] as String? ?? 'unknown',
      title: json['title'] as String? ?? '',
      score: (json['score'] as num?)?.toDouble(),
      maxScore: json['max_score'] as int?,
      status: json['status'] as String? ?? '',
      startedAt: json['started_at'] as String?,
      completedAt: json['completed_at'] as String?,
    );
  }
}

class ReviewComment {
  final String id;
  final String authorId;
  final String text;
  final String? emoji;
  final String createdAt;

  const ReviewComment({
    required this.id,
    required this.authorId,
    required this.text,
    this.emoji,
    required this.createdAt,
  });

  factory ReviewComment.fromJson(Map<String, dynamic> json) {
    return ReviewComment(
      id: json['id'] as String? ?? '',
      authorId: json['author_id'] as String? ?? '',
      text: json['text'] as String? ?? '',
      emoji: json['emoji'] as String?,
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class SessionDetail {
  final String id;
  final String type;
  final String title;
  final double? score;
  final int? maxScore;
  final String status;
  final String? startedAt;
  final String? text;
  final String? suggestion;
  final List<ReviewComment> comments;

  const SessionDetail({
    required this.id,
    required this.type,
    required this.title,
    this.score,
    this.maxScore,
    required this.status,
    this.startedAt,
    this.text,
    this.suggestion,
    required this.comments,
  });

  factory SessionDetail.fromJson(Map<String, dynamic> json) {
    return SessionDetail(
      id: json['id'] as String? ?? '',
      type: json['type'] as String? ?? 'unknown',
      title: json['title'] as String? ?? '',
      score: (json['score'] as num?)?.toDouble(),
      maxScore: json['max_score'] as int?,
      status: json['status'] as String? ?? '',
      startedAt: json['started_at'] as String?,
      text: json['text'] as String?,
      suggestion: json['suggestion'] as String?,
      comments: (json['comments'] as List<dynamic>?)
              ?.map(
                (e) => ReviewComment.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          [],
    );
  }
}

// ── State ──

class SharedReviewState {
  final bool isLoading;
  final String? error;
  final List<ReviewSession> sessions;
  final SessionDetail? detail;
  final bool isPosting;

  const SharedReviewState({
    this.isLoading = false,
    this.error,
    this.sessions = const [],
    this.detail,
    this.isPosting = false,
  });

  SharedReviewState copyWith({
    bool? isLoading,
    String? error,
    List<ReviewSession>? sessions,
    SessionDetail? detail,
    bool? isPosting,
    bool clearError = false,
    bool clearDetail = false,
  }) {
    return SharedReviewState(
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      sessions: sessions ?? this.sessions,
      detail: clearDetail ? null : (detail ?? this.detail),
      isPosting: isPosting ?? this.isPosting,
    );
  }
}

// ── Notifier ──

class SharedReviewNotifier extends StateNotifier<SharedReviewState> {
  SharedReviewNotifier(this._ref) : super(const SharedReviewState());

  final Ref _ref;

  Future<void> loadSessions(String childId) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.get('/shared-reviews/$childId/sessions');
      final sessions = (resp.data['sessions'] as List<dynamic>?)
              ?.map(
                (e) => ReviewSession.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          [];
      state = state.copyWith(isLoading: false, sessions: sessions);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadDetail(String childId, String sessionId) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.get(
        '/shared-reviews/$childId/sessions/$sessionId',
      );
      state = state.copyWith(
        isLoading: false,
        detail: SessionDetail.fromJson(resp.data),
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> addComment(
    String childId,
    String sessionId, {
    required String text,
    String? emoji,
  }) async {
    state = state.copyWith(isPosting: true, clearError: true);
    try {
      final api = _ref.read(apiClientProvider);
      await api.post(
        '/shared-reviews/$childId/sessions/$sessionId/comments',
        body: {'text': text, if (emoji != null) 'emoji': emoji},
      );
      // Reload detail to get updated comments
      await loadDetail(childId, sessionId);
      state = state.copyWith(isPosting: false);
    } catch (e) {
      state = state.copyWith(isPosting: false, error: e.toString());
    }
  }

  void clearDetail() {
    state = state.copyWith(clearDetail: true);
  }
}

// ── Provider ──

final sharedReviewProvider =
    StateNotifierProvider<SharedReviewNotifier, SharedReviewState>((ref) {
  return SharedReviewNotifier(ref);
});
