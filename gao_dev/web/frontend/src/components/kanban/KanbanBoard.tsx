/**
 * Kanban Board - Grid layout with 5 state columns
 *
 * Story 39.15: Kanban Board Layout and State Columns
 * Story 39.17: Drag-and-Drop State Transitions
 */
import { useEffect, useState } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  KeyboardSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { KanbanColumn } from './KanbanColumn';
import {
  useKanbanStore,
  COLUMN_STATES,
  type ColumnState,
  type PendingMove,
  type StoryCard,
  type EpicCard,
} from '@/stores/kanbanStore';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ConfirmMoveDialog } from './ConfirmMoveDialog';
import { EpicCard as EpicCardComponent } from './EpicCard';
import { StoryCard as StoryCardComponent } from './StoryCard';
import { FilterBar } from './FilterBar';
import { toast } from 'sonner';

export function KanbanBoard() {
  const {
    columns,
    isLoading,
    error,
    fetchBoard,
    moveCardOptimistic,
    rollbackMove,
    setCardLoading,
    moveCardServer,
    getFilteredCards,
    getTotalCardCount,
    getFilteredCardCount,
  } = useKanbanStore();

  // Drag-and-drop state
  const [activeCard, setActiveCard] = useState<(StoryCard | EpicCard) | null>(null);
  const [pendingMove, setPendingMove] = useState<PendingMove | null>(null);

  // Configure sensors for drag-and-drop
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement required to start drag
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 500, // 500ms long press to start drag on touch devices
        tolerance: 5,
      },
    }),
    useSensor(KeyboardSensor)
  );

  // Fetch board data on mount
  useEffect(() => {
    fetchBoard();
  }, [fetchBoard]);

  // Drag-and-drop handlers
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    setActiveCard(active.data.current?.card || null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCard(null);

    // No drop target
    if (!over) return;

    const cardId = active.id as string;
    const fromStatus = active.data.current?.status as ColumnState;
    const toStatus = over.id as ColumnState;

    // Same column - no state change
    if (fromStatus === toStatus) return;

    // Prepare pending move for confirmation
    const card = active.data.current?.card as (StoryCard | EpicCard);
    setPendingMove({
      cardId,
      fromStatus,
      toStatus,
      card,
    });
  };

  // Handle confirmed move
  const handleConfirmMove = async (move: PendingMove) => {
    // Close dialog
    setPendingMove(null);

    // Optimistic UI update
    moveCardOptimistic(move.cardId, move.fromStatus, move.toStatus);
    setCardLoading(move.cardId, true);

    try {
      // Server update
      await moveCardServer(move.cardId, move.fromStatus, move.toStatus);

      // Success toast
      toast.success('Card moved successfully', {
        description: `Moved to ${move.toStatus}`,
      });
    } catch (error) {
      // Rollback optimistic update
      rollbackMove(move.cardId, move.fromStatus, move.toStatus);

      // Error toast with retry option
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to move card', {
        description: errorMessage,
        action: {
          label: 'Retry',
          onClick: () => handleConfirmMove(move),
        },
      });
    } finally {
      setCardLoading(move.cardId, false);
    }
  };

  // Handle canceled move
  const handleCancelMove = () => {
    setPendingMove(null);
  };

  // Keyboard navigation for Shift+Arrow keys to move cards
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Handle Shift+Arrow keys for card movement
      if (event.shiftKey && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
        const activeElement = document.activeElement as HTMLElement;

        // Only handle if focused on a card
        if (!activeElement?.hasAttribute('data-testid')) return;

        const testId = activeElement.getAttribute('data-testid');
        if (!testId?.startsWith('draggable-')) return;

        event.preventDefault();

        // Extract card ID from data-testid
        const cardId = testId.replace('draggable-', '');

        // Find current column
        let currentColumnIndex = -1;
        let card: (StoryCard | EpicCard) | null = null;

        for (let i = 0; i < COLUMN_STATES.length; i++) {
          const state = COLUMN_STATES[i];
          const foundCard = columns[state].find((c: StoryCard | EpicCard) => c.id === cardId);
          if (foundCard) {
            currentColumnIndex = i;
            card = foundCard as (StoryCard | EpicCard);
            break;
          }
        }

        if (currentColumnIndex === -1 || !card) return;

        // Calculate target column
        let targetColumnIndex = currentColumnIndex;
        if (event.key === 'ArrowLeft' && currentColumnIndex > 0) {
          targetColumnIndex = currentColumnIndex - 1;
        } else if (event.key === 'ArrowRight' && currentColumnIndex < COLUMN_STATES.length - 1) {
          targetColumnIndex = currentColumnIndex + 1;
        }

        // No change
        if (targetColumnIndex === currentColumnIndex) return;

        // Show confirmation dialog
        setPendingMove({
          cardId,
          fromStatus: COLUMN_STATES[currentColumnIndex],
          toStatus: COLUMN_STATES[targetColumnIndex],
          card,
        });

        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [columns]);

  // Keyboard navigation (Arrow keys within column, Tab between columns)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const activeElement = document.activeElement as HTMLElement;

      // Only handle if we're focused on a card
      if (!activeElement || !activeElement.hasAttribute('role') || activeElement.getAttribute('role') !== 'listitem') {
        return;
      }

      // Arrow Up/Down: Navigate within column
      if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        event.preventDefault();
        const cards = Array.from(activeElement.parentElement?.querySelectorAll('[role="listitem"]') || []);
        const currentIndex = cards.indexOf(activeElement);

        if (event.key === 'ArrowUp' && currentIndex > 0) {
          (cards[currentIndex - 1] as HTMLElement).focus();
        } else if (event.key === 'ArrowDown' && currentIndex < cards.length - 1) {
          (cards[currentIndex + 1] as HTMLElement).focus();
        }
      }

      // Arrow Left/Right: Navigate between columns
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        const columns = Array.from(document.querySelectorAll('[data-testid^="kanban-column-"]'));
        const currentColumn = activeElement.closest('[data-testid^="kanban-column-"]');
        const currentColumnIndex = columns.indexOf(currentColumn as Element);

        let targetColumnIndex = currentColumnIndex;
        if (event.key === 'ArrowLeft' && currentColumnIndex > 0) {
          targetColumnIndex = currentColumnIndex - 1;
        } else if (event.key === 'ArrowRight' && currentColumnIndex < columns.length - 1) {
          targetColumnIndex = currentColumnIndex + 1;
        }

        // Focus first card in target column
        const targetColumn = columns[targetColumnIndex];
        const firstCard = targetColumn?.querySelector('[role="listitem"]') as HTMLElement;
        if (firstCard) {
          firstCard.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" message="Loading Kanban board..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Check if there are filtered results
  const totalCards = getTotalCardCount();
  const filteredCards = getFilteredCardCount();
  const hasResults = filteredCards > 0;

  return (
    <div className="flex h-full flex-col">
      {/* Filter Bar */}
      <FilterBar />

      {/* Empty state for no filter results */}
      {!hasResults && totalCards > 0 && (
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-medium text-muted-foreground mb-2">
              No cards match your filters
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              Try adjusting your search or filter criteria
            </p>
            <p className="text-xs text-muted-foreground">
              Showing {filteredCards} of {totalCards} cards
            </p>
          </div>
        </div>
      )}

      {/* Kanban Board */}
      {hasResults && (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div
            className="grid h-full grid-cols-5 overflow-hidden"
            role="main"
            aria-label="Kanban board with 5 columns"
          >
            {COLUMN_STATES.map((state) => (
              <KanbanColumn key={state} state={state} cards={getFilteredCards(state)} />
            ))}
          </div>

          {/* Drag overlay - ghost image during drag */}
          <DragOverlay>
            {activeCard ? (
              <div className="opacity-75 rotate-3 scale-105">
                {activeCard.type === 'epic' ? (
                  <EpicCardComponent epic={activeCard as EpicCard} />
                ) : (
                  <StoryCardComponent story={activeCard as StoryCard} />
                )}
              </div>
            ) : null}
          </DragOverlay>

          {/* Confirmation dialog */}
          <ConfirmMoveDialog
            pendingMove={pendingMove}
            onConfirm={handleConfirmMove}
            onCancel={handleCancelMove}
          />
        </DndContext>
      )}
    </div>
  );
}
