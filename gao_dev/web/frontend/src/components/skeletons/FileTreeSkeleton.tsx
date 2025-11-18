/**
 * FileTreeSkeleton - Loading skeleton for file tree
 *
 * Story 39.40: Loading States - Skeleton loaders
 */
import { Skeleton } from '@/components/ui/skeleton';

export function FileTreeSkeleton() {
  return (
    <div className="space-y-2 p-4">
      {/* File tree nodes */}
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-2" style={{ paddingLeft: `${(i % 3) * 12}px` }}>
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 flex-1" />
        </div>
      ))}
    </div>
  );
}
