import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content/content_item.dart';

String _normalizeProgressStatus(String? value) {
  switch (value?.trim().toLowerCase()) {
    case 'completed':
      return 'completed';
    case 'started':
    case 'in_progress':
      return 'in_progress';
    default:
      return 'not_started';
  }
}

@immutable
class StoryReaderRequest {
  final String contentItemId;
  final String? initialProgressStatus;

  const StoryReaderRequest({
    required this.contentItemId,
    this.initialProgressStatus,
  });

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        other is StoryReaderRequest &&
            runtimeType == other.runtimeType &&
            contentItemId == other.contentItemId &&
            initialProgressStatus == other.initialProgressStatus;
  }

  @override
  int get hashCode => Object.hash(contentItemId, initialProgressStatus);
}

@immutable
class StoryReaderState {
  final ContentItem contentItem;
  final List<ContentItemAsset> pages;
  final int currentPageIndex;
  final bool isDrawingMode;
  final bool isAudioPlaying;
  final String progressStatus;

  const StoryReaderState({
    required this.contentItem,
    required this.pages,
    this.currentPageIndex = 0,
    this.isDrawingMode = false,
    this.isAudioPlaying = false,
    this.progressStatus = 'not_started',
  });

  StoryReaderState copyWith({
    ContentItem? contentItem,
    List<ContentItemAsset>? pages,
    int? currentPageIndex,
    bool? isDrawingMode,
    bool? isAudioPlaying,
    String? progressStatus,
  }) {
    return StoryReaderState(
      contentItem: contentItem ?? this.contentItem,
      pages: pages ?? this.pages,
      currentPageIndex: currentPageIndex ?? this.currentPageIndex,
      isDrawingMode: isDrawingMode ?? this.isDrawingMode,
      isAudioPlaying: isAudioPlaying ?? this.isAudioPlaying,
      progressStatus: progressStatus ?? this.progressStatus,
    );
  }

  ContentItemAsset? get currentPage =>
      pages.isEmpty ? null : pages[currentPageIndex];

  int get totalPages => pages.length;

  bool get isLastPage =>
      pages.isNotEmpty && currentPageIndex == pages.length - 1;

  bool get isCompleted => progressStatus == 'completed';

  bool get hasAssociatedQuiz => pages.any((page) => page.hasActivity);

  double get progress {
    if (pages.isEmpty) {
      return 0;
    }
    return ((currentPageIndex + 1) / pages.length).clamp(0.0, 1.0).toDouble();
  }
}

class StoryReaderNotifier
    extends FamilyAsyncNotifier<StoryReaderState, StoryReaderRequest> {
  @override
  Future<StoryReaderState> build(StoryReaderRequest arg) async {
    final repo = ref.read(contentRepositoryProvider);
    final contentItem = await repo.getContentItem(arg.contentItemId);
    final pages = await repo.getStoryPages(arg.contentItemId);
    final sortedPages = List<ContentItemAsset>.of(pages)
      ..sort(
        (left, right) =>
            (left.pageNumber ?? 0).compareTo(right.pageNumber ?? 0),
      );

    return StoryReaderState(
      contentItem: contentItem,
      pages: sortedPages,
      progressStatus: _normalizeProgressStatus(arg.initialProgressStatus),
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => build(arg));
  }

  Future<void> setCurrentPageIndex(int index) async {
    final current = state.valueOrNull;
    if (current == null || index < 0 || index >= current.pages.length) {
      return;
    }

    final nextStatus = current.isCompleted
        ? current.progressStatus
        : index > 0
            ? 'in_progress'
            : current.progressStatus;
    state = AsyncData(
      current.copyWith(
        currentPageIndex: index,
        progressStatus: nextStatus,
      ),
    );
    await _persistProgress(
      currentStatus: current.progressStatus,
      nextStatus: nextStatus,
    );
  }

  Future<void> completeStory() async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final completedState = current.copyWith(progressStatus: 'completed');
    state = AsyncData(completedState);
    await _persistProgress(
      currentStatus: current.progressStatus,
      nextStatus: completedState.progressStatus,
    );
  }

  void toggleDrawingMode() {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    state = AsyncData(
      current.copyWith(isDrawingMode: !current.isDrawingMode),
    );
  }

  void setAudioPlaying(bool isPlaying) {
    final current = state.valueOrNull;
    if (current == null || current.isAudioPlaying == isPlaying) {
      return;
    }

    state = AsyncData(current.copyWith(isAudioPlaying: isPlaying));
  }

  Future<void> _persistProgress({
    required String currentStatus,
    required String nextStatus,
  }) async {
    if (currentStatus == nextStatus || nextStatus == 'not_started') {
      return;
    }
    if (currentStatus == 'completed' && nextStatus != 'completed') {
      return;
    }

    try {
      await ref.read(contentRepositoryProvider).updateProgress(
            arg.contentItemId,
            nextStatus,
          );
    } catch (_) {
      // Progress failures should not block the reader UI.
    }
  }
}

final storyReaderProvider = AsyncNotifierProvider.family<StoryReaderNotifier,
    StoryReaderState, StoryReaderRequest>(
  StoryReaderNotifier.new,
);
