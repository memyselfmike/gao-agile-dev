# Product Requirements Document: Interactive Provider Selection

**Feature Name**: Interactive Provider Selection for Brian REPL
**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Status**: Planning
**Owner**: Amelia (Software Developer)
**Created**: 2025-01-12

---

## 1. Executive Summary

### Problem Statement

Currently, users starting the GAO-Dev REPL (`gao-dev start`) have no way to interactively choose which AI provider to use. The system defaults to `claude-code`, and users must manually set environment variables (`AGENT_PROVIDER`) or modify configuration files to change providers. This creates friction, especially when:

- Testing with different providers (Claude Code, OpenCode, direct APIs)
- Switching between local models (Ollama) and cloud models
- Experimenting with cost optimization strategies
- Working offline with local models

### Proposed Solution

Add an interactive provider selection flow during REPL startup that:
1. Detects available providers on the system
2. Prompts user to select provider (Claude Code, OpenCode, direct API)
3. For OpenCode: asks if using local model (Ollama) vs cloud
4. Prompts for model selection from available models
5. Saves preferences for future sessions (optional)
6. Validates configuration before starting

### Success Criteria

- ✅ Interactive prompts appear on first-time startup
- ✅ Saved preferences are reused on subsequent startups (with option to change)
- ✅ All existing functionality works without regression
- ✅ Provider selection takes <30 seconds for users
- ✅ Invalid configurations are caught before starting REPL
- ✅ Users can skip prompts and use defaults
- ✅ Comprehensive test coverage (>90%)

---

## 2. User Stories

### US-1: As a developer, I want to select my AI provider at startup

**Acceptance Criteria**:
- Given I run `gao-dev start`
- When I'm on first-time startup (no saved preferences)
- Then I see a list of available providers with clear descriptions
- And I can select my preferred provider using keyboard input
- And the selection is validated before proceeding

### US-2: As a cost-conscious developer, I want to use local Ollama models

**Acceptance Criteria**:
- Given I select "OpenCode" as my provider
- When prompted for AI provider type
- Then I see options for "local (Ollama)" and "cloud (Anthropic/OpenAI/Google)"
- And I can choose "local"
- And the system lists available Ollama models
- And I can select a specific local model

### US-3: As a returning user, I want my preferences remembered

**Acceptance Criteria**:
- Given I've previously selected a provider and saved preferences
- When I run `gao-dev start` again
- Then I see my saved configuration
- And I'm asked "Use saved provider: opencode + deepseek-r1? [Y/n]"
- And pressing Enter uses the saved config
- And I can type "n" to reconfigure

### US-4: As a power user, I want to skip prompts and use environment variables

**Acceptance Criteria**:
- Given I have `AGENT_PROVIDER=claude-code` set
- When I run `gao-dev start`
- Then the system uses my env var without prompting
- And I see a message confirming the provider in use

### US-5: As a developer, I want clear error messages when providers fail

**Acceptance Criteria**:
- Given I select a provider that's not properly configured
- When the system validates the provider
- Then I see a clear error message explaining the issue
- And I get suggestions for fixing it (e.g., "Install OpenCode CLI: npm install -g opencode")
- And I'm prompted to select a different provider

---

## 3. Technical Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Complexity |
|----|-------------|----------|------------|
| FR-1 | Interactive provider selection UI with Rich formatting | P0 | Medium |
| FR-2 | Preference persistence to `.gao-dev/provider_preferences.yaml` | P0 | Low |
| FR-3 | Provider availability detection | P0 | Medium |
| FR-4 | OpenCode-specific prompts (local vs cloud) | P0 | Low |
| FR-5 | Model selection from available models | P0 | Medium |
| FR-6 | Validation before starting REPL | P0 | Medium |
| FR-7 | Skip option for defaults | P1 | Low |
| FR-8 | Environment variable override | P1 | Low |
| FR-9 | Interactive reconfiguration command | P2 | Low |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Selection flow completes in <30 seconds | <30s |
| NFR-2 | Zero regressions in existing functionality | 100% |
| NFR-3 | Test coverage for new code | >90% |
| NFR-4 | Works on Windows, macOS, Linux | All platforms |
| NFR-5 | Preference loading time | <100ms |
| NFR-6 | Clear, user-friendly prompts | Subjective/QA |

### 3.3 Constraints

- Must maintain backward compatibility with existing configurations
- Must work with all existing providers (Claude Code, OpenCode, direct APIs)
- Must not require network calls during provider selection (except validation)
- Must respect existing environment variables
- Must be testable without live API credentials

