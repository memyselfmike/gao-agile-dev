/**
 * Layout Constants - Preset definitions for panel layouts
 *
 * Story 39.39: Layout Persistence & Presets
 * Epic 39.9: Customizable Layout & UX Polish
 */

/**
 * Layout preset definitions
 * Each preset defines panel size percentages: [left%, main%]
 * Note: Currently using 2-panel layout (DualSidebar + MainContent)
 * Future: May add right sidebar for additional content (3-panel layout)
 */
export const LAYOUT_PRESETS = {
  default: [25, 75],      // Balanced: 25% DualSidebar, 75% main content
  'code-focused': [20, 80], // Narrow sidebar: 20% DualSidebar, 80% main content
  'chat-focused': [30, 70], // Wide sidebar: 30% DualSidebar, 70% main content
} as const;

export type LayoutPresetName = keyof typeof LAYOUT_PRESETS;

/**
 * Check if current layout matches a preset (within tolerance)
 */
export function detectPreset(
  sizes: number[],
  tolerance: number = 2
): LayoutPresetName | 'custom' {
  const [left, main] = sizes;

  // Check each preset
  for (const [name, preset] of Object.entries(LAYOUT_PRESETS)) {
    const [presetLeft, presetMain] = preset;

    // Compare within tolerance
    const leftMatch = Math.abs(left - presetLeft) <= tolerance;
    const mainMatch = Math.abs(main - presetMain) <= tolerance;

    if (leftMatch && mainMatch) {
      return name as LayoutPresetName;
    }
  }

  return 'custom';
}

/**
 * Preset metadata for UI display
 */
export const PRESET_METADATA: Record<
  LayoutPresetName,
  {
    label: string;
    description: string;
    icon?: string;
  }
> = {
  default: {
    label: 'Default',
    description: 'Balanced layout (25% | 75%)',
  },
  'code-focused': {
    label: 'Code-Focused',
    description: 'Wide main content (20% | 80%)',
  },
  'chat-focused': {
    label: 'Chat-Focused',
    description: 'Wide sidebar (30% | 70%)',
  },
};
