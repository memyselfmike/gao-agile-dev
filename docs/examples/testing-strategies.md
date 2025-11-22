# Testing Strategies

Real test examples extracted from GAO-Dev codebase.

---

## 1. Testing Async Endpoints

**Context**: Testing FastAPI async endpoints with database operations

**Example from**: `tests/web/api/test_git_endpoints.py`

```python
import pytest
from pathlib import Path


@pytest.fixture
def git_repo(tmp_path):
    """Create temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Initialize git
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path)

    # Create initial commit
    (repo_path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_path, check=True)

    return repo_path


@pytest.mark.asyncio
async def test_get_commits(client, git_repo):
    """Test fetching commits from git repository."""
    response = client.get(
        "/api/git/commits",
        params={"limit": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert "commits" in data
    assert len(data["commits"]) > 0
```

---

## 2. Testing WebSocket Events

**Context**: Verifying WebSocket event emission and handling

**Example from**: `tests/web/test_event_bus.py`

```python
import pytest
from gao_dev.web.event_bus import EventBus
from gao_dev.web.events import WebEvent, EventType


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    """Test event bus publish/subscribe pattern."""
    event_bus = EventBus()
    received_events = []

    # Subscriber
    async def collector(event: WebEvent):
        received_events.append(event)

    event_bus.subscribe(collector)

    # Publish multiple events
    await event_bus.publish(WebEvent(
        type=EventType.FILE_CREATED,
        data={"path": "test.md"}
    ))

    await event_bus.publish(WebEvent(
        type=EventType.FILE_MODIFIED,
        data={"path": "test.md"}
    ))

    # Verify
    assert len(received_events) == 2
    assert received_events[0].type == EventType.FILE_CREATED
    assert received_events[1].type == EventType.FILE_MODIFIED
```

---

## 3. Testing with Mocked Dependencies

**Context**: Isolating tests by mocking external services

**Example from**: `tests/web/adapters/test_brian_adapter.py`

```python
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_brian_adapter_with_mock(mocker):
    """Test Brian adapter with mocked LLM provider."""
    # Mock the LLM provider
    mock_provider = mocker.patch('gao_dev.core.providers.anthropic.AnthropicProvider')
    mock_instance = mock_provider.return_value

    # Setup mock response
    mock_instance.send_message = AsyncMock(return_value={
        "content": "Test response",
        "role": "assistant"
    })

    # Test adapter
    from gao_dev.web.adapters.brian_adapter import BrianWebAdapter

    adapter = BrianWebAdapter()
    response = await adapter.process_message("Test message")

    # Verify
    assert response["content"] == "Test response"
    mock_instance.send_message.assert_called_once()
```

---

## 4. Parametrized Testing

**Context**: Testing multiple scenarios with same test logic

**Example from**: `tests/core/test_workflow_registry.py`

```python
@pytest.mark.parametrize("workflow_name,expected_phase", [
    ("prd", 2),
    ("architecture", 3),
    ("create-story", 4),
    ("planning-ceremony", 5),
])
def test_workflow_phases(workflow_registry, workflow_name, expected_phase):
    """Test workflows are in correct phases."""
    workflow = workflow_registry.get_workflow(workflow_name)

    assert workflow is not None, f"Workflow '{workflow_name}' not found"
    assert workflow.phase == expected_phase


@pytest.mark.parametrize("input,expected_valid", [
    ("valid_name", True),
    ("", False),
    ("a" * 200, False),  # Too long
    ("name with spaces", True),
    (None, False),
])
def test_name_validation(input, expected_valid):
    """Test name validation with various inputs."""
    result = validate_name(input)
    assert result == expected_valid
```

---

## 5. Testing State Transitions

**Context**: Testing complex state machine logic

**Example from**: `tests/core/test_story_lifecycle.py`

```python
def test_story_state_transitions(story_lifecycle, tmp_path):
    """Test valid story state transitions."""
    # Create story
    story = story_lifecycle.create_story(
        epic_num=1,
        story_num=1,
        title="Test Story"
    )

    assert story.status == "backlog"

    # Transition to ready
    story_lifecycle.transition_story(1, 1, "ready")
    updated = story_lifecycle.get_story(1, 1)
    assert updated.status == "ready"

    # Transition to in_progress
    story_lifecycle.transition_story(1, 1, "in_progress")
    updated = story_lifecycle.get_story(1, 1)
    assert updated.status == "in_progress"

    # Invalid transition should fail
    with pytest.raises(ValueError, match="Invalid transition"):
        story_lifecycle.transition_story(1, 1, "backlog")  # Can't go backward
```

---

## 6. Integration Testing

**Context**: Testing multiple components working together

**Example from**: `tests/integration/test_workflow_execution.py`

```python
@pytest.mark.integration
def test_end_to_end_prd_workflow(tmp_path):
    """Test complete PRD creation workflow."""
    from gao_dev.orchestrator import GAODevOrchestrator

    # Setup
    orchestrator = GAODevOrchestrator(project_root=tmp_path)

    # Execute workflow
    result = orchestrator.execute_workflow(
        workflow_name="prd",
        variables={
            "project_name": "Test Project",
            "prd_location": str(tmp_path / "docs" / "PRD.md")
        }
    )

    # Verify workflow success
    assert result.success, f"Workflow failed: {result.error}"

    # Verify output file created
    prd_file = tmp_path / "docs" / "PRD.md"
    assert prd_file.exists()

    # Verify content
    content = prd_file.read_text()
    assert "Test Project" in content
    assert "Executive Summary" in content
    assert "Success Metrics" in content
```

---

## 7. Testing React Components

**Context**: Testing frontend components with user interactions

**Example from**: `src/components/chat/ChatMessage.test.tsx`

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatMessage } from './ChatMessage';

describe('ChatMessage', () => {
  it('renders user message correctly', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hello',
      timestamp: Date.now(),
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByText('You')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders markdown in agent responses', () => {
    const message = {
      id: '2',
      role: 'agent' as const,
      content: '# Heading\n\nParagraph with **bold**',
      timestamp: Date.now(),
    };

    render(<ChatMessage message={message} />);

    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    expect(screen.getByText('bold')).toBeInTheDocument();
  });

  it('hides reasoning by default', () => {
    const message = {
      id: '3',
      role: 'agent' as const,
      content: 'Response <thinking>Internal thoughts</thinking>',
      timestamp: Date.now(),
    };

    render(<ChatMessage message={message} showReasoning={false} />);

    expect(screen.queryByText('Internal thoughts')).not.toBeInTheDocument();
  });
});
```

---

## Key Takeaways

1. **Use fixtures** for reusable test setup
2. **Mock external dependencies** for isolation
3. **Parametrize** to test multiple scenarios efficiently
4. **Test state transitions** explicitly
5. **Integration tests** verify components work together
6. **Frontend tests** use React Testing Library patterns

**See Also**:
- [Testing Guide](../developers/TESTING_GUIDE.md) - Complete testing documentation
- [Quick Start](../QUICK_START.md) - Testing examples
