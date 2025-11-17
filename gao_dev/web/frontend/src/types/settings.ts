/**
 * TypeScript types for provider settings
 *
 * Story 39.28: Provider Selection Settings Panel
 */

export interface Model {
  id: string;
  name: string;
  description?: string;
}

export interface Provider {
  id: string;
  name: string;
  description: string;
  icon?: string;
  models: Model[];
}

export interface ProviderSettings {
  current_provider: string;
  current_model: string;
  available_providers: Provider[];
}

export interface SaveProviderRequest {
  provider: string;
  model: string;
}

export interface SaveProviderResponse {
  success: boolean;
  message: string;
  validation_errors?: string[];
}
