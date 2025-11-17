/**
 * Epic Card - Epic summary card for Kanban board
 *
 * Story 39.16: Epic and Story Card Components
 */
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useKanbanStore } from '@/stores/kanbanStore';
import { HighlightedText } from './HighlightedText';

export interface EpicCardProps {
  epic: {
    id: string;
    number: string;
    title: string;
    progress: number;
    totalPoints: number;
    completedPoints: number;
    storyCounts: {
      total: number;
      done: number;
      in_progress: number;
      backlog: number;
    };
  };
  onClick?: () => void;
}

export function EpicCard({ epic, onClick }: EpicCardProps) {
  const { filters } = useKanbanStore();

  // Determine progress bar color based on completion percentage
  const getProgressColor = (progress: number): string => {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const progressColor = getProgressColor(epic.progress);

  return (
    <Card
      className="cursor-pointer border-2 border-purple-200 transition-all hover:shadow-lg hover:border-purple-400 dark:border-purple-800 dark:hover:border-purple-600"
      onClick={onClick}
      role="listitem"
      tabIndex={0}
      aria-label={`Epic ${epic.number}: ${epic.title}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      <CardContent className="p-4 space-y-3">
        {/* Epic header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <Badge
              variant="secondary"
              className="mb-2 bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300"
            >
              Epic {epic.number}
            </Badge>
            <h4 className="text-sm font-semibold leading-tight line-clamp-2">
              <HighlightedText text={epic.title} search={filters.search} />
            </h4>
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span className="font-medium">{Math.round(epic.progress)}%</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={cn('h-full transition-all duration-300', progressColor)}
              style={{ width: `${epic.progress}%` }}
              role="progressbar"
              aria-valuenow={epic.progress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Epic progress: ${Math.round(epic.progress)}%`}
            />
          </div>
        </div>

        {/* Story counts badge */}
        <div className="flex items-center gap-2 text-xs">
          <Badge variant="outline" className="text-xs">
            {epic.storyCounts.done} of {epic.storyCounts.total} stories done
          </Badge>
        </div>

        {/* Points summary */}
        <div className="flex items-center justify-between text-xs text-muted-foreground border-t pt-2">
          <span>Story Points</span>
          <span className="font-medium">
            {epic.completedPoints} / {epic.totalPoints}
          </span>
        </div>

        {/* Story breakdown */}
        <div className="flex gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="h-2 w-2 rounded-full bg-gray-400" />
            <span>{epic.storyCounts.backlog} backlog</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-2 w-2 rounded-full bg-yellow-400" />
            <span>{epic.storyCounts.in_progress} in progress</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
