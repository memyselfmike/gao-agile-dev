/**
 * Settings Icon - Button to open settings panel
 *
 * Story 39.28: Provider Selection Settings Panel
 */
import { Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SettingsIconProps {
  onClick: () => void;
}

export function SettingsIcon({ onClick }: SettingsIconProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onClick}
      aria-label="Open settings"
      className="h-9 w-9"
    >
      <Settings className="h-5 w-5" />
    </Button>
  );
}
