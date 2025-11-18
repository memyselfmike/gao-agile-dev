/**
 * DMList - Full DM list with sorting and keyboard navigation
 *
 * Story 39.31: DMs Section - Agent List and Conversation UI
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { Separator } from '@/components/ui/separator';
import { useChatStore } from '@/stores/chatStore';
import { DMItem } from './DMItem';
import type { Agent } from '@/types';

interface DMConversation {
  agent: string;
  lastMessage: string;
  lastMessageAt: string;
  messageCount: number;
}

interface DMListProps {
  agents: Agent[];
}

export function DMList({ agents }: DMListProps) {
  const { activeAgent, switchAgent } = useChatStore();
  const [conversations, setConversations] = useState<DMConversation[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Fetch DM conversations from API
  useEffect(() => {
    async function fetchConversations() {
      try {
        const response = await fetch('/api/dms');
        if (!response.ok) {
          throw new Error('Failed to fetch DM conversations');
        }
        const data = await response.json();
        setConversations(data.conversations);
      } catch (error) {
        console.error('Failed to fetch DM conversations:', error);
        // Fallback to empty conversations
        setConversations(
          agents.map((agent) => ({
            agent: agent.id,
            lastMessage: 'No messages yet',
            lastMessageAt: new Date().toISOString(),
            messageCount: 0,
          }))
        );
      }
    }

    fetchConversations();

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchConversations, 30000);
    return () => clearInterval(interval);
  }, [agents]);

  // Subscribe to WebSocket for real-time updates
  useEffect(() => {
    // TODO: Add WebSocket subscription for dm.updated events
    // This will be implemented when WebSocket infrastructure is enhanced
  }, []);

  // Merge conversations with agent metadata and sort
  const enrichedConversations = conversations
    .map((conv) => {
      const agent = agents.find((a) => a.id === conv.agent);
      if (!agent) return null;
      return { ...conv, agent };
    })
    .filter((c): c is NonNullable<typeof c> => c !== null)
    .sort((a, b) => {
      // Sort by last message timestamp (most recent first)
      return (
        new Date(b.lastMessageAt).getTime() -
        new Date(a.lastMessageAt).getTime()
      );
    });

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (
        !listRef.current ||
        !listRef.current.contains(document.activeElement)
      ) {
        return;
      }

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setSelectedIndex((prev) => {
            const nextIndex =
              prev < enrichedConversations.length - 1 ? prev + 1 : prev;
            // Scroll into view
            itemRefs.current[nextIndex]?.scrollIntoView({
              block: 'nearest',
              behavior: 'smooth',
            });
            return nextIndex;
          });
          break;

        case 'ArrowUp':
          event.preventDefault();
          setSelectedIndex((prev) => {
            const nextIndex = prev > 0 ? prev - 1 : prev;
            // Scroll into view
            itemRefs.current[nextIndex]?.scrollIntoView({
              block: 'nearest',
              behavior: 'smooth',
            });
            return nextIndex;
          });
          break;

        case 'Enter':
          event.preventDefault();
          const selected = enrichedConversations[selectedIndex];
          if (selected) {
            switchAgent(selected.agent);
          }
          break;
      }
    },
    [enrichedConversations, selectedIndex, switchAgent]
  );

  // Attach keyboard listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Update selected index when active agent changes
  useEffect(() => {
    if (activeAgent) {
      const index = enrichedConversations.findIndex(
        (c) => c.agent.id === activeAgent.id
      );
      if (index !== -1) {
        setSelectedIndex(index);
      }
    }
  }, [activeAgent, enrichedConversations]);

  return (
    <div ref={listRef} className="flex flex-col gap-1 p-2" tabIndex={0}>
      <div className="mb-2 px-2">
        <h3 className="text-sm font-semibold text-foreground">
          Direct Messages
        </h3>
        <p className="text-xs text-muted-foreground">
          Chat with GAO-Dev agents
        </p>
      </div>
      <Separator className="mb-2" />

      {enrichedConversations.length === 0 ? (
        <div className="px-2 py-4 text-center text-sm text-muted-foreground">
          No conversations yet
        </div>
      ) : (
        enrichedConversations.map((conv, index) => (
          <div
            key={conv.agent.id}
            ref={(el) => {
              itemRefs.current[index] = el;
            }}
          >
            <DMItem
              agent={conv.agent}
              lastMessage={conv.lastMessage}
              lastMessageAt={conv.lastMessageAt}
              messageCount={conv.messageCount}
              isActive={activeAgent?.id === conv.agent.id}
              onClick={() => switchAgent(conv.agent)}
            />
          </div>
        ))
      )}
    </div>
  );
}
