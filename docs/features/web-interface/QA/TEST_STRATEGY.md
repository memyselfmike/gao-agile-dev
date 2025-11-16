# Test Strategy: Epic 39 - Web Interface

**Feature**: Browser-Based Web Interface for GAO-Dev
**Epic Number**: 39
**Test Architect**: Murat
**Version**: 1.0
**Last Updated**: 2025-01-16
**Status**: Ready for Implementation

---

## Executive Summary

This document defines the comprehensive testing strategy for Epic 39 across all 8 testing levels: linting, unit testing, integration testing, regression testing, E2E testing (AI-powered via Playwright MCP), performance testing, accessibility testing, and security testing.

### Key Testing Principles

1. **Risk-Based Testing**: Testing depth scales with impact. Critical paths (chat, file editing, WebSocket) receive comprehensive coverage.
2. **AI as Beta Tester**: Claude Code via Playwright MCP performs E2E testing, finding real UX issues.
3. **Test Pyramid**: Many unit tests (70%), fewer integration tests (20%), minimal E2E tests (10%).
4. **ATDD Approach**: Acceptance tests written before implementation, defining "done" criteria.
5. **Continuous Testing**: All tests run in CI/CD pipeline with quality gates.
6. **Cross-Platform**: Tests run on Windows, macOS, Linux.

### Coverage Targets

| Test Level | Target Coverage | Rationale |
|-----------|----------------|-----------|
| **Linting** | 100% files | Code quality baseline |
| **Unit Tests** | >85% business logic | High confidence in core functionality |
| **Integration Tests** | >80% critical paths | Validate component interactions |
| **Regression Tests** | 100% critical user flows | Zero breaking changes |
| **E2E Tests** | 14 scenarios (all phases) | End-to-end validation by AI |
| **Performance Tests** | All 8 metrics (P95) | Performance benchmarks met |
| **Accessibility** | 100% WCAG 2.1 AA | Full accessibility compliance |
| **Security** | 100% attack vectors | No security vulnerabilities |

---

## Table of Contents

