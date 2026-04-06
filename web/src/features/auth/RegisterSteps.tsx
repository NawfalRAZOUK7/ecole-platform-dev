import type { RegisterStepsProps } from './register.types';

export function RegisterSteps({ currentStep, steps }: RegisterStepsProps) {
  const stepIndex = steps.indexOf(currentStep);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 20 }}>
      {steps.map((step, index) => (
        <div
          key={step}
          style={{
            width: 32,
            height: 4,
            borderRadius: 2,
            background: index <= stepIndex ? 'var(--color-primary)' : 'var(--color-border)',
          }}
        />
      ))}
    </div>
  );
}
