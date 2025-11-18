/**
 * Settings Panel - Main modal for provider settings
 *
 * Story 39.28: Provider Selection Settings Panel
 * Story 39.29: Provider Validation and Persistence
 */
import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ProviderSelect } from './ProviderSelect';
import { ModelSelect } from './ModelSelect';
import { CurrentProviderBadge } from './CurrentProviderBadge';
import { ValidationIndicator } from './ValidationIndicator';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { getApiUrl } from '@/lib/api';
import type { ProviderSettings, ValidationStatus, SaveProviderResponse } from '@/types/settings';

interface SettingsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsPanel({ open, onOpenChange }: SettingsPanelProps) {
  const apiUrl = getApiUrl();

  // Fetch provider settings
  const { data, isLoading, error } = useQuery<ProviderSettings>({
    queryKey: ['provider-settings'],
    queryFn: async () => {
      const response = await fetch(`${apiUrl}/api/settings/provider`);
      if (!response.ok) {
        throw new Error('Failed to fetch provider settings');
      }
      return response.json();
    },
    enabled: open,
  });

  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [validationStatus, setValidationStatus] = useState<ValidationStatus | null>(null);
  const initializedRef = useRef(false);

  const queryClient = useQueryClient();

  // Initialize selections when data loads (once only)
  useEffect(() => {
    if (data && !initializedRef.current) {
      setSelectedProvider(data.current_provider);
      setSelectedModel(data.current_model);
      initializedRef.current = true;
    }
  }, [data]);

  // Check if there are changes
  const hasChanges =
    data &&
    (selectedProvider !== data.current_provider ||
      selectedModel !== data.current_model);

  // Handle provider change
  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);

    // Auto-select first model from new provider
    const provider = data?.available_providers.find((p: { id: string }) => p.id === providerId);
    if (provider && provider.models.length > 0) {
      setSelectedModel(provider.models[0].id);
    } else {
      setSelectedModel('');
    }
  };

  // Handle model change
  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
  };

  // Save mutation (Story 39.29)
  const saveMutation = useMutation({
    mutationFn: async ({ provider, model }: { provider: string; model: string }) => {
      const response = await fetch(`${apiUrl}/api/settings/provider`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, model }),
      });
      if (!response.ok) {
        throw new Error('Failed to save provider settings');
      }
      return response.json() as Promise<SaveProviderResponse>;
    },
    onSuccess: (responseData) => {
      if (responseData.success) {
        // Show success toast
        toast.success(responseData.message || 'Provider settings saved', {
          duration: 5000,
        });

        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: ['provider-settings'] });

        // Reset initialization flag
        initializedRef.current = false;

        // Close panel
        onOpenChange(false);
      } else {
        // Show error toast with fix suggestion
        toast.error(responseData.error || 'Failed to save settings', {
          description: responseData.fix_suggestion,
          duration: Infinity, // Persist until dismissed
        });
      }
    },
    onError: (error) => {
      toast.error('Failed to save settings', {
        description: error.message,
        duration: Infinity,
      });
    },
  });

  // Real-time validation (debounced 500ms)
  const debouncedProvider = useDebouncedValue(selectedProvider, 500);
  const debouncedModel = useDebouncedValue(selectedModel, 500);

  useEffect(() => {
    if (debouncedProvider && debouncedModel) {
      // Fetch validation status
      fetch(`${apiUrl}/api/settings/provider/validate?provider=${debouncedProvider}&model=${debouncedModel}`)
        .then((res) => res.json())
        .then((data: ValidationStatus) => setValidationStatus(data))
        .catch(() => setValidationStatus(null));
    }
  }, [debouncedProvider, debouncedModel, apiUrl]);

  // Handle save
  const handleSave = () => {
    saveMutation.mutate({ provider: selectedProvider, model: selectedModel });
  };

  // Handle cancel
  const handleCancel = () => {
    // Reset to current values
    if (data) {
      setSelectedProvider(data.current_provider);
      setSelectedModel(data.current_model);
    }
    initializedRef.current = false;
    onOpenChange(false);
  };

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        handleCancel();
      }
    };

    if (open) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [open, data]);

  // Get selected provider's models
  const selectedProviderModels =
    data?.available_providers.find((p: { id: string }) => p.id === selectedProvider)?.models ||
    [];

  // Determine if save button should be disabled
  const isSaveDisabled =
    !hasChanges ||
    saveMutation.isPending ||
    (validationStatus !== null && !validationStatus.valid);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>AI Provider Settings</DialogTitle>
          <DialogDescription>
            Configure which AI provider and model to use for agent interactions.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-sm text-muted-foreground">
              Loading settings...
            </div>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <div className="text-sm font-medium text-destructive">
              Failed to load settings
            </div>
            <div className="text-xs text-destructive/80 mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </div>
          </div>
        ) : data ? (
          <div className="space-y-4 py-4">
            {/* Current Provider Badge */}
            <CurrentProviderBadge
              provider={data.current_provider}
              model={data.current_model}
            />

            <Separator />

            {/* Provider Selection */}
            <ProviderSelect
              providers={data.available_providers}
              value={selectedProvider}
              onChange={handleProviderChange}
            />

            {/* Model Selection */}
            <ModelSelect
              models={selectedProviderModels}
              value={selectedModel}
              onChange={handleModelChange}
              disabled={selectedProviderModels.length === 0}
            />

            {/* Validation Indicator */}
            {validationStatus && <ValidationIndicator status={validationStatus} />}

            {/* Change indicator */}
            {hasChanges && (
              <div className="rounded-lg bg-blue-500/10 border border-blue-500/30 p-3">
                <div className="text-xs font-medium text-blue-600 dark:text-blue-400">
                  You have unsaved changes
                </div>
              </div>
            )}
          </div>
        ) : null}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={handleCancel} disabled={saveMutation.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaveDisabled}>
            {saveMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
