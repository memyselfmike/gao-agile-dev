/**
 * ValidationIndicator - API key status indicator
 *
 * Story 39.29: Provider Validation and Persistence
 */
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import type { ValidationStatus } from '@/types/settings';

interface ValidationIndicatorProps {
  status: ValidationStatus | null;
}

export function ValidationIndicator({ status }: ValidationIndicatorProps) {
  if (!status) {
    return null;
  }

  // Determine display based on api_key_status
  const getStatusConfig = () => {
    if (status.api_key_status === 'valid') {
      return {
        icon: CheckCircle2,
        color: 'text-green-600 dark:text-green-400',
        bgColor: 'bg-green-50 dark:bg-green-950/30',
        borderColor: 'border-green-200 dark:border-green-800',
        message: 'API key configured',
      };
    } else if (status.api_key_status === 'invalid') {
      return {
        icon: XCircle,
        color: 'text-red-600 dark:text-red-400',
        bgColor: 'bg-red-50 dark:bg-red-950/30',
        borderColor: 'border-red-200 dark:border-red-800',
        message: 'Invalid API key',
      };
    } else if (status.api_key_status === 'missing') {
      return {
        icon: AlertTriangle,
        color: 'text-yellow-600 dark:text-yellow-400',
        bgColor: 'bg-yellow-50 dark:bg-yellow-950/30',
        borderColor: 'border-yellow-200 dark:border-yellow-800',
        message: 'API key missing',
      };
    } else {
      return {
        icon: AlertTriangle,
        color: 'text-gray-600 dark:text-gray-400',
        bgColor: 'bg-gray-50 dark:bg-gray-950/30',
        borderColor: 'border-gray-200 dark:border-gray-800',
        message: 'Checking...',
      };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div
      className={`rounded-lg border ${config.borderColor} ${config.bgColor} p-3 flex items-center gap-2`}
    >
      <Icon className={`${config.color} h-5 w-5 flex-shrink-0`} />
      <div className="flex-1">
        <div className={`text-sm font-medium ${config.color}`}>
          {config.message}
        </div>
        {status.error && (
          <div className="text-xs text-muted-foreground mt-1">
            {status.error}
          </div>
        )}
        {status.fix_suggestion && (
          <div className="text-xs text-muted-foreground mt-1">
            {status.fix_suggestion}
          </div>
        )}
      </div>
    </div>
  );
}
