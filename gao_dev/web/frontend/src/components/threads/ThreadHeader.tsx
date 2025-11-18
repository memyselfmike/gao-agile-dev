/**
 * ThreadHeader - Thread panel header with close button
 *
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Shows parent message preview and close button
 */
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { ChatMessage } from '@/types';

interface ThreadHeaderProps {
  parentMessage: ChatMessage;
  onClose: () => void;
}

export function ThreadHeader({ parentMessage, onClose }: ThreadHeaderProps) {
  // Truncate parent message content for preview
  const truncateContent = (content: string, maxLength: number = 60) => {
    if (content.length <= maxLength) return content;
    return content.slice(0, maxLength) + '...';
  };

  return (
    <div className="flex items-center justify-between border-b bg-background px-4 py-3">
      <div className="flex-1 overflow-hidden">
        <h3 className="text-sm font-semibold">Thread</h3>
        <p className="truncate text-xs text-muted-foreground">
          {truncateContent(parentMessage.content)}
        </p>
      </div>

      <Button
        variant="ghost"
        size="icon"
        onClick={onClose}
        className="ml-2 h-8 w-8 shrink-0"
        data-testid="thread-close-button"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
