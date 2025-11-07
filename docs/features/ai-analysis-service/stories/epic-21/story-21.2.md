# Story 21.2: Refactor Brian to Use Analysis Service

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Story Points**: 5
**Status**: Blocked (depends on Story 21.1)
**Priority**: High
**Assignee**: TBD

---

## User Story

As a **developer**, I want **Brian to use AIAnalysisService instead of the Anthropic client**, so that **Brian can work with any AI provider (Claude, OpenCode, local models) without hardcoded dependencies**.

---

## Context

Brian currently uses the Anthropic client directly for workflow analysis:

```python
# gao_dev/orchestrator/brian_orchestrator.py:206-210
response = self.anthropic.messages.create(
    model=self.model,
    max_tokens=2048,
    messages=[{"role": "user", "content": analysis_prompt}]
)
```

**Problems**:
- Hardcoded dependency on Anthropic
- Cannot use local models (Ollama + deepseek-r1)
- Cannot use OpenCode provider
- Cannot be tested without live API
- Inconsistent with agent architecture

**Solution**:
Refactor Brian to:
1. Remove direct Anthropic client dependency
2. Receive AIAnalysisService via dependency injection
3. Use `analysis_service.analyze()` for all AI calls
4. Maintain existing functionality

---

## Acceptance Criteria

### AC1: Remove Anthropic Client
- [ ] Remove `from anthropic import Anthropic` import
- [ ] Remove `self.anthropic = Anthropic(...)` initialization
- [ ] Remove all `self.anthropic.messages.create()` calls
- [ ] No direct API client dependencies

### AC2: Add Analysis Service Parameter
- [ ] Add `analysis_service: AIAnalysisService` parameter to `__init__`
- [ ] Store as `self.analysis_service`
- [ ] Update docstring to document new parameter
- [ ] Type hints correct

### AC3: Refactor _analyze_prompt Method
- [ ] Replace `self.anthropic.messages.create()` with `self.analysis_service.analyze()`
- [ ] Pass correct parameters:
  - `prompt`: Analysis prompt (existing)
  - `model`: `self.model` (existing)
  - `response_format`: "json"
  - `max_tokens`: 2048
- [ ] Extract response from `AnalysisResult.response`
- [ ] Parse JSON response (existing logic)

### AC4: Maintain Existing Functionality
- [ ] Same prompt structure as before
- [ ] Same JSON response parsing
- [ ] Same `PromptAnalysis` result
- [ ] Same error handling behavior
- [ ] Same logging output

### AC5: Update Error Handling
- [ ] Catch `AnalysisError` instead of Anthropic exceptions
- [ ] Log errors with same detail level
- [ ] Return same error information to caller
- [ ] Preserve existing retry logic if any

### AC6: Preserve Model Configuration
- [ ] Model still loaded from:
  1. GAO_DEV_MODEL environment variable
  2. Brian's YAML config (brian.agent.yaml)
  3. Default fallback
- [ ] Model passed to `analyze()` method
- [ ] Logging shows model selection

### AC7: Update Tests
- [ ] All existing Brian tests pass
- [ ] Mock AIAnalysisService instead of Anthropic client
- [ ] Add test with mocked service
- [ ] Add test verifying service calls
- [ ] No live API calls in tests

### AC8: Backwards Compatibility
- [ ] Existing callers work (may need updates in Story 21.3)
- [ ] Same public interface (except __init__)
- [ ] Same return types
- [ ] Same behavior

---

## Technical Details

### File Changes

```
gao_dev/orchestrator/
└── brian_orchestrator.py          # MODIFIED - Remove Anthropic, use service

tests/unit/orchestrator/
└── test_brian_orchestrator.py     # MODIFIED - Mock service instead of API
```

### Code Changes

#### Before (Current Implementation)

```python
# gao_dev/orchestrator/brian_orchestrator.py

from anthropic import Anthropic
import os

class BrianOrchestrator:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        api_key: Optional[str] = None,
        brian_persona_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
        model: Optional[str] = None
    ):
        # Initialize Anthropic client
        self.anthropic = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

        # Load model from config
        self.model = model or "claude-sonnet-4-5-20250929"

    async def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(prompt)

        # Call Anthropic API
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": analysis_prompt}]
        )

        # Parse response
        response_text = response.content[0].text
        data = json.loads(response_text)

        return PromptAnalysis(**data)
```

#### After (Refactored Implementation)

