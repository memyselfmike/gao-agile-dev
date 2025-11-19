/**
 * Onboarding components barrel export
 *
 * Story 41.3: Web Wizard Frontend Components
 */

export { OnboardingWizard } from './OnboardingWizard';
export { StepIndicator } from './StepIndicator';
export { ProjectStep } from './ProjectStep';
export { GitStep } from './GitStep';
export { ProviderStep } from './ProviderStep';
export { CredentialsStep } from './CredentialsStep';
export { CompletionStep } from './CompletionStep';
export { ProviderCard } from './ProviderCard';

export type {
  OnboardingStatus,
  ProjectDefaults,
  GitDefaults,
  ProviderInfo,
  ProjectStepData,
  GitStepData,
  ProviderStepData,
  CredentialsStepData,
  StepValidationError,
  StepResponse,
  OnboardingCompleteResponse,
  WizardStep,
  WizardState,
} from './types';
