/**
 * Layout Store - Manages layout state and preset selection
 *
 * Story 39.39: Layout Persistence & Presets
 * Epic 39.9: Customizable Layout & UX Polish
 */
import { create } from 'zustand';
import type { LayoutPresetName } from '@/lib/layout.constants';
import { detectPreset } from '@/lib/layout.constants';

interface LayoutState {
  /** Current active preset ('custom' if manually resized) */
  currentPreset: LayoutPresetName | 'custom';

  /** Set the current preset (used when applying preset) */
  setPreset: (preset: LayoutPresetName | 'custom') => void;

  /** Update preset based on current panel sizes (auto-detect) */
  updatePresetFromSizes: (sizes: number[]) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  currentPreset: 'default',

  setPreset: (preset) => set({ currentPreset: preset }),

  updatePresetFromSizes: (sizes) => {
    const detected = detectPreset(sizes);
    set({ currentPreset: detected });
  },
}));
