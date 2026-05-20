import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { ComplianceDashboardItem } from '../model/compliance.types';
import { useComplianceDashboard } from '../model/useCompliance';

type GapRow = ComplianceDashboardItem & Record<string, unknown>;

export function ComplianceDashboardPage() {
  const { t } = useTranslation();
  const [academicYearId, setAcademicYearId] = useState('');
  const [level, setLevel] = useState('');
  const [grade, setGrade] = useState('');
  const [subject, setSubject] = useState('');
  const dashboardQuery = useComplianceDashboard({
    academic_year_id: academicYearId,
    level: level || undefined,
    grade: grade || undefined,
    subject: subject || undefined,
  });

  const gapColumns: ColumnDef<GapRow>[] = useMemo(
    () => [
      { key: 'subject', header: 'compliance.subject' },
      { key: 'grade', header: 'compliance.grade' },
      { key: 'total_objectives', header: 'compliance.totalObjectives' },
      { key: 'mapped_objectives', header: 'compliance.mappedObjectives' },
      { key: 'unmapped_objectives', header: 'compliance.unmappedObjectives' },
      { key: 'compliance_percent', header: 'compliance.compliancePercent' },
    ],
    [],
  );

  if (dashboardQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('compliance.title')}</h1>
        <p className="page-subtitle">{t('compliance.subtitle')}</p>
      </div>

      <ErrorBanner error={toBannerError(dashboardQuery.error, t('app.error'))} />

      <div className="filters-bar">
        <input
          className="filter-input"
          value={academicYearId}
          onChange={(event) => setAcademicYearId(event.target.value)}
          placeholder={t('compliance.academicYearIdPlaceholder')}
        />
        <input
          className="filter-input"
          value={level}
          onChange={(event) => setLevel(event.target.value)}
          placeholder={t('compliance.level')}
        />
        <input
          className="filter-input"
          value={grade}
          onChange={(event) => setGrade(event.target.value)}
          placeholder={t('compliance.grade')}
        />
        <input
          className="filter-input"
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
          placeholder={t('compliance.subject')}
        />
      </div>

      <div className="stats-grid">
        <StatCard
          label="compliance.curriculumCount"
          value={dashboardQuery.data?.curriculum_count ?? 0}
          icon="📚"
        />
        <StatCard
          label="compliance.totalObjectives"
          value={dashboardQuery.data?.total_objectives ?? 0}
          icon="🎯"
        />
        <StatCard
          label="compliance.mappedObjectives"
          value={dashboardQuery.data?.mapped_objectives ?? 0}
          icon="🔗"
        />
        <StatCard
          label="compliance.overallCompliance"
          value={`${dashboardQuery.data?.overall_compliance_percent ?? 0}%`}
          icon="✅"
        />
      </div>

      <div className="card-list">
        {(dashboardQuery.data?.items ?? []).map((item) => (
          <div key={item.curriculum_id} className="card" style={{ minHeight: 300 }}>
            <h2>{item.subject}</h2>
            <p>
              {item.level} · {item.grade}
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <RadialBarChart
                innerRadius="60%"
                outerRadius="100%"
                barSize={18}
                data={[{ name: item.subject, value: item.compliance_percent }]}
                startAngle={180}
                endAngle={0}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar dataKey="value" cornerRadius={10} fill="var(--color-primary)" />
              </RadialBarChart>
            </ResponsiveContainer>
            <p style={{ textAlign: 'center', fontWeight: 700 }}>{item.compliance_percent}%</p>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>{t('compliance.gapAnalysis')}</h2>
        <DataTable
          columns={gapColumns}
          data={(dashboardQuery.data?.items ?? []) as GapRow[]}
          loading={dashboardQuery.isLoading}
          emptyMessage="compliance.empty"
          ariaLabel={t('compliance.gapAnalysis')}
        />
      </div>
    </div>
  );
}
