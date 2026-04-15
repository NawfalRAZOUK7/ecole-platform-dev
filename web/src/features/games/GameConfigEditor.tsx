import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useFieldArray, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { ErrorBanner, FormCheckbox, FormField, FormSelect, FormTextarea } from '@/shared/ui';
import { useCreateGameConfig, useUpdateGameConfig, type GameConfigInput } from './useGames';
import { GAME_DIFFICULTIES, GAME_TYPES, type GameConfig } from './types';

interface GameConfigEditorProps {
  config?: GameConfig | null;
  embedded?: boolean;
  onSaved?: (config: GameConfig) => void;
  onCancel?: () => void;
}

interface UnknownRecord {
  [key: string]: unknown;
}

interface MemoryMatchPairForm {
  front: string;
  back: string;
  imageUrl: string;
}

interface SortingCategoryForm {
  name: string;
  itemsText: string;
}

interface VocabularyCardForm {
  wordAr: string;
  wordFr: string;
  imageUrl: string;
  audioUrl: string;
}

function parseOptionalNumber(value: unknown): number | null | unknown {
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
}

const optionalAgeField = z.preprocess(
  parseOptionalNumber,
  z.number().int().min(0, 'games.validation.age').max(18, 'games.validation.age').nullable(),
);

const limitedStringField = z.string().trim().max(500, 'games.validation.url');

const gameConfigSchema = z
  .object({
    gameType: z.enum(GAME_TYPES, {
      message: 'games.validation.gameType',
    }),
    title: z.string().trim().min(1, 'games.validation.title').max(300, 'games.validation.title'),
    titleAr: z.string().trim().max(300, 'games.validation.localizedTitle'),
    titleFr: z.string().trim().max(300, 'games.validation.localizedTitle'),
    subject: z.string().trim().max(50, 'games.validation.subject'),
    difficulty: z.enum(GAME_DIFFICULTIES, {
      message: 'games.validation.difficulty',
    }),
    targetAgeMin: optionalAgeField,
    targetAgeMax: optionalAgeField,
    rewardStars: z.coerce.number().int().min(0, 'games.validation.reward'),
    rewardXp: z.coerce.number().int().min(0, 'games.validation.reward'),
    isActive: z.boolean(),
    memoryMatch: z.object({
      gridCols: z.coerce
        .number()
        .int()
        .min(1, 'games.validation.grid')
        .max(12, 'games.validation.grid'),
      gridRows: z.coerce
        .number()
        .int()
        .min(1, 'games.validation.grid')
        .max(12, 'games.validation.grid'),
      timeLimit: z.coerce.number().int().min(0, 'games.validation.timeLimit'),
      pairs: z.array(
        z.object({
          front: z.string().trim(),
          back: z.string().trim(),
          imageUrl: limitedStringField,
        }),
      ),
    }),
    sorting: z.object({
      categories: z.array(
        z.object({
          name: z.string().trim(),
          itemsText: z.string().trim(),
        }),
      ),
    }),
    vocabularyCards: z.object({
      cards: z.array(
        z.object({
          wordAr: z.string().trim(),
          wordFr: z.string().trim(),
          imageUrl: limitedStringField,
          audioUrl: limitedStringField,
        }),
      ),
    }),
  })
  .superRefine((values, context) => {
    if (
      values.targetAgeMin !== null &&
      values.targetAgeMax !== null &&
      values.targetAgeMin > values.targetAgeMax
    ) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'games.validation.ageRange',
        path: ['targetAgeMax'],
      });
    }

    if (values.gameType === 'memory_match') {
      if (values.memoryMatch.pairs.length === 0) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'games.validation.pairsRequired',
          path: ['memoryMatch', 'pairs'],
        });
      }

      values.memoryMatch.pairs.forEach((pair, index) => {
        if (!pair.front.trim()) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'games.validation.pairText',
            path: ['memoryMatch', 'pairs', index, 'front'],
          });
        }
        if (!pair.back.trim()) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'games.validation.pairText',
            path: ['memoryMatch', 'pairs', index, 'back'],
          });
        }
      });
    }

    if (values.gameType === 'sorting') {
      if (values.sorting.categories.length === 0) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'games.validation.categoriesRequired',
          path: ['sorting', 'categories'],
        });
      }

      values.sorting.categories.forEach((category, index) => {
        if (!category.name.trim()) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'games.validation.categoryName',
            path: ['sorting', 'categories', index, 'name'],
          });
        }
        if (!category.itemsText.trim()) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'games.validation.categoryItems',
            path: ['sorting', 'categories', index, 'itemsText'],
          });
        }
      });
    }

    if (values.gameType === 'vocabulary_cards') {
      if (values.vocabularyCards.cards.length === 0) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'games.validation.cardsRequired',
          path: ['vocabularyCards', 'cards'],
        });
      }

      values.vocabularyCards.cards.forEach((card, index) => {
        if (!card.wordAr.trim()) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'games.validation.wordAr',
            path: ['vocabularyCards', 'cards', index, 'wordAr'],
          });
        }
        if (!card.wordFr.trim()) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'games.validation.wordFr',
            path: ['vocabularyCards', 'cards', index, 'wordFr'],
          });
        }
      });
    }
  });

