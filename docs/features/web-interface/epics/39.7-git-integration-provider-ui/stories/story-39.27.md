# Story 39.27: Git Filters and Search

**Story Number**: 39.27
**Epic**: 39.7 - Git Integration & Provider UI
**Feature**: Web Interface
**Status**: Planned
**Priority**: SHOULD HAVE (P1 - V1.1)
**Effort Estimate**: M (Medium - 3 story points)
**Dependencies**: Story 39.25 (Git Timeline Commit History)

---

## User Story

As a **product owner**
I want **to filter and search commits by author, date range, and message**
So that **I can quickly find specific changes without scrolling through entire history**

---

## Acceptance Criteria

### Filter Controls
- [ ] AC1: Filter bar displayed at top of Git Timeline with three sections:
  - Author dropdown
  - Date range picker
  - Search input
- [ ] AC2: Author dropdown options:
  - "All" (default)
  - "Agents only" (all GAO-Dev agents)
  - "User only" (non-agent commits)
  - Individual agent names (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary)
  - Git usernames (for user commits)
- [ ] AC3: Date range picker with presets:
  - "Last 7 days"
  - "Last 30 days"
  - "Last 90 days"
  - "Custom range" (date picker opens)
- [ ] AC4: Search input with placeholder: "Search commit messages..."

### Real-Time Filtering
- [ ] AC5: Filters apply immediately (<50ms) as user changes selections
- [ ] AC6: Multiple filters combine with AND logic (all must match)
- [ ] AC7: Search highlights matching text in commit messages (yellow background)
- [ ] AC8: Filter results update commit count: "Showing X of Y commits"

### Filter State Management
- [ ] AC9: "Clear all filters" button visible when any filter active
- [ ] AC10: Filter state persists in URL query parameters:
  - `?author=amelia&since=2025-01-01&search=bug`
  - Shareable URL recreates exact filter state
- [ ] AC11: Filter count badge on filter bar shows number of active filters

### Empty States & Edge Cases
- [ ] AC12: Empty results state: "No commits match filters. Try adjusting your criteria."
- [ ] AC13: Clear filters button in empty state
- [ ] AC14: Search debounced (300ms) to avoid excessive filtering during typing
- [ ] AC15: Invalid date ranges show validation error: "Start date must be before end date"

---

## Technical Context

### Architecture Integration

**Integration with Story 39.25 (Git Timeline)**:
- Reuse commit list component
- Apply filters to commit query
- Maintain pagination with filtered results

**API Endpoints** (Backend - Story 39.27):
```
GET /api/git/commits?author=<author>&since=<date>&until=<date>&search=<query>&limit=50&offset=0
Response: {
  commits: [...],
  total: 42,          // Total commits matching filters
  total_unfiltered: 1234,  // Total commits without filters
  has_more: false,
  filters_applied: {
    author: "amelia",
    since: "2025-01-01T00:00:00Z",
    search: "bug"
  }
}
```

**Frontend Components** (Story 39.27):
```
src/components/git/
├── FilterBar.tsx            # Main filter controls container
├── AuthorFilter.tsx         # Author dropdown
├── DateRangeFilter.tsx      # Date range picker
├── SearchInput.tsx          # Commit message search
├── FilterBadge.tsx          # Active filter count badge
└── ClearFiltersButton.tsx   # Clear all filters
```

### Dependencies

**Story 39.25 (Git Timeline Commit History)**:
- Commit list rendering
- Pagination logic
- WebSocket updates

**Epic 27 (GitIntegratedStateManager)**:
- `GitManager.get_commit_history()` with filter parameters
- Efficient git log filtering

---

## Test Scenarios

### Test 1: Author Filter - Agents Only
**Given**: Repository with 100 commits (60 from agents, 40 from users)
**When**: User selects "Agents only" in author dropdown
**Then**:
- Commit list updates to show 60 commits
- Filter count badge shows "1"
- URL updates to `?author=agents`
- Counter shows "Showing 60 of 100 commits"

### Test 2: Author Filter - Specific Agent
**Given**: Repository with commits from Brian (20), John (15), Amelia (30)
**When**: User selects "Amelia" in author dropdown
**Then**:
- Commit list shows 30 commits authored by Amelia
- All commits have blue robot badge with "Amelia"
- Filter count badge shows "1"
- URL updates to `?author=amelia`

