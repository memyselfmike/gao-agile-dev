/**
 * Kanban Column - Single column with header and cards
 *
 * Story 39.15: Kanban Board Layout and State Columns
 * Story 39.16: Epic and Story Card Components
 * Story 39.17: Drag-and-Drop State Transitions
 * Story 39.19: Virtual Scrolling for Large Boards
 */
import type { ColumnState, StoryCard as StoryCardType, EpicCard as EpicCardType } from '@/stores/kanbanStore';
import { COLUMN_LABELS, COLUMN_COLORS } from '@/stores/kanbanStore';
import { cn } from '@/lib/utils';
import { DroppableColumn } from './DroppableColumn';
import { VirtualizedColumn } from './VirtualizedColumn';

interface KanbanColumnProps {
  state: ColumnState;
  cards: (StoryCardType | EpicCardType)[];
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
    <DroppableColumn status={state} className="flex h-full flex-col border-r border-border bg-card last:border-r-0">
      <div
        data-testid={`kanban-column-${state}`}
        role="region"
        aria-label={`${label} column with ${count} items`}
        className="flex h-full flex-col"
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

        {/* Column Content - Story 39.19: Virtual Scrolling */}
        <div className="flex-1">
          <VirtualizedColumn status={state} cards={cards} />
        </div>
      </div>
    </DroppableColumn>
  );
}
