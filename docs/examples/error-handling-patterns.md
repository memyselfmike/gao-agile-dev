# Error Handling Patterns

Comprehensive error handling patterns from GAO-Dev.

---

## 1. API Validation Errors

**Context**: Handling Pydantic validation errors in FastAPI

**Example from**: `gao_dev/web/api/settings.py`

```python
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator


class ProviderSettings(BaseModel):
    """Provider settings with validation."""

    provider: str = Field(..., pattern="^(anthropic|openai|ollama)$")
    model: str = Field(..., min_length=1, max_length=100)
    api_key: str | None = None

    @validator('model')
    def validate_model(cls, v, values):
        """Validate model based on provider."""
        provider = values.get('provider')

        if provider == 'anthropic' and not v.startswith('claude-'):
            raise ValueError("Anthropic models must start with 'claude-'")

        if provider == 'openai' and not v.startswith('gpt-'):
            raise ValueError("OpenAI models must start with 'gpt-'")

        return v

    @validator('api_key')
    def validate_api_key(cls, v, values):
        """Ensure API key provided for cloud providers."""
        provider = values.get('provider')

        if provider in ('anthropic', 'openai') and not v:
            raise ValueError(f"{provider.title()} requires API key")

        return v


@router.post("/settings/provider")
async def update_provider(settings: ProviderSettings):
    """Update provider settings with comprehensive validation."""
    try:
        # Pydantic validates automatically
        # Additional business logic validation
        if settings.provider == 'ollama':
            # Check if Ollama is running
            import requests
            try:
                requests.get("http://localhost:11434/api/tags", timeout=2)
            except requests.RequestException:
                raise HTTPException(
                    status_code=503,
                    detail="Ollama server not running. Start it with: ollama serve"
                )

        # Save settings
        # ...

        return {"status": "success", "provider": settings.provider}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 2. File Operation Errors

**Context**: Handling file system errors with rollback

**Example from**: `gao_dev/core/services/git_integrated_state_manager.py`

```python
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class GitIntegratedStateManager:
    """State manager with atomic operations and rollback."""

    async def create_epic(self, epic_num: int, title: str, file_path: Path, content: str):
        """Create epic with automatic rollback on failure."""
        db_created = False
        file_created = False
        git_committed = False

        try:
            # Step 1: Create DB record
            logger.info("creating_epic_db_record", epic_num=epic_num)
            self.db.execute(
                "INSERT INTO epics (epic_num, title, status) VALUES (?, ?, ?)",
                (epic_num, title, "backlog")
            )
            db_created = True

            # Step 2: Write file
            logger.info("creating_epic_file", path=str(file_path))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            file_created = True

            # Step 3: Git commit
            logger.info("creating_epic_git_commit", epic_num=epic_num)
            self.git_manager.stage_files([file_path])
            commit_sha = self.git_manager.commit(
                f"feat(epic-{epic_num}): Create epic {epic_num} - {title}"
            )
            git_committed = True

            logger.info("epic_created_successfully", epic_num=epic_num, commit_sha=commit_sha)

        except Exception as e:
            logger.error("epic_creation_failed", epic_num=epic_num, error=str(e))

            # Rollback in reverse order
            if git_committed:
                try:
                    self.git_manager.reset_hard("HEAD~1")
                except Exception as rollback_error:
                    logger.error("git_rollback_failed", error=str(rollback_error))

            if file_created and file_path.exists():
                try:
                    file_path.unlink()
                except Exception as rollback_error:
                    logger.error("file_rollback_failed", error=str(rollback_error))

            if db_created:
                try:
                    self.db.execute("DELETE FROM epics WHERE epic_num = ?", (epic_num,))
                except Exception as rollback_error:
                    logger.error("db_rollback_failed", error=str(rollback_error))

            raise ValueError(f"Failed to create epic {epic_num}: {e}")
```

---

## 3. Network Request Errors

**Context**: Handling API requests with retries and timeouts

**Example from**: `gao_dev/core/providers/anthropic.py`

```python
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class AnthropicProvider:
    """Anthropic API provider with robust error handling."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def send_message(self, messages: list[dict], model: str) -> dict:
        """Send message with automatic retries."""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 4096
                    }
                )

                if response.status_code == 429:
                    # Rate limited - extract retry-after header
                    retry_after = int(response.headers.get("retry-after", 5))
                    logger.warning("rate_limited", retry_after=retry_after)
                    await asyncio.sleep(retry_after)
                    raise httpx.HTTPStatusError(
                        "Rate limited",
                        request=response.request,
                        response=response
                    )

                if response.status_code == 401:
                    raise ValueError("Invalid API key")

                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        "Server error",
                        request=response.request,
                        response=response
                    )

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error("request_timeout", model=model)
            raise ValueError("Request timed out after 300 seconds")

        except httpx.NetworkError as e:
            logger.error("network_error", error=str(e))
            raise ValueError(f"Network error: {e}")
```

---

## 4. Frontend Error Boundaries

**Context**: Catching React component errors gracefully

**Example from**: `gao_dev/web/frontend/src/components/ErrorBoundary.tsx`

```typescript
import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);

    // Send to error tracking service
    // trackError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-background">
          <div className="max-w-md rounded-lg border border-destructive/50 bg-destructive/10 p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-destructive" />
              <h2 className="text-lg font-semibold text-destructive">
                Something went wrong
              </h2>
            </div>

            <p className="text-sm text-muted-foreground mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>

            <button
              onClick={() => window.location.reload()}
              className="rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 5. Async Error Handling

**Context**: Handling errors in async/await code

**Example from**: `gao_dev/web/adapters/brian_adapter.py`

```python
async def process_message(self, message: str) -> dict:
    """Process message with comprehensive error handling."""
    try:
        # Validate input
        if not message.strip():
            return {
                "error": "Message cannot be empty",
                "code": "EMPTY_MESSAGE"
            }

        # Process with timeout
        try:
            result = await asyncio.wait_for(
                self._process_internal(message),
                timeout=300.0
            )
            return result

        except asyncio.TimeoutError:
            logger.error("message_processing_timeout", message_length=len(message))
            return {
                "error": "Processing timed out after 5 minutes",
                "code": "TIMEOUT"
            }

    except ValueError as e:
        logger.warning("validation_error", error=str(e))
        return {"error": str(e), "code": "VALIDATION_ERROR"}

    except Exception as e:
        logger.error("unexpected_error", error=str(e), exc_info=True)
        return {
            "error": "An unexpected error occurred",
            "code": "INTERNAL_ERROR",
            "details": str(e) if self.debug_mode else None
        }
```

---

## Key Patterns

1. **Validate early**: Check inputs before processing
2. **Rollback on failure**: Undo partial changes
3. **Retry with backoff**: Handle transient failures
4. **Log comprehensively**: Use structlog for context
5. **Catch at boundaries**: Error boundaries in UI
6. **Provide context**: Include helpful error messages

**See Also**:
- [Quick Start](../QUICK_START.md) - Basic error handling
- [Testing Guide](../developers/TESTING_GUIDE.md) - Testing error cases
