# Story 39.18: Kanban Filters and Search

**Epic**: 39.5 - Kanban Board (Visual Project Management)
**Story Points**: 3
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING
**Commits**: N/A

---

## Description

As a **product manager**, I want to **filter and search the Kanban board** so that **I can focus on specific epics, owners, or priorities without visual clutter**.

## Acceptance Criteria

1. **AC1**: Search input filters cards by epic title or story title (case-insensitive, partial match)
2. **AC2**: Epic filter dropdown shows all epic numbers (e.g., "Epic 39", "Epic 40"), selecting filters to that epic only
3. **AC3**: Owner filter dropdown shows all unique owners, selecting filters to that owner's stories
4. **AC4**: Priority filter dropdown shows P0-P3 options, selecting filters to that priority level
5. **AC5**: Active filters display as removable chips below filter controls (e.g., "Epic 39 ×", "P0 ×")
6. **AC6**: "Clear all filters" button resets board to show all cards
7. **AC7**: Filters combine using AND logic (e.g., "Epic 39 AND P0" shows only P0 stories in Epic 39)
8. **AC8**: Search highlights matched text in card titles (yellow background)
9. **AC9**: Filter state persists in URL query parameters (e.g., `?epic=39&priority=0&search=auth`)
10. **AC10**: Filtering happens client-side (no backend API call) for instant results
11. **AC11**: Filter controls are keyboard accessible (Tab, Enter, Escape)
12. **AC12**: Empty filter results show "No cards match your filters. [Clear filters]" message

## Technical Notes

### UI Design

**Filter Bar Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ 🔍 Search...  │ Epic ▼  │ Owner ▼  │ Priority ▼  │ Clear  │
├────────────────────────────────────────────────────────────┤
│ [Epic 39 ×]  [P0 ×]  [Search: auth ×]                    │
└────────────────────────────────────────────────────────────┘
```

**Component Structure**:
- **FilterBar.tsx**: Container component
- **SearchInput.tsx**: Debounced search input
- **FilterDropdown.tsx**: Reusable dropdown component
- **FilterChip.tsx**: Removable filter chip
- **ClearFiltersButton.tsx**: Reset button

### Frontend Implementation

**1. FilterBar Component**

```typescript
interface FilterState {
  search: string;
  epicNum: number | null;
  owner: string | null;
  priority: number | null;
}

