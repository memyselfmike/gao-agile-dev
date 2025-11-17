# Story 39.29: Provider Validation and Persistence

**Story Number**: 39.29
**Epic**: 39.7 - Git Integration & Provider UI
**Feature**: Web Interface
**Status**: Planned
**Priority**: SHOULD HAVE (P1 - V1.1)
**Effort Estimate**: M (Medium - 4 story points)
**Dependencies**: Story 39.28 (Provider Selection Settings Panel), Epic 35 (Provider Selection)

---

## User Story

As a **product owner**
I want **provider changes validated and persisted to YAML configuration**
So that **my settings are saved correctly and invalid configurations are prevented**

---

## Acceptance Criteria

### Validation
- [ ] AC1: Provider + model combination validated before save:
  - Claude Code + Claude models: Valid
  - OpenCode + OpenRouter models: Valid
  - Ollama + local models: Valid
  - Mismatched combinations: Invalid (error shown)
- [ ] AC2: API key validation displays status indicator:
  - Valid: Green checkmark with "API key configured"
  - Invalid: Red X with "Invalid API key"
  - Not configured: Yellow warning with "API key missing"
- [ ] AC3: Real-time validation during typing (debounced 500ms)
- [ ] AC4: Save button disabled if validation fails
- [ ] AC5: Validation errors show specific fix suggestions:
  - "Invalid API key. Check environment variable ANTHROPIC_API_KEY."
  - "Ollama not running. Start Ollama with `ollama serve`."
  - "Model not available. Select a different model."

### Persistence
- [ ] AC6: Save writes to `.gao-dev/provider_preferences.yaml` atomically:
  - Backup existing file to `.gao-dev/provider_preferences.yaml.bak`
  - Write new configuration
  - Delete backup on success
- [ ] AC7: YAML structure matches Epic 35 format:
  ```yaml
  provider: claude_code
  model: claude-sonnet-4-5-20250929
  last_updated: 2025-01-17T14:30:00Z
  ```
- [ ] AC8: File permissions set to 0600 (read/write owner only) for security
- [ ] AC9: Rollback on save failure (restore from backup)
- [ ] AC10: Settings panel shows loading state during save (<1s)

### User Feedback
- [ ] AC11: Success toast notification: "Provider changed to [Provider] - [Model]"
- [ ] AC12: Error toast notification with actionable message
- [ ] AC13: Toast auto-dismisses after 5 seconds (success) or persists until dismissed (error)
- [ ] AC14: Settings panel closes automatically on successful save

### Real-Time Updates
- [ ] AC15: File watcher emits `provider.changed` WebSocket event after save
- [ ] AC16: All connected clients receive update notification
- [ ] AC17: Settings panel reflects new provider immediately (optimistic update)

---

## Technical Context

### Architecture Integration

**Integration with Epic 35 (Provider Selection)**:
- Reuse `ProviderValidator` class for validation logic
- Reuse YAML structure from `.gao-dev/provider_preferences.yaml`
- Reuse API key detection and validation
- DO NOT duplicate validation logic

**API Endpoints** (Backend - Story 39.29):
```
POST /api/settings/provider
Request: {
  provider: "claude_code",
  model: "claude-sonnet-4-5-20250929"
}
Response (Success): {
  success: true,
  provider: "claude_code",
  model: "claude-sonnet-4-5-20250929",
  message: "Provider changed to Claude Code - claude-sonnet-4-5-20250929"
}
Response (Error): {
  success: false,
  error: "Invalid API key",
  fix_suggestion: "Check environment variable ANTHROPIC_API_KEY",
  validation_details: {
    api_key_status: "invalid",
    model_available: true
  }
}

GET /api/settings/provider/validate?provider=<provider>&model=<model>
Response: {
  valid: true,
  api_key_status: "valid",  // "valid", "invalid", "missing"
  model_available: true,
  warnings: []
}
```

**Frontend Components** (Story 39.29):
```
src/components/settings/
├── ValidationIndicator.tsx  # API key status indicator
├── SaveButton.tsx           # Save with loading state
├── ToastNotification.tsx    # Success/error toasts
└── ProviderValidator.ts     # Client-side validation logic
```

### Dependencies

**Story 39.28 (Provider Selection Settings Panel)**:
- Settings panel UI
- Provider/model selection dropdowns

**Epic 35 (Provider Selection)**:
- `ProviderValidator` class for validation
- YAML file structure
- API key detection logic
- Ollama availability checking

---

## Test Scenarios

### Test 1: Valid Provider Change - Success
**Given**: User selects valid provider (Claude Code) and model (claude-sonnet-4-5-20250929)
**When**: User clicks "Save Changes"
**Then**:
- Validation passes (green checkmark)
- API key status: "Valid" (green)
- Save button shows loading spinner
- YAML file written to `.gao-dev/provider_preferences.yaml`
- Success toast: "Provider changed to Claude Code - claude-sonnet-4-5-20250929"
- Settings panel closes
- WebSocket emits `provider.changed` event

