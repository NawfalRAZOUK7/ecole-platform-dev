/// Letter Puzzle — procedural jigsaw (Feature: Montessori Arabic letters).
///
/// A rows×cols grid of interlocking jigsaw pieces is laid over a faint letter
/// watermark. Each piece carries a vocabulary word + emoji that starts with the
/// letter. The child DRAGS each piece into its matching slot; on a correct drop
/// the word is pronounced (TTS), the device gives haptic feedback and the score
/// rises. Completing the letter fires confetti and a success dialog.
///
/// The jigsaw geometry is generated procedurally (see jigsaw_geometry.dart), so
/// it scales to any letter / language — Arabic now, French & English later — with
/// no per-letter hand-drawing. Letters are seeded locally here (Arabic first),
/// consistent with the other mobile mini-games; backend config can drive it next.

import 'dart:math';

import 'package:confetti/confetti.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/core/di/providers.dart';
import 'package:ecole_platform/features/ai/games/letter_puzzle/jigsaw_geometry.dart';

class PuzzleVocab {
  final String word;
  final String emoji;
  final Color color;
  const PuzzleVocab(this.word, this.emoji, this.color);
}

class LetterDef {
  final String letter;
  final String lang; // 'ar' | 'fr' | 'en'
  final List<PuzzleVocab> vocab;
  final int rows;
  final int cols;
  const LetterDef(
    this.letter,
    this.lang,
    this.vocab, {
    this.rows = 2,
    this.cols = 3,
  });
}

const _green = Color(0xFF4CAF50);
const _orange = Color(0xFFFF9800);
const _blue = Color(0xFF42A5F5);
const _purple = Color(0xFFAB47BC);
const _red = Color(0xFFEF5350);
const _teal = Color(0xFF26A69A);
const _palette = [_green, _orange, _blue, _purple, _red, _teal];

/// Arabic-first seed (vocalised vocabulary). 6 pieces → 2×3 grid.
const List<LetterDef> _letters = [
  LetterDef('أ', 'ar', [
    PuzzleVocab('أَرْنَبٌ', '🐰', _green),
    PuzzleVocab('أَسَدٌ', '🦁', _orange),
    PuzzleVocab('أَنَانَاسٌ', '🍍', _blue),
    PuzzleVocab('أَفْعَى', '🐍', _purple),
    PuzzleVocab('أَزْهَارٌ', '🌸', _red),
    PuzzleVocab('أُذُنٌ', '👂', _teal),
  ]),
  LetterDef('ب', 'ar', [
    PuzzleVocab('بُرْتُقَالٌ', '🍊', _orange),
    PuzzleVocab('بَصَلٌ', '🧅', _purple),
    PuzzleVocab('بَيْتٌ', '🏠', _blue),
    PuzzleVocab('بِطِّيخٌ', '🍉', _red),
    PuzzleVocab('بَاذِنْجَانٌ', '🍆', _green),
    PuzzleVocab('بِطْرِيقٌ', '🐧', _teal),
  ]),
  LetterDef('ت', 'ar', [
    PuzzleVocab('تُفَّاحٌ', '🍎', _red),
    PuzzleVocab('تَاجٌ', '👑', _orange),
    PuzzleVocab('تِمْسَاحٌ', '🐊', _green),
    PuzzleVocab('تُوتٌ', '🫐', _blue),
    PuzzleVocab('تِينٌ', '🪴', _teal),
    PuzzleVocab('تَلٌّ', '⛰️', _purple),
  ]),
  LetterDef('ث', 'ar', [
    PuzzleVocab('ثُعْبَانٌ', '🐍', _green),
    PuzzleVocab('ثَلْجٌ', '❄️', _blue),
    PuzzleVocab('ثَوْرٌ', '🐂', _orange),
    PuzzleVocab('ثَعْلَبٌ', '🦊', _red),
    PuzzleVocab('ثُومٌ', '🧄', _purple),
    PuzzleVocab('ثَوْبٌ', '👗', _teal),
  ]),
  LetterDef('ز', 'ar', [
    PuzzleVocab('زَيْتُونٌ', '🫒', _green),
    PuzzleVocab('زَيْتٌ', '🍶', _orange),
    PuzzleVocab('زَرَافَةٌ', '🦒', _blue),
    PuzzleVocab('زَهْرَةٌ', '🌸', _red),
    PuzzleVocab('زَوْرَقٌ', '⛵', _teal),
    PuzzleVocab('زُجَاجٌ', '🥃', _purple),
  ]),
];

