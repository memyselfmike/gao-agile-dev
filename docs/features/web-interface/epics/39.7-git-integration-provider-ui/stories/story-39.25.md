# Story 39.25: Git Timeline Commit History

**Story Number**: 39.25
**Epic**: 39.7 - Git Integration & Provider UI
**Feature**: Web Interface
**Status**: Planned
**Priority**: SHOULD HAVE (P1 - V1.1)
**Effort Estimate**: M (Medium - 4 story points)
**Dependencies**: Epic 39.1-39.4 (Backend & Frontend Foundation), Epic 27 (GitIntegratedStateManager)

---

## User Story

As a **product owner**
I want **to see a chronological commit history in the web interface**
So that **I can track changes over time and understand project evolution**

---

## Acceptance Criteria

### Commit List Display
- [ ] AC1: Commit list shows commit message, author, timestamp, and short hash (7 characters)
- [ ] AC2: Commit cards display author badge with visual distinction:
  - Agent commits: Blue robot icon with agent name (Brian, John, Winston, etc.)
  - User commits: Purple user icon with git username
- [ ] AC3: Commits ordered newest first (reverse chronological)
- [ ] AC4: Clicking a commit navigates to diff view (Story 39.26)
- [ ] AC5: Timestamp format adapts to age:
  - < 7 days: Relative format ("2 hours ago", "3 days ago")
  - >= 7 days: Absolute format ("Jan 15, 2025 14:30")

### Performance & Scalability
- [ ] AC6: Virtual scrolling implemented for repositories with >10,000 commits
- [ ] AC7: Initial load shows 50 commits, "Load More" button fetches next 50
- [ ] AC8: Commit list renders in <200ms for standard repositories (<1,000 commits)
- [ ] AC9: Virtual scrolling maintains 60fps during scrolling

### Interactivity
- [ ] AC10: Commit hash is clickable and copies full hash to clipboard with toast notification
- [ ] AC11: Click file name in commit card navigates to Files tab with file highlighted
- [ ] AC12: Real-time updates when new commits are made (via WebSocket `git.commit` event)

### Edge Cases & Empty States
- [ ] AC13: Empty state when no commits exist: "No commits yet. Start coding to see history!"
- [ ] AC14: Loading state while fetching commits shows skeleton loader
- [ ] AC15: Error state when git operations fail: "Failed to load commits. Check git repository."

---

## Technical Context

### Architecture Integration

**Integration with Epic 27 (GitIntegratedStateManager)**:
- Reuse `GitManager.get_commit_history()` method
- Leverage existing git wrapper for safe operations
- Use atomic git operations for consistency

**API Endpoints** (Backend - Story 39.25):
```
GET /api/git/commits?limit=50&offset=0&author=<author>&since=<date>&until=<date>
Response: {
  commits: [
    {
      hash: "abc1234",
      short_hash: "abc1234",
      message: "feat(web): Story 39.25 - Git Timeline",
      author: {
        name: "Amelia",
        email: "amelia@gao-dev.local",
        is_agent: true
      },
      timestamp: "2025-01-17T14:30:00Z",
      files_changed: 5,
      insertions: 120,
      deletions: 30
    }
  ],
  total: 1234,
  has_more: true
}
```

**Frontend Components** (Story 39.25):
```
src/components/git/
├── GitTimeline.tsx          # Main timeline container
├── CommitList.tsx           # Virtual scrolling commit list
├── CommitCard.tsx           # Individual commit card
├── AuthorBadge.tsx          # Agent/User badge component
└── EmptyState.tsx           # No commits state
```

### Dependencies

**Epic 27 (GitIntegratedStateManager)**:
- `GitManager.get_commit_history()` - Fetch commit log
- `GitManager.get_commit_details()` - Get detailed commit info
- Git wrapper ensures safe operations

**Epic 39.1-39.4**:
- Backend: FastAPI endpoints for git operations
- Frontend: React components, WebSocket integration

