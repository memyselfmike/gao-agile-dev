/**
 * FilterBar - Main filter controls container for git commits
 *
 * Features:
 * - Author filtering (all, agents, user, specific agents)
 * - Date range filtering (presets and custom)
 * - Message search with debouncing
 * - URL query parameter persistence
 * - Active filter count badge
 * - Clear all filters button
 */
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AuthorFilter } from './AuthorFilter';
import { DateRangeFilter } from './DateRangeFilter';
import { SearchInput } from './SearchInput';
import { FilterBadge } from './FilterBadge';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { GitTimelineFilters } from '@/types/git';

interface FilterBarProps {
  onFilterChange: (filters: GitTimelineFilters) => void;
}

export function FilterBar({ onFilterChange }: FilterBarProps) {
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialize filters from URL
  const [filters, setFilters] = useState<GitTimelineFilters>({
    author: searchParams.get('author') || undefined,
    since: searchParams.get('since') || undefined,
    until: searchParams.get('until') || undefined,
    search: searchParams.get('search') || undefined,
  });

  // Count active filters
  const activeFilterCount = [
    filters.author && filters.author !== 'all',
    filters.since,
    filters.until,
    filters.search,
  ].filter(Boolean).length;

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.author && filters.author !== 'all') {
      params.set('author', filters.author);
    }
    if (filters.since) {
      params.set('since', filters.since);
    }
    if (filters.until) {
      params.set('until', filters.until);
    }
    if (filters.search) {
      params.set('search', filters.search);
    }

    setSearchParams(params, { replace: true });
    onFilterChange(filters);
  }, [filters, onFilterChange, setSearchParams]);

  const handleClearFilters = () => {
    setFilters({
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
          onChange={(author) => setFilters({ ...filters, author: author === 'all' ? undefined : author })}
        />

        {/* Date Range Filter */}
        <DateRangeFilter
          since={filters.since}
          until={filters.until}
          onChange={(since, until) => setFilters({ ...filters, since, until })}
        />

        {/* Search Input */}
        <div className="flex-1 min-w-[200px]">
          <SearchInput
            value={filters.search || ''}
            onChange={(search) => setFilters({ ...filters, search: search || undefined })}
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
