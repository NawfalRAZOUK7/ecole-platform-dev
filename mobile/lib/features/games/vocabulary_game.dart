/// Vocabulary mini-game — flash a word and choose the correct translation.
///
/// Configurable via [wordPairs]. Defaults to a basic Arabic→French set.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/services/tts_service.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

class WordPair {
  final String source;         // word shown (Arabic)
  final String translation;    // correct answer (French)

  const WordPair(this.source, this.translation);
}

const _kDefaultPairs = <WordPair>[
  WordPair('شمس', 'Soleil'),
  WordPair('قمر', 'Lune'),
  WordPair('نجمة', 'Étoile'),
  WordPair('بيت', 'Maison'),
  WordPair('كتاب', 'Livre'),
  WordPair('قلم', 'Stylo'),
  WordPair('سمكة', 'Poisson'),
  WordPair('طائر', 'Oiseau'),
  WordPair('قطة', 'Chat'),
  WordPair('كلب', 'Chien'),
];

const _kRound = 10; // questions per session

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

class VocabularyGame extends ConsumerStatefulWidget {
  final List<WordPair>? wordPairs;
  final void Function(int score) onComplete;

  const VocabularyGame({
    super.key,
    this.wordPairs,
    required this.onComplete,
  });

  @override
  ConsumerState<VocabularyGame> createState() => _VocabularyGameState();
}

class _VocabularyGameState extends ConsumerState<VocabularyGame> {
  late List<WordPair> _pairs;
  late List<WordPair> _round;
  final _rng = math.Random();
  int _index = 0;
  int _score = 0;
  int? _selectedIdx;
  bool _answered = false;
  bool _done = false;
  late List<String> _choices; // 4 choices for current question

  @override
  void initState() {
    super.initState();
    _pairs = widget.wordPairs ?? _kDefaultPairs;
    _newRound();
  }

  void _newRound() {
    final shuffled = [..._pairs]..shuffle(_rng);
    _round = shuffled.take(math.min(_kRound, shuffled.length)).toList();
    _index = 0;
    _score = 0;
    _selectedIdx = null;
    _answered = false;
    _done = false;
    _buildChoices();
  }

  void _buildChoices() {
    if (_index >= _round.length) return;
    final correct = _round[_index].translation;
    final distractors = _pairs
        .where((p) => p.translation != correct)
        .map((p) => p.translation)
        .toList()
      ..shuffle(_rng);
    final choices = [correct, ...distractors.take(3)]..shuffle(_rng);
    _choices = choices;
  }

  void _speak() {
    final word = _round[_index].source;
    ref.read(ttsServiceProvider.notifier).speak(word);
  }

  void _onChoice(int idx) {
    if (_answered) return;
    setState(() {
      _selectedIdx = idx;
      _answered = true;
      if (_choices[idx] == _round[_index].translation) {
        _score++;
      }
    });
    Future.delayed(const Duration(milliseconds: 900), _next);
  }

  void _next() {
    if (!mounted) return;
    final nextIndex = _index + 1;
    if (nextIndex >= _round.length) {
      setState(() => _done = true);
      widget.onComplete(_score);
    } else {
      setState(() {
        _index = nextIndex;
        _selectedIdx = null;
        _answered = false;
        _buildChoices();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_done) {
      return Scaffold(
        appBar: AppBar(title: const Text('Vocabulaire')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                _score == _round.length ? '🌟' : '💪',
                style: const TextStyle(fontSize: 64),
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                '$_score / ${_round.length}',
                style: theme.textTheme.headlineMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(_score == _round.length
                  ? 'Parfait !'
                  : 'Bien joué, continue !'),
              const SizedBox(height: AppSpacing.lg),
              FilledButton.icon(
                onPressed: () => setState(_newRound),
                icon: const Icon(Icons.replay),
                label: const Text('Rejouer'),
              ),
              const SizedBox(height: AppSpacing.sm),
              OutlinedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Retour aux jeux'),
              ),
            ],
          ),
        ),
      );
    }

    final current = _round[_index];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Vocabulaire'),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: AppSpacing.sm),
              child: Text('${_index + 1}/${_round.length}  •  $_score pts'),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Progress bar
          LinearProgressIndicator(
            value: (_index + 1) / _round.length,
            backgroundColor: KidsContentColors.xpBarBackground,
            color: KidsContentColors.xpBar,
          ),

          // Word card
          Expanded(
            flex: 2,
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Comment dit-on en français ?',
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  GestureDetector(
                    onTap: _speak,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.xl, vertical: AppSpacing.lg),
                      decoration: BoxDecoration(
                        color: KidsContentColors.storyBackground,
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: const [
                          BoxShadow(blurRadius: 8, color: Colors.black12),
                        ],
                      ),
                      child: Column(
                        children: [
                          Text(
                            current.source,
                            style: const TextStyle(
                              fontSize: 48,
                              fontWeight: FontWeight.bold,
                            ),
                            textDirection: TextDirection.rtl,
                          ),
                          const SizedBox(height: AppSpacing.xs),
                          const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.volume_up,
                                  size: 16,
                                  color: KidsContentColors.storyPageTurn),
                              SizedBox(width: 4),
                              Text('Écouter',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: KidsContentColors.storyPageTurn,
                                  )),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Choice buttons
          Expanded(
            flex: 2,
            child: GridView.count(
              crossAxisCount: 2,
              padding: const EdgeInsets.all(AppSpacing.md),
              mainAxisSpacing: AppSpacing.sm,
              crossAxisSpacing: AppSpacing.sm,
              childAspectRatio: 2.5,
              children: List.generate(_choices.length, (i) {
                return _ChoiceButton(
                  label: _choices[i],
                  index: i,
                  selectedIndex: _selectedIdx,
                  correctIndex: _answered
                      ? _choices.indexOf(current.translation)
                      : null,
                  onTap: () => _onChoice(i),
                );
              }),
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Choice button
// ---------------------------------------------------------------------------

class _ChoiceButton extends StatelessWidget {
  final String label;
  final int index;
  final int? selectedIndex;
  final int? correctIndex;
  final VoidCallback onTap;

  const _ChoiceButton({
    required this.label,
    required this.index,
    required this.selectedIndex,
    required this.correctIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color borderColor;

    if (correctIndex != null) {
      if (index == correctIndex) {
        bgColor = KidsContentColors.gameGreen.withAlpha(60);
        borderColor = KidsContentColors.gameGreen;
      } else if (index == selectedIndex) {
        bgColor = KidsContentColors.gameRed.withAlpha(60);
        borderColor = KidsContentColors.gameRed;
      } else {
        bgColor = Colors.transparent;
        borderColor = Colors.grey.shade300;
      }
    } else {
      bgColor = Colors.transparent;
      borderColor = Theme.of(context).colorScheme.outline;
    }

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor, width: 2),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Center(
          child: Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}
