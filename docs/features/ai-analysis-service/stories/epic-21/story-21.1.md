# Story 21.1: Create AI Analysis Service

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Story Points**: 8
**Status**: Ready
**Priority**: High
**Assignee**: TBD

---

## User Story

As a **developer**, I want **a reusable AI analysis service that provides provider-abstracted AI calls**, so that **components can use AI for decision-making without full agent overhead or hardcoded provider dependencies**.

---

## Context

Currently, components that need AI for analysis (like Brian) have two bad options:
1. **Use Anthropic client directly** - Breaks provider abstraction, hardcodes dependency
2. **Implement IAgent interface** - Overengineering for analysis-only use cases

**Problem**:
- Brian uses `self.anthropic.messages.create()` directly
- Cannot use local models (Ollama + deepseek-r1)
- Cannot use OpenCode provider
- Cannot be tested without live API
- Violates architecture principles

**Solution**:
Create **AIAnalysisService** - a lightweight, reusable service for analysis-only AI calls that:
- Uses ProcessExecutor internally for provider abstraction
- Works with any provider (Claude, OpenCode, local models)
- Easy to test (mock service or executor)
- Simple interface focused on analysis tasks

---

## Acceptance Criteria

### AC1: Service Implementation
- [ ] Create `gao_dev/core/services/ai_analysis_service.py`
- [ ] `AIAnalysisService` class with clear interface
- [ ] Uses ProcessExecutor for provider abstraction
- [ ] Works with all existing providers

### AC2: Analyze Method
- [ ] `async def analyze()` method implemented
- [ ] Parameters:
  - `prompt: str` - Analysis prompt
  - `model: Optional[str]` - Model to use (defaults to configured)
  - `system_prompt: Optional[str]` - System instructions
  - `response_format: str` - "json" or "text"
  - `max_tokens: int` - Response length limit
  - `temperature: float` - Sampling temperature
- [ ] Returns `AnalysisResult` with response and metadata

### AC3: Result Model
- [ ] Create `AnalysisResult` dataclass:
  - `response: str` - AI response text
  - `model_used: str` - Model that processed request
  - `tokens_used: int` - Token count
  - `duration_ms: float` - Processing time
- [ ] Clean, typed interface

### AC4: Error Handling
- [ ] Create `AnalysisError` exception class
- [ ] Handle provider failures gracefully
- [ ] Handle timeout errors
- [ ] Handle invalid model errors
- [ ] Clear error messages with context

### AC5: Logging and Observability
- [ ] Structured logging with structlog
- [ ] Log analysis requests (model, prompt length)
- [ ] Log analysis results (tokens, duration)
- [ ] Log errors with full context
- [ ] Performance metrics captured

### AC6: Configuration
- [ ] Support default model configuration
- [ ] Support per-call model override
- [ ] Respect GAO_DEV_MODEL environment variable
- [ ] Load from agent config if available

### AC7: Unit Tests
- [ ] Test service initialization
- [ ] Test analyze() with various parameters
- [ ] Test with mocked ProcessExecutor
- [ ] Test error scenarios (API failures, timeouts)
- [ ] Test model selection logic
- [ ] Test response parsing (JSON and text)
- [ ] >90% code coverage

### AC8: API Documentation
- [ ] Comprehensive docstrings
- [ ] Usage examples in docstrings
- [ ] Type hints throughout
- [ ] Clear error documentation

---

## Technical Details

### File Structure

```
gao_dev/
├── core/
│   └── services/
│       ├── __init__.py              # NEW - Export AIAnalysisService
│       └── ai_analysis_service.py   # NEW - Main service
│
└── exceptions/
    └── analysis_exceptions.py        # NEW - AnalysisError

tests/
└── unit/
    └── core/
        └── services/
            └── test_ai_analysis_service.py  # NEW - Unit tests
```

### AIAnalysisService Implementation

```python
# gao_dev/core/services/ai_analysis_service.py

from dataclasses import dataclass
from typing import Optional
import structlog
import time

from ..process_executor import ProcessExecutor

logger = structlog.get_logger()


@dataclass
class AnalysisResult:
    """Result from AI analysis."""
    response: str
    model_used: str
    tokens_used: int
    duration_ms: float


class AnalysisError(Exception):
    """Error during AI analysis."""
    pass


class AIAnalysisService:
    """
    Provider-abstracted AI analysis service.

    Provides simple interface for components that need AI analysis
    without full agent capabilities (tools, artifacts, etc.).

    Example:
        ```python
        service = AIAnalysisService(executor)
        result = await service.analyze(
            prompt="Analyze this project complexity",
            model="claude-sonnet-4-5-20250929",
            response_format="json"
        )
        print(result.response)
        ```
    """

    def __init__(
        self,
        executor: ProcessExecutor,
        default_model: Optional[str] = None
    ):
        """
        Initialize analysis service.

        Args:
            executor: ProcessExecutor for provider abstraction
            default_model: Default model if not specified per-call
        """
        self.executor = executor
        self.default_model = default_model or "claude-sonnet-4-5-20250929"
        self.logger = logger.bind(service="ai_analysis")

    async def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        response_format: str = "json",
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> AnalysisResult:
        """
        Send analysis prompt to AI provider.

        Args:
            prompt: User prompt for analysis
            model: Model to use (defaults to configured model)
            system_prompt: Optional system instructions
            response_format: Expected format ("json" or "text")
            max_tokens: Maximum response length
            temperature: Sampling temperature

        Returns:
            AnalysisResult with response and metadata

        Raises:
            AnalysisError: If analysis fails

        Example:
            ```python
            result = await service.analyze(
                prompt="Rate complexity 1-10",
                model="deepseek-r1",
                response_format="json"
            )
            ```
        """
        model_to_use = model or self.default_model
        start_time = time.time()

        self.logger.info(
            "analysis_started",
            model=model_to_use,
            prompt_length=len(prompt),
            response_format=response_format
        )

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Execute via ProcessExecutor
            # TODO: Implement execution via ProcessExecutor
            # This will need a simple execution context that ProcessExecutor can handle

            # For now, placeholder
            raise NotImplementedError("ProcessExecutor integration needed")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "analysis_failed",
                model=model_to_use,
                error=str(e),
                duration_ms=duration_ms
            )
            raise AnalysisError(f"Analysis failed: {e}") from e
```

