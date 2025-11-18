/**
 * ChatSkeleton - Loading skeleton for chat messages
 *
 * Story 39.40: Loading States - Skeleton loaders
 */
import { Skeleton } from '@/components/ui/skeleton';

export function ChatSkeleton() {
  return (
    <div className="space-y-4 p-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className={`flex gap-3 ${i % 2 === 0 ? '' : 'flex-row-reverse'}`}>
          {/* Avatar */}
          <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
          {/* Message */}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-20 w-full rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  );
}
