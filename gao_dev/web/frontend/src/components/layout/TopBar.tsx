/**
 * Top Bar - Project name, session status, agent switcher, theme toggle
 *
 * Story 39.8: Enhanced agent switcher with per-agent chat history and Cmd+K shortcut
 * Story 39.36: Search bar integration
 */
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SessionStatus } from '@/components/session/SessionStatus';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { SettingsIcon, SettingsPanel } from '@/components/settings';
import { SearchBar } from '@/components/search';
import { User, ChevronDown } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import type { Agent } from '@/types';

interface TopBarProps {
  isConnected: boolean;
  projectName?: string;
}

export function TopBar({ isConnected, projectName = 'GAO-Dev' }: TopBarProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const activeAgent = useChatStore((state) => state.activeAgent);
  const switchAgent = useChatStore((state) => state.switchAgent);

  // Load agents from backend
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
        const response = await fetch(`${apiUrl}/api/agents`);
        if (response.ok) {
          const data = (await response.json()) as { agents: Agent[] };
          setAgents(data.agents);

          // Set Brian as default if no active agent
          if (!activeAgent && data.agents.length > 0) {
            const brian = data.agents.find((a) => a.id === 'brian') || data.agents[0];
            switchAgent(brian);
          }
        }
      } catch (error) {
        console.error('Failed to load agents:', error);
      }
    };

    loadAgents();
  }, [activeAgent, switchAgent]);

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsMenuOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSelectAgent = (agent: Agent) => {
    switchAgent(agent);
    setIsMenuOpen(false);
  };

  const displayAgent = activeAgent || agents[0];

  return (
    <>
      <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
      {/* Left Section: Project Name + Agent Indicator */}
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">{projectName}</h1>
        {displayAgent && (
          <Badge variant="outline" className="gap-1 text-xs">
            <User className="h-3 w-3" />
            <span className="hidden sm:inline">Chatting with</span>
            <span className="font-medium">{displayAgent.name}</span>
          </Badge>
        )}
      </div>

      {/* Center Section: Search Bar */}
      <div className="flex-1 mx-8 max-w-xl">
        <SearchBar />
      </div>

      {/* Right Section: Agent Switcher, Session Status, Settings */}
      <div className="flex items-center gap-3">
        {/* Agent Switcher */}
        <DropdownMenu open={isMenuOpen} onOpenChange={setIsMenuOpen}>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">{displayAgent?.name || 'Select Agent'}</span>
              <ChevronDown className="h-3 w-3 opacity-50" />
              <kbd className="pointer-events-none ml-1 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:inline-flex">
                <span className="text-xs">⌘</span>K
              </kbd>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-72">
            <DropdownMenuLabel>Switch Agent (⌘K)</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {agents.map((agent) => (
              <DropdownMenuItem
                key={agent.id}
                onClick={() => handleSelectAgent(agent)}
                className="flex flex-col items-start gap-1 py-3"
              >
                <div className="flex w-full items-center justify-between">
                  <span className="font-medium">{agent.name}</span>
                  {agent.id === activeAgent?.id && (
                    <Badge variant="secondary" className="text-xs">
                      Active
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">{agent.role}</div>
                <div className="line-clamp-1 text-xs text-muted-foreground">{agent.description}</div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Session Status */}
        <SessionStatus isConnected={isConnected} />

        {/* Settings Icon */}
        <SettingsIcon onClick={() => setIsSettingsOpen(true)} />

        {/* Theme Toggle */}
        <ThemeToggle />
      </div>
    </header>

      {/* Settings Panel */}
      <SettingsPanel open={isSettingsOpen} onOpenChange={setIsSettingsOpen} />
    </>
  );
}
