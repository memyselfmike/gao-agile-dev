/**
 * ThreadPanel - Main thread panel with slide-in animation
 *
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Slide-in panel from right (40% width, min 400px)
 * Shows parent message, thread replies, and message input
 * Supports virtual scrolling for >100 replies
 */
import { useEffect, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Loader2 } from 'lucide-react';
import { useThreadStore } from '@/stores';
import { ThreadHeader } from './ThreadHeader';
import { Message } from '../dms/Message';
import { MessageInput } from '../dms/MessageInput';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface ThreadPanelProps {
  agentName: string;
  showReasoning?: boolean;
}

export function ThreadPanel({ agentName, showReasoning = false }: ThreadPanelProps) {
  const {
    activeThread,
    isLoading,
    isSendingReply,
    error,
    closeThread,
    addThreadReply,
  } = useThreadStore();

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Virtual scrolling for thread replies (>100 replies)
  const rowVirtualizer = useVirtualizer({
    count: activeThread?.replies.length || 0,
    getScrollElement: () => scrollContainerRef.current,
    estimateSize: () => 100, // Estimated row height
    overscan: 5,
  });

  // Scroll to bottom when thread opens or new reply added
  useEffect(() => {
    if (activeThread && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [activeThread?.replies.length]);

  // Handle Escape key to close thread panel
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && activeThread) {
        closeThread();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [activeThread, closeThread]);

  // Don't render if no active thread
  if (!activeThread) return null;

  const handleSendReply = async (content: string) => {
    await addThreadReply(content);
  };

  const useVirtualScrolling = (activeThread?.replies.length || 0) > 100;

  return (
    <>
      {/* Backdrop (click to close) */}
      <div
        className="fixed inset-0 z-40 bg-black/10 backdrop-blur-[2px]"
        onClick={closeThread}
        data-testid="thread-panel-backdrop"
      />

      {/* Thread Panel */}
      <div
        className={cn(
          'fixed right-0 top-0 z-50 flex h-full flex-col border-l bg-background shadow-2xl',
          'transition-transform duration-200 ease-out',
          'w-[40%] min-w-[400px]',
          activeThread && 'animate-in slide-in-from-right'
        )}
        data-testid="thread-panel"
      >
        {/* Header */}
        <ThreadHeader parentMessage={activeThread.parentMessage} onClose={closeThread} />

        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-1 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex flex-1 items-center justify-center p-4">
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
              <p className="font-semibold">Failed to load thread</p>
              <p className="mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Content */}
        {!isLoading && !error && (
          <>
            {/* Scrollable content */}
            <div
              ref={scrollContainerRef}
              className="flex-1 overflow-y-auto"
              style={{ contain: 'strict' }}
            >
              {/* Parent message */}
              <div className="border-b bg-muted/30">
                <Message
                  message={activeThread.parentMessage}
                  agentName={agentName}
                  showReasoning={showReasoning}
                />
              </div>

              <Separator className="my-2" />

              {/* Thread replies */}
              {useVirtualScrolling ? (
                // Virtual scrolling for large threads
                <div
                  style={{
                    height: `${rowVirtualizer.getTotalSize()}px`,
                    width: '100%',
                    position: 'relative',
                  }}
                >
                  {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                    const reply = activeThread.replies[virtualRow.index];
                    return (
                      <div
                        key={virtualRow.key}
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          transform: `translateY(${virtualRow.start}px)`,
                        }}
                      >
                        <Message
                          message={reply}
                          agentName={agentName}
                          showReasoning={showReasoning}
                        />
                      </div>
                    );
                  })}
                </div>
              ) : (
                // Regular rendering for small threads
                <div>
                  {activeThread.replies.length === 0 ? (
                    <div className="flex flex-col items-center justify-center p-8 text-center">
                      <p className="text-sm text-muted-foreground">
                        No replies yet. Start the conversation!
                      </p>
                    </div>
                  ) : (
                    activeThread.replies.map((reply) => (
                      <Message
                        key={reply.id}
                        message={reply}
                        agentName={agentName}
                        showReasoning={showReasoning}
                      />
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Message input */}
            <MessageInput
              onSend={handleSendReply}
              disabled={isSendingReply}
              placeholder="Reply in thread..."
              agentName={agentName}
              error={null}
              onRetry={() => {}}
            />
          </>
        )}
      </div>
    </>
  );
}
