/**
 * DateRangeFilter - Date range picker with presets
 *
 * Features:
 * - Preset options (Last 7/30/90 days)
 * - Custom date range picker
 * - Date validation (start must be before end)
 * - ISO 8601 date formatting
 */
import { useState } from 'react';
import { format, subDays } from 'date-fns';
import { Calendar } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface DateRangeFilterProps {
  since?: string;
  until?: string;
  onChange: (since?: string, until?: string) => void;
}

export function DateRangeFilter({ since, until, onChange }: DateRangeFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customSince, setCustomSince] = useState('');
  const [customUntil, setCustomUntil] = useState('');
  const [validationError, setValidationError] = useState('');

  const presets = [
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
  ];

  const handlePresetClick = (days: number) => {
    const sinceDate = format(subDays(new Date(), days), 'yyyy-MM-dd');
    onChange(sinceDate, undefined);
    setIsOpen(false);
  };

  const handleCustomApply = () => {
    setValidationError('');

    // Validate dates
    if (customSince && customUntil) {
      const sinceDate = new Date(customSince);
      const untilDate = new Date(customUntil);

      if (sinceDate > untilDate) {
        setValidationError('Start date must be before end date');
        return;
      }
    }

    onChange(customSince || undefined, customUntil || undefined);
    setIsOpen(false);
  };

  const handleClearDates = () => {
    setCustomSince('');
    setCustomUntil('');
    setValidationError('');
    onChange(undefined, undefined);
    setIsOpen(false);
  };

  // Format display text
  const getDisplayText = () => {
    if (since && !until) {
      return `Since ${since}`;
    }
    if (since && until) {
      return `${since} to ${until}`;
    }
    if (!since && until) {
      return `Until ${until}`;
    }
    return 'Date Range';
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" className="w-[200px] justify-start gap-2">
          <Calendar className="h-4 w-4" />
          <span className="truncate">{getDisplayText()}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-4" align="start">
        <div className="space-y-4">
          {/* Presets */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Quick Presets</Label>
            <div className="grid gap-2">
              {presets.map((preset) => (
                <Button
                  key={preset.label}
                  variant="ghost"
                  size="sm"
                  onClick={() => handlePresetClick(preset.days)}
                  className="justify-start"
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Custom Range */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Custom Range</Label>
            <div className="space-y-2">
              <div>
                <Label htmlFor="since-date" className="text-xs text-muted-foreground">
                  From
                </Label>
                <Input
                  id="since-date"
                  type="date"
                  value={customSince}
                  onChange={(e) => setCustomSince(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="until-date" className="text-xs text-muted-foreground">
                  To
                </Label>
                <Input
                  id="until-date"
                  type="date"
                  value={customUntil}
                  onChange={(e) => setCustomUntil(e.target.value)}
                />
              </div>

              {validationError && (
                <Alert variant="destructive">
                  <AlertDescription className="text-xs">
                    {validationError}
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex gap-2 pt-2">
                <Button
                  size="sm"
                  onClick={handleCustomApply}
                  className="flex-1"
                  disabled={!customSince && !customUntil}
                >
                  Apply
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleClearDates}
                  className="flex-1"
                >
                  Clear
                </Button>
              </div>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
