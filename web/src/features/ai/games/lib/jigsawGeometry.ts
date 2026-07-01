/**
 * Procedural jigsaw geometry (web) — mirrors the Flutter `jigsaw_geometry.dart`.
 *
 * Lays a rows×cols grid over a glyph and generates classic tab/blank jigsaw
 * edges whose neighbours always interlock. Produces an SVG path string per
 * piece, so it scales to any letter / language with no per-letter authoring.
 *
 * Each piece is returned in LOCAL coordinates with the cell inset by `pad`
 * (= knob size) on every side, so all tiles share the same size and align by
 * positioning the cell, not the bounds.
 */

export type Edge = 'flat' | 'tabOut' | 'tabIn';

const KNOB_FRACTION = 0.22;
const NECK = 0.18;

function mirror(e: Edge): Edge {
  if (e === 'tabOut') return 'tabIn';
  if (e === 'tabIn') return 'tabOut';
  return 'flat';
}

// Tiny deterministic PRNG (mulberry32) so layouts are stable per seed.
function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface JigsawLayout {
  rows: number;
  cols: number;
  top: (r: number, c: number) => Edge;
  right: (r: number, c: number) => Edge;
  bottom: (r: number, c: number) => Edge;
  left: (r: number, c: number) => Edge;
}

export function generateLayout(rows: number, cols: number, seed: number): JigsawLayout {
  const rnd = rng(seed);
  // vertical cuts: vEdge[r][c] = right edge of (r,c), c in 0..cols-2
  const vEdge: Edge[][] = Array.from({ length: rows }, () =>
    Array.from({ length: Math.max(0, cols - 1) }, () => (rnd() < 0.5 ? 'tabOut' : 'tabIn')),
  );
  // horizontal cuts: hEdge[r][c] = bottom edge of (r,c), r in 0..rows-2
  const hEdge: Edge[][] = Array.from({ length: Math.max(0, rows - 1) }, () =>
    Array.from({ length: cols }, () => (rnd() < 0.5 ? 'tabOut' : 'tabIn')),
  );
  return {
    rows,
    cols,
    top: (r, c) => (r === 0 ? 'flat' : mirror(hEdge[r - 1][c])),
    bottom: (r, c) => (r === rows - 1 ? 'flat' : hEdge[r][c]),
    left: (r, c) => (c === 0 ? 'flat' : mirror(vEdge[r][c - 1])),
    right: (r, c) => (c === cols - 1 ? 'flat' : vEdge[r][c]),
  };
}

interface Pt {
  x: number;
  y: number;
}

function edgeTo(
  parts: string[],
  edge: Edge,
  start: Pt,
  end: Pt,
  length: number,
  knob: number,
  outwardSign: number,
  horizontal: boolean,
): void {
  if (edge === 'flat') {
    parts.push(`L ${end.x} ${end.y}`);
    return;
  }
  const dir: Pt = { x: (end.x - start.x) / length, y: (end.y - start.y) / length };
  const normal: Pt = horizontal ? { x: 0, y: outwardSign } : { x: outwardSign, y: 0 };
  const sign = edge === 'tabOut' ? 1 : -1;
  const bulge: Pt = { x: normal.x * knob * sign, y: normal.y * knob * sign };

  const at = (t: number): Pt => ({ x: start.x + dir.x * length * t, y: start.y + dir.y * length * t });
  const neckStart = at(0.5 - NECK);
  const neckEnd = at(0.5 + NECK);
  const mid = at(0.5);
  const head: Pt = { x: mid.x + bulge.x, y: mid.y + bulge.y };
  const headLeft: Pt = { x: neckStart.x + bulge.x, y: neckStart.y + bulge.y };
  const headRight: Pt = { x: neckEnd.x + bulge.x, y: neckEnd.y + bulge.y };

  parts.push(`L ${neckStart.x} ${neckStart.y}`);
  parts.push(`C ${headLeft.x} ${headLeft.y} ${head.x} ${head.y} ${head.x} ${head.y}`);
  parts.push(`C ${head.x} ${head.y} ${headRight.x} ${headRight.y} ${neckEnd.x} ${neckEnd.y}`);
  parts.push(`L ${end.x} ${end.y}`);
}

export interface PieceGeom {
  row: number;
  col: number;
  d: string; // SVG path in local coords (cell inset by pad)
  tileW: number;
  tileH: number;
  pad: number;
  cellW: number;
  cellH: number;
}

/** Build the local SVG path for piece (row,col). */
export function piecePath(
  layout: JigsawLayout,
  row: number,
  col: number,
  cellW: number,
  cellH: number,
): PieceGeom {
  const knob = KNOB_FRACTION * Math.min(cellW, cellH);
  const pad = knob;
  const l = pad;
  const t = pad;
  const r = pad + cellW;
  const b = pad + cellH;

  const parts: string[] = [`M ${l} ${t}`];
  edgeTo(parts, layout.top(row, col), { x: l, y: t }, { x: r, y: t }, cellW, knob, -1, true);
  edgeTo(parts, layout.right(row, col), { x: r, y: t }, { x: r, y: b }, cellH, knob, 1, false);
  edgeTo(parts, layout.bottom(row, col), { x: r, y: b }, { x: l, y: b }, cellW, knob, 1, true);
  edgeTo(parts, layout.left(row, col), { x: l, y: b }, { x: l, y: t }, cellH, knob, -1, false);
  parts.push('Z');

  return {
    row,
    col,
    d: parts.join(' '),
    tileW: cellW + 2 * pad,
    tileH: cellH + 2 * pad,
    pad,
    cellW,
    cellH,
  };
}

export function allPieces(
  layout: JigsawLayout,
  cellW: number,
  cellH: number,
): PieceGeom[] {
  const out: PieceGeom[] = [];
  for (let r = 0; r < layout.rows; r++) {
    for (let c = 0; c < layout.cols; c++) {
      out.push(piecePath(layout, r, c, cellW, cellH));
    }
  }
  return out;
}