/// Fetches letter-puzzle definitions from the backend game configs
/// (`/games/configs?game_type=letter_puzzle`) so Arabic/French/English flow
/// from data. Falls back to the local Arabic seed when offline or empty.
final letterPuzzleConfigsProvider =
    FutureProvider<List<LetterDef>>((ref) async {
  try {
    final api = ref.read(apiClientProvider);
    final resp = await api.list(
      '/games/configs',
      params: {'game_type': 'letter_puzzle'},
    );
    final defs = <LetterDef>[];
    for (final item in resp.data) {
      final cfg = item['config'] as Map<String, dynamic>?;
      if (cfg == null) continue;
      final letter = (cfg['letter'] as String?)?.trim() ?? '';
      final lang = cfg['language'] as String? ?? 'ar';
      final piecesJson = (cfg['pieces'] as List<dynamic>? ?? const []);
      final n = piecesJson.length;
      if (letter.isEmpty || n == 0) continue;
      // Grid from config; fall back to a sensible shape for the piece count.
      final grid = cfg['grid'] as Map<String, dynamic>?;
      var rows = (grid?['rows'] as num?)?.toInt() ?? (n <= 3 ? 1 : 2);
      var cols = (grid?['cols'] as num?)?.toInt() ?? ((n + rows - 1) ~/ rows);
      if (rows < 1) rows = 1;
      if (rows * cols < n) cols = (n + rows - 1) ~/ rows; // ensure it fits
      final vocab = <PuzzleVocab>[
        for (var i = 0; i < n; i++)
          PuzzleVocab(
            (piecesJson[i] as Map<String, dynamic>)['word'] as String? ?? '',
            (piecesJson[i] as Map<String, dynamic>)['emoji'] as String? ?? '🔤',
            _palette[i % _palette.length],
          ),
      ];
      defs.add(LetterDef(letter, lang, vocab, rows: rows, cols: cols));
    }
    return defs.isEmpty ? _letters : defs;
  } catch (_) {
    return _letters; // offline / error → local Arabic seed
  }
});

class LetterPuzzleScreen extends ConsumerStatefulWidget {
  const LetterPuzzleScreen({super.key});

  @override
  ConsumerState<LetterPuzzleScreen> createState() => _LetterPuzzleScreenState();
}

class _LetterPuzzleScreenState extends ConsumerState<LetterPuzzleScreen> {
  // Grid is per-letter (from the backend config), not fixed.
  late int _rows;
  late int _cols;

  late ConfettiController _confetti;
  int _letterIndex = 0;
  late JigsawLayout _layout;
  late List<_PieceGeom> _geoms;
  late List<bool> _placed;
  late List<int> _tray; // shuffled indices still in the tray
  int _score = 0;
  final _random = Random();

  /// Active letter set — local Arabic seed by default, replaced by the backend
  /// configs (AR/FR/EN) once they load.
  List<LetterDef> _source = _letters;
  bool _appliedRemote = false;

  LetterDef get _letter => _source[_letterIndex];

  @override
  void initState() {
    super.initState();
    _confetti = ConfettiController(duration: const Duration(seconds: 2));
    _setupPuzzle();
  }

  @override
  void dispose() {
    _confetti.dispose();
    super.dispose();
  }

