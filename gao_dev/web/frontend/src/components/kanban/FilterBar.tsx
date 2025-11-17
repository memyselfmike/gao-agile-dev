/**
 * Filter Bar - Main filter controls for Kanban board
 *
 * Story 39.18: Kanban Filters and Search
 */
import { useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { SearchInput } from './SearchInput';
import { FilterDropdown } from './FilterDropdown';
import { FilterChips, type FilterChip } from './FilterChips';
import { useKanbanStore, type StoryCard, type EpicCard } from '@/stores/kanbanStore';

function useUrlFilters() {
  const { filters, setFilters } = useKanbanStore();

  // Sync filters to URL on change
  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.search) params.set('search', filters.search);
    if (filters.epicNums.length > 0) params.set('epic', filters.epicNums.join(','));
    if (filters.owners.length > 0) params.set('owner', filters.owners.join(','));
    if (filters.priorities.length > 0) params.set('priority', filters.priorities.join(','));

    const newUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
    window.history.replaceState({}, '', newUrl);
  }, [filters]);

  // Load filters from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    const search = params.get('search') || '';
    const epicNums = params.get('epic')
      ? params.get('epic')!.split(',').map(Number).filter((n) => !isNaN(n))
      : [];
    const owners = params.get('owner') ? params.get('owner')!.split(',') : [];
    const priorities = params.get('priority')
      ? params.get('priority')!.split(',')
      : [];

    if (search || epicNums.length > 0 || owners.length > 0 || priorities.length > 0) {
      setFilters({
        search,
        epicNums,
        owners,
        priorities,
      });
    }
  }, [setFilters]);
}

export function FilterBar() {
  const { columns, filters, setFilters } = useKanbanStore();

  // Sync URL state
  useUrlFilters();

  // Extract unique values for dropdowns
  const { epicOptions, ownerOptions, priorityOptions } = useMemo(() => {
    const allCards: (StoryCard | EpicCard)[] = (Object.values(columns) as (StoryCard | EpicCard)[][]).flat();

    // Epic numbers
    const epicNums = new Set<number>();
    allCards.forEach((card: StoryCard | EpicCard) => {
      if (card.type === 'epic') {
        epicNums.add(parseInt(card.number));
      } else if (card.type === 'story') {
        epicNums.add((card as StoryCard).epicNumber);
      }
    });

    // Owners (from stories only)
    const owners = new Set<string>();
    allCards.forEach((card: StoryCard | EpicCard) => {
      if (card.type === 'story' && (card as StoryCard).owner) {
        owners.add((card as StoryCard).owner!);
      }
    });

    // Priorities (from stories only)
    const priorities = new Set<string>();
    allCards.forEach((card: StoryCard | EpicCard) => {
      if (card.type === 'story') {
        priorities.add((card as StoryCard).priority);
      }
    });

    return {
      epicOptions: Array.from(epicNums)
        .sort((a: number, b: number) => a - b)
        .map((num: number) => ({ value: num, label: `Epic ${num}` })),
      ownerOptions: Array.from(owners)
        .sort()
        .map((owner: string) => ({ value: owner, label: owner })),
      priorityOptions: ['P0', 'P1', 'P2', 'P3'].map((p: string) => ({ value: p, label: p })),
    };
  }, [columns]);

  // Build filter chips
  const filterChips = useMemo((): FilterChip[] => {
    const chips: FilterChip[] = [];

    if (filters.search) {
      chips.push({
        type: 'search',
        label: `Search: "${filters.search}"`,
        value: filters.search,
      });
    }

    filters.epicNums.forEach((num) => {
      chips.push({
        type: 'epic',
        label: `Epic ${num}`,
        value: num,
      });
    });

    filters.owners.forEach((owner) => {
      chips.push({
        type: 'owner',
        label: owner,
        value: owner,
      });
    });

    filters.priorities.forEach((priority) => {
      chips.push({
        type: 'priority',
        label: priority,
        value: priority,
      });
    });

    return chips;
  }, [filters]);

  const hasActiveFilters =
    filters.search ||
    filters.epicNums.length > 0 ||
    filters.owners.length > 0 ||
    filters.priorities.length > 0;

  const handleClearAll = () => {
    setFilters({
      search: '',
      epicNums: [],
      owners: [],
      priorities: [],
    });
  };

  const handleRemoveChip = (type: FilterChip['type'], value: string | number) => {
    switch (type) {
      case 'search':
        setFilters({ ...filters, search: '' });
        break;
      case 'epic':
        setFilters({
          ...filters,
          epicNums: filters.epicNums.filter((n) => n !== value),
        });
        break;
      case 'owner':
        setFilters({
          ...filters,
          owners: filters.owners.filter((o) => o !== value),
        });
        break;
      case 'priority':
        setFilters({
          ...filters,
          priorities: filters.priorities.filter((p) => p !== value),
        });
        break;
    }
  };

  return (
    <div className="space-y-3 border-b bg-background p-4">
      {/* Filter controls */}
      <div className="flex flex-wrap gap-2">
        <SearchInput
          value={filters.search}
          onChange={(value) => setFilters({ ...filters, search: value })}
        />

        <FilterDropdown
          label="Epic"
          options={epicOptions}
          selectedValues={filters.epicNums as (string | number)[]}
          onChange={(values: (string | number)[]) =>
            setFilters({ ...filters, epicNums: values as number[] })
          }
          testId="epic-filter-dropdown"
        />

        <FilterDropdown
          label="Owner"
          options={ownerOptions}
          selectedValues={filters.owners as (string | number)[]}
          onChange={(values: (string | number)[]) =>
            setFilters({ ...filters, owners: values as string[] })
          }
          testId="owner-filter-dropdown"
        />

        <FilterDropdown
          label="Priority"
          options={priorityOptions}
          selectedValues={filters.priorities as (string | number)[]}
          onChange={(values: (string | number)[]) =>
            setFilters({ ...filters, priorities: values as string[] })
          }
          testId="priority-filter-dropdown"
        />

        {hasActiveFilters && (
          <Button
            variant="ghost"
            onClick={handleClearAll}
            className="ml-auto"
            data-testid="clear-all-filters-button"
          >
            <X className="mr-2 h-4 w-4" />
            Clear All
          </Button>
        )}
      </div>

      {/* Active filter chips */}
      {filterChips.length > 0 && (
        <FilterChips chips={filterChips} onRemove={handleRemoveChip} />
      )}
    </div>
  );
}
