/**
 * ChannelMessage - Individual message in channel view
 *
 * Story 39.33: Channels Section - Ceremony Channels UI
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Shows multi-agent participants with avatars and names
 * Includes thread reply button and thread count
 */
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';
import { Bot, User as UserIcon } from 'lucide-react';
import type { ChannelMessage as IChannelMessage } from '@/types';
import { ReplyButton } from '../threads/ReplyButton';
import { ThreadCount } from '../threads/ThreadCount';
import { useThreadStore } from '@/stores';

interface ChannelMessageProps {
  message: IChannelMessage;
  channelId: string;
}

// Agent color mapping (consistent with DMItem)
const AGENT_COLORS: Record<string, string> = {
  brian: 'bg-blue-500',
  mary: 'bg-purple-500',
  john: 'bg-green-500',
  winston: 'bg-orange-500',
  sally: 'bg-pink-500',
  bob: 'bg-teal-500',
  amelia: 'bg-indigo-500',
  murat: 'bg-red-500',
};

// Format timestamp
function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function ChannelMessage({ message, channelId }: ChannelMessageProps) {
  const isUser = message.role === 'user';
  const isAgent = message.role === 'agent';
  const isSystem = message.role === 'system';

  const { threadCounts, openThread } = useThreadStore();

  // Get agent color
  const agentColor = message.agentId
    ? AGENT_COLORS[message.agentId] || 'bg-gray-500'
    : 'bg-gray-500';

  // Get thread count for this message
  const threadCount = threadCounts[message.id] || 0;

  // Handle reply in thread click
  const handleReplyInThread = () => {
    openThread(message.id, channelId, 'channel');
  };

  return (
    <div
      className={cn(
        'group flex gap-3 px-4 py-3 transition-colors hover:bg-accent/50',
        isSystem && 'bg-muted/30'
      )}
      data-testid="channel-message"
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback
          className={cn(
            'text-white',
            isUser && 'bg-slate-600',
            isAgent && agentColor,
            isSystem && 'bg-gray-400'
          )}
        >
          {isUser && <UserIcon className="h-4 w-4" />}
          {isAgent && message.agentName && (
            <span className="text-xs font-semibold">
              {message.agentName[0]}
            </span>
          )}
          {isSystem && <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Message content */}
      <div className="flex-1 overflow-hidden">
        {/* Header: Agent name + timestamp */}
        <div className="mb-1 flex items-baseline gap-2">
          <span
            className={cn(
              'text-sm font-semibold',
              isUser && 'text-slate-600',
              isAgent && 'text-foreground',
              isSystem && 'text-muted-foreground'
            )}
          >
            {isUser && 'You'}
            {isAgent && message.agentName}
            {isSystem && 'System'}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
        </div>

        {/* Message text */}
        <div className="text-sm text-foreground/90">
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Thread actions (Story 39.35) */}
        {!isSystem && (
          <div className="mt-2 flex items-center gap-2">
            {/* Thread count (if has replies) */}
            <ThreadCount count={threadCount} onClick={handleReplyInThread} />

            {/* Reply button (shows on hover) */}
            <ReplyButton onClick={handleReplyInThread} />
          </div>
        )}
      </div>
    </div>
  );
}
