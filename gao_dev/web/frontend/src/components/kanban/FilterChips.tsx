/**
 * Filter Chips - Display active filters as removable chips
 *
 * Story 39.18: Kanban Filters and Search
 */
import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export interface FilterChip {
  type: 'search' | 'epic' | 'owner' | 'priority';
  label: string;
  value: string | number;
}

interface FilterChipsProps {
  chips: FilterChip[];
  onRemove: (type: FilterChip['type'], value: string | number) => void;
}

export function FilterChips({ chips, onRemove }: FilterChipsProps) {
  if (chips.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2" data-testid="filter-chips">
      {chips.map((chip) => (
        <Badge
          key={`${chip.type}-${chip.value}`}
          variant="secondary"
          className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground transition-colors pr-1"
          onClick={() => onRemove(chip.type, chip.value)}
          data-testid={`filter-chip-${chip.type}-${chip.value}`}
        >
          <span className="mr-1">{chip.label}</span>
          <X className="h-3 w-3" aria-label={`Remove ${chip.label} filter`} />
        </Badge>
      ))}
    </div>
  );
}
