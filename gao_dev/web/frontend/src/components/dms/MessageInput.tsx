/**
 * MessageInput - DM message input with send button
 *
 * Story 39.32: DM Conversation View and Message Sending
 *
 * Reuses ChatInput patterns with DM-specific features
 */
import { useState, useRef, type KeyboardEvent } from 'react';
import { Send, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';

interface MessageInputProps {
  onSend: (message: string) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  agentName: string;
  error?: string | null;
  onRetry?: () => void;
}

export function MessageInput({
  onSend,
  disabled = false,
  placeholder = 'Type a message...',
  agentName,
  error,
  onRetry,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = async () => {
    const trimmed = message.trim();
    if (!trimmed || disabled || isSending) return;

    setIsSending(true);
    try {
      await onSend(trimmed);
      setMessage('');

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (err) {
      // Error handled by parent
      console.error('Failed to send message:', err);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };

  return (
    <div className="border-t bg-background">
      {/* Error banner */}
      {error && (
        <Alert variant="destructive" className="m-4 mb-0">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            {onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry}>
                Retry
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Input area */}
      <div className="p-4">
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={
              isSending
                ? `Sending to ${agentName}...`
                : placeholder || `Message ${agentName}...`
            }
            disabled={disabled || isSending}
            rows={1}
            data-testid="chat-input"
            className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ maxHeight: '200px' }}
          />
          <Button
            onClick={handleSend}
            disabled={disabled || isSending || !message.trim()}
            size="icon"
            data-testid="chat-send-button"
          >
            <Send className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}
