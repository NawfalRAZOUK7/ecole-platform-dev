import 'dart:async';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';
import 'package:ecole_platform/features/games/models/game_config.dart';

const List<GameItem> _fallbackVisualItems = <GameItem>[
  GameItem(
    id: 'alif',
    prompt: 'ا',
    answer: 'أرنب',
    ttsText: 'ا',
    category: 'Letters',
    accentHex: '#F97316',
  ),
  GameItem(
    id: 'ba',
    prompt: 'ب',
    answer: 'بطة',
    ttsText: 'ب',
    category: 'Letters',
    accentHex: '#0EA5E9',
  ),
  GameItem(
    id: 'ta',
    prompt: 'ت',
    answer: 'تفاحة',
    ttsText: 'ت',
    category: 'Letters',
    accentHex: '#22C55E',
  ),
  GameItem(
    id: 'tha',
    prompt: 'ث',
    answer: 'ثعلب',
    ttsText: 'ث',
    category: 'Letters',
    accentHex: '#A855F7',
  ),
  GameItem(
    id: 'jim',
    prompt: 'ج',
    answer: 'جمل',
    ttsText: 'ج',
    category: 'Letters',
    accentHex: '#EF4444',
  ),
  GameItem(
    id: 'ha',
    prompt: 'ح',
    answer: 'حصان',
    ttsText: 'ح',
    category: 'Letters',
    accentHex: '#EAB308',
  ),
  GameItem(
    id: 'kitab',
    prompt: 'كتاب',
    answer: 'Livre',
    ttsText: 'كتاب',
    category: 'Words',
    accentHex: '#14B8A6',
  ),
  GameItem(
    id: 'qamar',
    prompt: 'قمر',
    answer: 'Lune',
    ttsText: 'قمر',
    category: 'Words',
    accentHex: '#6366F1',
  ),
];

const List<GameItem> _fallbackSortingItems = <GameItem>[
  GameItem(
    id: 'cat',
    prompt: 'قطة',
    answer: 'قطة',
    ttsText: 'قطة',
    category: 'Animals',
    accentHex: '#F97316',
  ),
  GameItem(
    id: 'bird',
    prompt: 'طائر',
    answer: 'طائر',
    ttsText: 'طائر',
    category: 'Animals',
    accentHex: '#F97316',
  ),
  GameItem(
    id: 'sun',
    prompt: 'شمس',
    answer: 'شمس',
    ttsText: 'شمس',
    category: 'Sky',
    accentHex: '#0EA5E9',
  ),
  GameItem(
    id: 'moon',
    prompt: 'قمر',
    answer: 'قمر',
    ttsText: 'قمر',
    category: 'Sky',
    accentHex: '#0EA5E9',
  ),
  GameItem(
    id: 'book',
    prompt: 'كتاب',
    answer: 'كتاب',
    ttsText: 'كتاب',
    category: 'School',
    accentHex: '#22C55E',
  ),
  GameItem(
    id: 'pen',
    prompt: 'قلم',
    answer: 'قلم',
    ttsText: 'قلم',
    category: 'School',
    accentHex: '#22C55E',
  ),
];

@immutable
class GameSessionState {
  final GameConfig config;
  final int elapsedSeconds;
  final int moveCount;
  final List<MemoryCardState> memoryCards;
  final bool memoryLocked;
  final Map<String, String> sortingPlacements;
  final Map<String, bool> sortingFeedback;
  final int vocabularyIndex;
  final bool vocabularyShowingBack;
  final int knownCount;
  final int unknownCount;
  final bool isCompleted;

  const GameSessionState({
    required this.config,
    this.elapsedSeconds = 0,
    this.moveCount = 0,
    this.memoryCards = const <MemoryCardState>[],
    this.memoryLocked = false,
    this.sortingPlacements = const <String, String>{},
    this.sortingFeedback = const <String, bool>{},
    this.vocabularyIndex = 0,
    this.vocabularyShowingBack = false,
    this.knownCount = 0,
    this.unknownCount = 0,
    this.isCompleted = false,
  });

  factory GameSessionState.initial(GameConfig config, Random random) {
    return GameSessionState(
      config: config,
      memoryCards: config.type == GameType.memoryMatch
          ? buildMemoryDeck(config.items, random)
          : const <MemoryCardState>[],
    );
  }

