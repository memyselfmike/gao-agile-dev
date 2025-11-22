# Quick Start: GAO-Dev Integration Patterns

## TL;DR

**What**: Copy-paste code examples for common GAO-Dev integration tasks
**When**: Adding features, testing, or integrating with existing systems
**Key steps**: Copy example, adapt to your needs, test
**Time**: 5-30 minutes per pattern

## Prerequisites

- GAO-Dev development environment installed
- Python 3.11+, Node.js 20+
- Familiarity with FastAPI, React, TypeScript

---

## Adding Features

### 1. Add API Endpoint (100 lines)

**File**: `gao_dev/web/api/your_feature.py`

```python
"""Your Feature API endpoints.

Story XX.X: Your Feature Implementation
"""
from datetime import datetime
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/your-feature", tags=["your-feature"])


# Request/Response Models
class CreateItemRequest(BaseModel):
    """Request body for creating an item."""
    name: str
    description: str


class ItemResponse(BaseModel):
    """Response for item operations."""
    id: str
    name: str
    description: str
    created_at: str


# In-memory storage (replace with DB integration)
ITEMS = {}


@router.post("/items", response_model=ItemResponse)
async def create_item(request: CreateItemRequest):
    """Create a new item."""
    logger.info("creating_item", name=request.name)

    # Validate
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    # Create
    item_id = f"item-{len(ITEMS) + 1}"
    item = ItemResponse(
        id=item_id,
        name=request.name,
        description=request.description,
        created_at=datetime.utcnow().isoformat()
    )

    ITEMS[item_id] = item
    logger.info("item_created", item_id=item_id)
    return item


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get item by ID."""
    if item_id not in ITEMS:
        raise HTTPException(status_code=404, detail="Item not found")

    return ITEMS[item_id]
```

**Register router** in `gao_dev/web/server.py`:
```python
from gao_dev.web.api.your_feature import router as your_feature_router
app.include_router(your_feature_router)
```

---

### 2. Add WebSocket Event (80 lines)

**Step 1**: Define event type in `gao_dev/web/events.py`:
```python
class EventType(str, Enum):
    """WebSocket event types."""
    # ... existing events ...
    YOUR_FEATURE_CREATED = "your_feature.created"
    YOUR_FEATURE_UPDATED = "your_feature.updated"
```

**Step 2**: Emit event from your API:
```python
from gao_dev.web.event_bus import event_bus
from gao_dev.web.events import WebEvent, EventType

# Inside your endpoint
await event_bus.publish(WebEvent(
    type=EventType.YOUR_FEATURE_CREATED,
    data={
        "item_id": item_id,
        "name": request.name,
        "created_at": datetime.utcnow().isoformat()
    }
))
```

**Step 3**: Handle on frontend in `WebSocketProvider.tsx`:
```typescript
case 'your_feature.created':
  useYourFeatureStore.getState().addItem(event.data);
  break;
```

---

### 3. Add Frontend Component (120 lines)

**File**: `gao_dev/web/frontend/src/components/your-feature/ItemCard.tsx`

```typescript
/**
 * ItemCard - Display individual item with actions
 *
 * Story XX.X: Your Feature UI Component
 */
import { formatDistanceToNow } from 'date-fns';
import { Trash2, Edit } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ItemCardProps {
  item: {
    id: string;
    name: string;
    description: string;
    created_at: string;
  };
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
}

export function ItemCard({ item, onDelete, onEdit }: ItemCardProps) {
  const timeAgo = formatDistanceToNow(new Date(item.created_at), {
    addSuffix: true
  });

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      {/* Header */}
      <div className="mb-2 flex items-start justify-between">
        <h3 className="text-lg font-semibold">{item.name}</h3>
        <div className="flex gap-2">
          {onEdit && (
            <button
              onClick={() => onEdit(item.id)}
              className="rounded p-1 hover:bg-muted"
              aria-label="Edit item"
            >
              <Edit className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(item.id)}
              className="rounded p-1 hover:bg-destructive/10 text-destructive"
              aria-label="Delete item"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      <p className="mb-3 text-sm text-muted-foreground">
        {item.description}
      </p>

      {/* Footer */}
      <div className="text-xs text-muted-foreground">
        Created {timeAgo}
      </div>
    </div>
  );
}
```

