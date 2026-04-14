import 'dart:math';

enum GameType {
  memoryMatch('memory'),
  sorting('sorting'),
  vocabulary('vocabulary');

  const GameType(this.slug);

  final String slug;
}

enum GameDifficulty {
  easy,
  medium,
  hard,
}

class GameItem {
  final String id;
  final String prompt;
  final String answer;
  final String? category;
  final String? imageUrl;
  final String ttsText;
  final String? accentHex;

  const GameItem({
    required this.id,
    required this.prompt,
    required this.answer,
    required this.ttsText,
    this.category,
    this.imageUrl,
    this.accentHex,
  });
}

class GameConfig {
  final GameType type;
  final List<GameItem> items;
  final GameDifficulty difficulty;
  final int rewardStars;

  const GameConfig({
    required this.type,
    required this.items,
    required this.difficulty,
    required this.rewardStars,
  });
}

enum MemoryCardFaceKind {
  prompt,
  answer,
}

class MemoryCardState {
  final String id;
  final String pairId;
  final String label;
  final String ttsText;
  final String? imageUrl;
  final String? accentHex;
  final MemoryCardFaceKind faceKind;
  final bool isFaceUp;
  final bool isMatched;

  const MemoryCardState({
    required this.id,
    required this.pairId,
    required this.label,
    required this.ttsText,
    required this.faceKind,
    this.imageUrl,
    this.accentHex,
    this.isFaceUp = false,
    this.isMatched = false,
  });

  MemoryCardState copyWith({
    bool? isFaceUp,
    bool? isMatched,
  }) {
    return MemoryCardState(
      id: id,
      pairId: pairId,
      label: label,
      ttsText: ttsText,
      faceKind: faceKind,
      imageUrl: imageUrl,
      accentHex: accentHex,
      isFaceUp: isFaceUp ?? this.isFaceUp,
      isMatched: isMatched ?? this.isMatched,
    );
  }
}

List<MemoryCardState> buildMemoryDeck(
  List<GameItem> items,
  Random random,
) {
  final deck = <MemoryCardState>[
    for (final item in items) ...[
      MemoryCardState(
        id: '${item.id}:prompt',
        pairId: item.id,
        label: item.prompt,
        ttsText: item.ttsText,
        accentHex: item.accentHex,
        faceKind: MemoryCardFaceKind.prompt,
      ),
      MemoryCardState(
        id: '${item.id}:answer',
        pairId: item.id,
        label: item.answer,
        ttsText: item.ttsText,
        imageUrl: item.imageUrl,
        accentHex: item.accentHex,
        faceKind: MemoryCardFaceKind.answer,
      ),
    ],
  ]..shuffle(random);
  return deck;
}
