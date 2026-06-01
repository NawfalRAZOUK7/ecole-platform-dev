import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { VocabularyCardsGame } from '@/features/ai/games/ui/VocabularyCardsGame';
import type { GameConfig } from '@/features/ai/games/api/games.api';
import { renderWithProviders } from '../../../utils/render';
import { apiResponse, server } from '../../../utils/mocks';

const mockGame: GameConfig = {
  id: 'game-vocab-1',
  gameType: 'vocabulary_cards',
  title: 'Arabic Vocabulary',
  titleAr: 'مفردات عربية',
  titleFr: 'Vocabulaire Arabe',
  subject: 'arabic',
  difficulty: 'easy',
  targetAgeMin: 6,
  targetAgeMax: 10,
  config: {
    cards: [
      { word_ar: 'تفاحة', word_fr: 'Pomme', image_url: null },
      { word_ar: 'كتاب', word_fr: 'Livre', image_url: null },
      { word_ar: 'مدرسة', word_fr: 'École', image_url: null },
    ],
  },
  rewardStars: 3,
  rewardXp: 50,
  schoolId: 'school-1',
  isActive: true,
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-01-01T00:00:00Z',
};

const mockGameNoCards: GameConfig = {
  ...mockGame,
  id: 'game-empty',
  config: { cards: [] },
};

describe('VocabularyCardsGame', () => {
  it('shows "no cards" message when config has no cards', () => {
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGameNoCards} onExit={onExit} />, {
      user: { role: 'STD' },
    });
    expect(screen.getByText(/Aucune carte/i)).toBeInTheDocument();
  });

  it('renders first card with Arabic word', () => {
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });
    expect(screen.getByText('تفاحة')).toBeInTheDocument();
  });

  it('shows card progress counter', () => {
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });
    // Should show "1 / 3" style progress
    expect(screen.getByText(/1.*3/)).toBeInTheDocument();
  });

  it('has previous and next navigation buttons', () => {
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });
    // Previous button should be disabled on first card
    const prevButton = screen.getByRole('button', { name: /précédent/i });
    expect(prevButton).toBeDisabled();
  });

  it('navigates to next card on next click', async () => {
    const user = userEvent.setup();
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });

    const nextButton = screen.getByRole('button', { name: /suivant|next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('كتاب')).toBeInTheDocument();
    });
  });

  it('previous button enabled after navigating forward', async () => {
    const user = userEvent.setup();
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });

    const nextButton = screen.getByRole('button', { name: /suivant|next/i });
    await user.click(nextButton);

    await waitFor(() => {
      const prevButton = screen.getByRole('button', { name: /précédent/i });
      expect(prevButton).not.toBeDisabled();
    });
  });

  it('shows completion banner after finishing all cards', async () => {
    server.use(
      http.post('/api/v1/games/configs/:gameId/complete', () =>
        apiResponse({ xpEarned: 50, levelUp: false }),
      ),
    );
    const user = userEvent.setup();
    const onExit = vi.fn();
    const singleCardGame: GameConfig = {
      ...mockGame,
      config: { cards: [{ word_ar: 'تفاحة', word_fr: 'Pomme', image_url: null }] },
    };
    renderWithProviders(<VocabularyCardsGame game={singleCardGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });

    // With single card, the next/finish button shows "Terminer"
    const finishButton = screen.getByRole('button', { name: /terminer|finish/i });
    await user.click(finishButton);

    await waitFor(() => {
      // After finishing, the GameCompleteBanner should be rendered
      expect(
        document.querySelector('.game-complete-banner') ||
          screen.queryByRole('button', { name: /replay|rejouer|exit|quitter/i }),
      ).toBeTruthy();
    });
  });

  it('flips card when clicking on it', async () => {
    const user = userEvent.setup();
    const onExit = vi.fn();
    renderWithProviders(<VocabularyCardsGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });

    // Initial state: aria-label is 'Voir la traduction' (not yet flipped)
    const flipButton = screen.getByLabelText(/voir la traduction/i);
    await user.click(flipButton);

    // After flip, French word 'Pomme' should be in DOM
    expect(screen.getByText('Pomme')).toBeInTheDocument();
  });
});
