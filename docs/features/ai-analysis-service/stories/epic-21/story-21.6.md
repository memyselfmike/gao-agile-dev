# Story 21.6: Documentation & Examples

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Story Points**: 3
**Status**: Blocked (depends on Stories 21.1-21.5)
**Priority**: Medium
**Assignee**: TBD

---

## User Story

As a **developer**, I want **comprehensive documentation for AIAnalysisService and local model setup**, so that **I can easily use the service in my components and run GAO-Dev with local models**.

---

## Context

With AIAnalysisService implemented and Brian refactored, we need complete documentation covering:
1. **API Documentation**: How to use AIAnalysisService
2. **Architecture Documentation**: Why we chose this approach
3. **Usage Examples**: Common patterns and use cases
4. **Migration Guide**: How to migrate components from direct API calls
5. **Setup Guide**: How to use local models (Ollama + deepseek-r1)
6. **Best Practices**: When to use service vs. agent

---

## Acceptance Criteria

### AC1: API Documentation
- [ ] Complete AIAnalysisService API docs
- [ ] Class overview and purpose
- [ ] Method signatures with examples
- [ ] Parameter descriptions
- [ ] Return value documentation
- [ ] Exception documentation
- [ ] Usage examples

### AC2: Architecture Decision Record
- [ ] Document why AIAnalysisService was created
- [ ] Explain Brian's classification (orchestrator vs. agent)
- [ ] Justify design decisions
- [ ] Document alternatives considered
- [ ] Trade-offs and benefits

### AC3: Usage Examples
- [ ] Basic usage example
- [ ] Advanced usage with custom model
- [ ] Error handling example
- [ ] Testing example (mocking)
- [ ] Integration with existing code

### AC4: Migration Guide
- [ ] When to use AIAnalysisService vs. IAgent
- [ ] How to migrate from direct API calls
- [ ] Step-by-step migration process
- [ ] Common pitfalls and solutions
- [ ] Testing strategies

### AC5: Local Model Setup Guide
- [ ] Install Ollama instructions
- [ ] Pull deepseek-r1 model
- [ ] Configure OpenCode server
- [ ] Set environment variables
- [ ] Run benchmark instructions
- [ ] Troubleshooting section

### AC6: Update README.md
- [ ] Add local model support section
- [ ] Link to setup guide
- [ ] Performance comparison table
- [ ] Cost comparison (free vs. paid)
- [ ] Quick start example

### AC7: Best Practices Guide
- [ ] When to use AIAnalysisService
- [ ] When to use IAgent
- [ ] Model selection guidelines
- [ ] Performance optimization tips
- [ ] Cost optimization tips

### AC8: Code Comments
- [ ] All public methods documented
- [ ] Complex logic explained
- [ ] Examples in docstrings
- [ ] Type hints complete

---

## Technical Details

### Documentation Files to Create/Update

```
docs/
├── features/
│   └── ai-analysis-service/
│       ├── PRD.md                          # EXISTS
│       ├── EPIC-21-PLAN.md                 # EXISTS
│       ├── ARCHITECTURE.md                 # NEW - Architecture decision record
│       ├── API_REFERENCE.md                # NEW - Complete API docs
│       ├── USAGE_GUIDE.md                  # NEW - How to use the service
│       ├── MIGRATION_GUIDE.md              # NEW - Migration from direct API
│       └── LOCAL_MODELS_SETUP.md           # NEW - Ollama setup guide
│
├── analysis/
│   └── brian-architecture-analysis.md      # EXISTS
│
└── examples/
    └── ai-analysis-service/                # NEW - Code examples
        ├── basic_usage.py
        ├── custom_model.py
        ├── error_handling.py
        └── testing_example.py

README.md                                   # UPDATE - Add local model section
```

### ARCHITECTURE.md Template

