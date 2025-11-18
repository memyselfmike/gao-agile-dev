/**
 * Secondary Sidebar - Detailed content based on primary selection
 *
 * Story 39.30: Dual Sidebar Navigation (Primary + Secondary)
 * Story 39.31: Enhanced DM list with real API data
 * Story 39.33: Channels Section UI
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { DMList } from '@/components/dms/DMList';
import { ChannelList } from '@/components/channels/ChannelList';
import { useChannelStore } from '@/stores/channelStore';
import { cn } from '@/lib/utils';
import type { PrimaryView } from '@/stores/navigationStore';
import type { Agent } from '@/types';
import {
  FileText,
  Bell,
  Palette,
  Shield,
  Database,
} from 'lucide-react';

interface SecondarySidebarProps {
  primaryView: PrimaryView;
  isOpen: boolean;
}

// GAO-Dev's 8 agents
const AGENTS: Agent[] = [
  {
    id: 'brian',
    name: 'Brian',
    role: 'Workflow Coordinator',
    description: 'Intelligent workflow selection and coordination',
    status: 'idle',
  },
  {
    id: 'john',
    name: 'John',
    role: 'Product Manager',
    description: 'Product requirements and feature definition',
    status: 'idle',
  },
  {
    id: 'winston',
    name: 'Winston',
    role: 'Technical Architect',
    description: 'System architecture and technical design',
    status: 'idle',
  },
  {
    id: 'sally',
    name: 'Sally',
    role: 'UX Designer',
    description: 'User experience and interface design',
    status: 'idle',
  },
  {
    id: 'bob',
    name: 'Bob',
    role: 'Scrum Master',
    description: 'Story management and sprint coordination',
    status: 'idle',
  },
  {
    id: 'amelia',
    name: 'Amelia',
    role: 'Software Developer',
    description: 'Code implementation and testing',
    status: 'idle',
  },
  {
    id: 'murat',
    name: 'Murat',
    role: 'Test Architect',
    description: 'Quality assurance and test strategies',
    status: 'idle',
  },
  {
    id: 'mary',
    name: 'Mary',
    role: 'Business Analyst',
    description: 'Vision elicitation and requirements analysis',
    status: 'idle',
  },
];

// DMsList now uses the enhanced DMList component from Story 39.31
function DMsList() {
  return <DMList agents={AGENTS} />;
}

// ChannelsList now uses the enhanced ChannelList component from Story 39.33
function ChannelsList() {
  const { activeChannel, selectChannel } = useChannelStore();

  return (
    <ChannelList
      activeChannelId={activeChannel?.id || null}
      onChannelSelect={selectChannel}
    />
  );
}

function HomeView() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-foreground">Dashboard</h3>
        <p className="text-xs text-muted-foreground">Quick overview of GAO-Dev activity</p>
      </div>
      <Separator />
      <div className="space-y-2">
        <Button variant="ghost" className="w-full justify-start" disabled>
          <FileText className="mr-2 h-4 w-4" />
          Recent Documents
        </Button>
        <Button variant="ghost" className="w-full justify-start" disabled>
          <Bell className="mr-2 h-4 w-4" />
          Notifications
        </Button>
      </div>
      <p className="text-xs text-muted-foreground italic">
        Dashboard view coming in future story
      </p>
    </div>
  );
}

function SettingsView() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold text-foreground">Settings</h3>
        <p className="text-xs text-muted-foreground">Configure GAO-Dev preferences</p>
      </div>
      <Separator />
      <div className="space-y-2">
        <Button variant="ghost" className="w-full justify-start" disabled>
          <Palette className="mr-2 h-4 w-4" />
          Appearance
        </Button>
        <Button variant="ghost" className="w-full justify-start" disabled>
          <Bell className="mr-2 h-4 w-4" />
          Notifications
        </Button>
        <Button variant="ghost" className="w-full justify-start" disabled>
          <Shield className="mr-2 h-4 w-4" />
          Security
        </Button>
        <Button variant="ghost" className="w-full justify-start" disabled>
          <Database className="mr-2 h-4 w-4" />
          Data & Storage
        </Button>
      </div>
      <p className="text-xs text-muted-foreground italic">
        Settings panel coming in future story
      </p>
    </div>
  );
}

export function SecondarySidebar({ primaryView, isOpen }: SecondarySidebarProps) {
  if (!isOpen) return null;

  return (
    <aside
      className={cn(
        'hidden min-w-0 flex-1 border-r border-border bg-card transition-all duration-75 lg:block',
        !isOpen && 'w-0 opacity-0'
      )}
      data-testid="secondary-sidebar"
      aria-label="Secondary navigation"
    >
      <ScrollArea className="h-full">
        {primaryView === 'dms' && <DMsList />}
        {primaryView === 'channels' && <ChannelsList />}
        {primaryView === 'home' && <HomeView />}
        {primaryView === 'settings' && <SettingsView />}
      </ScrollArea>
    </aside>
  );
}
