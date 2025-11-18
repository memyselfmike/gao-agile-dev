/**
 * ChannelList - Full channel list with sorting and filtering
 *
 * Story 39.33: Channels Section - Ceremony Channels UI
 */
import { useEffect, useState, useCallback } from 'react';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { ChannelItem } from './ChannelItem';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { Channel } from '@/types';

interface ChannelListProps {
  activeChannelId: string | null;
  onChannelSelect: (channel: Channel) => void;
}

export function ChannelList({
  activeChannelId,
  onChannelSelect,
}: ChannelListProps) {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isArchivedExpanded, setIsArchivedExpanded] = useState(false);

  // Fetch channels from API
  const fetchChannels = useCallback(async () => {
    try {
      const response = await fetch('/api/channels');
      if (!response.ok) {
        throw new Error('Failed to fetch channels');
      }
      const data = await response.json();
      setChannels(data.channels);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch channels:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchChannels();

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchChannels, 30000);
    return () => clearInterval(interval);
  }, [fetchChannels]);

  // Subscribe to WebSocket for real-time updates
  useEffect(() => {
    // TODO: Add WebSocket subscription for channel events:
    // - channel.created
    // - channel.message
    // - channel.archived
  }, []);

  // Separate active and archived channels
  const activeChannels = channels.filter((c) => c.status === 'active');
  const archivedChannels = channels.filter((c) => c.status === 'archived');

  // Sort active channels by last message timestamp (most recent first)
  const sortedActiveChannels = [...activeChannels].sort(
    (a, b) =>
      new Date(b.lastMessageAt).getTime() -
      new Date(a.lastMessageAt).getTime()
  );

  // Sort archived channels by last message timestamp (most recent first)
  const sortedArchivedChannels = [...archivedChannels].sort(
    (a, b) =>
      new Date(b.lastMessageAt).getTime() -
      new Date(a.lastMessageAt).getTime()
  );

  if (isLoading) {
    return (
      <div className="flex flex-col gap-1 p-2">
        <div className="mb-2 px-2">
          <h3 className="text-sm font-semibold text-foreground">
            Ceremony Channels
          </h3>
          <p className="text-xs text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-1 p-2">
        <div className="mb-2 px-2">
          <h3 className="text-sm font-semibold text-foreground">
            Ceremony Channels
          </h3>
          <p className="text-xs text-destructive">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 p-2">
      <div className="mb-2 px-2">
        <h3 className="text-sm font-semibold text-foreground">
          Ceremony Channels
        </h3>
        <p className="text-xs text-muted-foreground">
          Multi-agent ceremony coordination
        </p>
      </div>
      <Separator className="mb-2" />

      {/* Active Channels */}
      {sortedActiveChannels.length > 0 && (
        <div className="mb-4">
          <h4 className="mb-1 px-2 text-xs font-medium text-muted-foreground">
            Active
          </h4>
          {sortedActiveChannels.map((channel) => (
            <ChannelItem
              key={channel.id}
              channel={channel}
              isActive={activeChannelId === channel.id}
              onClick={() => onChannelSelect(channel)}
            />
          ))}
        </div>
      )}

      {/* Archived Channels (Collapsible) */}
      {sortedArchivedChannels.length > 0 && (
        <div>
          <Button
            variant="ghost"
            size="sm"
            className="mb-1 w-full justify-start px-2 text-xs font-medium text-muted-foreground hover:bg-transparent"
            onClick={() => setIsArchivedExpanded(!isArchivedExpanded)}
          >
            {isArchivedExpanded ? (
              <ChevronDown className="mr-1 h-3 w-3" />
            ) : (
              <ChevronRight className="mr-1 h-3 w-3" />
            )}
            Archived ({sortedArchivedChannels.length})
          </Button>
          {isArchivedExpanded && (
            <div className="space-y-0.5">
              {sortedArchivedChannels.map((channel) => (
                <div key={channel.id} data-testid="archived-channel">
                  <ChannelItem
                    channel={channel}
                    isActive={activeChannelId === channel.id}
                    onClick={() => onChannelSelect(channel)}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {channels.length === 0 && (
        <div className="px-2 py-4 text-center text-sm text-muted-foreground">
          No active ceremonies
        </div>
      )}
    </div>
  );
}
