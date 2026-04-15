import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { formatDate } from '@/shared/i18n';
import {
  DataTable,
  ErrorBanner,
  FormCheckbox,
  FormField,
  FormSelect,
  FormTextarea,
  LoadingState,
} from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  GAME_DIFFICULTIES,
  GAME_TYPES,
  type GameConfig,
  type GameConfigPayload,
} from './games.service';
import {
  useCreateGameConfig,
  useGameConfig,
  useGameConfigs,
  useUpdateGameConfig,
} from './useGames';

type GameConfigRow = GameConfig & Record<string, unknown>;

const optionalAgeField = z.preprocess((value) => {
  if (value === '' || value === null || value === undefined) {
    return null;
  }

  if (typeof value === 'number') {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? value : parsed;
  }

  return value;
}, z.number().int().min(0, 'games.validation.age').max(18, 'games.validation.age').nullable());

const gameConfigSchema = z
  .object({
    game_type: z.enum(GAME_TYPES, {
      message: 'games.validation.gameType',
    }),
    title: z.string().trim().min(1, 'games.validation.title'),
    title_ar: z.string().trim().max(300, 'games.validation.localizedTitle').optional(),
    title_fr: z.string().trim().max(300, 'games.validation.localizedTitle').optional(),
    subject: z.string().trim().max(50, 'games.validation.subject').optional(),
    difficulty: z.enum(GAME_DIFFICULTIES, {
      message: 'games.validation.difficulty',
    }),
    target_age_min: optionalAgeField,
    target_age_max: optionalAgeField,
    config_json: z
      .string()
      .trim()
      .min(2, 'games.validation.config')
      .refine((value) => {
        try {
          const parsed = JSON.parse(value) as unknown;
          return typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed);
        } catch {
          return false;
        }
      }, 'games.validation.config'),
    reward_stars: z.coerce.number().int().min(0, 'games.validation.reward'),
    reward_xp: z.coerce.number().int().min(0, 'games.validation.reward'),
    is_active: z.boolean(),
  })
  .refine(
    (values) => {
      const minAge =
        typeof values.target_age_min === 'number' && !Number.isNaN(values.target_age_min)
          ? values.target_age_min
          : null;
      const maxAge =
        typeof values.target_age_max === 'number' && !Number.isNaN(values.target_age_max)
          ? values.target_age_max
          : null;

      return minAge === null || maxAge === null || minAge <= maxAge;
    },
    {
      message: 'games.validation.ageRange',
      path: ['target_age_max'],
    },
  );

type GameConfigFormValues = z.infer<typeof gameConfigSchema>;

function getAgeValue(value: GameConfigFormValues['target_age_min']): number | null {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }

  return value;
}

function buildDefaultValues(config?: GameConfig | null): GameConfigFormValues {
  return {
    game_type: (config?.game_type as (typeof GAME_TYPES)[number]) || 'memory_match',
    title: config?.title ?? '',
    title_ar: config?.title_ar ?? '',
    title_fr: config?.title_fr ?? '',
    subject: config?.subject ?? '',
    difficulty: (config?.difficulty as (typeof GAME_DIFFICULTIES)[number]) || 'easy',
    target_age_min: config?.target_age_min ?? null,
    target_age_max: config?.target_age_max ?? null,
    config_json: JSON.stringify(config?.config ?? { pairs: [] }, null, 2),
    reward_stars: config?.reward_stars ?? 10,
    reward_xp: config?.reward_xp ?? 15,
    is_active: config?.is_active ?? true,
  };
}

