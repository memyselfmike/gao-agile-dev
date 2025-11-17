/**
 * Provider Select - Dropdown for selecting AI provider
 *
 * Story 39.28: Provider Selection Settings Panel
 */
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import type { Provider } from '@/types/settings';
import { Sparkles, Globe, Server } from 'lucide-react';

interface ProviderSelectProps {
  providers: Provider[];
  value: string;
  onChange: (value: string) => void;
}

const providerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  sparkles: Sparkles,
  globe: Globe,
  server: Server,
};

export function ProviderSelect({
  providers,
  value,
  onChange,
}: ProviderSelectProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="provider" className="text-sm font-medium">
        AI Provider
      </Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="provider" className="w-full">
          <SelectValue placeholder="Select provider" />
        </SelectTrigger>
        <SelectContent>
          {providers.map((provider) => {
            const IconComponent = provider.icon
              ? providerIcons[provider.icon] || Sparkles
              : Sparkles;

            return (
              <SelectItem key={provider.id} value={provider.id}>
                <div className="flex items-center gap-2">
                  <IconComponent className="h-4 w-4 text-muted-foreground" />
                  <div className="flex flex-col">
                    <span className="font-medium">{provider.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {provider.description}
                    </span>
                  </div>
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
}
