/**
 * Droppable Column - Wrapper for Kanban columns with drop zone
 *
 * Story 39.17: Drag-and-Drop State Transitions
 */
import { useDroppable } from '@dnd-kit/core';
import { cn } from '@/lib/utils';
import type { ColumnState } from '@/stores/kanbanStore';

export interface DroppableColumnProps {
  status: ColumnState;
  children: React.ReactNode;
  className?: string;
}

export function DroppableColumn({ status, children, className }: DroppableColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: { status },
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'transition-colors',
        isOver && 'bg-accent/30 ring-2 ring-accent ring-offset-2',
        className
      )}
      data-testid={`droppable-column-${status}`}
      aria-label={`Drop zone for ${status} column`}
    >
      {children}
    </div>
  );
}
