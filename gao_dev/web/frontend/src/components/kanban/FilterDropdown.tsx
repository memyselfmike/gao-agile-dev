/**
 * Filter Dropdown - Multi-select dropdown for filtering
 *
 * Story 39.18: Kanban Filters and Search
 */
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FilterOption {
  value: string | number;
  label: string;
}

interface FilterDropdownProps {
  label: string;
  options: FilterOption[];
  selectedValues: (string | number)[];
  onChange: (values: (string | number)[]) => void;
  testId?: string;
}

export function FilterDropdown({
  label,
  options,
  selectedValues,
  onChange,
  testId,
}: FilterDropdownProps) {
  const hasSelection = selectedValues.length > 0;

  const handleToggle = (value: string | number) => {
    const newValues = selectedValues.includes(value)
      ? selectedValues.filter((v) => v !== value)
      : [...selectedValues, value];
    onChange(newValues);
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const handleSelectAll = () => {
    onChange(options.map((opt) => opt.value));
  };

  const getButtonLabel = () => {
    if (selectedValues.length === 0) {
      return `All ${label}s`;
    }
    if (selectedValues.length === 1) {
      const selected = options.find((opt) => opt.value === selectedValues[0]);
      return selected?.label || `${selectedValues.length} selected`;
    }
    return `${selectedValues.length} ${label}s`;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className={cn('justify-between', hasSelection && 'border-primary')}
          data-testid={testId}
          aria-label={`Filter by ${label.toLowerCase()}`}
        >
          {getButtonLabel()}
          <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {/* Select/Clear All */}
        <div className="flex gap-2 px-2 py-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 flex-1 text-xs"
            onClick={handleSelectAll}
          >
            Select All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 flex-1 text-xs"
            onClick={handleClearAll}
            disabled={!hasSelection}
          >
            Clear All
          </Button>
        </div>
        <DropdownMenuSeparator />

        {/* Options */}
        {options.map((option) => {
          const isSelected = selectedValues.includes(option.value);
          return (
            <DropdownMenuCheckboxItem
              key={String(option.value)}
              checked={isSelected}
              onCheckedChange={() => handleToggle(option.value)}
              data-testid={`filter-option-${option.value}`}
            >
              <span className="flex-1">{option.label}</span>
              {isSelected && <Check className="ml-2 h-4 w-4" />}
            </DropdownMenuCheckboxItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
