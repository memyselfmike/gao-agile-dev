/**
 * ChatWindow - Message list with virtual scrolling
 *
 * Story 39.7: Virtual scrolling for 1,000+ messages
 */
import { useEffect, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { ChatMessage as ChatMessageType } from '../../types';
import { ChatMessage } from './ChatMessage';
import { Button } from '../ui/button';
import { ArrowDown } from 'lucide-react';

interface ChatWindowProps {
  messages: ChatMessageType[];
  showReasoning: boolean;
  isTyping?: boolean;
}

export function ChatWindow({ messages, showReasoning, isTyping = false }: ChatWindowProps) {
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

    setShowScrollButton(!isNearBottom);
    setAutoScroll(isNearBottom);
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

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div>
          <p className="text-lg font-medium text-muted-foreground">No messages yet</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Start a conversation with Brian by typing a message below.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-full">
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
                <ChatMessage message={message} showReasoning={showReasoning} />
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
              Brian is typing...
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
