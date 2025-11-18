/**
 * ProgressSpinner - Circular progress indicator
 *
 * Story 39.40: Loading States - Progress indicator
 */
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface ProgressSpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

export function ProgressSpinner({ className, size = 'md', message }: ProgressSpinnerProps) {
  const prefersReducedMotion = useReducedMotion();

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-2', className)}
      role="status"
      aria-live="polite"
    >
      <Loader2
        className={cn(
          'text-primary',
          sizeClasses[size],
          !prefersReducedMotion && 'animate-spin'
        )}
      />
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
      <span className="sr-only">Loading...</span>
    </div>
  );
}
