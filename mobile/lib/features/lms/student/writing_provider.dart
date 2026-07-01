/// Riverpod provider for the writing workspace.
///
/// Phase A2: Mirrors web writing.service.ts + useWriting.ts.
/// API: POST /api/v1/writing-attempts

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';

// ── Models ──

class WritingFeedback {
  final String correctedText;
  final List<String> suggestions;
  final int? score;
  final String encouragement;

  const WritingFeedback({
    required this.correctedText,
    required this.suggestions,
    this.score,
    required this.encouragement,
  });

  factory WritingFeedback.fromJson(Map<String, dynamic> json) {
    return WritingFeedback(
      correctedText: json['corrected_text'] as String? ?? '',
      suggestions: (json['suggestions'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      score: json['score'] as int?,
      encouragement: json['encouragement'] as String? ?? '',
    );
  }
}

class WritingAttemptResponse {
  final String id;
  final String text;
  final WritingFeedback feedback;
  final String createdAt;

  const WritingAttemptResponse({
    required this.id,
    required this.text,
    required this.feedback,
    required this.createdAt,
  });

  factory WritingAttemptResponse.fromJson(Map<String, dynamic> json) {
    return WritingAttemptResponse(
      id: json['id'] as String? ?? '',
      text: json['text'] as String? ?? '',
      feedback: WritingFeedback.fromJson(
        json['feedback'] as Map<String, dynamic>? ?? {},
      ),
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

// ── State ──

class WritingState {
  final bool isLoading;
  final String? error;
  final WritingAttemptResponse? result;

  const WritingState({
    this.isLoading = false,
    this.error,
    this.result,
  });

  WritingState copyWith({
    bool? isLoading,
    String? error,
    WritingAttemptResponse? result,
    bool clearError = false,
    bool clearResult = false,
  }) {
    return WritingState(
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      result: clearResult ? null : (result ?? this.result),
    );
  }
}

// ── Notifier ──

class WritingNotifier extends StateNotifier<WritingState> {
  WritingNotifier(this._ref) : super(const WritingState());

  final Ref _ref;

  Future<void> submit({
    required String text,
    String language = 'ar',
    String writingType = 'free',
  }) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.post(
        '/writing-attempts',
        body: {
          'text': text,
          'language': language,
          'writing_type': writingType,
        },
      );
      state = state.copyWith(
        isLoading: false,
        result: WritingAttemptResponse.fromJson(resp.data),
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  void reset() {
    state = const WritingState();
  }
}

// ── Provider ──

final writingProvider =
    StateNotifierProvider<WritingNotifier, WritingState>((ref) {
  return WritingNotifier(ref);
});
