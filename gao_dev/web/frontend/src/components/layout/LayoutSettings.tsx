/**
 * Layout Settings - Dropdown menu for layout preset selection
 *
 * Story 39.39: Layout Persistence & Presets
 * Epic 39.9: Customizable Layout & UX Polish
 *
 * Features:
 * - Layout preset dropdown (Default, Code-Focused, Chat-Focused)
 * - Current preset highlighted
 * - Reset to Default button
 * - Keyboard navigation
 * - Toast notifications
 */
import { Layout } from 'lucide-react';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { useLayoutStore } from '@/stores/layoutStore';
import {
  LAYOUT_PRESETS,
  PRESET_METADATA,
  type LayoutPresetName,
} from '@/lib/layout.constants';

interface LayoutSettingsProps {
  /** Callback to apply preset to ResizableLayout */
  onApplyPreset: (sizes: number[]) => void;
}

export function LayoutSettings({ onApplyPreset }: LayoutSettingsProps) {
  const { currentPreset, setPreset } = useLayoutStore();

  const handlePresetSelect = (presetName: string) => {
    if (presetName === 'custom') return; // Cannot manually select 'custom'

    const preset = presetName as LayoutPresetName;
    const sizes = [...LAYOUT_PRESETS[preset]]; // Clone to make mutable

    // Apply preset
    onApplyPreset(sizes);
    setPreset(preset);

    // Show toast notification
    const metadata = PRESET_METADATA[preset];
    toast.success(`Layout preset applied: ${metadata.label}`, {
      description: metadata.description,
      duration: 3000,
    });
  };

  const handleResetToDefault = () => {
    handlePresetSelect('default');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9"
          data-testid="layout-settings-trigger"
          aria-label="Layout settings"
        >
          <Layout className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>Layout Presets</DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DropdownMenuRadioGroup
          value={currentPreset}
          onValueChange={handlePresetSelect}
        >
          {Object.entries(PRESET_METADATA).map(([presetName, metadata]) => (
            <DropdownMenuRadioItem
              key={presetName}
              value={presetName}
              data-testid={`layout-preset-${presetName}`}
              className="cursor-pointer"
            >
              <div className="flex flex-col gap-1">
                <div className="font-medium">{metadata.label}</div>
                <div className="text-xs text-muted-foreground">
                  {metadata.description}
                </div>
              </div>
            </DropdownMenuRadioItem>
          ))}

          {/* Show 'Custom' if current preset is custom (not selectable) */}
          {currentPreset === 'custom' && (
            <DropdownMenuRadioItem
              value="custom"
              disabled
              data-testid="layout-preset-custom"
            >
              <div className="flex flex-col gap-1">
                <div className="font-medium">Custom</div>
                <div className="text-xs text-muted-foreground">
                  Manually adjusted layout
                </div>
              </div>
            </DropdownMenuRadioItem>
          )}
        </DropdownMenuRadioGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleResetToDefault}
          data-testid="layout-reset-default"
          className="cursor-pointer"
        >
          <span className="font-medium">Reset to Default</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