  void _setupPuzzle() {
    const cell = 96.0;
    _rows = _letter.rows;
    _cols = _letter.cols;
    final n = _letter.vocab.length;
    _layout = JigsawLayout.generate(_rows, _cols, seed: _letterIndex + 1);
    // One piece per vocabulary entry, laid out row-major into the grid.
    _geoms = [
      for (int i = 0; i < n; i++)
        _PieceGeom.build(_layout, i ~/ _cols, i % _cols, cell, cell),
    ];
    _placed = List<bool>.filled(n, false);
    _tray = List<int>.generate(n, (i) => i)..shuffle(_random);
    _score = 0;
  }

  Future<void> _onPlaced(int index) async {
    HapticFeedback.mediumImpact();
    setState(() {
      _placed[index] = true;
      _tray.remove(index);
      _score++;
    });
    final vocab = _letter.vocab[index];
    await ref
        .read(ttsServiceProvider)
        .speakWord(vocab.word, lang: _letter.lang);
    if (_placed.every((p) => p)) {
      _confetti.play();
      await ref.read(ttsServiceProvider).speakPraise();
      if (mounted) _showSuccess();
    }
  }

  void _showSuccess() {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('🎉', style: TextStyle(fontSize: 56)),
            const SizedBox(height: 8),
            Text(
              'أحسنت! Bravo !',
              style: Theme.of(ctx).textTheme.headlineSmall,
            ),
            const SizedBox(height: 4),
            Text('Lettre « ${_letter.letter} » complétée'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(_setupPuzzle);
            },
            child: const Text('Rejouer'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(() {
                _letterIndex = (_letterIndex + 1) % _source.length;
                _setupPuzzle();
              });
            },
            child: const Text('Lettre suivante'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // Upgrade from the local seed to the backend configs (AR/FR/EN) once,
    // when they load. The fetch is kicked off by watching the provider.
    ref.listen<AsyncValue<List<LetterDef>>>(letterPuzzleConfigsProvider,
        (prev, next) {
      next.whenData((defs) {
        if (!_appliedRemote && defs.isNotEmpty) {
          setState(() {
            _appliedRemote = true;
            _source = defs;
            _letterIndex = 0;
            _setupPuzzle();
          });
        }
      });
    });
    ref.watch(letterPuzzleConfigsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('Puzzle — ${_letter.letter}'),
        actions: [
          PopupMenuButton<int>(
            icon: const Icon(Icons.apps),
            tooltip: 'Choisir une lettre',
            onSelected: (i) => setState(() {
              _letterIndex = i;
              _setupPuzzle();
            }),
            itemBuilder: (ctx) => [
              for (int i = 0; i < _source.length; i++)
                PopupMenuItem<int>(
                  value: i,
                  child: Row(
                    children: [
                      Text(
                        _source[i].letter,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '(${_source[i].lang})',
                        style: TextStyle(
                          color: Theme.of(ctx).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Center(child: Text('⭐ $_score')),
          ),
        ],
      ),
      body: Stack(
        children: [
          SafeArea(
            child: Column(
              children: [
                const SizedBox(height: 8),
                Text(
                  'Glisse chaque pièce à sa place pour former la lettre.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: 12),
                Expanded(child: Center(child: _buildBoard(theme))),
                _buildTray(),
                const SizedBox(height: 16),
              ],
            ),
          ),
          Align(
            alignment: Alignment.topCenter,
            child: ConfettiWidget(
              confettiController: _confetti,
              blastDirectionality: BlastDirectionality.explosive,
              shouldLoop: false,
              numberOfParticles: 20,
              colors: _palette,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBoard(ThemeData theme) {
    const cell = 96.0;
    final boardW = _cols * cell;
    final boardH = _rows * cell;
    final knobPad = 0.22 * cell;

    return SizedBox(
      width: boardW + 2 * knobPad,
      height: boardH + 2 * knobPad,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Faint letter watermark behind the board.
          Positioned.fill(
            child: Center(
              child: Text(
                _letter.letter,
                style: TextStyle(
                  fontSize: boardH * 0.9,
                  fontWeight: FontWeight.w900,
                  color: theme.colorScheme.primary.withValues(alpha: 0.08),
                ),
              ),
            ),
          ),
          // Slots + placed pieces.
          for (int i = 0; i < _geoms.length; i++)
            Positioned(
              left: knobPad + _geoms[i].bounds.left,
              top: knobPad + _geoms[i].bounds.top,
              width: _geoms[i].bounds.width,
              height: _geoms[i].bounds.height,
              child: DragTarget<int>(
                onWillAcceptWithDetails: (d) => d.data == i && !_placed[i],
                onAcceptWithDetails: (_) => _onPlaced(i),
                builder: (ctx, candidate, rejected) {
                  if (_placed[i]) {
                    return _JigsawTile(
                      geom: _geoms[i],
                      vocab: _letter.vocab[i],
                    );
                  }
                  return CustomPaint(
                    painter: _SlotPainter(
                      _geoms[i].local,
                      highlight: candidate.isNotEmpty,
                      color: theme.colorScheme.outlineVariant,
                      highlightColor: _orange,
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTray() {
    return SizedBox(
      height: 132,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          for (final i in _tray)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6),
              child: Draggable<int>(
                data: i,
                feedback: Material(
                  color: Colors.transparent,
                  child: _JigsawTile(geom: _geoms[i], vocab: _letter.vocab[i]),
                ),
                childWhenDragging: Opacity(
                  opacity: 0.3,
                  child: _JigsawTile(geom: _geoms[i], vocab: _letter.vocab[i]),
                ),
                child: _JigsawTile(geom: _geoms[i], vocab: _letter.vocab[i]),
              ),
            ),
        ],
      ),
    );
  }
}

/// Precomputed geometry for one piece, normalised to its own bounds.
class _PieceGeom {
  final Path local;
  final Rect bounds;
  const _PieceGeom(this.local, this.bounds);

  factory _PieceGeom.build(
    JigsawLayout layout,
    int row,
    int col,
    double cellW,
    double cellH,
  ) {
    final boardPath = jigsawPiecePath(
      layout: layout,
      row: row,
      col: col,
      cellW: cellW,
      cellH: cellH,
    );
    final bounds = boardPath.getBounds();
    final local = boardPath.shift(-bounds.topLeft);
    return _PieceGeom(local, bounds);
  }
}

/// A filled, bordered jigsaw piece showing its emoji + vocabulary word.
class _JigsawTile extends StatelessWidget {
  final _PieceGeom geom;
  final PuzzleVocab vocab;
  const _JigsawTile({required this.geom, required this.vocab});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: geom.bounds.width,
      height: geom.bounds.height,
      child: Stack(
        children: [
          ClipPath(
            clipper: _PathClipper(geom.local),
            child: Container(
              color: vocab.color,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(vocab.emoji, style: const TextStyle(fontSize: 26)),
                    Text(
                      vocab.word,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 11,
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          CustomPaint(
            size: geom.bounds.size,
            painter: _BorderPainter(geom.local),
          ),
        ],
      ),
    );
  }
}

class _PathClipper extends CustomClipper<Path> {
  final Path path;
  _PathClipper(this.path);
  @override
  Path getClip(Size size) => path;
  @override
  bool shouldReclip(covariant _PathClipper old) => old.path != path;
}

class _BorderPainter extends CustomPainter {
  final Path path;
  _BorderPainter(this.path);
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..color = Colors.white.withValues(alpha: 0.85),
    );
  }

  @override
  bool shouldRepaint(covariant _BorderPainter old) => old.path != path;
}

class _SlotPainter extends CustomPainter {
  final Path path;
  final bool highlight;
  final Color color;
  final Color highlightColor;
  _SlotPainter(
    this.path, {
    required this.highlight,
    required this.color,
    required this.highlightColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.fill
        ..color = (highlight ? highlightColor : color).withValues(alpha: 0.18),
    );
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = highlight ? 3 : 1.5
        ..color = highlight ? highlightColor : color,
    );
  }

  @override
  bool shouldRepaint(covariant _SlotPainter old) =>
      old.highlight != highlight || old.path != path;
}
