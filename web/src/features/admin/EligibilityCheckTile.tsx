/**
 * EligibilityCheckTile — Phase 3.4 helper widget.
 *
 * Embeddable tile: pick a target program + kind, runs the eligibility
 * check, renders the per-rule pass/fail breakdown. Read-only consumer of
 * GET /students/{id}/eligibility — no rule editing here.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LoadingState } from '@/shared/ui';
import { useEligibilityCheckQuery, useProgramsQuery } from './usePrograms';
import type { EligibilityRuleKind } from './programs.service';

const KINDS: EligibilityRuleKind[] = ['PROMOTION', 'ADMISSION', 'TRANSFER'];

interface EligibilityCheckTileProps {
  readonly studentId: string;
}

export function EligibilityCheckTile({ studentId }: EligibilityCheckTileProps) {
  const { t } = useTranslation();
  const programsQuery = useProgramsQuery(true);
  const [kind, setKind] = useState<EligibilityRuleKind>('PROMOTION');
  const [targetProgramId, setTargetProgramId] = useState('');

  const checkQuery = useEligibilityCheckQuery(studentId, kind, targetProgramId || undefined);

  return (
    <section className="card" style={{ padding: 16, marginTop: 16 }}>
      <h3 style={{ marginTop: 0 }}>
        {t('admin.eligibility.title', { defaultValue: 'Eligibility check' })}
      </h3>

      <div className="filters-bar" style={{ marginBottom: 12 }}>
        <select
          className="filter-select"
          value={kind}
          onChange={(e) => setKind(e.target.value as EligibilityRuleKind)}
          aria-label={t('admin.eligibility.kindLabel', { defaultValue: 'Kind' })}
        >
          {KINDS.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <select
          className="filter-select"
          value={targetProgramId}
          onChange={(e) => setTargetProgramId(e.target.value)}
          aria-label={t('admin.eligibility.targetLabel', {
            defaultValue: 'Target program',
          })}
        >
          <option value="">
            {t('admin.eligibility.choose', {
              defaultValue: '— choose program —',
            })}
          </option>
          {(programsQuery.data ?? []).map((program) => (
            <option key={program.id} value={program.id}>
              {program.code} — {program.name}
            </option>
          ))}
        </select>
      </div>

      {!targetProgramId ? (
        <p style={{ color: 'var(--color-text-secondary)' }}>
          {t('admin.eligibility.pickProgram', {
            defaultValue: 'Pick a target program to run the check.',
          })}
        </p>
      ) : checkQuery.isLoading ? (
        <LoadingState />
      ) : checkQuery.data ? (
        <>
          <p>
            <strong>
              {checkQuery.data.eligible
                ? t('admin.eligibility.eligible', {
                    defaultValue: '✅ Eligible',
                  })
                : t('admin.eligibility.notEligible', {
                    defaultValue: '❌ Not eligible',
                  })}
            </strong>
          </p>
          {(checkQuery.data.rules ?? []).length === 0 ? (
            <p style={{ color: 'var(--color-text-secondary)' }}>
              {t('admin.eligibility.noRules', {
                defaultValue: 'No rules configured for this combination.',
              })}
            </p>
          ) : (
            <ul style={{ paddingInlineStart: 16, margin: 0 }}>
              {checkQuery.data.rules.map((r) => (
                <li key={r.rule_id} style={{ marginBottom: 4 }}>
                  <span aria-hidden="true">{r.passed ? '✓' : '✗'}</span>{' '}
                  <code>{r.condition_type}</code> — <em>{r.message_key}</em>
                  {r.detail && (
                    <span style={{ color: 'var(--color-text-secondary)' }}> ({r.detail})</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      ) : null}
    </section>
  );
}
