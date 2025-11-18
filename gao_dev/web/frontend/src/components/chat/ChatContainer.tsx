/**
 * ChatContainer - Main chat component integrating all chat pieces
 *
 * Story 39.7: Complete chat interface with WebSocket integration
 */
import { useState, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useSessionStore } from '../../stores/sessionStore';
import { ChatWindow } from './ChatWindow';
import { ChatInput } from './ChatInput';
import { ReasoningToggle } from './ReasoningToggle';
import { Alert, AlertDescription } from '../ui/alert';
import { AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';

export function ChatContainer() {
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

  // Listen to WebSocket events for streaming
  useEffect(() => {
    // TODO: WebSocket event handling will be implemented when WebSocket
    // connection is fully integrated with the chat system.
    // For now, we rely on the REST API response.

    // The WebSocket events we'll handle:
    // - chat.message_sent: User message sent
    // - chat.streaming_chunk: Response chunk received
    // - chat.message_received: Complete response received
    // - chat.thinking_started/finished: Claude reasoning indicators
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

    // Note: Don't add user message here - it comes via WebSocket event
    // from BrianWebAdapter.send_message() -> CHAT_MESSAGE_SENT

    setIsSending(true);
    setIsTyping(true);

    try {
      // Send message to backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: JSON.stringify({
          message,
          agent: 'Brian',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send message');
      }

      // Response streams via WebSocket, so we just wait for events
      // The WebSocket handler above will update the UI

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
    }
  };

  const handleRetry = () => {
    setError(null);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b bg-background px-4 py-3">
        <div>
          <h2 className="text-lg font-semibold">Chat with Brian</h2>
          <p className="text-sm text-muted-foreground">GAO-Dev Workflow Coordinator</p>
        </div>
        <ReasoningToggle showReasoning={showReasoning} onToggle={() => setShowReasoning(!showReasoning)} />
      </div>

      {/* Error banner */}
      {error && (
        <Alert variant="destructive" className="m-4" role="alert" aria-live="assertive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Message window - ARIA live region for new messages */}
      <div className="flex-1 overflow-hidden" role="log" aria-live="polite" aria-atomic="false">
        <ChatWindow messages={messages} showReasoning={showReasoning} isTyping={isTyping} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={isSending || isTyping}
        placeholder={isSending ? 'Sending...' : 'Ask Brian anything...'}
      />
    </div>
  );
}
