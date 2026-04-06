import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { ErrorBanner, FormField, FormSelect } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useCreateMicroPayment, useEnrollMicroStudent } from './useMicroSchools';

const enrollSchema = z.object({
  student_id: z.string().min(1),
  student_name: z.string().min(2),
  payment_amount: z.coerce.number().gt(0),
  payment_status: z.enum(['pending', 'paid']),
});

type EnrollFormValues = z.infer<typeof enrollSchema>;

const STUDENT_OPTIONS = [
  { value: 'student-1', label: 'Student 1' },
  { value: 'student-2', label: 'Student 2' },
  { value: 'student-3', label: 'Student 3' },
];

export function MicroSchoolEnrollPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const enrollMutation = useEnrollMicroStudent();
  const createPaymentMutation = useCreateMicroPayment();
  const methods = useForm<EnrollFormValues>({
    resolver: zodResolver(enrollSchema) as Resolver<EnrollFormValues>,
    defaultValues: {
      student_id: '',
      student_name: '',
      payment_amount: 0,
      payment_status: 'pending',
    },
  });

  async function handleSubmit(values: EnrollFormValues) {
    await enrollMutation.mutateAsync({
      microSchoolId: id,
      payload: values,
    });
    await createPaymentMutation.mutateAsync({
      microSchoolId: id,
      payload: {
        student_id: values.student_id,
        amount: values.payment_amount,
        status: values.payment_status,
      },
    });
    navigate(`/micro-schools/${id}`);
  }

  return (
    <div className="page micro-school-enroll-page">
      <div className="page-header">
        <h1 className="page-title">{t('microSchools.enroll')}</h1>
      </div>

      <ErrorBanner error={toBannerError(enrollMutation.error ?? createPaymentMutation.error, t('app.error'))} />

      <FormProvider {...methods}>
        <form className="card micro-schools-page__form" onSubmit={methods.handleSubmit(handleSubmit)}>
          <FormSelect<EnrollFormValues>
            name="student_id"
            label="microSchools.student"
            options={STUDENT_OPTIONS}
            placeholder="microSchools.selectStudent"
          />
          <FormField<EnrollFormValues> name="student_name" label="microSchools.studentName" />
          <FormField<EnrollFormValues> name="payment_amount" label="microSchools.amount" type="number" />
          <FormSelect<EnrollFormValues>
            name="payment_status"
            label="microSchools.paymentStatus"
            options={[
              { value: 'pending', label: 'microSchools.pending' },
              { value: 'paid', label: 'microSchools.paid' },
            ]}
          />
          <button type="submit" className="btn btn-primary" disabled={enrollMutation.isPending || createPaymentMutation.isPending}>
            {(enrollMutation.isPending || createPaymentMutation.isPending) ? t('app.loading') : t('microSchools.enroll')}
          </button>
        </form>
      </FormProvider>
    </div>
  );
}
