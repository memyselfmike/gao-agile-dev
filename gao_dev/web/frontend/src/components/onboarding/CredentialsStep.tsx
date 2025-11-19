/**
 * Credentials Step - API key input with validation
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { useEffect, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { CredentialsStepData, ProviderInfo } from './types';

interface CredentialsStepProps {
  data: CredentialsStepData;
  provider: ProviderInfo | null;
  errors: Record<string, string>;
  isValidating: boolean;
  validationResult: { valid: boolean; message?: string } | null;
  onChange: (data: CredentialsStepData) => void;
  onValidate: () => void;
}

export function CredentialsStep({
  data,
  provider,
  errors,
  isValidating,
  validationResult,
  onChange,
  onValidate,
}: CredentialsStepProps) {
  const apiKeyInputRef = useRef<HTMLInputElement>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Focus first field on mount
  useEffect(() => {
    if (!data.use_env_var) {
      apiKeyInputRef.current?.focus();
    }
  }, [data.use_env_var]);

  const handleApiKeyChange = (value: string) => {
    onChange({
      ...data,
      api_key: value,
    });
  };

  const handleEnvVarToggle = () => {
    onChange({
      ...data,
      use_env_var: !data.use_env_var,
      api_key: '',
    });
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  // If provider doesn't require API key, show success message
  if (provider && !provider.requires_api_key) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold">Credentials</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure API credentials
          </p>
        </div>

        <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950">
          <CheckCircle className="h-5 w-5 text-green-600" aria-hidden="true" />
          <div>
            <p className="font-medium text-green-800 dark:text-green-200">
              No API key required
            </p>
            <p className="text-sm text-green-700 dark:text-green-300">
              {provider.name} does not require an API key
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Credentials</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure API credentials for {provider?.name || 'the provider'}
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="use-env-var"
            checked={data.use_env_var}
            onChange={handleEnvVarToggle}
            className="h-4 w-4 rounded border-input"
          />
          <Label htmlFor="use-env-var" className="cursor-pointer">
            Use environment variable ({provider?.api_key_env_var})
          </Label>
        </div>

        {!data.use_env_var && (
          <div className="space-y-2">
            <Label htmlFor="api-key">
              API Key
              <span className="text-destructive" aria-hidden="true">
                {' '}
                *
              </span>
            </Label>
            <div className="relative">
              <Input
                ref={apiKeyInputRef}
                id="api-key"
                type={showPassword ? 'text' : 'password'}
                value={data.api_key}
                onChange={(e) => handleApiKeyChange(e.target.value)}
                placeholder="Enter your API key"
                aria-required="true"
                aria-invalid={!!errors.api_key}
                aria-describedby={
                  errors.api_key
                    ? 'api-key-error'
                    : validationResult
                      ? 'api-key-validation'
                      : undefined
                }
                className={cn(
                  'pr-10',
                  errors.api_key && 'border-destructive',
                  validationResult?.valid && 'border-green-500'
                )}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={togglePasswordVisibility}
                aria-label={showPassword ? 'Hide API key' : 'Show API key'}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>

            {errors.api_key && (
              <p
                id="api-key-error"
                className="text-sm text-destructive"
                role="alert"
              >
                {errors.api_key}
              </p>
            )}
          </div>
        )}

        {data.use_env_var && provider?.has_api_key && (
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle className="h-4 w-4" aria-hidden="true" />
            <span>Environment variable {provider.api_key_env_var} is set</span>
          </div>
        )}

        {data.use_env_var && provider && !provider.has_api_key && (
          <div className="flex items-center gap-2 text-sm text-destructive">
            <XCircle className="h-4 w-4" aria-hidden="true" />
            <span>Environment variable {provider.api_key_env_var} is not set</span>
          </div>
        )}

        {/* Validation button and result */}
        {!data.use_env_var && data.api_key && (
          <div className="space-y-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onValidate}
              disabled={isValidating || !data.api_key}
            >
              {isValidating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Validating...
                </>
              ) : (
                'Validate API Key'
              )}
            </Button>

            {validationResult && (
              <div
                id="api-key-validation"
                className={cn(
                  'flex items-center gap-2 text-sm',
                  validationResult.valid ? 'text-green-600' : 'text-destructive'
                )}
                role="status"
                aria-live="polite"
              >
                {validationResult.valid ? (
                  <CheckCircle className="h-4 w-4" aria-hidden="true" />
                ) : (
                  <XCircle className="h-4 w-4" aria-hidden="true" />
                )}
                <span>
                  {validationResult.message ||
                    (validationResult.valid
                      ? 'API key is valid'
                      : 'API key validation failed')}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
