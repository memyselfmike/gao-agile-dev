/**
 * Skeleton - Loading placeholder component with shimmer effect
 *
 * Story 39.40: Loading States - Skeleton with shimmer
 */
import { cn } from '@/lib/utils';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  shimmer?: boolean;
}

export function Skeleton({ className, shimmer = true, ...props }: SkeletonProps) {
  const prefersReducedMotion = useReducedMotion();
  const shouldShimmer = shimmer && !prefersReducedMotion;

  return (
    <div
      className={cn(
        'rounded-md bg-muted',
        shouldShimmer ? 'animate-shimmer' : 'animate-pulse',
        className
      )}
      role="status"
      aria-label="Loading"
      {...props}
    />
  );
}
