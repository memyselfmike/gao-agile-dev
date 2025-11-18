/**
 * Navigation Store - Manages dual sidebar navigation state
 *
 * Story 39.30: Dual Sidebar Navigation (Primary + Secondary)
 */
import { create } from 'zustand';

export type PrimaryView = 'home' | 'dms' | 'channels' | 'settings';

interface NavigationState {
  primaryView: PrimaryView;
  isSecondarySidebarOpen: boolean;
  setPrimaryView: (view: PrimaryView) => void;
  toggleSecondarySidebar: () => void;
  setSecondarySidebarOpen: (open: boolean) => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  primaryView: 'dms',
  isSecondarySidebarOpen: true,

  setPrimaryView: (view) => set({ primaryView: view }),

  toggleSecondarySidebar: () =>
    set((state) => ({ isSecondarySidebarOpen: !state.isSecondarySidebarOpen })),

  setSecondarySidebarOpen: (open) => set({ isSecondarySidebarOpen: open }),
}));
