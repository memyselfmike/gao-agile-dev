# AIAnalysisService Migration Guide

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Version**: 1.0
**Audience**: Developers migrating to AIAnalysisService
**Last Updated**: 2025-11-07

---

## Table of Contents

1. [Overview](#overview)
2. [When to Migrate](#when-to-migrate)
3. [Migration Steps](#migration-steps)
4. [Before and After Examples](#before-and-after-examples)
5. [Testing Migration](#testing-migration)
6. [Common Pitfalls](#common-pitfalls)
7. [Rollback Plan](#rollback-plan)

---

## Overview

This guide helps you migrate from direct Anthropic API calls to the new `AIAnalysisService`. This migration provides:

- **Provider abstraction** - Switch between Claude, local models, etc.
- **Better testability** - Easy to mock for unit tests
- **Cost savings** - Use free local models for development
- **Consistency** - All components use same pattern

---

## When to Migrate

### Migrate to AIAnalysisService When:

Your component has code that:
- Imports `anthropic` directly
- Creates `AsyncAnthropic` client
- Calls `client.messages.create()` for analysis
- Doesn't create artifacts (files, commits)
- Returns decisions or analysis results

**Example code to migrate:**
```python
import anthropic

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": prompt}]
)
```

### Do NOT Migrate When:

Your component:
- Is already an IAgent with tools (Read, Write, etc.)
- Creates artifacts (files, commits, etc.)
- Needs multi-step workflows
- Maintains conversation state

**Keep using IAgent for artifact-creating agents.**

---

## Migration Steps

### Step 1: Identify Direct API Calls

Search your codebase for direct Anthropic usage:

```bash
# Find files with direct Anthropic imports
grep -r "import anthropic" gao_dev/

# Find AsyncAnthropic usage
grep -r "AsyncAnthropic" gao_dev/

# Find messages.create calls
grep -r "messages.create" gao_dev/
```

**Example findings:**
- `gao_dev/orchestrator/brian_orchestrator.py` - MIGRATE
- `gao_dev/agents/john.py` - DON'T MIGRATE (uses IAgent)

---

### Step 2: Install Dependencies

Ensure AIAnalysisService dependencies are installed:

```bash
pip install anthropic structlog
```

Or update your requirements:

```toml
# pyproject.toml
[project]
dependencies = [
    "anthropic>=0.40.0",
    "structlog>=24.1.0",
    # ... other deps
]
```

---

### Step 3: Update Imports

**Before:**
```python
import anthropic
import os
```

**After:**
```python
from gao_dev.core.services import AIAnalysisService, AnalysisResult
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError
)
```

---

### Step 4: Replace Client Initialization

**Before:**
```python
class MyOrchestrator:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
```

**After:**
```python
class MyOrchestrator:
    def __init__(
        self,
        analysis_service: Optional[AIAnalysisService] = None
    ):
        # Accept service via dependency injection (better for testing)
        self.analysis_service = analysis_service or AIAnalysisService()
```

---

### Step 5: Replace API Calls

**Before:**
```python
async def analyze(self, prompt: str):
    response = await self.client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract text
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    return text
```

**After:**
```python
async def analyze(self, prompt: str):
    result = await self.analysis_service.analyze(
        prompt=prompt,
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        temperature=0.7,
        response_format="json"
    )

    return result.response
```

---

### Step 6: Update Error Handling

**Before:**
```python
try:
    response = await self.client.messages.create(...)
except anthropic.APITimeoutError as e:
    logger.error("Timeout", error=str(e))
except anthropic.NotFoundError as e:
    logger.error("Model not found", error=str(e))
except anthropic.APIError as e:
    logger.error("API error", error=str(e))
```

**After:**
```python
try:
    result = await self.analysis_service.analyze(...)
except AnalysisTimeoutError as e:
    logger.error("Timeout", error=str(e))
except InvalidModelError as e:
    logger.error("Model not found", error=str(e))
except AnalysisError as e:
    logger.error("Analysis error", error=str(e))
```

---

### Step 7: Update Tests

**Before:**
```python
@pytest.fixture
def mock_anthropic():
    with patch('anthropic.AsyncAnthropic') as mock:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="response")]
        mock.return_value.messages.create.return_value = mock_response
        yield mock
```

**After:**
```python
@pytest.fixture
def mock_analysis_service():
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='{"result": "data"}',
        model_used="claude-sonnet-4-5-20250929",
        tokens_used=100,
        duration_ms=500.0
    ))
    return service
```

---

## Before and After Examples

### Example 1: Brian Orchestrator

**Before (Story 21.1):**

```python
# gao_dev/orchestrator/brian_orchestrator.py
import anthropic
import os
import json

class BrianOrchestrator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def analyze_complexity(self, user_prompt: str):
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze complexity: {user_prompt}"
                }
            ]
        )

        # Extract response
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text

        return json.loads(text)
```

**After (Story 21.2):**

```python
# gao_dev/orchestrator/brian_orchestrator.py
from gao_dev.core.services import AIAnalysisService, AnalysisResult
from gao_dev.core.providers.exceptions import AnalysisError
import json

class BrianOrchestrator:
    def __init__(
        self,
        analysis_service: Optional[AIAnalysisService] = None
    ):
        # Dependency injection for testability
        self.analysis_service = analysis_service or AIAnalysisService()

    async def analyze_complexity(self, user_prompt: str):
        try:
            result = await self.analysis_service.analyze(
                prompt=f"Analyze complexity: {user_prompt}",
                response_format="json",
                max_tokens=2048,
                temperature=0.7
            )

            return json.loads(result.response)

        except AnalysisError as e:
            logger.error("complexity_analysis_failed", error=str(e))
            raise
```

**Key Changes:**
1. No direct `anthropic` import
2. Service injected via constructor (testable)
3. Simpler error handling
4. Cleaner code (less boilerplate)

---

### Example 2: Generic Analysis Component

**Before:**

```python
import anthropic

class CodeReviewer:
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def review_code(self, code: str):
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": f"Review this code:\n{code}"
                }
            ],
            system="You are a code reviewer"
        )

        return response.content[0].text
```

**After:**

```python
from gao_dev.core.services import AIAnalysisService

class CodeReviewer:
    def __init__(self, analysis_service: Optional[AIAnalysisService] = None):
        self.analysis_service = analysis_service or AIAnalysisService()

    async def review_code(self, code: str):
        result = await self.analysis_service.analyze(
            prompt=f"Review this code:\n{code}",
            system_prompt="You are a code reviewer",
            response_format="json",
            max_tokens=1500
        )

        return result.response
```

---

### Example 3: Test Migration

**Before:**

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_analyze_complexity():
    with patch('anthropic.AsyncAnthropic') as mock_anthropic:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"scale_level": 2}')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Test
        orchestrator = BrianOrchestrator()
        result = await orchestrator.analyze_complexity("Build todo app")

        assert result["scale_level"] == 2
```

**After:**

```python
import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.core.services import AnalysisResult

@pytest.fixture
def mock_service():
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='{"scale_level": 2}',
        model_used="claude-sonnet-4-5-20250929",
        tokens_used=100,
        duration_ms=500.0
    ))
    return service

@pytest.mark.asyncio
async def test_analyze_complexity(mock_service):
    # Test with mocked service
    orchestrator = BrianOrchestrator(analysis_service=mock_service)
    result = await orchestrator.analyze_complexity("Build todo app")

    # Verify
    assert result["scale_level"] == 2
    mock_service.analyze.assert_called_once()
```

**Key Improvements:**
1. Cleaner mock setup
2. Dependency injection
3. Easier to maintain
4. More explicit assertions

---

## Testing Migration

### Step 1: Run Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/integration/test_brian_orchestrator.py

# Run with coverage
pytest --cov=gao_dev tests/
```

### Step 2: Run Integration Tests

```bash
# Set API key for integration tests
export ANTHROPIC_API_KEY="sk-ant-..."

# Run integration tests
pytest tests/integration/ -m integration
```

### Step 3: Verify Functionality

```bash
# Test with real prompt
python -c "
import asyncio
from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator

async def test():
    orchestrator = BrianOrchestrator()
    result = await orchestrator.analyze_complexity('Build a todo app')
    print(result)

asyncio.run(test())
"
```

---

## Common Pitfalls

### Pitfall 1: Forgetting Dependency Injection

**Wrong:**
```python
class MyComponent:
    def __init__(self):
        self.service = AIAnalysisService()  # Hard to test
```

**Right:**
```python
class MyComponent:
    def __init__(self, service: Optional[AIAnalysisService] = None):
        self.service = service or AIAnalysisService()  # Easy to test
```

---

### Pitfall 2: Not Handling Exceptions

**Wrong:**
```python
result = await service.analyze(prompt)  # Can throw exceptions
return result.response
```

**Right:**
```python
try:
    result = await service.analyze(prompt)
    return result.response
except AnalysisError as e:
    logger.error("analysis_failed", error=str(e))
    raise
```

---

### Pitfall 3: Assuming JSON is Valid

**Wrong:**
```python
result = await service.analyze(prompt, response_format="json")
data = json.loads(result.response)  # Can fail if invalid JSON
```

**Right:**
```python
result = await service.analyze(prompt, response_format="json")
try:
    data = json.loads(result.response)
except json.JSONDecodeError as e:
    logger.error("invalid_json", error=str(e), response=result.response)
    raise AnalysisError(f"Invalid JSON response: {e}")
```

---

### Pitfall 4: Not Updating Environment Variables

**Issue:** Code expects `ANTHROPIC_API_KEY` but it's not set

**Solution:**
```bash
# Set before running
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

---

## Rollback Plan

If migration causes issues, you can rollback:

### Option 1: Keep Old Code Temporarily

```python
class BrianOrchestrator:
    def __init__(
        self,
        analysis_service: Optional[AIAnalysisService] = None,
        use_legacy: bool = False  # Feature flag
    ):
        self.use_legacy = use_legacy
        if use_legacy:
            self.client = anthropic.AsyncAnthropic(...)
        else:
            self.analysis_service = analysis_service or AIAnalysisService()

    async def analyze(self, prompt: str):
        if self.use_legacy:
            return await self._analyze_legacy(prompt)
        else:
            return await self._analyze_new(prompt)
```

### Option 2: Git Revert

```bash
# Find commit before migration
git log --oneline

# Revert to previous commit
git revert <commit-hash>
```

### Option 3: Gradual Migration

Migrate one component at a time:

1. Week 1: Migrate Brian orchestrator
2. Week 2: Migrate complexity analyzer
3. Week 3: Remove legacy code

---

## Success Checklist

After migration, verify:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No direct `import anthropic` in migrated files
- [ ] Components accept service via dependency injection
- [ ] Error handling uses new exception types
- [ ] Tests use mocked service
- [ ] Documentation updated
- [ ] Environment variables set correctly
- [ ] No performance regression
- [ ] Cost tracking works

---

## Getting Help

If you encounter issues:

1. **Check logs**: Look for error messages in structlog output
2. **Review tests**: Ensure test setup matches new pattern
3. **Check environment**: Verify `ANTHROPIC_API_KEY` is set
4. **Read docs**: Review [API_REFERENCE.md](./API_REFERENCE.md)
5. **Open issue**: If stuck, open GitHub issue with details

---

## References

- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API docs
- [USAGE_GUIDE.md](./USAGE_GUIDE.md) - Usage examples
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Why we created this service
- [Epic 21 Plan](./EPIC-21-PLAN.md) - Full migration plan

---

**Guide Version**: 1.0
**Last Updated**: 2025-11-07
**Migration Support**: Open an issue for help
