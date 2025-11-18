/**
 * DMConversationView - Main DM conversation container
 *
 * Story 39.32: DM Conversation View and Message Sending
 *
 * Orchestrates MessageList, MessageInput, and WebSocket streaming
 */
import { useState, useEffect, useCallback } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useSessionStore } from '../../stores/sessionStore';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ReasoningToggle } from '../chat/ReasoningToggle';
import type { Agent } from '../../types';
import { cn } from '../../lib/utils';

interface DMConversationViewProps {
  agent: Agent;
}

export function DMConversationView({ agent }: DMConversationViewProps) {
  const {
    messages,
    isTyping,
    addMessage,
    setIsTyping,
    addStreamingChunk,
    finishStreamingMessage,
  } = useChatStore();

  const { sessionToken } = useSessionStore();
  const [showReasoning, setShowReasoning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  // Pagination state
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [offset, setOffset] = useState(0);

  // Load initial messages
  useEffect(() => {
    async function loadMessages() {
      try {
        const response = await fetch(
          `/api/dms/${agent.id}/messages?offset=0&limit=50`
        );

        if (!response.ok) {
          throw new Error('Failed to load messages');
        }

        const data = await response.json();
        // Messages are already in the store from agent switch
        // Just update pagination state
        setHasMore(data.hasMore);
        setOffset(data.messages.length);
      } catch (err) {
        console.error('Failed to load messages:', err);
      }
    }

    // Only load if agent has changed
    loadMessages();
  }, [agent.id]);

  // Load more messages (pagination)
  const handleLoadMore = useCallback(async () => {
    if (isLoadingMore || !hasMore) return;

    setIsLoadingMore(true);
    try {
      const response = await fetch(
        `/api/dms/${agent.id}/messages?offset=${offset}&limit=50`
      );

      if (!response.ok) {
        throw new Error('Failed to load more messages');
      }

      const data = await response.json();

      // Prepend older messages to the list
      // Note: This would need store support for prepending messages
      // For now, we just update pagination state
      setOffset(offset + data.messages.length);
      setHasMore(data.hasMore);
    } catch (err) {
      console.error('Failed to load more messages:', err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [agent.id, offset, hasMore, isLoadingMore]);

  // Listen to WebSocket events for streaming
  useEffect(() => {
    // TODO: WebSocket event handling will be enhanced when
    // multi-agent support is fully integrated.
    // For now, we rely on the existing chat store WebSocket handling.

    // The WebSocket events we handle:
    // - chat.message_sent: User message sent
    // - chat.streaming_chunk: Response chunk received
    // - chat.message_received: Complete response received
    // - system.error: Error handling

    return () => {
      // Cleanup
    };
  }, [addStreamingChunk, finishStreamingMessage, setIsTyping]);

  const handleSendMessage = async (message: string) => {
    if (!sessionToken) {
      setError('No session token. Please refresh the page.');
      return;
    }

    // Clear previous errors
    setError(null);

    // Add user message immediately
    addMessage({
      role: 'user',
      content: message,
    });

    setIsSending(true);
    setIsTyping(true);

    try {
      // Send message to backend
      const response = await fetch(`/api/dms/${agent.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: JSON.stringify({
          content: message,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send message');
      }

      // Response streams via WebSocket, so we just wait for events
      // The WebSocket handler in chatStore will update the UI

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setIsTyping(false);
      setIsSending(false);

      // Add error message to chat
      addMessage({
        role: 'system',
        content: `Error: ${errorMessage}`,
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleRetry = () => {
    setError(null);
  };

  // Get agent status indicator color
  const getStatusColor = () => {
    switch (agent.status) {
      case 'active':
        return 'bg-green-500';
      case 'busy':
        return 'bg-yellow-500';
      case 'idle':
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b bg-background px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Agent avatar with status */}
          <div className="relative">
            <div
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-full text-white',
                // Agent-specific colors (matching DMItem)
                agent.id === 'brian' && 'bg-blue-500',
                agent.id === 'mary' && 'bg-purple-500',
                agent.id === 'john' && 'bg-green-500',
                agent.id === 'winston' && 'bg-orange-500',
                agent.id === 'sally' && 'bg-pink-500',
                agent.id === 'bob' && 'bg-teal-500',
                agent.id === 'amelia' && 'bg-indigo-500',
                agent.id === 'murat' && 'bg-red-500'
              )}
            >
              <span className="text-sm font-semibold">{agent.name[0]}</span>
            </div>
            {/* Status indicator */}
            {agent.status && (
              <div
                className={cn(
                  'absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background',
                  getStatusColor()
                )}
              />
            )}
          </div>

          {/* Agent info */}
          <div>
            <h2 className="text-lg font-semibold">{agent.name}</h2>
            <p className="text-sm text-muted-foreground">{agent.role}</p>
          </div>
        </div>

        {/* Reasoning toggle */}
        <ReasoningToggle
          showReasoning={showReasoning}
          onToggle={() => setShowReasoning(!showReasoning)}
        />
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-hidden">
        <MessageList
          messages={messages}
          agentName={agent.name}
          showReasoning={showReasoning}
          isTyping={isTyping}
          onLoadMore={handleLoadMore}
          hasMore={hasMore}
          isLoadingMore={isLoadingMore}
        />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSendMessage}
        disabled={isSending || isTyping}
        placeholder={`Message ${agent.name}...`}
        agentName={agent.name}
        error={error}
        onRetry={handleRetry}
      />
    </div>
  );
}
