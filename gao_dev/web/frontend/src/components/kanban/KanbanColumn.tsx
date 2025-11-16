/**
 * Kanban Column - Single column with header and cards
 *
 * Story 39.15: Kanban Board Layout and State Columns
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import type { ColumnState, StoryCard, EpicCard } from '@/stores/kanbanStore';
import { COLUMN_LABELS, COLUMN_COLORS } from '@/stores/kanbanStore';
import { cn } from '@/lib/utils';

interface KanbanColumnProps {
  state: ColumnState;
  cards: (StoryCard | EpicCard)[];
}

export function KanbanColumn({ state, cards }: KanbanColumnProps) {
  const label = COLUMN_LABELS[state];
  const color = COLUMN_COLORS[state];
  const count = cards.length;

  // Color mapping for column headers
  const colorClasses: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100',
    blue: 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100',
    yellow: 'bg-yellow-100 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-100',
    purple: 'bg-purple-100 text-purple-900 dark:bg-purple-900 dark:text-purple-100',
    green: 'bg-green-100 text-green-900 dark:bg-green-900 dark:text-green-100',
  };

  return (
    <div
      className="flex h-full flex-col border-r border-border bg-card last:border-r-0"
      data-testid={`kanban-column-${state}`}
      role="region"
      aria-label={`${label} column with ${count} items`}
    >
      {/* Column Header */}
      <div className={cn('flex items-center justify-between p-4', colorClasses[color])}>
        <h3 className="text-sm font-semibold">{label}</h3>
        <span
          className="flex h-6 w-6 items-center justify-center rounded-full bg-white/20 text-xs font-medium"
          aria-label={`${count} cards in ${label}`}
        >
          {count}
        </span>
      </div>

      {/* Column Content */}
      <ScrollArea className="flex-1 p-2">
        {count === 0 ? (
          // Empty state placeholder
          <div className="flex h-32 items-center justify-center">
            <p className="text-sm text-muted-foreground">No items</p>
          </div>
        ) : (
          // Card list
          <div className="space-y-2" role="list">
            {cards.map((card) => (
              <Card
                key={card.id}
                className="cursor-pointer p-3 transition-shadow hover:shadow-md"
                role="listitem"
                tabIndex={0}
                aria-label={`${card.type} ${card.number}: ${card.title}`}
                onKeyDown={(e) => {
                  // Allow Enter/Space to trigger click
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.currentTarget.click();
                  }
                }}
              >
                {/* Card type indicator */}
                <div className="mb-1 flex items-center gap-2">
                  <span
                    className={cn(
                      'rounded px-1.5 py-0.5 text-xs font-medium',
                      card.type === 'epic'
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    )}
                  >
                    {card.type === 'epic' ? 'Epic' : 'Story'} {card.number}
                  </span>
                  {card.type === 'story' && (
                    <span className="text-xs text-muted-foreground">
                      {card.points} {card.points === 1 ? 'point' : 'points'}
                    </span>
                  )}
                </div>

                {/* Card title */}
                <h4 className="mb-2 text-sm font-medium leading-tight">{card.title}</h4>

                {/* Epic-specific metadata */}
                {card.type === 'epic' && (
                  <div className="space-y-1">
                    {/* Progress bar */}
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${card.progress}%` }}
                        role="progressbar"
                        aria-valuenow={card.progress}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label={`Epic progress: ${card.progress}%`}
                      />
                    </div>
                    {/* Story counts */}
                    <div className="flex gap-2 text-xs text-muted-foreground">
                      <span>{card.storyCounts.total} stories</span>
                      <span>·</span>
                      <span>{card.storyCounts.done} done</span>
                      <span>·</span>
                      <span>{card.completedPoints}/{card.totalPoints} points</span>
                    </div>
                  </div>
                )}

                {/* Story-specific metadata */}
                {card.type === 'story' && card.owner && (
                  <div className="mt-1 text-xs text-muted-foreground">
                    Owner: {card.owner}
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
