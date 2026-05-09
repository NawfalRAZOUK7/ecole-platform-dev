import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useMyRewards } from '@/features/rewards/useRewards';
import { xpThresholdForLevel } from '@/features/rewards/rewards.service';
import { useAgeTheme } from '@/shared/hooks/useAgeTheme';
import { LoadingState } from '@/shared/ui/LoadingState';

export function StudentHomePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const ageTier = useAgeTheme();
  const rewardsQuery = useMyRewards();
  const rewards = rewardsQuery.data;

  const firstName = user?.full_name?.split(' ')[0] ?? user?.full_name ?? '';

  const xpForCurrentLevel = rewards ? xpThresholdForLevel(rewards.level) : 0;
  const xpForNextLevel = rewards ? xpThresholdForLevel(rewards.level + 1) : 100;
  const xpInLevel = rewards ? rewards.xp - xpForCurrentLevel : 0;
  const xpNeeded = xpForNextLevel - xpForCurrentLevel;
  const levelProgress =
    xpNeeded > 0 ? Math.min(100, Math.round((xpInLevel / xpNeeded) * 100)) : 100;

  if (rewardsQuery.isLoading) return <LoadingState />;

  return (
    <div className="page kids-home">
      <h1 className="kids-home__greeting">
        {ageTier === 'maternelle'
          ? t('studentHome.greetingYoung', {
              name: firstName,
              defaultValue: `مرحبا ${firstName}! 🌟🎉`,
            })
          : t('studentHome.greeting', {
              name: firstName,
              defaultValue: `مرحبا، ${firstName}! 👋`,
            })}
      </h1>

      {/* Mascot — visible only for maternelle */}
      <div className="kids-mascot" aria-hidden="true">
        <div className="kids-mascot__bubble">
          <span className="kids-mascot__emoji">🦊</span>
          <span className="kids-mascot__text">
            {t('studentHome.mascotMessage', {
              defaultValue: "Let's learn together today!",
            })}
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div className="kids-stat-cards">
        <div className="kids-stat-card kids-stat-card--xp">
          <span className="kids-stat-card__icon">✨</span>
          <span className="kids-stat-card__value">{rewards?.xp ?? 0}</span>
          <span className="kids-stat-card__label">XP</span>
        </div>
        <div className="kids-stat-card kids-stat-card--stars">
          <span className="kids-stat-card__icon">⭐</span>
          <span className="kids-stat-card__value">{rewards?.stars ?? 0}</span>
          <span className="kids-stat-card__label">{t('rewards.stats.stars', 'Stars')}</span>
        </div>
        <div className="kids-stat-card kids-stat-card--streak">
          <span className="kids-stat-card__icon">🔥</span>
          <span className="kids-stat-card__value">{rewards?.streakDays ?? 0}</span>
          <span className="kids-stat-card__label">{t('rewards.stats.streak', 'Day streak')}</span>
        </div>
        <div className="kids-stat-card kids-stat-card--level">
          <span className="kids-stat-card__icon">🏅</span>
          <span className="kids-stat-card__value">{rewards?.level ?? 1}</span>
          <span className="kids-stat-card__label">{t('rewards.stats.level', 'Level')}</span>
          {rewards && (
            <div className="kids-xp-bar-wrap" style={{ marginTop: 6 }}>
              <div
                className="kids-xp-bar-fill"
                style={{ width: `${levelProgress}%` }}
                role="progressbar"
                aria-valuenow={levelProgress}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
          )}
        </div>
      </div>

      {/* Call-to-action buttons */}
      <div className="kids-section-title">
        <span>🚀</span>
        {t('studentHome.readyToLearn', 'Ready to learn?')}
      </div>
      <div className="kids-cta-row">
        <button
          type="button"
          className="kids-cta-btn kids-cta-btn--primary"
          onClick={() => navigate('/student/content')}
        >
          <span className="kids-cta-btn__icon">📚</span>
          {t('studentHome.startLearning', 'Start Learning')}
        </button>
        <button
          type="button"
          className="kids-cta-btn kids-cta-btn--secondary"
          onClick={() => navigate('/student/quizzes')}
        >
          <span className="kids-cta-btn__icon">📝</span>
          {t('studentHome.takeQuiz', 'Take a Quiz')}
        </button>
        <button
          type="button"
          className="kids-cta-btn kids-cta-btn--writing"
          onClick={() => navigate('/student/writing')}
        >
          <span className="kids-cta-btn__icon">✏️</span>
          {t('studentHome.writeStory', 'Write a Story')}
        </button>
      </div>

      {/* Badges section */}
      {rewards && rewards.badges.length > 0 && (
        <>
          <div className="kids-section-title">
            <span>🏆</span>
            {t('studentHome.myBadges', 'My Badges')}
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
            {rewards.badges.slice(0, 8).map((badge) => (
              <div
                key={badge}
                style={{
                  background: 'var(--color-surface)',
                  border: '2px solid var(--color-border)',
                  borderRadius: 14,
                  padding: '8px 14px',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: 'var(--color-primary)',
                }}
              >
                🎖️ {badge}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Quick links */}
      <div className="kids-section-title">
        <span>⚡</span>
        {t('studentHome.quickLinks', 'Quick Links')}
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
          gap: 12,
          marginBottom: 24,
        }}
      >
        {[
          { icon: '📊', label: t('nav.progress', 'Progress'), path: '/progress' },
          { icon: '🏆', label: t('nav.myRewards', 'Rewards'), path: '/rewards' },
          { icon: '📋', label: t('nav.submissions', 'Submissions'), path: '/submissions' },
          { icon: '🎯', label: t('nav.skills', 'Skills'), path: '/skills' },
          { icon: '📢', label: t('nav.announcements', 'News'), path: '/announcements' },
          { icon: '🗓️', label: t('nav.calendar', 'Calendar'), path: '/calendar' },
        ].map((link) => (
          <button
            key={link.path}
            type="button"
            onClick={() => navigate(link.path)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 6,
              padding: '14px 8px',
              background: 'var(--color-surface)',
              border: '2px solid var(--color-border)',
              borderRadius: 16,
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--color-text)',
              transition: 'transform 0.15s ease, box-shadow 0.15s ease',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-2px)';
              (e.currentTarget as HTMLButtonElement).style.boxShadow =
                '0 6px 20px rgba(124,58,237,0.12)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.transform = '';
              (e.currentTarget as HTMLButtonElement).style.boxShadow = '';
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>{link.icon}</span>
            <span>{link.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