### Test 3: Date Range Filter - Last 7 Days
**Given**: Repository with commits spanning 6 months
**When**: User selects "Last 7 days" in date range picker
**Then**:
- Commit list shows only commits from last 7 days
- Filter count badge shows "1"
- URL updates to `?since=<7_days_ago_ISO>`
- Counter shows "Showing X of Y commits"

### Test 4: Custom Date Range
**Given**: User wants commits from January 2025
**When**: User selects "Custom range", enters 2025-01-01 to 2025-01-31
**Then**:
- Commit list shows commits from January 2025 only
- Filter count badge shows "1"
- URL updates to `?since=2025-01-01&until=2025-01-31`
- Date range picker shows custom dates

### Test 5: Search Commit Messages
**Given**: Repository with 100 commits
**When**: User types "bug fix" in search input
**Then**:
- Search debounces 300ms
- Commit list shows commits with "bug fix" in message
- Matching text highlighted in yellow
- Filter count badge shows "1"
- URL updates to `?search=bug+fix`

### Test 6: Combined Filters
**Given**: Repository with diverse commits
**When**: User applies:
  - Author: "Amelia"
  - Date range: "Last 30 days"
  - Search: "story"
**Then**:
- Commit list shows Amelia's commits from last 30 days with "story" in message
- Filter count badge shows "3"
- URL: `?author=amelia&since=<30_days_ago>&search=story`
- Counter: "Showing X of Y commits"

### Test 7: No Matching Results
**Given**: User applies filters that match no commits
**When**: No commits match criteria
**Then**:
- Empty state: "No commits match filters. Try adjusting your criteria."
- Clear filters button visible
- Commit count: "Showing 0 of Y commits"
- Filters remain active (user can adjust)

### Test 8: Clear All Filters
**Given**: User has 3 active filters applied
**When**: User clicks "Clear all filters" button
**Then**:
- All filters reset to default (All, no date range, empty search)
- Commit list shows all commits
- Filter count badge disappears
- URL updates to `/git` (no query params)
- Counter: "Showing 50 of Y commits" (first page)

### Test 9: URL Query Parameters Persistence
**Given**: User applies filters and shares URL
**When**: User (or another user) opens URL: `?author=amelia&search=epic`
**Then**:
- Author dropdown shows "Amelia" selected
- Search input shows "epic"
- Commit list filtered correctly
- Filter count badge shows "2"

### Test 10: Invalid Date Range
**Given**: User opens custom date range picker
**When**: User enters start date after end date (e.g., 2025-02-01 to 2025-01-01)
**Then**:
- Validation error: "Start date must be before end date"
- Apply button disabled
- Filter not applied
- User can correct dates

---

## Definition of Done

### Code Quality
- [ ] Code follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] Type hints throughout (no `any` in TypeScript)
- [ ] structlog for all logging (backend)
- [ ] Error handling comprehensive (try-catch blocks)
- [ ] ESLint + Prettier applied (frontend)
- [ ] Black formatting applied (backend, line length 100)

### Testing
- [ ] Unit tests: 100% coverage for FilterBar, AuthorFilter, DateRangeFilter, SearchInput components
- [ ] Integration tests: API endpoint filtering tested with various combinations
- [ ] E2E tests: Playwright test for applying filters, URL persistence, clearing filters
- [ ] Performance tests: Filtering response time <50ms for repositories <10,000 commits

### Documentation
- [ ] API documentation: `/api/git/commits` filter parameters documented
- [ ] Component documentation: FilterBar props and usage
- [ ] User guide: How to filter and search commits

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] No security vulnerabilities (SQL injection prevention)
- [ ] No regressions (100% existing tests pass)

---

## Implementation Notes

### Backend Implementation (FastAPI)