```markdown
# AI Analysis Service Architecture

## Problem Statement

Brian orchestrator uses Anthropic client directly, preventing:
- Use of local models (Ollama + deepseek-r1)
- Use of alternative providers (OpenCode)
- Testing without live API
- Architectural consistency

## Solution: AIAnalysisService

### Decision

Create AIAnalysisService - a reusable service for analysis-only AI calls.

### Why Service Instead of IAgent?

**Brian is not an agent:**
- No artifacts created
- No tools used
- Single-shot analysis
- Returns decisions, not work products

**IAgent is too heavy:**
- Designed for artifact-creating agents
- Full tool access (Read, Write, Bash, etc.)
- Complex lifecycle management
- Overengineering for analysis tasks

**Service is right fit:**
- Simple interface for analysis
- Lightweight abstraction
- Reusable across components
- Easy to test

### Architecture

```
Component (Brian, etc.)
    ↓ uses
AIAnalysisService
    ↓ uses
ProcessExecutor
    ↓ uses
Provider Abstraction
    ↓
Any Provider (Claude, OpenCode, local models)
```

### Benefits

1. **Provider Independence**: Works with any AI provider
2. **Cost Savings**: Free local models for development
3. **Testability**: Easy to mock for testing
4. **Reusability**: Any component can use for analysis
5. **Consistency**: All components use provider abstraction

### Trade-offs

**Pros:**
- Clean separation of concerns
- Reusable service
- Right level of abstraction
- Easy to test

**Cons:**
- New service to maintain
- Slightly more complexity than direct calls
- Learning curve for developers

**Verdict**: Benefits far outweigh costs.

## Future Extensions

- Cost estimation service
- Code review summarization
- Complexity analysis for other components
- Multi-model analysis (consensus)
```

### API_REFERENCE.md Template

```markdown
# AIAnalysisService API Reference

## Overview

AIAnalysisService provides provider-abstracted AI calls for analysis tasks.

## Class: AIAnalysisService

### Constructor

```python
def __init__(
    self,
    executor: ProcessExecutor,
    default_model: Optional[str] = None
)
```

**Parameters:**
- `executor`: ProcessExecutor instance for provider abstraction
- `default_model`: Default model to use if not specified per-call

**Example:**
```python
from gao_dev.core.services import AIAnalysisService
from gao_dev.core.process_executor import ProcessExecutor

executor = ProcessExecutor(provider="opencode-sdk")
service = AIAnalysisService(
    executor=executor,
    default_model="deepseek-r1"
)
```

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

**Parameters:**
- `prompt`: User prompt for analysis (required)
- `model`: Model to use (defaults to configured model)
- `system_prompt`: Optional system instructions
- `response_format`: "json" or "text"
- `max_tokens`: Maximum response length
- `temperature`: Sampling temperature (0.0-1.0)

**Returns:**
- `AnalysisResult` with response, model_used, tokens_used, duration_ms

**Raises:**
- `AnalysisError`: If analysis fails

**Example:**
```python
result = await service.analyze(
    prompt="Analyze project complexity",
    model="deepseek-r1",
    response_format="json"
)

print(result.response)  # JSON string
print(f"Used {result.tokens_used} tokens in {result.duration_ms}ms")
```

## Class: AnalysisResult

```python
@dataclass
class AnalysisResult:
    response: str           # AI response
    model_used: str         # Model that processed request
    tokens_used: int        # Token count
    duration_ms: float      # Processing time
```

## Exceptions

### AnalysisError

Base exception for AI analysis errors.

### AnalysisTimeoutError

Analysis request timed out.

### InvalidModelError

Requested model is invalid or unavailable.
```

### LOCAL_MODELS_SETUP.md Template

```markdown
# Local Models Setup Guide

## Overview

Run GAO-Dev with free local models using Ollama + deepseek-r1.

## Benefits

- **Free**: No API costs
- **Private**: Data stays local
- **Offline**: No internet required
- **Fast**: No network latency

## Prerequisites

- MacOS, Linux, or Windows with WSL
- 8GB+ RAM (16GB recommended)
- 10GB+ disk space

## Step 1: Install Ollama

### MacOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows (WSL)
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## Step 2: Pull DeepSeek-R1 Model

```bash
# Pull 8B model (recommended)
ollama pull deepseek-r1:8b

# Verify
ollama list
# Should show: deepseek-r1:8b
```

## Step 3: Start Ollama Service

```bash
# Start Ollama
ollama serve

