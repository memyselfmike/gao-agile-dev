/**
 * ChannelItem - Individual channel item in channel list
 *
 * Story 39.33: Channels Section - Ceremony Channels UI
 */
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Hash, Archive, Users } from 'lucide-react';
import type { Channel } from '@/types';

interface ChannelItemProps {
  channel: Channel;
  isActive: boolean;
  onClick: () => void;
}

// Format timestamp as relative time
function formatRelativeTime(isoTimestamp: string): string {
  const now = new Date();
  const timestamp = new Date(isoTimestamp);
  const diffMs = now.getTime() - timestamp.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return timestamp.toLocaleDateString();
}

export function ChannelItem({ channel, isActive, onClick }: ChannelItemProps) {
  const isArchived = channel.status === 'archived';

  return (
    <Button
      variant="ghost"
      className={cn(
        'h-auto w-full justify-start gap-3 px-3 py-2.5 text-left transition-colors',
        isActive && 'bg-accent',
        isArchived && 'opacity-60'
      )}
      onClick={onClick}
      data-testid="channel-item"
    >
      {/* Channel icon */}
      <div className="flex-shrink-0">
        {isArchived ? (
          <Archive className="h-5 w-5 text-muted-foreground" />
        ) : (
          <Hash className="h-5 w-5 text-muted-foreground" />
        )}
      </div>

      {/* Channel info */}
      <div className="flex-1 overflow-hidden">
        {/* Name and status */}
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'truncate font-medium',
              isActive && 'text-foreground',
              !isActive && 'text-foreground/90'
            )}
          >
            {channel.name}
          </span>

          {/* Active indicator dot */}
          {!isArchived && (
            <div className="h-2 w-2 flex-shrink-0 rounded-full bg-green-500" />
          )}
        </div>

        {/* Last message preview */}
        <p className="mt-0.5 truncate text-xs text-muted-foreground">
          {channel.lastMessage}
        </p>

        {/* Metadata row */}
        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
          {/* Participants */}
          <div className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            <span>{channel.participants.length}</span>
          </div>

          {/* Separator */}
          <span>•</span>

          {/* Timestamp */}
          <span>{formatRelativeTime(channel.lastMessageAt)}</span>

          {/* Message count */}
          {!isArchived && channel.messageCount > 0 && (
            <>
              <span>•</span>
              <span>{channel.messageCount} messages</span>
            </>
          )}
        </div>
      </div>

      {/* Archive badge (if archived) */}
      {isArchived && (
        <Badge variant="outline" className="flex-shrink-0 text-xs">
          Archived
        </Badge>
      )}
    </Button>
  );
}
