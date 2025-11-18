/**
 * Top Bar - Project name, search, session status, settings, theme toggle
 *
 * Epic 39.8: Simplified top bar - agent selection moved to Communication tab's DM list
 * Story 39.36: Search bar integration
 * Story 39.39: Layout settings integration
 */
import { SessionStatus } from '@/components/session/SessionStatus';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { SettingsIcon, SettingsPanel } from '@/components/settings';
import { SearchBar } from '@/components/search';
import { LayoutSettings } from '@/components/layout/LayoutSettings';
import { useState } from 'react';
import type { ResizableLayoutHandle } from '@/components/layout/ResizableLayout';

interface TopBarProps {
  isConnected: boolean;
  projectName?: string;
  /** Reference to ResizableLayout for preset application */
  layoutRef?: React.RefObject<ResizableLayoutHandle | null>;
}

export function TopBar({ isConnected, projectName = 'GAO-Dev', layoutRef }: TopBarProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleApplyPreset = (sizes: number[]) => {
    if (layoutRef?.current) {
      layoutRef.current.applyPreset(sizes);
    }
  };

  return (
    <>
      <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
        {/* Left Section: Project Name */}
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">{projectName}</h1>
        </div>

        {/* Center Section: Search Bar */}
        <div className="flex-1 mx-8 max-w-xl">
          <SearchBar />
        </div>

        {/* Right Section: Session Status, Layout, Settings, Theme */}
        <div className="flex items-center gap-3">
          {/* Session Status */}
          <SessionStatus isConnected={isConnected} />

          {/* Layout Settings */}
          {layoutRef && <LayoutSettings onApplyPreset={handleApplyPreset} />}

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
