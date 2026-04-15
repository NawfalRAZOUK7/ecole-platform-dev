import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { formatDate } from '@/shared/i18n';
import {
  DataTable,
  EmptyState,
  ErrorBanner,
  FormField,
  FormSelect,
  LoadingState,
  StatCard,
} from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useAwardReward,
  useCreateRewardBadge,
  useMyRewards,
  useRewardBadges,
  useRewardChildren,
  useRewardClasses,
  useRewardClassStudents,
  useRewardHistory,
  useRewardLeaderboard,
  useStudentRewards,
} from './useRewards';
import type {
  RewardBadge,
  RewardHistoryEntry,
  RewardLeaderboardEntry,
  StudentRewards,
} from './rewards.service';
import { xpThresholdForLevel } from './rewards.service';

type RewardHistoryRow = RewardHistoryEntry & Record<string, unknown>;
type RewardLeaderboardRow = RewardLeaderboardEntry & Record<string, unknown>;

const rewardSourceTypes = ['content', 'quiz', 'game', 'coloring', 'login'] as const;

const awardRewardSchema = z
  .object({
    student_id: z.string().uuid('rewards.validation.studentId'),
    event_type: z.string().min(1, 'rewards.validation.eventType'),
    stars: z.coerce.number().int().min(0, 'rewards.validation.nonNegative'),
    xp: z.coerce.number().int().min(0, 'rewards.validation.nonNegative'),
    source_type: z.union([z.enum(rewardSourceTypes), z.literal('')]),
    source_id: z.union([z.string().uuid('rewards.validation.sourceId'), z.literal('')]),
  })
  .refine((value) => value.stars > 0 || value.xp > 0, {
    message: 'rewards.validation.rewardAmount',
    path: ['xp'],
  });

const badgeSchema = z.object({
  code: z
    .string()
    .trim()
    .min(2, 'rewards.validation.badgeCode')
    .max(50, 'rewards.validation.badgeCode'),
  title: z.string().trim().max(120, 'rewards.validation.badgeTitle').optional(),
  icon: z.string().trim().max(12, 'rewards.validation.badgeIcon').optional(),
});

type AwardRewardFormValues = z.infer<typeof awardRewardSchema>;
type BadgeFormValues = z.infer<typeof badgeSchema>;

function buildStudentOptions(
  children: Array<{ student_id: string; student_name: string }>,
  students: Array<{ id: string; full_name: string }>,
) {
  if (children.length > 0) {
    return children.map((child) => ({
      value: child.student_id,
      label: child.student_name,
    }));
  }

  return students.map((student) => ({
    value: student.id,
    label: student.full_name,
  }));
}

function getXpToNextLevel(rewards: StudentRewards) {
  const nextThreshold = xpThresholdForLevel(rewards.level + 1);
  return Math.max(0, nextThreshold - rewards.xp);
}

function getLastActiveLabel(value: string | null, language: string, fallback: string) {
  if (!value) {
    return fallback;
  }

  return formatDate(value, language);
}

