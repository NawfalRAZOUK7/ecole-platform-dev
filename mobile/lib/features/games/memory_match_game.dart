/// Memory Match mini-game.
///
/// Shows a grid of face-down cards. Player taps two cards; if they match,
/// they stay face-up. All pairs found = win. Configurable with any emoji or
/// letter pairs.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

// ---------------------------------------------------------------------------
// Default card data — Arabic letters
// ---------------------------------------------------------------------------

const _kDefaultPairs = [
  'أ', 'ب', 'ت', 'ث',
  'ج', 'ح', 'خ', 'د',
];

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class _Card {
  final int id;        // unique index in the deck
  final String value;  // the letter/emoji shown when face-up
  bool faceUp = false;
  bool matched = false;

  _Card({required this.id, required this.value});
}

// ---------------------------------------------------------------------------
// Game
// ---------------------------------------------------------------------------

class MemoryMatchGame extends StatefulWidget {
  final List<String>? pairs; // override default pairs
  final void Function(int score) onComplete;

  const MemoryMatchGame({super.key, this.pairs, required this.onComplete});

  @override
  State<MemoryMatchGame> createState() => _MemoryMatchGameState();
}

class _MemoryMatchGameState extends State<MemoryMatchGame> {
  late List<_Card> _deck;
  final List<_Card> _selected = [];
  bool _locked = false;
  int _moves = 0;
  int _matches = 0;
  bool _won = false;

  @override
  void initState() {
    super.initState();
    _buildDeck();
  }

  void _buildDeck() {
    final pairs = widget.pairs ?? _kDefaultPairs;
    final items = [...pairs, ...pairs];
    items.shuffle();
    _deck = items.asMap().entries
        .map((e) => _Card(id: e.key, value: e.value))
        .toList();
    _selected.clear();
    _moves = 0;
    _matches = 0;
    _won = false;
    _locked = false;
  }

  void _onTap(_Card card) {
    if (_locked || card.faceUp || card.matched) return;
    setState(() {
      card.faceUp = true;
      _selected.add(card);
    });
    if (_selected.length == 2) {
      _moves++;
      _locked = true;
      if (_selected[0].value == _selected[1].value) {
        // Match!
        _matches++;
        for (final c in _selected) {
          c.matched = true;
        }
        _selected.clear();
        _locked = false;
        if (_matches == _deck.length ~/ 2) {
          setState(() => _won = true);
          widget.onComplete(_moves);
        } else {
          setState(() {});
        }
      } else {
        // No match — flip back after delay
        Timer(const Duration(milliseconds: 800), () {
          setState(() {
            for (final c in _selected) {
              c.faceUp = false;
            }
            _selected.clear();
            _locked = false;
          });
        });
      }
    }
  }

  void _restart() {
    setState(_buildDeck);
  }

  @override
  Widget build(BuildContext context) {
    final totalPairs = _deck.length ~/ 2;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Memory Match'),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: AppSpacing.sm),
              child: Text('$_matches/$totalPairs paires'),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Stats row
          Padding(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.base, vertical: AppSpacing.sm),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Chip(label: Text('$_moves coups')),
                FilledButton.tonal(
                  onPressed: _restart,
                  child: const Text('Rejouer'),
                ),
              ],
            ),
          ),

          // Grid
          Expanded(
            child: _won
                ? _WinBanner(moves: _moves, onRestart: _restart)
                : GridView.builder(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 4,
                      mainAxisSpacing: AppSpacing.sm,
                      crossAxisSpacing: AppSpacing.sm,
                    ),
                    itemCount: _deck.length,
                    itemBuilder: (_, i) {
                      final card = _deck[i];
                      return _CardTile(
                        card: card,
                        onTap: () => _onTap(card),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Card tile
// ---------------------------------------------------------------------------

class _CardTile extends StatelessWidget {
  final _Card card;
  final VoidCallback onTap;

  const _CardTile({required this.card, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final show = card.faceUp || card.matched;
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      transitionBuilder: (child, anim) =>
          ScaleTransition(scale: anim, child: child),
      child: GestureDetector(
        key: ValueKey('${card.id}_$show'),
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            color: card.matched
                ? KidsContentColors.gameGreen.withAlpha(60)
                : show
                    ? Colors.white
                    : KidsContentColors.gameCardBack,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: card.matched
                  ? KidsContentColors.gameGreen
                  : show
                      ? KidsContentColors.gameBlue
                      : KidsContentColors.gameCardBack,
              width: 2,
            ),
          ),
          child: Center(
            child: show
                ? Text(
                    card.value,
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  )
                : const Icon(Icons.help_outline,
                    color: Colors.white, size: 28),
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Win banner
// ---------------------------------------------------------------------------

class _WinBanner extends StatelessWidget {
  final int moves;
  final VoidCallback onRestart;

  const _WinBanner({required this.moves, required this.onRestart});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🎉', style: TextStyle(fontSize: 64)),
          const SizedBox(height: AppSpacing.md),
          Text(
            'Gagné !',
            style: Theme.of(context)
                .textTheme
                .headlineMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text('$moves coups'),
          const SizedBox(height: AppSpacing.lg),
          FilledButton.icon(
            onPressed: onRestart,
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
    );
  }
}
