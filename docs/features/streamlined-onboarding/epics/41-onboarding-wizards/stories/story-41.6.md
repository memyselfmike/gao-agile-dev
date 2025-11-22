# Story 41.6: API Key Validation

## User Story

As a developer entering my API key during onboarding,
I want real-time validation that tells me if my key works,
So that I don't complete setup with invalid credentials.

## Acceptance Criteria

- [ ] AC1: Validates API key by making test request to provider
- [ ] AC2: Validation completes within 3 seconds or times out
- [ ] AC3: Shows clear success message: "API key validated successfully"
- [ ] AC4: Shows clear error message with specific failure reason
- [ ] AC5: Provides actionable fix suggestions for common errors (invalid key, rate limit, network)
- [ ] AC6: Supports skip option with warning about limitations
- [ ] AC7: Supports retry option after failure
- [ ] AC8: Works offline for Ollama (local) provider - checks if server is running
- [ ] AC9: Defers validation for cloud providers when offline (with clear warning)
- [ ] AC10: Never sends actual key in error messages or logs
- [ ] AC11: Rate limits validation attempts (max 3 per minute per provider)
- [ ] AC12: Caches successful validation for session duration

## Technical Notes

### Implementation Details

Create `gao_dev/core/api_key_validator.py`:

```python
from enum import Enum
from typing import Optional
import httpx
import asyncio

class ValidationResult(Enum):
    VALID = "valid"
    INVALID = "invalid"
    NETWORK_ERROR = "network_error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    OFFLINE = "offline"

class APIKeyValidator:
    """Validate API keys with various providers."""

    TIMEOUT_SECONDS = 3
    MAX_ATTEMPTS_PER_MINUTE = 3

    async def validate(
        self,
        provider: str,
        api_key: str
    ) -> Tuple[ValidationResult, str]:
        """Validate API key and return result with message."""
        pass

    async def _validate_anthropic(self, api_key: str) -> Tuple[ValidationResult, str]:
        """Validate Anthropic API key."""
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    }
                )

                if response.status_code == 200:
                    return ValidationResult.VALID, "API key validated successfully"
                elif response.status_code == 401:
                    return ValidationResult.INVALID, "Invalid API key"
                elif response.status_code == 429:
                    return ValidationResult.RATE_LIMITED, "Rate limited by provider"
                else:
                    return ValidationResult.INVALID, f"Unexpected error: {response.status_code}"

        except httpx.TimeoutException:
            return ValidationResult.TIMEOUT, "Validation timed out"
        except httpx.NetworkError:
            return ValidationResult.NETWORK_ERROR, "Network error during validation"

    async def _validate_ollama(self, api_key: str) -> Tuple[ValidationResult, str]:
        """Validate Ollama is running locally."""
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    return ValidationResult.VALID, "Ollama server is running"
                else:
                    return ValidationResult.INVALID, "Ollama server not responding correctly"
        except httpx.ConnectError:
            return ValidationResult.INVALID, "Ollama server not running at localhost:11434"

    def get_fix_suggestion(self, result: ValidationResult, provider: str) -> str:
        """Get actionable fix suggestion for validation failure."""
        pass
```

### Provider Validation Endpoints

| Provider | Validation Method |
|----------|-------------------|
| Anthropic | `GET /v1/models` with API key header |
| OpenAI | `GET /v1/models` with Bearer token |
| OpenCode | Provider-specific endpoint |
| Ollama | `GET http://localhost:11434/api/tags` |

### Error Messages and Fixes

| Result | Message | Fix Suggestion |
|--------|---------|----------------|
| INVALID | "Invalid API key" | "Get a valid key from the provider dashboard. Check for extra spaces or missing characters." |
| RATE_LIMITED | "Rate limited by provider" | "Wait a few minutes and try again, or use a different API key." |
| NETWORK_ERROR | "Network error during validation" | "Check your internet connection and try again." |
| TIMEOUT | "Validation timed out" | "The provider may be experiencing issues. Try again or skip validation." |

### Skip Option Behavior

When user skips validation:
1. Show warning: "Skipping validation. You may encounter errors if the key is invalid."
2. Allow onboarding to continue
3. Store credential as "unvalidated"
4. Show warning on first use attempt

## Test Scenarios

1. **Valid Anthropic key**: Given valid Anthropic API key, When validation runs, Then returns VALID with success message

2. **Invalid key**: Given malformed API key, When validation runs, Then returns INVALID with error message

3. **Network error**: Given no internet connection, When cloud validation runs, Then returns NETWORK_ERROR

4. **Timeout**: Given slow API response, When validation runs over 3 seconds, Then returns TIMEOUT

5. **Rate limited**: Given provider returns 429, When validation runs, Then returns RATE_LIMITED with wait suggestion

6. **Ollama running**: Given Ollama running locally, When validation runs, Then returns VALID

7. **Ollama not running**: Given Ollama not running, When validation runs, Then returns INVALID with start suggestion

8. **Skip validation**: Given user chooses skip, When validation fails, Then onboarding continues with warning

9. **Retry after failure**: Given validation fails, When user chooses retry, Then validation runs again

10. **Rate limit protection**: Given 4 attempts in 1 minute, When 4th attempt made, Then returns rate limit error

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests with mock API responses
- [ ] Tested with real API keys (manual)
- [ ] Code reviewed
- [ ] Error messages reviewed for actionability
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Story 41.4: CredentialManager (for credential retrieval)
- `httpx` library for async HTTP requests

## Notes

- Use `httpx` instead of `requests` for async support
- Consider caching validation result in session
- Log validation attempts (without keys) for debugging
- Document validation endpoints in architecture
- Consider adding health check for providers in main interface
- Offline mode should be clearly indicated throughout the flow
