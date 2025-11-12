# Epic 35: Interactive Provider Selection at Startup

**Status**: Planning
**Owner**: Amelia (Software Developer)
**Created**: 2025-01-12
**Target Duration**: 1.5-2 weeks (60-80 hours) - UPDATED after CRAAP review

---

## Epic Overview

Add interactive provider selection to the Brian REPL startup flow, enabling users to choose their AI provider (Claude Code, OpenCode, local models) through clear prompts with preference persistence and zero regressions.

This epic implements a comprehensive provider selection system that:
- Detects available AI providers on the system
- Prompts users interactively with Rich-formatted tables
- Validates provider configurations before REPL startup
- Persists preferences to `.gao-dev/provider_preferences.yaml`
- Maintains backward compatibility with existing environment variables
- Includes security hardening (YAML injection prevention)
- Works in both interactive and headless CI/CD environments

---

## Epic Goal

Enable users to interactively select and configure their AI provider at startup through a guided, validated, and secure selection flow that works across all platforms and deployment environments.

---

## Success Criteria

- ✅ Interactive prompts work on first-time startup
- ✅ Saved preferences reused on subsequent startups
- ✅ All existing tests pass (no regressions)
- ✅ >90% test coverage for new code
- ✅ Works on Windows, macOS, Linux
- ✅ Selection flow completes in <30 seconds
- ✅ Clear error messages with actionable suggestions
- ✅ Secure against YAML injection attacks
- ✅ Works in headless CI/CD environments (with env var bypass)
- ✅ Feature flag available for rollback

---

## Story Breakdown

### Phase 1: Foundation (Stories 35.1-35.3)

| Story | Title | Points | Dependencies | Priority |
|-------|-------|--------|--------------|----------|
| 35.1 | Project Setup & Architecture | 2 | None | P0 |
| 35.2 | PreferenceManager Implementation | 5 | 35.1 | P0 |
| 35.3 | ProviderValidator Implementation | 5 | 35.1 | P0 |

**Phase 1 Total**: 12 points (~12-16 hours)

**Can Be Done in Parallel**: Stories 35.2 and 35.3 can be developed simultaneously after 35.1 completes.

### Phase 2: UI & Integration (Stories 35.4-35.6)

| Story | Title | Points | Dependencies | Priority |
|-------|-------|--------|--------------|----------|
| 35.4 | InteractivePrompter Implementation | 8 | 35.1 | P0 |
| 35.5 | ProviderSelector Implementation | 5 | 35.2, 35.3, 35.4 | P0 |
| 35.6 | ChatREPL Integration | 3 | 35.5 | P0 |

**Phase 2 Total**: 16 points (~16-20 hours)

**Can Be Done in Parallel**: Story 35.4 can be developed in parallel with 35.2 and 35.3.

### Phase 3: Testing & Polish (Stories 35.7-35.8)

| Story | Title | Points | Dependencies | Priority |
|-------|-------|--------|--------------|----------|
| 35.7 | Comprehensive Testing & Regression Validation | 8 | 35.6 | P0 |
| 35.8 | Documentation & Examples | 3 | 35.7 | P0 |

**Phase 3 Total**: 11 points (~11-14 hours)

---

## Epic Total

**Total Story Points**: 39 points
**Estimated Duration**: 40-50 hours of focused development
**Realistic Timeline**: 1.5-2 weeks (accounting for meetings, reviews, context switching)

---

## Key Dependencies

### Internal Dependencies
- ✅ Epic 30 (Interactive Brian Chat) - Complete
- ✅ Epic 21 (AI Analysis Service) - Complete
- ✅ Provider abstraction system - Complete

### External Dependencies
- ✅ `rich` library - Already installed
- ✅ `prompt_toolkit` - Already installed
- ✅ `pyyaml` - Already installed

### Story-Level Dependencies
- Stories 35.2, 35.3, 35.4 can be developed in parallel after 35.1
- Story 35.5 requires 35.2, 35.3, and 35.4 to be complete
- Stories 35.6, 35.7, 35.8 must be sequential

---

## Architectural Components

### New Components (All in `gao_dev/cli/`)

1. **PreferenceManager** - Manages preference persistence to YAML
   - Load/save preferences with atomic writes
   - YAML injection prevention with `safe_dump()`
   - Input sanitization for security
   - File backup and corruption recovery

