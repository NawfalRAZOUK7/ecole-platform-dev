/**
 * LetterPuzzleGame — procedural jigsaw (web), parity with the Flutter screen.
 *
 * A rows×cols grid of interlocking jigsaw pieces sits over a faint letter
 * watermark. Each piece carries a vocabulary word + emoji that starts with the
 * letter. The child DRAGS each piece (HTML5 drag-and-drop) into its matching
 * slot; a correct drop pronounces the word (Web Speech / audio), bumps the
 * score, and completing the letter shows the celebration banner.
 *
 * Jigsaw geometry is generated procedurally (see lib/jigsawGeometry.ts), so it
 * works for any letter / language with no per-letter authoring.
 */

import { useMemo, useRef, useState, type DragEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useSpeech } from '@/shared/hooks/useSpeech';
import type { GameConfig, LetterPuzzleConfig, LetterPuzzlePiece } from '../model/types';
import { useCompleteGameConfig } from '../model/useGames';
import { allPieces, generateLayout, type PieceGeom } from '../lib/jigsawGeometry';
import { GameCompleteBanner } from './GameCompleteBanner';

interface LetterPuzzleGameProps {
  game: GameConfig;
  onExit: () => void;
}

const CELL = 92;
const PALETTE = ['#4CAF50', '#FF9800', '#42A5F5', '#AB47BC', '#EF5350', '#26A69A'];

function seedFromLetter(letter: string): number {
  let h = 0;
  for (let i = 0; i < letter.length; i++) h = (h * 31 + letter.charCodeAt(i)) >>> 0;
  return h || 1;
}

function PieceVisual({
  geom,
  piece,
  color,
}: {
  geom: PieceGeom;
  piece: LetterPuzzlePiece;
  color: string;
}) {
  return (
    <div style={{ position: 'relative', width: geom.tileW, height: geom.tileH }}>
      <svg
        width={geom.tileW}
        height={geom.tileH}
        viewBox={`0 0 ${geom.tileW} ${geom.tileH}`}
        style={{ display: 'block' }}
      >
        <path d={geom.d} fill={color} stroke="#ffffff" strokeWidth={2} />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
          color: '#fff',
          textAlign: 'center',
        }}
      >
        {piece.image_url ? (
          <img src={piece.image_url} alt={piece.word} width={32} height={32} />
        ) : (
          <span style={{ fontSize: 26, lineHeight: 1 }}>{piece.emoji ?? '🔤'}</span>
        )}
        <span style={{ fontSize: 11, fontWeight: 700 }}>{piece.word}</span>
      </div>
    </div>
  );
}

export function LetterPuzzleGame({ game, onExit }: LetterPuzzleGameProps) {
  const { t } = useTranslation();
  const { speak } = useSpeech();
  const config = game.config as unknown as LetterPuzzleConfig;
  const letter = config.letter ?? '?';
  const lang = config.language ?? 'ar';
  const pieces = useMemo(() => config.pieces ?? [], [config.pieces]);

  const { rows, cols, geoms } = useMemo(() => {
    const n = pieces.length || 6;
    const r = config.grid?.rows ?? (n <= 3 ? 1 : 2);
    const c = config.grid?.cols ?? Math.ceil(n / r);
    const lay = generateLayout(r, c, seedFromLetter(letter));
    return { rows: r, cols: c, geoms: allPieces(lay, CELL, CELL) };
  }, [pieces.length, config.grid, letter]);

  const [placed, setPlaced] = useState<boolean[]>(() => pieces.map(() => false));
  const [score, setScore] = useState(0);
  const [completed, setCompleted] = useState(false);
  const completeMutation = useCompleteGameConfig();
  const completionSentRef = useRef(false);
  const startedAt = useRef(Date.now());

  if (pieces.length === 0) {
    return <p>{t('letterPuzzle.noPieces', 'Aucune pièce disponible.')}</p>;
  }

  const pad = geoms[0]?.pad ?? 20;
  const boardW = cols * CELL + 2 * pad;
  const boardH = rows * CELL + 2 * pad;
  const isRtl = lang === 'ar';

  function place(index: number) {
    if (placed[index]) return;
    const piece = pieces[index];
    speak(piece.word, { lang, audioUrl: piece.audio_url ?? undefined });
    setScore((s) => s + 1);
    setPlaced((prev) => {
      const next = [...prev];
      next[index] = true;
      const done = next.every(Boolean);
      if (done && !completionSentRef.current) {
        completionSentRef.current = true;
        const elapsed = Math.floor((Date.now() - startedAt.current) / 1000);
        completeMutation.mutate({ gameId: game.id, score: 100, timeSeconds: elapsed });
        speak(letter, { lang, audioUrl: config.letter_audio_url ?? undefined });
        setCompleted(true);
      }
      return next;
    });
  }

  function handleDrop(e: DragEvent<HTMLDivElement>, slotIndex: number) {
    e.preventDefault();
    const dragged = Number(e.dataTransfer.getData('text/plain'));
    if (dragged === slotIndex) place(slotIndex);
  }

  function handleReplay() {
    completionSentRef.current = false;
    startedAt.current = Date.now();
    setPlaced(pieces.map(() => false));
    setScore(0);
    setCompleted(false);
  }

  const tray = pieces.map((_, i) => i).filter((i) => !placed[i]);

  return (
    <div dir={isRtl ? 'rtl' : 'ltr'}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>
          {t('letterPuzzle.instructions', 'Glisse chaque pièce à sa place pour former la lettre.')}
        </p>
        <span style={{ fontWeight: 700 }}>⭐ {score}</span>
      </div>

      {/* Board */}
      <div
        style={{
          position: 'relative',
          width: boardW,
          height: boardH,
          margin: '0 auto 24px',
        }}
      >
        {/* Letter watermark */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: boardH * 0.8,
            fontWeight: 900,
            color: 'var(--color-primary)',
            opacity: 0.08,
            pointerEvents: 'none',
            userSelect: 'none',
          }}
        >
          {letter}
        </div>

        {geoms.map((geom, i) => (
          <div
            key={`slot-${i}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => handleDrop(e, i)}
            style={{
              position: 'absolute',
              left: geom.col * CELL,
              top: geom.row * CELL,
              width: geom.tileW,
              height: geom.tileH,
            }}
          >
            {placed[i] ? (
              <PieceVisual geom={geom} piece={pieces[i]} color={PALETTE[i % PALETTE.length]} />
            ) : (
              <svg
                width={geom.tileW}
                height={geom.tileH}
                viewBox={`0 0 ${geom.tileW} ${geom.tileH}`}
                style={{ display: 'block' }}
              >
                <path
                  d={geom.d}
                  fill="var(--color-border, #e5e7eb)"
                  fillOpacity={0.25}
                  stroke="var(--color-border, #cbd5e1)"
                  strokeWidth={1.5}
                />
              </svg>
            )}
          </div>
        ))}
      </div>

      {/* Tray */}
      {!completed && (
        <div
          style={{
            display: 'flex',
            gap: 8,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {tray.map((i) => (
            <div
              key={`tray-${i}`}
              draggable
              onDragStart={(e) => e.dataTransfer.setData('text/plain', String(i))}
              style={{ cursor: 'grab' }}
            >
              <PieceVisual geom={geoms[i]} piece={pieces[i]} color={PALETTE[i % PALETTE.length]} />
            </div>
          ))}
        </div>
      )}

      {completed && (
        <GameCompleteBanner
          success
          starsEarned={game.rewardStars}
          xpEarned={game.rewardXp}
          loading={completeMutation.isPending}
          onReplay={handleReplay}
          onExit={onExit}
        />
      )}
    </div>
  );
}
