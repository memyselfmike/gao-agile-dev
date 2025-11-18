/**
 * Main Content - Tab content area
 *
 * Epic 39.8: Updated to show DualSidebar within Communication tab
 * Story 39.32: Added DMConversationView integration
 * Story 39.33: Added ChannelView integration
 * Story 39.38: Added ResizableLayout for panel resizing
 * Story 39.39: Added layout ref for preset application
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import { ReadOnlyBanner } from '@/components/session/ReadOnlyBanner';
import { ActivityTab } from '@/components/tabs/ActivityTab';
import { FilesTab } from '@/components/tabs/FilesTab';
import { KanbanTab } from '@/components/tabs/KanbanTab';
import { GitTab } from '@/components/tabs/GitTab';
import { DMConversationView } from '@/components/dms/DMConversationView';
import { ChannelView } from '@/components/channels/ChannelView';
import { DualSidebar } from './DualSidebar';
import { ResizableLayout, type ResizableLayoutHandle } from './ResizableLayout';
import { useChatStore } from '@/stores/chatStore';
import { useChannelStore } from '@/stores/channelStore';
import { useNavigationStore } from '@/stores/navigationStore';
import type { TabId } from './Sidebar';

interface MainContentProps {
  activeTab: TabId;
  layoutRef?: React.RefObject<ResizableLayoutHandle | null>;
}

export function MainContent({ activeTab, layoutRef }: MainContentProps) {
  const { activeAgent } = useChatStore();
  const { activeChannel } = useChannelStore();
  const { primaryView } = useNavigationStore();

  // Communication tab: Show DualSidebar + DM/Channel conversation views with resizable layout
  if (activeTab === 'communication') {
    // Story 39.32: Show DM conversation view when in DMs and an agent is selected
    const showDMConversation = primaryView === 'dms' && activeAgent !== null;

    // Story 39.33: Show channel view when in Channels and a channel is selected
    const showChannelView = primaryView === 'channels' && activeChannel !== null;

    return (
      <ResizableLayout
        ref={layoutRef}
        leftSidebar={<DualSidebar />}
        mainContent={
          <main id="main-content" className="flex h-full flex-col overflow-hidden">
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
              // Default: Show welcome/empty state
              <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
                <div>
                  <h2 className="mb-2 text-xl font-semibold">Welcome to GAO-Dev Communication</h2>
                  <p>Select an agent from Direct Messages or a channel to start chatting.</p>
                </div>
              </div>
            )}
          </main>
        }
      />
    );
  }

  // Other tabs: Show regular tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'activity':
        return <ActivityTab />;
      case 'files':
        return <FilesTab />;
      case 'kanban':
        return <KanbanTab />;
      case 'git':
        return <GitTab />;
      default:
        return <ActivityTab />;
    }
  };

  return (
    <main id="main-content" className="flex flex-col overflow-hidden">
      {/* Read-Only Banner */}
      <div className="shrink-0 p-4 pb-0">
        <ReadOnlyBanner />
      </div>

      {/* Tab Content */}
      <ScrollArea className="flex-1">
        <div className="h-full min-h-0">{renderTabContent()}</div>
      </ScrollArea>
    </main>
  );
}
