# Developer Guide: Testing GAO-Dev

## TL;DR

**What**: Comprehensive testing patterns and strategies for GAO-Dev development

**When**: Before committing code, during development, for CI/CD

**Key Points**:
- **Backend**: pytest + TestClient (400+ tests, >80% coverage)
- **Frontend**: Vitest + React Testing Library
- **Integration**: End-to-end workflow testing
- **Quality**: TDD recommended, all PRs require tests

**Test Command**: `pytest --cov=gao_dev tests/`

---

## Table of Contents

- [Overview](#overview)
- [Testing Stack](#testing-stack)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [Workflow Testing](#workflow-testing)
- [Agent Testing](#agent-testing)
- [Best Practices](#best-practices)

---

## Overview

### Testing Philosophy

**GAO-Dev follows Test-Driven Development (TDD)**:
1. Write test first (defines behavior)
2. Implement feature
3. Refactor with confidence

**Quality Standards**:
- Minimum 80% code coverage
- All public APIs must have tests
- All bug fixes must include regression test
- Integration tests for critical paths

---

## Testing Stack

### Backend

| Tool | Purpose | Usage |
|------|---------|-------|
| **pytest** | Test framework | `pytest tests/` |
| **pytest-cov** | Coverage reporting | `pytest --cov=gao_dev` |
| **pytest-asyncio** | Async test support | `@pytest.mark.asyncio` |
| **FastAPI TestClient** | API endpoint testing | `client = TestClient(app)` |
| **pytest-mock** | Mocking | `mocker.patch()` |
| **structlog** testing | Log assertion | `caplog.records` |

### Frontend

| Tool | Purpose | Usage |
|------|---------|-------|
| **Vitest** | Test runner | `npm test` |
| **React Testing Library** | Component testing | `render()`, `screen` |
| **@testing-library/user-event** | User interaction | `user.click()` |
| **msw** | API mocking | Mock Service Worker |

---

## Backend Testing

### Unit Test Pattern

**File**: `tests/web/api/test_feature.py`

```python
"""Tests for feature API endpoints."""
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
    """Create FastAPI test client."""
    app = create_app(test_config)
    return TestClient(app)


class TestFeatureAPI:
    """Test suite for feature API."""

    def test_create_item_success(self, client):
        """Test creating item successfully."""
        response = client.post(
            "/api/feature/items",
            json={"name": "Test", "value": 42}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test"
        assert data["value"] == 42

    def test_create_item_validation_error(self, client):
        """Test validation error handling."""
        response = client.post(
            "/api/feature/items",
            json={"name": ""}  # Invalid empty name
        )

        assert response.status_code == 400
        assert "name" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_async_operation(self, client):
        """Test async endpoint operation."""
        # Async test example
        result = await some_async_function()
        assert result.success
```

### Testing with Mocks

```python
"""Test with mocked dependencies."""
from unittest.mock import patch, MagicMock


def test_with_mock_service(client, mocker):
    """Test endpoint with mocked service layer."""
    # Mock the service call
    mock_service = mocker.patch('gao_dev.services.feature_service.FeatureService')
    mock_instance = mock_service.return_value
    mock_instance.create_item.return_value = {"id": "123", "name": "Test"}

    response = client.post(
        "/api/feature/items",
        json={"name": "Test"}
    )

    assert response.status_code == 200
    mock_instance.create_item.assert_called_once()
```

### Testing WebSocket Events

```python
"""Test WebSocket event emission."""
import pytest
from gao_dev.web.event_bus import EventBus
from gao_dev.web.events import WebEvent, EventType


@pytest.mark.asyncio
async def test_event_emission():
    """Test event is emitted correctly."""
    event_bus = EventBus()
    received_events = []

    async def collector(event: WebEvent):
        received_events.append(event)

    event_bus.subscribe(collector)

    # Emit event
    await event_bus.publish(WebEvent(
        type=EventType.FILE_CREATED,
        data={"path": "test.md"}
    ))

    assert len(received_events) == 1
    assert received_events[0].type == EventType.FILE_CREATED
    assert received_events[0].data["path"] == "test.md"
```

---

## Frontend Testing

### Component Test Pattern

**File**: `src/components/Feature/FeatureCard.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FeatureCard } from './FeatureCard';
import type { Feature } from '../../types';

describe('FeatureCard', () => {
  const mockFeature: Feature = {
    id: '1',
    name: 'Test Feature',
    description: 'Test description',
    created_at: new Date().toISOString(),
  };

  it('renders feature details', () => {
    render(<FeatureCard feature={mockFeature} />);

    expect(screen.getByText('Test Feature')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('calls onDelete when delete clicked', () => {
    const onDelete = vi.fn();
    render(<FeatureCard feature={mockFeature} onDelete={onDelete} />);

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith('1');
  });

  it('handles missing description', () => {
    const featureNoDesc = { ...mockFeature, description: undefined };
    render(<FeatureCard feature={featureNoDesc} />);

    expect(screen.queryByText('Test description')).not.toBeInTheDocument();
  });
});
```

### Testing Zustand Stores

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useFeatureStore } from './featureStore';
import type { Feature } from '../types';

describe('featureStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useFeatureStore.setState({ items: [], selectedItem: null });
  });

  it('adds item to store', () => {
    const item: Feature = {
      id: '1',
      name: 'Test',
      description: 'Test',
      created_at: new Date().toISOString(),
    };

    useFeatureStore.getState().addItem(item);

    const state = useFeatureStore.getState();
    expect(state.items).toHaveLength(1);
    expect(state.items[0]).toEqual(item);
  });

  it('removes item from store', () => {
    const item: Feature = { id: '1', name: 'Test', created_at: '' };
    useFeatureStore.setState({ items: [item] });

    useFeatureStore.getState().removeItem('1');

    expect(useFeatureStore.getState().items).toHaveLength(0);
  });
});
```

### Testing with API Mocks (MSW)

```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { beforeAll, afterAll, afterEach } from 'vitest';

