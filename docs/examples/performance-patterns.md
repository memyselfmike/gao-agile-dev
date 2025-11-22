# Performance Patterns

Optimization patterns and techniques used in GAO-Dev.

---

## 1. Caching with LRU Cache

**Context**: Fast context loading with caching

**Example from**: `gao_dev/core/services/fast_context_loader.py`

```python
from functools import lru_cache
from pathlib import Path
import time


class FastContextLoader:
    """Fast context loading with LRU caching."""

    def __init__(self, cache_size: int = 128):
        """Initialize with cache size."""
        self.cache_size = cache_size
        self._setup_cache()

    def _setup_cache(self):
        """Setup LRU cache for file reading."""
        @lru_cache(maxsize=self.cache_size)
        def _read_file_cached(file_path: str, mtime: float) -> str:
            """Read file with caching based on modification time."""
            return Path(file_path).read_text()

        self._read_file_cached = _read_file_cached

    def load_context(self, file_path: Path) -> str:
        """Load file with caching.

        Cache key includes modification time to auto-invalidate on changes.
        """
        start = time.time()

        # Get modification time for cache key
        mtime = file_path.stat().st_mtime

        # Read from cache (or filesystem if cache miss)
        content = self._read_file_cached(str(file_path), mtime)

        duration_ms = (time.time() - start) * 1000
        logger.debug("context_loaded",
                    path=str(file_path),
                    duration_ms=duration_ms,
                    cache_hit=duration_ms < 5)  # < 5ms = cache hit

        return content

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        cache_info = self._read_file_cached.cache_info()

        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "hit_rate": cache_info.hits / (cache_info.hits + cache_info.misses)
                if (cache_info.hits + cache_info.misses) > 0 else 0,
            "size": cache_info.currsize,
            "max_size": cache_info.maxsize
        }
```

**Performance**: <5ms cache hits, <50ms cache misses, >80% hit rate

---

## 2. Virtual Scrolling for Large Lists

**Context**: Rendering 10,000+ items efficiently

**Example from**: `gao_dev/web/frontend/src/components/activity/ActivityStream.tsx`

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