export function GameConfigsPage() {
  const { t, i18n } = useTranslation();
  const [filterType, setFilterType] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState('');
  const [filterSubject, setFilterSubject] = useState('');
  const [filterActive, setFilterActive] = useState('');
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [formMessage, setFormMessage] = useState<string | null>(null);

  const filters = useMemo(
    () => ({
      game_type: filterType || undefined,
      difficulty: filterDifficulty || undefined,
      subject: filterSubject || undefined,
      is_active: filterActive === '' ? undefined : filterActive === 'true',
    }),
    [filterActive, filterDifficulty, filterSubject, filterType],
  );

  const configsQuery = useGameConfigs(filters);
  const createConfigMutation = useCreateGameConfig();
  const updateConfigMutation = useUpdateGameConfig();
  const selectedConfigQuery = useGameConfig(selectedConfigId, Boolean(selectedConfigId));
  const items: GameConfigRow[] = useMemo(
    () => (configsQuery.data?.pages.flatMap((page) => page.data) ?? []) as GameConfigRow[],
    [configsQuery.data],
  );

  const methods = useForm<GameConfigFormValues>({
    resolver: zodResolver(gameConfigSchema) as Resolver<GameConfigFormValues>,
    defaultValues: buildDefaultValues(),
  });

  useEffect(() => {
    if (!selectedConfigId) {
      methods.reset(buildDefaultValues());
      return;
    }

    if (selectedConfigQuery.data) {
      methods.reset(buildDefaultValues(selectedConfigQuery.data));
    }
  }, [methods, selectedConfigId, selectedConfigQuery.data]);

  const columns: ColumnDef<GameConfigRow>[] = useMemo(
    () => [
      { key: 'title', header: 'games.table.title' },
      {
        key: 'game_type',
        header: 'games.table.type',
        render: (value) => t(`games.types.${String(value)}`, { defaultValue: String(value) }),
      },
      {
        key: 'difficulty',
        header: 'games.table.difficulty',
        render: (value) =>
          t(`games.difficulties.${String(value)}`, { defaultValue: String(value) }),
      },
      {
        key: 'subject',
        header: 'games.table.subject',
        render: (value) => String(value || '—'),
      },
      {
        key: 'reward_stars',
        header: 'games.table.reward',
        render: (_value, row) => `${row.reward_stars}⭐ / ${row.reward_xp} XP`,
      },
      {
        key: 'updated_at',
        header: 'games.table.updated',
        render: (value, row) => formatDate(String(value || row.created_at), i18n.language),
      },
    ],
    [i18n.language, t],
  );

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          configsQuery.error ??
            selectedConfigQuery.error ??
            createConfigMutation.error ??
            updateConfigMutation.error,
          t('app.error'),
        ),
      [
        configsQuery.error,
        createConfigMutation.error,
        selectedConfigQuery.error,
        t,
        updateConfigMutation.error,
      ],
    ),
  );

  async function handleSubmit(values: GameConfigFormValues) {
    const payload: GameConfigPayload = {
      game_type: values.game_type,
      title: values.title.trim(),
      title_ar: values.title_ar?.trim() || null,
      title_fr: values.title_fr?.trim() || null,
      subject: values.subject?.trim() || null,
      difficulty: values.difficulty,
      target_age_min: getAgeValue(values.target_age_min),
      target_age_max: getAgeValue(values.target_age_max),
      config: JSON.parse(values.config_json) as Record<string, unknown>,
      reward_stars: values.reward_stars,
      reward_xp: values.reward_xp,
      is_active: values.is_active,
    };

    if (selectedConfigId) {
      await updateConfigMutation.mutateAsync({
        gameId: selectedConfigId,
        payload,
      });
      setFormMessage(t('games.updated'));
      return;
    }

    const created = await createConfigMutation.mutateAsync(payload);
    setSelectedConfigId(created.id);
    setFormMessage(t('games.created'));
  }

  function handleResetForm() {
    setSelectedConfigId(null);
    setFormMessage(null);
    methods.reset(buildDefaultValues());
  }

  if (configsQuery.isLoading && !configsQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('games.title')}</h1>
          <p className="page-subtitle">{t('games.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={handleResetForm}>
          {t('games.newConfig')}
        </button>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => {
          const refetches: Array<Promise<unknown>> = [configsQuery.refetch()];

          if (selectedConfigId) {
            refetches.push(selectedConfigQuery.refetch());
          }

          void Promise.all(refetches);
        }}
      />

      <div className="filters-bar" style={{ flexWrap: 'wrap', gap: 8 }}>
        <select
          className="filter-select"
          value={filterType}
          aria-label={t('games.filters.type')}
          onChange={(event) => setFilterType(event.target.value)}
        >
          <option value="">{t('games.filters.allTypes')}</option>
          {GAME_TYPES.map((gameType) => (
            <option key={gameType} value={gameType}>
              {t(`games.types.${gameType}`)}
            </option>
          ))}
        </select>
        <select
          className="filter-select"
          value={filterDifficulty}
          aria-label={t('games.filters.difficulty')}
          onChange={(event) => setFilterDifficulty(event.target.value)}
        >
          <option value="">{t('games.filters.allDifficulties')}</option>
          {GAME_DIFFICULTIES.map((difficulty) => (
            <option key={difficulty} value={difficulty}>
              {t(`games.difficulties.${difficulty}`)}
            </option>
          ))}
        </select>
        <input
          type="text"
          className="filter-input"
          value={filterSubject}
          placeholder={t('games.filters.subjectPlaceholder')}
          onChange={(event) => setFilterSubject(event.target.value)}
        />
        <select
          className="filter-select"
          value={filterActive}
          aria-label={t('games.filters.status')}
          onChange={(event) => setFilterActive(event.target.value)}
        >
          <option value="">{t('games.filters.allStatuses')}</option>
          <option value="true">{t('games.status.active')}</option>
          <option value="false">{t('games.status.inactive')}</option>
        </select>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.3fr) minmax(320px, 0.9fr)',
          gap: 16,
          alignItems: 'start',
          marginTop: 16,
        }}
      >
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{t('games.listTitle')}</h2>
          <DataTable
            columns={columns}
            data={items}
            loading={configsQuery.isLoading}
            emptyMessage="games.empty"
            ariaLabel={t('games.listTitle')}
            onRowClick={(row) => {
              setSelectedConfigId(String(row.id));
              setFormMessage(null);
            }}
          />

          {configsQuery.hasNextPage ? (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void configsQuery.fetchNextPage()}
                disabled={configsQuery.isFetchingNextPage}
              >
                {configsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          ) : null}
        </div>

        <div className="card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 12,
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <div>
              <h2 style={{ margin: 0 }}>
                {selectedConfigId ? t('games.editTitle') : t('games.createTitle')}
              </h2>
              <p style={{ marginBottom: 0, color: 'var(--color-text-secondary)' }}>
                {t('games.formSubtitle')}
              </p>
            </div>
            {formMessage ? (
              <span style={{ color: 'var(--color-success)', fontSize: 13 }}>{formMessage}</span>
            ) : null}
          </div>

          <FormProvider {...methods}>
            <form
              style={{ display: 'grid', gap: 12 }}
              onSubmit={methods.handleSubmit((values) => void handleSubmit(values))}
            >
              <FormSelect<GameConfigFormValues>
                name="game_type"
                label="games.form.gameType"
                options={GAME_TYPES.map((gameType) => ({
                  value: gameType,
                  label: `games.types.${gameType}`,
                }))}
              />
              <FormField<GameConfigFormValues> name="title" label="games.form.title" />
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: 12,
                }}
              >
                <FormField<GameConfigFormValues> name="title_ar" label="games.form.titleAr" />
                <FormField<GameConfigFormValues> name="title_fr" label="games.form.titleFr" />
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: 12,
                }}
              >
                <FormField<GameConfigFormValues> name="subject" label="games.form.subject" />
                <FormSelect<GameConfigFormValues>
                  name="difficulty"
                  label="games.form.difficulty"
                  options={GAME_DIFFICULTIES.map((difficulty) => ({
                    value: difficulty,
                    label: `games.difficulties.${difficulty}`,
                  }))}
                />
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: 12,
                }}
              >
                <FormField<GameConfigFormValues>
                  name="target_age_min"
                  label="games.form.targetAgeMin"
                  type="number"
                />
                <FormField<GameConfigFormValues>
                  name="target_age_max"
                  label="games.form.targetAgeMax"
                  type="number"
                />
              </div>
              <FormTextarea<GameConfigFormValues>
                name="config_json"
                label="games.form.config"
                rows={10}
              />
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: 12,
                }}
              >
                <FormField<GameConfigFormValues>
                  name="reward_stars"
                  label="games.form.rewardStars"
                  type="number"
                />
                <FormField<GameConfigFormValues>
                  name="reward_xp"
                  label="games.form.rewardXp"
                  type="number"
                />
              </div>
              <FormCheckbox<GameConfigFormValues> name="is_active" label="games.form.isActive" />

              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={
                    createConfigMutation.isPending ||
                    updateConfigMutation.isPending ||
                    selectedConfigQuery.isLoading
                  }
                >
                  {createConfigMutation.isPending || updateConfigMutation.isPending
                    ? t('app.loading')
                    : selectedConfigId
                      ? t('games.saveChanges')
                      : t('games.createConfig')}
                </button>
                <button type="button" className="btn btn-secondary" onClick={handleResetForm}>
                  {t('app.cancel')}
                </button>
              </div>
            </form>
          </FormProvider>
        </div>
      </div>
    </div>
  );
}
