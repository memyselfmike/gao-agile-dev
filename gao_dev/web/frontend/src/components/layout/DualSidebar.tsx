/**
 * Dual Sidebar - Wrapper for Primary + Secondary sidebars
 *
 * Story 39.30: Dual Sidebar Navigation (Primary + Secondary)
 */
import { useNavigationStore } from '@/stores/navigationStore';
import { PrimarySidebar } from './PrimarySidebar';
import { SecondarySidebar } from './SecondarySidebar';

export function DualSidebar() {
  const { primaryView, isSecondarySidebarOpen, setPrimaryView } = useNavigationStore();

  return (
    <>
      <PrimarySidebar activeView={primaryView} onViewChange={setPrimaryView} />
      <SecondarySidebar primaryView={primaryView} isOpen={isSecondarySidebarOpen} />
    </>
  );
}
