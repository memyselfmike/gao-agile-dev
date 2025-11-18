/**
 * ReplyButton - "Reply in thread" button on hover
 *
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Shows on message hover, opens thread panel when clicked
 */
import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ReplyButtonProps {
  onClick: () => void;
  className?: string;
}

export function ReplyButton({ onClick, className }: ReplyButtonProps) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className={cn(
        'h-7 gap-1.5 px-2 text-xs opacity-0 transition-opacity group-hover:opacity-100',
        className
      )}
      data-testid="thread-reply-button"
    >
      <MessageSquare className="h-3.5 w-3.5" />
      <span>Reply in thread</span>
    </Button>
  );
}
