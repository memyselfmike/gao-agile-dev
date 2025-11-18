/**
 * Primary Sidebar - Icon navigation for main sections
 *
 * Story 39.30: Dual Sidebar Navigation (Primary + Secondary)
 */
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Home, MessageSquare, Hash, Settings, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PrimaryView } from '@/stores/navigationStore';

interface PrimaryNavItem {
  id: PrimaryView;
  label: string;
  icon: LucideIcon;
  ariaLabel: string;
}

const PRIMARY_NAV_ITEMS: PrimaryNavItem[] = [
  { id: 'home', label: 'Home', icon: Home, ariaLabel: 'Home Dashboard' },
  { id: 'dms', label: 'DMs', icon: MessageSquare, ariaLabel: 'Direct Messages' },
  { id: 'channels', label: 'Channels', icon: Hash, ariaLabel: 'Channels' },
  { id: 'settings', label: 'Settings', icon: Settings, ariaLabel: 'Settings' },
];

interface PrimarySidebarProps {
  activeView: PrimaryView;
  onViewChange: (view: PrimaryView) => void;
}

export function PrimarySidebar({ activeView, onViewChange }: PrimarySidebarProps) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, view: PrimaryView) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onViewChange(view);
    }
  };

  return (
    <aside
      className="flex w-16 flex-col items-center border-r border-border bg-card py-4"
      data-testid="primary-sidebar"
      aria-label="Primary navigation"
    >
      <Separator className="mb-2" />
      {/* Navigation Icons */}
      <nav className="flex flex-col gap-2" role="navigation">
        {PRIMARY_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <Button
              key={item.id}
              variant={isActive ? 'default' : 'ghost'}
              size="icon"
              onClick={() => onViewChange(item.id)}
              onKeyDown={(e) => handleKeyDown(e, item.id)}
              className={cn(
                'relative h-12 w-12 transition-all duration-75',
                isActive && 'bg-primary text-primary-foreground'
              )}
              aria-label={item.ariaLabel}
              aria-current={isActive ? 'page' : undefined}
              data-testid={`primary-nav-${item.id}`}
            >
              <Icon className="h-5 w-5" />
              {/* Active indicator */}
              {isActive && (
                <div className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r bg-primary-foreground" />
              )}
            </Button>
          );
        })}
      </nav>
    </aside>
  );
}
