# AIAnalysisService API Reference

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Version**: 1.0
**Status**: Stable
**Last Updated**: 2025-11-07

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [AIAnalysisService Class](#aianalysisservice-class)
5. [AnalysisResult Class](#analysisresult-class)
6. [Exceptions](#exceptions)
7. [Configuration](#configuration)
8. [Examples](#examples)

---

## Overview

`AIAnalysisService` provides a simple, provider-abstracted interface for AI-powered analysis tasks without the overhead of full agent capabilities.

**Use this service when you need:**
- Quick AI-powered decision-making
- Complexity analysis
- Code review suggestions
- Structured JSON responses
- Lightweight analysis without artifacts

**Don't use this service when you need:**
- Full agent with tools (Read, Write, Bash, etc.)
- Artifact creation (files, commits)
- Complex multi-step workflows
- Stateful interactions

---

## Installation

The service is included with GAO-Dev. No additional installation needed.

```bash
# Already installed with GAO-Dev
pip install -e .
```

**Dependencies:**
- `anthropic` (required)
- `structlog` (required)
- Python 3.11+

---

## Quick Start

```python
import asyncio
from gao_dev.core.services import AIAnalysisService

async def main():
    # Create service (uses ANTHROPIC_API_KEY from environment)
    service = AIAnalysisService(
        default_model="claude-sonnet-4-5-20250929"
    )

    # Analyze a prompt
    result = await service.analyze(
        prompt="Analyze the complexity of building a todo app with auth",
        response_format="json"
    )

    print("Response:", result.response)
    print(f"Tokens used: {result.tokens_used}")
    print(f"Duration: {result.duration_ms}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## AIAnalysisService Class

### Constructor

```python
def __init__(
    self,
    api_key: Optional[str] = None,
    default_model: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | `str \| None` | No | `ANTHROPIC_API_KEY` env var | Anthropic API key for authentication |
| `default_model` | `str \| None` | No | `GAO_DEV_MODEL` env var or `"claude-sonnet-4-5-20250929"` | Default model to use for analysis |

**Raises:**
- `ValueError`: If API key not provided and not in environment
- `ImportError`: If `anthropic` package not installed

**Example:**

```python
# Use environment variables (recommended)
service = AIAnalysisService()

# Explicit configuration
service = AIAnalysisService(
    api_key="sk-ant-...",
    default_model="claude-sonnet-4-5-20250929"
)
```

**Environment Variables:**
- `ANTHROPIC_API_KEY`: API key (required if not passed to constructor)
- `GAO_DEV_MODEL`: Default model name (optional)

---

### Method: analyze()

```python
async def analyze(
    self,
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    response_format: str = "json",
    max_tokens: int = 2048,
    temperature: float = 0.7
) -> AnalysisResult
```

Send analysis prompt to AI provider and return structured result.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | `str` | Yes | - | User prompt for analysis |
| `model` | `str \| None` | No | Service default | Model to use for this request |
| `system_prompt` | `str \| None` | No | `None` | Optional system instructions |
| `response_format` | `str` | No | `"json"` | Expected response format (`"json"` or `"text"`) |
| `max_tokens` | `int` | No | `2048` | Maximum response length in tokens |
| `temperature` | `float` | No | `0.7` | Sampling temperature (0.0-1.0) |

**Returns:**
- `AnalysisResult`: Result object with response and metadata

**Raises:**
- `AnalysisError`: Base exception for analysis failures
- `AnalysisTimeoutError`: Request timed out
- `InvalidModelError`: Model invalid or unavailable

**Example - JSON Response:**

```python
result = await service.analyze(
    prompt="Rate this code complexity from 1-10: def add(a, b): return a + b",
    response_format="json",
    system_prompt="You are a code analyzer. Return JSON with 'complexity' field."
)

import json
data = json.loads(result.response)
print(f"Complexity: {data['complexity']}/10")
```

**Example - Text Response:**

```python
result = await service.analyze(
    prompt="Explain how to optimize this function",
    response_format="text",
    system_prompt="You are a performance expert."
)

print(result.response)  # Human-readable explanation
```

**Example - Custom Model:**

```python
# Override default model for this request
result = await service.analyze(
    prompt="Quick yes/no: Is this code thread-safe?",
    model="claude-3-haiku-20240307",  # Faster, cheaper model
    max_tokens=100
)
```

**Example - Temperature Control:**

```python
# Low temperature for deterministic output
result = await service.analyze(
    prompt="Calculate code complexity",
    temperature=0.0  # More deterministic
)

# High temperature for creative output
result = await service.analyze(
    prompt="Suggest creative refactoring ideas",
    temperature=0.9  # More creative
)
```

---

## AnalysisResult Class

```python
@dataclass
class AnalysisResult:
    response: str
    model_used: str
    tokens_used: int
    duration_ms: float
```

Result object returned by `analyze()` method.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `response` | `str` | AI response content (text or JSON string) |
| `model_used` | `str` | Model that processed the request |
| `tokens_used` | `int` | Total tokens (input + output) |
| `duration_ms` | `float` | Processing time in milliseconds |

**Example Usage:**

```python
result = await service.analyze("Analyze this code")

# Access response
print(result.response)

# Access metadata
print(f"Model: {result.model_used}")
print(f"Cost estimate: ${result.tokens_used * 0.000003:.4f}")  # Rough estimate
print(f"Latency: {result.duration_ms}ms")

# Parse JSON response
if result.response.startswith('{'):
    data = json.loads(result.response)
    print(data)
```

---

## Exceptions

### AnalysisError

```python
class AnalysisError(Exception):
    """Base exception for AI analysis errors."""
```

Base exception class for all analysis failures.

**When Raised:**
- General analysis failures
- Anthropic API errors
- Unexpected errors

**Example:**

```python
from gao_dev.core.providers.exceptions import AnalysisError

try:
    result = await service.analyze(prompt="...")
except AnalysisError as e:
    print(f"Analysis failed: {e}")
```

---

### AnalysisTimeoutError

```python
class AnalysisTimeoutError(AnalysisError):
    """Analysis request timed out."""
```

Raised when analysis operation times out.

**When Raised:**
- Request exceeds provider timeout
- Network timeout

**Example:**

```python
from gao_dev.core.providers.exceptions import AnalysisTimeoutError

try:
    result = await service.analyze(prompt="...", max_tokens=8000)
except AnalysisTimeoutError as e:
    print(f"Request timed out: {e}")
    # Retry with smaller max_tokens or different model
```

---

### InvalidModelError

```python
class InvalidModelError(AnalysisError):
    """Requested model is invalid or unavailable."""
```

Raised when model not found or not supported.

**When Raised:**
- Model name misspelled
- Model not available on provider
- Model deprecated or removed

**Example:**

```python
from gao_dev.core.providers.exceptions import InvalidModelError

try:
    result = await service.analyze(prompt="...", model="invalid-model")
except InvalidModelError as e:
    print(f"Model not found: {e}")
    # Fall back to default model
    result = await service.analyze(prompt="...")
```

---

## Configuration

### Environment Variables

**ANTHROPIC_API_KEY** (required)
- Your Anthropic API key
- Get from: https://console.anthropic.com/
- Example: `sk-ant-api03-...`

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**GAO_DEV_MODEL** (optional)
- Default model for all requests
- Overrides service default
- Example: `claude-sonnet-4-5-20250929`

```bash
export GAO_DEV_MODEL="claude-3-haiku-20240307"  # Use cheaper model
```

---

### Supported Models

**Claude Sonnet 4.5** (Recommended)
- Model ID: `claude-sonnet-4-5-20250929`
- Best balance of speed, quality, cost
- Use for: Complex analysis, production

**Claude 3 Opus**
- Model ID: `claude-3-opus-20240229`
- Highest quality
- Use for: Critical analysis, complex reasoning

**Claude 3 Sonnet**
- Model ID: `claude-3-sonnet-20240229`
- Balanced
- Use for: General analysis

**Claude 3 Haiku**
- Model ID: `claude-3-haiku-20240307`
- Fastest, cheapest
- Use for: Simple analysis, high volume

---

## Examples

### Example 1: Complexity Analysis

```python
async def analyze_project_complexity(project_description: str):
    """Analyze project complexity and recommend scale level."""
    service = AIAnalysisService()

    result = await service.analyze(
        prompt=f"""
        Analyze this project and recommend a scale level (0-4):

        {project_description}

        Return JSON:
        {{
            "scale_level": 0-4,
            "rationale": "explanation",
            "estimated_stories": 10,
            "complexity_factors": ["factor1", "factor2"]
        }}
        """,
        response_format="json",
        system_prompt="You are a project complexity analyzer."
    )

    import json
    analysis = json.loads(result.response)
    return analysis
```

### Example 2: Code Review

```python
async def review_code_snippet(code: str):
    """Get AI code review suggestions."""
    service = AIAnalysisService()

    result = await service.analyze(
        prompt=f"""
        Review this code and suggest improvements:

        ```python
        {code}
        ```

        Return JSON:
        {{
            "quality_score": 1-10,
            "issues": ["issue1", "issue2"],
            "suggestions": ["suggestion1", "suggestion2"]
        }}
        """,
        response_format="json",
        temperature=0.3  # More deterministic for code review
    )

    return json.loads(result.response)
```

### Example 3: Multi-Model Comparison

```python
async def compare_models(prompt: str):
    """Compare responses from different models."""
    service = AIAnalysisService()

    models = [
        "claude-sonnet-4-5-20250929",
        "claude-3-haiku-20240307"
    ]

    results = []
    for model in models:
        result = await service.analyze(
            prompt=prompt,
            model=model,
            response_format="json"
        )
        results.append({
            "model": result.model_used,
            "response": result.response,
            "tokens": result.tokens_used,
            "duration_ms": result.duration_ms
        })

    return results
```

### Example 4: Error Handling

```python
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError
)

async def robust_analysis(prompt: str):
    """Analysis with comprehensive error handling."""
    service = AIAnalysisService()

    try:
        result = await service.analyze(prompt=prompt)
        return result.response

    except AnalysisTimeoutError:
        print("Request timed out, retrying with smaller max_tokens")
        result = await service.analyze(prompt=prompt, max_tokens=1024)
        return result.response

    except InvalidModelError:
        print("Model not found, using default")
        service.default_model = "claude-3-haiku-20240307"
        result = await service.analyze(prompt=prompt)
        return result.response

    except AnalysisError as e:
        print(f"Analysis failed: {e}")
        return None
```

---

## Best Practices

### 1. Use Environment Variables

```python
# Good - Uses environment variables
service = AIAnalysisService()

# Avoid - Hardcoded credentials
service = AIAnalysisService(api_key="sk-ant-...")
```

### 2. Request JSON When Possible

```python
# Good - Structured, parseable
result = await service.analyze(prompt, response_format="json")

# Use text only when truly needed
result = await service.analyze(prompt, response_format="text")
```

### 3. Handle Errors Gracefully

```python
# Good - Specific error handling
try:
    result = await service.analyze(prompt)
except InvalidModelError:
    # Fallback to different model
    result = await service.analyze(prompt, model="claude-3-haiku-20240307")
except AnalysisError as e:
    # Log and handle gracefully
    logger.error("analysis_failed", error=str(e))
```

### 4. Choose Right Model

```python
# Quick yes/no decisions - use Haiku (fast, cheap)
result = await service.analyze(prompt, model="claude-3-haiku-20240307")

# Complex analysis - use Sonnet 4.5 (balanced)
result = await service.analyze(prompt, model="claude-sonnet-4-5-20250929")

# Critical decisions - use Opus (best quality)
result = await service.analyze(prompt, model="claude-3-opus-20240229")
```

### 5. Monitor Costs

```python
result = await service.analyze(prompt)

# Estimate cost (rough approximation)
input_cost = result.tokens_used * 0.000003  # $3 per million tokens
print(f"Estimated cost: ${input_cost:.4f}")

# Track over time
logger.info("analysis_cost", tokens=result.tokens_used, cost=input_cost)
```

---

## Performance Tips

### Reduce Latency

```python
# Use faster model
result = await service.analyze(prompt, model="claude-3-haiku-20240307")

# Lower max_tokens
result = await service.analyze(prompt, max_tokens=512)

# Consider caching results for identical prompts
```

### Reduce Cost

```python
# Use cheaper model when quality difference is minimal
result = await service.analyze(prompt, model="claude-3-haiku-20240307")

# Limit max_tokens
result = await service.analyze(prompt, max_tokens=1024)

# Batch similar analyses together
```

---

## Testing

See [USAGE_GUIDE.md](./USAGE_GUIDE.md) for testing examples with mocks.

---

## See Also

- [USAGE_GUIDE.md](./USAGE_GUIDE.md) - Comprehensive usage guide
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture decisions
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migration instructions
- [LOCAL_MODELS_SETUP.md](./LOCAL_MODELS_SETUP.md) - Local model setup

---

**API Version**: 1.0
**Status**: Stable
**Last Updated**: 2025-11-07
