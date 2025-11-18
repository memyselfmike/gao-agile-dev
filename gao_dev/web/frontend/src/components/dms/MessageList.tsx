/**
 * MessageList - Virtualized message list for DM conversations
 *
 * Story 39.32: DM Conversation View and Message Sending
 *
 * Reuses ChatWindow virtual scrolling patterns
 */
import { useEffect, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { ChatMessage as ChatMessageType } from '../../types';
import { Message } from './Message';
import { Button } from '../ui/button';
import { ArrowDown, Loader2 } from 'lucide-react';

interface MessageListProps {
  messages: ChatMessageType[];
  agentName: string;
  showReasoning?: boolean;
  isTyping?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoadingMore?: boolean;
}

export function MessageList({
  messages,
  agentName,
  showReasoning = false,
  isTyping = false,
  onLoadMore,
  hasMore = false,
  isLoadingMore = false,
}: MessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  // Virtual scrolling for performance with 1,000+ messages
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 150, // Estimated height per message
    overscan: 5, // Render 5 extra items above/below viewport
  });

  const items = virtualizer.getVirtualItems();

  // Auto-scroll to bottom on new messages (if autoScroll enabled)
  useEffect(() => {
    if (autoScroll && messages.length > 0 && parentRef.current) {
      // Use virtualizer scrollToIndex for smooth scrolling
      virtualizer.scrollToIndex(messages.length - 1, {
        align: 'end',
        behavior: 'smooth',
      });
    }
  }, [messages.length, autoScroll, virtualizer]);

  // Detect user scroll and disable auto-scroll
  const handleScroll = () => {
    if (!parentRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = parentRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    const isNearTop = scrollTop < 50;

    setShowScrollButton(!isNearBottom);
    setAutoScroll(isNearBottom);

    // Trigger load more when near top
    if (isNearTop && hasMore && !isLoadingMore && onLoadMore) {
      onLoadMore();
    }
  };

  const scrollToBottom = () => {
    if (messages.length > 0) {
      virtualizer.scrollToIndex(messages.length - 1, {
        align: 'end',
        behavior: 'smooth',
      });
      setAutoScroll(true);
    }
  };

  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div>
          <p className="text-lg font-medium text-muted-foreground">No messages yet</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Start a conversation with {agentName} by typing a message below.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-full">
      {/* Load more button at top */}
      {hasMore && (
        <div className="sticky top-0 z-10 flex justify-center border-b bg-background/95 py-2 backdrop-blur">
          <Button
            variant="outline"
            size="sm"
            onClick={onLoadMore}
            disabled={isLoadingMore}
          >
            {isLoadingMore ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              'Load more'
            )}
          </Button>
        </div>
      )}

      {/* Virtualized message list */}
      <div
        ref={parentRef}
        onScroll={handleScroll}
        className="h-full overflow-auto"
        style={{ overflowAnchor: 'none' }}
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {items.map((virtualItem) => {
            const message = messages[virtualItem.index];
            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                <Message
                  message={message}
                  agentName={agentName}
                  showReasoning={showReasoning}
                />
              </div>
            );
          })}
        </div>

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex gap-3 px-4 py-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500 text-white">
              <span className="text-xs">...</span>
            </div>
            <div className="flex items-center text-sm text-muted-foreground">
              {agentName} is typing...
            </div>
          </div>
        )}
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <div className="absolute bottom-4 right-4">
          <Button
            size="icon"
            onClick={scrollToBottom}
            className="shadow-lg"
            aria-label="Scroll to bottom"
          >
            <ArrowDown className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
