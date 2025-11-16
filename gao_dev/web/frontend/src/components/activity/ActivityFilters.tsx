/**
 * Activity Filters - Filter events by type and agent
 *
 * Story 39.10: Activity stream filters and search
 */
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Filter, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { ActivityEventType } from '@/types';

interface ActivityFiltersProps {
  selectedTypes: ActivityEventType[];
  selectedAgents: string[];
  onTypesChange: (types: ActivityEventType[]) => void;
  onAgentsChange: (agents: string[]) => void;
}

const EVENT_TYPES: ActivityEventType[] = ['Workflow', 'Chat', 'File', 'State', 'Ceremony', 'Git'];

const AGENTS = [
  'Brian',
  'Mary',
  'John',
  'Winston',
  'Sally',
  'Bob',
  'Amelia',
  'Murat',
];

export function ActivityFilters({
  selectedTypes,
  selectedAgents,
  onTypesChange,
  onAgentsChange,
}: ActivityFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Keyboard shortcut: Cmd+Shift+F
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'f') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const toggleType = (type: ActivityEventType) => {
    if (selectedTypes.includes(type)) {
      onTypesChange(selectedTypes.filter((t) => t !== type));
    } else {
      onTypesChange([...selectedTypes, type]);
    }
  };

  const toggleAgent = (agent: string) => {
    if (selectedAgents.includes(agent)) {
      onAgentsChange(selectedAgents.filter((a) => a !== agent));
    } else {
      onAgentsChange([...selectedAgents, agent]);
    }
  };

  const clearAll = () => {
    onTypesChange([]);
    onAgentsChange([]);
  };

  const totalSelected = selectedTypes.length + selectedAgents.length;

  return (
    <div className="flex items-center gap-2">
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Filter className="h-4 w-4" />
            Filters
            {totalSelected > 0 && (
              <Badge variant="secondary" className="ml-1 h-5 px-1 text-xs">
                {totalSelected}
              </Badge>
            )}
            <kbd className="pointer-events-none ml-1 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:inline-flex">
              <span className="text-xs">⌘⇧</span>F
            </kbd>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          <div className="flex items-center justify-between px-2 py-1.5">
            <DropdownMenuLabel className="p-0">Event Type</DropdownMenuLabel>
            {selectedTypes.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onTypesChange([])}
                className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </Button>
            )}
          </div>
          {EVENT_TYPES.map((type) => (
            <DropdownMenuCheckboxItem
              key={type}
              checked={selectedTypes.includes(type)}
              onCheckedChange={() => toggleType(type)}
            >
              {type}
            </DropdownMenuCheckboxItem>
          ))}

          <DropdownMenuSeparator />

          <div className="flex items-center justify-between px-2 py-1.5">
            <DropdownMenuLabel className="p-0">Agent</DropdownMenuLabel>
            {selectedAgents.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onAgentsChange([])}
                className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </Button>
            )}
          </div>
          {AGENTS.map((agent) => (
            <DropdownMenuCheckboxItem
              key={agent}
              checked={selectedAgents.includes(agent)}
              onCheckedChange={() => toggleAgent(agent)}
            >
              {agent}
            </DropdownMenuCheckboxItem>
          ))}

          {totalSelected > 0 && (
            <>
              <DropdownMenuSeparator />
              <div className="p-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAll}
                  className="w-full gap-2"
                >
                  <X className="h-3 w-3" />
                  Clear All Filters
                </Button>
              </div>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Active Filter Chips */}
      {selectedTypes.map((type) => (
        <Badge key={type} variant="secondary" className="gap-1">
          {type}
          <button
            onClick={() => toggleType(type)}
            className="ml-1 rounded-sm hover:bg-muted"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
      {selectedAgents.map((agent) => (
        <Badge key={agent} variant="secondary" className="gap-1">
          {agent}
          <button
            onClick={() => toggleAgent(agent)}
            className="ml-1 rounded-sm hover:bg-muted"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
    </div>
  );
}
