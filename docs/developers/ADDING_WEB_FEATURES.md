# Developer Guide: Adding Web Features to GAO-Dev

## TL;DR

**What**: Complete guide to extending the GAO-Dev Web Interface with new features

**When**: Adding new UI capabilities, API endpoints, WebSocket events, or frontend components

**Key Steps**:
1. Design API endpoints (backend)
2. Create frontend components (React + TypeScript)
3. Add state management (Zustand stores)
4. Implement WebSocket events (real-time updates)
5. Write tests (backend + frontend)
6. Update documentation

**Time**: 2-6 hours depending on complexity

---

## Table of Contents

- [Overview](#overview)
- [Architecture Recap](#architecture-recap)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)
- [State Management](#state-management)
- [WebSocket Events](#websocket-events)
- [Testing](#testing)
- [Common Patterns](#common-patterns)
- [Complete Example](#complete-example)

---

## Overview

### Web Interface Stack

**Backend**: Python 3.11+ / FastAPI / WebSocket / asyncio.Queue
**Frontend**: React 19 / TypeScript / Vite / Zustand
**UI**: shadcn/ui (Radix + Tailwind CSS)
**Editor**: Monaco Editor

### Development Workflow

```
1. Design → 2. Backend → 3. Frontend → 4. Integration → 5. Test
```

**Best practice**: Start with backend API, then build frontend to consume it.

---

## Architecture Recap

### Request Flow

```
User Action (Browser)
  ↓
React Component
  ↓
API Call (fetch)
  ↓
FastAPI Endpoint
  ↓
Business Logic / Service Layer
  ↓
Database / File System / Git
  ↓
Response + WebSocket Event
  ↓
Frontend State Update
  ↓
UI Re-render
```

### Key Directories

```
gao_dev/
├── web/
│   ├── server.py           # FastAPI app + main endpoints
│   ├── api/                # Feature-specific API routers
│   │   ├── git.py
│   │   ├── channels.py
│   │   └── your_feature.py  # ← Add new routers here
│   ├── events.py           # WebSocket event types
│   ├── event_bus.py        # Event pub/sub system
│   └── frontend/
│       └── src/
│           ├── components/  # React components
│           ├── stores/      # Zustand state stores
│           ├── types/       # TypeScript types
│           └── lib/         # Utilities (API client, etc.)
└── tests/
    └── web/
        ├── api/            # Backend API tests
        └── frontend/       # Frontend component tests
```

---

## Backend Development

### Step 1: Create API Router

**File**: `gao_dev/web/api/your_feature.py`

```python
"""Your Feature API endpoints.

Story XX.X: Your Feature Implementation
"""
from datetime import datetime
import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/your-feature", tags=["your-feature"])


# Define request/response models
class CreateItemRequest(BaseModel):
    """Request body for creating an item."""
    name: str
    description: str | None = None


class ItemResponse(BaseModel):
    """Response for item operations."""
    id: str
    name: str
    description: str | None
    created_at: str


# Simple in-memory storage (replace with DB/service layer)
ITEMS = {}


@router.post("/items", response_model=ItemResponse)
async def create_item(request: CreateItemRequest):
    """Create a new item.

    Returns:
        ItemResponse: Created item with ID

    Raises:
        HTTPException: 400 if validation fails
    """
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
    """Get item by ID.

    Args:
        item_id: Item identifier

    Returns:
        ItemResponse: Item details

    Raises:
        HTTPException: 404 if item not found
    """
    if item_id not in ITEMS:
        raise HTTPException(status_code=404, detail="Item not found")

    return ITEMS[item_id]


@router.get("/items", response_model=list[ItemResponse])
async def list_items(limit: int = 50):
    """List all items.

    Args:
        limit: Maximum items to return

    Returns:
        List of items
    """
    return list(ITEMS.values())[:limit]
```

### Step 2: Register Router in Server

**File**: `gao_dev/web/server.py`

```python
# Add import at top
from gao_dev.web.api import your_feature as your_feature_router

# In create_app() function, add router
def create_app(config: WebConfig) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title="GAO-Dev Web Interface")

    # ... existing routers ...

    # Add your router
    app.include_router(your_feature_router.router)

    # ... rest of setup ...

    return app
```

### Step 3: Add Business Logic Layer (Optional)

For complex features, create a service layer:

**File**: `gao_dev/services/your_feature_service.py`

```python
"""Your Feature Service - Business logic layer."""
from pathlib import Path
from typing import List, Optional
import structlog

logger = structlog.get_logger(__name__)


class YourFeatureService:
    """Service for managing your feature."""

    def __init__(self, project_root: Path):
        """Initialize service.

        Args:
            project_root: Path to project root
        """
        self.project_root = project_root
        self.data_dir = project_root / ".gao-dev" / "your-feature"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def create_item(self, name: str, description: str | None = None) -> dict:
        """Create item with validation and persistence.

        Args:
            name: Item name
            description: Optional description

        Returns:
            Created item data

        Raises:
            ValueError: If validation fails
        """
        if not name.strip():
            raise ValueError("Name cannot be empty")

        # Business logic here
        item = {
            "id": f"item-{datetime.utcnow().timestamp()}",
            "name": name.strip(),
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }

        # Persist to file/database
        self._save_item(item)

        return item

    def _save_item(self, item: dict) -> None:
        """Save item to storage."""
        file_path = self.data_dir / f"{item['id']}.json"
        file_path.write_text(json.dumps(item, indent=2))
```

---

## Frontend Development

### Step 1: Define TypeScript Types

**File**: `gao_dev/web/frontend/src/types/index.ts`

```typescript
// Add to existing types
export interface YourFeatureItem {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface CreateItemRequest {
  name: string;
  description?: string;
}
```

### Step 2: Create API Client Functions

**File**: `gao_dev/web/frontend/src/lib/api.ts`

```typescript
// Add to existing API functions
export async function createItem(
  token: string,
  data: CreateItemRequest
): Promise<YourFeatureItem> {
  const response = await fetch('/api/your-feature/items', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-Token': token,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create item');
  }

  return response.json();
}

export async function getItem(
  token: string,
  itemId: string
): Promise<YourFeatureItem> {
  const response = await fetch(`/api/your-feature/items/${itemId}`, {
    headers: {
      'X-Session-Token': token,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get item');
  }

  return response.json();
}

export async function listItems(token: string): Promise<YourFeatureItem[]> {
  const response = await fetch('/api/your-feature/items', {
    headers: {
      'X-Session-Token': token,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to list items');
  }

  return response.json();
}
```

### Step 3: Create React Component

**File**: `gao_dev/web/frontend/src/components/your-feature/ItemCard.tsx`

```typescript
/**
 * ItemCard - Display individual item with actions
 *
 * Story XX.X: Your Feature UI Component
 */
import { formatDistanceToNow } from 'date-fns';
import { Trash2, Edit } from 'lucide-react';
import type { YourFeatureItem } from '../../types';
import { cn } from '../../lib/utils';

interface ItemCardProps {
  item: YourFeatureItem;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
}

export function ItemCard({ item, onDelete, onEdit }: ItemCardProps) {
  const timeAgo = formatDistanceToNow(new Date(item.created_at), {
    addSuffix: true,
  });

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="mb-2 flex items-start justify-between">
        <h3 className="text-lg font-semibold text-card-foreground">
          {item.name}
        </h3>

        <div className="flex gap-2">
          {onEdit && (
            <button
              onClick={() => onEdit(item.id)}
              className="rounded p-1 hover:bg-muted transition-colors"
              aria-label="Edit item"
            >
              <Edit className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(item.id)}
              className="rounded p-1 hover:bg-destructive/10 text-destructive transition-colors"
              aria-label="Delete item"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Description */}
      {item.description && (
        <p className="mb-3 text-sm text-muted-foreground">
          {item.description}
        </p>
      )}

      {/* Footer */}
      <div className="text-xs text-muted-foreground">
        Created {timeAgo}
      </div>
    </div>
  );
}
```

### Step 4: Create Tab Component (if needed)

**File**: `gao_dev/web/frontend/src/components/tabs/YourFeatureTab.tsx`

```typescript
/**
 * YourFeatureTab - Main tab for your feature
 *
 * Story XX.X: Your Feature Tab
 */
import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { ItemCard } from '../your-feature/ItemCard';
import { useYourFeatureStore } from '../../stores/yourFeatureStore';
import { useSessionStore } from '../../stores/sessionStore';
import { createItem, listItems } from '../../lib/api';

export function YourFeatureTab() {
  const { items, addItem, removeItem, setLoading, setError } = useYourFeatureStore();
  const token = useSessionStore((state) => state.token);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemDescription, setNewItemDescription] = useState('');

  // Load items on mount
  useEffect(() => {
    async function loadItems() {
      if (!token) return;

      setLoading(true);
      try {
        const items = await listItems(token);
        items.forEach((item) => addItem(item));
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to load items');
      } finally {
        setLoading(false);
      }
    }

    loadItems();
  }, [token, addItem, setLoading, setError]);

  const handleCreate = async () => {
    if (!token || !newItemName.trim()) return;

    try {
      const item = await createItem(token, {
        name: newItemName,
        description: newItemDescription || undefined,
      });

      addItem(item);
      setNewItemName('');
      setNewItemDescription('');
      setShowCreateForm(false);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create item');
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Your Feature</h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Create Item
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="border-b bg-muted/50 p-4">
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Item name"
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              className="w-full rounded-lg border bg-background px-3 py-2"
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newItemDescription}
              onChange={(e) => setNewItemDescription(e.target.value)}
              className="w-full rounded-lg border bg-background px-3 py-2"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                className="rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Items List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              onDelete={(id) => {
                // Handle delete
                removeItem(id);
              }}
              onEdit={(id) => {
                // Handle edit
                console.log('Edit:', id);
              }}
            />
          ))}
        </div>

        {items.length === 0 && !showCreateForm && (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            No items yet. Click "Create Item" to get started.
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## State Management

### Create Zustand Store

**File**: `gao_dev/web/frontend/src/stores/yourFeatureStore.ts`

```typescript
/**
 * Your Feature Store - Zustand state management
 *
 * Story XX.X: State management for your feature
 */
import { create } from 'zustand';
import type { YourFeatureItem } from '../types';

interface YourFeatureState {
  items: YourFeatureItem[];
  selectedItem: YourFeatureItem | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  addItem: (item: YourFeatureItem) => void;
  updateItem: (id: string, updates: Partial<YourFeatureItem>) => void;
  removeItem: (id: string) => void;
  selectItem: (item: YourFeatureItem | null) => void;
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

---

## WebSocket Events

### Step 1: Add Event Type

**File**: `gao_dev/web/events.py`

```python
class EventType(str, Enum):
    """WebSocket event types."""

    # ... existing events ...

    # Your feature events
    YOUR_FEATURE_ITEM_CREATED = "your_feature.item_created"
    YOUR_FEATURE_ITEM_UPDATED = "your_feature.item_updated"
    YOUR_FEATURE_ITEM_DELETED = "your_feature.item_deleted"
```

### Step 2: Emit Events from Backend

**File**: `gao_dev/web/api/your_feature.py`

```python
from gao_dev.web.event_bus import event_bus
from gao_dev.web.events import WebEvent, EventType

@router.post("/items", response_model=ItemResponse)
async def create_item(request: CreateItemRequest):
    """Create a new item."""
    # ... create item logic ...

    # Emit WebSocket event
    await event_bus.publish(WebEvent(
        type=EventType.YOUR_FEATURE_ITEM_CREATED,
        data={
            "item_id": item.id,
            "name": item.name,
            "description": item.description,
            "created_at": item.created_at
        }
    ))

    return item
```

### Step 3: Handle Events in Frontend

**File**: `gao_dev/web/frontend/src/lib/websocket.ts`

```typescript
// In handleMessage function, add case for your events
case 'your_feature.item_created':
  useYourFeatureStore.getState().addItem(event.data);
  break;

case 'your_feature.item_updated':
  useYourFeatureStore.getState().updateItem(
    event.data.item_id,
    event.data
  );
  break;

case 'your_feature.item_deleted':
  useYourFeatureStore.getState().removeItem(event.data.item_id);
  break;
```

---

## Testing

### Backend API Tests

**File**: `tests/web/api/test_your_feature.py`

```python
"""Tests for your feature API endpoints."""
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
        json={"name": "Test Item", "description": "Test description"},
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
        json={"name": "", "description": "Test"},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_get_item_not_found(client):
    """Test getting non-existent item."""
    response = client.get("/api/your-feature/items/nonexistent")

    assert response.status_code == 404
```

### Frontend Component Tests

**File**: `gao_dev/web/frontend/src/components/your-feature/ItemCard.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ItemCard } from './ItemCard';
import type { YourFeatureItem } from '../../types';

describe('ItemCard', () => {
  const mockItem: YourFeatureItem = {
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

  it('does not show buttons when handlers not provided', () => {
    render(<ItemCard item={mockItem} />);

    expect(screen.queryByLabelText('Delete item')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Edit item')).not.toBeInTheDocument();
  });
});
```

---

## Common Patterns

### Pattern: Add New Tab to Main UI

**File**: `gao_dev/web/frontend/src/App.tsx`

```typescript
// Import your tab
import { YourFeatureTab } from './components/tabs/YourFeatureTab';

// Add to tabs array
const tabs = [
  // ... existing tabs ...
  {
    id: 'your-feature',
    label: 'Your Feature',
    icon: YourIcon,
    component: YourFeatureTab,
  },
];
```

### Pattern: Session Token Authentication

All API calls require session token:

```typescript
const token = useSessionStore((state) => state.token);

const response = await fetch('/api/your-feature/items', {
  headers: {
    'X-Session-Token': token,
  },
});
```

### Pattern: Error Handling

```typescript
try {
  const result = await apiCall();
  // Success
} catch (error) {
  const message = error instanceof Error ? error.message : 'Unknown error';
  useYourFeatureStore.getState().setError(message);
}
```

---

## Complete Example

See [Quick Start Guide](../QUICK_START.md) for complete working examples of:
- Adding API endpoint
- Adding WebSocket event
- Adding frontend component
- Adding backend service
- Integrating with state manager

---

## See Also

- [Quick Start Guide](../QUICK_START.md) - Copy-paste integration patterns
- [API Reference](../API_REFERENCE.md) - Complete API catalog
- [Web Interface Architecture](../features/web-interface/ARCHITECTURE.md) - Full architecture
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing patterns

**Estimated tokens**: ~2,450