---

### 4. Add Backend Service (150 lines)

**File**: `gao_dev/services/your_feature_service.py`

```python
"""Your Feature Service - Business logic layer.

Story XX.X: Your Feature Service Implementation
"""
from pathlib import Path
from typing import List, Optional
import structlog
from gao_dev.core.models.your_feature import Item, ItemCreate
from gao_dev.core.database import Database

logger = structlog.get_logger(__name__)


class YourFeatureService:
    """Service for managing your feature items."""

    def __init__(self, project_root: Path, db: Optional[Database] = None):
        """Initialize service.

        Args:
            project_root: Path to project root directory
            db: Optional database instance (for testing)
        """
        self.project_root = project_root
        self.db = db or Database(project_root / ".gao-dev" / "items.db")
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure database tables exist."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)

    async def create_item(self, item_data: ItemCreate) -> Item:
        """Create new item.

        Args:
            item_data: Item creation data

        Returns:
            Created item with ID

        Raises:
            ValueError: If item data is invalid
        """
        logger.info("creating_item", name=item_data.name)

        # Validate
        if not item_data.name.strip():
            raise ValueError("Item name cannot be empty")

        # Generate ID
        from datetime import datetime
        item_id = f"item-{datetime.utcnow().timestamp()}"

        # Create item
        item = Item(
            id=item_id,
            name=item_data.name,
            description=item_data.description,
            created_at=datetime.utcnow().isoformat()
        )

        # Save to database
        self.db.execute(
            """INSERT INTO items (id, name, description, created_at)
               VALUES (?, ?, ?, ?)""",
            (item.id, item.name, item.description, item.created_at)
        )

        logger.info("item_created", item_id=item.id)
        return item

    async def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID.

        Args:
            item_id: Item identifier

        Returns:
            Item if found, None otherwise
        """
        row = self.db.execute(
            "SELECT id, name, description, created_at FROM items WHERE id = ?",
            (item_id,)
        ).fetchone()

        if not row:
            return None

        return Item(
            id=row[0],
            name=row[1],
            description=row[2],
            created_at=row[3]
        )

    async def list_items(self, limit: int = 100) -> List[Item]:
        """List all items.

        Args:
            limit: Maximum items to return

        Returns:
            List of items ordered by creation date
        """
        rows = self.db.execute(
            """SELECT id, name, description, created_at
               FROM items
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()

        return [
            Item(id=row[0], name=row[1], description=row[2], created_at=row[3])
            for row in rows
        ]
```

---

### 5. Integrate with State Manager (100 lines)

**File**: `gao_dev/web/frontend/src/stores/yourFeatureStore.ts`

```typescript
/**
 * Your Feature Store - Zustand state management
 *
 * Story XX.X: State management for your feature
 */
import { create } from 'zustand';

interface Item {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

interface YourFeatureState {
  items: Item[];
  selectedItem: Item | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  addItem: (item: Item) => void;
  updateItem: (id: string, updates: Partial<Item>) => void;
  removeItem: (id: string) => void;
  selectItem: (item: Item | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearItems: () => void;
}

export const useYourFeatureStore = create<YourFeatureState>((set) => ({
  items: [],
  selectedItem: null,
  isLoading: false,
  error: null,

  addItem: (item) =>
    set((state) => ({
      items: [...state.items, item],
    })),

  updateItem: (id, updates) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, ...updates } : item
      ),
    })),

  removeItem: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
      selectedItem: state.selectedItem?.id === id ? null : state.selectedItem,
    })),

  selectItem: (item) => set({ selectedItem: item }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearItems: () =>
    set({
      items: [],
      selectedItem: null,
      error: null,
    }),
}));
```

