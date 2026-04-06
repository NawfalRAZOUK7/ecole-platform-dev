import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, Tabs } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { MicroEnrollment, MicroPayment, MicroResource } from './micro-schools.types';
import {
  useCreateMicroResource,
  useMicroSchoolDetail,
  useMicroSchoolEnrollments,
  useMicroSchoolPayments,
  useMicroSchoolProgress,
  useMicroSchoolResources,
  useUnenrollMicroStudent,
} from './useMicroSchools';

type EnrollmentRow = MicroEnrollment & Record<string, unknown>;
type PaymentRow = MicroPayment & Record<string, unknown>;
type ResourceRow = MicroResource & Record<string, unknown>;

const madFormatter = new Intl.NumberFormat('fr-MA', {
  style: 'currency',
  currency: 'MAD',
});

export function MicroSchoolDetailPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const detailQuery = useMicroSchoolDetail(id);
  const enrollmentsQuery = useMicroSchoolEnrollments(id);
  const paymentsQuery = useMicroSchoolPayments(id);
  const resourcesQuery = useMicroSchoolResources(id);
  const progressQuery = useMicroSchoolProgress(id);
  const unenrollMutation = useUnenrollMicroStudent();
  const createResourceMutation = useCreateMicroResource();

  const enrollmentColumns: ColumnDef<EnrollmentRow>[] = useMemo(
    () => [
      { key: 'student_name', header: 'microSchools.student' },
      { key: 'status', header: 'microSchools.status' },
      {
        key: 'enrolled_at',
        header: 'microSchools.enrolledAt',
        render: (value) => formatDate(String(value), i18n.language),
      },
      {
        key: 'id',
        header: 'microSchools.actions',
        sortable: false,
        render: (_value, row) => (
          <button
            type="button"
            className="btn btn-danger btn-sm"
            onClick={() => void unenrollMutation.mutateAsync({ microSchoolId: id, enrollmentId: row.id })}
          >
            {t('microSchools.unenroll')}
          </button>
        ),
      },
    ],
    [i18n.language, id, t, unenrollMutation]
  );

  const paymentColumns: ColumnDef<PaymentRow>[] = useMemo(
    () => [
      {
        key: 'amount',
        header: 'microSchools.amount',
        render: (value) => madFormatter.format(Number(value)),
      },
      { key: 'status', header: 'microSchools.status' },
      {
        key: 'created_at',
        header: 'microSchools.date',
        render: (value) => formatDate(String(value), i18n.language),
      },
    ],
    [i18n.language]
  );

  const resourceColumns: ColumnDef<ResourceRow>[] = useMemo(
    () => [
      { key: 'title', header: 'microSchools.name' },
      { key: 'type', header: 'microSchools.type' },
      { key: 'language', header: 'microSchools.language' },
    ],
    []
  );

  return (
    <div className="page micro-school-detail-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{detailQuery.data?.name ?? t('microSchools.title')}</h1>
          <p className="page-subtitle">
            {detailQuery.data?.location}, {detailQuery.data?.city} · {t('microSchools.capacity')}: {detailQuery.data?.capacity ?? 0}
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => navigate(`/micro-schools/${id}/enroll`)}>
          {t('microSchools.enroll')}
        </button>
      </div>

      <ErrorBanner
        error={toBannerError(
          detailQuery.error ??
            enrollmentsQuery.error ??
            paymentsQuery.error ??
            resourcesQuery.error ??
            progressQuery.error ??
            createResourceMutation.error ??
            unenrollMutation.error,
          t('app.error')
        )}
      />

      <div className="card micro-school-detail-page__hero">
        <p>{detailQuery.data?.description || t('microSchools.noDescription')}</p>
        <p>{t('microSchools.students')}: {detailQuery.data?.student_count ?? 0}</p>
      </div>

      <Tabs
        defaultTab="students"
        tabs={[
          {
            id: 'students',
            label: 'microSchools.students',
            content: (
              <DataTable
                columns={enrollmentColumns}
                data={(enrollmentsQuery.data ?? []) as EnrollmentRow[]}
                loading={enrollmentsQuery.isLoading}
                emptyMessage="microSchools.empty"
                ariaLabel={t('microSchools.students')}
              />
            ),
          },
          {
            id: 'resources',
            label: 'microSchools.resources',
            content: (
              <div className="micro-school-detail-page__resources">
                <div className="filters-bar">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() =>
                      void createResourceMutation.mutateAsync({
                        microSchoolId: id,
                        payload: {
                          title: `Resource ${(resourcesQuery.data?.length ?? 0) + 1}`,
                          type: 'lesson_plan',
                          language: 'fr',
                        },
                      })
                    }
                  >
                    {t('microSchools.addResource')}
                  </button>
                </div>
                <DataTable
                  columns={resourceColumns}
                  data={(resourcesQuery.data ?? []) as ResourceRow[]}
                  loading={resourcesQuery.isLoading}
                  emptyMessage="microSchools.empty"
                  ariaLabel={t('microSchools.resources')}
                />
              </div>
            ),
          },
          {
            id: 'payments',
            label: 'microSchools.payments',
            content: (
              <DataTable
                columns={paymentColumns}
                data={(paymentsQuery.data ?? []) as PaymentRow[]}
                loading={paymentsQuery.isLoading}
                emptyMessage="microSchools.empty"
                ariaLabel={t('microSchools.payments')}
              />
            ),
          },
          {
            id: 'progress',
            label: 'microSchools.progress',
            content: (
              <div className="card micro-school-detail-page__progress">
                <p>{t('microSchools.averageProgress')}: {progressQuery.data?.average_progress ?? 0}%</p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={progressQuery.data?.series ?? []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="label" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="var(--color-primary)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
