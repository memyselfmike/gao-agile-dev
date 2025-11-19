/**
 * Step Indicator - Displays wizard progress
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';
import type { WizardStep } from './types';

interface StepIndicatorProps {
  currentStep: WizardStep;
  completedSteps: WizardStep[];
}

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'project', label: 'Project' },
  { key: 'git', label: 'Git' },
  { key: 'provider', label: 'Provider' },
  { key: 'credentials', label: 'Credentials' },
  { key: 'completion', label: 'Complete' },
];

export function StepIndicator({ currentStep, completedSteps }: StepIndicatorProps) {
  const currentStepIndex = STEPS.findIndex((s) => s.key === currentStep);
  const currentStepNumber = currentStepIndex + 1;
  const totalSteps = STEPS.length;

  return (
    <div className="mb-8">
      <div className="mb-4 text-center">
        <span
          className="text-sm font-medium text-muted-foreground"
          aria-live="polite"
          aria-atomic="true"
        >
          Step {currentStepNumber} of {totalSteps}
        </span>
      </div>

      <nav aria-label="Onboarding progress">
        <ol className="flex items-center justify-center gap-2">
          {STEPS.map((step, index) => {
            const isCompleted = completedSteps.includes(step.key);
            const isCurrent = step.key === currentStep;
            const isPast = index < currentStepIndex;

            return (
              <li key={step.key} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors',
                      isCompleted || isPast
                        ? 'border-primary bg-primary text-primary-foreground'
                        : isCurrent
                          ? 'border-primary bg-background text-primary'
                          : 'border-muted bg-background text-muted-foreground'
                    )}
                    aria-current={isCurrent ? 'step' : undefined}
                  >
                    {isCompleted || isPast ? (
                      <Check className="h-4 w-4" aria-hidden="true" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                  <span
                    className={cn(
                      'mt-1 text-xs',
                      isCurrent ? 'font-medium text-foreground' : 'text-muted-foreground'
                    )}
                  >
                    {step.label}
                  </span>
                </div>

                {index < STEPS.length - 1 && (
                  <div
                    className={cn(
                      'mx-2 h-0.5 w-8',
                      isPast ? 'bg-primary' : 'bg-muted'
                    )}
                    aria-hidden="true"
                  />
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
}