**Usage in component**:
```typescript
import { useYourFeatureStore } from '../../stores/yourFeatureStore';

function YourComponent() {
  const { items, addItem, isLoading } = useYourFeatureStore();

  const handleCreate = async (name: string, description: string) => {
    const response = await fetch('/api/your-feature/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });

    const item = await response.json();
    addItem(item);
  };

  return <div>{/* UI */}</div>;
}
```

---

## Testing Patterns

### 1. Test API Endpoint (60 lines)

**File**: `tests/web/test_your_feature.py`

```python
"""Tests for your feature API endpoints.

Story XX.X: Your Feature - API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from gao_dev.web.server import create_app
from gao_dev.web.config import WebConfig


@pytest.fixture
def test_config(tmp_path):
    """Create test configuration."""
    frontend_dist = tmp_path / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<html></html>")

    return WebConfig(
        host="127.0.0.1",
        port=3000,
        frontend_dist_path=str(frontend_dist),
        auto_open=False,
    )


@pytest.fixture
def client(test_config):
    """Create test client."""
    app = create_app(test_config)
    return TestClient(app)


def test_create_item_success(client):
    """Test creating an item successfully."""
    response = client.post(
        "/api/your-feature/items",
        json={"name": "Test Item", "description": "Test description"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "Test description"
    assert "id" in data
    assert "created_at" in data


def test_create_item_empty_name(client):
    """Test that empty name is rejected."""
    response = client.post(
        "/api/your-feature/items",
        json={"name": "", "description": "Test"}
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
```

---

### 2. Test WebSocket Event (50 lines)

**File**: `tests/web/test_your_feature_events.py`

```python
"""Tests for your feature WebSocket events.

Story XX.X: Your Feature - Event tests
"""
import pytest
from gao_dev.web.event_bus import EventBus
from gao_dev.web.events import WebEvent, EventType


@pytest.mark.asyncio
async def test_emit_item_created_event():
    """Test emitting item created event."""
    event_bus = EventBus()
    received_events = []

    # Subscribe to events
    async def collector(event: WebEvent):
        received_events.append(event)

    event_bus.subscribe(collector)

    # Emit event
    test_event = WebEvent(
        type=EventType.YOUR_FEATURE_CREATED,
        data={
            "item_id": "item-1",
            "name": "Test Item",
            "created_at": "2025-01-16T10:00:00Z"
        }
    )

    await event_bus.publish(test_event)

    # Verify event received
    assert len(received_events) == 1
    assert received_events[0].type == EventType.YOUR_FEATURE_CREATED
    assert received_events[0].data["item_id"] == "item-1"
    assert received_events[0].data["name"] == "Test Item"
```

---

### 3. Test React Component (80 lines)

**File**: `gao_dev/web/frontend/src/components/your-feature/ItemCard.test.tsx`

```typescript
/**
 * Tests for ItemCard component
 *
 * Story XX.X: Your Feature Component Tests
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ItemCard } from './ItemCard';

describe('ItemCard', () => {
  const mockItem = {
    id: 'item-1',
    name: 'Test Item',
    description: 'Test description',
    created_at: new Date().toISOString(),
  };

  it('renders item details correctly', () => {
    render(<ItemCard item={mockItem} />);

    expect(screen.getByText('Test Item')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('calls onDelete when delete button clicked', () => {
    const onDelete = vi.fn();
    render(<ItemCard item={mockItem} onDelete={onDelete} />);

    const deleteButton = screen.getByLabelText('Delete item');
    fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith('item-1');
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it('calls onEdit when edit button clicked', () => {
    const onEdit = vi.fn();
    render(<ItemCard item={mockItem} onEdit={onEdit} />);

    const editButton = screen.getByLabelText('Edit item');
    fireEvent.click(editButton);

    expect(onEdit).toHaveBeenCalledWith('item-1');
    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it('does not show buttons when handlers not provided', () => {
    render(<ItemCard item={mockItem} />);

    expect(screen.queryByLabelText('Delete item')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Edit item')).not.toBeInTheDocument();
  });

  it('displays relative time correctly', () => {
    const pastDate = new Date(Date.now() - 1000 * 60 * 5); // 5 minutes ago
    const item = { ...mockItem, created_at: pastDate.toISOString() };

    render(<ItemCard item={item} />);

    expect(screen.getByText(/5 minutes ago/i)).toBeInTheDocument();
  });
});
```

