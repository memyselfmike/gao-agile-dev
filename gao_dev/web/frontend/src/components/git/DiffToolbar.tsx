/**
 * DiffToolbar - Toolbar for diff view with navigation and toggle
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, SplitSquareHorizontal, ListTree } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DiffToolbarProps {
  viewMode: 'split' | 'unified';
  onToggleView: () => void;
  onNext: () => void;
  onPrevious: () => void;
  hasNext: boolean;
  hasPrevious: boolean;
}

export function DiffToolbar({
  viewMode,
  onToggleView,
  onNext,
  onPrevious,
  hasNext,
  hasPrevious,
}: DiffToolbarProps) {
  return (
    <div className="flex items-center justify-between gap-2 p-3 border-b bg-muted/30">
      {/* Navigation buttons */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={onPrevious}
          disabled={!hasPrevious}
          title="Previous file (P)"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onNext}
          disabled={!hasNext}
          title="Next file (N)"
        >
          Next
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {/* View mode toggle */}
      <div className="flex items-center gap-1">
        <Button
          variant={viewMode === 'split' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => viewMode !== 'split' && onToggleView()}
          title="Side-by-side view"
          className={cn(viewMode === 'split' && 'pointer-events-none')}
        >
          <SplitSquareHorizontal className="h-4 w-4 mr-1" />
          Split
        </Button>
        <Button
          variant={viewMode === 'unified' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => viewMode !== 'unified' && onToggleView()}
          title="Unified view (T to toggle)"
          className={cn(viewMode === 'unified' && 'pointer-events-none')}
        >
          <ListTree className="h-4 w-4 mr-1" />
          Unified
        </Button>
      </div>
    </div>
  );
}
