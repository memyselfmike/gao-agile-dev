# AIAnalysisService Usage Guide

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Version**: 1.0
**Audience**: Developers using AIAnalysisService
**Last Updated**: 2025-11-07

---

## Table of Contents

1. [Introduction](#introduction)
2. [When to Use This Service](#when-to-use-this-service)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Common Patterns](#common-patterns)
6. [Testing](#testing)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

`AIAnalysisService` is a lightweight service for AI-powered analysis tasks. It provides a simple interface to send prompts to AI models and receive structured responses, without the overhead of full agent capabilities.

**What you can do:**
- Analyze code complexity
- Get structured decisions (JSON)
- Code review suggestions
- Project analysis
- Quick AI-powered decisions

**What you cannot do:**
- Create files or artifacts (use IAgent instead)
- Execute tools (Read, Write, Bash, etc.)
- Multi-step workflows
- Maintain conversational state

---

## When to Use This Service

### Use AIAnalysisService When:

- **Single-shot analysis**: One prompt, one response
- **Decision-making**: Need AI to make a choice
- **Structured output**: Want JSON responses
- **Lightweight task**: No artifact creation needed
- **Reusable logic**: Multiple components need same analysis

**Examples:**
```python
# Good use cases
- Analyze project complexity and return scale level
- Review code snippet and return quality score
- Classify user request type
- Generate structured recommendations
```

### Use IAgent When:

- **Artifact creation**: Need to create files, commits, etc.
- **Tool usage**: Need Read, Write, Bash, Grep, etc.
- **Multi-step workflow**: Complex task with multiple phases
- **Stateful interaction**: Maintain conversation context

**Examples:**
```python
# Use IAgent instead
- Implement a feature (creates code)
- Review PR and commit changes
- Run tests and fix failures
- Generate documentation files
```

---

## Basic Usage

### 1. Installation

Already included with GAO-Dev:

```bash
pip install -e .
```

Set up environment:

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### 2. Simple Example

```python
import asyncio
from gao_dev.core.services import AIAnalysisService

async def main():
    # Create service
    service = AIAnalysisService()

    # Analyze a prompt
    result = await service.analyze(
        prompt="Analyze the complexity of building a todo app",
        response_format="json"
    )

    # Use result
    print("Response:", result.response)
    print(f"Tokens: {result.tokens_used}")
    print(f"Duration: {result.duration_ms}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. With Configuration

```python
# Explicit configuration
service = AIAnalysisService(
    api_key="sk-ant-...",  # Or use ANTHROPIC_API_KEY env var
    default_model="claude-sonnet-4-5-20250929"
)

# Analyze with custom parameters
result = await service.analyze(
    prompt="Review this code: def add(a, b): return a + b",
    model="claude-3-haiku-20240307",  # Override default
    system_prompt="You are a code reviewer",
    response_format="json",
    max_tokens=1024,
    temperature=0.7
)
```

---

## Advanced Usage

### 1. JSON Response Parsing

```python
import json
from gao_dev.core.services import AIAnalysisService

async def analyze_complexity(project_description: str):
    service = AIAnalysisService()

    result = await service.analyze(
        prompt=f"""
        Analyze this project and return JSON:
        {{
            "scale_level": 0-4,
            "estimated_stories": number,
            "complexity_factors": ["factor1", "factor2"],
            "rationale": "explanation"
        }}

        Project: {project_description}
        """,
        response_format="json"
    )

    # Parse JSON response
    analysis = json.loads(result.response)

    print(f"Scale Level: {analysis['scale_level']}")
    print(f"Stories: {analysis['estimated_stories']}")
    print(f"Factors: {', '.join(analysis['complexity_factors'])}")
    print(f"Rationale: {analysis['rationale']}")

    return analysis
```

### 2. System Prompts

```python
async def code_review(code: str):
    service = AIAnalysisService()

    result = await service.analyze(
        prompt=f"""
        Review this code:
        ```python
        {code}
        ```

        Return JSON with:
        - quality_score (1-10)
        - issues (list)
        - suggestions (list)
        """,
        system_prompt="""
        You are an expert code reviewer.
        Focus on:
        - Code quality and readability
        - Performance issues
        - Security concerns
        - Best practices
        Be concise and specific.
        """,
        response_format="json",
        temperature=0.3  # More deterministic for reviews
    )

    review = json.loads(result.response)
    return review
```

### 3. Custom Models

```python
async def multi_model_analysis(prompt: str):
    """Compare different models for same task."""
    service = AIAnalysisService()

    # Fast, cheap model for simple analysis
    quick_result = await service.analyze(
        prompt=prompt,
        model="claude-3-haiku-20240307",
        max_tokens=512
    )

    # Powerful model for complex analysis
    detailed_result = await service.analyze(
        prompt=prompt,
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048
    )

    return {
        "quick": quick_result,
        "detailed": detailed_result
    }
```

### 4. Temperature Control

```python
async def creative_vs_deterministic():
    service = AIAnalysisService()

    # Deterministic output (same input = same output)
    deterministic = await service.analyze(
        prompt="Calculate complexity score for: def add(a, b): return a + b",
        temperature=0.0  # Completely deterministic
    )

    # Creative output (more varied responses)
    creative = await service.analyze(
        prompt="Suggest creative refactoring ideas",
        temperature=0.9  # More creative/varied
    )

    return deterministic, creative
```

---

## Common Patterns

### Pattern 1: Complexity Analysis (Brian Use Case)

```python
from typing import Dict, Any
import json

async def analyze_project_complexity(
    user_prompt: str,
    service: AIAnalysisService
) -> Dict[str, Any]:
    """
    Analyze project complexity and recommend scale level.

    Used by Brian orchestrator for workflow selection.
    """
    result = await service.analyze(
        prompt=f"""
        Analyze this project request and classify complexity:

        USER REQUEST: {user_prompt}

        Return JSON:
        {{
            "scale_level": 0-4,
            "project_type": "greenfield|feature|bugfix|chore",
            "estimated_stories": number,
            "complexity_factors": ["auth", "database", "ui", "api"],
            "rationale": "brief explanation"
        }}

        Scale levels:
        - 0: Chore (<1 hour)
        - 1: Bug fix (1-4 hours)
        - 2: Small feature (1-2 weeks)
        - 3: Medium feature (1-2 months)
        - 4: Greenfield app (2-6 months)
        """,
        response_format="json",
        system_prompt="You are a project complexity analyzer.",
        temperature=0.3  # Consistent analysis
    )

    analysis = json.loads(result.response)
    return analysis
```

### Pattern 2: Code Quality Assessment

```python
async def assess_code_quality(
    code: str,
    service: AIAnalysisService
) -> Dict[str, Any]:
    """
    Assess code quality and suggest improvements.
    """
    result = await service.analyze(
        prompt=f"""
        Analyze this code:

        ```python
        {code}
        ```

        Return JSON:
        {{
            "quality_score": 1-10,
            "maintainability": 1-10,
            "readability": 1-10,
            "issues": [
                {{"severity": "high|medium|low", "description": "..."}}
            ],
            "suggestions": ["suggestion1", "suggestion2"]
        }}
        """,
        response_format="json",
        system_prompt="You are a senior code reviewer focusing on quality.",
        max_tokens=1500
    )

    return json.loads(result.response)
```

### Pattern 3: Workflow Selection

```python
async def select_workflows(
    scale_level: int,
    project_type: str,
    service: AIAnalysisService
) -> list[str]:
    """
    Select appropriate workflows based on scale and type.
    """
    result = await service.analyze(
        prompt=f"""
        Select workflows for:
        - Scale Level: {scale_level}
        - Project Type: {project_type}

        Return JSON:
        {{
            "workflows": ["workflow1", "workflow2", "workflow3"],
            "rationale": "why these workflows"
        }}

        Available workflows:
        - prd: Product requirements
        - architecture: System design
        - epic: Epic creation
        - story: Story creation
        - implement: Implementation
        """,
        response_format="json"
    )

    data = json.loads(result.response)
    return data["workflows"]
```

### Pattern 4: Cost Tracking

```python
from dataclasses import dataclass
from typing import List

@dataclass
class AnalysisMetrics:
    total_calls: int = 0
    total_tokens: int = 0
    total_duration_ms: float = 0.0
    total_cost_usd: float = 0.0

class AnalysisTracker:
    """Track analysis metrics for cost monitoring."""

    def __init__(self, service: AIAnalysisService):
        self.service = service
        self.metrics = AnalysisMetrics()

    async def analyze_with_tracking(
        self,
        prompt: str,
        **kwargs
    ) -> AnalysisResult:
        """Analyze and track metrics."""
        result = await self.service.analyze(prompt=prompt, **kwargs)

        # Track metrics
        self.metrics.total_calls += 1
        self.metrics.total_tokens += result.tokens_used
        self.metrics.total_duration_ms += result.duration_ms

        # Estimate cost ($3 per million tokens for Sonnet 4.5)
        cost = result.tokens_used * 0.000003
        self.metrics.total_cost_usd += cost

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_calls": self.metrics.total_calls,
            "total_tokens": self.metrics.total_tokens,
            "avg_tokens_per_call": (
                self.metrics.total_tokens / self.metrics.total_calls
                if self.metrics.total_calls > 0 else 0
            ),
            "total_duration_ms": self.metrics.total_duration_ms,
            "avg_duration_ms": (
                self.metrics.total_duration_ms / self.metrics.total_calls
                if self.metrics.total_calls > 0 else 0
            ),
            "total_cost_usd": self.metrics.total_cost_usd
        }
```

---

## Testing

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.core.services import AIAnalysisService, AnalysisResult

@pytest.fixture
def mock_analysis_service():
    """Mock AIAnalysisService for testing."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='{"scale_level": 2, "estimated_stories": 8}',
        model_used="claude-sonnet-4-5-20250929",
        tokens_used=150,
        duration_ms=500.0
    ))
    return service

async def test_component_with_analysis(mock_analysis_service):
    """Test component that uses AIAnalysisService."""
    from my_module import MyOrchestrator

    # Create component with mocked service
    orchestrator = MyOrchestrator(
        analysis_service=mock_analysis_service
    )

    # Execute
    result = await orchestrator.analyze_and_route("Build a todo app")

    # Verify service was called
    mock_analysis_service.analyze.assert_called_once()

    # Verify result
    assert result is not None
    assert result["scale_level"] == 2
```

### Integration Testing

```python
import pytest
from gao_dev.core.services import AIAnalysisService

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_analysis():
    """Test with real API (requires ANTHROPIC_API_KEY)."""
    service = AIAnalysisService()

    result = await service.analyze(
        prompt="Rate complexity 1-10: def add(a, b): return a + b",
        response_format="json",
        max_tokens=100
    )

    # Verify response
    assert result.response
    assert result.tokens_used > 0
    assert result.duration_ms > 0

    # Parse JSON
    import json
    data = json.loads(result.response)
    assert "complexity" in data or "rating" in data
```

### Error Testing

```python
import pytest
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    InvalidModelError
)

@pytest.mark.asyncio
async def test_invalid_model():
    """Test handling of invalid model."""
    service = AIAnalysisService()

    with pytest.raises(InvalidModelError):
        await service.analyze(
            prompt="Test",
            model="non-existent-model"
        )

@pytest.mark.asyncio
async def test_error_recovery():
    """Test graceful error recovery."""
    service = AIAnalysisService()

    try:
        result = await service.analyze(
            prompt="Test",
            model="invalid-model"
        )
    except InvalidModelError:
        # Fallback to default model
        result = await service.analyze(prompt="Test")
        assert result is not None
```

---

## Best Practices

### 1. Use Dependency Injection

```python
# Good - Service injected, easy to test
class MyOrchestrator:
    def __init__(self, analysis_service: AIAnalysisService):
        self.analysis_service = analysis_service

    async def analyze(self, prompt: str):
        return await self.analysis_service.analyze(prompt)

# Avoid - Service created internally, hard to test
class MyOrchestrator:
    def __init__(self):
        self.analysis_service = AIAnalysisService()  # Hard to mock
```

### 2. Handle Errors Gracefully

```python
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError
)

async def robust_analysis(prompt: str, service: AIAnalysisService):
    """Analysis with error handling."""
    try:
        return await service.analyze(prompt=prompt)

    except AnalysisTimeoutError:
        # Retry with smaller max_tokens
        logger.warning("Analysis timed out, retrying with smaller limit")
        return await service.analyze(prompt=prompt, max_tokens=1024)

    except InvalidModelError:
        # Fallback to cheaper model
        logger.warning("Model not found, using fallback")
        return await service.analyze(
            prompt=prompt,
            model="claude-3-haiku-20240307"
        )

    except AnalysisError as e:
        # Log and raise
        logger.error("analysis_failed", error=str(e), exc_info=True)
        raise
```

### 3. Validate JSON Responses

```python
import json
from jsonschema import validate, ValidationError

async def validated_analysis(prompt: str, service: AIAnalysisService):
    """Analyze with JSON schema validation."""
    result = await service.analyze(prompt=prompt, response_format="json")

    # Define expected schema
    schema = {
        "type": "object",
        "properties": {
            "scale_level": {"type": "integer", "minimum": 0, "maximum": 4},
            "estimated_stories": {"type": "integer", "minimum": 1}
        },
        "required": ["scale_level", "estimated_stories"]
    }

    # Parse and validate
    try:
        data = json.loads(result.response)
        validate(instance=data, schema=schema)
        return data
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error("invalid_response", error=str(e), response=result.response)
        raise AnalysisError(f"Invalid response format: {e}")
```

### 4. Log Metrics

```python
import structlog

logger = structlog.get_logger()

async def analyzed_with_logging(prompt: str, service: AIAnalysisService):
    """Analyze with comprehensive logging."""
    logger.info(
        "analysis_started",
        prompt_length=len(prompt)
    )

    result = await service.analyze(prompt=prompt)

    logger.info(
        "analysis_completed",
        model=result.model_used,
        tokens=result.tokens_used,
        duration_ms=result.duration_ms,
        cost_estimate=result.tokens_used * 0.000003
    )

    return result
```

### 5. Choose Right Model for Task

```python
async def smart_model_selection(task_complexity: str, service: AIAnalysisService):
    """Select model based on task complexity."""

    # Simple task - use Haiku (fast, cheap)
    if task_complexity == "simple":
        model = "claude-3-haiku-20240307"
        max_tokens = 512

    # Complex task - use Sonnet 4.5 (balanced)
    elif task_complexity == "complex":
        model = "claude-sonnet-4-5-20250929"
        max_tokens = 2048

    # Critical task - use Opus (best quality)
    else:  # critical
        model = "claude-3-opus-20240229"
        max_tokens = 4096

    result = await service.analyze(
        prompt="...",
        model=model,
        max_tokens=max_tokens
    )

    return result
```

---

## Troubleshooting

### Issue: "API key required" Error

**Cause**: ANTHROPIC_API_KEY not set

**Solution**:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

Or pass explicitly:
```python
service = AIAnalysisService(api_key="sk-ant-...")
```

---

### Issue: JSON Parsing Fails

**Cause**: AI returned invalid JSON

**Solution**:
```python
import json

result = await service.analyze(prompt="...", response_format="json")

try:
    data = json.loads(result.response)
except json.JSONDecodeError:
    # Fallback: use text response or retry
    logger.warning("invalid_json", response=result.response)
    # Retry with stronger instructions
    result = await service.analyze(
        prompt="... IMPORTANT: Return ONLY valid JSON, no markdown",
        response_format="json"
    )
```

---

### Issue: Timeout Errors

**Cause**: Request too large or complex

**Solution**:
```python
# Reduce max_tokens
result = await service.analyze(
    prompt="...",
    max_tokens=1024  # Instead of 4096
)

# Or use faster model
result = await service.analyze(
    prompt="...",
    model="claude-3-haiku-20240307"
)
```

---

### Issue: High Costs

**Cause**: Too many tokens or expensive model

**Solution**:
```python
# Use cheaper model
result = await service.analyze(
    prompt="...",
    model="claude-3-haiku-20240307"  # $0.25 per million tokens
)

# Limit max_tokens
result = await service.analyze(
    prompt="...",
    max_tokens=512  # Reduce output length
)

# Make prompts more concise
prompt = "Rate complexity 1-10 for: <code>"  # Short and specific
```

---

## See Also

- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture decisions
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migration from direct API
- [LOCAL_MODELS_SETUP.md](./LOCAL_MODELS_SETUP.md) - Use local models for free

---

**Guide Version**: 1.0
**Last Updated**: 2025-11-07
**Feedback**: Open an issue or PR with suggestions
