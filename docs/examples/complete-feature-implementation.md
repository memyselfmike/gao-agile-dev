# Complete Feature Implementation

**Context**: Building a complete feature from scratch with backend API, frontend UI, state management, WebSocket events, and tests.

**Example**: Adding a "Feature Flags" system to GAO-Dev

---

## 1. Backend API (FastAPI)

### API Router

**File**: `gao_dev/web/api/feature_flags.py`

```python
"""Feature Flags API endpoints.

Story: Add feature flag management system
"""
from datetime import datetime
from typing import List
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/feature-flags", tags=["feature-flags"])


# Models
class FeatureFlagCreate(BaseModel):
    """Request to create feature flag."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    enabled: bool = Field(default=False)


class FeatureFlagResponse(BaseModel):
    """Feature flag response."""
    id: str
    name: str
    description: str
    enabled: bool
    created_at: str
    updated_at: str


# In-memory storage (replace with DB in production)
FLAGS: dict[str, FeatureFlagResponse] = {}


@router.post("", response_model=FeatureFlagResponse, status_code=201)
async def create_flag(flag: FeatureFlagCreate):
    """Create a new feature flag."""
    logger.info("creating_feature_flag", name=flag.name)

    # Validate unique name
    if any(f.name == flag.name for f in FLAGS.values()):
        raise HTTPException(
            status_code=409,
            detail=f"Feature flag '{flag.name}' already exists"
        )

    # Create flag
    flag_id = f"flag-{len(FLAGS) + 1}"
    now = datetime.utcnow().isoformat()

    new_flag = FeatureFlagResponse(
        id=flag_id,
        name=flag.name,
        description=flag.description,
        enabled=flag.enabled,
        created_at=now,
        updated_at=now
    )

    FLAGS[flag_id] = new_flag
    logger.info("feature_flag_created", flag_id=flag_id, name=flag.name)

    # Emit WebSocket event
    await emit_flag_event("created", new_flag)

    return new_flag


@router.get("", response_model=List[FeatureFlagResponse])
async def list_flags():
    """List all feature flags."""
    return list(FLAGS.values())


@router.patch("/{flag_id}/toggle", response_model=FeatureFlagResponse)
async def toggle_flag(flag_id: str):
    """Toggle feature flag enabled state."""
    if flag_id not in FLAGS:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag = FLAGS[flag_id]
    flag.enabled = not flag.enabled
    flag.updated_at = datetime.utcnow().isoformat()

    logger.info("feature_flag_toggled", flag_id=flag_id, enabled=flag.enabled)

    # Emit WebSocket event
    await emit_flag_event("toggled", flag)

    return flag


# Helper function
async def emit_flag_event(action: str, flag: FeatureFlagResponse):
    """Emit feature flag event via WebSocket."""
    from gao_dev.web.event_bus import event_bus
    from gao_dev.web.events import WebEvent, EventType

    await event_bus.publish(WebEvent(
        type=getattr(EventType, f"FEATURE_FLAG_{action.upper()}"),
        data={
            "flag_id": flag.id,
            "name": flag.name,
            "enabled": flag.enabled,
            "action": action
        }
    ))
```

### Register Router

**File**: `gao_dev/web/server.py`

```python
# Add import
from gao_dev.web.api import feature_flags as feature_flags_router

# In create_app()
app.include_router(feature_flags_router.router)
```

---

## 2. Frontend Components (React + TypeScript)

### TypeScript Types

**File**: `gao_dev/web/frontend/src/types/index.ts`

```typescript
export interface FeatureFlag {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateFeatureFlagRequest {
  name: string;
  description?: string;
  enabled?: boolean;
}
```

### API Client

**File**: `gao_dev/web/frontend/src/lib/api.ts`

```typescript
import type { FeatureFlag, CreateFeatureFlagRequest } from '../types';

export async function createFeatureFlag(
  token: string,
  data: CreateFeatureFlagRequest
): Promise<FeatureFlag> {
  const response = await fetch('/api/feature-flags', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-Token': token,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create feature flag');
  }

  return response.json();
}

export async function listFeatureFlags(token: string): Promise<FeatureFlag[]> {
  const response = await fetch('/api/feature-flags', {
    headers: { 'X-Session-Token': token },
  });

  if (!response.ok) {
    throw new Error('Failed to list feature flags');
  }

  return response.json();
}

export async function toggleFeatureFlag(
  token: string,
  flagId: string
): Promise<FeatureFlag> {
  const response = await fetch(`/api/feature-flags/${flagId}/toggle`, {
    method: 'PATCH',
    headers: { 'X-Session-Token': token },
  });

  if (!response.ok) {
    throw new Error('Failed to toggle feature flag');
  }

  return response.json();
}
```

### Zustand Store

**File**: `gao_dev/web/frontend/src/stores/featureFlagStore.ts`

```typescript
import { create } from 'zustand';
import type { FeatureFlag } from '../types';

interface FeatureFlagState {
  flags: FeatureFlag[];
  isLoading: boolean;
  error: string | null;

  addFlag: (flag: FeatureFlag) => void;
  updateFlag: (id: string, updates: Partial<FeatureFlag>) => void;
  removeFlag: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearFlags: () => void;
}

export const useFeatureFlagStore = create<FeatureFlagState>((set) => ({
  flags: [],
  isLoading: false,
  error: null,

  addFlag: (flag) =>
    set((state) => ({
      flags: [...state.flags, flag],
    })),

  updateFlag: (id, updates) =>
    set((state) => ({
      flags: state.flags.map((f) => (f.id === id ? { ...f, ...updates } : f)),
    })),

  removeFlag: (id) =>
    set((state) => ({
      flags: state.flags.filter((f) => f.id !== id),
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearFlags: () => set({ flags: [], error: null }),
}));
```

