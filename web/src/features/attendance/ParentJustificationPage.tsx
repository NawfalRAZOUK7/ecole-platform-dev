import { useMemo, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { ErrorBanner, FileUpload, FormField, FormTextarea } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useSubmitJustification } from './useAttendance';

const justificationSchema = z.object({
  attendanceRecordId: z.string().min(1, 'justification.attendanceRecordId'),
  reason: z.string().min(3, 'justification.reason').max(2000, 'justification.reason'),
});

type JustificationFormValues = z.infer<typeof justificationSchema>;

type Step = 'form' | 'done';

export function ParentJustificationPage() {
  const { t } = useTranslation();
  const [step, setStep] = useState<Step>('form');
  const [attachment, setAttachment] = useState<File | undefined>(undefined);
  const submitJustificationMutation = useSubmitJustification();
  const methods = useForm<JustificationFormValues>({
    resolver: zodResolver(justificationSchema),
    defaultValues: {
      attendanceRecordId: '',
      reason: '',
    },
  });

  const bannerError = useMemo(
    () => toBannerError(submitJustificationMutation.error, t('app.error')),
    [submitJustificationMutation.error, t]
  );

  async function handleSubmit(values: JustificationFormValues) {
    await submitJustificationMutation.mutateAsync({
      recordId: values.attendanceRecordId.trim(),
      justification: values.reason.trim(),
      file: attachment,
    });
    setStep('done');
  }

  function handleReset() {
    methods.reset();
    setAttachment(undefined);
    setStep('form');
  }

  return (
    <div className="page attendance-justification-page">
      <h1 className="page-title">{t('justification.title')}</h1>

      <ErrorBanner error={bannerError} />

      {step === 'done' ? (
        <div className="card attendance-banner attendance-banner--success">
          <h2 className="attendance-page__section-title">{t('justification.success')}</h2>
          <p className="attendance-page__summary">{t('justification.successMessage')}</p>
          <button type="button" className="btn btn-primary" onClick={handleReset}>
            {t('justification.submitAnother')}
          </button>
        </div>
      ) : (
        <FormProvider {...methods}>
          <form onSubmit={methods.handleSubmit(handleSubmit)} className="attendance-justification-page__form">
            <div className="card attendance-justification-page__card">
              <p className="attendance-page__summary">{t('justification.instructions')}</p>

              <FormField<JustificationFormValues>
                name="attendanceRecordId"
                label="justification.attendanceRecordId"
                placeholder="justification.recordIdPlaceholder"
                disabled={submitJustificationMutation.isPending}
              />

              <FormTextarea<JustificationFormValues>
                name="reason"
                label="justification.reason"
                placeholder="justification.reasonPlaceholder"
                rows={5}
                maxLength={2000}
                disabled={submitJustificationMutation.isPending}
              />

              <div className="attendance-justification-page__upload">
                <span className="attendance-filter__label">{t('justification.attachFile')}</span>
                <FileUpload
                  maxFiles={1}
                  maxSizeMb={5}
                  accept=".pdf,.jpg,.jpeg,.png"
                  disabled={submitJustificationMutation.isPending}
                  onFilesSelected={(files) => {
                    setAttachment(files[0]);
                  }}
                />
              </div>

              <div className="attendance-page__actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitJustificationMutation.isPending}
                >
                  {submitJustificationMutation.isPending ? t('app.loading') : t('justification.submit')}
                </button>
              </div>
            </div>
          </form>
        </FormProvider>
      )}
    </div>
  );
}
