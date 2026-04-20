import { useTranslation } from 'react-i18next';

interface GameCompleteBannerProps {
  success: boolean;
  starsEarned: number;
  xpEarned: number;
  loading?: boolean;
  onReplay: () => void;
  onExit: () => void;
}

export function GameCompleteBanner({
  success,
  starsEarned,
  xpEarned,
  loading,
  onReplay,
  onExit,
}: GameCompleteBannerProps) {
  const { t } = useTranslation();

  return (
    <div
      style={{
        marginTop: 24,
        padding: 24,
        borderRadius: 16,
        background: success
          ? 'linear-gradient(135deg, #fef3c7, #fde68a)'
          : 'linear-gradient(135deg, #fee2e2, #fecaca)',
        textAlign: 'center',
        border: '2px solid',
        borderColor: success ? '#f59e0b' : '#ef4444',
      }}
      role="alert"
    >
      <div style={{ fontSize: 64, marginBottom: 8 }}>{success ? '🎉' : '⏰'}</div>
      <h2 style={{ margin: '0 0 12px', fontSize: 24, color: 'var(--color-text)' }}>
        {success
          ? t('studentGames.congrats', 'Bravo !')
          : t('studentGames.timedOut', 'Temps écoulé')}
      </h2>
      {success ? (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 36 }}>⭐</div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>+{starsEarned}</div>
          </div>
          <div>
            <div style={{ fontSize: 36 }}>✨</div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>+{xpEarned} XP</div>
          </div>
        </div>
      ) : (
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 16 }}>
          {t('studentGames.tryAgain', 'Essaie encore !')}
        </p>
      )}
      {loading ? (
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
          {t('app.loading', 'Chargement...')}
        </p>
      ) : null}
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 8 }}>
        <button type="button" className="btn btn-primary" onClick={onReplay}>
          🔄 {t('studentGames.replay', 'Rejouer')}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onExit}>
          {t('studentGames.backToGames', 'Retour aux jeux')}
        </button>
      </div>
    </div>
  );
}