```python
# gao_dev/web/api/git.py (enhanced from Story 39.25)
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import structlog

from gao_dev.core.git_manager import GitManager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/git", tags=["git"])

@router.get("/commits")
async def get_commits(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    author: Optional[str] = None,  # "all", "agents", "user", or specific agent name
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    search: Optional[str] = None,  # Search commit messages
):
    """Get commit history with filtering and pagination"""
    try:
        git_manager = GitManager()

        # Parse author filter
        author_filter = None
        if author and author != "all":
            if author == "agents":
                # Filter for all agent commits
                author_filter = _get_agent_emails()
            elif author == "user":
                # Filter for non-agent commits
                author_filter = _get_agent_emails()
                author_filter["exclude"] = True
            else:
                # Specific agent or user
                author_filter = [author]

        # Get filtered commits
        commits = git_manager.get_commit_history(
            limit=limit,
            offset=offset,
            author=author_filter,
            since=since,
            until=until,
            message_search=search,
        )

        # Get total counts
        total_filtered = git_manager.get_commit_count(
            author=author_filter, since=since, until=until, message_search=search
        )
        total_unfiltered = git_manager.get_commit_count()

        return {
            "commits": [_format_commit(c) for c in commits],
            "total": total_filtered,
            "total_unfiltered": total_unfiltered,
            "has_more": (offset + limit) < total_filtered,
            "filters_applied": {
                "author": author,
                "since": since.isoformat() if since else None,
                "until": until.isoformat() if until else None,
                "search": search,
            },
        }
    except Exception as e:
        logger.error("failed_to_get_commits", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load commits")

def _get_agent_emails() -> list[str]:
    """Get email addresses for all GAO-Dev agents"""
    return [
        "brian@gao-dev.local",
        "john@gao-dev.local",
        "winston@gao-dev.local",
        "sally@gao-dev.local",
        "bob@gao-dev.local",
        "amelia@gao-dev.local",
        "murat@gao-dev.local",
        "mary@gao-dev.local",
        "noreply@anthropic.com",  # Claude's email
    ]

def _format_commit(commit):
    """Format commit for API response"""
    return {
        "hash": commit.hash,
        "short_hash": commit.hash[:7],
        "message": commit.message,
        "author": {
            "name": commit.author_name,
            "email": commit.author_email,
            "is_agent": _is_agent_commit(commit.author_email),
        },
        "timestamp": commit.timestamp.isoformat(),
        "files_changed": commit.files_changed,
        "insertions": commit.insertions,
        "deletions": commit.deletions,
    }
```

### Frontend Implementation (React + TypeScript)

```typescript
// src/components/git/FilterBar.tsx
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AuthorFilter } from './AuthorFilter';
import { DateRangeFilter } from './DateRangeFilter';
import { SearchInput } from './SearchInput';
import { FilterBadge } from './FilterBadge';
import { Button } from '../common/Button';

interface FilterBarProps {
  onFilterChange: (filters: CommitFilters) => void;
  activeFilterCount: number;
}

export const FilterBar: React.FC<FilterBarProps> = ({ onFilterChange, activeFilterCount }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [filters, setFilters] = useState<CommitFilters>({
    author: searchParams.get('author') || 'all',
    since: searchParams.get('since') || undefined,
    until: searchParams.get('until') || undefined,
    search: searchParams.get('search') || '',
  });

  // Update URL when filters change
  useEffect(() => {
    const params: Record<string, string> = {};
    if (filters.author && filters.author !== 'all') params.author = filters.author;
    if (filters.since) params.since = filters.since;
    if (filters.until) params.until = filters.until;
    if (filters.search) params.search = filters.search;

    setSearchParams(params);
    onFilterChange(filters);
  }, [filters, onFilterChange, setSearchParams]);

  const handleClearFilters = () => {
    setFilters({
      author: 'all',
      since: undefined,
      until: undefined,
      search: '',
    });
  };

  return (
    <div className="filter-bar">
      <AuthorFilter
        value={filters.author}
        onChange={(author) => setFilters({ ...filters, author })}
      />
      <DateRangeFilter
        since={filters.since}
        until={filters.until}
        onChange={(since, until) => setFilters({ ...filters, since, until })}
      />
      <SearchInput
        value={filters.search}
        onChange={(search) => setFilters({ ...filters, search })}
      />
      {activeFilterCount > 0 && (
        <>
          <FilterBadge count={activeFilterCount} />
          <Button onClick={handleClearFilters} variant="ghost">
            Clear all filters
          </Button>
        </>
      )}
    </div>
  );
};
```

