import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { SearchInput } from '@/shared/ui/SearchInput';
import { Badge, ErrorBanner, FormField } from '@/shared/ui';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { MicroSchool } from './micro-schools.types';
import { useCreateMicroSchool, useMicroSchools } from './useMicroSchools';

const createSchema = z.object({
  name: z.string().min(2),
  location: z.string().min(2),
  city: z.string().min(2),
  capacity: z.coerce.number().min(1),
});

type CreateFormValues = z.infer<typeof createSchema>;

function getBadgeVariant(status: string) {
  if (status === 'active') return 'success';
  if (status === 'suspended') return 'warning';
  return 'neutral';
}

export function MicroSchoolListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const microSchoolsQuery = useMicroSchools({ status: statusFilter || undefined });
  const createMicroSchoolMutation = useCreateMicroSchool();
  const methods = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema) as Resolver<CreateFormValues>,
    defaultValues: {
      name: '',
      location: '',
      city: '',
      capacity: 20,
    },
  });

  const filteredSchools = useMemo(
    () =>
      (microSchoolsQuery.data ?? []).filter((school) =>
        school.name.toLowerCase().includes(search.toLowerCase())
      ),
    [microSchoolsQuery.data, search]
  );

  async function handleCreate(values: CreateFormValues) {
    await createMicroSchoolMutation.mutateAsync(values);
    methods.reset();
    setShowCreate(false);
  }

  return (
    <div className="page micro-schools-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('microSchools.title')}</h1>
          <p className="page-subtitle">{t('microSchools.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => setShowCreate((open) => !open)}>
          {t('microSchools.create')}
        </button>
      </div>

      <ErrorBanner error={toBannerError(microSchoolsQuery.error ?? createMicroSchoolMutation.error, t('app.error'))} />

      <div className="filters-bar">
        <SearchInput value={search} onChange={setSearch} placeholder="microSchools.search" />
        <select className="filter-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">{t('microSchools.allStatuses')}</option>
          <option value="active">{t('microSchools.active')}</option>
          <option value="suspended">{t('microSchools.suspended')}</option>
          <option value="closed">{t('microSchools.closed')}</option>
        </select>
      </div>

      {showCreate && (
        <FormProvider {...methods}>
          <form className="card micro-schools-page__form" onSubmit={methods.handleSubmit(handleCreate)}>
            <FormField<CreateFormValues> name="name" label="microSchools.name" />
            <FormField<CreateFormValues> name="location" label="microSchools.location" />
            <FormField<CreateFormValues> name="city" label="microSchools.city" />
            <FormField<CreateFormValues> name="capacity" label="microSchools.capacity" type="number" />
            <button type="submit" className="btn btn-primary" disabled={createMicroSchoolMutation.isPending}>
              {createMicroSchoolMutation.isPending ? t('app.loading') : t('microSchools.create')}
            </button>
          </form>
        </FormProvider>
      )}

      <div className="micro-schools-grid">
        {filteredSchools.map((school: MicroSchool) => {
          const capacityRate = school.capacity === 0 ? 0 : Math.min(100, Math.round((school.student_count / school.capacity) * 100));
          return (
            <button
              key={school.id}
              type="button"
              className="micro-school-card"
              onClick={() => navigate(`/micro-schools/${school.id}`)}
            >
              <div className="micro-school-card__header">
                <strong>{school.name}</strong>
                <Badge variant={getBadgeVariant(school.status)}>{t(`microSchools.${school.status}`)}</Badge>
              </div>
              <p>{school.location}, {school.city}</p>
              <p>{t('microSchools.students')}: {school.student_count}</p>
              <div className="micro-school-card__capacity">
                <div className="micro-school-card__capacity-bar" style={{ width: `${capacityRate}%` }} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