### Test 2: Invalid API Key - Error
**Given**: User selects Claude Code but ANTHROPIC_API_KEY not set
**When**: User clicks "Save Changes"
**Then**:
- Validation fails
- API key status: "Not configured" (yellow warning)
- Error toast: "API key missing. Set environment variable ANTHROPIC_API_KEY."
- Settings panel stays open
- Save button re-enabled (user can fix and retry)
- No YAML file written

### Test 3: Ollama Not Running - Error
**Given**: User selects Ollama provider but Ollama not running
**When**: User clicks "Save Changes"
**Then**:
- Validation fails
- Error toast: "Ollama not running. Start Ollama with `ollama serve`."
- Fix suggestion: "Run `ollama serve` in terminal and try again."
- Settings panel stays open
- No YAML file written

### Test 4: Real-Time Validation
**Given**: Settings panel open
**When**: User selects different provider/model combinations
**Then**:
- Validation runs after 500ms debounce
- API key status updates in real-time
- Save button enabled/disabled based on validation
- No API calls until debounce completes

### Test 5: Atomic Save with Rollback
**Given**: Valid provider selected, existing `.gao-dev/provider_preferences.yaml`
**When**: Save fails mid-write (e.g., disk full)
**Then**:
- Backup file created: `.gao-dev/provider_preferences.yaml.bak`
- Write fails
- Original file restored from backup
- Error toast: "Failed to save settings. [Error details]"
- Settings panel stays open

### Test 6: Concurrent Save Prevention
**Given**: User clicks "Save Changes"
**When**: User clicks "Save Changes" again before first save completes
**Then**:
- Second click ignored (button disabled)
- Loading spinner persists
- Only one save operation executes
- Toast shown once on completion

### Test 7: WebSocket Real-Time Update
**Given**: Two browser tabs open with GAO-Dev web UI
**When**: User saves provider change in Tab 1
**Then**:
- Tab 1: Success toast, panel closes
- Tab 2: Receives `provider.changed` WebSocket event
- Tab 2: Settings panel (if open) updates to show new provider
- Both tabs reflect new provider immediately

### Test 8: Mismatched Provider-Model Combination
**Given**: User manually modifies YAML file to invalid state (e.g., provider=claude_code, model=ollama:llama2)
**When**: User opens settings panel
**Then**:
- Validation detects mismatch
- Warning shown: "Invalid provider-model combination detected"
- Dropdowns show current values with error indicator
- User can correct by selecting valid model

### Test 9: File Permissions Security
**Given**: User saves provider settings
**When**: YAML file written to `.gao-dev/provider_preferences.yaml`
**Then**:
- File permissions set to 0600 (read/write owner only)
- Other users cannot read file (security)
- Git ignores file (not committed)

### Test 10: Validation Error with Fix Suggestion
**Given**: User selects OpenCode but OPENROUTER_API_KEY invalid
**When**: Validation runs
**Then**:
- API key status: "Invalid" (red X)
- Error message: "Invalid API key"
- Fix suggestion: "Check environment variable OPENROUTER_API_KEY"
- Link to documentation (if applicable)

---

## Definition of Done

### Code Quality
- [ ] Code follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] Type hints throughout (no `any` in TypeScript)
- [ ] structlog for all logging (backend)
- [ ] Error handling comprehensive (try-catch blocks)
- [ ] ESLint + Prettier applied (frontend)
- [ ] Black formatting applied (backend, line length 100)

### Testing
- [ ] Unit tests: 100% coverage for validation logic, file operations, rollback
- [ ] Integration tests: API endpoint `/api/settings/provider` POST tested with valid/invalid inputs
- [ ] E2E tests: Playwright test for saving valid provider, handling errors, real-time updates
- [ ] Security tests: File permissions, YAML injection prevention, input sanitization

### Documentation
- [ ] API documentation: `/api/settings/provider` POST endpoint documented
- [ ] Component documentation: Validation logic and error handling
- [ ] User guide: How to fix common validation errors
- [ ] Security documentation: File permissions and sensitive data handling

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] Security review: YAML injection prevention, input sanitization validated
- [ ] No regressions (100% existing tests pass)

---

## Implementation Notes

### Backend Implementation (FastAPI)