2. **ProviderValidator** - Validates provider configurations
   - CLI availability detection (cross-platform)
   - Ollama model detection
   - API key validation
   - Actionable error messages

3. **InteractivePrompter** - User interaction with Rich formatting
   - Provider selection tables
   - Model selection tables
   - OpenCode-specific prompts
   - Error/success displays
   - Lazy import pattern for CI/CD compatibility

4. **ProviderSelector** - Orchestrates the selection flow
   - Priority order: env var → saved prefs → interactive → defaults
   - Validation integration
   - Preference persistence
   - Cancellation handling

### Integration Points
- **ChatREPL** - Modified `__init__()` to call ProviderSelector
- **ProcessExecutor** - Receives provider config (no changes needed)
- **ProviderFactory** - Existing provider registry (no changes needed)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation | Status |
|------|--------|-------------|------------|--------|
| **YAML Injection** | **HIGH** | Low | Use `yaml.safe_dump()`, input sanitization | RESOLVED |
| **CI/CD Breakage** | **HIGH** | Medium | Lazy imports, env var bypass | RESOLVED |
| Breaks existing configs | **HIGH** | Low | Extensive regression testing | IN EPIC |
| Windows compatibility | Medium | Medium | Platform-specific testing | IN EPIC |
| User confusion | Medium | Medium | Clear prompts, good defaults, FAQ | IN EPIC |
| Validation hangs | Medium | Low | Timeouts on all async operations | IN EPIC |
| Performance issues | Low | Low | Caching, async operations | IN EPIC |
| Test complexity | Medium | Medium | Mock everything, clear structure | IN EPIC |

**Critical Risks Resolved**: The CRAAP review identified YAML injection and CI/CD compatibility as critical risks. These have been incorporated into the story requirements with specific mitigation strategies.

---

## CRAAP Review Resolutions

The following critical and moderate issues from the CRAAP review have been incorporated into the story requirements:

### Critical Issues (Priority 1) - RESOLVED

1. **YAML Injection Prevention** (Story 35.2)
   - Added `yaml.safe_dump()` requirement
   - Added input sanitization methods
   - Added security test cases

2. **CI/CD Compatibility** (Story 35.4)
   - Added lazy import pattern for `prompt_toolkit`
   - Added fallback to `input()` for headless environments
   - Added specific test cases

3. **Testing Estimates** (Story 35.7)
   - Acknowledged 8 points is aggressive for 120+ tests
   - Tests distributed across implementation stories (TDD)
   - Story 35.7 focuses on E2E and regression only

4. **Feature Flag for Rollback** (Story 35.1)
   - Added `features.interactive_provider_selection` to defaults.yaml
   - Enables production rollback if issues arise

### Moderate Issues (Priority 2) - INCORPORATED

5. **Windows Compatibility** (All Stories)
   - Added platform-specific notes and test requirements
   - Cross-platform validation in acceptance criteria

6. **Ollama Timeout** (Story 35.3)
   - Increased from 3s to 10s with user feedback

7. **Preference Backup** (Story 35.2)
   - Added backup strategy for corruption recovery
   - Atomic writes with `.bak` files

8. **Async/Sync Handling** (Story 35.6)
   - Clarified sync wrapper pattern for ChatREPL.__init__()
   - Documented in architecture notes

9. **TDD Approach** (All Implementation Stories)
   - Each story 35.2-35.6 includes its own tests
   - Story 35.7 adds E2E and regression tests only

---

## Timeline & Milestones

**Week 1 (40 hours)**:
- **Days 1-2** (16 hours): Stories 35.1-35.3 (Foundation)
  - Day 1: Story 35.1 (2 pts)
  - Days 1-2: Stories 35.2, 35.3, 35.4 in parallel (18 pts total)
    - Developer A: Story 35.2 (PreferenceManager)
    - Developer B: Story 35.3 (ProviderValidator)
    - Developer C: Story 35.4 (InteractivePrompter)

- **Days 3-4** (16 hours): Stories 35.4-35.6 (UI & Integration)
  - Day 3: Story 35.5 (ProviderSelector) - requires 35.2, 35.3, 35.4
  - Day 4: Story 35.6 (ChatREPL Integration)

- **Day 5** (8 hours): Checkpoint & Buffer
  - Integration testing
  - Bug fixes
  - Code reviews

