# Story 39.28: Provider Selection Settings Panel

**Story Number**: 39.28
**Epic**: 39.7 - Git Integration & Provider UI
**Feature**: Web Interface
**Status**: Planned
**Priority**: SHOULD HAVE (P1 - V1.1)
**Effort Estimate**: S (Small - 2 story points)
**Dependencies**: Epic 39.1-39.4 (Backend & Frontend Foundation), Epic 35 (Provider Selection)

---

## User Story

As a **product owner**
I want **to select AI provider from the web UI settings panel**
So that **I don't have to manually edit YAML files or use CLI prompts**

---

## Acceptance Criteria

### Settings Panel Access
- [ ] AC1: Settings icon (gear/cog) visible in top navigation bar (right side)
- [ ] AC2: Clicking settings icon opens settings panel as modal/drawer
- [ ] AC3: Settings panel can be closed via:
  - Close button (X icon)
  - Escape key
  - Click outside panel (if modal)
- [ ] AC4: Settings panel accessible via keyboard (Tab navigation, Enter to open)

### Provider Selection UI
- [ ] AC5: Provider dropdown displays three options:
  - "Claude Code" (Anthropic Claude API)
  - "OpenCode" (OpenRouter API)
  - "Ollama" (Local models)
- [ ] AC6: Model dropdown filtered by selected provider:
  - Claude Code: claude-sonnet-4-5-20250929, claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022
  - OpenCode: openrouter models (fetched from API)
  - Ollama: deepseek-r1, llama2, codellama (fetched from local Ollama)
- [ ] AC7: Current provider and model shown at top of panel:
  - "Current: Claude Code - claude-sonnet-4-5-20250929"
  - Badge indicating active provider (green checkmark)

### Interaction & Accessibility
- [ ] AC8: Save button enabled only when provider/model changes from current
- [ ] AC9: Cancel button closes panel without saving changes
- [ ] AC10: Settings panel supports dark/light mode (inherits from app theme)
- [ ] AC11: Keyboard shortcuts:
  - Tab: Navigate between fields
  - Enter: Save changes (if on Save button)
  - Escape: Cancel and close panel

### Visual Design
- [ ] AC12: Settings panel follows Shadcn UI design system
- [ ] AC13: Provider dropdown shows provider logos/icons
- [ ] AC14: Model dropdown shows model descriptions (tooltips)
- [ ] AC15: Panel width: 400px (desktop), full-width (mobile)

---

## Technical Context

### Architecture Integration

**Integration with Epic 35 (Provider Selection)**:
- Reuse provider validation logic from CLI
- Read current provider from `.gao-dev/provider_preferences.yaml`
- Reuse Ollama model detection
- DO NOT duplicate validation (Story 39.29 handles validation)

**API Endpoints** (Backend - Story 39.28):
```
GET /api/settings/provider
Response: {
  current_provider: "claude_code",
  current_model: "claude-sonnet-4-5-20250929",
  available_providers: [
    {
      id: "claude_code",
      name: "Claude Code",
      models: [
        { id: "claude-sonnet-4-5-20250929", name: "Claude Sonnet 4.5" },
        { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet" }
      ]
    },
    {
      id: "opencode",
      name: "OpenCode",
      models: [...] // Fetched from OpenRouter
    },
    {
      id: "ollama",
      name: "Ollama (Local)",
      models: [...] // Fetched from local Ollama
    }
  ]
}

POST /api/settings/provider (handled in Story 39.29)
```

**Frontend Components** (Story 39.28):
```
src/components/settings/
├── SettingsPanel.tsx        # Main settings modal/drawer
├── ProviderSelect.tsx       # Provider dropdown
├── ModelSelect.tsx          # Model dropdown
├── CurrentProviderBadge.tsx # Active provider indicator
└── SettingsIcon.tsx         # Settings icon button
```

### Dependencies

**Epic 35 (Provider Selection)**:
- Reuse `ProviderSelector` logic for provider/model lists
- Reuse YAML structure from `.gao-dev/provider_preferences.yaml`
- Reuse Ollama detection and model fetching

**Epic 39.1-39.4**:
- Backend: FastAPI endpoints for settings
- Frontend: React components, modal/drawer UI

**Story 39.29 (Provider Validation and Persistence)**:
- Validation logic (API key checks, model availability)
- Persistence to YAML file

---

## Test Scenarios

### Test 1: Open Settings Panel
**Given**: User is on web interface
**When**: User clicks settings icon in top bar
**Then**:
- Settings panel opens as modal/drawer
- Current provider shown: "Claude Code - claude-sonnet-4-5-20250929"
- Provider dropdown shows 3 providers
- Model dropdown shows Claude models
- Save button disabled (no changes)

### Test 2: Change Provider
**Given**: Settings panel open, current provider is Claude Code
**When**: User selects "Ollama" from provider dropdown
**Then**:
- Model dropdown updates to show Ollama models (deepseek-r1, llama2, codellama)
- First Ollama model auto-selected (deepseek-r1)
- Save button becomes enabled
- Current provider badge unchanged (not saved yet)

