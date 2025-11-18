/**
 * EmptyActivity - Empty state for activity feed when no events exist
 *
 * Story 39.40: Empty States
 */
import { Activity } from 'lucide-react';

interface EmptyActivityProps {
  hasFilters?: boolean;
  onClearFilters?: () => void;
}

export function EmptyActivity({ hasFilters = false, onClearFilters }: EmptyActivityProps) {
  if (hasFilters) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center">
        <div className="mb-4 rounded-full bg-muted p-6">
          <Activity className="h-12 w-12 text-muted-foreground" />
        </div>
        <h3 className="mb-2 text-lg font-semibold">No matching events</h3>
        <p className="mb-6 max-w-sm text-sm text-muted-foreground">
          No events match your current filters. Try adjusting your filters or clearing them to see
          all activity.
        </p>
        {onClearFilters && (
          <button
            onClick={onClearFilters}
            className="text-sm text-primary hover:underline"
          >
            Clear all filters
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="mb-4 rounded-full bg-primary/10 p-6">
        <Activity className="h-12 w-12 text-primary" />
      </div>
      <h3 className="mb-2 text-lg font-semibold">No activity yet</h3>
      <p className="max-w-sm text-sm text-muted-foreground">
        Events will appear here as agents work on your project. Chat with Brian to get started!
      </p>
    </div>
  );
}
