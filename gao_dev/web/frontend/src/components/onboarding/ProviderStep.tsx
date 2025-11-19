/**
 * Provider Step - AI provider selection
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { ProviderCard } from './ProviderCard';
import type { ProviderInfo, ProviderStepData } from './types';

interface ProviderStepProps {
  data: ProviderStepData;
  providers: ProviderInfo[];
  errors: Record<string, string>;
  onChange: (data: ProviderStepData, provider: ProviderInfo) => void;
}

export function ProviderStep({ data, providers, errors, onChange }: ProviderStepProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Focus container on mount
  useEffect(() => {
    // Focus first provider card
    const firstCard = containerRef.current?.querySelector('[role="option"]') as HTMLElement;
    firstCard?.focus();
  }, []);

  const handleSelect = (provider: ProviderInfo) => {
    onChange({ provider_id: provider.id }, provider);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">AI Provider</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Select your preferred AI provider
        </p>
      </div>

      <div
        ref={containerRef}
        role="listbox"
        aria-label="Available AI providers"
        className={cn(
          'grid gap-4',
          providers.length <= 2 ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2'
        )}
      >
        {providers.map((provider) => (
          <ProviderCard
            key={provider.id}
            provider={provider}
            isSelected={data.provider_id === provider.id}
            onSelect={handleSelect}
          />
        ))}
      </div>

      {errors.provider_id && (
        <p className="text-sm text-destructive" role="alert">
          {errors.provider_id}
        </p>
      )}
    </div>
  );
}