# Verify (in another terminal)
curl http://localhost:11434/api/tags
# Should return list of models
```

## Step 4: Configure OpenCode (Optional)

If using OpenCode provider:

```bash
# Create opencode.json
cat > opencode.json <<EOF
{
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "deepseek-r1:8b": {
          "name": "DeepSeek R1 8B",
          "tools": true
        }
      }
    }
  }
}
EOF

# Start OpenCode server
opencode start
```

## Step 5: Set Environment Variables

```bash
export AGENT_PROVIDER=opencode-sdk
export GAO_DEV_MODEL=deepseek-r1
```

## Step 6: Run Benchmark

```bash
# Run benchmark with local model
python run_deepseek_benchmark.py

# Or use CLI
gao-dev sandbox run sandbox/benchmarks/simple-todo-deepseek.yaml
```

## Troubleshooting

### Issue: Connection Refused
**Solution**: Ensure Ollama is running (`ollama serve`)

### Issue: Model Not Found
**Solution**: Pull model (`ollama pull deepseek-r1:8b`)

### Issue: Slow Performance
**Solution**: Normal for CPU inference. Consider GPU for faster results.

## Performance Comparison

| Metric | DeepSeek-R1 | Claude Sonnet 4.5 |
|--------|-------------|-------------------|
| Cost | $0 | $0.01-0.05 |
| Speed | 5-15s | 2-5s |
| Quality | Good | Excellent |
| Offline | Yes | No |
```

---

## Example Files

### basic_usage.py

```python
"""
Basic usage example for AIAnalysisService.
"""
import asyncio
from gao_dev.core.services import AIAnalysisService
from gao_dev.core.process_executor import ProcessExecutor


async def main():
    # Create executor (uses provider from environment)
    executor = ProcessExecutor(provider="opencode-sdk")

    # Create analysis service
    service = AIAnalysisService(
        executor=executor,
        default_model="deepseek-r1"
    )

    # Analyze a prompt
    result = await service.analyze(
        prompt="Analyze the complexity of building a todo application",
        response_format="json"
    )

    print("Response:", result.response)
    print(f"Model: {result.model_used}")
    print(f"Tokens: {result.tokens_used}")
    print(f"Duration: {result.duration_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
```

### testing_example.py

```python
"""
Example of testing components that use AIAnalysisService.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.core.services import AIAnalysisService, AnalysisResult


@pytest.fixture
def mock_analysis_service():
    """Mock AIAnalysisService for testing."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='{"complexity": "medium"}',
        model_used="test-model",
        tokens_used=100,
        duration_ms=500
    ))
    return service


async def test_my_component(mock_analysis_service):
    """Test component that uses analysis service."""
    from my_module import MyComponent

    component = MyComponent(analysis_service=mock_analysis_service)

    result = await component.do_something()

    # Verify service was called
    mock_analysis_service.analyze.assert_called_once()

    # Verify result
    assert result is not None
```

---

## Definition of Done

- [ ] All documentation files created
- [ ] API reference complete
- [ ] Architecture decision record written
- [ ] Usage examples working
- [ ] Migration guide complete
- [ ] Local model setup guide tested
- [ ] README.md updated
- [ ] Code comments complete
- [ ] Docs reviewed and approved

---

## Review Checklist

- [ ] Documentation is clear and concise
- [ ] Examples are correct and tested
- [ ] All links work
- [ ] Formatting consistent
- [ ] Technical accuracy verified
- [ ] Beginner-friendly language
- [ ] Advanced topics covered
- [ ] Troubleshooting comprehensive

---

## Dependencies

- **Story 21.1** (required): AIAnalysisService implemented
- **Story 21.2** (required): Brian refactored
- **Story 21.5** (required): Benchmark validated (for performance data)

---

## Related Documents

- **Epic 21 Plan**: `docs/features/ai-analysis-service/EPIC-21-PLAN.md`
- **PRD**: `docs/features/ai-analysis-service/PRD.md`
- **Architecture Analysis**: `docs/analysis/brian-architecture-analysis.md`
- **AIAnalysisService**: `gao_dev/core/services/ai_analysis_service.py`
