/**
 * Draggable Card - Wrapper for Epic/Story cards with drag-and-drop
 *
 * Story 39.17: Drag-and-Drop State Transitions
 */
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { cn } from '@/lib/utils';
import type { KanbanCard } from '@/stores/kanbanStore';
import { Loader2 } from 'lucide-react';

export interface DraggableCardProps {
  card: KanbanCard;
  isLoading?: boolean;
  children: React.ReactNode;
}

export function DraggableCard({ card, isLoading, children }: DraggableCardProps) {
  const { attributes, listeners, setNodeRef, isDragging, transform } = useDraggable({
    id: card.id,
    data: {
      type: card.type,
      status: card.status,
      card,
    },
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
    cursor: isDragging ? 'grabbing' : 'grab',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={cn(
        'relative transition-opacity',
        isDragging && 'z-50',
        isLoading && 'pointer-events-none'
      )}
      aria-label={`Draggable card: ${card.title}`}
      data-testid={`draggable-${card.id}`}
    >
      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-background/50 backdrop-blur-sm">
          <Loader2 className="h-6 w-6 animate-spin text-primary" aria-label="Moving card..." />
        </div>
      )}

      {children}
    </div>
  );
}
