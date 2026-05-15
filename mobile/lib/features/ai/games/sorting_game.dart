/// Sorting mini-game — drag items into the correct category bucket.
///
/// Configurable via [categories] and [items]. Defaults to a fruit/vegetable
/// sort for young learners.
library;

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

// ---------------------------------------------------------------------------
// Default data
// ---------------------------------------------------------------------------

class SortItem {
  final String label;
  final String category;
  final String emoji;

  const SortItem(this.label, this.category, this.emoji);
}

const _kDefaultCategories = <String>['Fruits', 'Légumes'];
const _kDefaultItems = <SortItem>[
  SortItem('Pomme', 'Fruits', '🍎'),
  SortItem('Banane', 'Fruits', '🍌'),
  SortItem('Orange', 'Fruits', '🍊'),
  SortItem('Fraise', 'Fruits', '🍓'),
  SortItem('Carotte', 'Légumes', '🥕'),
  SortItem('Brocoli', 'Légumes', '🥦'),
  SortItem('Tomate', 'Légumes', '🍅'),
  SortItem('Oignon', 'Légumes', '🧅'),
];

// ---------------------------------------------------------------------------
// Game state
// ---------------------------------------------------------------------------

class _ItemState {
  final SortItem item;
  String? placedCategory;

  _ItemState(this.item);
  bool get isPlaced => placedCategory != null;
  bool get isCorrect => placedCategory == item.category;
}

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

class SortingGame extends StatefulWidget {
  final List<String>? categories;
  final List<SortItem>? items;
  final void Function(int score) onComplete;

  const SortingGame({
    super.key,
    this.categories,
    this.items,
    required this.onComplete,
  });

  @override
  State<SortingGame> createState() => _SortingGameState();
}

class _SortingGameState extends State<SortingGame> {
  late List<String> _categories;
  late List<_ItemState> _items;
  bool _submitted = false;
  int _score = 0;

  @override
  void initState() {
    super.initState();
    _reset();
  }

  void _reset() {
    _categories = widget.categories ?? _kDefaultCategories;
    final rawItems = [...(widget.items ?? _kDefaultItems)]..shuffle();
    _items = rawItems.map((i) => _ItemState(i)).toList();
    _submitted = false;
    _score = 0;
  }

  void _submit() {
    setState(() {
      _submitted = true;
      _score = _items.where((i) => i.isCorrect).length;
    });
    if (_score == _items.length) {
      widget.onComplete(_score);
    }
  }

  List<_ItemState> get _unplaced => _items.where((i) => !i.isPlaced).toList();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trier les objets'),
        actions: [
          TextButton(
            onPressed: () => setState(_reset),
            child: const Text('Reset'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Category drop zones
          Expanded(
            flex: 3,
            child: Row(
              children: _categories.map((cat) {
                final placed =
                    _items.where((i) => i.placedCategory == cat).toList();
                return Expanded(
                  child: _DropZone(
                    category: cat,
                    items: placed,
                    submitted: _submitted,
                    onAccept: (item) {
                      setState(() {
                        item.placedCategory = cat;
                      });
                    },
                  ),
                );
              }).toList(),
            ),
          ),
          const Divider(),
          // Unplaced items
          Expanded(
            flex: 2,
            child: _unplaced.isEmpty
                ? Center(
                    child: FilledButton(
                      onPressed: _submitted ? null : _submit,
                      child: Text(
                        _submitted
                            ? 'Score: $_score/${_items.length}'
                            : 'Vérifier',
                      ),
                    ),
                  )
                : Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(AppSpacing.sm),
                        child: Text(
                          'À classer',
                          style: theme.textTheme.titleSmall,
                        ),
                      ),
                      Expanded(
                        child: Wrap(
                          spacing: AppSpacing.sm,
                          runSpacing: AppSpacing.sm,
                          alignment: WrapAlignment.center,
                          children: _unplaced
                              .map((item) => _DraggableItem(item: item))
                              .toList(),
                        ),
                      ),
                      if (_unplaced.isEmpty) ...[
                        FilledButton(
                          onPressed: _submitted ? null : _submit,
                          child: const Text('Vérifier'),
                        ),
                      ],
                    ],
                  ),
          ),
          if (_submitted) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.md),
              color: _score == _items.length
                  ? KidsContentColors.gameGreen.withAlpha(40)
                  : KidsContentColors.gameYellow.withAlpha(100),
              child: Text(
                _score == _items.length
                    ? '🎉 Parfait ! $_score/${_items.length} bien classés'
                    : '💪 $_score/${_items.length} bien classés — Réessaie !',
                textAlign: TextAlign.center,
                style:
                    const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Drop zone
// ---------------------------------------------------------------------------

class _DropZone extends StatelessWidget {
  final String category;
  final List<_ItemState> items;
  final bool submitted;
  final void Function(_ItemState) onAccept;

  const _DropZone({
    required this.category,
    required this.items,
    required this.submitted,
    required this.onAccept,
  });

  @override
  Widget build(BuildContext context) {
    return DragTarget<_ItemState>(
      onAcceptWithDetails: (details) => onAccept(details.data),
      builder: (_, candidates, __) {
        final hovering = candidates.isNotEmpty;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          margin: const EdgeInsets.all(AppSpacing.sm),
          decoration: BoxDecoration(
            color: hovering
                ? KidsContentColors.gameBlue.withAlpha(40)
                : Theme.of(context).colorScheme.surfaceContainerLow,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: hovering
                  ? KidsContentColors.gameBlue
                  : Theme.of(context).colorScheme.outline,
              width: hovering ? 2 : 1,
            ),
          ),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(AppSpacing.sm),
                child: Text(
                  category,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
              Expanded(
                child: Wrap(
                  alignment: WrapAlignment.center,
                  spacing: AppSpacing.xs,
                  runSpacing: AppSpacing.xs,
                  children: items
                      .map((i) => _PlacedChip(item: i, submitted: submitted))
                      .toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ---------------------------------------------------------------------------
// Draggable item
// ---------------------------------------------------------------------------

class _DraggableItem extends StatelessWidget {
  final _ItemState item;
  const _DraggableItem({required this.item});

  @override
  Widget build(BuildContext context) {
    return Draggable<_ItemState>(
      data: item,
      feedback: _ItemChip(item: item, opacity: 0.7),
      childWhenDragging: Opacity(
        opacity: 0.3,
        child: _ItemChip(item: item),
      ),
      child: _ItemChip(item: item),
    );
  }
}

class _ItemChip extends StatelessWidget {
  final _ItemState item;
  final double opacity;
  const _ItemChip({required this.item, this.opacity = 1.0});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: opacity,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm,
          vertical: AppSpacing.xs,
        ),
        decoration: BoxDecoration(
          color: KidsContentColors.gameYellow.withAlpha(80),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: KidsContentColors.starGold.withAlpha(120),
          ),
        ),
        child: Text(
          '${item.item.emoji} ${item.item.label}',
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
      ),
    );
  }
}

class _PlacedChip extends StatelessWidget {
  final _ItemState item;
  final bool submitted;
  const _PlacedChip({required this.item, required this.submitted});

  @override
  Widget build(BuildContext context) {
    Color? bg;
    if (submitted) {
      bg = item.isCorrect
          ? KidsContentColors.gameGreen.withAlpha(60)
          : KidsContentColors.gameRed.withAlpha(80);
    }
    return Container(
      margin: const EdgeInsets.all(2),
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: bg ?? KidsContentColors.gameYellow.withAlpha(60),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        '${item.item.emoji} ${item.item.label}',
        style: const TextStyle(fontSize: 12),
      ),
    );
  }
}
