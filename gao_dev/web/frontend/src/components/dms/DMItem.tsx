/**
 * DMItem - Individual DM item component with avatar, name, preview, timestamp
 *
 * Story 39.31: DMs Section - Agent List and Conversation UI
 */
import { formatDistanceToNow } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Agent } from '@/types';

interface DMItemProps {
  agent: Agent;
  lastMessage: string;
  lastMessageAt: string;
  messageCount: number;
  isActive: boolean;
  onClick: () => void;
}

/**
 * Format timestamp to relative time (e.g., "2 min ago", "yesterday")
 */
function formatRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Unknown';
  }
}

/**
 * Get agent avatar color based on agent ID
 */
function getAgentColor(agentId: string): string {
  const colors: Record<string, string> = {
    brian: 'bg-blue-500',
    mary: 'bg-purple-500',
    john: 'bg-green-500',
    winston: 'bg-orange-500',
    sally: 'bg-pink-500',
    bob: 'bg-teal-500',
    amelia: 'bg-indigo-500',
    murat: 'bg-red-500',
  };
  return colors[agentId] || 'bg-gray-500';
}

export function DMItem({
  agent,
  lastMessage,
  lastMessageAt,
  messageCount,
  isActive,
  onClick,
}: DMItemProps) {
  const relativeTime = formatRelativeTime(lastMessageAt);
  const avatarColor = getAgentColor(agent.id);

  return (
    <Button
      variant={isActive ? 'secondary' : 'ghost'}
      className={cn(
        'h-auto w-full justify-start px-3 py-2.5 text-left transition-colors',
        isActive && 'bg-secondary',
        !isActive && 'hover:bg-accent'
      )}
      onClick={onClick}
      data-testid={`dm-item-${agent.id}`}
    >
      <div className="flex w-full items-start gap-3">
        {/* Avatar */}
        <div
          className={cn(
            'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-white',
            avatarColor
          )}
        >
          <span className="text-sm font-semibold">{agent.name[0]}</span>
        </div>

        {/* Content */}
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          {/* Header: Name + Timestamp */}
          <div className="flex items-center justify-between gap-2">
            <span className="truncate font-semibold text-foreground">
              {agent.name}
            </span>
            <span className="flex-shrink-0 text-xs text-muted-foreground">
              {relativeTime}
            </span>
          </div>

          {/* Role */}
          <p className="text-xs text-muted-foreground">{agent.role}</p>

          {/* Last Message Preview */}
          <p className="truncate text-sm text-muted-foreground">
            {lastMessage}
          </p>

          {/* Message Count Badge (if > 0) */}
          {messageCount > 0 && (
            <div className="mt-1">
              <Badge variant="outline" className="h-5 px-1.5 text-xs">
                {messageCount} {messageCount === 1 ? 'message' : 'messages'}
              </Badge>
            </div>
          )}
        </div>

        {/* Active Indicator */}
        {agent.status === 'active' && (
          <div className="flex h-10 items-center">
            <div className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
          </div>
        )}
      </div>
    </Button>
  );
}
