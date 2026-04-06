import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, LoadingState } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { complianceService } from './compliance.service';
import type { ComplianceReport } from './compliance.types';
import { useComplianceReport, useComplianceReports, useCurricula, useGenerateComplianceReport } from './useCompliance';

type ReportRow = ComplianceReport & Record<string, unknown>;

function downloadCsv(report: ComplianceReport) {
  const csv = [
    ['id', 'curriculum_subject', 'curriculum_grade', 'curriculum_level', 'compliance_percent', 'total_objectives', 'mapped_objectives', 'unmapped_objectives'],
    [
      report.id,
      report.curriculum_subject || '',
      report.curriculum_grade || '',
      report.curriculum_level || '',
      String(report.compliance_percent),
      String(report.total_objectives),
      String(report.mapped_objectives),
      report.unmapped_objectives.join('; '),
    ],
  ]
    .map((row) => row.map((value) => `"${String(value).split('"').join('""')}"`).join(','))
    .join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `men-compliance-report-${report.id}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export function ComplianceReportPage() {
  const { t } = useTranslation();
  const [curriculumId, setCurriculumId] = useState('');
  const [academicYearId, setAcademicYearId] = useState('');
  const [selectedReportId, setSelectedReportId] = useState('');
  const curriculaQuery = useCurricula();
  const reportsQuery = useComplianceReports({
    curriculum_id: curriculumId || undefined,
    academic_year_id: academicYearId || undefined,
  });
  const reportDetailQuery = useComplianceReport(selectedReportId);
  const generateReportMutation = useGenerateComplianceReport();

  const reportColumns: ColumnDef<ReportRow>[] = useMemo(
    () => [
      { key: 'curriculum_subject', header: 'compliance.subject' },
      { key: 'curriculum_grade', header: 'compliance.grade' },
      { key: 'compliance_percent', header: 'compliance.compliancePercent' },
      { key: 'generated_at', header: 'compliance.generatedAt' },
      {
        key: 'id',
        header: 'compliance.actions',
        sortable: false,
        render: (_value, row) => (
          <div className="page-actions">
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelectedReportId(row.id)}>
              {t('compliance.viewReport')}
            </button>
            <a
              className="btn btn-secondary btn-sm"
              href={complianceService.downloadReportUrl(row.id)}
              target="_blank"
              rel="noopener noreferrer"
            >
              {t('compliance.downloadPdf')}
            </a>
            <button type="button" className="btn btn-primary btn-sm" onClick={() => downloadCsv(row)}>
              {t('compliance.downloadCsv')}
            </button>
          </div>
        ),
      },
    ],
    [t]
  );

  async function handleGenerateReport() {
    if (!curriculumId || !academicYearId) {
      return;
    }

    await generateReportMutation.mutateAsync({
      curriculum_id: curriculumId,
      academic_year_id: academicYearId,
    });
  }

  if (curriculaQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('compliance.reportsTitle')}</h1>
        <p className="page-subtitle">{t('compliance.reportsSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          curriculaQuery.error ??
            reportsQuery.error ??
            reportDetailQuery.error ??
            generateReportMutation.error,
          t('app.error')
        )}
      />

      <div className="filters-bar">
        <select className="filter-select" value={curriculumId} onChange={(event) => setCurriculumId(event.target.value)}>
          <option value="">{t('compliance.selectCurriculum')}</option>
          {(curriculaQuery.data ?? []).map((curriculum) => (
            <option key={curriculum.id} value={curriculum.id}>
              {curriculum.subject} · {curriculum.grade}
            </option>
          ))}
        </select>
        <input
          className="filter-input"
          value={academicYearId}
          onChange={(event) => setAcademicYearId(event.target.value)}
          placeholder={t('compliance.academicYearIdPlaceholder')}
        />
        <button type="button" className="btn btn-primary" onClick={() => void handleGenerateReport()}>
          {generateReportMutation.isPending ? t('app.loading') : t('compliance.generateReport')}
        </button>
      </div>

      <DataTable
        columns={reportColumns}
        data={(reportsQuery.data ?? []) as ReportRow[]}
        loading={reportsQuery.isLoading}
        emptyMessage="compliance.empty"
        ariaLabel={t('compliance.reportsTitle')}
      />

      {reportDetailQuery.data ? (
        <div className="card">
          <h2>{t('compliance.reportDetail')}</h2>
          <p>{reportDetailQuery.data.curriculum_subject} · {reportDetailQuery.data.curriculum_grade}</p>
          <p>{t('compliance.compliancePercent')}: {reportDetailQuery.data.compliance_percent}%</p>
          <p>{t('compliance.unmappedObjectives')}: {reportDetailQuery.data.unmapped_objectives.join(', ') || '-'}</p>
        </div>
      ) : null}
    </div>
  );
}
