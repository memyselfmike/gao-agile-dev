/**
 * ActivitySkeleton - Loading skeleton for activity feed
 *
 * Story 39.40: Loading States - Skeleton loaders
 */
import { Skeleton } from '@/components/ui/skeleton';

export function ActivitySkeleton() {
  return (
    <div className="space-y-4 p-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="space-y-2 rounded-lg border p-4">
          {/* Header */}
          <div className="flex items-center gap-2">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="ml-auto h-4 w-16" />
          </div>
          {/* Content */}
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      ))}
    </div>
  );
}
