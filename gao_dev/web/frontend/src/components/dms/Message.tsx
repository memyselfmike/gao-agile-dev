/**
 * Message - Individual DM message with markdown rendering
 *
 * Story 39.32: DM Conversation View and Message Sending
 *
 * Reuses ChatMessage patterns with DM-specific styling
 */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDistanceToNow } from 'date-fns';
import { User, Bot } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types';
import { cn } from '../../lib/utils';

interface MessageProps {
  message: ChatMessageType;
  agentName: string;
  showReasoning?: boolean;
}

export function Message({ message, agentName, showReasoning = false }: MessageProps) {
  const isUser = message.role === 'user';
  const isAgent = message.role === 'agent';
  const isSystem = message.role === 'system';

  // Format timestamp as relative time
  const timeAgo = formatDistanceToNow(message.timestamp, { addSuffix: true });

  // Extract thinking tags if present
  const thinkingRegex = /<thinking>([\s\S]*?)<\/thinking>/g;
  const thinkingMatches = [...message.content.matchAll(thinkingRegex)];
  const hasThinking = thinkingMatches.length > 0;

  // Remove thinking tags from content if not showing reasoning
  const displayContent = showReasoning
    ? message.content
    : message.content.replace(thinkingRegex, '').trim();

  return (
    <div
      className={cn(
        'flex gap-3 px-4 py-3 hover:bg-muted/30 transition-colors',
        isUser && 'bg-muted/50',
        isSystem && 'bg-yellow-50 dark:bg-yellow-950/20'
      )}
      data-testid={`chat-message-${isAgent ? agentName.toLowerCase() : 'user'}`}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser && 'bg-primary text-primary-foreground',
          isAgent && 'bg-blue-500 text-white',
          isSystem && 'bg-yellow-500 text-white'
        )}
      >
        {isUser && <User className="h-4 w-4" />}
        {isAgent && <Bot className="h-4 w-4" />}
        {isSystem && <span className="text-xs font-bold">!</span>}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {/* Header */}
        <div className="mb-1 flex items-baseline gap-2">
          <span className="text-sm font-semibold">
            {isUser ? 'You' : isAgent ? agentName : 'System'}
          </span>
          <span className="text-xs text-muted-foreground">{timeAgo}</span>
        </div>

        {/* Message content with markdown */}
        <div className="prose prose-sm dark:prose-invert max-w-none break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Custom link renderer (open in new tab)
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer" />
              ),
              // Custom code block renderer
              code: ({ node, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';

                // Check if inline by looking at the element type
                const isInline = !className || !className.includes('language-');

                if (isInline) {
                  return (
                    <code
                      className="rounded bg-muted px-1 py-0.5 font-mono text-sm"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                }

                return (
                  <div className="relative">
                    {language && (
                      <div className="absolute right-2 top-2 rounded bg-muted px-2 py-1 text-xs text-muted-foreground">
                        {language}
                      </div>
                    )}
                    <pre className="overflow-x-auto rounded-lg bg-muted p-4">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                );
              },
            }}
          >
            {displayContent}
          </ReactMarkdown>
        </div>

        {/* Thinking section (if reasoning shown) */}
        {showReasoning && hasThinking && (
          <div className="mt-2 border-l-2 border-yellow-500 bg-yellow-50 p-3 dark:bg-yellow-950/20">
            <div className="mb-1 text-xs font-semibold text-yellow-700 dark:text-yellow-400">
              {agentName}'s Reasoning
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none text-sm">
              {thinkingMatches.map((match, i) => (
                <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
                  {match[1].trim()}
                </ReactMarkdown>
              ))}
            </div>
          </div>
        )}

        {/* Thread count placeholder for Story 39.35 */}
        {/* TODO: Add thread count indicator when threaded replies are implemented */}
      </div>
    </div>
  );
}