**Story 39.26 (Monaco Diff Viewer)**:
- Commit click handler navigates to diff view

---

## Test Scenarios

### Test 1: Successful Commit History Load
**Given**: Repository with 150 commits
**When**: User navigates to Git Timeline tab
**Then**:
- First 50 commits displayed in reverse chronological order
- Each commit shows message, author badge, timestamp, short hash
- "Load More" button visible
- Rendering completes in <200ms

### Test 2: Agent vs User Commit Badges
**Given**: Repository with agent and user commits
**When**: User views commit list
**Then**:
- Agent commits show blue robot icon with agent name
- User commits show purple user icon with git username
- Badges visually distinct and easily identifiable

### Test 3: Virtual Scrolling Performance
**Given**: Repository with 15,000 commits
**When**: User scrolls through commit list
**Then**:
- Virtual scrolling maintains 60fps
- Only visible commits rendered (performance optimization)
- Scroll position preserved on tab switch

### Test 4: Commit Hash Copy
**Given**: User viewing commit list
**When**: User clicks commit hash "abc1234"
**Then**:
- Full hash copied to clipboard
- Toast notification: "Commit hash copied: abc1234567890abcdef..."
- No page navigation

### Test 5: Real-Time Updates
**Given**: User viewing commit list, WebSocket connected
**When**: New commit created (e.g., via CLI or agent)
**Then**:
- WebSocket emits `git.commit` event
- New commit appears at top of list
- Smooth animation for new commit insertion
- No full page reload

### Test 6: Empty State
**Given**: New repository with no commits
**When**: User navigates to Git Timeline tab
**Then**:
- Empty state message: "No commits yet. Start coding to see history!"
- Illustration or icon displayed
- No error or loading spinner

### Test 7: Error Handling
**Given**: Git repository corrupted or inaccessible
**When**: User navigates to Git Timeline tab
**Then**:
- Error state: "Failed to load commits. Check git repository."
- Retry button available
- Error logged to console with details

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
- [ ] Unit tests: 100% coverage for CommitList, CommitCard, AuthorBadge components
- [ ] Integration tests: API endpoint `/api/git/commits` tested with mock git repository
- [ ] E2E tests: Playwright test for commit list rendering, virtual scrolling, copy hash
- [ ] Performance tests: Virtual scrolling maintains 60fps with 10,000+ commits

### Documentation
- [ ] API documentation: `/api/git/commits` endpoint documented
- [ ] Component documentation: CommitList, CommitCard props and usage
- [ ] User guide: How to view commit history

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] No security vulnerabilities (git operations sandboxed)
- [ ] No regressions (100% existing tests pass)

---

## Implementation Notes

### Backend Implementation (FastAPI)

```python
# gao_dev/web/api/git.py
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime
import structlog

from gao_dev.core.git_manager import GitManager
from gao_dev.web.models.git import CommitResponse, AuthorInfo

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/git", tags=["git"])

@router.get("/commits", response_model=dict)
async def get_commits(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    author: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    """Get commit history with pagination and filtering"""
    try:
        git_manager = GitManager()
        commits = git_manager.get_commit_history(
            limit=limit,
            offset=offset,
            author=author,
            since=since,
            until=until,
        )

        total_commits = git_manager.get_commit_count(
            author=author, since=since, until=until
        )

        commit_list = [
            {
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
            for commit in commits
        ]

        return {
            "commits": commit_list,
            "total": total_commits,
            "has_more": (offset + limit) < total_commits,
        }
    except Exception as e:
        logger.error("failed_to_get_commits", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load commits")

def _is_agent_commit(email: str) -> bool:
    """Detect if commit is from GAO-Dev agent"""
    agent_domains = ["@gao-dev.local", "noreply@anthropic.com"]
    return any(domain in email for domain in agent_domains)
```

### Frontend Implementation (React + TypeScript)

