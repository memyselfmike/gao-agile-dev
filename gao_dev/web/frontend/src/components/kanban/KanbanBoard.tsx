/**
 * Kanban Board - Grid layout with 5 state columns
 *
 * Story 39.15: Kanban Board Layout and State Columns
 */
import { useEffect } from 'react';
import { KanbanColumn } from './KanbanColumn';
import { useKanbanStore, COLUMN_STATES } from '@/stores/kanbanStore';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export function KanbanBoard() {
  const { columns, isLoading, error, fetchBoard } = useKanbanStore();

  // Fetch board data on mount
  useEffect(() => {
    fetchBoard();
  }, [fetchBoard]);

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

  return (
    <div
      className="grid h-full grid-cols-5 overflow-hidden"
      role="main"
      aria-label="Kanban board with 5 columns"
    >
      {COLUMN_STATES.map((state) => (
        <KanbanColumn
          key={state}
          state={state}
          cards={columns[state]}
        />
      ))}
    </div>
  );
}