### React Component

**File**: `gao_dev/web/frontend/src/components/feature-flags/FeatureFlagCard.tsx`

```typescript
import { formatDistanceToNow } from 'date-fns';
import { ToggleLeft, ToggleRight } from 'lucide-react';
import type { FeatureFlag } from '../../types';

interface FeatureFlagCardProps {
  flag: FeatureFlag;
  onToggle: (id: string) => void;
}

export function FeatureFlagCard({ flag, onToggle }: FeatureFlagCardProps) {
  const timeAgo = formatDistanceToNow(new Date(flag.updated_at), {
    addSuffix: true,
  });

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold">{flag.name}</h3>
          {flag.description && (
            <p className="mt-1 text-sm text-muted-foreground">
              {flag.description}
            </p>
          )}
          <p className="mt-2 text-xs text-muted-foreground">
            Updated {timeAgo}
          </p>
        </div>

        <button
          onClick={() => onToggle(flag.id)}
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            flag.enabled
              ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-100'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
          }`}
          aria-label={flag.enabled ? 'Disable flag' : 'Enable flag'}
        >
          {flag.enabled ? (
            <>
              <ToggleRight className="h-4 w-4" />
              Enabled
            </>
          ) : (
            <>
              <ToggleLeft className="h-4 w-4" />
              Disabled
            </>
          )}
        </button>
      </div>
    </div>
  );
}
```

---

## 3. WebSocket Events

### Add Event Types

**File**: `gao_dev/web/events.py`

```python
class EventType(str, Enum):
    # ... existing events ...

    # Feature flag events
    FEATURE_FLAG_CREATED = "feature_flag.created"
    FEATURE_FLAG_TOGGLED = "feature_flag.toggled"
    FEATURE_FLAG_DELETED = "feature_flag.deleted"
```

### Handle Events in Frontend

**File**: `gao_dev/web/frontend/src/lib/websocket.ts`

```typescript
// In handleMessage function
case 'feature_flag.created':
  useFeatureFlagStore.getState().addFlag(event.data);
  break;

case 'feature_flag.toggled':
  useFeatureFlagStore.getState().updateFlag(event.data.flag_id, {
    enabled: event.data.enabled,
    updated_at: event.data.updated_at,
  });
  break;

case 'feature_flag.deleted':
  useFeatureFlagStore.getState().removeFlag(event.data.flag_id);
  break;
```

---

## 4. Testing

### Backend Tests

**File**: `tests/web/api/test_feature_flags.py`

```python
"""Tests for feature flags API."""
import pytest
from fastapi.testclient import TestClient


class TestFeatureFlagsAPI:
    """Test suite for feature flags API."""

    def test_create_flag_success(self, client):
        """Test creating feature flag."""
        response = client.post(
            "/api/feature-flags",
            json={
                "name": "test-flag",
                "description": "Test flag",
                "enabled": False
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-flag"
        assert data["enabled"] is False

    def test_create_duplicate_flag(self, client):
        """Test creating duplicate flag fails."""
        client.post(
            "/api/feature-flags",
            json={"name": "duplicate", "enabled": False}
        )

        response = client.post(
            "/api/feature-flags",
            json={"name": "duplicate", "enabled": False}
        )

        assert response.status_code == 409

    def test_toggle_flag(self, client):
        """Test toggling feature flag."""
        # Create flag
        create_resp = client.post(
            "/api/feature-flags",
            json={"name": "toggle-test", "enabled": False}
        )
        flag_id = create_resp.json()["id"]

        # Toggle
        toggle_resp = client.patch(f"/api/feature-flags/{flag_id}/toggle")

        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["enabled"] is True
```

### Frontend Tests

**File**: `src/components/feature-flags/FeatureFlagCard.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FeatureFlagCard } from './FeatureFlagCard';

describe('FeatureFlagCard', () => {
  const mockFlag = {
    id: '1',
    name: 'Test Flag',
    description: 'Test description',
    enabled: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  it('renders flag details', () => {
    render(<FeatureFlagCard flag={mockFlag} onToggle={() => {}} />);

    expect(screen.getByText('Test Flag')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('calls onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(<FeatureFlagCard flag={mockFlag} onToggle={onToggle} />);

    const toggleButton = screen.getByRole('button');
    fireEvent.click(toggleButton);

    expect(onToggle).toHaveBeenCalledWith('1');
  });

  it('shows correct state for enabled flag', () => {
    const enabledFlag = { ...mockFlag, enabled: true };
    render(<FeatureFlagCard flag={enabledFlag} onToggle={() => {}} />);

    expect(screen.getByText('Enabled')).toBeInTheDocument();
  });
});
```

---

## Summary

This complete example demonstrates:

✅ **Backend**: FastAPI router with Pydantic validation
✅ **Frontend**: React components with TypeScript
✅ **State**: Zustand store for state management
✅ **Real-time**: WebSocket events for live updates
✅ **Testing**: Comprehensive tests for both sides
✅ **Error Handling**: Validation and error responses
✅ **Type Safety**: Full TypeScript + Python type hints

**Time to Implement**: 2-4 hours for experienced developer

**See Also**:
- [Adding Web Features Guide](../developers/ADDING_WEB_FEATURES.md)
- [Testing Guide](../developers/TESTING_GUIDE.md)
- [API Reference](../API_REFERENCE.md)