const server = setupServer(
  rest.get('/api/feature/items', (req, res, ctx) => {
    return res(
      ctx.json([
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' },
      ])
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

it('fetches items from API', async () => {
  const items = await fetchItems('token');
  expect(items).toHaveLength(2);
});
```

---

## Integration Testing

### E2E Workflow Test

```python
"""tests/integration/test_workflow_execution.py"""
import pytest
from pathlib import Path
from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.core.workflow_executor import WorkflowExecutor


@pytest.mark.integration
def test_prd_workflow_execution(tmp_path):
    """Test complete PRD creation workflow."""
    # Setup
    orchestrator = GAODevOrchestrator(project_root=tmp_path)
    executor = WorkflowExecutor()

    # Execute workflow
    result = executor.execute(
        workflow_name="prd",
        variables={
            "project_name": "Test Project",
            "prd_location": str(tmp_path / "docs" / "PRD.md")
        }
    )

    # Assertions
    assert result.success, f"Workflow failed: {result.error}"
    assert (tmp_path / "docs" / "PRD.md").exists()

    # Verify content
    content = (tmp_path / "docs" / "PRD.md").read_text()
    assert "Test Project" in content
    assert "Executive Summary" in content
```

### Multi-Agent Integration Test

```python
"""Test multi-agent collaboration."""
@pytest.mark.integration
async def test_brian_to_john_workflow(tmp_path):
    """Test Brian → John workflow coordination."""
    orchestrator = GAODevOrchestrator(project_root=tmp_path)

    # Brian selects workflow
    brian_result = await orchestrator.brian.select_workflow(
        prompt="Create a PRD for todo app",
        project_context={"type": "greenfield"}
    )

    assert brian_result.selected_workflow == "prd"

    # John executes workflow
    john_result = await orchestrator.john.execute_workflow(
        workflow_name=brian_result.selected_workflow,
        variables=brian_result.variables
    )

    assert john_result.success
    assert Path(john_result.output_file).exists()
```

---

## Workflow Testing

### Testing Workflow Discovery

```python
"""tests/core/test_workflow_registry.py"""
from gao_dev.core.workflow_registry import WorkflowRegistry


def test_workflow_discovery():
    """Test workflows are discovered from directories."""
    registry = WorkflowRegistry(config_loader)
    registry.index_workflows()

    workflows = registry.list_workflows()
    assert len(workflows) > 50  # We have 55+ workflows

    # Verify specific workflow
    prd_workflow = registry.get_workflow("prd")
    assert prd_workflow is not None
    assert prd_workflow.phase == 2
    assert prd_workflow.author == "John (Product Manager)"
```

### Testing Variable Resolution

```python
"""Test workflow variable resolution."""
def test_variable_resolution():
    """Test variables resolve in correct priority order."""
    executor = WorkflowExecutor()

    # Runtime params > workflow defaults > config defaults
    result = executor.resolve_variables(
        workflow_name="prd",
        runtime_params={"prd_location": "/custom/path.md"},
        workflow_defaults={"prd_location": "docs/PRD.md"},
        config_defaults={"prd_location": "default.md"}
    )

    assert result["prd_location"] == "/custom/path.md"
```

---

## Agent Testing

### Unit Test for Agent

```python
"""tests/agents/test_diana.py"""
import pytest
from gao_dev.agents.diana import DianaAgent


@pytest.fixture
def diana(tmp_path):
    """Create Diana agent for testing."""
    config = {
        "name": "Diana",
        "role": "Document Keeper",
        "tools": ["read_file", "write_file"],
    }
    return DianaAgent(config=config, project_root=tmp_path)


def test_diana_reviews_documentation(diana, tmp_path):
    """Test Diana can review documentation."""
    # Create test doc
    test_doc = tmp_path / "test.md"
    test_doc.write_text("# Test\nNo TL;DR section\n" * 100)

    # Execute review
    result = diana.review_documentation(test_doc)

    assert result.success
    assert "TL;DR" in result.issues  # Should flag missing TL;DR
```

---

## Best Practices

### 1. Test Organization

```
tests/
├── unit/                # Unit tests (fast, isolated)
│   ├── core/
│   ├── services/
│   └── web/
├── integration/         # Integration tests (slower, multi-component)
│   ├── workflows/
│   └── agents/
└── e2e/                # End-to-end tests (slowest, full system)
    └── scenarios/
```

### 2. Naming Conventions

```python
# Test files: test_{module}.py
# Test classes: Test{Feature}
# Test methods: test_{feature}_{scenario}

def test_create_item_with_valid_data():
    """Test creating item with valid data."""
    pass

def test_create_item_with_invalid_data():
    """Test validation error with invalid data."""
    pass
```

### 3. Fixtures

```python
# Reusable fixtures in conftest.py
@pytest.fixture
def test_config(tmp_path):
    """Test configuration fixture."""
    return WebConfig(...)

@pytest.fixture
def mock_event_bus(mocker):
    """Mock event bus for isolated testing."""
    return mocker.patch('gao_dev.web.event_bus.event_bus')
```

### 4. Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("valid", True),
    ("", False),
    (None, False),
])
def test_validation(input, expected):
    """Test validation with various inputs."""
    result = validate(input)
    assert result == expected
```

### 5. Coverage Goals

```bash
# Run with coverage
pytest --cov=gao_dev --cov-report=html tests/

# View coverage
open htmlcov/index.html

# Fail if below threshold
pytest --cov=gao_dev --cov-fail-under=80
```

---

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gao_dev --cov-report=term-missing

# Run specific test file
pytest tests/web/api/test_feature.py

# Run specific test
pytest tests/web/api/test_feature.py::test_create_item
```

### Test Markers

```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run unit tests only
pytest tests/unit/
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=gao_dev --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## See Also

- [Quick Start Guide](../QUICK_START.md) - Testing examples
- [CLAUDE.md](../../CLAUDE.md#development-patterns) - TDD workflow
- [pytest documentation](https://docs.pytest.org/)
- [Vitest documentation](https://vitest.dev/)

**Estimated tokens**: ~2,350