type GameConfigFormValues = z.infer<typeof gameConfigSchema>;

const EMPTY_PAIR: MemoryMatchPairForm = { front: '', back: '', imageUrl: '' };
const EMPTY_CATEGORY: SortingCategoryForm = { name: '', itemsText: '' };
const EMPTY_CARD: VocabularyCardForm = { wordAr: '', wordFr: '', imageUrl: '', audioUrl: '' };

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function getRecordArray(value: unknown): UnknownRecord[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord);
}

function getStringValue(record: UnknownRecord, ...keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'string') {
      return value;
    }
  }

  return '';
}

function getNumberValue(record: UnknownRecord, fallback: number, ...keys: string[]): number {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'number' && !Number.isNaN(value)) {
      return value;
    }
  }

  return fallback;
}

function getConfigRecord(config?: GameConfig | null): UnknownRecord {
  return config && isRecord(config.config) ? config.config : {};
}

function parseMemoryMatchPairs(configRecord: UnknownRecord): MemoryMatchPairForm[] {
  const pairs = getRecordArray(configRecord.pairs).map((pair) => ({
    front: getStringValue(pair, 'front'),
    back: getStringValue(pair, 'back'),
    imageUrl: getStringValue(pair, 'imageUrl', 'image_url'),
  }));

  return pairs.length > 0 ? pairs : [EMPTY_PAIR];
}

function parseSortingCategories(configRecord: UnknownRecord): SortingCategoryForm[] {
  const categories = getRecordArray(configRecord.categories).map((category) => {
    const items = Array.isArray(category.items)
      ? category.items.map((item) => String(item)).filter((item) => item.trim().length > 0)
      : [];

    return {
      name: getStringValue(category, 'name'),
      itemsText: items.join('\n'),
    };
  });

  return categories.length > 0 ? categories : [EMPTY_CATEGORY];
}

function parseVocabularyCards(configRecord: UnknownRecord): VocabularyCardForm[] {
  const cards = getRecordArray(configRecord.cards).map((card) => ({
    wordAr: getStringValue(card, 'wordAr', 'word_ar'),
    wordFr: getStringValue(card, 'wordFr', 'word_fr'),
    imageUrl: getStringValue(card, 'imageUrl', 'image_url'),
    audioUrl: getStringValue(card, 'audioUrl', 'audio_url'),
  }));

  return cards.length > 0 ? cards : [EMPTY_CARD];
}

