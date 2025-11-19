/**
 * TypeScript types for onboarding wizard components
 *
 * Story 41.3: Web Wizard Frontend Components
 */

export interface OnboardingStatus {
  needs_onboarding: boolean;
  completed_steps: string[];
  current_step: string;
  project_defaults: ProjectDefaults;
  git_defaults: GitDefaults;
  available_providers: ProviderInfo[];
}

export interface ProjectDefaults {
  name: string;
  type: string;
  description: string;
}

export interface GitDefaults {
  name: string;
  email: string;
}

export interface ProviderInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  requires_api_key: boolean;
  api_key_env_var: string;
  has_api_key: boolean;
}

export interface ProjectStepData {
  name: string;
  type: string;
  description: string;
}

export interface GitStepData {
  name: string;
  email: string;
}

export interface ProviderStepData {
  provider_id: string;
}

export interface CredentialsStepData {
  api_key: string;
  use_env_var: boolean;
}

export interface StepValidationError {
  field: string;
  message: string;
}

export interface StepResponse {
  success: boolean;
  errors?: StepValidationError[];
  validation?: {
    valid: boolean;
    message?: string;
  };
}

export interface OnboardingCompleteResponse {
  success: boolean;
  config_path?: string;
  message?: string;
  error?: string;
}

export type WizardStep = 'project' | 'git' | 'provider' | 'credentials' | 'completion';

export interface WizardState {
  currentStep: WizardStep;
  projectData: ProjectStepData;
  gitData: GitStepData;
  providerData: ProviderStepData;
  credentialsData: CredentialsStepData;
  selectedProvider: ProviderInfo | null;
  isLoading: boolean;
  errors: Record<string, string>;
}