  GameSessionState copyWith({
    int? elapsedSeconds,
    int? moveCount,
    List<MemoryCardState>? memoryCards,
    bool? memoryLocked,
    Map<String, String>? sortingPlacements,
    Map<String, bool>? sortingFeedback,
    int? vocabularyIndex,
    bool? vocabularyShowingBack,
    int? knownCount,
    int? unknownCount,
    bool? isCompleted,
  }) {
    return GameSessionState(
      config: config,
      elapsedSeconds: elapsedSeconds ?? this.elapsedSeconds,
      moveCount: moveCount ?? this.moveCount,
      memoryCards: memoryCards ?? this.memoryCards,
      memoryLocked: memoryLocked ?? this.memoryLocked,
      sortingPlacements: sortingPlacements ?? this.sortingPlacements,
      sortingFeedback: sortingFeedback ?? this.sortingFeedback,
      vocabularyIndex: vocabularyIndex ?? this.vocabularyIndex,
      vocabularyShowingBack:
          vocabularyShowingBack ?? this.vocabularyShowingBack,
      knownCount: knownCount ?? this.knownCount,
      unknownCount: unknownCount ?? this.unknownCount,
      isCompleted: isCompleted ?? this.isCompleted,
    );
  }

  List<MemoryCardState> get visibleMemoryCards => memoryCards;

  int get matchedPairCount => memoryCards
      .where((card) => card.isMatched)
      .map((card) => card.pairId)
      .toSet()
      .length;

  GameItem? get currentVocabularyItem {
    if (vocabularyIndex < 0 || vocabularyIndex >= config.items.length) {
      return null;
    }
    return config.items[vocabularyIndex];
  }

  int get placedSortingCount => sortingPlacements.entries.where((entry) {
        final item =
            config.items.firstWhere((candidate) => candidate.id == entry.key);
        return item.category == entry.value;
      }).length;
}