1. [Test Strategy Overview](#test-strategy-overview)
2. [Level 1: Linting and Code Quality](#level-1-linting-and-code-quality)
3. [Level 2: Unit Testing](#level-2-unit-testing)
4. [Level 3: Integration Testing](#level-3-integration-testing)
5. [Level 4: Regression Testing](#level-4-regression-testing)
6. [Level 5: E2E Testing (Playwright MCP)](#level-5-e2e-testing-playwright-mcp)
7. [Level 6: Performance Testing](#level-6-performance-testing)
8. [Level 7: Accessibility Testing](#level-7-accessibility-testing)
9. [Level 8: Security Testing](#level-8-security-testing)
10. [Test Environment Strategy](#test-environment-strategy)
11. [CI/CD Pipeline Integration](#cicd-pipeline-integration)
12. [Story-Level Test Plans](#story-level-test-plans)
13. [Quality Gates](#quality-gates)
14. [Tools and Frameworks](#tools-and-frameworks)
15. [Metrics and Reporting](#metrics-and-reporting)

---

## Test Strategy Overview

### Test Pyramid Distribution

```
      /\        E2E Tests (14 scenarios, ~10%)
     /  \       - Playwright MCP (AI-driven)
    /    \      - Critical user journeys
   /      \     - Cross-browser validation
  /________\
   /      \     Integration Tests (~20%)
  /        \    - API + WebSocket + Frontend
 /          \   - Component integration
/__________  \  - Real-time event flow
  /        \
 /          \   Unit Tests (~70%)
/____________\  - Component tests (React)
                - Service tests (Python)
                - Utility tests
```

### Testing Philosophy

**1. Test Early, Test Often**:
- Write acceptance tests before implementation (ATDD)
- Run unit tests on every code change
- Run full suite on every PR

**2. Fast Feedback**:
- Unit tests: <1ms per test (400+ tests in <5s)
- Integration tests: <100ms per test
- E2E tests: <30s per scenario

**3. Realistic Testing**:
- Use real databases (SQLite) in integration tests
- Use real WebSocket connections
- Use real browser (Chromium) in E2E tests
- Mock only external services (Anthropic API)

**4. AI-Testable by Design**:
- Semantic HTML (button, nav, main)
- Stable data-testid attributes
- ARIA labels for context
- Clear state indicators (data-state)

---

## Level 1: Linting and Code Quality

### Frontend Linting (React/TypeScript)

**Tools**:
- **ESLint** (JavaScript/TypeScript linting)
- **Prettier** (code formatting)
- **TypeScript** (strict type checking)
- **eslint-plugin-jsx-a11y** (accessibility linting)
- **eslint-plugin-react-hooks** (React Hooks rules)

**ESLint Configuration** (`.eslintrc.js`):
```javascript
module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'prettier',
  ],
  plugins: ['@typescript-eslint', 'react', 'react-hooks', 'jsx-a11y'],
  rules: {
    // TypeScript strict mode
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': 'error',

    // React best practices
    'react/prop-types': 'off', // Using TypeScript
    'react/react-in-jsx-scope': 'off', // React 18
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',

    // Accessibility
    'jsx-a11y/anchor-is-valid': 'error',
    'jsx-a11y/click-events-have-key-events': 'error',
    'jsx-a11y/no-static-element-interactions': 'error',

    // General
    'no-console': 'warn',
    'prefer-const': 'error',
  },
  settings: {
    react: { version: 'detect' },
  },
};
```

**TypeScript Configuration** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "jsx": "react-jsx",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

**Prettier Configuration** (`.prettierrc`):
```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "always"
}
```

### Backend Linting (Python/FastAPI)

**Tools**:
- **Ruff** (fast Python linter, replaces flake8)
- **Black** (code formatting)
- **MyPy** (strict type checking)
- **isort** (import sorting)
- **Bandit** (security linting)

**Ruff Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports
"tests/**/*.py" = ["ARG001"]  # Unused arguments in fixtures
```

**Black Configuration** (already in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ["py311"]
```

**MyPy Configuration** (`pyproject.toml` - enhanced):
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true  # STRICT MODE for web interface
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_unreachable = true
strict_equality = true

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false  # Relaxed for tests
```

**isort Configuration** (`pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true
```

### Pre-Commit Hooks

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  # Frontend hooks
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        types: [file]
        additional_dependencies:
          - eslint@8.56.0
          - '@typescript-eslint/parser@6.18.0'
          - '@typescript-eslint/eslint-plugin@6.18.0'
          - 'eslint-plugin-react@7.33.2'
          - 'eslint-plugin-react-hooks@4.6.0'
          - 'eslint-plugin-jsx-a11y@6.8.0'

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, css, scss]

  # Backend hooks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-r', 'gao_dev/web', '-ll']
        exclude: tests/

  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
```

### Linting Quality Gates

**All PRs must pass**:
- ESLint: 0 errors, <10 warnings
- TypeScript: 0 type errors
- Ruff: 0 violations
- Black: 100% formatted
- MyPy: 0 type errors (strict mode)
- Bandit: 0 high/medium severity issues

**IDE Integration**:
- VS Code: Install ESLint, Prettier, Pylance, Ruff extensions
- Auto-fix on save enabled
- Show inline errors/warnings

---

## Level 2: Unit Testing

### Frontend Unit Tests (Vitest + React Testing Library)

**Framework**: Vitest (faster than Jest, Vite-native)

**Vitest Configuration** (`vitest.config.ts`):
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/test/**',
        'src/**/*.d.ts',
        'src/main.tsx',
      ],
      all: true,
      lines: 85,
      functions: 85,
      branches: 80,
      statements: 85,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

**Test Setup** (`src/test/setup.ts`):
```typescript
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock WebSocket
global.WebSocket = vi.fn(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
})) as any;

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

**Component Test Example** (`ChatInput.test.tsx`):
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInput } from './ChatInput';

describe('ChatInput', () => {
  it('renders input and send button', () => {
    render(<ChatInput onSend={vi.fn()} />);

    expect(screen.getByTestId('chat-input')).toBeInTheDocument();
    expect(screen.getByTestId('chat-send-button')).toBeInTheDocument();
  });

  it('enables send button when input has text', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={vi.fn()} />);

    const input = screen.getByTestId('chat-input');
    const button = screen.getByTestId('chat-send-button');

    expect(button).toBeDisabled();

    await user.type(input, 'Hello Brian');

    expect(button).toBeEnabled();
  });

  it('calls onSend with message and clears input', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const input = screen.getByTestId('chat-input');
    const button = screen.getByTestId('chat-send-button');

    await user.type(input, 'Create a PRD');
    await user.click(button);

    expect(onSend).toHaveBeenCalledWith('Create a PRD');
    expect(input).toHaveValue('');
  });

  it('disables input during loading state', () => {
    render(<ChatInput onSend={vi.fn()} isLoading={true} />);

    const input = screen.getByTestId('chat-input');
    const button = screen.getByTestId('chat-send-button');

    expect(input).toBeDisabled();
    expect(button).toBeDisabled();
  });
});
```

**Hook Test Example** (`useChatStore.test.ts`):
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatStore } from './useChatStore';

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store
    useChatStore.setState({ messages: [], activeAgent: 'brian' });
  });

  it('adds message to store', () => {
    const { result } = renderHook(() => useChatStore());

    act(() => {
      result.current.addMessage({
        id: '1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('Hello');
  });

  it('switches active agent', () => {
    const { result } = renderHook(() => useChatStore());

    act(() => {
      result.current.switchAgent('john');
    });

    expect(result.current.activeAgent).toBe('john');
  });

  it('clears messages for new agent', () => {
    const { result } = renderHook(() => useChatStore());

    // Add message for brian
    act(() => {
      result.current.addMessage({
        id: '1',
        role: 'user',
        content: 'Hello Brian',
        timestamp: new Date(),
      });
    });

    expect(result.current.messages).toHaveLength(1);

    // Switch to john
    act(() => {
      result.current.switchAgent('john');
    });

    // Messages should be cleared (per-agent history)
    expect(result.current.messages).toHaveLength(0);
  });
});
```

### Backend Unit Tests (pytest)

**Backend Test Example** (`test_web_event_bus.py`):
```python
import pytest
import asyncio
from gao_dev.web.core.event_bus import WebEventBus, WebEvent

@pytest.mark.asyncio
async def test_publish_event():
    """Test publishing event to subscribers."""
    bus = WebEventBus()
    queue = bus.subscribe("test.event")

    event = WebEvent(type="test.event", data={"message": "hello"})
    await bus.publish(event)

    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received.type == "test.event"
    assert received.data["message"] == "hello"

@pytest.mark.asyncio
async def test_multiple_subscribers():
    """Test multiple subscribers receive same event."""
    bus = WebEventBus()
    queue1 = bus.subscribe("test.event")
    queue2 = bus.subscribe("test.event")

    event = WebEvent(type="test.event", data={"id": 1})
    await bus.publish(event)

    # Both queues should receive event
    received1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    received2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

    assert received1.data["id"] == 1
    assert received2.data["id"] == 1

@pytest.mark.asyncio
async def test_buffer_overflow():
    """Test buffer overflow drops oldest event."""
    bus = WebEventBus(max_buffer=2)
    queue = bus.subscribe("test.event")

    # Publish 3 events (buffer size = 2)
    await bus.publish(WebEvent(type="test.event", data={"num": 1}))
    await bus.publish(WebEvent(type="test.event", data={"num": 2}))
    await bus.publish(WebEvent(type="test.event", data={"num": 3}))

    # Should only receive events 2 and 3 (oldest dropped)
    event1 = await queue.get()
    event2 = await queue.get()

    assert event1.data["num"] == 2
    assert event2.data["num"] == 3
```

**API Endpoint Test Example** (`test_chat_api.py`):
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from gao_dev.web.api.main import app
from gao_dev.web.api.dependencies import get_brian_adapter

@pytest.fixture
def mock_brian_adapter():
    """Mock BrianWebAdapter."""
    adapter = MagicMock()
    adapter.send_message = AsyncMock(return_value={
        "response": "Hello, how can I help?",
        "agent": "brian"
    })
    return adapter

@pytest.fixture
def client(mock_brian_adapter):
    """Test client with mocked dependencies."""
    app.dependency_overrides[get_brian_adapter] = lambda: mock_brian_adapter
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_send_chat_message(client, mock_brian_adapter):
    """Test POST /api/chat endpoint."""
    response = client.post(
        "/api/chat",
        json={"agent": "brian", "message": "Create a PRD"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello, how can I help?"
    assert data["agent"] == "brian"

    # Verify adapter called
    mock_brian_adapter.send_message.assert_called_once_with(
        agent="brian",
        message="Create a PRD"
    )

def test_chat_validation_error(client):
    """Test validation error for invalid payload."""
    response = client.post(
        "/api/chat",
        json={"message": "Missing agent field"}
    )

    assert response.status_code == 422  # Validation error
```

### Unit Test Coverage Targets

**Frontend** (85% business logic):
- All React components: >80%
- Zustand stores: >90%
- Utility functions: >95%
- Hooks: >85%

**Backend** (85% business logic):
- API endpoints: >90%
- Event bus: >95%
- Adapters: >85%
- WebSocket manager: >90%

### Test Organization

**Frontend**:
```
src/
├── components/
│   ├── ChatInput/
│   │   ├── ChatInput.tsx
│   │   ├── ChatInput.test.tsx
│   │   └── ChatInput.module.css
│   └── ActivityStream/
│       ├── ActivityStream.tsx
│       └── ActivityStream.test.tsx
├── stores/
│   ├── chatStore.ts
│   └── chatStore.test.ts
└── hooks/
    ├── useWebSocket.ts
    └── useWebSocket.test.ts
```

**Backend**:
```
gao_dev/web/
├── api/
│   ├── endpoints/
│   │   └── chat.py
│   └── tests/
│       └── test_chat.py
├── core/
│   ├── event_bus.py
│   └── tests/
│       └── test_event_bus.py
└── adapters/
    ├── brian_adapter.py
    └── tests/
        └── test_brian_adapter.py
```

---

## Level 3: Integration Testing

### Frontend Integration Tests

**Test Scenarios**:

**1. Chat Flow Integration**:
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatTab } from './ChatTab';
import { WebSocketProvider } from '@/providers/WebSocketProvider';

describe('Chat Flow Integration', () => {
  it('sends message and receives streaming response', async () => {
    const user = userEvent.setup();

    // Mock WebSocket that streams response
    const mockWs = {
      send: vi.fn(),
      addEventListener: vi.fn((event, handler) => {
        if (event === 'message') {
          // Simulate streaming chunks
          setTimeout(() => handler({ data: JSON.stringify({
            type: 'chat.chunk',
            data: { content: 'Hello' }
          })}), 100);
          setTimeout(() => handler({ data: JSON.stringify({
            type: 'chat.chunk',
            data: { content: ' there!' }
          })}), 200);
          setTimeout(() => handler({ data: JSON.stringify({
            type: 'chat.complete',
            data: {}
          })}), 300);
        }
      }),
    };

    global.WebSocket = vi.fn(() => mockWs) as any;

    render(
      <WebSocketProvider>
        <ChatTab />
      </WebSocketProvider>
    );

    // Type message
    const input = screen.getByTestId('chat-input');
    await user.type(input, 'Create a PRD');

    // Send
    const button = screen.getByTestId('chat-send-button');
    await user.click(button);

    // Verify user message displayed
    expect(screen.getByText('Create a PRD')).toBeInTheDocument();

    // Wait for streaming response
    await waitFor(() => {
      expect(screen.getByText(/Hello there!/)).toBeInTheDocument();
    }, { timeout: 500 });
  });
});
```

**2. Activity Stream Real-Time Updates**:
```typescript
describe('Activity Stream Integration', () => {
  it('receives and displays real-time events', async () => {
    const mockWs = {
      addEventListener: vi.fn((event, handler) => {
        if (event === 'message') {
          // Simulate file creation event
          setTimeout(() => handler({ data: JSON.stringify({
            type: 'file.created',
            data: {
              path: 'docs/PRD.md',
              agent: 'john',
              timestamp: new Date().toISOString()
            }
          })}), 100);
        }
      }),
    };

    global.WebSocket = vi.fn(() => mockWs) as any;

    render(
      <WebSocketProvider>
        <ActivityStream />
      </WebSocketProvider>
    );

    // Wait for event to appear
    await waitFor(() => {
      expect(screen.getByText(/john created docs\/PRD.md/)).toBeInTheDocument();
    });
  });
});
```

### Backend Integration Tests

**Test Scenarios**:

**1. ChatREPL Integration**:
```python
import pytest
from gao_dev.web.adapters.brian_adapter import BrianWebAdapter
from gao_dev.cli.chat_repl import ChatSession

@pytest.mark.asyncio
async def test_brian_adapter_chatrepl_integration(temp_dir):
    """Test BrianWebAdapter integrates with ChatREPL."""
    # Create ChatSession (Epic 30)
    session = ChatSession(project_root=temp_dir)

    # Create adapter
    adapter = BrianWebAdapter(chat_session=session)

    # Send message
    response = await adapter.send_message(
        agent="brian",
        message="What workflows are available?"
    )

    # Verify response structure
    assert "response" in response
    assert "agent" in response
    assert response["agent"] == "brian"

    # Verify session history updated
    assert len(session.history) > 0
```

**2. GitIntegratedStateManager Integration**:
```python
import pytest
from pathlib import Path
from gao_dev.web.api.endpoints.files import save_file
from gao_dev.core.state_manager import GitIntegratedStateManager

@pytest.mark.asyncio
async def test_file_save_atomic_commit(temp_dir):
    """Test file save triggers atomic file+DB+git commit."""
    # Setup state manager
    state_manager = GitIntegratedStateManager(project_root=temp_dir)

    # Save file via API
    result = await save_file(
        file_path="docs/test.md",
        content="# Test Document",
        commit_message="feat(docs): Add test document",
        state_manager=state_manager
    )

    # Verify file exists
    assert (temp_dir / "docs" / "test.md").exists()

    # Verify git commit created
    import git
    repo = git.Repo(temp_dir)
    assert len(list(repo.iter_commits())) > 0
    assert "feat(docs): Add test document" in repo.head.commit.message

    # Verify DB record created
    # (Assuming document lifecycle tracking)
    assert result["committed"] is True
```

**3. WebSocket Event Flow**:
```python
import pytest
from gao_dev.web.core.event_bus import WebEventBus
from gao_dev.web.adapters.filesystem_adapter import FileSystemAdapter
from gao_dev.web.api.websocket import WebSocketManager

@pytest.mark.asyncio
async def test_websocket_event_flow(temp_dir):
    """Test file change triggers WebSocket broadcast."""
    # Setup components
    event_bus = WebEventBus()
    fs_adapter = FileSystemAdapter(project_root=temp_dir, event_bus=event_bus)
    ws_manager = WebSocketManager(event_bus=event_bus)

    # Mock WebSocket connection
    mock_ws = MockWebSocket()
    await ws_manager.connect(mock_ws)

    # Create file (simulating agent action)
    (temp_dir / "docs" / "new.md").write_text("# New Doc")

    # FileSystemAdapter should detect and emit event
    await fs_adapter.watch()  # Trigger watch

    # WebSocketManager should broadcast
    # Wait for event
    import asyncio
    await asyncio.sleep(0.1)

    # Verify WebSocket received event
    assert len(mock_ws.sent_messages) > 0
    event = json.loads(mock_ws.sent_messages[0])
    assert event["type"] == "file.created"
    assert event["data"]["path"] == "docs/new.md"
```

### Integration Test Coverage

**Critical Paths** (>80% coverage):
- Chat message send → ChatREPL → Response stream → UI update
- File edit → GitIntegratedStateManager → Commit → WebSocket → UI update
- Kanban drag → State transition → DB update → Git commit → Broadcast
- Agent creates file → FileSystemWatcher → Event → Activity stream update

### Test Environment

**Integration tests use**:
- Real SQLite database (`.gao-dev/documents.db`)
- Real git repository (initialized in temp directory)
- Real WebSocket connections (localhost)
- Mocked Anthropic API (no real API calls)

---

## Level 4: Regression Testing

### Regression Suite

**Critical User Paths** (must not break):

**1. CLI Functionality (Zero Regressions)**:
```python
@pytest.mark.regression
def test_cli_create_prd_still_works():
    """Regression: Ensure CLI create-prd still works after web UI added."""
    from gao_dev.cli.commands import create_prd
    # Test implementation remains unchanged
    # This validates no breaking changes to existing CLI
```

**2. Existing State Manager Operations**:
```python
@pytest.mark.regression
def test_state_manager_epic_creation():
    """Regression: GitIntegratedStateManager.create_epic still works."""
    from gao_dev.core.state_manager import GitIntegratedStateManager
    # Test epic creation
    # Validates Epic 27 functionality preserved
```

**3. ChatREPL Functionality**:
```python
@pytest.mark.regression
def test_chatrepl_conversation_flow():
    """Regression: Epic 30 ChatREPL still works."""
    from gao_dev.cli.chat_repl import ChatSession
    # Test chat session
    # Validates Epic 30 functionality preserved
```

### Performance Benchmarks

**Track performance over time** (prevent regressions):

| Metric | Baseline | Threshold | Measurement |
|--------|----------|-----------|-------------|
| Page load (TTI) | <2s | <2.5s | Lighthouse |
| WebSocket connect | <100ms | <150ms | Custom timing |
| Event delivery | <10ms | <20ms | Custom timing |
| Chat response start | <200ms | <300ms | Custom timing |
| File tree render (500 files) | <300ms | <400ms | Performance API |
| Activity stream render (1000 events) | <200ms | <300ms | Performance API |

**Automated Performance Tests**:
```python
import pytest
import time
from gao_dev.web.core.event_bus import WebEventBus

@pytest.mark.performance
def test_event_bus_throughput():
    """Performance: Event bus handles 1000 events/second."""
    bus = WebEventBus()
    queue = bus.subscribe("test.event")

    start = time.perf_counter()

    # Publish 1000 events
    for i in range(1000):
        asyncio.run(bus.publish(WebEvent(type="test.event", data={"id": i})))

    end = time.perf_counter()
    duration = end - start

    # Should handle 1000 events in <1 second
    assert duration < 1.0, f"Event bus too slow: {duration:.2f}s for 1000 events"
```

### Cross-Browser Compatibility

**Test matrix**:
- Chrome 90+ (primary)
- Firefox 88+
- Safari 14+
- Edge 90+

**Automated cross-browser tests** (Playwright):
```typescript
import { test, expect, devices } from '@playwright/test';

const browsers = [
  { name: 'Chrome', device: devices['Desktop Chrome'] },
  { name: 'Firefox', device: devices['Desktop Firefox'] },
  { name: 'Safari', device: devices['Desktop Safari'] },
  { name: 'Edge', device: devices['Desktop Edge'] },
];

for (const browser of browsers) {
  test.describe(`${browser.name} compatibility`, () => {
    test.use(browser.device);

    test('chat interface works', async ({ page }) => {
      await page.goto('http://localhost:3000');
      await page.fill('[data-testid="chat-input"]', 'Hello');
      await page.click('[data-testid="chat-send-button"]');
      // Verify chat works
    });
  });
}
```

### Responsive Design Tests

**Breakpoints**:
- 1024px (minimum)
- 1440px (default)
- 1920px (large)

**Test implementation**:
```typescript
test.describe('Responsive layout', () => {
  const viewports = [
    { width: 1024, height: 768 },
    { width: 1440, height: 900 },
    { width: 1920, height: 1080 },
  ];

  for (const viewport of viewports) {
    test(`layout works at ${viewport.width}x${viewport.height}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('http://localhost:3000');

      // Verify sidebar visible
      await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();

      // Verify main content area
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    });
  }
});
```

---

## Level 5: E2E Testing (Playwright MCP)

### Playwright MCP Integration

**Critical Requirement**: Enable Claude Code to test GAO-Dev via Playwright MCP.

**Key Principles**:
1. **Semantic HTML**: All interactive elements use proper HTML tags
2. **Stable Selectors**: `data-testid` attributes on all interactive elements
3. **ARIA Labels**: Context for screen readers and AI agents
4. **State Indicators**: `data-state` attributes (loading, error, success)

### E2E Test Scenarios (14 Total)

**Phase 1: MVP (6 scenarios)**

**Scenario 1: Server Startup**
```typescript
import { test, expect } from '@playwright/test';

test('MVP-1: Server startup and accessibility', async ({ page }) => {
  // Given: Server is not running
  // When: User runs `gao-dev start --web`
  // (Server starts externally, this test connects to it)

  // Navigate to localhost:3000
  await page.goto('http://localhost:3000');

  // Then: Page loads successfully
  await expect(page).toHaveTitle(/GAO-Dev/);

  // Verify main interface visible
  await expect(page.locator('[data-testid="main-layout"]')).toBeVisible();

  // Verify sidebar navigation
  await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();

  // Verify default tab (Chat) is active
  await expect(page.locator('[data-testid="tab-chat"]')).toHaveAttribute(
    'data-state',
    'active'
  );
});
```

**Scenario 2: Chat Flow**
```typescript
test('MVP-2: Send message to Brian and receive response', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Chat tab is active
  await page.click('[data-testid="tab-chat"]');

  // When: User types message
  const input = page.locator('[data-testid="chat-input"]');
  await input.fill('Create a PRD for user authentication');

  // And: User clicks send
  await page.click('[data-testid="chat-send-button"]');

  // Then: User message appears
  await expect(page.locator('[data-testid="chat-message-user"]').last())
    .toContainText('Create a PRD for user authentication');

  // And: Brian's response streams in
  await expect(page.locator('[data-testid="chat-message-brian"]').last())
    .toBeVisible({ timeout: 5000 });

  // And: Response contains expected content
  await expect(page.locator('[data-testid="chat-message-brian"]').last())
    .toContainText(/PRD|Product Requirements|authentication/i);
});
```

**Scenario 3: Activity Stream**
```typescript
test('MVP-3: Activity stream shows real-time events', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Activity stream tab is open
  await page.click('[data-testid="tab-activity"]');

  // When: Workflow is triggered (via chat or CLI)
  // (Assuming CLI running in background creates events)

  // Then: Events appear in activity stream
  await expect(page.locator('[data-testid="activity-event"]').first())
    .toBeVisible({ timeout: 3000 });

  // And: Event shows agent name
  await expect(page.locator('[data-testid="activity-event-agent"]').first())
    .toBeVisible();

  // And: Event shows timestamp
  await expect(page.locator('[data-testid="activity-event-timestamp"]').first())
    .toBeVisible();
});
```

**Scenario 4: File Tree and Monaco Editor**
```typescript
test('MVP-4: Browse file tree and view file in Monaco', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Files tab is active
  await page.click('[data-testid="tab-files"]');

  // When: User clicks on a file in tree
  await page.click('[data-testid="file-tree-item"][data-path="docs/PRD.md"]');

  // Then: Monaco editor opens
  await expect(page.locator('[data-testid="monaco-editor"]')).toBeVisible();

  // And: File content is displayed
  await expect(page.locator('.monaco-editor')).toBeVisible();

  // And: File path shown in breadcrumb
  await expect(page.locator('[data-testid="file-breadcrumb"]'))
    .toContainText('docs/PRD.md');
});
```

**Scenario 5: Read-Only Mode**
```typescript
test('MVP-5: Read-only mode when CLI active', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: CLI is running (holds write lock)
  // (Simulated by creating .gao-dev/session.lock file)

  // When: Page loads
  // Then: Read-only banner is visible
  await expect(page.locator('[data-testid="read-only-banner"]'))
    .toBeVisible();

  // And: Banner contains informative message
  await expect(page.locator('[data-testid="read-only-banner"]'))
    .toContainText(/Read-only mode|CLI is active/i);

  // And: Write controls are disabled
  await expect(page.locator('[data-testid="chat-send-button"]'))
    .toBeDisabled();

  // And: Monaco editor is read-only
  await page.click('[data-testid="tab-files"]');
  await page.click('[data-testid="file-tree-item"][data-path="docs/PRD.md"]');

  // Verify editor has read-only attribute
  const editor = page.locator('[data-testid="monaco-editor"]');
  await expect(editor).toHaveAttribute('data-readonly', 'true');
});
```

**Scenario 6: Theme Toggle**
```typescript
test('MVP-6: Dark/light theme toggle', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: App loads with default theme (system preference)
  const html = page.locator('html');
  const initialTheme = await html.getAttribute('data-theme');

  // When: User clicks theme toggle
  await page.click('[data-testid="theme-toggle"]');

  // Then: Theme switches
  const newTheme = await html.getAttribute('data-theme');
  expect(newTheme).not.toBe(initialTheme);

  // And: All components update colors
  const bgColor = await page.locator('[data-testid="main-layout"]')
    .evaluate((el) => window.getComputedStyle(el).backgroundColor);

  // Verify background color changed (light vs dark)
  expect(bgColor).toBeTruthy();
});
```

**Phase 2: V1.1 (4 scenarios)**

**Scenario 7: Kanban Drag-Drop**
```typescript
test('V1.1-1: Drag story card to change state', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Kanban tab is open
  await page.click('[data-testid="tab-kanban"]');

  // When: User drags story from Backlog to Ready
  const story = page.locator('[data-testid="story-card-1.1"]');
  const readyColumn = page.locator('[data-testid="kanban-column-ready"]');

  await story.dragTo(readyColumn);

  // Then: Confirmation dialog appears
  await expect(page.locator('[data-testid="transition-confirm-dialog"]'))
    .toBeVisible();

  // When: User confirms
  await page.click('[data-testid="confirm-transition"]');

  // Then: Story moves to Ready column
  await expect(readyColumn.locator('[data-testid="story-card-1.1"]'))
    .toBeVisible();

  // And: Git commit created (verify in Git tab)
  await page.click('[data-testid="tab-git"]');
  await expect(page.locator('[data-testid="commit-message"]').first())
    .toContainText(/Story 1.1.*ready/i);
});
```

**Scenario 8: Workflow Controls**
```typescript
test('V1.1-2: Pause and resume workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Workflow is running
  // (Triggered via chat or CLI)
  await page.click('[data-testid="tab-workflows"]');

  // When: User clicks pause button
  await page.click('[data-testid="workflow-pause-btn"]');

  // Then: Workflow pauses
  await expect(page.locator('[data-testid="workflow-status"]'))
    .toContainText('Paused');

  // When: User clicks resume
  await page.click('[data-testid="workflow-resume-btn"]');

  // Then: Workflow resumes
  await expect(page.locator('[data-testid="workflow-status"]'))
    .toContainText('Running');
});
```

**Scenario 9: Git History and Diff**
```typescript
test('V1.1-3: View commit history and diff', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Git tab is open
  await page.click('[data-testid="tab-git"]');

  // When: User clicks on a commit
  await page.click('[data-testid="commit-card"]');

  // Then: Diff view opens
  await expect(page.locator('[data-testid="diff-viewer"]')).toBeVisible();

  // And: Shows added/removed lines
  await expect(page.locator('.diff-line-added')).toBeVisible();

  // And: Can switch between files
  await page.click('[data-testid="diff-file-selector"]');
  await page.click('[data-testid="diff-file-option"]');
});
```

**Scenario 10: Provider Configuration**
```typescript
test('V1.1-4: Change AI provider in settings', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Settings panel is open
  await page.click('[data-testid="settings-button"]');

  // When: User selects different provider
  await page.selectOption('[data-testid="provider-select"]', 'opencode');

  // And: Selects model
  await page.selectOption('[data-testid="model-select"]', 'claude-opus-4');

  // And: Clicks save
  await page.click('[data-testid="save-settings"]');

  // Then: Success toast appears
  await expect(page.locator('[data-testid="toast-success"]'))
    .toContainText(/Settings saved|Provider updated/i);

  // And: YAML file persisted
  // (Verify via API or file system check)
});
```

**Phase 3: V1.2 (4 scenarios)**

**Scenario 11: Ceremony Channel**
```typescript
test('V1.2-1: Join retrospective ceremony channel', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Ceremony is active
  // When: Ceremony channels tab becomes visible
  await expect(page.locator('[data-testid="tab-ceremonies"]')).toBeVisible();

  // And: User clicks tab
  await page.click('[data-testid="tab-ceremonies"]');

  // Then: Channel list shows active ceremony
  await expect(page.locator('[data-testid="ceremony-channel"]'))
    .toContainText(/retrospective/i);

  // When: User clicks channel
  await page.click('[data-testid="ceremony-channel"]');

  // Then: Message stream appears
  await expect(page.locator('[data-testid="ceremony-message"]').first())
    .toBeVisible();

  // And: Messages show agent avatars
  await expect(page.locator('[data-testid="message-avatar"]').first())
    .toBeVisible();
});
```

**Scenario 12: Layout Resize**
```typescript
test('V1.2-2: Resize panel and persist layout', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Files tab with split panel
  await page.click('[data-testid="tab-files"]');

  // When: User drags panel divider
  const divider = page.locator('[data-testid="panel-divider"]');
  const box = await divider.boundingBox();

  await page.mouse.move(box.x, box.y);
  await page.mouse.down();
  await page.mouse.move(box.x + 200, box.y);
  await page.mouse.up();

  // Then: Panel width changes
  const fileTree = page.locator('[data-testid="file-tree"]');
  const newWidth = await fileTree.evaluate((el) => el.offsetWidth);

  // Reload page
  await page.reload();

  // Then: Layout persisted from localStorage
  const restoredWidth = await fileTree.evaluate((el) => el.offsetWidth);
  expect(restoredWidth).toBeCloseTo(newWidth, 10);
});
```

**Scenario 13: Metrics Dashboard**
```typescript
test('V1.2-3: View metrics dashboard with charts', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Metrics tab exists (V1.2)
  await page.click('[data-testid="tab-metrics"]');

  // Then: Dashboard loads
  await expect(page.locator('[data-testid="metrics-dashboard"]')).toBeVisible();

  // And: Velocity chart visible
  await expect(page.locator('[data-testid="velocity-chart"]')).toBeVisible();

  // And: Agent activity chart visible
  await expect(page.locator('[data-testid="agent-activity-chart"]')).toBeVisible();

  // When: User hovers over data point
  await page.hover('[data-testid="chart-data-point"]');

  // Then: Tooltip shows details
  await expect(page.locator('[data-testid="chart-tooltip"]')).toBeVisible();
});
```

**Scenario 14: Export Metrics**
```typescript
test('V1.2-4: Export metrics to CSV', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Given: Metrics dashboard is open
  await page.click('[data-testid="tab-metrics"]');

  // When: User clicks export button
  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-testid="export-metrics-btn"]');

  // Then: CSV file downloads
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/metrics.*\.csv/i);

  // And: File contains expected data
  const path = await download.path();
  const fs = require('fs');
  const content = fs.readFileSync(path, 'utf-8');
  expect(content).toContain('Story,Points,Status');
});
```

### Playwright MCP Configuration

**Configuration** (`playwright.config.ts`):
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'gao-dev start --web --test-mode',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

### Semantic HTML Requirements

**All interactive elements must have**:

1. **Semantic HTML tags**:
```html
<!-- Good -->
<button data-testid="chat-send-button">Send</button>
<nav data-testid="sidebar">...</nav>
<main data-testid="main-content">...</main>

<!-- Bad -->
<div onClick={handleClick}>Send</div>
```

2. **data-testid attributes**:
```html
<button data-testid="chat-send-button">Send</button>
<input data-testid="chat-input" />
<div data-testid="activity-event">...</div>
```

3. **ARIA labels**:
```html
<button
  data-testid="theme-toggle"
  aria-label="Toggle dark/light theme"
>
  <ThemeIcon />
</button>
```

4. **State indicators**:
```html
<button
  data-testid="chat-send-button"
  data-state={isLoading ? 'loading' : 'idle'}
  disabled={isLoading}
>
  {isLoading ? 'Sending...' : 'Send'}
</button>
```

### data-testid Naming Conventions

**Pattern**: `{component}-{element}-{modifier}`

**Examples**:
- `chat-input` - Chat input textarea
- `chat-send-button` - Chat send button
- `chat-message-user` - User chat message
- `chat-message-brian` - Brian's chat message
- `activity-event` - Activity stream event card
- `activity-event-agent` - Agent name in event
- `file-tree-item` - File tree item
- `file-tree-item[data-path="..."]` - Specific file
- `monaco-editor` - Monaco editor instance
- `kanban-column-ready` - Kanban Ready column
- `story-card-1.1` - Story 1.1 card
- `theme-toggle` - Theme toggle button
- `sidebar` - Sidebar navigation
- `tab-chat` - Chat tab
- `tab-activity` - Activity tab

---

## Level 6: Performance Testing

### Performance Metrics (P95)

**Target Benchmarks**:

| Metric | Target | Measurement | Tool |
|--------|--------|-------------|------|
| **Page Load (TTI)** | <2s | Time to Interactive | Lighthouse |
| **Event Latency** | <100ms | WebSocket → DOM | Performance API |
| **Activity Stream Render** | <200ms | 1,000 events | Performance API |
| **File Tree Render** | <300ms | 500 files | Performance API |
| **Monaco Load** | <500ms | Editor init | Performance API |
| **Kanban Render** | <400ms | 100 stories | Performance API |
| **API Response** | <50ms | Backend processing | Logging |
| **WebSocket Reconnect** | <3s | Connection restore | Custom timing |

### Lighthouse Performance Tests

**Configuration** (`lighthouse.config.js`):
```javascript
module.exports = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices'],
    formFactor: 'desktop',
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
    },
    screenEmulation: {
      mobile: false,
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
    },
  },
};
```

**Automated Lighthouse Test**:
```typescript
import { test, expect } from '@playwright/test';
import { playAudit } from 'playwright-lighthouse';

test('Lighthouse performance audit', async ({ page, context }) => {
  await page.goto('http://localhost:3000');

  await playAudit({
    page,
    port: 9222,
    thresholds: {
      performance: 90,
      accessibility: 95,
      'best-practices': 90,
      'first-contentful-paint': 1000,
      'largest-contentful-paint': 2000,
      'cumulative-layout-shift': 0.1,
      'total-blocking-time': 200,
    },
    reports: {
      formats: {
        html: true,
        json: true,
      },
      directory: 'lighthouse-reports',
    },
  });
});
```

### WebSocket Performance Tests

**Event Delivery Latency**:
```python
import pytest
import asyncio
import time
from gao_dev.web.core.event_bus import WebEventBus

@pytest.mark.performance
async def test_event_delivery_latency():
    """Performance: Event delivery <10ms."""
    bus = WebEventBus()
    queue = bus.subscribe("test.event")

    latencies = []

    for i in range(100):
        start = time.perf_counter()
        await bus.publish(WebEvent(type="test.event", data={"id": i}))
        event = await queue.get()
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

    # Calculate P95
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]

    assert p95_latency < 10, f"P95 latency too high: {p95_latency:.2f}ms"
```

**WebSocket Stress Test**:
```python
@pytest.mark.performance
async def test_websocket_stress():
    """Performance: Handle 1,000 events/minute."""
    bus = WebEventBus()
    queues = [bus.subscribe("test.event") for _ in range(10)]

    start = time.perf_counter()

    # Publish 1,000 events
    for i in range(1000):
        await bus.publish(WebEvent(type="test.event", data={"id": i}))

    end = time.perf_counter()
    duration = end - start

    # Should complete in <1 second
    assert duration < 1.0, f"Stress test too slow: {duration:.2f}s"

    # Verify all subscribers received events
    for queue in queues:
        assert queue.qsize() == 1000
```

### Frontend Performance Tests

**Activity Stream Rendering**:
```typescript
import { test, expect } from '@playwright/test';

test('Activity stream renders 1000 events <200ms', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.click('[data-testid="tab-activity"]');

  // Trigger API to load 1000 events
  await page.evaluate(() => {
    performance.mark('render-start');
  });

  // Wait for events to render
  await page.waitForSelector('[data-testid="activity-event"]');

  await page.evaluate(() => {
    performance.mark('render-end');
    performance.measure('render-duration', 'render-start', 'render-end');
  });

  const duration = await page.evaluate(() => {
    const measure = performance.getEntriesByName('render-duration')[0];
    return measure.duration;
  });

  expect(duration).toBeLessThan(200);
});
```

**Memory Leak Detection**:
```typescript
test('No memory leaks after 1 hour', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Measure initial memory
  const initialMemory = await page.evaluate(() => {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize;
    }
    return 0;
  });

  // Simulate 1 hour of activity
  for (let i = 0; i < 60; i++) {
    // Send chat message
    await page.fill('[data-testid="chat-input"]', `Message ${i}`);
    await page.click('[data-testid="chat-send-button"]');

    // Switch tabs
    await page.click('[data-testid="tab-activity"]');
    await page.click('[data-testid="tab-files"]');
    await page.click('[data-testid="tab-chat"]');

    await page.waitForTimeout(1000); // 1 minute = 60 iterations
  }

  // Measure final memory
  const finalMemory = await page.evaluate(() => {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize;
    }
    return 0;
  });

  // Memory should not grow >500MB
  const growth = finalMemory - initialMemory;
  expect(growth).toBeLessThan(500 * 1024 * 1024); // 500MB
});
```

### Load Testing (k6)

**Load Test Script** (`load-test.js`):
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import ws from 'k6/ws';

export let options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up to 10 users
    { duration: '5m', target: 10 },  // Stay at 10 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<50'],  // 95% of API requests <50ms
    ws_connecting: ['p(95)<100'],     // 95% of WebSocket connects <100ms
  },
};

export default function () {
  // HTTP: Send chat message
  let response = http.post('http://localhost:3000/api/chat', JSON.stringify({
    agent: 'brian',
    message: 'What workflows are available?'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 50ms': (r) => r.timings.duration < 50,
  });

  // WebSocket: Connect and receive events
  const url = 'ws://localhost:3000/ws';
  const params = { tags: { name: 'EventStream' } };

  ws.connect(url, params, function (socket) {
    socket.on('open', () => console.log('connected'));
    socket.on('message', (data) => console.log('received:', data));

    socket.setTimeout(() => {
      socket.close();
    }, 5000);
  });

  sleep(1);
}
```

---

## Level 7: Accessibility Testing

### WCAG 2.1 AA Compliance

**Standard**: Web Content Accessibility Guidelines 2.1 Level AA

**Commitment**: 100% compliance for all features.

### Automated Accessibility Testing

**axe-core Integration** (Playwright):
```typescript
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await injectAxe(page);
  });

  test('Chat tab has no accessibility violations', async ({ page }) => {
    await page.click('[data-testid="tab-chat"]');
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });
  });

  test('Activity stream has no violations', async ({ page }) => {
    await page.click('[data-testid="tab-activity"]');
    await checkA11y(page);
  });

  test('Files tab has no violations', async ({ page }) => {
    await page.click('[data-testid="tab-files"]');
    await checkA11y(page);
  });

  test('Kanban board has no violations', async ({ page }) => {
    await page.click('[data-testid="tab-kanban"]');
    await checkA11y(page);
  });
});
```

### Keyboard Navigation Tests

**All features accessible via keyboard**:
```typescript
test('Keyboard navigation works throughout app', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Tab through navigation
  await page.keyboard.press('Tab'); // Focus sidebar
  await page.keyboard.press('Tab'); // Focus first tab
  await page.keyboard.press('Enter'); // Activate tab

  // Navigate chat with keyboard
  await page.keyboard.press('Tab'); // Focus input
  await page.keyboard.type('Hello Brian');
  await page.keyboard.press('Tab'); // Focus send button
  await page.keyboard.press('Enter'); // Send message

  // Verify message sent
  await expect(page.locator('[data-testid="chat-message-user"]').last())
    .toContainText('Hello Brian');
});
```

**Keyboard Shortcuts**:
```typescript
test('Keyboard shortcuts work', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Cmd+1 switches to Chat tab
  await page.keyboard.press('Meta+1');
  await expect(page.locator('[data-testid="tab-chat"]'))
    .toHaveAttribute('data-state', 'active');

  // Cmd+2 switches to Activity tab
  await page.keyboard.press('Meta+2');
  await expect(page.locator('[data-testid="tab-activity"]'))
    .toHaveAttribute('data-state', 'active');

  // Cmd+/ focuses chat input
  await page.keyboard.press('Meta+/');
  await expect(page.locator('[data-testid="chat-input"]')).toBeFocused();
});
```

### Screen Reader Testing

**Manual Testing Process**:

**macOS (VoiceOver)**:
1. Cmd+F5 to enable VoiceOver
2. Navigate through app with VO+arrows
3. Verify all interactive elements announced
4. Verify state changes announced (loading, error, success)
5. Verify ARIA live regions work (chat messages, activity stream)

**Windows (NVDA)**:
1. Install NVDA (free)
2. Navigate through app with arrow keys
3. Verify all content readable
4. Verify form labels read correctly
5. Verify dynamic updates announced

**Automated Screen Reader Tests** (limited):
```typescript
test('ARIA labels present on interactive elements', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Verify buttons have labels
  const buttons = page.locator('button');
  const count = await buttons.count();

  for (let i = 0; i < count; i++) {
    const button = buttons.nth(i);
    const ariaLabel = await button.getAttribute('aria-label');
    const text = await button.textContent();

    // Button must have either aria-label or visible text
    expect(ariaLabel || text).toBeTruthy();
  }
});
```

### Color Contrast Tests

**Automated Contrast Checking**:
```typescript
test('Color contrast meets WCAG AA', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Use axe to check contrast
  await injectAxe(page);
  await checkA11y(page, null, {
    rules: {
      'color-contrast': { enabled: true },
    },
  });
});
```

**Manual Contrast Verification**:
- Use browser DevTools color picker
- Minimum contrast ratios:
  - Normal text: 4.5:1
  - Large text (18pt+): 3:1
  - UI components: 3:1

### Focus Management Tests

**Focus Visible**:
```typescript
test('Focus indicators visible', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Tab to first focusable element
  await page.keyboard.press('Tab');

  // Get focused element
  const focused = await page.evaluate(() => {
    const el = document.activeElement;
    const styles = window.getComputedStyle(el);
    return {
      outline: styles.outline,
      outlineWidth: styles.outlineWidth,
    };
  });

  // Verify outline visible
  expect(focused.outline).not.toBe('none');
  expect(parseInt(focused.outlineWidth)).toBeGreaterThan(0);
});
```

**No Keyboard Traps**:
```typescript
test('No keyboard traps in modals', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Open modal
  await page.click('[data-testid="settings-button"]');

  // Tab through modal
  for (let i = 0; i < 20; i++) {
    await page.keyboard.press('Tab');
  }

  // Verify still within modal
  const focused = await page.evaluate(() => {
    return document.activeElement.closest('[role="dialog"]') !== null;
  });

  expect(focused).toBe(true);

  // Press Escape to close
  await page.keyboard.press('Escape');

  // Verify modal closed
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
});
```

### Accessibility Checklist

**All features must**:
- [ ] Color contrast 4.5:1 (normal text), 3:1 (large text/UI)
- [ ] All images have alt text (or alt="" if decorative)
- [ ] All icons have aria-label
- [ ] 100% keyboard accessible
- [ ] Logical tab order (left-to-right, top-to-bottom)
- [ ] Focus visible (outline or border)
- [ ] No keyboard traps
- [ ] Keyboard shortcuts documented
- [ ] HTML lang attribute set
- [ ] Form labels for all inputs
- [ ] Validation errors clear and actionable
- [ ] Valid HTML (no duplicate IDs)
- [ ] Semantic HTML (button, nav, main)
- [ ] ARIA labels where needed
- [ ] ARIA live regions for dynamic content
- [ ] Screen reader tested (VoiceOver, NVDA)

---

## Level 8: Security Testing

### Security Threat Model

**Attack Vectors**:

1. **WebSocket Session Hijacking**: Attacker intercepts session token
2. **CORS Bypass**: Attacker makes requests from unauthorized origin
3. **Path Traversal**: Attacker reads files outside project directory
4. **Command Injection**: Attacker injects commands via commit message
5. **XSS**: Attacker injects malicious script via chat/files
6. **CSRF**: Attacker tricks user into making unauthorized request
7. **Session Lock Bypass**: Attacker bypasses read-only mode enforcement

### Security Test Suite

**1. WebSocket Authentication**:
```python
import pytest
from fastapi.testclient import TestClient
from gao_dev.web.api.main import app

def test_websocket_requires_session_token():
    """Security: WebSocket connection requires valid session token."""
    client = TestClient(app)

    # Attempt connection without token
    with pytest.raises(Exception):
        with client.websocket_connect("/ws"):
            pass  # Should fail

    # Attempt connection with invalid token
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?token=invalid"):
            pass  # Should fail

    # Valid token should succeed
    # (Get token from /api/session endpoint)
    response = client.get("/api/session")
    token = response.json()["token"]

    with client.websocket_connect(f"/ws?token={token}") as ws:
        # Connection successful
        pass
```

**2. CORS Enforcement**:
```python
def test_cors_restricted_to_localhost():
    """Security: CORS only allows localhost origins."""
    client = TestClient(app)

    # Request from unauthorized origin
    response = client.post(
        "/api/chat",
        json={"agent": "brian", "message": "test"},
        headers={"Origin": "https://malicious-site.com"}
    )

    # Should be rejected
    assert response.status_code == 403

    # Request from localhost should succeed
    response = client.post(
        "/api/chat",
        json={"agent": "brian", "message": "test"},
        headers={"Origin": "http://localhost:3000"}
    )

    assert response.status_code == 200
```

**3. Path Traversal Prevention**:
```python
def test_path_traversal_prevented():
    """Security: Cannot read files outside project directory."""
    client = TestClient(app)

    # Attempt to read /etc/passwd
    response = client.get("/api/files/../../etc/passwd")

    # Should be rejected
    assert response.status_code == 400
    assert "Invalid path" in response.json()["error"]

    # Attempt to read .env file
    response = client.get("/api/files/../../../.env")

    # Should be rejected
    assert response.status_code == 400
```

**4. Command Injection Prevention**:
```python
def test_commit_message_sanitization():
    """Security: Commit messages sanitized to prevent injection."""
    client = TestClient(app)

    # Attempt injection via commit message
    response = client.post(
        "/api/files/save",
        json={
            "path": "test.md",
            "content": "test",
            "commit_message": "test; rm -rf /"
        }
    )

    # Should be rejected or sanitized
    # Check git log doesn't contain dangerous commands
    import git
    repo = git.Repo(".")
    latest_commit = list(repo.iter_commits())[0]
    assert "rm -rf" not in latest_commit.message
```

**5. XSS Prevention**:
```typescript
test('XSS prevented in chat messages', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Attempt XSS via chat message
  await page.fill('[data-testid="chat-input"]', '<script>alert("XSS")</script>');
  await page.click('[data-testid="chat-send-button"]');

  // Verify script not executed
  page.on('dialog', () => {
    throw new Error('XSS vulnerability: alert dialog appeared');
  });

  // Verify message displayed as text (escaped)
  await expect(page.locator('[data-testid="chat-message-user"]').last())
    .toContainText('<script>alert("XSS")</script>');
});
```

**6. CSRF Protection**:
```python
def test_csrf_protection_state_changes():
    """Security: State-changing operations require CSRF token."""
    client = TestClient(app)

    # Attempt to transition story without CSRF token
    response = client.post(
        "/api/kanban/transition",
        json={"epic": 1, "story": 1, "status": "in_progress"}
    )

    # Should be rejected
    assert response.status_code == 403
    assert "CSRF" in response.json()["error"]

    # Get CSRF token
    session_response = client.get("/api/session")
    csrf_token = session_response.json()["csrf_token"]

    # Retry with token
    response = client.post(
        "/api/kanban/transition",
        json={"epic": 1, "story": 1, "status": "in_progress"},
        headers={"X-CSRF-Token": csrf_token}
    )

    assert response.status_code == 200
```

**7. Session Lock Enforcement**:
```python
def test_read_only_mode_enforced():
    """Security: Read-only mode prevents write operations."""
    client = TestClient(app)

    # Simulate CLI holding lock
    from gao_dev.web.core.session_lock import SessionLock
    lock = SessionLock(project_root=Path("."))
    lock.acquire("cli", mode="write")

    # Attempt write operation from web
    response = client.post(
        "/api/chat",
        json={"agent": "brian", "message": "test"}
    )

    # Should be rejected (423 Locked)
    assert response.status_code == 423
    assert "Session locked by CLI" in response.json()["error"]

    # Read operations should succeed
    response = client.get("/api/files/docs/PRD.md")
    assert response.status_code == 200

    # Release lock
    lock.release()
```

### Security Scanning Tools

**1. Bandit (Python Security Linter)**:
```bash
# Already in pre-commit hooks
bandit -r gao_dev/web -ll
```

**2. npm audit (Frontend Dependencies)**:
```bash
npm audit --audit-level=moderate
```

**3. Safety (Python Dependencies)**:
```bash
safety check --full-report
```

**4. OWASP ZAP (Dynamic Security Scan)**:
```bash
# Run OWASP ZAP in daemon mode
docker run -u zap -p 8090:8090 -i owasp/zap2docker-stable zap.sh \
  -daemon -host 0.0.0.0 -port 8090 -config api.disablekey=true

# Scan web interface
docker run -u zap owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:3000 -r zap-report.html
```

### Security Checklist

**All PRs must pass**:
- [ ] WebSocket session token required
- [ ] CORS restricted to localhost
- [ ] Path validation prevents directory traversal
- [ ] Commit message sanitization prevents injection
- [ ] XSS prevention (all user input escaped)
- [ ] CSRF tokens for state-changing operations
- [ ] Session lock enforcement (read-only mode works)
- [ ] Bandit: 0 high/medium issues
- [ ] npm audit: 0 critical/high vulnerabilities
- [ ] Safety: 0 known vulnerabilities
- [ ] OWASP ZAP: 0 high/medium findings

---

## Test Environment Strategy

### Local Development

**Environment**: Developer workstation

**Setup**:
```bash
# Install dependencies
npm install
pip install -e ".[dev]"

# Run linters
npm run lint
ruff check gao_dev/web

# Run unit tests
npm test
pytest tests/web/unit

# Run integration tests
pytest tests/web/integration

# Run E2E tests
npx playwright test
```

**Database**: SQLite (`.gao-dev/documents.db`)
**Server**: FastAPI dev server (auto-reload enabled)
**Browser**: Chromium (Playwright)

### CI/CD Environment

**Environment**: GitHub Actions

**Matrix Testing**:
- Python: 3.11, 3.12
- Node.js: 18, 20
- OS: Ubuntu, macOS, Windows

**Database**: SQLite (ephemeral)
**Server**: FastAPI production mode
**Browser**: Chromium headless

### Staging Environment

**Environment**: Docker container

**Setup**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
RUN npm install && npm run build
CMD ["gao-dev", "start", "--web", "--host", "0.0.0.0"]
```

**Database**: SQLite
**Server**: uvicorn (production)
**Browser**: Chromium (for E2E tests)

### Test Data Management

**Fixtures**:
```python
# tests/web/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_project(tmp_path):
    """Create sample project with epics and stories."""
    project_root = tmp_path / "sample-project"
    project_root.mkdir()

    # Create .gao-dev directory
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()

    # Create documents.db
    from gao_dev.core.state_manager import GitIntegratedStateManager
    state_manager = GitIntegratedStateManager(project_root=project_root)

    # Create sample epics and stories
    state_manager.create_epic(1, "Foundation", "docs/epics/epic-1.md", "# Epic 1")
    state_manager.create_story(1, 1, "Setup", "docs/stories/story-1.1.md", "# Story 1.1")

    return project_root
```

**Mock Data**:
```typescript
// src/test/mocks/chatMessages.ts
export const mockChatMessages = [
  {
    id: '1',
    role: 'user',
    content: 'Create a PRD for user auth',
    timestamp: new Date('2025-01-16T10:00:00Z'),
  },
  {
    id: '2',
    role: 'assistant',
    agent: 'brian',
    content: 'I will coordinate with John to create a comprehensive PRD.',
    timestamp: new Date('2025-01-16T10:00:05Z'),
  },
];
```

---

## CI/CD Pipeline Integration

### GitHub Actions Workflow

**Configuration** (`.github/workflows/web-interface-tests.yml`):
```yaml
name: Web Interface Tests

on:
  push:
    branches: [main, feature/epic-39-*]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Frontend linting
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install frontend dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

      - name: Run Prettier
        run: npm run format:check

      - name: TypeScript type check
        run: npm run type-check

      # Backend linting
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Python dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run Ruff
        run: ruff check gao_dev/web

      - name: Run Black
        run: black --check gao_dev/web

      - name: Run MyPy
        run: mypy gao_dev/web --strict

      - name: Run Bandit
        run: bandit -r gao_dev/web -ll

  unit-tests:
    name: Unit Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12']
        node-version: ['18', '20']
    steps:
      - uses: actions/checkout@v3

      # Frontend unit tests
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install frontend dependencies
        run: npm ci

      - name: Run Vitest
        run: npm test -- --coverage

      - name: Upload frontend coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
          flags: frontend

      # Backend unit tests
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install Python dependencies
        run: pip install -e ".[dev]"

      - name: Run pytest (unit tests)
        run: pytest tests/web/unit --cov=gao_dev/web --cov-report=xml

      - name: Upload backend coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: backend

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          npm ci

      - name: Build frontend
        run: npm run build

      - name: Run integration tests
        run: pytest tests/web/integration -v

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: integration-test-results
          path: test-results/

  e2e-tests:
    name: E2E Tests (Playwright)
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          npm ci
          npx playwright install --with-deps chromium

      - name: Build frontend
        run: npm run build

      - name: Run Playwright tests
        run: npx playwright test

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

      - name: Upload test videos
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-videos
          path: test-results/

  performance-tests:
    name: Performance Tests
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          npm ci
          npm install -g @lhci/cli

      - name: Build frontend
        run: npm run build

      - name: Start server
        run: |
          gao-dev start --web --test-mode &
          npx wait-on http://localhost:3000

      - name: Run Lighthouse CI
        run: lhci autorun --config=.lighthouserc.json

      - name: Run k6 load tests
        run: |
          docker run --network=host grafana/k6 run /scripts/load-test.js

      - name: Upload performance results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: .lighthouseci/

  accessibility-tests:
    name: Accessibility Tests
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          npm ci
          npx playwright install --with-deps chromium

      - name: Build frontend
        run: npm run build

      - name: Start server
        run: |
          npx serve -s dist -l 3000 &
          npx wait-on http://localhost:3000

      - name: Run axe accessibility tests
        run: npx playwright test --grep "@accessibility"

      - name: Upload accessibility report
        uses: actions/upload-artifact@v3
        with:
          name: accessibility-report
          path: accessibility-report/

  security-tests:
    name: Security Tests
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          npm ci

      - name: Run npm audit
        run: npm audit --audit-level=moderate

      - name: Run Safety check
        run: safety check --full-report

      - name: Run security tests
        run: pytest tests/web/security -v

      - name: Run OWASP ZAP
        uses: zaproxy/action-baseline@v0.7.0
        with:
          target: 'http://localhost:3000'
```

### Quality Gates

**All PRs must pass**:

**Stage 1: Linting**
- ESLint: 0 errors, <10 warnings
- TypeScript: 0 type errors
- Ruff: 0 violations
- Black: 100% formatted
- MyPy: 0 type errors (strict mode)
- Bandit: 0 high/medium issues

**Stage 2: Unit Tests**
- Frontend coverage: >85%
- Backend coverage: >85%
- All tests pass

**Stage 3: Integration Tests**
- All integration tests pass
- Performance benchmarks met

**Stage 4: E2E Tests**
- All Playwright tests pass
- Cross-browser compatibility verified

**Stage 5: Performance Tests**
- Lighthouse score: >90 (performance)
- All P95 metrics met

**Stage 6: Accessibility Tests**
- axe-core: 0 violations
- Lighthouse accessibility: >95

**Stage 7: Security Tests**
- npm audit: 0 critical/high
- Safety: 0 known vulnerabilities
- Security tests pass
- OWASP ZAP: 0 high/medium

**If any stage fails**: PR cannot merge.

---

## Story-Level Test Plans

### High-Risk Stories (Comprehensive Testing)

**Story 39.2: WebSocket Manager and Event Bus**

**Risk**: High (critical infrastructure, complex async)

**Test Plan**:
- Unit tests:
  - Event publishing and subscription (15 tests)
  - Buffer overflow handling (5 tests)
  - Multiple subscribers (5 tests)
  - Event ordering (3 tests)
- Integration tests:
  - WebSocket connection and message flow (8 tests)
  - Reconnection handling (4 tests)
  - Event broadcast to multiple clients (3 tests)
- Performance tests:
  - Event delivery latency <10ms (1 test)
  - Throughput 1000+ events/second (1 test)
  - Memory usage under load (1 test)
- Security tests:
  - Session token required (2 tests)
  - Invalid token rejected (2 tests)

**Total**: 50 tests

**Story 39.7: Brian Chat Component**

**Risk**: High (user-facing, integration with Epic 30)

**Test Plan**:
- Unit tests:
  - Component rendering (8 tests)
  - User input handling (5 tests)
  - Message display (4 tests)
  - Loading states (3 tests)
- Integration tests:
  - ChatREPL integration (6 tests)
  - Streaming response (4 tests)
  - Error handling (3 tests)
- E2E tests:
  - End-to-end chat flow (2 tests, Scenario 2)
  - Multi-agent switching (1 test, Scenario 6)
- Accessibility tests:
  - Keyboard navigation (2 tests)
  - Screen reader compatibility (2 tests)

**Total**: 40 tests

**Story 39.14: Monaco Edit Mode with Commit Enforcement**

**Risk**: High (data integrity, git operations)

**Test Plan**:
- Unit tests:
  - Editor initialization (4 tests)
  - Commit message validation (6 tests)
  - Read-only mode (3 tests)
- Integration tests:
  - GitIntegratedStateManager integration (8 tests)
  - Atomic file+DB+git commit (5 tests)
  - Document lifecycle validation (4 tests)
- E2E tests:
  - File editing flow (2 tests, Scenario 4)
  - Commit enforcement (2 tests)
- Security tests:
  - Command injection prevention (3 tests)
  - Path traversal prevention (2 tests)

**Total**: 39 tests

### Medium-Risk Stories (Standard Testing)

**Story 39.11: File Tree Navigation Component**

**Risk**: Medium (performance with large projects)

**Test Plan**:
- Unit tests: 12 tests (rendering, virtual scrolling, filtering)
- Integration tests: 5 tests (real-time updates, file system integration)
- E2E tests: 1 test (Scenario 4)
- Performance tests: 2 tests (500+ files, rendering time <300ms)

**Total**: 20 tests

### Low-Risk Stories (Basic Testing)

**Story 39.6: Dark/Light Theme Support**

**Risk**: Low (isolated feature, simple logic)

**Test Plan**:
- Unit tests: 6 tests (theme switching, localStorage persistence)
- E2E tests: 1 test (Scenario 6)
- Accessibility tests: 1 test (contrast in both themes)

**Total**: 8 tests

### Complete Story Test Matrix

**(See separate document: `STORY_TEST_MATRIX.md` for all 39 stories)**

---

## Quality Gates

### Definition of Done (DoD)

**All stories must meet**:

1. **Code Complete**:
   - All acceptance criteria met
   - Code reviewed by peer
   - No P0 or P1 bugs

2. **Testing Complete**:
   - All unit tests pass (>85% coverage)
   - All integration tests pass
   - All E2E scenarios pass (if applicable)
   - Performance benchmarks met (if applicable)
   - Accessibility verified (axe-core 0 violations)
   - Security tests pass (if applicable)

3. **Quality Standards**:
   - Linting passes (0 errors)
   - Type checking passes (0 errors)
   - No code smells (DRY, SOLID)
   - Documentation updated

4. **Integration**:
   - Merged to main branch
   - CI/CD pipeline green
   - Deployed to staging

### Release Criteria

**MVP Release** (Phase 1):
- All 14 stories complete (39.1-39.14)
- All acceptance criteria met
- E2E test coverage: 6 scenarios passing
- Performance: All P95 metrics <targets
- Accessibility: WCAG 2.1 AA (100%)
- Security: All attack vectors mitigated
- Zero CLI regressions (100% existing tests pass)
- Beta testing: >80% satisfaction, ≥5 AI-discovered UX issues

**V1.1 Release** (Phase 2):
- All 13 stories complete (39.15-39.27)
- E2E test coverage: 10 scenarios passing
- Zero regressions from MVP
- Beta testing: >80% satisfaction

**V1.2 Release** (Phase 3):
- All 12 stories complete (39.28-39.40)
- E2E test coverage: 14 scenarios passing
- Zero regressions from V1.1
- Beta testing: >80% satisfaction
- Memory usage <500MB after 8 hours

---

## Tools and Frameworks

### Frontend Testing Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **Vitest** | 1.1+ | Unit testing (faster than Jest) |
| **React Testing Library** | 14+ | Component testing |
| **Playwright** | 1.40+ | E2E testing (AI-driven via MCP) |
| **axe-core** | 4.8+ | Accessibility testing |
| **Lighthouse** | 11+ | Performance auditing |
| **ESLint** | 8.56+ | JavaScript/TypeScript linting |
| **Prettier** | 3.1+ | Code formatting |
| **TypeScript** | 5.3+ | Type checking |

### Backend Testing Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **pytest** | 7.4+ | Unit/integration testing |
| **pytest-asyncio** | 0.21+ | Async test support |
| **pytest-cov** | 4.1+ | Coverage reporting |
| **Ruff** | 0.1+ | Fast Python linting |
| **Black** | 23.10+ | Code formatting |
| **MyPy** | 1.6+ | Type checking (strict mode) |
| **Bandit** | 1.7+ | Security linting |
| **Safety** | 2.3+ | Dependency vulnerability scanning |
| **k6** | 0.47+ | Load testing |

### CI/CD Tools

| Tool | Purpose |
|------|---------|
| **GitHub Actions** | CI/CD pipeline |
| **Codecov** | Coverage reporting |
| **OWASP ZAP** | Dynamic security scanning |
| **Dependabot** | Dependency updates |

---

## Metrics and Reporting

### Test Execution Metrics

**Track per PR**:
- Total tests run
- Tests passed/failed/skipped
- Test duration
- Coverage percentage (frontend, backend)
- Flaky test rate

**Example Report**:
```
Test Execution Summary
─────────────────────────────────────────
Frontend Tests:
  Unit: 287 passed, 0 failed (85.4% coverage)
  Integration: 45 passed, 0 failed
  E2E: 6 passed, 0 failed
  Total: 338 tests, 12m 34s

Backend Tests:
  Unit: 156 passed, 0 failed (87.2% coverage)
  Integration: 32 passed, 0 failed
  Security: 18 passed, 0 failed
  Total: 206 tests, 8m 12s

Performance Metrics (P95):
  Page Load: 1.8s ✓ (<2s target)
  Event Latency: 8ms ✓ (<100ms target)
  File Tree Render: 245ms ✓ (<300ms target)

Accessibility:
  axe-core violations: 0 ✓
  Lighthouse score: 97/100 ✓

Security:
  Bandit issues: 0 ✓
  npm audit: 0 high/critical ✓
  OWASP ZAP findings: 0 high/medium ✓

Overall: PASS ✓
```

### Coverage Trends

**Track over time**:
- Overall coverage percentage
- Coverage by component/module
- Uncovered lines (hotspots)

**Visualization**: Codecov dashboard

### Flaky Test Tracking

**Definition**: Test that passes/fails non-deterministically

**Action**:
- Mark as flaky: `@pytest.mark.flaky`
- Investigate root cause within 24 hours
- Fix or delete within 1 week

**Flaky Test Report**:
```
Flaky Tests (Last 30 Days)
──────────────────────────────────────────
test_websocket_reconnection   12% failure rate   Priority: HIGH
test_monaco_editor_load       5% failure rate    Priority: MEDIUM
```

### Test Quality Metrics

**Track**:
- Test-to-code ratio (ideal: 2:1 for critical paths)
- Average test execution time
- Test maintenance burden (time spent fixing tests)

---

## Conclusion

This comprehensive test strategy ensures Epic 39 (Web Interface) is delivered with high quality, performance, accessibility, and security. The strategy covers 8 testing levels with clear targets, tools, and quality gates.

**Key Takeaways**:

1. **Risk-Based**: High-risk stories (WebSocket, Chat, Monaco editing) receive comprehensive testing.
2. **AI-Powered**: Playwright MCP enables Claude Code to test GAO-Dev, finding real UX issues.
3. **Test Pyramid**: Many unit tests (70%), fewer integration tests (20%), minimal E2E tests (10%).
4. **Continuous**: All tests run in CI/CD with strict quality gates.
5. **Comprehensive**: 8 levels cover linting, unit, integration, regression, E2E, performance, accessibility, security.

**Expected Outcomes**:
- Test coverage: >85% (frontend), >85% (backend)
- E2E scenarios: 14 (all 3 phases)
- Performance: All P95 metrics <targets
- Accessibility: 100% WCAG 2.1 AA compliance
- Security: 0 high/medium vulnerabilities
- Zero CLI regressions

**Next Steps**:
1. Review and approve test strategy
2. Create detailed E2E test plan (separate document)
3. Set up CI/CD pipeline
4. Begin implementation with Story 39.1 (Backend Foundation)

---

**Document Status**: Complete - Ready for Review
**Author**: Murat (Test Architect)
**Reviewers**: Winston (Architect), Bob (Scrum Master), Amelia (Developer)
**Version**: 1.0
**Last Updated**: 2025-01-16
