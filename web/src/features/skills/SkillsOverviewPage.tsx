import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from 'recharts';
import { useAuth } from '@/services/auth/AuthContext';
import { DataTable, ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { SkillDimension } from './skills.types';
import { useSkillDimensions, useSkillMilestones, useStudentSkillProgress } from './useSkills';

type SummaryRow = {
  dimension: string;
  unlocked: number;
  total: number;
  value: number;
} & Record<string, unknown>;

function getDimensionLabel(dimension: SkillDimension, language: string) {
  if (language.startsWith('ar')) {
    return dimension.name_ar;
  }
  if (language.startsWith('en')) {
    return dimension.name_en;
  }
  return dimension.name_fr;
}

export function SkillsOverviewPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [studentId, setStudentId] = useState('');
  const [academicYearId, setAcademicYearId] = useState('');
  const dimensionsQuery = useSkillDimensions();
  const milestonesQuery = useSkillMilestones();
  const progressQuery = useStudentSkillProgress(studentId, academicYearId);

  useEffect(() => {
    if (!studentId && user?.role === 'STD' && user.id) {
      setStudentId(user.id);
    }
  }, [studentId, user]);

  const radarData = useMemo(() => {
    const dimensions = dimensionsQuery.data ?? [];
    const milestones = milestonesQuery.data ?? [];
    const progressItems = progressQuery.data ?? [];

    return dimensions.map((dimension) => {
      const relatedMilestones = milestones.filter((milestone) => milestone.dimension_id === dimension.id);
      const relatedProgress = progressItems.filter((progress) => progress.dimension_id === dimension.id);
      const unlockedCount = relatedProgress.filter((item) => item.status === 'unlocked').length;
      const highestLevel = relatedMilestones.reduce((current, milestone) => {
        const isUnlocked = relatedProgress.some(
          (progress) => progress.milestone_id === milestone.id && progress.status === 'unlocked'
        );
        return isUnlocked ? Math.max(current, milestone.level) : current;
      }, 0);

      return {
        dimension: getDimensionLabel(dimension, i18n.language),
        unlocked: unlockedCount,
        total: relatedMilestones.length,
        value: highestLevel,
      };
    });
  }, [dimensionsQuery.data, i18n.language, milestonesQuery.data, progressQuery.data]);

  const summaryColumns: ColumnDef<SummaryRow>[] = useMemo(
    () => [
      { key: 'dimension', header: 'skills.dimension' },
      { key: 'unlocked', header: 'skills.unlocked' },
      { key: 'total', header: 'skills.totalMilestones' },
      { key: 'value', header: 'skills.currentLevel' },
    ],
    []
  );

  if (dimensionsQuery.isLoading || milestonesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('skills.title')}</h1>
        <p className="page-subtitle">{t('skills.subtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          dimensionsQuery.error ?? milestonesQuery.error ?? progressQuery.error,
          t('app.error')
        )}
      />

      <div className="filters-bar">
        <input
          className="filter-input"
          value={studentId}
          onChange={(event) => setStudentId(event.target.value)}
          placeholder={t('skills.studentIdPlaceholder')}
        />
        <input
          className="filter-input"
          value={academicYearId}
          onChange={(event) => setAcademicYearId(event.target.value)}
          placeholder={t('skills.academicYearIdPlaceholder')}
        />
      </div>

      <div className="stats-grid">
        <StatCard label="skills.dimensions" value={dimensionsQuery.data?.length ?? 0} icon="🧭" />
        <StatCard label="skills.totalMilestones" value={milestonesQuery.data?.length ?? 0} icon="🏁" />
        <StatCard
          label="skills.unlocked"
          value={progressQuery.data?.filter((item) => item.status === 'unlocked').length ?? 0}
          icon="✨"
        />
        <StatCard label="skills.progressEntries" value={progressQuery.data?.length ?? 0} icon="📘" />
      </div>

      <div className="card" style={{ minHeight: 420 }}>
        <h2>{t('skills.overviewRadar')}</h2>
        <ResponsiveContainer width="100%" height={360}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="dimension" />
            <Radar
              name={t('skills.currentLevel')}
              dataKey="value"
              stroke="var(--color-primary)"
              fill="var(--color-primary)"
              fillOpacity={0.28}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <DataTable
        columns={summaryColumns}
        data={radarData as SummaryRow[]}
        loading={progressQuery.isLoading}
        emptyMessage="skills.empty"
        ariaLabel={t('skills.title')}
      />
    </div>
  );
}
