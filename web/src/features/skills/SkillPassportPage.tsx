import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { formatDate } from '@/shared/i18n';
import { Badge, ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { skillsService } from './skills.service';
import type { SkillDimension, SkillMilestone } from './skills.types';
import { useGenerateSkillPassport, useSkillDimensions, useSkillMilestones, useSkillPassport } from './useSkills';

function getDimensionLabel(dimension: SkillDimension, language: string) {
  if (language.startsWith('ar')) {
    return dimension.name_ar;
  }
  if (language.startsWith('en')) {
    return dimension.name_en;
  }
  return dimension.name_fr;
}

function getMilestoneLabel(milestone: SkillMilestone, language: string) {
  if (language.startsWith('ar')) {
    return milestone.name_ar;
  }
  return milestone.name_fr;
}

export function SkillPassportPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const { studentId = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [academicYearId, setAcademicYearId] = useState(searchParams.get('academicYearId') || '');
  const dimensionsQuery = useSkillDimensions();
  const milestonesQuery = useSkillMilestones();
  const passportQuery = useSkillPassport(studentId, academicYearId);
  const generatePassportMutation = useGenerateSkillPassport();
  const canGenerate = ['TCH', 'DIR'].includes(user?.role || '');

  const passportSections = useMemo(() => {
    const dimensions = dimensionsQuery.data ?? [];
    const milestones = milestonesQuery.data ?? [];
    const progressItems = passportQuery.data?.progress_items ?? [];
    const unlockedMilestones = new Set(
      progressItems.filter((item) => item.status === 'unlocked').map((item) => item.milestone_id)
    );

    return dimensions.map((dimension) => {
      const dimensionMilestones = milestones.filter((milestone) => milestone.dimension_id === dimension.id);
      const achieved = dimensionMilestones.filter((milestone) => unlockedMilestones.has(milestone.id));

      return {
        id: dimension.id,
        label: getDimensionLabel(dimension, i18n.language),
        achieved,
        total: dimensionMilestones.length,
      };
    });
  }, [dimensionsQuery.data, i18n.language, milestonesQuery.data, passportQuery.data?.progress_items]);

  async function handleGeneratePassport() {
    if (!studentId || !academicYearId) {
      return;
    }

    await generatePassportMutation.mutateAsync({
      studentId,
      academicYearId,
    });
  }

  function handleApplyAcademicYear() {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      if (academicYearId) {
        next.set('academicYearId', academicYearId);
      } else {
        next.delete('academicYearId');
      }
      return next;
    });
  }

  if (dimensionsQuery.isLoading || milestonesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('skills.passportTitle')}</h1>
          <p className="page-subtitle">{t('skills.passportSubtitle')}</p>
        </div>
        <div className="page-actions">
          <input
            className="filter-input"
            value={academicYearId}
            onChange={(event) => setAcademicYearId(event.target.value)}
            placeholder={t('skills.academicYearIdPlaceholder')}
          />
          <button type="button" className="btn btn-secondary" onClick={handleApplyAcademicYear}>
            {t('skills.loadPassport')}
          </button>
          {passportQuery.data?.pdf_url || academicYearId ? (
            <a
              className="btn btn-secondary"
              href={skillsService.downloadPassportUrl(studentId, academicYearId)}
              target="_blank"
              rel="noopener noreferrer"
            >
              {t('skills.downloadPdf')}
            </a>
          ) : null}
          <button type="button" className="btn btn-primary" onClick={() => window.print()}>
            {t('skills.printPassport')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={toBannerError(
          dimensionsQuery.error ??
            milestonesQuery.error ??
            passportQuery.error ??
            generatePassportMutation.error,
          t('app.error')
        )}
      />

      {!passportQuery.data && canGenerate ? (
        <div className="card">
          <p>{t('skills.passportMissing')}</p>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!academicYearId || generatePassportMutation.isPending}
            onClick={() => void handleGeneratePassport()}
          >
            {generatePassportMutation.isPending ? t('app.loading') : t('skills.generatePassport')}
          </button>
        </div>
      ) : null}

      {passportQuery.isLoading ? <LoadingState /> : null}

      {passportQuery.data ? (
        <div className="card" style={{ padding: 24 }}>
          <div className="stats-grid">
            <StatCard label="skills.overallScore" value={`${passportQuery.data.overall_score}%`} icon="🏅" />
            <StatCard label="skills.unlocked" value={passportQuery.data.unlocked_milestones} icon="✨" />
            <StatCard label="skills.totalMilestones" value={passportQuery.data.total_milestones} icon="🏁" />
            <StatCard
              label="skills.generatedAt"
              value={formatDate(passportQuery.data.generated_at, i18n.language)}
              icon="🖨"
            />
          </div>

          <div className="card-list">
            {passportSections.map((section) => (
              <div key={section.id} className="card">
                <div className="page-header page-header--split">
                  <div>
                    <h2>{section.label}</h2>
                    <p>{t('skills.achievedCount', { count: section.achieved.length, total: section.total })}</p>
                  </div>
                  <Badge variant={section.achieved.length === section.total && section.total > 0 ? 'success' : 'info'}>
                    {section.achieved.length}/{section.total}
                  </Badge>
                </div>
                {section.achieved.length === 0 ? (
                  <p>{t('skills.noMilestonesUnlocked')}</p>
                ) : (
                  <ul>
                    {section.achieved.map((milestone) => (
                      <li key={milestone.id}>
                        {getMilestoneLabel(milestone, i18n.language)} ({t('skills.levelValue', { level: milestone.level })})
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