```typescript
// src/components/git/GitTimeline.tsx
import React, { useEffect, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { VirtualList } from '../common/VirtualList';
import { CommitCard } from './CommitCard';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { Skeleton } from '../common/Skeleton';
import { useWebSocket } from '../../hooks/useWebSocket';

export const GitTimeline: React.FC = () => {
  const { data, fetchNextPage, hasNextPage, isLoading, error } = useInfiniteQuery({
    queryKey: ['git-commits'],
    queryFn: ({ pageParam = 0 }) =>
      fetch(`/api/git/commits?limit=50&offset=${pageParam}`).then(res => res.json()),
    getNextPageParam: (lastPage, pages) =>
      lastPage.has_more ? pages.length * 50 : undefined,
  });

  const { subscribe } = useWebSocket();

  // Real-time updates via WebSocket
  useEffect(() => {
    const unsubscribe = subscribe('git.commit', (event) => {
      // Refetch first page to show new commit
      queryClient.invalidateQueries(['git-commits']);
    });
    return unsubscribe;
  }, [subscribe]);

  if (isLoading) return <Skeleton count={10} />;
  if (error) return <ErrorState message="Failed to load commits" />;

  const commits = data?.pages.flatMap(page => page.commits) ?? [];

  if (commits.length === 0) {
    return <EmptyState message="No commits yet. Start coding to see history!" />;
  }

  return (
    <VirtualList
      items={commits}
      height={600}
      itemHeight={80}
      renderItem={(commit) => <CommitCard key={commit.hash} commit={commit} />}
      onEndReached={() => hasNextPage && fetchNextPage()}
    />
  );
};
```

```typescript
// src/components/git/CommitCard.tsx
import React from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { AuthorBadge } from './AuthorBadge';
import { CopyButton } from '../common/CopyButton';
import { useNavigate } from 'react-router-dom';
import type { Commit } from '../../types/git';

interface CommitCardProps {
  commit: Commit;
}

export const CommitCard: React.FC<CommitCardProps> = ({ commit }) => {
  const navigate = useNavigate();
  const commitAge = new Date(commit.timestamp);
  const isRecent = Date.now() - commitAge.getTime() < 7 * 24 * 60 * 60 * 1000;

  const formattedTime = isRecent
    ? formatDistanceToNow(commitAge, { addSuffix: true })
    : format(commitAge, 'MMM d, yyyy HH:mm');

  return (
    <div
      className="commit-card"
      onClick={() => navigate(`/git/commits/${commit.hash}`)}
    >
      <AuthorBadge author={commit.author} />
      <div className="commit-content">
        <div className="commit-message">{commit.message}</div>
        <div className="commit-meta">
          <span className="commit-time">{formattedTime}</span>
          <CopyButton
            text={commit.hash}
            label={commit.short_hash}
            onClick={(e) => e.stopPropagation()}
          />
          <span className="commit-stats">
            +{commit.insertions} -{commit.deletions}
          </span>
        </div>
      </div>
    </div>
  );
};
```

```typescript
// src/components/git/AuthorBadge.tsx
import React from 'react';
import { RobotIcon, UserIcon } from '../icons';
import type { Author } from '../../types/git';

interface AuthorBadgeProps {
  author: Author;
}

export const AuthorBadge: React.FC<AuthorBadgeProps> = ({ author }) => {
  const Icon = author.is_agent ? RobotIcon : UserIcon;
  const colorClass = author.is_agent ? 'badge-agent' : 'badge-user';

  return (
    <div className={`author-badge ${colorClass}`}>
      <Icon size={20} />
      <span className="author-name">{author.name}</span>
    </div>
  );
};
```

---

## Related Stories

**Dependencies**:
- **Epic 27**: GitIntegratedStateManager (git operations)
- **Epic 39.1**: FastAPI Web Server Setup (backend)
- **Epic 39.4**: React + Vite Setup (frontend)

**Enables**:
- **Story 39.26**: Monaco Diff Viewer for Commits (click commit to view diff)
- **Story 39.27**: Git Filters and Search (filtering commit list)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