```python
# gao_dev/web/api/settings.py (enhanced from Story 39.28)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import structlog
import yaml
import shutil
import os

from gao_dev.core.provider_selector import ProviderValidator
from gao_dev.web.websocket import broadcast_event

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])

class ProviderChangeRequest(BaseModel):
    provider: str
    model: str

@router.post("/provider")
async def update_provider(request: ProviderChangeRequest):
    """Save provider settings with validation and atomic persistence"""
    try:
        # Validate provider + model combination
        validator = ProviderValidator()
        validation_result = validator.validate(
            provider=request.provider,
            model=request.model
        )

        if not validation_result.valid:
            return {
                "success": False,
                "error": validation_result.error,
                "fix_suggestion": validation_result.fix_suggestion,
                "validation_details": {
                    "api_key_status": validation_result.api_key_status,
                    "model_available": validation_result.model_available,
                },
            }

        # Atomic save with rollback
        prefs_file = Path(".gao-dev/provider_preferences.yaml")
        backup_file = Path(".gao-dev/provider_preferences.yaml.bak")

        # Backup existing file
        if prefs_file.exists():
            shutil.copy(prefs_file, backup_file)

        try:
            # Write new preferences
            new_prefs = {
                "provider": request.provider,
                "model": request.model,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }

            with open(prefs_file, "w") as f:
                yaml.dump(new_prefs, f, default_flow_style=False)

            # Set secure file permissions (0600)
            os.chmod(prefs_file, 0o600)

            # Delete backup on success
            if backup_file.exists():
                backup_file.unlink()

            # Broadcast WebSocket event
            await broadcast_event("provider.changed", {
                "provider": request.provider,
                "model": request.model,
            })

            logger.info(
                "provider_settings_updated",
                provider=request.provider,
                model=request.model,
            )

            return {
                "success": True,
                "provider": request.provider,
                "model": request.model,
                "message": f"Provider changed to {_format_provider_name(request.provider)} - {request.model}",
            }

        except Exception as e:
            # Rollback on failure
            if backup_file.exists():
                shutil.copy(backup_file, prefs_file)
                backup_file.unlink()
            raise e

    except Exception as e:
        logger.error("failed_to_update_provider", error=str(e))
        return {
            "success": False,
            "error": "Failed to save settings",
            "fix_suggestion": f"Error: {str(e)}. Please try again.",
        }

@router.get("/provider/validate")
async def validate_provider(provider: str, model: str):
    """Validate provider and model combination (real-time validation)"""
    try:
        validator = ProviderValidator()
        result = validator.validate(provider=provider, model=model)

        return {
            "valid": result.valid,
            "api_key_status": result.api_key_status,
            "model_available": result.model_available,
            "warnings": result.warnings,
        }
    except Exception as e:
        logger.error("failed_to_validate_provider", error=str(e))
        raise HTTPException(status_code=500, detail="Validation failed")

def _format_provider_name(provider_id: str) -> str:
    """Format provider ID to display name"""
    names = {
        "claude_code": "Claude Code",
        "opencode": "OpenCode",
        "ollama": "Ollama",
    }
    return names.get(provider_id, provider_id)
```

```python
# gao_dev/core/provider_selector.py (reuse from Epic 35)
from dataclasses import dataclass
from typing import Optional
import os
import requests
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None
    fix_suggestion: Optional[str] = None
    api_key_status: str = "unknown"  # "valid", "invalid", "missing"
    model_available: bool = True
    warnings: list[str] = None

class ProviderValidator:
    """Validate provider and model configurations"""

    def validate(self, provider: str, model: str) -> ValidationResult:
        """Validate provider + model combination"""
        if provider == "claude_code":
            return self._validate_claude_code(model)
        elif provider == "opencode":
            return self._validate_opencode(model)
        elif provider == "ollama":
            return self._validate_ollama(model)
        else:
            return ValidationResult(
                valid=False,
                error=f"Unknown provider: {provider}",
                fix_suggestion="Select Claude Code, OpenCode, or Ollama.",
            )

    def _validate_claude_code(self, model: str) -> ValidationResult:
        """Validate Claude Code configuration"""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            return ValidationResult(
                valid=False,
                error="API key missing",
                fix_suggestion="Set environment variable ANTHROPIC_API_KEY",
                api_key_status="missing",
            )

        # Basic API key format validation
        if not api_key.startswith("sk-ant-"):
            return ValidationResult(
                valid=False,
                error="Invalid API key format",
                fix_suggestion="Anthropic API keys start with 'sk-ant-'",
                api_key_status="invalid",
            )

        # Validate model
        valid_models = [
            "claude-sonnet-4-5-20250929",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]
        if model not in valid_models:
            return ValidationResult(
                valid=False,
                error="Invalid model",
                fix_suggestion=f"Valid models: {', '.join(valid_models)}",
                api_key_status="valid",
                model_available=False,
            )

        return ValidationResult(valid=True, api_key_status="valid")

    def _validate_opencode(self, model: str) -> ValidationResult:
        """Validate OpenCode configuration"""
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            return ValidationResult(
                valid=False,
                error="API key missing",
                fix_suggestion="Set environment variable OPENROUTER_API_KEY",
                api_key_status="missing",
            )

        # Validate API key by fetching available models
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )
            if response.status_code == 401:
                return ValidationResult(
                    valid=False,
                    error="Invalid API key",
                    fix_suggestion="Check environment variable OPENROUTER_API_KEY",
                    api_key_status="invalid",
                )
            response.raise_for_status()
            return ValidationResult(valid=True, api_key_status="valid")
        except Exception as e:
            logger.warning("opencode_validation_failed", error=str(e))
            return ValidationResult(
                valid=False,
                error="OpenRouter API unavailable",
                fix_suggestion="Check network connection and API key",
                api_key_status="unknown",
            )

    def _validate_ollama(self, model: str) -> ValidationResult:
        """Validate Ollama configuration"""
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            response.raise_for_status()

            available_models = [m["name"] for m in response.json().get("models", [])]
            if model not in available_models:
                return ValidationResult(
                    valid=False,
                    error="Model not available",
                    fix_suggestion=f"Pull model with: ollama pull {model}",
                    api_key_status="valid",
                    model_available=False,
                )

            return ValidationResult(valid=True, api_key_status="valid")
        except requests.exceptions.ConnectionError:
            return ValidationResult(
                valid=False,
                error="Ollama not running",
                fix_suggestion="Start Ollama with: ollama serve",
                api_key_status="missing",
            )
        except Exception as e:
            logger.warning("ollama_validation_failed", error=str(e))
            return ValidationResult(
                valid=False,
                error="Ollama validation failed",
                fix_suggestion=str(e),
                api_key_status="unknown",
            )
```

