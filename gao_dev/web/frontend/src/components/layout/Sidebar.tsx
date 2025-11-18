/**
 * Sidebar - Tab navigation icons
 *
 * Updated: Epic 39.8 - Unified Chat+Ceremonies into single "Communication" tab
 */
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  MessageSquare,
  Activity,
  FolderTree,
  LayoutDashboard,
  GitBranch,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export type TabId = 'communication' | 'activity' | 'files' | 'kanban' | 'git';

interface Tab {
  id: TabId;
  label: string;
  icon: LucideIcon;
  shortcut: string;
}

const TABS: Tab[] = [
  { id: 'communication', label: 'Communication', icon: MessageSquare, shortcut: '1' },
  { id: 'activity', label: 'Activity', icon: Activity, shortcut: '2' },
  { id: 'files', label: 'Files', icon: FolderTree, shortcut: '3' },
  { id: 'kanban', label: 'Kanban', icon: LayoutDashboard, shortcut: '4' },
  { id: 'git', label: 'Git', icon: GitBranch, shortcut: '5' },
];

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tabId: TabId) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <aside className="flex w-16 flex-col items-center border-r border-border bg-card py-4">
      {/* Tab Icons */}
      <div className="flex flex-col gap-2">
        {TABS.map((tab, index) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <div key={tab.id}>
              {index === 0 && <Separator className="mb-2" />}
              <Button
                variant={isActive ? 'default' : 'ghost'}
                size="icon"
                onClick={() => onTabChange(tab.id)}
                className={cn(
                  'relative h-12 w-12',
                  isActive && 'bg-primary text-primary-foreground',
                )}
                aria-label={`${tab.label} (Cmd+${tab.shortcut})`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="h-5 w-5" />
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r bg-primary-foreground" />
                )}
              </Button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

export { TABS };