### Exception Classes

```python
# gao_dev/exceptions/analysis_exceptions.py

class AnalysisError(Exception):
    """Base exception for AI analysis errors."""
    pass


class AnalysisTimeoutError(AnalysisError):
    """Analysis request timed out."""
    pass


class InvalidModelError(AnalysisError):
    """Requested model is invalid or unavailable."""
    pass
```

### ProcessExecutor Integration

The service needs to leverage ProcessExecutor's existing provider abstraction. This requires:
1. Creating a minimal execution context for analysis tasks
2. Extracting the response from ProcessExecutor's result format
3. Handling provider-specific details transparently

**Note**: This story focuses on the service interface. ProcessExecutor integration details will be refined during implementation based on ProcessExecutor's actual API.

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/core/services/test_ai_analysis_service.py

import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.core.services import AIAnalysisService, AnalysisResult
from gao_dev.exceptions.analysis_exceptions import AnalysisError


@pytest.fixture
def mock_executor():
    """Mock ProcessExecutor."""
    executor = Mock()
    executor.execute = AsyncMock()
    return executor


@pytest.fixture
def service(mock_executor):
    """Create service with mocked executor."""
    return AIAnalysisService(executor=mock_executor)


async def test_analyze_basic(service, mock_executor):
    """Test basic analysis call."""
    # Setup mock response
    mock_executor.execute.return_value = Mock(
        response='{"scale_level": 2}',
        tokens_used=150
    )

    # Call service
    result = await service.analyze(
        prompt="Analyze this",
        model="claude-sonnet-4-5",
        response_format="json"
    )

    # Verify
    assert result.response == '{"scale_level": 2}'
    assert result.model_used == "claude-sonnet-4-5"
    assert result.tokens_used == 150
    assert result.duration_ms > 0


async def test_analyze_with_system_prompt(service, mock_executor):
    """Test analysis with system prompt."""
    mock_executor.execute.return_value = Mock(
        response="Analysis complete",
        tokens_used=100
    )

    result = await service.analyze(
        prompt="User request",
        system_prompt="You are an expert analyzer",
        response_format="text"
    )

    assert result.response == "Analysis complete"


async def test_analyze_error_handling(service, mock_executor):
    """Test error handling."""
    mock_executor.execute.side_effect = Exception("API Error")

    with pytest.raises(AnalysisError) as exc_info:
        await service.analyze(prompt="Test")

    assert "Analysis failed" in str(exc_info.value)


async def test_analyze_default_model(service):
    """Test default model usage."""
    result = await service.analyze(prompt="Test")
    # Should use default model
    assert service.default_model == "claude-sonnet-4-5-20250929"


async def test_analyze_model_override(service, mock_executor):
    """Test per-call model override."""
    mock_executor.execute.return_value = Mock(
        response="OK",
        tokens_used=50
    )

    result = await service.analyze(
        prompt="Test",
        model="deepseek-r1"
    )

    assert result.model_used == "deepseek-r1"
```

---

## Definition of Done

- [ ] AIAnalysisService implemented
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Type hints complete (mypy passes)
- [ ] Docstrings complete with examples
- [ ] Code reviewed and approved
- [ ] No new technical debt introduced

---

## Dependencies

- **ProcessExecutor** (exists): Will be used for provider abstraction
- **structlog** (installed): For logging
- **pytest** (installed): For testing
- **pytest-asyncio** (installed): For async tests

---

## Notes

- This service is designed to be simple and focused on analysis tasks only
- It does NOT provide agent capabilities (tools, artifacts, etc.)
- Future analysis components (cost estimators, code reviewers) can reuse this service
- The service interface is provider-agnostic - all provider details are handled by ProcessExecutor

---

## Related Documents

- **Epic 21 Plan**: `docs/features/ai-analysis-service/EPIC-21-PLAN.md`
- **PRD**: `docs/features/ai-analysis-service/PRD.md`
- **Architecture Analysis**: `docs/analysis/brian-architecture-analysis.md`
- **ProcessExecutor**: `gao_dev/core/process_executor.py`
