/// Procedural jigsaw geometry — language-agnostic.
///
/// Instead of hand-drawing each letter's pieces, we lay a rows×cols grid over
/// the letter glyph and generate classic jigsaw edges (tab / blank) whose
/// neighbours always match. This scales to any letter in any script (Arabic,
/// French, English, digits…) with zero per-letter authoring.
///
/// Pure geometry: no widgets, no I/O — unit-testable.
library;

import 'dart:math';
import 'dart:ui';

/// One side of a piece. A `tabOut` on one piece is always paired with a
/// `tabIn` on its neighbour, so adjacent edges interlock.
enum JigsawEdge { flat, tabOut, tabIn }

/// A consistent set of edges for a rows×cols grid. Internal edges are shared:
/// the right edge of (r,c) is the mirror of the left edge of (r,c+1), etc.
class JigsawLayout {
  final int rows;
  final int cols;

  /// Vertical cuts between columns: `_vEdge[r][c]` is the edge on the RIGHT of
  /// piece (r,c) for c in 0..cols-2. `tabOut` means (r,c) bulges right.
  final List<List<JigsawEdge>> _vEdge;

  /// Horizontal cuts between rows: `_hEdge[r][c]` is the edge on the BOTTOM of
  /// piece (r,c) for r in 0..rows-2. `tabOut` means (r,c) bulges down.
  final List<List<JigsawEdge>> _hEdge;

  JigsawLayout._(this.rows, this.cols, this._vEdge, this._hEdge);

  /// Generate a layout with random (but neighbour-consistent) knobs.
  factory JigsawLayout.generate(int rows, int cols, {int? seed}) {
    final rnd = Random(seed);
    final vEdge = List.generate(
      rows,
      (_) => List.generate(
        cols - 1,
        (_) => rnd.nextBool() ? JigsawEdge.tabOut : JigsawEdge.tabIn,
      ),
    );
    final hEdge = List.generate(
      rows - 1,
      (_) => List.generate(
        cols,
        (_) => rnd.nextBool() ? JigsawEdge.tabOut : JigsawEdge.tabIn,
      ),
    );
    return JigsawLayout._(rows, cols, vEdge, hEdge);
  }

  static JigsawEdge _mirror(JigsawEdge e) => switch (e) {
        JigsawEdge.tabOut => JigsawEdge.tabIn,
        JigsawEdge.tabIn => JigsawEdge.tabOut,
        JigsawEdge.flat => JigsawEdge.flat,
      };

  JigsawEdge topOf(int r, int c) =>
      r == 0 ? JigsawEdge.flat : _mirror(_hEdge[r - 1][c]);
  JigsawEdge bottomOf(int r, int c) =>
      r == rows - 1 ? JigsawEdge.flat : _hEdge[r][c];
  JigsawEdge leftOf(int r, int c) =>
      c == 0 ? JigsawEdge.flat : _mirror(_vEdge[r][c - 1]);
  JigsawEdge rightOf(int r, int c) =>
      c == cols - 1 ? JigsawEdge.flat : _vEdge[r][c];

  int get pieceCount => rows * cols;
}

/// How far a knob bulges, as a fraction of the shorter cell side.
const double _kKnobFraction = 0.22;

/// Neck width of a knob, as a fraction of the edge length.
const double _kNeck = 0.18;

/// Build the closed [Path] for the piece at (row,col).
///
/// Coordinates are in BOARD space: the piece sits at its grid cell, and knobs
/// may extend beyond the cell rectangle into neighbouring cells (that overlap
/// is intentional and how jigsaws interlock).
Path jigsawPiecePath({
  required JigsawLayout layout,
  required int row,
  required int col,
  required double cellW,
  required double cellH,
}) {
  final left = col * cellW;
  final top = row * cellH;
  final right = left + cellW;
  final bottom = top + cellH;
  final knob = _kKnobFraction * min(cellW, cellH);

  final path = Path()..moveTo(left, top);

  _edge(
    path,
    layout.topOf(row, col),
    Offset(left, top),
    Offset(right, top),
    cellW,
    knob,
    outwardSign: -1,
    horizontal: true,
  );
  _edge(
    path,
    layout.rightOf(row, col),
    Offset(right, top),
    Offset(right, bottom),
    cellH,
    knob,
    outwardSign: 1,
    horizontal: false,
  );
  _edge(
    path,
    layout.bottomOf(row, col),
    Offset(right, bottom),
    Offset(left, bottom),
    cellW,
    knob,
    outwardSign: 1,
    horizontal: true,
  );
  _edge(
    path,
    layout.leftOf(row, col),
    Offset(left, bottom),
    Offset(left, top),
    cellH,
    knob,
    outwardSign: -1,
    horizontal: false,
  );

  path.close();
  return path;
}

/// Draw one edge from [start] to [end]. For tab edges, a rounded knob bulges
/// out (away from the piece centre) for [JigsawEdge.tabOut] and in for tabIn.
void _edge(
  Path path,
  JigsawEdge edge,
  Offset start,
  Offset end,
  double length,
  double knob, {
  required int outwardSign,
  required bool horizontal,
}) {
  if (edge == JigsawEdge.flat) {
    path.lineTo(end.dx, end.dy);
    return;
  }

  // Direction along the edge and the outward normal.
  final dir = (end - start) / length;
  final normal = horizontal
      ? Offset(0, outwardSign.toDouble())
      : Offset(outwardSign.toDouble(), 0);
  final bulge = edge == JigsawEdge.tabOut ? normal * knob : normal * -knob;

  final neckStart = start + dir * (length * (0.5 - _kNeck));
  final neckEnd = start + dir * (length * (0.5 + _kNeck));
  final headCenter = start + dir * (length * 0.5) + bulge;
  final headLeft = neckStart + bulge;
  final headRight = neckEnd + bulge;

  path.lineTo(neckStart.dx, neckStart.dy);
  // Up into the knob, around the head, and back down — two cubics.
  path.cubicTo(
    headLeft.dx,
    headLeft.dy,
    headCenter.dx,
    headCenter.dy,
    headCenter.dx,
    headCenter.dy,
  );
  path.cubicTo(
    headCenter.dx,
    headCenter.dy,
    headRight.dx,
    headRight.dy,
    neckEnd.dx,
    neckEnd.dy,
  );
  path.lineTo(end.dx, end.dy);
}

/// The straight cell rectangle for a slot at (row,col) — used to position the
/// recessed board slots (the knob overlap is handled by the piece path).
Rect cellRect(int row, int col, double cellW, double cellH) =>
    Rect.fromLTWH(col * cellW, row * cellH, cellW, cellH);
