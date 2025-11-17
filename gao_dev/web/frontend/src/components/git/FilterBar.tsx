/**
 * FilterBar - Main filter controls container for git commits
 *
 * Features:
 * - Author filtering (all, agents, user, specific agents)
 * - Date range filtering (presets and custom)
 * - Message search with debouncing
 * - Controlled component (receives filters as prop)
 * - Active filter count badge
 * - Clear all filters button
 */
import { AuthorFilter } from './AuthorFilter';
import { DateRangeFilter } from './DateRangeFilter';
import { SearchInput } from './SearchInput';
import { FilterBadge } from './FilterBadge';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { GitTimelineFilters } from '@/types/git';

interface FilterBarProps {
  filters: GitTimelineFilters;
  onFilterChange: (filters: GitTimelineFilters) => void;
}

export function FilterBar({ filters, onFilterChange }: FilterBarProps) {
  // Count active filters
  const activeFilterCount = [
    filters.author && filters.author !== 'all',
    filters.since,
    filters.until,
    filters.search,
  ].filter(Boolean).length;

  const handleClearFilters = () => {
    onFilterChange({
      author: undefined,
      since: undefined,
      until: undefined,
      search: undefined,
    });
  };

  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        {/* Author Filter */}
        <AuthorFilter
          value={filters.author || 'all'}
          onChange={(author) => {
            onFilterChange({ ...filters, author: author === 'all' ? undefined : author });
          }}
        />

        {/* Date Range Filter */}
        <DateRangeFilter
          since={filters.since}
          until={filters.until}
          onChange={(since, until) => {
            onFilterChange({ ...filters, since, until });
          }}
        />

        {/* Search Input */}
        <div className="flex-1 min-w-[200px]">
          <SearchInput
            value={filters.search || ''}
            onChange={(search) => {
              onFilterChange({ ...filters, search: search || undefined });
            }}
          />
        </div>

        {/* Filter Badge and Clear Button */}
        {activeFilterCount > 0 && (
          <>
            <FilterBadge count={activeFilterCount} />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearFilters}
              className="gap-2"
            >
              <X className="h-4 w-4" />
              Clear filters
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