---

## Common Patterns

### 1. Read from Database (40 lines)

```python
from gao_dev.core.database import Database

# Initialize database
db = Database(Path(".gao-dev") / "your_feature.db")

# Create tables
db.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        data TEXT,
        created_at TEXT NOT NULL
    )
""")

# Insert
db.execute(
    "INSERT INTO items (id, name, data, created_at) VALUES (?, ?, ?, ?)",
    ("item-1", "Test", "data", "2025-01-16T10:00:00Z")
)

# Query single row
row = db.execute("SELECT * FROM items WHERE id = ?", ("item-1",)).fetchone()
if row:
    print(f"Found: {row[1]}")  # name column

# Query multiple rows
rows = db.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
for row in rows:
    print(f"{row[0]}: {row[1]}")  # id: name
```

---

### 2. Emit Git Commit (50 lines)

```python
from gao_dev.services.git_manager import GitManager
from pathlib import Path

# Initialize git manager
git_manager = GitManager(project_root=Path.cwd())

# Check if in git repo
if not git_manager.is_git_repo():
    print("Not a git repository")
    return

# Stage files
files_to_commit = [
    Path("docs/new_document.md"),
    Path("src/new_feature.py"),
]
git_manager.stage_files(files_to_commit)

# Create commit
commit_message = """feat(your-feature): Add new feature

- Added new document
- Implemented feature logic
- Added tests

Story XX.X: Your Feature Implementation
"""

commit_sha = git_manager.commit(commit_message)
print(f"Created commit: {commit_sha[:8]}")

# Get recent commits
commits = git_manager.get_recent_commits(limit=5)
for commit in commits:
    print(f"{commit['sha'][:8]}: {commit['message']}")
```

---

### 3. Validate User Input (60 lines)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ItemCreateRequest(BaseModel):
    """Validated request for creating an item."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: int = Field(default=0, ge=0, le=10)
    tags: list[str] = Field(default_factory=list, max_items=5)

    @validator('name')
    def name_not_empty(cls, v):
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip()

    @validator('tags')
    def tags_valid(cls, v):
        """Validate tags format."""
        for tag in v:
            if not tag.strip():
                raise ValueError('Tags cannot be empty')
            if len(tag) > 20:
                raise ValueError('Tags must be 20 characters or less')
        return [tag.strip() for tag in v]


# Usage in endpoint
@router.post("/items")
async def create_item(request: ItemCreateRequest):
    # Request is automatically validated by Pydantic
    # Access validated data
    print(f"Creating item: {request.name}")
    print(f"Priority: {request.priority}")
    print(f"Tags: {request.tags}")

    # Validation errors are automatically returned as 422 responses
    # with detailed error information

    return {"status": "created", "name": request.name}


# Example validation errors:
# {"name": ""} -> "Name cannot be empty or whitespace"
# {"name": "Test", "priority": 11} -> "ensure this value is less than or equal to 10"
# {"name": "Test", "tags": ["a", "b", "c", "d", "e", "f"]} -> "ensure this value has at most 5 items"
```

---

## See Also

- [API Reference](API_REFERENCE.md) - Complete endpoint and event reference
- [Web Interface Architecture](features/web-interface/ARCHITECTURE.md) - System architecture
- [Testing Guide](../tests/README.md) - Comprehensive testing patterns

**Estimated tokens**: ~1,950