**Week 2 (20 hours)**:
- **Days 6-7** (16 hours): Story 35.7 (Testing & Regression)
  - E2E test scenarios
  - Regression validation
  - Cross-platform testing
  - Security testing
  - Performance validation

- **Day 8** (4 hours): Story 35.8 (Documentation)
  - User guide
  - API reference
  - Examples

**Total Estimated Duration**: 1.5-2 weeks (realistic accounting for meetings, reviews, context switching)

---

## Testing Strategy

### Coverage Requirements

| Component | Unit Tests | Integration Tests | E2E Tests | Target Coverage |
|-----------|-----------|-------------------|-----------|-----------------|
| PreferenceManager | 20+ | 3+ | 1+ | >95% |
| ProviderValidator | 15+ | 5+ | 2+ | >90% |
| InteractivePrompter | 25+ | 5+ | 2+ | >85% |
| ProviderSelector | 10+ | 10+ | 3+ | >90% |
| ChatREPL Integration | 5+ | 15+ | 5+ | >80% |

**Total Target**: 100+ tests, >90% coverage for new code

### Test Distribution (TDD Approach)

- **Story 35.2**: 20+ PreferenceManager tests
- **Story 35.3**: 15+ ProviderValidator tests
- **Story 35.4**: 25+ InteractivePrompter tests
- **Story 35.5**: 20+ ProviderSelector tests
- **Story 35.6**: 10+ ChatREPL integration tests
- **Story 35.7**: 20+ E2E and regression tests
- **Total**: 110+ tests

### Key Test Scenarios

1. **Security Tests** (Story 35.2, 35.7)
   - YAML injection attempts
   - Input sanitization validation
   - Malicious input handling

2. **CI/CD Tests** (Story 35.4, 35.7)
   - Headless environment (no TTY)
   - Docker container without prompt_toolkit
   - Env var bypass validation

3. **Regression Tests** (Story 35.7)
   - All existing CLI commands work
   - Existing configurations unchanged
   - Environment variables still respected
   - Backward compatibility verified

4. **Cross-Platform Tests** (Story 35.7)
   - Windows (CMD, PowerShell, Git Bash)
   - macOS (Terminal)
   - Linux (bash)

---

## Rollback Plan

### Feature Flag
```yaml
# gao_dev/config/defaults.yaml
features:
  interactive_provider_selection: true  # Set to false to disable
```

### Rollback Procedure
1. Set `interactive_provider_selection: false` in defaults.yaml
2. Deploy updated config
3. System reverts to previous behavior (env vars + hardcoded defaults)
4. No data loss, preferences remain but unused

### Monitoring
- Alert on validation failure rate >5%
- Alert on startup time >5s (P95)
- Track preference save/load errors

---

## Success Metrics

### Functional Metrics
- ✅ 100% of provider types supported (3/3: Claude Code, OpenCode, Direct API)
- ✅ 100% of existing tests pass (no regressions)
- ✅ >90% test coverage for new code
- ✅ 0 breaking changes to existing APIs

### Performance Metrics
- ✅ Selection flow completes in <30 seconds
- ✅ Preference loading <100ms
- ✅ Provider validation <2 seconds
- ✅ No increase in REPL startup time (when using env vars)

### Quality Metrics
- ✅ Zero critical security vulnerabilities
- ✅ Works on all platforms (Windows, macOS, Linux)
- ✅ Clear error messages with actionable suggestions
- ✅ Zero critical bugs in production

---

## Future Enhancements (Post-Epic 35)

After Epic 35 complete, consider:
- Global preferences (`~/.gao-dev/global_preferences.yaml`)
- `gao-dev configure` standalone command
- Provider benchmarking and automatic recommendations
- Automatic fallback on provider failure
- Mid-session provider switching (`/switch-provider` command)
- Usage analytics and reporting
- Web-based configuration UI

---

## References

- **PRD**: `docs/features/interactive-provider-selection/PRD.md`
- **Architecture**: `docs/features/interactive-provider-selection/ARCHITECTURE.md`
- **CRAAP Review**: `docs/features/interactive-provider-selection/CRAAP_Review_Interactive_Provider_Selection.md`
- **Epic Definition**: `docs/features/interactive-provider-selection/EPIC-35.md`

---

**Epic Status**: Planning
**Next Action**: Address CRAAP critical issues, then begin Story 35.1
**Last Updated**: 2025-01-12 (Post-CRAAP Review)
