/**
 * Root Layout - CSS Grid layout with top bar, sidebar, and main content
 */
import { useState, useEffect } from 'react';
import { TopBar } from './TopBar';
import { Sidebar, type TabId, TABS } from './Sidebar';
import { MainContent } from './MainContent';
import { Toaster } from '@/components/ui/sonner';

interface RootLayoutProps {
  isConnected: boolean;
  projectName?: string;
}

export function RootLayout({ isConnected, projectName }: RootLayoutProps) {
  const [activeTab, setActiveTab] = useState<TabId>('chat');

  // Keyboard shortcuts for tab navigation (Cmd/Ctrl + 1-6)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && !event.shiftKey && !event.altKey) {
        const key = event.key;
        const tabIndex = parseInt(key, 10) - 1;

        if (tabIndex >= 0 && tabIndex < TABS.length) {
          event.preventDefault();
          setActiveTab(TABS[tabIndex].id);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <div className="grid h-screen grid-cols-[auto_1fr] grid-rows-[auto_1fr]">
        {/* Top Bar - spans both columns */}
        <div className="col-span-2">
          <TopBar isConnected={isConnected} projectName={projectName} />
        </div>

        {/* Sidebar - left column */}
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Main Content - right column */}
        <MainContent activeTab={activeTab} />
      </div>
      <Toaster richColors closeButton position="top-right" />
    </>
  );
}
