/**
 * Admin Eligibility Rules page — Phase 3.4 follow-up.
 *
 * Operational model: rules are set once and edited rarely. Edit is
 * delete-and-recreate; this page does not offer an inline edit. Three
 * built-in condition_types match the backend evaluator catalog —
 * unknown condition_types are rejected by the API (422).
 *
 * Route: /admin/eligibility-rules
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState, ErrorBanner, LoadingState, toBannerError } from '@/shared/ui';
import {
  useCreateEligibilityRuleMutation,
  useDeleteEligibilityRuleMutation,
  useEligibilityRulesQuery,
  useProgramsQuery,
} from '../model/usePrograms';
import type { EligibilityRuleKind } from '../api/programs.api';

const KINDS: EligibilityRuleKind[] = ['PROMOTION', 'ADMISSION', 'TRANSFER'];

// Mirrors the catalog in eligibility_service.KNOWN_CONDITION_TYPES.
const CONDITION_TYPES = [
  'has_completed_program',
  'min_attendance_rate',
  'min_grade_average',
] as const;
type ConditionType = (typeof CONDITION_TYPES)[number];

export function EligibilityRulesPage() {
  const { t } = useTranslation();
  const programsQuery = useProgramsQuery(true);
  const rulesQuery = useEligibilityRulesQuery({ active_only: false });
  const createMutation = useCreateEligibilityRuleMutation();
  const deleteMutation = useDeleteEligibilityRuleMutation();

  const [kind, setKind] = useState<EligibilityRuleKind>('PROMOTION');
  const [targetProgramId, setTargetProgramId] = useState('');
  const [conditionType, setConditionType] = useState<ConditionType>('has_completed_program');
  const [paramsText, setParamsText] = useState('{}');
  const [messageKey, setMessageKey] = useState('');

  const programNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of programsQuery.data ?? []) {
      map.set(p.id, `${p.code} — ${p.name}`);
    }
    return map;
  }, [programsQuery.data]);

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          rulesQuery.error ?? createMutation.error ?? deleteMutation.error,
          t('app.error'),
        ),
      [createMutation.error, deleteMutation.error, rulesQuery.error, t],
    ),
  );

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!targetProgramId || !messageKey.trim()) return;

    let parsedParams: Record<string, unknown> = {};
    try {
      parsedParams = JSON.parse(paramsText.trim() || '{}');
    } catch {
      // Leave as {} — the backend will validate the structure of params
      // against the chosen condition_type.
    }

    await createMutation.mutateAsync({
      kind,
      target_program_id: targetProgramId,
      condition_type: conditionType,
      condition_params: parsedParams,
      message_key: messageKey.trim(),
      is_active: true,
    });

    setMessageKey('');
    setParamsText('{}');
  }

  if (rulesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">
        {t('admin.eligibilityRules.title', {
          defaultValue: 'Eligibility rules',
        })}
      </h1>
      <p className="page-subtitle">
        {t('admin.eligibilityRules.subtitle', {
          defaultValue:
            'Declarative rules evaluated when a student is checked for promotion, admission, or transfer.',
        })}
      </p>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void rulesQuery.refetch()}
      />

      <form
        className="card"
        style={{ maxWidth: 720, marginBottom: 24, padding: 16 }}
        onSubmit={handleCreate}
      >
        <h2 style={{ marginTop: 0 }}>
          {t('admin.eligibilityRules.create', { defaultValue: 'New rule' })}
        </h2>
        <div className="form-field">
          <label htmlFor="rule-kind">
            {t('admin.eligibilityRules.kind', { defaultValue: 'Kind' })}
          </label>
          <select
            id="rule-kind"
            className="filter-select"
            value={kind}
            onChange={(e) => setKind(e.target.value as EligibilityRuleKind)}
          >
            {KINDS.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="rule-target">
            {t('admin.eligibilityRules.targetProgram', {
              defaultValue: 'Target program',
            })}
          </label>
          <select
            id="rule-target"
            className="filter-select"
            value={targetProgramId}
            onChange={(e) => setTargetProgramId(e.target.value)}
            required
          >
            <option value="">—</option>
            {(programsQuery.data ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} — {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="rule-condition">
            {t('admin.eligibilityRules.condition', {
              defaultValue: 'Condition type',
            })}
          </label>
          <select
            id="rule-condition"
            className="filter-select"
            value={conditionType}
            onChange={(e) => setConditionType(e.target.value as ConditionType)}
          >
            {CONDITION_TYPES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="rule-params">
            {t('admin.eligibilityRules.params', {
              defaultValue: 'Parameters (JSON)',
            })}
          </label>
          <textarea
            id="rule-params"
            className="input"
            rows={3}
            value={paramsText}
            onChange={(e) => setParamsText(e.target.value)}
            placeholder='{"min_rate": 0.8}'
          />
        </div>
        <div className="form-field">
          <label htmlFor="rule-message">
            {t('admin.eligibilityRules.messageKey', {
              defaultValue: 'Message key (i18n)',
            })}
          </label>
          <input
            id="rule-message"
            className="input"
            value={messageKey}
            onChange={(e) => setMessageKey(e.target.value)}
            placeholder="eligibility.attendance.required"
            required
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!targetProgramId || !messageKey.trim() || createMutation.isPending}
        >
          {createMutation.isPending
            ? t('app.loading')
            : t('admin.eligibilityRules.create', { defaultValue: 'Create' })}
        </button>
      </form>

      {(rulesQuery.data?.length ?? 0) === 0 ? (
        <EmptyState
          message={t('admin.eligibilityRules.empty', {
            defaultValue: 'No rules configured yet.',
          })}
          icon="📜"
        />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('admin.eligibilityRules.kind', { defaultValue: 'Kind' })}</th>
                <th>
                  {t('admin.eligibilityRules.targetProgram', {
                    defaultValue: 'Target',
                  })}
                </th>
                <th>
                  {t('admin.eligibilityRules.condition', {
                    defaultValue: 'Condition',
                  })}
                </th>
                <th>
                  {t('admin.eligibilityRules.params', {
                    defaultValue: 'Params',
                  })}
                </th>
                <th>
                  {t('admin.eligibilityRules.messageKey', {
                    defaultValue: 'Message',
                  })}
                </th>
                <th>{t('admin.programs.status', { defaultValue: 'Status' })}</th>
                <th>{t('admin.programs.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {(rulesQuery.data ?? []).map((rule) => (
                <tr key={rule.id}>
                  <td>
                    <code>{rule.kind}</code>
                  </td>
                  <td>
                    {programNameById.get(rule.target_program_id) ??
                      rule.target_program_id.slice(0, 8)}
                  </td>
                  <td>
                    <code>{rule.condition_type}</code>
                  </td>
                  <td>
                    <code>{JSON.stringify(rule.condition_params)}</code>
                  </td>
                  <td>
                    <code>{rule.message_key}</code>
                  </td>
                  <td>
                    <span
                      className="status-badge"
                      style={{
                        color: rule.is_active
                          ? 'var(--color-success)'
                          : 'var(--color-text-secondary)',
                        borderColor: rule.is_active
                          ? 'var(--color-success)'
                          : 'var(--color-text-secondary)',
                      }}
                    >
                      {rule.is_active
                        ? t('admin.programs.statusActive')
                        : t('admin.programs.statusInactive')}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => void deleteMutation.mutateAsync(rule.id)}
                      disabled={deleteMutation.isPending}
                    >
                      {t('admin.equivalences.delete', {
                        defaultValue: 'Delete',
                      })}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
