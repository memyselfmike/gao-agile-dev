/**
 * Secondary Sidebar - Detailed content based on primary selection
 *
 * Story 39.30: Dual Sidebar Navigation (Primary + Secondary)
 * Story 39.31: Enhanced DM list with real API data
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DMList } from '@/components/dms/DMList';
import { cn } from '@/lib/utils';
import type { PrimaryView } from '@/stores/navigationStore';
import type { Agent } from '@/types';
import {
  Hash,
  Archive,
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

// Mock ceremony channels
const ACTIVE_CHANNELS = [
  { id: 'sprint-planning', name: 'Sprint Planning', unread: 3, lastActivity: '2 hours ago' },
  { id: 'daily-standup', name: 'Daily Standup', unread: 0, lastActivity: '5 hours ago' },
  { id: 'retrospective', name: 'Retrospective', unread: 1, lastActivity: '1 day ago' },
];

const ARCHIVED_CHANNELS = [
  { id: 'epic-28-retro', name: 'Epic 28 Retrospective', lastActivity: '2 weeks ago' },
  { id: 'q4-planning', name: 'Q4 Planning', lastActivity: '1 month ago' },
];

// DMsList now uses the enhanced DMList component from Story 39.31
function DMsList() {
  return <DMList agents={AGENTS} />;
}

function ChannelsList() {
  return (
    <div className="flex flex-col gap-1 p-2">
      <div className="mb-2 px-2">
        <h3 className="text-sm font-semibold text-foreground">Ceremony Channels</h3>
        <p className="text-xs text-muted-foreground">Multi-agent ceremony coordination</p>
      </div>
      <Separator className="mb-2" />

      {/* Active Channels */}
      <div className="mb-4">
        <h4 className="mb-1 px-2 text-xs font-medium text-muted-foreground">Active</h4>
        {ACTIVE_CHANNELS.map((channel) => (
          <Button
            key={channel.id}
            variant="ghost"
            className="h-auto justify-start px-3 py-2 text-left"
            data-testid={`channel-${channel.id}`}
          >
            <div className="flex w-full items-start gap-2">
              <Hash className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <div className="flex-1 overflow-hidden">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{channel.name}</span>
                  {channel.unread > 0 && (
                    <Badge variant="destructive" className="ml-1 h-5 px-1.5 text-xs">
                      {channel.unread}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{channel.lastActivity}</p>
              </div>
            </div>
          </Button>
        ))}
      </div>

      {/* Archived Channels */}
      <div>
        <h4 className="mb-1 px-2 text-xs font-medium text-muted-foreground">Archived</h4>
        {ARCHIVED_CHANNELS.map((channel) => (
          <Button
            key={channel.id}
            variant="ghost"
            className="h-auto justify-start px-3 py-2 text-left opacity-60"
            data-testid={`channel-${channel.id}`}
          >
            <div className="flex w-full items-start gap-2">
              <Archive className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <div className="flex-1 overflow-hidden">
                <span className="font-medium">{channel.name}</span>
                <p className="text-xs text-muted-foreground">{channel.lastActivity}</p>
              </div>
            </div>
          </Button>
        ))}
      </div>
    </div>
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
        'hidden w-64 border-r border-border bg-card transition-all duration-75 lg:block',
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
