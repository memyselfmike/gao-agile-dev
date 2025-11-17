/**
 * Current Provider Badge - Shows active provider/model
 *
 * Story 39.28: Provider Selection Settings Panel
 */
import { CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface CurrentProviderBadgeProps {
  provider: string;
  model: string;
}

const providerNames: Record<string, string> = {
  claude_code: 'Claude Code',
  opencode: 'OpenCode',
  ollama: 'Ollama (Local)',
};

export function CurrentProviderBadge({
  provider,
  model,
}: CurrentProviderBadgeProps) {
  const displayName = providerNames[provider] || provider;

  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/50 p-4">
      <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-500 dark:text-green-400 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
          Current Provider
        </div>
        <div className="font-semibold text-foreground break-words">
          {displayName}
        </div>
        <div className="text-sm text-muted-foreground mt-1 break-all">
          {model}
        </div>
      </div>
      <Badge variant="secondary" className="flex-shrink-0">
        Active
      </Badge>
    </div>
  );
}
