/**
 * Main Content - Tab content area
 *
 * Story 39.30: Updated for DualSidebar support
 * Story 39.32: Added DMConversationView integration
 * Story 39.33: Added ChannelView integration
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import { ReadOnlyBanner } from '@/components/session/ReadOnlyBanner';
import { ChatTab } from '@/components/tabs/ChatTab';
import { ActivityTab } from '@/components/tabs/ActivityTab';
import { FilesTab } from '@/components/tabs/FilesTab';
import { KanbanTab } from '@/components/tabs/KanbanTab';
import { GitTab } from '@/components/tabs/GitTab';
import { CeremoniesTab } from '@/components/tabs/CeremoniesTab';
import { DMConversationView } from '@/components/dms/DMConversationView';
import { ChannelView } from '@/components/channels/ChannelView';
import { useChatStore } from '@/stores/chatStore';
import { useChannelStore } from '@/stores/channelStore';
import { useNavigationStore } from '@/stores/navigationStore';
import type { TabId } from './Sidebar';

interface MainContentProps {
  activeTab: TabId;
}

export function MainContent({ activeTab }: MainContentProps) {
  const { activeAgent } = useChatStore();
  const { activeChannel } = useChannelStore();
  const { primaryView } = useNavigationStore();

  const renderTabContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatTab />;
      case 'activity':
        return <ActivityTab />;
      case 'files':
        return <FilesTab />;
      case 'kanban':
        return <KanbanTab />;
      case 'git':
        return <GitTab />;
      case 'ceremonies':
        return <CeremoniesTab />;
      default:
        return <ChatTab />;
    }
  };

  // Story 39.32: Show DM conversation view when in DMs and an agent is selected
  const showDMConversation = primaryView === 'dms' && activeAgent !== null;

  // Story 39.33: Show channel view when in Channels and a channel is selected
  const showChannelView = primaryView === 'channels' && activeChannel !== null;

  return (
    <main className="flex flex-col overflow-hidden">
      {/* Read-Only Banner */}
      {!showDMConversation && !showChannelView && (
        <div className="shrink-0 p-4 pb-0">
          <ReadOnlyBanner />
        </div>
      )}

      {/* Tab Content or DM Conversation or Channel View */}
      {showDMConversation && activeAgent ? (
        // Story 39.32: Direct conversation view (no ScrollArea - handled internally)
        <div className="h-full">
          <DMConversationView agent={activeAgent} />
        </div>
      ) : showChannelView && activeChannel ? (
        // Story 39.33: Channel view (no ScrollArea - handled internally)
        <div className="h-full">
          <ChannelView channel={activeChannel} />
        </div>
      ) : (
        // Original tab content
        <ScrollArea className="flex-1">
          <div className="h-full min-h-0">{renderTabContent()}</div>
        </ScrollArea>
      )}
    </main>
  );
}