```python
# gao_dev/orchestrator/brian_orchestrator.py

from ..core.services import AIAnalysisService, AnalysisError
import os

class BrianOrchestrator:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        analysis_service: AIAnalysisService,  # NEW PARAMETER
        brian_persona_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Brian orchestrator.

        Args:
            workflow_registry: Registry of available workflows
            analysis_service: AI analysis service for prompt analysis
            brian_persona_path: Path to Brian's persona file
            project_root: Project root directory
            model: Model to use for analysis (optional)
        """
        self.workflow_registry = workflow_registry
        self.analysis_service = analysis_service  # NEW

        # Load model from config
        self.model = model or os.getenv("GAO_DEV_MODEL") or "claude-sonnet-4-5-20250929"

        # ... rest of initialization

    async def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """
        Analyze user prompt to determine scale and workflow requirements.

        Args:
            prompt: User's initial request

        Returns:
            PromptAnalysis with scale level and requirements

        Raises:
            AnalysisError: If analysis fails
        """
        try:
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(prompt)

            # Call analysis service (NOT Anthropic directly)
            result = await self.analysis_service.analyze(
                prompt=analysis_prompt,
                model=self.model,
                response_format="json",
                max_tokens=2048
            )

            # Parse JSON response
            data = json.loads(result.response)

            self.logger.info(
                "brian_analysis_complete",
                scale_level=data.get("scale_level"),
                model=result.model_used,
                tokens=result.tokens_used
            )

            return PromptAnalysis(**data)

        except AnalysisError as e:
            self.logger.error(
                "brian_analysis_failed",
                error=str(e),
                model=self.model
            )
            raise
        except json.JSONDecodeError as e:
            self.logger.error(
                "brian_response_parse_failed",
                error=str(e),
                response=result.response[:200]
            )
            raise AnalysisError(f"Failed to parse analysis response: {e}")
```

---

## Testing Strategy

### Updated Test Structure

```python
# tests/unit/orchestrator/test_brian_orchestrator.py

import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.core.services import AIAnalysisService, AnalysisResult


@pytest.fixture
def mock_analysis_service():
    """Mock AIAnalysisService."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def mock_workflow_registry():
    """Mock WorkflowRegistry."""
    return Mock()


@pytest.fixture
def brian_orchestrator(mock_workflow_registry, mock_analysis_service):
    """Create Brian with mocked dependencies."""
    return BrianOrchestrator(
        workflow_registry=mock_workflow_registry,
        analysis_service=mock_analysis_service,
        model="claude-sonnet-4-5-20250929"
    )


async def test_analyze_prompt_basic(brian_orchestrator, mock_analysis_service):
    """Test basic prompt analysis."""
    # Setup mock response
    mock_analysis_service.analyze.return_value = AnalysisResult(
        response='{"scale_level": 2, "needs_clarification": false}',
        model_used="claude-sonnet-4-5-20250929",
        tokens_used=150,
        duration_ms=1200
    )

    # Call Brian
    result = await brian_orchestrator._analyze_prompt("Build a todo app")

    # Verify
    assert result.scale_level == 2
    assert result.needs_clarification == False

    # Verify service was called correctly
    mock_analysis_service.analyze.assert_called_once()
    call_args = mock_analysis_service.analyze.call_args
    assert call_args.kwargs["model"] == "claude-sonnet-4-5-20250929"
    assert call_args.kwargs["response_format"] == "json"
    assert call_args.kwargs["max_tokens"] == 2048


async def test_analyze_prompt_with_deepseek(brian_orchestrator, mock_analysis_service):
    """Test analysis with deepseek-r1 model."""
    # Brian configured with deepseek-r1
    brian_orchestrator.model = "deepseek-r1"

    mock_analysis_service.analyze.return_value = AnalysisResult(
        response='{"scale_level": 1, "needs_clarification": false}',
        model_used="deepseek-r1",
        tokens_used=100,
        duration_ms=800
    )

    result = await brian_orchestrator._analyze_prompt("Add login page")

    # Verify correct model used
    call_args = mock_analysis_service.analyze.call_args
    assert call_args.kwargs["model"] == "deepseek-r1"


async def test_analyze_prompt_error_handling(brian_orchestrator, mock_analysis_service):
    """Test error handling."""
    from gao_dev.exceptions.analysis_exceptions import AnalysisError

    # Service raises error
    mock_analysis_service.analyze.side_effect = AnalysisError("API timeout")

    # Should propagate error
    with pytest.raises(AnalysisError) as exc_info:
        await brian_orchestrator._analyze_prompt("Test")

    assert "API timeout" in str(exc_info.value)
```

---

## Definition of Done

- [ ] All Anthropic client code removed from Brian
- [ ] Brian uses AIAnalysisService
- [ ] All acceptance criteria met
- [ ] All existing tests pass with mocked service
- [ ] New tests added for service integration
- [ ] Code reviewed and approved
- [ ] No functional regression
- [ ] Documentation updated

---

## Dependencies

- **Story 21.1** (required): AIAnalysisService must be implemented first
- **WorkflowRegistry** (exists): Used by Brian
- **Brian persona** (exists): gao_dev/agents/brian.md

---

## Migration Checklist

- [ ] Remove Anthropic import
- [ ] Add analysis_service parameter
- [ ] Update _analyze_prompt() method
- [ ] Update error handling
- [ ] Update tests
- [ ] Verify all tests pass
- [ ] Test with multiple providers (wait for Story 21.3)

---

## Notes

- This story only refactors Brian internally
- Story 21.3 will update all Brian initialization points
- Existing callers may need updates in Story 21.3
- Focus: Remove hardcoded provider dependency
- Maintain exact same external behavior

---

## Related Documents

- **Story 21.1**: Create AI Analysis Service (prerequisite)
- **Story 21.3**: Update Brian Initialization Points (follow-up)
- **Epic 21 Plan**: `docs/features/ai-analysis-service/EPIC-21-PLAN.md`
- **Architecture Analysis**: `docs/analysis/brian-architecture-analysis.md`
- **Brian Implementation**: `gao_dev/orchestrator/brian_orchestrator.py`