### Frontend Implementation (React + TypeScript)

```typescript
// src/components/settings/SettingsPanel.tsx (enhanced from Story 39.28)
import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ValidationIndicator } from './ValidationIndicator';
import { useDebouncedValue } from '../../hooks/useDebouncedValue';

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ open, onOpenChange }) => {
  // ... existing code from Story 39.28 ...

  const [validationStatus, setValidationStatus] = useState<ValidationStatus | null>(null);

  const queryClient = useQueryClient();

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async ({ provider, model }: { provider: string; model: string }) => {
      const response = await fetch('/api/settings/provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, model }),
      });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message);
        queryClient.invalidateQueries(['provider-settings']);
        onOpenChange(false);
      } else {
        toast.error(data.error, {
          description: data.fix_suggestion,
          duration: Infinity, // Error persists until dismissed
        });
      }
    },
    onError: (error) => {
      toast.error('Failed to save settings', {
        description: error.message,
      });
    },
  });

  // Real-time validation (debounced)
  const debouncedProvider = useDebouncedValue(selectedProvider, 500);
  const debouncedModel = useDebouncedValue(selectedModel, 500);

  useEffect(() => {
    if (debouncedProvider && debouncedModel) {
      fetch(`/api/settings/provider/validate?provider=${debouncedProvider}&model=${debouncedModel}`)
        .then(res => res.json())
        .then(data => setValidationStatus(data))
        .catch(() => setValidationStatus(null));
    }
  }, [debouncedProvider, debouncedModel]);

  const handleSave = () => {
    saveMutation.mutate({ provider: selectedProvider, model: selectedModel });
  };

  const isSaveDisabled = !hasChanges || !validationStatus?.valid || saveMutation.isLoading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        {/* ... existing UI ... */}

        <ValidationIndicator status={validationStatus} />

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={saveMutation.isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaveDisabled} loading={saveMutation.isLoading}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

```typescript
// src/components/settings/ValidationIndicator.tsx
import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import type { ValidationStatus } from '../../types/settings';

interface ValidationIndicatorProps {
  status: ValidationStatus | null;
}

export const ValidationIndicator: React.FC<ValidationIndicatorProps> = ({ status }) => {
  if (!status) return null;

  const statusConfig = {
    valid: {
      icon: CheckCircle2,
      color: 'text-green-500',
      message: 'API key configured',
    },
    invalid: {
      icon: XCircle,
      color: 'text-red-500',
      message: 'Invalid API key',
    },
    missing: {
      icon: AlertTriangle,
      color: 'text-yellow-500',
      message: 'API key missing',
    },
  };

  const config = statusConfig[status.api_key_status] ?? statusConfig.missing;
  const Icon = config.icon;

  return (
    <div className={`validation-indicator ${config.color}`}>
      <Icon size={20} />
      <span>{config.message}</span>
    </div>
  );
};
```

---

## Related Stories

**Dependencies**:
- **Story 39.28**: Provider Selection Settings Panel (UI)
- **Epic 35**: Provider Selection (validation logic, YAML structure)

**Completes**:
- **Epic 39.7**: Git Integration & Provider UI (final story)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