---

## 4. User Experience Design

### 4.1 First-Time Startup Flow

```
$ gao-dev start

┌─────────────────────────────────────────────────┐
│ Welcome to GAO-Dev Interactive Setup            │
└─────────────────────────────────────────────────┘

Available AI Providers
┌────────┬─────────────────────┬──────────────────────────────────┐
│ Option │ Provider            │ Description                      │
├────────┼─────────────────────┼──────────────────────────────────┤
│ 1      │ claude-code         │ Claude Code CLI (Anthropic)      │
│ 2      │ opencode            │ OpenCode CLI (Multi-provider)    │
│ 3      │ direct-api-anthropic│ Direct Anthropic API             │
└────────┴─────────────────────┴──────────────────────────────────┘

Select provider [1/2/3] (1): 2

┌─────────────────────────────────────────────────┐
│ OpenCode Configuration                          │
└─────────────────────────────────────────────────┘

Use local model via Ollama? [y/N]: y

Detecting available Ollama models...

Available Models
┌────────┬────────────────┬─────────────────────────────┐
│ Option │ Model          │ Size                         │
├────────┼────────────────┼─────────────────────────────┤
│ 1      │ deepseek-r1    │ 7B (recommended for coding) │
│ 2      │ llama2         │ 7B                          │
│ 3      │ codellama      │ 13B                         │
└────────┴────────────────┴─────────────────────────────┘

Select model [1/2/3] (1): 1

✓ Configuration validated successfully

Save as default for future sessions? [Y/n]: y

✓ Preferences saved to .gao-dev/provider_preferences.yaml

Starting GAO-Dev with OpenCode + deepseek-r1...

[Normal REPL greeting follows...]
```

### 4.2 Returning User Flow

```
$ gao-dev start

┌─────────────────────────────────────────────────┐
│ Provider Configuration Detected                 │
└─────────────────────────────────────────────────┘

Saved provider: opencode (local: deepseek-r1)

Use saved configuration? [Y/n/c(hange)]:

  Y - Use saved config (default)
  n - Reconfigure from scratch
  c - Change specific settings

Your choice [Y/n/c]: <Enter>

✓ Using saved configuration

Starting GAO-Dev with OpenCode + deepseek-r1...

[Normal REPL greeting follows...]
```

### 4.3 Error Handling Flow

```
$ gao-dev start

[Provider selection...]

Select provider [1/2/3] (1): 2

Validating OpenCode CLI...

✗ Error: OpenCode CLI not found

OpenCode is not installed or not in PATH.

Installation Options:
  1. npm install -g opencode
  2. Download from: https://github.com/opencode/cli

Would you like to:
  [1] Try different provider
  [2] Exit and install OpenCode
  [3] Continue anyway (may fail)

Your choice [1/2/3] (1): 1

[Returns to provider selection...]
```

---

## 5. System Architecture Integration

### 5.1 Component Diagram

```
ChatREPL
  │
  ├─ ProviderSelector (NEW)
  │   ├─ InteractivePrompter (NEW)
  │   ├─ PreferenceManager (NEW)
  │   └─ ProviderValidator (NEW)
  │
  ├─ ProcessExecutor (EXISTING - no changes)
  │   └─ ProviderFactory (EXISTING)
  │
  └─ ConversationalBrian (EXISTING - no changes)
```

### 5.2 Data Flow

```
1. User runs `gao-dev start`
2. ChatREPL.__init__() → ProviderSelector.select_provider()
3. ProviderSelector checks:
   - Environment variables (AGENT_PROVIDER)
   - Saved preferences (.gao-dev/provider_preferences.yaml)
   - If neither: prompt user
4. ProviderSelector.validate_provider() → validates configuration
5. Return provider_config dict
6. ChatREPL creates ProcessExecutor with provider_config
7. Normal REPL startup continues
```

### 5.3 Configuration File Format

**`.gao-dev/provider_preferences.yaml`**:
```yaml
# GAO-Dev Provider Preferences
# Auto-generated by interactive setup

version: "1.0"
last_updated: "2025-01-12T10:30:00Z"

provider:
  name: "opencode"
  type: "cli"  # cli, api, sdk

  config:
    ai_provider: "ollama"  # ollama, anthropic, openai, google
    model: "deepseek-r1"
    timeout: 3600

    # OpenCode-specific
    use_local: true
    local_model_path: null  # null = use default

  validation:
    last_validated: "2025-01-12T10:30:00Z"
    cli_version: "1.2.3"
    status: "healthy"

preferences:
  skip_prompts: false  # Set to true to always use saved config
  auto_validate: true  # Validate provider on startup
  fallback_enabled: true  # Fall back to claude-code if provider fails
```

