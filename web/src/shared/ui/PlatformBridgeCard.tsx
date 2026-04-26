/**
 * Cross-platform bridge card — informs users that a feature
 * is available on the other platform (web or mobile) with an
 * attractive design and a brief explanation of why.
 *
 * Usage:
 *   <PlatformBridgeCard
 *     targetPlatform="mobile"
 *     title="تلوين تفاعلي"
 *     description="هذا النشاط مصمم للأجهزة اللوحية — استخدم التطبيق لتجربة تلوين تفاعلية بلمسة إصبعك."
 *     icon="📱"
 *   />
 */

import { useTranslation } from 'react-i18next';

type BridgePlatform = 'web' | 'mobile';

interface PlatformBridgeCardProps {
  targetPlatform: BridgePlatform;
  title: string;
  description: string;
  icon?: string;
}

export function PlatformBridgeCard({
  targetPlatform,
  title,
  description,
  icon,
}: PlatformBridgeCardProps) {
  const { t } = useTranslation();
  const isMobile = targetPlatform === 'mobile';

  const platformLabel = isMobile
    ? t('bridge.availableOnMobile', { defaultValue: 'متوفر على التطبيق' })
    : t('bridge.availableOnWeb', { defaultValue: 'متوفر على الويب' });

  const platformEmoji = icon ?? (isMobile ? '📱' : '💻');

  const accentColor = isMobile
    ? 'var(--color-secondary, #7C3AED)'
    : 'var(--color-primary, #2563EB)';

  return (
    <div
      className="platform-bridge-card"
      dir="rtl"
      style={{
        display: 'flex',
        gap: 16,
        padding: '16px 20px',
        borderRadius: 16,
        border: `1.5px solid color-mix(in srgb, ${accentColor} 25%, transparent)`,
        background: `color-mix(in srgb, ${accentColor} 6%, transparent)`,
        marginBottom: 16,
        alignItems: 'flex-start',
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 14,
          background: `color-mix(in srgb, ${accentColor} 12%, transparent)`,
          border: `1px solid color-mix(in srgb, ${accentColor} 20%, transparent)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 28,
          flexShrink: 0,
        }}
      >
        {platformEmoji}
      </div>

      {/* Text content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Platform badge */}
        <span
          style={{
            display: 'inline-block',
            padding: '2px 10px',
            borderRadius: 8,
            background: `color-mix(in srgb, ${accentColor} 15%, transparent)`,
            color: accentColor,
            fontSize: 11,
            fontWeight: 700,
            marginBottom: 8,
          }}
        >
          {platformLabel}
        </span>

        {/* Title */}
        <div
          style={{
            fontSize: '0.95rem',
            fontWeight: 700,
            color: 'var(--color-text)',
            marginBottom: 4,
          }}
        >
          {title}
        </div>

        {/* Description */}
        <div
          style={{
            fontSize: '0.82rem',
            color: 'var(--color-text-secondary)',
            lineHeight: 1.6,
          }}
        >
          {description}
        </div>
      </div>
    </div>
  );
}