export function RewardsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const role = user?.role || '';
  const isStudent = role === 'STD';
  const isParent = role === 'PAR';
  const canManageRewards = ['TCH', 'ADM', 'DIR', 'SUP', 'SYS'].includes(role);
  const canCreateBadges = role === 'ADM';

  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [leaderboardLimit, setLeaderboardLimit] = useState(10);
  const [awardSuccess, setAwardSuccess] = useState<string | null>(null);
  const [badgeSuccess, setBadgeSuccess] = useState<string | null>(null);

  const myRewardsQuery = useMyRewards(isStudent);
  const classesQuery = useRewardClasses(canManageRewards);
  const classStudentsQuery = useRewardClassStudents(
    selectedClassId,
    canManageRewards && Boolean(selectedClassId),
  );
  const childrenQuery = useRewardChildren(isParent);
  const activeStudentId = isStudent ? user?.id || '' : selectedStudentId;
  const studentRewardsQuery = useStudentRewards(
    activeStudentId,
    !isStudent && Boolean(activeStudentId),
  );
  const historyQuery = useRewardHistory(
    activeStudentId,
    Boolean(isStudent ? user?.id : activeStudentId),
  );
  const leaderboardQuery = useRewardLeaderboard(
    selectedClassId,
    leaderboardLimit,
    Boolean(selectedClassId),
  );
  const badgesQuery = useRewardBadges(true);
  const awardRewardMutation = useAwardReward();
  const createBadgeMutation = useCreateRewardBadge();

  const awardMethods = useForm<AwardRewardFormValues>({
    resolver: zodResolver(awardRewardSchema) as Resolver<AwardRewardFormValues>,
    defaultValues: {
      student_id: '',
      event_type: '',
      stars: 0,
      xp: 0,
      source_type: '',
      source_id: '',
    },
  });
  const badgeMethods = useForm<BadgeFormValues>({
    resolver: zodResolver(badgeSchema) as Resolver<BadgeFormValues>,
    defaultValues: {
      code: '',
      title: '',
      icon: '',
    },
  });

  const rewardsData = isStudent ? myRewardsQuery.data : studentRewardsQuery.data;
  const historyRows: RewardHistoryRow[] = useMemo(
    () => (historyQuery.data ?? []) as RewardHistoryRow[],
    [historyQuery.data],
  );
  const leaderboardRows: RewardLeaderboardRow[] = useMemo(
    () => (leaderboardQuery.data ?? []) as RewardLeaderboardRow[],
    [leaderboardQuery.data],
  );
  const badgeCatalog = badgesQuery.data ?? [];
  const classOptions = classesQuery.data ?? [];
  const selectableStudents = useMemo(
    () => buildStudentOptions(childrenQuery.data ?? [], classStudentsQuery.data ?? []),
    [childrenQuery.data, classStudentsQuery.data],
  );

  useEffect(() => {
    if (canManageRewards && !selectedClassId && classOptions.length > 0) {
      setSelectedClassId(classOptions[0].id);
    }
  }, [canManageRewards, classOptions, selectedClassId]);

  useEffect(() => {
    if (isParent && !selectedStudentId && (childrenQuery.data?.length ?? 0) > 0) {
      setSelectedStudentId(childrenQuery.data?.[0].student_id ?? '');
    }
  }, [childrenQuery.data, isParent, selectedStudentId]);

  useEffect(() => {
    if (canManageRewards && !selectedStudentId && (classStudentsQuery.data?.length ?? 0) > 0) {
      setSelectedStudentId(classStudentsQuery.data?.[0].id ?? '');
    }
  }, [canManageRewards, classStudentsQuery.data, selectedStudentId]);

  useEffect(() => {
    if (!activeStudentId) {
      return;
    }

    awardMethods.setValue('student_id', activeStudentId, {
      shouldDirty: false,
      shouldValidate: false,
    });
  }, [activeStudentId, awardMethods]);

  const historyColumns: ColumnDef<RewardHistoryRow>[] = useMemo(
    () => [
      {
        key: 'created_at',
        header: 'rewards.history.date',
        render: (value) => formatDate(String(value), i18n.language),
      },
      {
        key: 'event_type',
        header: 'rewards.history.event',
        render: (value) => t(`rewards.events.${String(value)}`, { defaultValue: String(value) }),
      },
      {
        key: 'stars_earned',
        header: 'rewards.stats.stars',
        render: (value) => `+${String(value)}`,
      },
      {
        key: 'xp_earned',
        header: 'rewards.stats.xp',
        render: (value) => `+${String(value)}`,
      },
      {
        key: 'source_type',
        header: 'rewards.history.source',
        render: (value) =>
          value
            ? t(`rewards.sources.${String(value)}`, {
                defaultValue: String(value),
              })
            : t('rewards.history.none'),
      },
    ],
    [i18n.language, t],
  );

  const leaderboardColumns: ColumnDef<RewardLeaderboardRow>[] = useMemo(
    () => [
      { key: 'rank', header: 'rewards.leaderboard.rank' },
      { key: 'student_name', header: 'rewards.leaderboard.student' },
      { key: 'stars', header: 'rewards.stats.stars' },
      { key: 'level', header: 'rewards.stats.level' },
    ],
    [],
  );

  const bannerError = useMemo(
    () =>
      toBannerError(
        myRewardsQuery.error ??
          studentRewardsQuery.error ??
          historyQuery.error ??
          leaderboardQuery.error ??
          badgesQuery.error ??
          classesQuery.error ??
          classStudentsQuery.error ??
          childrenQuery.error ??
          awardRewardMutation.error ??
          createBadgeMutation.error,
        t('app.error'),
      ),
    [
      awardRewardMutation.error,
      badgesQuery.error,
      childrenQuery.error,
      classStudentsQuery.error,
      classesQuery.error,
      createBadgeMutation.error,
      historyQuery.error,
      leaderboardQuery.error,
      myRewardsQuery.error,
      studentRewardsQuery.error,
      t,
    ],
  );
  const dismissibleError = useDismissibleError(bannerError);

  async function handleAwardSubmit(values: AwardRewardFormValues) {
    const payload = {
      student_id: values.student_id,
      event_type: values.event_type.trim(),
      stars: values.stars,
      xp: values.xp,
      source_type: values.source_type || null,
      source_id: values.source_id || null,
    };

    const response = await awardRewardMutation.mutateAsync(payload);
    setAwardSuccess(
      t('rewards.awardSuccess', {
        count: response.newly_earned_badges.length,
      }),
    );
    awardMethods.reset({
      student_id: values.student_id,
      event_type: '',
      stars: 0,
      xp: 0,
      source_type: '',
      source_id: '',
    });
  }

  async function handleCreateBadge(values: BadgeFormValues) {
    await createBadgeMutation.mutateAsync({
      code: values.code.trim(),
      title: values.title?.trim() || null,
      icon: values.icon?.trim() || null,
    });
    setBadgeSuccess(t('rewards.badgeCreateSuccess'));
    badgeMethods.reset();
  }

  const isInitialLoading =
    (isStudent && myRewardsQuery.isLoading) ||
    (!isStudent && activeStudentId !== '' && studentRewardsQuery.isLoading);

  if (isInitialLoading && !rewardsData) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rewards.title')}</h1>
          <p className="page-subtitle">{t('rewards.subtitle')}</p>
        </div>
        {rewardsData ? (
          <div className="page-actions">
            <span className="badge">⭐ {rewardsData.stars}</span>
            <span className="badge">XP {rewardsData.xp}</span>
            <span className="badge">
              {t('rewards.stats.level')} {rewardsData.level}
            </span>
          </div>
        ) : null}
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => {
          const refetches: Array<Promise<unknown>> = [badgesQuery.refetch()];

          if (isStudent) {
            refetches.push(myRewardsQuery.refetch(), historyQuery.refetch());
          }

          if (!isStudent && activeStudentId) {
            refetches.push(studentRewardsQuery.refetch(), historyQuery.refetch());
          }

          if (selectedClassId) {
            refetches.push(leaderboardQuery.refetch());
          }

          if (canManageRewards) {
            refetches.push(classesQuery.refetch());
            if (selectedClassId) {
              refetches.push(classStudentsQuery.refetch());
            }
          }

          if (isParent) {
            refetches.push(childrenQuery.refetch());
          }

          void Promise.all(refetches);
        }}
      />

      {!isStudent ? (
        <div className="filters-bar" style={{ flexWrap: 'wrap', gap: 8 }}>
          {classOptions.length > 0 ? (
            <select
              className="filter-select"
              value={selectedClassId}
              aria-label={t('rewards.filters.class')}
              onChange={(event) => {
                setSelectedClassId(event.target.value);
                setSelectedStudentId('');
              }}
            >
              {classOptions.map((classItem) => (
                <option key={classItem.id} value={classItem.id}>
                  {classItem.name}
                </option>
              ))}
            </select>
          ) : canManageRewards ? (
            <input
              type="text"
              className="filter-input"
              value={selectedClassId}
              placeholder={t('rewards.filters.classPlaceholder')}
              onChange={(event) => setSelectedClassId(event.target.value)}
            />
          ) : null}

          {selectableStudents.length > 0 ? (
            <select
              className="filter-select"
              value={selectedStudentId}
              aria-label={t('rewards.filters.student')}
              onChange={(event) => setSelectedStudentId(event.target.value)}
            >
              {selectableStudents.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              className="filter-input"
              value={selectedStudentId}
              placeholder={t('rewards.filters.studentPlaceholder')}
              onChange={(event) => setSelectedStudentId(event.target.value)}
            />
          )}

          <input
            type="number"
            min="3"
            max="50"
            className="filter-input"
            value={leaderboardLimit}
            aria-label={t('rewards.filters.limit')}
            onChange={(event) => setLeaderboardLimit(Number(event.target.value) || 10)}
          />
        </div>
      ) : null}

      {rewardsData ? (
        <>
          <div className="stats-grid" style={{ marginTop: 16 }}>
            <StatCard label="rewards.stats.stars" value={rewardsData.stars} icon="⭐" />
            <StatCard label="rewards.stats.xp" value={rewardsData.xp} icon="⚡" />
            <StatCard label="rewards.stats.level" value={rewardsData.level} icon="🏅" />
            <StatCard label="rewards.stats.streak" value={rewardsData.streak_days} icon="🔥" />
            <StatCard
              label="rewards.stats.nextLevel"
              value={getXpToNextLevel(rewardsData)}
              icon="⬆️"
            />
            <StatCard
              label="rewards.stats.lastActivity"
              value={getLastActiveLabel(
                rewardsData.last_activity_at,
                i18n.language,
                t('rewards.history.none'),
              )}
              icon="🕒"
            />
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: 16,
                alignItems: 'center',
                flexWrap: 'wrap',
              }}
            >
              <div>
                <h2 style={{ marginTop: 0 }}>{t('rewards.progress.title')}</h2>
                <p style={{ marginBottom: 0, color: 'var(--color-text-secondary)' }}>
                  {t('rewards.progress.subtitle')}
                </p>
              </div>
              <strong>{Math.round(rewardsData.level_progress)}%</strong>
            </div>
            <div
              style={{
                width: '100%',
                height: 12,
                background: 'var(--color-bg-muted)',
                borderRadius: 999,
                overflow: 'hidden',
                marginTop: 16,
              }}
            >
              <div
                style={{
                  width: `${Math.max(0, Math.min(100, rewardsData.level_progress))}%`,
                  height: '100%',
                  background: 'var(--color-primary)',
                }}
              />
            </div>
            <div style={{ marginTop: 16 }}>
              <h3>{t('rewards.badgesEarned')}</h3>
              {rewardsData.badges.length === 0 ? (
                <EmptyState message={t('rewards.badgesEmpty')} icon="🏅" />
              ) : (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {rewardsData.badges.map((badge) => (
                    <span key={badge} className="badge">
                      {badge}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        <EmptyState message={t('rewards.noStudentSelected')} icon="⭐" />
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 16,
          marginTop: 16,
        }}
      >
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t('rewards.history.title')}</h2>
          <DataTable
            columns={historyColumns}
            data={historyRows}
            loading={historyQuery.isLoading}
            emptyMessage="rewards.history.empty"
            ariaLabel={t('rewards.history.title')}
          />
        </div>

        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t('rewards.leaderboard.title')}</h2>
          {selectedClassId ? (
            <DataTable
              columns={leaderboardColumns}
              data={leaderboardRows}
              loading={leaderboardQuery.isLoading}
              emptyMessage="rewards.leaderboard.empty"
              ariaLabel={t('rewards.leaderboard.title')}
            />
          ) : (
            <EmptyState message={t('rewards.leaderboard.prompt')} icon="🏆" />
          )}
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 16,
          marginTop: 16,
        }}
      >
        {canManageRewards ? (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <div>
                <h2 style={{ marginTop: 0 }}>{t('rewards.awardTitle')}</h2>
                <p style={{ color: 'var(--color-text-secondary)' }}>{t('rewards.awardSubtitle')}</p>
              </div>
              {awardSuccess ? (
                <span style={{ color: 'var(--color-success)', fontSize: 13 }}>{awardSuccess}</span>
              ) : null}
            </div>

            <FormProvider {...awardMethods}>
              <form
                style={{ display: 'grid', gap: 12 }}
                onSubmit={awardMethods.handleSubmit((values) => void handleAwardSubmit(values))}
              >
                {selectableStudents.length > 0 ? (
                  <FormSelect<AwardRewardFormValues>
                    name="student_id"
                    label="rewards.filters.student"
                    options={selectableStudents}
                  />
                ) : (
                  <FormField<AwardRewardFormValues>
                    name="student_id"
                    label="rewards.filters.student"
                  />
                )}
                <FormField<AwardRewardFormValues>
                  name="event_type"
                  label="rewards.forms.eventType"
                />
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: 12,
                  }}
                >
                  <FormField<AwardRewardFormValues>
                    name="stars"
                    label="rewards.forms.stars"
                    type="number"
                  />
                  <FormField<AwardRewardFormValues>
                    name="xp"
                    label="rewards.forms.xp"
                    type="number"
                  />
                </div>
                <FormSelect<AwardRewardFormValues>
                  name="source_type"
                  label="rewards.forms.sourceType"
                  placeholder="rewards.forms.noneOption"
                  options={rewardSourceTypes.map((sourceType) => ({
                    value: sourceType,
                    label: `rewards.sources.${sourceType}`,
                  }))}
                />
                <FormField<AwardRewardFormValues> name="source_id" label="rewards.forms.sourceId" />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={awardRewardMutation.isPending}
                >
                  {awardRewardMutation.isPending ? t('app.loading') : t('rewards.submitAward')}
                </button>
              </form>
            </FormProvider>
          </div>
        ) : null}

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
            <div>
              <h2 style={{ marginTop: 0 }}>{t('rewards.catalogTitle')}</h2>
              <p style={{ color: 'var(--color-text-secondary)' }}>{t('rewards.catalogSubtitle')}</p>
            </div>
            {badgeSuccess ? (
              <span style={{ color: 'var(--color-success)', fontSize: 13 }}>{badgeSuccess}</span>
            ) : null}
          </div>

          {badgeCatalog.length === 0 && !badgesQuery.isLoading ? (
            <EmptyState message={t('rewards.catalogEmpty')} icon="🏅" />
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: 12,
                marginBottom: canCreateBadges ? 20 : 0,
              }}
            >
              {badgeCatalog.map((badge: RewardBadge) => (
                <div key={badge.code} className="card" style={{ padding: 12 }}>
                  <div style={{ fontSize: 20, marginBottom: 8 }}>{badge.icon || '🏅'}</div>
                  <strong>{badge.title || badge.code}</strong>
                  <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                    {badge.code}
                  </div>
                </div>
              ))}
            </div>
          )}

          {canCreateBadges ? (
            <FormProvider {...badgeMethods}>
              <form
                style={{ display: 'grid', gap: 12 }}
                onSubmit={badgeMethods.handleSubmit((values) => void handleCreateBadge(values))}
              >
                <FormField<BadgeFormValues> name="code" label="rewards.forms.badgeCode" />
                <FormField<BadgeFormValues> name="title" label="rewards.forms.badgeTitle" />
                <FormField<BadgeFormValues> name="icon" label="rewards.forms.badgeIcon" />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={createBadgeMutation.isPending}
                >
                  {createBadgeMutation.isPending ? t('app.loading') : t('rewards.createBadge')}
                </button>
              </form>
            </FormProvider>
          ) : null}
        </div>
      </div>
    </div>
  );
}
