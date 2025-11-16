/**
 * Time Window Selector - Select time range for activity stream
 *
 * Story 39.9: Real-time activity stream
 */
import { Button } from '@/components/ui/button';
import { Clock } from 'lucide-react';

export type TimeWindow = '1h' | '6h' | '24h' | '7d' | '30d' | 'all';

interface TimeWindowSelectorProps {
  selected: TimeWindow;
  onChange: (window: TimeWindow) => void;
}

const TIME_WINDOWS: { value: TimeWindow; label: string }[] = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: 'all', label: 'All Time' },
];

export function TimeWindowSelector({ selected, onChange }: TimeWindowSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <Clock className="h-4 w-4 text-muted-foreground" />
      <div className="flex gap-1">
        {TIME_WINDOWS.map((window) => (
          <Button
            key={window.value}
            variant={selected === window.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => onChange(window.value)}
            className="h-7 text-xs"
          >
            {window.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