### Test 3: Change Model
**Given**: Settings panel open, provider is Claude Code
**When**: User selects "claude-3-5-haiku-20241022" from model dropdown
**Then**:
- Model selection updates
- Save button becomes enabled
- Current provider badge unchanged (not saved yet)

### Test 4: Cancel Changes
**Given**: Settings panel open, user changed provider to Ollama
**When**: User clicks "Cancel" button
**Then**:
- Settings panel closes
- No changes saved
- Current provider still Claude Code
- Next time panel opens, shows Claude Code (not Ollama)

### Test 5: Keyboard Navigation
**Given**: Settings panel open
**When**: User presses Tab key
**Then**:
- Focus moves through: Provider dropdown → Model dropdown → Save button → Cancel button
- Focus visible (outline/ring)
- Enter key on Save button triggers save (Story 39.29)
- Escape key closes panel

### Test 6: Dark Mode Support
**Given**: App in dark mode
**When**: User opens settings panel
**Then**:
- Panel background dark (#1a1a1a)
- Text light (#e0e0e0)
- Dropdowns follow dark theme
- Icons inverted for visibility

### Test 7: Ollama Models Unavailable
**Given**: Ollama not running on localhost
**When**: User selects "Ollama" provider
**Then**:
- Model dropdown shows "Loading models..."
- After timeout (5s): "Ollama not available. Is it running?"
- Save button disabled (no valid model)
- Error handled gracefully (Story 39.29)

### Test 8: OpenRouter Models Fetch
**Given**: User has valid OpenRouter API key
**When**: User selects "OpenCode" provider
**Then**:
- Model dropdown shows "Loading models..."
- Models fetched from OpenRouter API
- Dropdown populated with available models
- Default model selected

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
- [ ] Unit tests: 100% coverage for SettingsPanel, ProviderSelect, ModelSelect components
- [ ] Integration tests: API endpoint `/api/settings/provider` tested
- [ ] E2E tests: Playwright test for opening panel, changing provider, canceling
- [ ] Accessibility tests: Keyboard navigation, screen reader compatibility

### Documentation
- [ ] API documentation: `/api/settings/provider` endpoint documented
- [ ] Component documentation: SettingsPanel props and usage
- [ ] User guide: How to change AI provider from web UI

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] No security vulnerabilities (no sensitive data in UI)
- [ ] No regressions (100% existing tests pass)

---

## Implementation Notes

### Backend Implementation (FastAPI)

```python
# gao_dev/web/api/settings.py
from fastapi import APIRouter, HTTPException
from pathlib import Path
import structlog
import yaml

from gao_dev.core.provider_selector import ProviderSelector

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/provider")
async def get_provider_settings():
    """Get current provider settings and available options"""
    try:
        # Read current provider from preferences
        prefs_file = Path(".gao-dev/provider_preferences.yaml")
        current_provider = "claude_code"
        current_model = "claude-sonnet-4-5-20250929"

        if prefs_file.exists():
            with open(prefs_file, "r") as f:
                prefs = yaml.safe_load(f)
                current_provider = prefs.get("provider", "claude_code")
                current_model = prefs.get("model", "claude-sonnet-4-5-20250929")

        # Get available providers and models
        provider_selector = ProviderSelector()
        available_providers = [
            {
                "id": "claude_code",
                "name": "Claude Code",
                "description": "Anthropic Claude API (requires ANTHROPIC_API_KEY)",
                "models": [
                    {
                        "id": "claude-sonnet-4-5-20250929",
                        "name": "Claude Sonnet 4.5",
                        "description": "Latest and most capable model"
                    },
                    {
                        "id": "claude-3-5-sonnet-20241022",
                        "name": "Claude 3.5 Sonnet",
                        "description": "Previous generation Sonnet"
                    },
                    {
                        "id": "claude-3-5-haiku-20241022",
                        "name": "Claude 3.5 Haiku",
                        "description": "Faster, more cost-effective"
                    }
                ]
            },
            {
                "id": "opencode",
                "name": "OpenCode",
                "description": "OpenRouter API (requires OPENROUTER_API_KEY)",
                "models": await _fetch_openrouter_models()
            },
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "description": "Run models locally with Ollama",
                "models": await _fetch_ollama_models()
            }
        ]

        return {
            "current_provider": current_provider,
            "current_model": current_model,
            "available_providers": available_providers,
        }
    except Exception as e:
        logger.error("failed_to_get_provider_settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load provider settings")

async def _fetch_openrouter_models() -> list[dict]:
    """Fetch available models from OpenRouter API"""
    try:
        # Implementation: Call OpenRouter API /api/v1/models
        # For now, return hardcoded list
        return [
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (OpenRouter)"},
            {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
        ]
    except Exception as e:
        logger.warning("failed_to_fetch_openrouter_models", error=str(e))
        return []

async def _fetch_ollama_models() -> list[dict]:
    """Fetch available models from local Ollama"""
    try:
        from gao_dev.core.provider_selector import ProviderSelector
        selector = ProviderSelector()
        models = selector._detect_ollama_models()
        return [{"id": model, "name": model.title()} for model in models]
    except Exception as e:
        logger.warning("failed_to_fetch_ollama_models", error=str(e))
        return []
```

### Frontend Implementation (React + TypeScript)

```typescript
// src/components/settings/SettingsPanel.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { ProviderSelect } from './ProviderSelect';
import { ModelSelect } from './ModelSelect';
import { CurrentProviderBadge } from './CurrentProviderBadge';
import type { ProviderSettings } from '../../types/settings';

interface SettingsPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ open, onOpenChange }) => {
  const { data, isLoading } = useQuery<ProviderSettings>({
    queryKey: ['provider-settings'],
    queryFn: () => fetch('/api/settings/provider').then(res => res.json()),
    enabled: open,
  });

  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');

  // Initialize selections when data loads
  React.useEffect(() => {
    if (data) {
      setSelectedProvider(data.current_provider);
      setSelectedModel(data.current_model);
    }
  }, [data]);

  const hasChanges =
    selectedProvider !== data?.current_provider ||
    selectedModel !== data?.current_model;

  const handleSave = async () => {
    // Story 39.29 handles save logic
    console.log('Saving provider settings:', { selectedProvider, selectedModel });
  };

  const handleCancel = () => {
    setSelectedProvider(data?.current_provider ?? '');
    setSelectedModel(data?.current_model ?? '');
    onOpenChange(false);
  };

  if (isLoading) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="settings-panel">
        <DialogHeader>
          <DialogTitle>AI Provider Settings</DialogTitle>
        </DialogHeader>

        <div className="settings-content">
          <CurrentProviderBadge
            provider={data?.current_provider ?? ''}
            model={data?.current_model ?? ''}
          />

          <ProviderSelect
            providers={data?.available_providers ?? []}
            value={selectedProvider}
            onChange={(provider) => {
              setSelectedProvider(provider);
              // Auto-select first model
              const firstModel = data?.available_providers.find(p => p.id === provider)?.models[0];
              if (firstModel) setSelectedModel(firstModel.id);
            }}
          />

          <ModelSelect
            models={
              data?.available_providers.find(p => p.id === selectedProvider)?.models ?? []
            }
            value={selectedModel}
            onChange={setSelectedModel}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

```typescript
// src/components/settings/ProviderSelect.tsx
import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import type { Provider } from '../../types/settings';

interface ProviderSelectProps {
  providers: Provider[];
  value: string;
  onChange: (value: string) => void;
}

export const ProviderSelect: React.FC<ProviderSelectProps> = ({
  providers,
  value,
  onChange,
}) => {
  return (
    <div className="provider-select">
      <label htmlFor="provider">AI Provider</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="provider">
          <SelectValue placeholder="Select provider" />
        </SelectTrigger>
        <SelectContent>
          {providers.map(provider => (
            <SelectItem key={provider.id} value={provider.id}>
              <div className="provider-option">
                <span className="provider-name">{provider.name}</span>
                <span className="provider-description">{provider.description}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
```

```typescript
// src/components/settings/ModelSelect.tsx
import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import type { Model } from '../../types/settings';

interface ModelSelectProps {
  models: Model[];
  value: string;
  onChange: (value: string) => void;
}

export const ModelSelect: React.FC<ModelSelectProps> = ({ models, value, onChange }) => {
  return (
    <div className="model-select">
      <label htmlFor="model">Model</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="model">
          <SelectValue placeholder="Select model" />
        </SelectTrigger>
        <SelectContent>
          {models.map(model => (
            <SelectItem key={model.id} value={model.id}>
              <div className="model-option">
                <span className="model-name">{model.name}</span>
                {model.description && (
                  <span className="model-description">{model.description}</span>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
```

```typescript
// src/components/settings/CurrentProviderBadge.tsx
import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Badge } from '../ui/badge';

interface CurrentProviderBadgeProps {
  provider: string;
  model: string;
}

export const CurrentProviderBadge: React.FC<CurrentProviderBadgeProps> = ({
  provider,
  model,
}) => {
  const providerNames: Record<string, string> = {
    claude_code: 'Claude Code',
    opencode: 'OpenCode',
    ollama: 'Ollama',
  };

  return (
    <div className="current-provider-badge">
      <CheckCircle2 className="text-green-500" size={20} />
      <div>
        <div className="text-sm text-muted-foreground">Current Provider</div>
        <div className="font-medium">
          {providerNames[provider]} - {model}
        </div>
      </div>
    </div>
  );
};
```

---

## Related Stories

**Dependencies**:
- **Epic 35**: Provider Selection (provider/model lists, YAML structure)
- **Epic 39.1**: FastAPI Web Server Setup (backend)
- **Epic 39.4**: React + Vite Setup (frontend)

**Enables**:
- **Story 39.29**: Provider Validation and Persistence (save logic)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