---

## 6. Testing Strategy

### 6.1 Test Coverage Requirements

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|-----------|-------------------|-----------|
| InteractivePrompter | 15+ | 5+ | 2+ |
| PreferenceManager | 20+ | 3+ | 1+ |
| ProviderValidator | 15+ | 5+ | 2+ |
| ProviderSelector | 10+ | 10+ | 3+ |
| ChatREPL Integration | 5+ | 15+ | 5+ |

**Total Target**: 100+ tests

### 6.2 Regression Test Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Existing env var set | Uses env var, no prompts |
| Legacy CLI args | Still works unchanged |
| Existing .gao-dev/documents.db | Not affected |
| Existing ChatREPL commands | All work identically |
| Brian analysis | Uses selected provider correctly |
| Command routing | Works with all providers |
| Session state | Persists correctly |

### 6.3 Test Automation

- **Mock all user input** using `prompt_toolkit` test utilities
- **Mock provider validation** to avoid live API calls
- **Parameterize tests** for all provider types
- **CI/CD integration** with existing pytest suite
- **Coverage gates**: >90% for new code, no decrease in overall coverage

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1)
- Stories 35.1-35.3
- Core components: PreferenceManager, ProviderValidator
- Unit tests and basic integration

### Phase 2: UI & Integration (Week 1)
- Stories 35.4-35.5
- InteractivePrompter, ProviderSelector
- ChatREPL integration

### Phase 3: Testing & Polish (Week 1)
- Stories 35.6-35.7
- Comprehensive testing, regression validation
- Documentation and examples

**Total Duration**: 1 week (40-50 hours)

---

## 8. Dependencies

### 8.1 Internal Dependencies
- Epic 30 (Interactive Brian Chat) - Complete ✅
- Epic 21 (AI Analysis Service) - Complete ✅
- Provider abstraction system - Complete ✅

### 8.2 External Dependencies
- `rich` library - Already installed ✅
- `prompt_toolkit` - Already installed ✅
- `pyyaml` - Already installed ✅

### 8.3 Blocked By
- None (all dependencies complete)

---

## 9. Success Metrics

### 9.1 Functional Metrics
- ✅ 100% of provider types supported (3/3)
- ✅ 100% of existing tests pass (no regressions)
- ✅ >90% test coverage for new code
- ✅ 0 breaking changes to existing APIs

### 9.2 User Experience Metrics
- ✅ Selection flow completes in <30 seconds
- ✅ Preference loading <100ms
- ✅ Clear error messages with actionable suggestions
- ✅ Works on all platforms (Windows, macOS, Linux)

### 9.3 Quality Metrics
- ✅ Zero critical bugs found in testing
- ✅ All acceptance criteria met
- ✅ Documentation complete and accurate
- ✅ Code review approved

---

## 10. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaks existing configs | High | Low | Extensive regression tests |
| User confusion with prompts | Medium | Medium | Clear UI, skip options, good defaults |
| Provider validation slow | Low | Low | Cache validation results |
| Cross-platform issues | Medium | Low | Test on all platforms |
| Preference file corruption | Low | Low | Validation + fallback to prompts |

---

## 11. Open Questions

1. **Q**: Should we add a `gao-dev configure` command for changing preferences without starting REPL?
   **A**: Yes, add in Story 35.8 (optional stretch goal)

2. **Q**: Should we auto-detect Ollama installation?
   **A**: Yes, check for `ollama` command in PATH

3. **Q**: Should preferences be per-project or global?
   **A**: Per-project (in `.gao-dev/`), with option for global defaults in future

4. **Q**: What if user Ctrl+C during prompts?
   **A**: Graceful exit with message, no preferences saved

---

## 12. Future Enhancements

- Global preferences in `~/.gao-dev/global_preferences.yaml`
- Provider performance benchmarking and recommendations
- Auto-switch to fastest provider based on task type
- Cloud cost estimation before starting session
- Provider A/B testing mode
- Integration with provider selection strategies from Epic 11

---

## Approval

- [ ] Product Owner: _______________
- [ ] Technical Lead: _______________
- [ ] Engineering Manager: _______________
- [ ] Date: _______________

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-12 | Claude | Initial PRD creation |
