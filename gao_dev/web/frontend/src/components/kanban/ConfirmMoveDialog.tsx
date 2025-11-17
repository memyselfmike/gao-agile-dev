/**
 * Confirm Move Dialog - Modal for confirming card state transitions
 *
 * Story 39.17: Drag-and-Drop State Transitions
 */
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { COLUMN_LABELS, type PendingMove } from '@/stores/kanbanStore';
import { useEffect } from 'react';

export interface ConfirmMoveDialogProps {
  pendingMove: PendingMove | null;
  onConfirm: (move: PendingMove) => void;
  onCancel: () => void;
}

export function ConfirmMoveDialog({ pendingMove, onConfirm, onCancel }: ConfirmMoveDialogProps) {
  // Keyboard shortcuts: Enter confirms, Escape cancels
  useEffect(() => {
    if (!pendingMove) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        onConfirm(pendingMove);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        onCancel();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [pendingMove, onConfirm, onCancel]);

  if (!pendingMove) return null;

  const fromLabel = COLUMN_LABELS[pendingMove.fromStatus];
  const toLabel = COLUMN_LABELS[pendingMove.toStatus];

  return (
    <Dialog open={!!pendingMove} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Confirm State Transition</DialogTitle>
          <DialogDescription>
            Move <strong>{pendingMove.card.title}</strong> from{' '}
            <span className="font-medium text-foreground">{fromLabel}</span> to{' '}
            <span className="font-medium text-foreground">{toLabel}</span>?
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-center space-x-4 py-4">
          {/* Visual state transition indicator */}
          <div className="flex items-center space-x-2">
            <div className="rounded bg-muted px-3 py-1 text-sm font-medium">{fromLabel}</div>
            <span className="text-muted-foreground">→</span>
            <div className="rounded bg-primary px-3 py-1 text-sm font-medium text-primary-foreground">
              {toLabel}
            </div>
          </div>
        </div>

        <DialogFooter className="sm:justify-between">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={() => onConfirm(pendingMove)} autoFocus>
            Move Card
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
