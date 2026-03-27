import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';

type RoleCode = 'ADM' | 'DIR' | 'TCH' | 'PAR' | 'STD';

type ReportType =
  | 'student_report_card'
  | 'class_summary'
  | 'attendance_report'
  | 'billing_statement'
  | 'school_analytics';

type ReportStatus = 'pending' | 'generating' | 'ready' | 'failed';

interface ReportOption {
  id: string;
  label?: string;
  code?: string;
  name?: string;
  full_name?: string;
  email?: string;
}

interface ReportOptionsPayload {
  classes: ReportOption[];
  periods: ReportOption[];
  students: ReportOption[];
  parents: ReportOption[];
}

interface ReportJobItem {
  id: string;
  type: ReportType;
  status: ReportStatus;
  parameters: Record<string, string | boolean | null>;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
  error_message: string | null;
  download_url: string | null;
  cache_hit: boolean;
}

const REPORT_TYPES_BY_ROLE: Record<RoleCode, ReportType[]> = {
  STD: ['student_report_card'],
  PAR: ['student_report_card', 'billing_statement'],
  TCH: ['class_summary', 'attendance_report'],
  ADM: [
    'student_report_card',
    'class_summary',
    'attendance_report',
    'billing_statement',
    'school_analytics',
  ],
  DIR: [
    'student_report_card',
    'class_summary',
    'attendance_report',
    'billing_statement',
    'school_analytics',
  ],
};

const STATUS_FILTERS: Array<ReportStatus | ''> = ['', 'pending', 'generating', 'ready', 'failed'];

function openDownload(downloadUrl: string | null) {
  if (!downloadUrl) {
    return;
  }

  const href = downloadUrl.startsWith('http')
    ? downloadUrl
    : `${window.location.origin}${downloadUrl}`;
  const anchor = document.createElement('a');
  anchor.href = href;
  anchor.target = '_blank';
  anchor.rel = 'noopener noreferrer';
  anchor.click();
}

