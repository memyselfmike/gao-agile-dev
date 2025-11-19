/**
 * Provider Card - Selectable card for AI provider
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Check, Key } from 'lucide-react';
import { Sparkles, Globe, Server, Cpu } from 'lucide-react';
import type { ProviderInfo } from './types';

interface ProviderCardProps {
  provider: ProviderInfo;
  isSelected: boolean;
  onSelect: (provider: ProviderInfo) => void;
}

const providerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  sparkles: Sparkles,
  globe: Globe,
  server: Server,
  cpu: Cpu,
};

export function ProviderCard({ provider, isSelected, onSelect }: ProviderCardProps) {
  const IconComponent = provider.icon
    ? providerIcons[provider.icon] || Sparkles
    : Sparkles;

  const handleClick = () => {
    onSelect(provider);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(provider);
    }
  };

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:border-primary/50',
        isSelected && 'border-2 border-primary bg-primary/5'
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="option"
      aria-selected={isSelected}
      aria-label={`${provider.name}: ${provider.description}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-lg',
                isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted'
              )}
            >
              <IconComponent className="h-5 w-5" aria-hidden="true" />
            </div>

            <div className="flex-1">
              <h3 className="font-medium">{provider.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {provider.description}
              </p>

              <div className="mt-2 flex items-center gap-2">
                {provider.requires_api_key && (
                  <div
                    className={cn(
                      'flex items-center gap-1 text-xs',
                      provider.has_api_key ? 'text-green-600' : 'text-muted-foreground'
                    )}
                  >
                    <Key className="h-3 w-3" aria-hidden="true" />
                    <span>
                      {provider.has_api_key
                        ? 'API key configured'
                        : `Requires ${provider.api_key_env_var}`}
                    </span>
                  </div>
                )}

                {!provider.requires_api_key && (
                  <div className="flex items-center gap-1 text-xs text-green-600">
                    <Check className="h-3 w-3" aria-hidden="true" />
                    <span>No API key required</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {isSelected && (
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <Check className="h-3 w-3" aria-hidden="true" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