function FilterBar() {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    epicNum: null,
    owner: null,
    priority: null
  });

  const { columns } = useKanbanStore();
  const epics = getUniqueEpics(columns);
  const owners = getUniqueOwners(columns);

  return (
    <div className="filter-bar">
      <SearchInput
        value={filters.search}
        onChange={(value) => setFilters({ ...filters, search: value })}
        placeholder="Search epics and stories..."
      />

      <FilterDropdown
        label="Epic"
        options={epics.map(e => ({ value: e, label: `Epic ${e}` }))}
        value={filters.epicNum}
        onChange={(value) => setFilters({ ...filters, epicNum: value })}
      />

      <FilterDropdown
        label="Owner"
        options={owners.map(o => ({ value: o, label: o }))}
        value={filters.owner}
        onChange={(value) => setFilters({ ...filters, owner: value })}
      />

      <FilterDropdown
        label="Priority"
        options={[
          { value: 0, label: 'P0 (Critical)' },
          { value: 1, label: 'P1 (High)' },
          { value: 2, label: 'P2 (Medium)' },
          { value: 3, label: 'P3 (Low)' }
        ]}
        value={filters.priority}
        onChange={(value) => setFilters({ ...filters, priority: value })}
      />

      <Button onClick={() => setFilters({ search: '', epicNum: null, owner: null, priority: null })}>
        Clear Filters
      </Button>
    </div>
  );
}
```

**2. Search Input with Debouncing**

```typescript
function SearchInput({ value, onChange, placeholder }: Props) {
  const [localValue, setLocalValue] = useState(value);

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue);
    }, 300);

    return () => clearTimeout(timer);
  }, [localValue]);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
      <Input
        type="search"
        placeholder={placeholder}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        className="pl-10"
        data-testid="kanban-search-input"
      />
    </div>
  );
}
```

**3. Filter Chips**

```typescript
function FilterChips({ filters, onRemove }: Props) {
  const chips = [];

  if (filters.epicNum) {
    chips.push({ type: 'epic', label: `Epic ${filters.epicNum}`, value: filters.epicNum });
  }
  if (filters.owner) {
    chips.push({ type: 'owner', label: filters.owner, value: filters.owner });
  }
  if (filters.priority !== null) {
    chips.push({ type: 'priority', label: `P${filters.priority}`, value: filters.priority });
  }
  if (filters.search) {
    chips.push({ type: 'search', label: `Search: ${filters.search}`, value: filters.search });
  }

  if (chips.length === 0) return null;

  return (
    <div className="flex gap-2 flex-wrap">
      {chips.map(chip => (
        <Badge
          key={chip.type}
          variant="secondary"
          className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
          onClick={() => onRemove(chip.type)}
        >
          {chip.label}
          <X className="ml-1 h-3 w-3" />
        </Badge>
      ))}
    </div>
  );
}
```

**4. Filtering Logic**

**Zustand Store Update**:
```typescript
const useKanbanStore = create<KanbanState>((set, get) => ({
  // ... existing state
  filters: {
    search: '',
    epicNum: null,
    owner: null,
    priority: null
  },

  setFilters: (filters: FilterState) => set({ filters }),

  getFilteredCards: (status: string) => {
    const { columns, filters } = get();
    let cards = columns[status];

    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      cards = cards.filter(card =>
        card.title.toLowerCase().includes(searchLower)
      );
    }

    // Apply epic filter
    if (filters.epicNum) {
      cards = cards.filter(card =>
        card.type === 'epic' ? card.epicNum === filters.epicNum :
        card.type === 'story' ? card.epicNum === filters.epicNum :
        false
      );
    }

    // Apply owner filter
    if (filters.owner) {
      cards = cards.filter(card =>
        card.type === 'story' && card.owner === filters.owner
      );
    }

    // Apply priority filter
    if (filters.priority !== null) {
      cards = cards.filter(card =>
        card.type === 'story' && card.priority === filters.priority
      );
    }

    return cards;
  }
}));
```

**5. URL State Sync**

**Use React Router (or custom hook)**:
```typescript
function useUrlFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters: FilterState = {
    search: searchParams.get('search') || '',
    epicNum: searchParams.get('epic') ? parseInt(searchParams.get('epic')!) : null,
    owner: searchParams.get('owner') || null,
    priority: searchParams.get('priority') ? parseInt(searchParams.get('priority')!) : null
  };

  const setFilters = (newFilters: FilterState) => {
    const params = new URLSearchParams();
    if (newFilters.search) params.set('search', newFilters.search);
    if (newFilters.epicNum) params.set('epic', newFilters.epicNum.toString());
    if (newFilters.owner) params.set('owner', newFilters.owner);
    if (newFilters.priority !== null) params.set('priority', newFilters.priority.toString());
    setSearchParams(params);
  };

  return { filters, setFilters };
}
```

**6. Search Highlighting**

```typescript
function highlightText(text: string, search: string) {
  if (!search) return text;

  const parts = text.split(new RegExp(`(${search})`, 'gi'));
  return (
    <span>
      {parts.map((part, i) =>
        part.toLowerCase() === search.toLowerCase() ? (
          <mark key={i} className="bg-yellow-200 dark:bg-yellow-800">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </span>
  );
}

// Usage in StoryCard
<h3>{highlightText(story.title, filters.search)}</h3>
```

**7. Empty State**

```typescript
function EmptyFilterResults({ onClearFilters }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <FilterX className="h-12 w-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">No cards match your filters</h3>
      <p className="text-muted-foreground mb-4">
        Try adjusting your search or filter criteria
      </p>
      <Button onClick={onClearFilters}>
        <X className="mr-2 h-4 w-4" />
        Clear all filters
      </Button>
    </div>
  );
}
```

### Performance Optimization

**Memoization**:
```typescript
const filteredCards = useMemo(() => {
  return getFilteredCards(status);
}, [status, filters, columns]);
```

**Debounced Search**:
- 300ms delay before applying search filter
- Prevents excessive re-renders during typing

**Virtual Scrolling**:
- Already implemented in Story 39.19
- Handles filtered lists efficiently

### Accessibility

**Keyboard Navigation**:
- Tab to move between filter controls
- Enter to open dropdown
- Arrow keys to navigate dropdown options
- Escape to close dropdown
- Space to select option

**ARIA Labels**:
```tsx
<Input
  aria-label="Search epics and stories"
  placeholder="Search..."
/>

<Select
  aria-label="Filter by epic number"
  data-testid="epic-filter-dropdown"
>
  {/* options */}
</Select>
```

**Screen Reader**:
- Announce filter count: "39 cards shown (filtered from 100)"
- Announce filter changes: "Applied filter: Epic 39"
- Announce clear action: "Filters cleared. Showing all 100 cards."

### Testing Strategy

**Unit Tests**:
1. Search filters cards by title (case-insensitive)
2. Epic filter shows only selected epic's cards
3. Owner filter shows only selected owner's stories
4. Priority filter shows only selected priority stories
5. Multiple filters combine with AND logic
6. Clear filters resets to show all cards
7. Empty filter results show empty state
8. Search highlighting works correctly

**Integration Tests**:
1. URL state sync (filters persist on page reload)
2. Filter state persists across tab switches

**E2E Tests** (Playwright):
1. Type in search box, verify cards filtered
2. Select epic from dropdown, verify filter applied
3. Select owner from dropdown, verify filter applied
4. Select priority from dropdown, verify filter applied
5. Remove filter chip, verify filter removed
6. Click "Clear filters", verify all filters removed
7. Verify URL updates with filter parameters
8. Reload page, verify filters restored from URL
9. Verify empty state when no cards match
10. Verify keyboard navigation works

## Dependencies

- Story 39.15: Kanban Board Layout (foundation)
- Story 39.16: Epic and Story Card Components (items to filter)
- React Router (or similar) for URL state management
- shadcn/ui: Input, Select, Badge components

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] FilterBar component implemented with search and 3 dropdowns
- [ ] Filter chips display active filters
- [ ] Clear filters button functional
- [ ] Filtering logic combines filters with AND
- [ ] Search highlighting implemented
- [ ] URL state sync working
- [ ] Client-side filtering (instant results)
- [ ] Empty state shows when no matches
- [ ] Keyboard accessibility verified
- [ ] ARIA labels on all filter controls
- [ ] 8+ unit tests passing
- [ ] 10+ E2E tests passing
- [ ] Debounced search (300ms)
- [ ] Performance: Filter 1,000 cards in <50ms
- [ ] Code reviewed and approved
- [ ] Zero regressions

---

**Priority**: Medium
**Complexity**: Medium (state management, URL sync)
**Risk**: Low
**User Impact**: High (improves usability significantly)