export function ReportsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const role = ((user?.role as RoleCode | undefined) || 'STD') as RoleCode;
  const availableTypes = REPORT_TYPES_BY_ROLE[role] || REPORT_TYPES_BY_ROLE.STD;

  const [selectedType, setSelectedType] = useState<ReportType>(availableTypes[0]);
  const [locale, setLocale] = useState<'fr' | 'ar' | 'en'>(
    i18n.language.startsWith('ar') ? 'ar' : i18n.language.startsWith('en') ? 'en' : 'fr'
  );
  const [periodId, setPeriodId] = useState('');
  const [classId, setClassId] = useState('');
  const [studentId, setStudentId] = useState('');
  const [parentId, setParentId] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [compare, setCompare] = useState(false);
  const [historyTypeFilter, setHistoryTypeFilter] = useState<ReportType | ''>('');
  const [historyStatusFilter, setHistoryStatusFilter] = useState<ReportStatus | ''>('');
  const [options, setOptions] = useState<ReportOptionsPayload>({
    classes: [],
    periods: [],
    students: [],
    parents: [],
  });
  const [history, setHistory] = useState<ReportJobItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pendingJobs = useMemo(
    () => history.filter((item) => item.status === 'pending' || item.status === 'generating'),
    [history]
  );

  const loadOptions = useCallback(async () => {
    try {
      const response = await api.get<ReportOptionsPayload>('/reports/options', {
        type: selectedType,
        class_id: classId || undefined,
      });
      setOptions(response.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [classId, selectedType, t]);

  const loadHistory = useCallback(
    async (cursor?: string, append = false) => {
      try {
        const response = await api.list<ReportJobItem>('/reports', {
          limit: 12,
          cursor,
          type: historyTypeFilter || undefined,
          status: historyStatusFilter || undefined,
        });
        setHistory((previous) => (append ? [...previous, ...response.data] : response.data));
        setNextCursor(response.meta.next_cursor);
        setHasMore(response.meta.has_more);
        setError(null);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : t('app.error'));
      }
    },
    [historyStatusFilter, historyTypeFilter, t]
  );

  useEffect(() => {
    setSelectedType(availableTypes[0]);
  }, [availableTypes]);

  useEffect(() => {
    setStudentId('');
    setParentId('');
    if (!['class_summary', 'attendance_report'].includes(selectedType)) {
      setClassId('');
    }
    void loadOptions();
  }, [loadOptions, selectedType]);

  useEffect(() => {
    setLoading(true);
    void loadHistory().finally(() => setLoading(false));
  }, [loadHistory]);

  useEffect(() => {
    if (pendingJobs.length === 0) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      void loadHistory();
    }, 5000);

    return () => window.clearInterval(timer);
  }, [loadHistory, pendingJobs.length]);

  const needsClass = selectedType === 'class_summary' || selectedType === 'attendance_report';
  const needsStudent = selectedType === 'student_report_card';
  const needsParent = selectedType === 'billing_statement';

  async function handleGenerate() {
    setSubmitting(true);
    try {
      await api.post<ReportJobItem>('/reports/generate', {
        type: selectedType,
        locale,
        compare: selectedType === 'school_analytics' ? compare : false,
        period_id: periodId || undefined,
        class_id: needsClass ? classId || undefined : undefined,
        student_id: needsStudent ? studentId || undefined : undefined,
        parent_id: needsParent ? parentId || undefined : undefined,
        from_date: periodId ? undefined : fromDate || undefined,
        to_date: periodId ? undefined : toDate || undefined,
      });
      await loadHistory();
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSubmitting(false);
    }
  }

  function describeScope(item: ReportJobItem) {
    if (item.parameters.student_id) {
      return item.parameters.student_id;
    }
    if (item.parameters.class_id) {
      return item.parameters.class_id;
    }
    if (item.parameters.parent_id) {
      return item.parameters.parent_id;
    }
    if (item.parameters.period_label) {
      return item.parameters.period_label;
    }
    if (item.parameters.from_date && item.parameters.to_date) {
      return `${item.parameters.from_date} → ${item.parameters.to_date}`;
    }
    return '—';
  }

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="page reports-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('reports.title')}</h1>
          <p className="page-subtitle">{t('reports.subtitle')}</p>
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => void loadHistory()} />

      {pendingJobs.length > 0 && (
        <div className="card report-highlight">
          <strong>{t('reports.progressTitle')}</strong>
          <p>{t('reports.progressMessage', { count: pendingJobs.length })}</p>
        </div>
      )}

      <div className="reports-grid">
        <section className="card report-form-card">
          <div className="report-form-card__header">
            <h2>{t('reports.generateTitle')}</h2>
            <span className="status-badge status-generating">{t(`roles.${role}`, role)}</span>
          </div>

          <div className="report-form">
            <label className="form-field">
              <span>{t('reports.fields.type')}</span>
              <select value={selectedType} onChange={(event) => setSelectedType(event.target.value as ReportType)}>
                {availableTypes.map((item) => (
                  <option key={item} value={item}>
                    {t(`reports.types.${item}`)}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field">
              <span>{t('reports.fields.language')}</span>
              <select value={locale} onChange={(event) => setLocale(event.target.value as 'fr' | 'ar' | 'en')}>
                <option value="fr">Français</option>
                <option value="ar">العربية</option>
                <option value="en">English</option>
              </select>
            </label>

            {options.periods.length > 0 && (
              <label className="form-field">
                <span>{t('reports.fields.period')}</span>
                <select value={periodId} onChange={(event) => setPeriodId(event.target.value)}>
                  <option value="">{t('reports.anyPeriod')}</option>
                  {options.periods.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.label || item.id}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {needsClass && (
              <label className="form-field">
                <span>{t('reports.fields.class')}</span>
                <select value={classId} onChange={(event) => setClassId(event.target.value)}>
                  <option value="">{t('reports.selectClass')}</option>
                  {options.classes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {[item.code, item.name].filter(Boolean).join(' · ')}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {needsStudent && options.students.length > 0 && (
              <label className="form-field">
                <span>{t('reports.fields.student')}</span>
                <select value={studentId} onChange={(event) => setStudentId(event.target.value)}>
                  <option value="">{t('reports.selectStudent')}</option>
                  {options.students.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.full_name || item.email || item.id}
                    </option>
                  ))}
                </select>
              </label>
            )}

            {needsParent && options.parents.length > 0 && (
              <label className="form-field">
                <span>{t('reports.fields.parent')}</span>
                <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
                  <option value="">{t('reports.selectParent')}</option>
                  {options.parents.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.full_name || item.email || item.id}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <label className="form-field">
              <span>{t('reports.fields.from')}</span>
              <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} disabled={Boolean(periodId)} />
            </label>

            <label className="form-field">
              <span>{t('reports.fields.to')}</span>
              <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} disabled={Boolean(periodId)} />
            </label>

            {selectedType === 'school_analytics' && (
              <label className="form-checkbox">
                <input type="checkbox" checked={compare} onChange={(event) => setCompare(event.target.checked)} />
                <span>{t('reports.comparePrevious')}</span>
              </label>
            )}
          </div>

          <div className="report-form-card__actions">
            <button className="btn btn-primary" disabled={submitting} onClick={() => void handleGenerate()}>
              {submitting ? t('reports.generating') : t('reports.generate')}
            </button>
          </div>
        </section>

        <section className="card">
          <div className="report-history__header">
            <div>
              <h2>{t('reports.historyTitle')}</h2>
              <p>{t('reports.historySubtitle')}</p>
            </div>
            <div className="page-actions">
              <select className="filter-select" value={historyTypeFilter} onChange={(event) => setHistoryTypeFilter(event.target.value as ReportType | '')}>
                <option value="">{t('reports.allTypes')}</option>
                {availableTypes.map((item) => (
                  <option key={item} value={item}>
                    {t(`reports.types.${item}`)}
                  </option>
                ))}
              </select>
              <select className="filter-select" value={historyStatusFilter} onChange={(event) => setHistoryStatusFilter(event.target.value as ReportStatus | '')}>
                {STATUS_FILTERS.map((item) => (
                  <option key={item || 'all'} value={item}>
                    {item ? t(`reports.status.${item}`) : t('reports.allStatuses')}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {history.length === 0 ? (
            <EmptyState message={t('reports.noHistory')} icon="🧾" />
          ) : (
            <>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('reports.table.report')}</th>
                      <th>{t('reports.table.scope')}</th>
                      <th>{t('reports.table.status')}</th>
                      <th>{t('reports.table.createdAt')}</th>
                      <th>{t('reports.table.actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <strong>{t(`reports.types.${item.type}`)}</strong>
                          {item.cache_hit && <div className="table-hint">{t('reports.cached')}</div>}
                        </td>
                        <td className="table-mono">{describeScope(item)}</td>
                        <td>
                          <span className={`status-badge status-${item.status}`}>
                            {t(`reports.status.${item.status}`)}
                          </span>
                          {item.error_message && <div className="table-hint table-hint--danger">{item.error_message}</div>}
                        </td>
                        <td>
                          {formatDate(item.created_at, i18n.language, {
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          })}
                        </td>
                        <td>
                          <div className="report-table__actions">
                            <button className="btn btn-secondary btn-sm" disabled={!item.download_url} onClick={() => openDownload(item.download_url)}>
                              {t('reports.download')}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {hasMore && (
                <div className="report-load-more">
                  <button
                    className="btn btn-secondary"
                    disabled={loadingMore}
                    onClick={() => {
                      if (!nextCursor) {
                        return;
                      }
                      setLoadingMore(true);
                      void loadHistory(nextCursor, true).finally(() => setLoadingMore(false));
                    }}
                  >
                    {loadingMore ? t('app.loading') : t('reports.loadMore')}
                  </button>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
