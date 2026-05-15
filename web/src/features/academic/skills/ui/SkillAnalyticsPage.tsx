import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, LoadingState, Tabs } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { SkillLeaderboardEntry } from '../model/skills.types';
import {
  useClassSkillAnalytics,
  useSchoolSkillAnalytics,
  useSkillLeaderboard,
} from '../model/useSkills';

type LeaderboardRow = SkillLeaderboardEntry & Record<string, unknown>;

export function SkillAnalyticsPage() {
  const { t } = useTranslation();
  const [classId, setClassId] = useState('');
  const [academicYearId, setAcademicYearId] = useState('');
  const [limit, setLimit] = useState(10);
  const classAnalyticsQuery = useClassSkillAnalytics(classId, academicYearId);
  const schoolAnalyticsQuery = useSchoolSkillAnalytics(academicYearId);
  const leaderboardQuery = useSkillLeaderboard(classId, academicYearId, limit);

  const comparisonData = useMemo(
    () => [
      {
        label: t('skills.classAverage'),
        classValue: classAnalyticsQuery.data?.average_overall_score ?? 0,
        schoolValue: schoolAnalyticsQuery.data?.average_overall_score ?? 0,
      },
    ],
    [
      classAnalyticsQuery.data?.average_overall_score,
      schoolAnalyticsQuery.data?.average_overall_score,
      t,
    ],
  );

  const radarData = useMemo(
    () =>
      (classAnalyticsQuery.data?.dimension_summaries ?? []).map((item) => ({
        dimension: item.name_fr,
        value: item.average_progress,
      })),
    [classAnalyticsQuery.data?.dimension_summaries],
  );

  const leaderboardColumns: ColumnDef<LeaderboardRow>[] = useMemo(
    () => [
      { key: 'rank', header: 'skills.rank' },
      { key: 'alias', header: 'skills.alias' },
      { key: 'overall_score', header: 'skills.overallScore' },
      { key: 'unlocked_milestones', header: 'skills.unlocked' },
      { key: 'total_milestones', header: 'skills.totalMilestones' },
    ],
    [],
  );

  if (classAnalyticsQuery.isLoading || schoolAnalyticsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('skills.analyticsTitle')}</h1>
        <p className="page-subtitle">{t('skills.analyticsSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          classAnalyticsQuery.error ?? schoolAnalyticsQuery.error ?? leaderboardQuery.error,
          t('app.error'),
        )}
      />

      <div className="filters-bar">
        <input
          className="filter-input"
          value={classId}
          onChange={(event) => setClassId(event.target.value)}
          placeholder={t('skills.classIdPlaceholder')}
        />
        <input
          className="filter-input"
          value={academicYearId}
          onChange={(event) => setAcademicYearId(event.target.value)}
          placeholder={t('skills.academicYearIdPlaceholder')}
        />
        <input
          className="filter-input"
          type="number"
          min="3"
          max="20"
          value={limit}
          onChange={(event) => setLimit(Number(event.target.value))}
          placeholder={t('skills.limit')}
        />
      </div>

      <Tabs
        defaultTab="comparison"
        tabs={[
          {
            id: 'comparison',
            label: 'skills.analyticsComparison',
            content: (
              <div className="card-list">
                <div className="card" style={{ minHeight: 360 }}>
                  <h2>{t('skills.analyticsComparison')}</h2>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={comparisonData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                      <XAxis dataKey="label" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar
                        dataKey="classValue"
                        fill="var(--color-primary)"
                        name={t('skills.classAverage')}
                      />
                      <Bar
                        dataKey="schoolValue"
                        fill="var(--color-success)"
                        name={t('skills.schoolAverage')}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="card" style={{ minHeight: 360 }}>
                  <h2>{t('skills.dimensionRadar')}</h2>
                  <ResponsiveContainer width="100%" height={280}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="dimension" />
                      <Radar
                        dataKey="value"
                        stroke="var(--color-primary)"
                        fill="var(--color-primary)"
                        fillOpacity={0.25}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ),
          },
          {
            id: 'leaderboard',
            label: 'skills.leaderboardTitle',
            content: (
              <div className="card">
                <DataTable
                  columns={leaderboardColumns}
                  data={(leaderboardQuery.data ?? []) as LeaderboardRow[]}
                  loading={leaderboardQuery.isLoading}
                  emptyMessage="skills.empty"
                  ariaLabel={t('skills.leaderboardTitle')}
                />
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
