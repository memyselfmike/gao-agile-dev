/**
 * Main Content - Tab content area
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import { ReadOnlyBanner } from '@/components/session/ReadOnlyBanner';
import { ChatTab } from '@/components/tabs/ChatTab';
import { ActivityTab } from '@/components/tabs/ActivityTab';
import { FilesTab } from '@/components/tabs/FilesTab';
import { KanbanTab } from '@/components/tabs/KanbanTab';
import { GitTab } from '@/components/tabs/GitTab';
import { CeremoniesTab } from '@/components/tabs/CeremoniesTab';
import type { TabId } from './Sidebar';

interface MainContentProps {
  activeTab: TabId;
}

export function MainContent({ activeTab }: MainContentProps) {
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

  return (
    <main className="flex flex-col overflow-hidden">
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