function buildDefaultValues(config?: GameConfig | null): GameConfigFormValues {
  const configRecord = getConfigRecord(config);

  return {
    gameType: config?.gameType ?? 'memory_match',
    title: config?.title ?? '',
    titleAr: config?.titleAr ?? '',
    titleFr: config?.titleFr ?? '',
    subject: config?.subject ?? '',
    difficulty: config?.difficulty ?? 'easy',
    targetAgeMin: config?.targetAgeMin ?? null,
    targetAgeMax: config?.targetAgeMax ?? null,
    rewardStars: config?.rewardStars ?? 10,
    rewardXp: config?.rewardXp ?? 15,
    isActive: config?.isActive ?? true,
    memoryMatch: {
      gridCols: getNumberValue(configRecord, 4, 'gridCols', 'grid_cols'),
      gridRows: getNumberValue(configRecord, 4, 'gridRows', 'grid_rows'),
      timeLimit: getNumberValue(configRecord, 60, 'timeLimit', 'time_limit'),
      pairs: parseMemoryMatchPairs(configRecord),
    },
    sorting: {
      categories: parseSortingCategories(configRecord),
    },
    vocabularyCards: {
      cards: parseVocabularyCards(configRecord),
    },
  };
}

function getAgeValue(value: GameConfigFormValues['targetAgeMin']): number | null {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }

  return value;
}

