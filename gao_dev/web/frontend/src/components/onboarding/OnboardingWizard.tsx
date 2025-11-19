/**
 * Onboarding Wizard - Main container for web onboarding flow
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { apiRequest } from '@/lib/api';
import { ArrowLeft, ArrowRight, Rocket, Loader2 } from 'lucide-react';
import { StepIndicator } from './StepIndicator';
import { ProjectStep } from './ProjectStep';
import { GitStep } from './GitStep';
import { ProviderStep } from './ProviderStep';
import { CredentialsStep } from './CredentialsStep';
import { CompletionStep } from './CompletionStep';
import type {
  OnboardingStatus,
  WizardStep,
  WizardState,
  ProjectStepData,
  GitStepData,
  ProviderStepData,
  CredentialsStepData,
  ProviderInfo,
  StepResponse,
  OnboardingCompleteResponse,
} from './types';

interface OnboardingWizardProps {
  onComplete?: () => void;
}

const STEP_ORDER: WizardStep[] = ['project', 'git', 'provider', 'credentials', 'completion'];

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [isInitializing, setIsInitializing] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message?: string;
  } | null>(null);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [completedSteps, setCompletedSteps] = useState<WizardStep[]>([]);
  const [initError, setInitError] = useState<string | null>(null);

  const [state, setState] = useState<WizardState>({
    currentStep: 'project',
    projectData: { name: '', type: '', description: '' },
    gitData: { name: '', email: '' },
    providerData: { provider_id: '' },
    credentialsData: { api_key: '', use_env_var: false },
    selectedProvider: null,
    isLoading: false,
    errors: {},
  });

  // Fetch initial status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await apiRequest('/api/onboarding/status');
        if (!response.ok) {
          throw new Error('Failed to fetch onboarding status');
        }

        const data = (await response.json()) as OnboardingStatus;

        // Update state with defaults
        setState((prev) => ({
          ...prev,
          projectData: {
            name: data.project_defaults.name,
            type: data.project_defaults.type,
            description: data.project_defaults.description,
          },
          gitData: {
            name: data.git_defaults.name,
            email: data.git_defaults.email,
          },
          currentStep: (data.current_step as WizardStep) || 'project',
        }));

        setProviders(data.available_providers);
        setCompletedSteps(data.completed_steps as WizardStep[]);
      } catch (error) {
        setInitError(
          error instanceof Error ? error.message : 'Failed to initialize wizard'
        );
      } finally {
        setIsInitializing(false);
      }
    };

    fetchStatus();
  }, []);

  // Validation helpers
  const validateProjectStep = (): boolean => {
    const errors: Record<string, string> = {};

    if (!state.projectData.name.trim()) {
      errors.name = 'Project name is required';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(state.projectData.name)) {
      errors.name = 'Project name can only contain letters, numbers, hyphens, and underscores';
    }

    setState((prev) => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  const validateGitStep = (): boolean => {
    const errors: Record<string, string> = {};

    if (!state.gitData.name.trim()) {
      errors.name = 'Git user name is required';
    }

    if (!state.gitData.email.trim()) {
      errors.email = 'Git email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(state.gitData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    setState((prev) => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  const validateProviderStep = (): boolean => {
    const errors: Record<string, string> = {};

    if (!state.providerData.provider_id) {
      errors.provider_id = 'Please select a provider';
    }

    setState((prev) => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  const validateCredentialsStep = (): boolean => {
    const errors: Record<string, string> = {};
    const provider = state.selectedProvider;

    if (provider?.requires_api_key) {
      if (!state.credentialsData.use_env_var && !state.credentialsData.api_key.trim()) {
        errors.api_key = 'API key is required';
      }

      if (state.credentialsData.use_env_var && !provider.has_api_key) {
        errors.api_key = `Environment variable ${provider.api_key_env_var} is not set`;
      }
    }

    setState((prev) => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  // Submit step to API
  const submitStep = useCallback(
    async (step: WizardStep): Promise<boolean> => {
      setIsSubmitting(true);

      try {
        let body: object;

        switch (step) {
          case 'project':
            body = state.projectData;
            break;
          case 'git':
            body = state.gitData;
            break;
          case 'provider':
            body = state.providerData;
            break;
          case 'credentials':
            body = state.credentialsData;
            break;
          default:
            body = {};
        }

        const response = await apiRequest(`/api/onboarding/${step}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        const data = (await response.json()) as StepResponse;

        if (!data.success && data.errors) {
          const errors: Record<string, string> = {};
          data.errors.forEach((err) => {
            errors[err.field] = err.message;
          });
          setState((prev) => ({ ...prev, errors }));
          return false;
        }

        // Mark step as completed
        if (!completedSteps.includes(step)) {
          setCompletedSteps((prev) => [...prev, step]);
        }

        return true;
      } catch (error) {
        setState((prev) => ({
          ...prev,
          errors: {
            general:
              error instanceof Error ? error.message : 'Failed to save step',
          },
        }));
        return false;
      } finally {
        setIsSubmitting(false);
      }
    },
    [state, completedSteps]
  );

  // Validate API key
  const handleValidateApiKey = async () => {
    setIsValidating(true);
    setValidationResult(null);

    try {
      const response = await apiRequest('/api/onboarding/validate-credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: state.providerData.provider_id,
          api_key: state.credentialsData.api_key,
        }),
      });

      const data = (await response.json()) as { valid: boolean; message?: string };
      setValidationResult(data);
    } catch (error) {
      setValidationResult({
        valid: false,
        message: error instanceof Error ? error.message : 'Validation failed',
      });
    } finally {
      setIsValidating(false);
    }
  };

  // Navigation
  const handleNext = async () => {
    const currentIndex = STEP_ORDER.indexOf(state.currentStep);

    // Validate current step
    let isValid = false;
    switch (state.currentStep) {
      case 'project':
        isValid = validateProjectStep();
        break;
      case 'git':
        isValid = validateGitStep();
        break;
      case 'provider':
        isValid = validateProviderStep();
        break;
      case 'credentials':
        isValid = validateCredentialsStep();
        break;
      case 'completion':
        isValid = true;
        break;
    }

    if (!isValid) return;

    // Submit to API (except for completion step)
    if (state.currentStep !== 'completion') {
      const success = await submitStep(state.currentStep);
      if (!success) return;
    }

    // Move to next step
    if (currentIndex < STEP_ORDER.length - 1) {
      setState((prev) => ({
        ...prev,
        currentStep: STEP_ORDER[currentIndex + 1],
        errors: {},
      }));
      setValidationResult(null);
    }
  };

  const handleBack = () => {
    const currentIndex = STEP_ORDER.indexOf(state.currentStep);
    if (currentIndex > 0) {
      setState((prev) => ({
        ...prev,
        currentStep: STEP_ORDER[currentIndex - 1],
        errors: {},
      }));
      setValidationResult(null);
    }
  };

  const handleComplete = async () => {
    setIsSubmitting(true);

    try {
      const response = await apiRequest('/api/onboarding/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = (await response.json()) as OnboardingCompleteResponse;

      if (data.success) {
        onComplete?.();
      } else {
        setState((prev) => ({
          ...prev,
          errors: { general: data.error || 'Failed to complete setup' },
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        errors: {
          general:
            error instanceof Error ? error.message : 'Failed to complete setup',
        },
      }));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Update handlers
  const handleProjectChange = (data: ProjectStepData) => {
    setState((prev) => ({
      ...prev,
      projectData: data,
      errors: {},
    }));
  };

  const handleGitChange = (data: GitStepData) => {
    setState((prev) => ({
      ...prev,
      gitData: data,
      errors: {},
    }));
  };

  const handleProviderChange = (data: ProviderStepData, provider: ProviderInfo) => {
    setState((prev) => ({
      ...prev,
      providerData: data,
      selectedProvider: provider,
      errors: {},
    }));
  };

  const handleCredentialsChange = (data: CredentialsStepData) => {
    setState((prev) => ({
      ...prev,
      credentialsData: data,
      errors: {},
    }));
    setValidationResult(null);
  };

  // Loading state
  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" message="Loading wizard..." />
      </div>
    );
  }

  // Error state
  if (initError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">{initError}</p>
          <Button
            className="mt-4"
            onClick={() => window.location.reload()}
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const currentStepIndex = STEP_ORDER.indexOf(state.currentStep);
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = state.currentStep === 'completion';

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-[600px]">
        <StepIndicator
          currentStep={state.currentStep}
          completedSteps={completedSteps}
        />

        <div className="rounded-lg border bg-card p-6 shadow-sm">
          {/* Step content */}
          <div className="mb-6">
            {state.currentStep === 'project' && (
              <ProjectStep
                data={state.projectData}
                errors={state.errors}
                onChange={handleProjectChange}
              />
            )}

            {state.currentStep === 'git' && (
              <GitStep
                data={state.gitData}
                errors={state.errors}
                onChange={handleGitChange}
              />
            )}

            {state.currentStep === 'provider' && (
              <ProviderStep
                data={state.providerData}
                providers={providers}
                errors={state.errors}
                onChange={handleProviderChange}
              />
            )}

            {state.currentStep === 'credentials' && (
              <CredentialsStep
                data={state.credentialsData}
                provider={state.selectedProvider}
                errors={state.errors}
                isValidating={isValidating}
                validationResult={validationResult}
                onChange={handleCredentialsChange}
                onValidate={handleValidateApiKey}
              />
            )}

            {state.currentStep === 'completion' && (
              <CompletionStep
                projectData={state.projectData}
                gitData={state.gitData}
                provider={state.selectedProvider}
                useEnvVar={state.credentialsData.use_env_var}
              />
            )}
          </div>

          {/* General error */}
          {state.errors.general && (
            <div className="mb-4 text-sm text-destructive" role="alert">
              {state.errors.general}
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex items-center justify-between">
            <div>
              {!isFirstStep && (
                <Button
                  variant="outline"
                  onClick={handleBack}
                  disabled={isSubmitting}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" aria-hidden="true" />
                  Back
                </Button>
              )}
            </div>

            <div>
              {isLastStep ? (
                <Button onClick={handleComplete} disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2
                        className="mr-2 h-4 w-4 animate-spin"
                        aria-hidden="true"
                      />
                      Finishing...
                    </>
                  ) : (
                    <>
                      <Rocket className="mr-2 h-4 w-4" aria-hidden="true" />
                      Start Building
                    </>
                  )}
                </Button>
              ) : (
                <Button onClick={handleNext} disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2
                        className="mr-2 h-4 w-4 animate-spin"
                        aria-hidden="true"
                      />
                      Saving...
                    </>
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
