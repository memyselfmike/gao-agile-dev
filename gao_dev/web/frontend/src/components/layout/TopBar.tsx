/**
 * Top Bar - Project name, session status, agent switcher, settings
 */
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SessionStatus } from '@/components/session/SessionStatus';
import { Settings, User, ChevronDown } from 'lucide-react';
import { useState } from 'react';

interface TopBarProps {
  isConnected: boolean;
  projectName?: string;
}

const AGENTS = [
  { id: 'brian', name: 'Brian', role: 'Workflow Coordinator' },
  { id: 'john', name: 'John', role: 'Product Manager' },
  { id: 'winston', name: 'Winston', role: 'Technical Architect' },
  { id: 'sally', name: 'Sally', role: 'UX Designer' },
  { id: 'bob', name: 'Bob', role: 'Scrum Master' },
  { id: 'amelia', name: 'Amelia', role: 'Software Developer' },
  { id: 'murat', name: 'Murat', role: 'Test Architect' },
  { id: 'mary', name: 'Mary', role: 'Business Analyst' },
];

export function TopBar({ isConnected, projectName = 'GAO-Dev' }: TopBarProps) {
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0]);

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
      {/* Project Name */}
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold text-foreground">{projectName}</h1>
      </div>

      {/* Right Section: Agent Switcher, Session Status, Settings */}
      <div className="flex items-center gap-3">
        {/* Agent Switcher */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">{selectedAgent.name}</span>
              <ChevronDown className="h-3 w-3 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel>Select Agent</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {AGENTS.map((agent) => (
              <DropdownMenuItem
                key={agent.id}
                onClick={() => setSelectedAgent(agent)}
                className="flex flex-col items-start"
              >
                <div className="font-medium">{agent.name}</div>
                <div className="text-xs text-muted-foreground">{agent.role}</div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Session Status */}
        <SessionStatus isConnected={isConnected} />

        {/* Settings */}
        <Button variant="ghost" size="icon" aria-label="Settings">
          <Settings className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