function splitItems(itemsText: string): string[] {
  return itemsText
    .split('\n')
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function buildConfigPayload(values: GameConfigFormValues): Record<string, unknown> {
  if (values.gameType === 'memory_match') {
    return {
      pairs: values.memoryMatch.pairs.map((pair) => ({
        front: pair.front.trim(),
        back: pair.back.trim(),
        image_url: pair.imageUrl.trim() || null,
      })),
      grid_cols: values.memoryMatch.gridCols,
      grid_rows: values.memoryMatch.gridRows,
      time_limit: values.memoryMatch.timeLimit,
    };
  }

  if (values.gameType === 'sorting') {
    return {
      categories: values.sorting.categories.map((category) => ({
        name: category.name.trim(),
        items: splitItems(category.itemsText),
      })),
    };
  }

  return {
    cards: values.vocabularyCards.cards.map((card) => ({
      word_ar: card.wordAr.trim(),
      word_fr: card.wordFr.trim(),
      image_url: card.imageUrl.trim() || null,
      audio_url: card.audioUrl.trim() || null,
    })),
  };
}

export function GameConfigEditor({
  config = null,
  embedded = false,
  onSaved,
  onCancel,
}: GameConfigEditorProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const createConfigMutation = useCreateGameConfig();
  const updateConfigMutation = useUpdateGameConfig();
  const [formMessage, setFormMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const methods = useForm<GameConfigFormValues>({
    resolver: zodResolver(gameConfigSchema) as Resolver<GameConfigFormValues>,
    defaultValues: buildDefaultValues(config),
  });
  const watchedGameType = methods.watch('gameType');

  const memoryPairsArray = useFieldArray({
    control: methods.control,
    name: 'memoryMatch.pairs',
  });
  const sortingCategoriesArray = useFieldArray({
    control: methods.control,
    name: 'sorting.categories',
  });
  const vocabularyCardsArray = useFieldArray({
    control: methods.control,
    name: 'vocabularyCards.cards',
  });

  useEffect(() => {
    methods.reset(buildDefaultValues(config));
  }, [config, methods]);

  const formError =
    localError ||
    (createConfigMutation.error instanceof Error
      ? createConfigMutation.error.message
      : updateConfigMutation.error instanceof Error
        ? updateConfigMutation.error.message
        : null);
  const isSaving = createConfigMutation.isPending || updateConfigMutation.isPending;

  const gameTypeOptions = useMemo(
    () =>
      GAME_TYPES.map((gameType) => ({
        value: gameType,
        label: `games.types.${gameType}`,
      })),
    [],
  );
  const difficultyOptions = useMemo(
    () =>
      GAME_DIFFICULTIES.map((difficulty) => ({
        value: difficulty,
        label: `games.difficulties.${difficulty}`,
      })),
    [],
  );

  async function handleSubmit(values: GameConfigFormValues) {
    setLocalError(null);
    setFormMessage(null);

    const payload: GameConfigInput = {
      gameType: values.gameType,
      title: values.title.trim(),
      titleAr: values.titleAr.trim() || null,
      titleFr: values.titleFr.trim() || null,
      subject: values.subject.trim() || null,
      difficulty: values.difficulty,
      targetAgeMin: getAgeValue(values.targetAgeMin),
      targetAgeMax: getAgeValue(values.targetAgeMax),
      config: buildConfigPayload(values),
      rewardStars: values.rewardStars,
      rewardXp: values.rewardXp,
      schoolId: config?.schoolId ?? null,
      isActive: values.isActive,
    };

    const savedConfig = config
      ? await updateConfigMutation.mutateAsync({
          gameId: config.id,
          payload,
        })
      : await createConfigMutation.mutateAsync(payload);

    setFormMessage(t(config ? 'games.updated' : 'games.created'));

    if (onSaved) {
      onSaved(savedConfig);
      return;
    }

    navigate(`/teacher/games/${savedConfig.id}`);
  }

  function handleCancel() {
    if (onCancel) {
      onCancel();
      return;
    }

    navigate('/teacher/games');
  }

  const formBody = (
    <>
      <ErrorBanner error={formError} onDismiss={() => setLocalError(null)} />
      {formMessage ? (
        <div
          className="alert alert-success"
          style={{ marginBottom: 16, padding: 12, borderRadius: 8 }}
        >
          {formMessage}
        </div>
      ) : null}

      <FormProvider {...methods}>
        <form
          onSubmit={methods.handleSubmit((values) => void handleSubmit(values))}
          className="card"
          style={{ padding: 20 }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 16,
            }}
          >
            <FormSelect<GameConfigFormValues>
              name="gameType"
              label="games.form.gameType"
              options={gameTypeOptions}
              disabled={isSaving}
            />
            <FormSelect<GameConfigFormValues>
              name="difficulty"
              label="games.form.difficulty"
              options={difficultyOptions}
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="title"
              label="games.form.title"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="titleAr"
              label="games.form.titleAr"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="titleFr"
              label="games.form.titleFr"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="subject"
              label="games.form.subject"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="targetAgeMin"
              label="games.form.targetAgeMin"
              type="number"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="targetAgeMax"
              label="games.form.targetAgeMax"
              type="number"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="rewardStars"
              label="games.form.rewardStars"
              type="number"
              disabled={isSaving}
            />
            <FormField<GameConfigFormValues>
              name="rewardXp"
              label="games.form.rewardXp"
              type="number"
              disabled={isSaving}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <FormCheckbox<GameConfigFormValues>
              name="isActive"
              label="games.form.isActive"
              disabled={isSaving}
            />
          </div>

          {watchedGameType === 'memory_match' ? (
            <section className="card" style={{ marginTop: 20, padding: 16 }}>
              <h3 style={{ marginTop: 0 }}>{t('games.editor.memoryMatchTitle')}</h3>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 16,
                }}
              >
                <FormField<GameConfigFormValues>
                  name="memoryMatch.gridCols"
                  label="games.editor.gridCols"
                  type="number"
                  disabled={isSaving}
                />
                <FormField<GameConfigFormValues>
                  name="memoryMatch.gridRows"
                  label="games.editor.gridRows"
                  type="number"
                  disabled={isSaving}
                />
                <FormField<GameConfigFormValues>
                  name="memoryMatch.timeLimit"
                  label="games.editor.timeLimit"
                  type="number"
                  disabled={isSaving}
                />
              </div>

              <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
                {memoryPairsArray.fields.map((field, index) => (
                  <div
                    key={field.id}
                    className="card"
                    style={{ padding: 16, display: 'grid', gap: 12 }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <strong>{t('games.editor.pairLabel', { index: index + 1 })}</strong>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={isSaving || memoryPairsArray.fields.length === 1}
                        onClick={() => memoryPairsArray.remove(index)}
                      >
                        {t('app.delete')}
                      </button>
                    </div>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: 12,
                      }}
                    >
                      <FormField<GameConfigFormValues>
                        name={`memoryMatch.pairs.${index}.front` as const}
                        label="games.editor.front"
                        disabled={isSaving}
                      />
                      <FormField<GameConfigFormValues>
                        name={`memoryMatch.pairs.${index}.back` as const}
                        label="games.editor.back"
                        disabled={isSaving}
                      />
                      <FormField<GameConfigFormValues>
                        name={`memoryMatch.pairs.${index}.imageUrl` as const}
                        label="games.editor.imageUrl"
                        disabled={isSaving}
                      />
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={isSaving}
                  onClick={() => memoryPairsArray.append({ ...EMPTY_PAIR })}
                >
                  {t('games.editor.addPair')}
                </button>
              </div>
            </section>
          ) : null}

          {watchedGameType === 'sorting' ? (
            <section className="card" style={{ marginTop: 20, padding: 16 }}>
              <h3 style={{ marginTop: 0 }}>{t('games.editor.sortingTitle')}</h3>
              <div style={{ display: 'grid', gap: 12 }}>
                {sortingCategoriesArray.fields.map((field, index) => (
                  <div
                    key={field.id}
                    className="card"
                    style={{ padding: 16, display: 'grid', gap: 12 }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <strong>{t('games.editor.categoryLabel', { index: index + 1 })}</strong>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={isSaving || sortingCategoriesArray.fields.length === 1}
                        onClick={() => sortingCategoriesArray.remove(index)}
                      >
                        {t('app.delete')}
                      </button>
                    </div>
                    <FormField<GameConfigFormValues>
                      name={`sorting.categories.${index}.name` as const}
                      label="games.editor.categoryName"
                      disabled={isSaving}
                    />
                    <FormTextarea<GameConfigFormValues>
                      name={`sorting.categories.${index}.itemsText` as const}
                      label="games.editor.categoryItems"
                      rows={4}
                      disabled={isSaving}
                    />
                  </div>
                ))}
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={isSaving}
                  onClick={() => sortingCategoriesArray.append({ ...EMPTY_CATEGORY })}
                >
                  {t('games.editor.addCategory')}
                </button>
              </div>
            </section>
          ) : null}

          {watchedGameType === 'vocabulary_cards' ? (
            <section className="card" style={{ marginTop: 20, padding: 16 }}>
              <h3 style={{ marginTop: 0 }}>{t('games.editor.vocabularyTitle')}</h3>
              <div style={{ display: 'grid', gap: 12 }}>
                {vocabularyCardsArray.fields.map((field, index) => (
                  <div
                    key={field.id}
                    className="card"
                    style={{ padding: 16, display: 'grid', gap: 12 }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <strong>{t('games.editor.cardLabel', { index: index + 1 })}</strong>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        disabled={isSaving || vocabularyCardsArray.fields.length === 1}
                        onClick={() => vocabularyCardsArray.remove(index)}
                      >
                        {t('app.delete')}
                      </button>
                    </div>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: 12,
                      }}
                    >
                      <FormField<GameConfigFormValues>
                        name={`vocabularyCards.cards.${index}.wordAr` as const}
                        label="games.editor.wordAr"
                        disabled={isSaving}
                      />
                      <FormField<GameConfigFormValues>
                        name={`vocabularyCards.cards.${index}.wordFr` as const}
                        label="games.editor.wordFr"
                        disabled={isSaving}
                      />
                      <FormField<GameConfigFormValues>
                        name={`vocabularyCards.cards.${index}.imageUrl` as const}
                        label="games.editor.imageUrl"
                        disabled={isSaving}
                      />
                      <FormField<GameConfigFormValues>
                        name={`vocabularyCards.cards.${index}.audioUrl` as const}
                        label="games.editor.audioUrl"
                        disabled={isSaving}
                      />
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={isSaving}
                  onClick={() => vocabularyCardsArray.append({ ...EMPTY_CARD })}
                >
                  {t('games.editor.addCard')}
                </button>
              </div>
            </section>
          ) : null}

          <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
            <button type="submit" className="btn btn-primary" disabled={isSaving}>
              {isSaving ? t('app.loading') : t(config ? 'games.saveChanges' : 'games.createConfig')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={handleCancel}>
              {t('app.cancel')}
            </button>
          </div>
        </form>
      </FormProvider>
    </>
  );

  if (embedded) {
    return formBody;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t(config ? 'games.editTitle' : 'games.createTitle')}</h1>
          <p className="page-subtitle">{t('games.formSubtitle')}</p>
        </div>
      </div>
      {formBody}
    </div>
  );
}
