/**
 * ChannelView - Main channel conversation container
 *
 * Story 39.33: Channels Section - Ceremony Channels UI
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Shows channel messages with multi-agent participants
 * Allows user to send messages to active channels
 * Shows archive banner for archived channels (read-only)
 * Includes ThreadPanel for threaded conversations
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ChannelMessage } from './ChannelMessage';
import { ThreadPanel } from '../threads/ThreadPanel';
import { useSessionStore } from '@/stores/sessionStore';
import { useThreadStore } from '@/stores/threadStore';
import { cn } from '@/lib/utils';
import { Archive, Send, Hash, Users, AlertCircle, Download } from 'lucide-react';
import type { Channel, ChannelMessage as IChannelMessage } from '@/types';

interface ChannelViewProps {
  channel: Channel;
}

export function ChannelView({ channel }: ChannelViewProps) {
  const { sessionToken } = useSessionStore();
  const { activeThread } = useThreadStore();
  const [messages, setMessages] = useState<IChannelMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isArchived = channel.status === 'archived';

  // Load messages
  const loadMessages = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/channels/${channel.id}/messages?offset=0&limit=50`
      );

      if (!response.ok) {
        throw new Error('Failed to load messages');
      }

      const data = await response.json();
      setMessages(data.messages);
      setError(null);
    } catch (err) {
      console.error('Failed to load messages:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [channel.id]);

  // Load messages when channel changes
  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Subscribe to WebSocket for real-time updates
  useEffect(() => {
    // TODO: WebSocket subscription for channel events
    // - channel.message: New message received
    // - channel.archived: Channel archived
  }, [channel.id]);

  // Send message
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSending || isArchived) return;

    if (!sessionToken) {
      setError('No session token. Please refresh the page.');
      return;
    }

    const content = inputValue.trim();
    setInputValue('');
    setIsSending(true);

    try {
      const response = await fetch(`/api/channels/${channel.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send message');
      }

      // Add user message optimistically
      const userMessage: IChannelMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      // Restore input on error
      setInputValue(content);
    } finally {
      setIsSending(false);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Export channel transcript
  const handleExportTranscript = async () => {
    if (isExporting) return;

    setIsExporting(true);

    try {
      const response = await fetch(`/api/channels/${channel.id}/export`);

      if (!response.ok) {
        throw new Error('Failed to export transcript');
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${channel.id}-transcript.md`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Export failed: ${errorMessage}`);
    } finally {
      setIsExporting(false);
    }
  };

  // Get ceremony type badge color
  const getCeremonyColor = () => {
    switch (channel.ceremonyType) {
      case 'sprint-planning':
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-400';
      case 'retrospective':
        return 'bg-purple-500/10 text-purple-700 dark:text-purple-400';
      case 'daily-standup':
        return 'bg-green-500/10 text-green-700 dark:text-green-400';
      case 'demo':
        return 'bg-orange-500/10 text-orange-700 dark:text-orange-400';
      case 'backlog-refinement':
        return 'bg-teal-500/10 text-teal-700 dark:text-teal-400';
      default:
        return 'bg-gray-500/10 text-gray-700 dark:text-gray-400';
    }
  };

  return (
    <div className="flex h-full">
      {/* Main channel area */}
      <div
        className={cn(
          'flex h-full flex-col transition-all duration-200',
          activeThread ? 'w-[60%]' : 'w-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b bg-background px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Channel icon */}
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg',
              isArchived ? 'bg-muted' : 'bg-primary/10'
            )}
          >
            {isArchived ? (
              <Archive className="h-5 w-5 text-muted-foreground" />
            ) : (
              <Hash className="h-5 w-5 text-primary" />
            )}
          </div>

          {/* Channel info */}
          <div>
            <h2 className="text-lg font-semibold">{channel.name}</h2>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {/* Ceremony type badge */}
              <Badge variant="outline" className={cn('text-xs', getCeremonyColor())}>
                {channel.ceremonyType.replace('-', ' ')}
              </Badge>

              {/* Participants count */}
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                <span>{channel.participants.length} participants</span>
              </div>
            </div>
          </div>
        </div>

        {/* Status badge and export button */}
        <div className="flex items-center gap-2">
          {isArchived && (
            <>
              <Badge variant="secondary" className="flex items-center gap-1">
                <Archive className="h-3 w-3" />
                Archived
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportTranscript}
                disabled={isExporting}
                className="flex items-center gap-1"
                data-testid="channel-export-button"
              >
                <Download className="h-3 w-3" />
                {isExporting ? 'Exporting...' : 'Export Transcript'}
              </Button>
            </>
          )}
        </div>
      </div>

        {/* Archive banner (if archived) */}
        {isArchived && (
          <Alert className="m-4 border-yellow-500/50 bg-yellow-500/10">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-sm text-yellow-700 dark:text-yellow-400">
              This channel is archived (read-only). You cannot send new messages.
            </AlertDescription>
          </Alert>
        )}

        {/* Error banner */}
        {error && !isArchived && (
          <Alert variant="destructive" className="m-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">{error}</AlertDescription>
          </Alert>
        )}

        {/* Message list */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full" ref={scrollRef}>
            {isLoading ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">Loading messages...</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">No messages yet</p>
              </div>
            ) : (
              <div className="flex flex-col">
                {messages.map((message) => (
                  <ChannelMessage key={message.id} message={message} channelId={channel.id} />
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Input (only for active channels) */}
        {!isArchived && (
          <div className="border-t bg-background p-4">
            <div className="flex gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Message ${channel.name}...`}
                disabled={isSending}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isSending}
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              This channel includes: {channel.participants.join(', ')}
            </p>
          </div>
        )}
      </div>

      {/* Thread Panel (slides in from right) */}
      <ThreadPanel agentName="Multi-agent" showReasoning={false} />
    </div>
  );
}
