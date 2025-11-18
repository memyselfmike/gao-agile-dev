/**
 * ThreadCount - Thread reply count indicator
 *
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Shows number of replies, clickable to open thread panel
 */
import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ThreadCountProps {
  count: number;
  onClick: () => void;
  className?: string;
}

export function ThreadCount({ count, onClick, className }: ThreadCountProps) {
  if (count === 0) return null;

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className={cn(
        'h-7 gap-1.5 px-2 text-xs text-blue-600 hover:bg-blue-50 hover:text-blue-700 dark:text-blue-400 dark:hover:bg-blue-950',
        className
      )}
      data-testid="thread-count"
    >
      <MessageSquare className="h-3.5 w-3.5" />
      <span className="font-medium">
        {count} {count === 1 ? 'reply' : 'replies'}
      </span>
    </Button>
  );
}
