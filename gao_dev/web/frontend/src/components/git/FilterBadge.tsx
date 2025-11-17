/**
 * FilterBadge - Badge showing active filter count
 *
 * Displays the number of active filters applied to the commit list
 */
import { Badge } from '@/components/ui/badge';
import { Filter } from 'lucide-react';

interface FilterBadgeProps {
  count: number;
}

export function FilterBadge({ count }: FilterBadgeProps) {
  return (
    <Badge variant="secondary" className="gap-1.5">
      <Filter className="h-3 w-3" />
      <span>{count} {count === 1 ? 'filter' : 'filters'}</span>
    </Badge>
  );
}