export function ActivityStream({ events }: { events: ActivityEvent[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  // Virtual scrolling for performance
  const virtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated height per item
    overscan: 5, // Render 5 extra items above/below viewport
  });

  return (
    <div
      ref={parentRef}
      className="h-full overflow-y-auto"
      style={{ contain: 'strict' }} // Performance optimization
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const event = events[virtualItem.index];

          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <ActivityEventCard event={event} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

**Performance**: 60fps with 10,000+ items, only renders visible items

---

## 3. Debouncing User Input

**Context**: Reducing API calls for search/filter

**Example from**: `gao_dev/web/frontend/src/hooks/useDebouncedValue.ts`

```typescript
import { useEffect, useState } from 'vitest';

export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage in component
function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebouncedValue(searchTerm, 300);

  useEffect(() => {
    if (debouncedSearch) {
      // API call only happens after 300ms of no typing
      performSearch(debouncedSearch);
    }
  }, [debouncedSearch]);

  return (
    <input
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      placeholder="Search..."
    />
  );
}
```

**Performance**: Reduces API calls by 90% during typing

---

## 4. Batch Database Operations

**Context**: Efficient bulk inserts/updates

**Example from**: `gao_dev/core/services/git_migration_manager.py`

```python
def migrate_files_to_database(self, files: list[Path]):
    """Migrate multiple files in single transaction."""
    start = time.time()

    # Batch operation in single transaction
    with self.db.begin_transaction():
        # Prepare batch data
        batch_data = []
        for file in files:
            file_data = self._parse_file(file)
            batch_data.append(file_data)

        # Single executemany() instead of multiple execute()
        self.db.executemany(
            """INSERT INTO documents (path, content, hash, created_at)
               VALUES (?, ?, ?, ?)""",
            batch_data
        )

    duration = time.time() - start
    logger.info("batch_migration_complete",
               file_count=len(files),
               duration_s=duration,
               files_per_second=len(files) / duration)
```

**Performance**: 100x faster than individual inserts (1000 files in 2s vs 200s)

---

## 5. Async Parallel Operations

**Context**: Running multiple async operations concurrently

**Example from**: `gao_dev/orchestrator/gao_dev_orchestrator.py`

```python
import asyncio


async def execute_parallel_workflows(self, workflow_names: list[str]) -> dict:
    """Execute multiple workflows in parallel."""
    start = time.time()

    # Create tasks for parallel execution
    tasks = [
        asyncio.create_task(self.execute_workflow(name))
        for name in workflow_names
    ]

    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = time.time() - start

    # Process results
    successful = []
    failed = []

    for workflow_name, result in zip(workflow_names, results):
        if isinstance(result, Exception):
            failed.append({"name": workflow_name, "error": str(result)})
        else:
            successful.append({"name": workflow_name, "result": result})

    logger.info("parallel_workflows_complete",
               total=len(workflow_names),
               successful=len(successful),
               failed=len(failed),
               duration_s=duration)

    return {"successful": successful, "failed": failed}
```

**Performance**: 5 workflows in 12s (parallel) vs 60s (sequential)

---

## 6. Memoization for Expensive Calculations

**Context**: Caching expensive computations

**Example from**: `gao_dev/core/workflow_registry.py`

```python
from functools import lru_cache


class WorkflowRegistry:
    """Workflow registry with memoized operations."""

    @lru_cache(maxsize=None)  # Cache all results
    def get_workflow_graph(self, workflow_name: str) -> dict:
        """Get workflow dependency graph (expensive calculation).

        Cached since graph doesn't change during runtime.
        """
        workflow = self.get_workflow(workflow_name)

        # Expensive graph traversal
        graph = self._build_dependency_graph(workflow)
        nodes = self._calculate_nodes(graph)
        edges = self._calculate_edges(graph)

        return {"nodes": nodes, "edges": edges}

    def clear_cache(self):
        """Clear memoization cache when workflows change."""
        self.get_workflow_graph.cache_clear()
```

**Performance**: First call 500ms, subsequent calls <1ms

---

## 7. Lazy Loading Components

**Context**: Loading UI components only when needed

**Example from**: `gao_dev/web/frontend/src/App.tsx`

```typescript
import { lazy, Suspense } from 'react';

// Lazy load heavy components
const MonacoEditor = lazy(() => import('./components/editor/MonacoEditor'));
const GitTimeline = lazy(() => import('./components/git/GitTimeline'));
const KanbanBoard = lazy(() => import('./components/kanban/KanbanBoard'));

export function App() {
  return (
    <div className="app">
      {/* Show loading spinner while component loads */}
      <Suspense fallback={<LoadingSpinner />}>
        {activeTab === 'editor' && <MonacoEditor />}
        {activeTab === 'git' && <GitTimeline />}
        {activeTab === 'kanban' && <KanbanBoard />}
      </Suspense>
    </div>
  );
}
```

**Performance**: Initial bundle size reduced by 60%, faster first load

---

## 8. Connection Pooling

**Context**: Reusing database connections

**Example from**: `gao_dev/core/database.py`

```python
import sqlite3
from contextlib import contextmanager


class Database:
    """Database with connection pooling."""

    def __init__(self, db_path: Path, pool_size: int = 5):
        """Initialize with connection pool."""
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: list[sqlite3.Connection] = []
        self._initialize_pool()

    def _initialize_pool(self):
        """Create connection pool."""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable column access
            self._pool.append(conn)

    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        if not self._pool:
            raise RuntimeError("Connection pool exhausted")

        conn = self._pool.pop()
        try:
            yield conn
        finally:
            self._pool.append(conn)  # Return to pool
```

**Performance**: 10x faster than creating new connections each time

---

## Key Principles

1. **Cache aggressively**: Use LRU cache for expensive operations
2. **Virtualize large lists**: Only render visible items
3. **Debounce user input**: Reduce unnecessary API calls
4. **Batch operations**: Single transaction vs many
5. **Run in parallel**: Use async/await for concurrency
6. **Lazy load**: Load components only when needed
7. **Pool connections**: Reuse expensive resources

**See Also**:
- [Architecture Overview](../ARCHITECTURE_OVERVIEW.md) - Performance design
- [Web Interface Architecture](../features/web-interface/ARCHITECTURE.md) - Frontend optimizations
