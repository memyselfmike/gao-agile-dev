/**
 * Settings Panel - Main modal for provider settings
 *
 * Story 39.28: Provider Selection Settings Panel
 */
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import type { ProviderSettings } from '@/types/settings';

interface SettingsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsPanel({ open, onOpenChange }: SettingsPanelProps) {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

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

  // Initialize selections when data loads
  useEffect(() => {
    if (data) {
      setSelectedProvider(data.current_provider);
      setSelectedModel(data.current_model);
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

  // Handle save (placeholder for Story 39.29)
  const handleSave = () => {
    console.log('Saving provider settings:', {
      provider: selectedProvider,
      model: selectedModel,
    });
    // Story 39.29 will implement actual save logic
    // For now, just close the panel
    onOpenChange(false);
  };

  // Handle cancel
  const handleCancel = () => {
    // Reset to current values
    if (data) {
      setSelectedProvider(data.current_provider);
      setSelectedModel(data.current_model);
    }
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
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges || isLoading}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