```typescript
// src/components/git/AuthorFilter.tsx
import React from 'react';
import { Select } from '../common/Select';

interface AuthorFilterProps {
  value: string;
  onChange: (value: string) => void;
}

export const AuthorFilter: React.FC<AuthorFilterProps> = ({ value, onChange }) => {
  const options = [
    { value: 'all', label: 'All Authors' },
    { value: 'agents', label: 'Agents Only' },
    { value: 'user', label: 'User Only' },
    { value: '---', label: '---', disabled: true },
    { value: 'brian', label: 'Brian (Workflow Coordinator)' },
    { value: 'john', label: 'John (Product Manager)' },
    { value: 'winston', label: 'Winston (Architect)' },
    { value: 'sally', label: 'Sally (UX Designer)' },
    { value: 'bob', label: 'Bob (Scrum Master)' },
    { value: 'amelia', label: 'Amelia (Developer)' },
    { value: 'murat', label: 'Murat (Test Architect)' },
    { value: 'mary', label: 'Mary (Business Analyst)' },
  ];

  return (
    <Select
      label="Author"
      value={value}
      onChange={onChange}
      options={options}
    />
  );
};
```

```typescript
// src/components/git/DateRangeFilter.tsx
import React, { useState } from 'react';
import { Popover } from '../common/Popover';
import { Button } from '../common/Button';
import { DatePicker } from '../common/DatePicker';
import { subDays, format } from 'date-fns';

interface DateRangeFilterProps {
  since?: string;
  until?: string;
  onChange: (since?: string, until?: string) => void;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({ since, until, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [customRange, setCustomRange] = useState({ since: '', until: '' });

  const presets = [
    { label: 'Last 7 days', since: format(subDays(new Date(), 7), 'yyyy-MM-dd') },
    { label: 'Last 30 days', since: format(subDays(new Date(), 30), 'yyyy-MM-dd') },
    { label: 'Last 90 days', since: format(subDays(new Date(), 90), 'yyyy-MM-dd') },
  ];

  const handlePresetClick = (preset: { since: string }) => {
    onChange(preset.since, undefined);
    setIsOpen(false);
  };

  const handleCustomRange = () => {
    if (customRange.since && customRange.until && customRange.since < customRange.until) {
      onChange(customRange.since, customRange.until);
      setIsOpen(false);
    }
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <Popover.Trigger>
        <Button variant="outline">
          {since ? `Since ${since}` : 'Date Range'}
        </Button>
      </Popover.Trigger>
      <Popover.Content>
        <div className="date-range-picker">
          {presets.map(preset => (
            <Button
              key={preset.label}
              variant="ghost"
              onClick={() => handlePresetClick(preset)}
            >
              {preset.label}
            </Button>
          ))}
          <div className="custom-range">
            <DatePicker
              label="From"
              value={customRange.since}
              onChange={(value) => setCustomRange({ ...customRange, since: value })}
            />
            <DatePicker
              label="To"
              value={customRange.until}
              onChange={(value) => setCustomRange({ ...customRange, until: value })}
            />
            <Button onClick={handleCustomRange}>Apply</Button>
          </div>
        </div>
      </Popover.Content>
    </Popover>
  );
};
```

```typescript
// src/components/git/SearchInput.tsx
import React, { useState, useEffect } from 'react';
import { Input } from '../common/Input';
import { SearchIcon } from '../icons';
import { useDebouncedValue } from '../../hooks/useDebouncedValue';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
}

export const SearchInput: React.FC<SearchInputProps> = ({ value, onChange }) => {
  const [localValue, setLocalValue] = useState(value);
  const debouncedValue = useDebouncedValue(localValue, 300);

  useEffect(() => {
    onChange(debouncedValue);
  }, [debouncedValue, onChange]);

  return (
    <Input
      placeholder="Search commit messages..."
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      icon={<SearchIcon />}
    />
  );
};
```

---

## Related Stories

**Dependencies**:
- **Story 39.25**: Git Timeline Commit History (commit list rendering)
- **Epic 27**: GitIntegratedStateManager (git filtering operations)

**Enables**:
- Enhanced commit history navigation
- Faster debugging and change tracking

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