class GameSessionController
    extends StateNotifier<AsyncValue<GameSessionState>> {
  GameSessionController(this._ref, this._type) : super(const AsyncLoading()) {
    _load();
    _ref.onDispose(_dispose);
  }

  final Ref _ref;
  final GameType _type;
  final Random _random = Random();
  Timer? _timer;

  Future<void> _load() async {
    state = const AsyncLoading();
    try {
      final config = await _buildConfig();
      final session = GameSessionState.initial(config, _random);
      state = AsyncData(session);
      _startTimer();
    } catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
    }
  }

  void resetGame() {
    _timer?.cancel();
    _load();
  }

  Future<GameConfig> _buildConfig() async {
    switch (_type) {
      case GameType.memoryMatch:
        return _buildMemoryConfig();
      case GameType.sorting:
        return _buildSortingConfig();
      case GameType.vocabulary:
        return _buildVocabularyConfig();
    }
  }

  Future<GameConfig> _buildMemoryConfig() async {
    final items = await _loadVisualItems(preferredCount: 8);
    final pairCount = items.length >= 8 ? 8 : min(items.length, 6);
    final difficulty =
        pairCount >= 8 ? GameDifficulty.medium : GameDifficulty.easy;
    return GameConfig(
      type: GameType.memoryMatch,
      items: items.take(pairCount).toList(),
      difficulty: difficulty,
      rewardStars: difficulty == GameDifficulty.medium ? 5 : 4,
    );
  }

  Future<GameConfig> _buildSortingConfig() async {
    final repo = _ref.read(contentRepositoryProvider);
    final result = await repo.getContentItems();
    final grouped = <String, List<ContentItem>>{};

    for (final item in result.items) {
      final category = _sortingCategory(item);
      grouped.putIfAbsent(category, () => <ContentItem>[]);
      grouped[category]!.add(item);
    }

    final selected = <GameItem>[];
    final sortedCategories = grouped.entries.toList()
      ..sort((left, right) => right.value.length.compareTo(left.value.length));

    for (final entry in sortedCategories.take(3)) {
      for (final item in entry.value.take(3)) {
        selected.add(
          GameItem(
            id: item.id,
            prompt: _displayPrompt(item),
            answer: item.title,
            ttsText: _ttsText(item),
            category: entry.key,
            accentHex: item.themeColor,
          ),
        );
      }
    }

    final items = selected.length >= 6
        ? selected.take(8).toList()
        : _fallbackSortingItems;
    return GameConfig(
      type: GameType.sorting,
      items: items,
      difficulty:
          items.length >= 8 ? GameDifficulty.medium : GameDifficulty.easy,
      rewardStars: items.length >= 8 ? 4 : 3,
    );
  }

  Future<GameConfig> _buildVocabularyConfig() async {
    final items = await _loadVisualItems(preferredCount: 8);
    final deckSize = min(items.length, 8);
    final difficulty =
        deckSize >= 8 ? GameDifficulty.medium : GameDifficulty.easy;
    return GameConfig(
      type: GameType.vocabulary,
      items: items.take(deckSize).toList(),
      difficulty: difficulty,
      rewardStars: difficulty == GameDifficulty.medium ? 4 : 3,
    );
  }

  Future<List<GameItem>> _loadVisualItems({
    required int preferredCount,
  }) async {
    final repo = _ref.read(contentRepositoryProvider);
    final storyResult = await repo.getContentItems(
      contentType: ContentType.story.apiValue,
    );
    final allResult = await repo.getContentItems();
    final seenIds = <String>{};
    final items = <GameItem>[];
    final candidates = <ContentItem>[
      ...storyResult.items,
      ...allResult.items,
    ];

    for (final item in candidates) {
      if (items.length >= preferredCount) {
        break;
      }
      if (seenIds.contains(item.id)) {
        continue;
      }
      seenIds.add(item.id);

      final prompt = _displayPrompt(item);
      if (prompt.isEmpty) {
        continue;
      }

      String? imageUrl;
      try {
        final pages = await repo.getStoryPages(item.id);
        if (pages.isNotEmpty) {
          imageUrl = pages.first.downloadUrl;
        }
      } catch (_) {
        imageUrl = null;
      }

      items.add(
        GameItem(
          id: item.id,
          prompt: prompt,
          answer: item.title,
          ttsText: _ttsText(item),
          category: _sortingCategory(item),
          imageUrl: imageUrl,
          accentHex: item.themeColor,
        ),
      );
    }

    if (items.length >= preferredCount) {
      return items;
    }

    final remaining = preferredCount - items.length;
    return <GameItem>[
      ...items,
      ..._fallbackVisualItems.take(remaining),
    ];
  }

  static String _sortingCategory(ContentItem item) {
    final contentType = item.type;
    switch (contentType) {
      case ContentType.story:
        return 'Story';
      case ContentType.interactive:
        return 'Interactive';
      case ContentType.coloringBook:
        return 'Coloring';
      case ContentType.document:
        return 'Document';
      case ContentType.audio:
        return 'Audio';
      case ContentType.video:
        return 'Video';
      case ContentType.unknown:
        return 'General';
    }
  }

  static String _displayPrompt(ContentItem item) {
    final letter = item.letter?.trim();
    if (letter != null && letter.isNotEmpty) {
      return letter;
    }
    return item.title.trim();
  }

  static String _ttsText(ContentItem item) {
    final prompt = _displayPrompt(item);
    return prompt.isEmpty ? item.title : prompt;
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      final current = state.valueOrNull;
      if (current == null || current.isCompleted) {
        return;
      }
      state = AsyncData(
        current.copyWith(elapsedSeconds: current.elapsedSeconds + 1),
      );
    });
  }

  void _dispose() {
    _timer?.cancel();
  }

  void flipMemoryCard(String cardId) {
    final current = state.valueOrNull;
    if (current == null || current.memoryLocked || current.isCompleted) {
      return;
    }

    final index =
        current.memoryCards.indexWhere((candidate) => candidate.id == cardId);
    if (index < 0) {
      return;
    }

    final targetCard = current.memoryCards[index];
    if (targetCard.isFaceUp || targetCard.isMatched) {
      return;
    }

    final deck = List<MemoryCardState>.of(current.memoryCards);
    deck[index] = targetCard.copyWith(isFaceUp: true);
    final flipped = deck
        .where((candidate) => candidate.isFaceUp && !candidate.isMatched)
        .toList();

    if (flipped.length < 2) {
      state = AsyncData(current.copyWith(memoryCards: deck));
      return;
    }

    final moveCount = current.moveCount + 1;
    final first = flipped[0];
    final second = flipped[1];

    if (first.pairId == second.pairId) {
      final matchedDeck = deck
          .map(
            (candidate) => candidate.pairId == first.pairId
                ? candidate.copyWith(isFaceUp: true, isMatched: true)
                : candidate,
          )
          .toList();
      final completed = matchedDeck.every((candidate) => candidate.isMatched);
      if (completed) {
        _timer?.cancel();
      }
      state = AsyncData(
        current.copyWith(
          memoryCards: matchedDeck,
          moveCount: moveCount,
          memoryLocked: false,
          isCompleted: completed,
        ),
      );
      return;
    }

    state = AsyncData(
      current.copyWith(
        memoryCards: deck,
        moveCount: moveCount,
        memoryLocked: true,
      ),
    );

    Future<void>.delayed(const Duration(milliseconds: 900), () {
      final latest = state.valueOrNull;
      if (latest == null) {
        return;
      }
      final resetDeck = latest.memoryCards
          .map(
            (candidate) => candidate.isMatched
                ? candidate
                : candidate.copyWith(isFaceUp: false),
          )
          .toList();
      state = AsyncData(
        latest.copyWith(
          memoryCards: resetDeck,
          memoryLocked: false,
        ),
      );
    });
  }

  Future<void> dropSortingItem(String itemId, String category) async {
    final current = state.valueOrNull;
    if (current == null || current.isCompleted) {
      return;
    }

    final item =
        current.config.items.firstWhere((candidate) => candidate.id == itemId);
    final isCorrect = item.category == category;
    final placements = Map<String, String>.of(current.sortingPlacements)
      ..[itemId] = category;
    final feedback = Map<String, bool>.of(current.sortingFeedback)
      ..[itemId] = isCorrect;

    if (isCorrect) {
      final completed = current.config.items.every(
        (candidate) => placements[candidate.id] == candidate.category,
      );
      if (completed) {
        _timer?.cancel();
      }
      state = AsyncData(
        current.copyWith(
          sortingPlacements: placements,
          sortingFeedback: feedback,
          moveCount: current.moveCount + 1,
          isCompleted: completed,
        ),
      );
      return;
    }

    state = AsyncData(
      current.copyWith(
        sortingPlacements: placements,
        sortingFeedback: feedback,
        moveCount: current.moveCount + 1,
      ),
    );

    await Future<void>.delayed(const Duration(milliseconds: 700));
    final latest = state.valueOrNull;
    if (latest == null) {
      return;
    }
    final nextPlacements = Map<String, String>.of(latest.sortingPlacements)
      ..remove(itemId);
    final nextFeedback = Map<String, bool>.of(latest.sortingFeedback)
      ..remove(itemId);
    state = AsyncData(
      latest.copyWith(
        sortingPlacements: nextPlacements,
        sortingFeedback: nextFeedback,
      ),
    );
  }

  void flipVocabularyCard() {
    final current = state.valueOrNull;
    if (current == null || current.isCompleted) {
      return;
    }
    state = AsyncData(
      current.copyWith(
        vocabularyShowingBack: !current.vocabularyShowingBack,
      ),
    );
  }

  void classifyVocabularyCard(bool known) {
    final current = state.valueOrNull;
    if (current == null || current.isCompleted) {
      return;
    }

    final nextIndex = current.vocabularyIndex + 1;
    final completed = nextIndex >= current.config.items.length;
    if (completed) {
      _timer?.cancel();
    }
    state = AsyncData(
      current.copyWith(
        vocabularyIndex: completed ? current.vocabularyIndex : nextIndex,
        vocabularyShowingBack: false,
        knownCount: current.knownCount + (known ? 1 : 0),
        unknownCount: current.unknownCount + (known ? 0 : 1),
        moveCount: current.moveCount + 1,
        isCompleted: completed,
      ),
    );
  }
}

final gameProvider = StateNotifierProvider.autoDispose
    .family<GameSessionController, AsyncValue<GameSessionState>, GameType>(
  (ref, type) => GameSessionController(ref, type),
);
