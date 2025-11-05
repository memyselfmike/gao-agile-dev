# Epic 11: Agent Provider Abstraction System
## Epic Breakdown

**Feature**: Agent Provider Abstraction
**Total Story Points**: 94
**Estimated Duration**: 4 weeks
**Priority**: High
**Status**: Planning

---

## Epic Overview

Transform GAO-Dev from Claude Code-dependent to provider-agnostic architecture supporting multiple AI agent backends (Claude Code, OpenCode, direct APIs, custom providers) without breaking existing functionality.

**Strategic Value**:
- **Risk Mitigation**: Eliminate single-provider dependency
- **Cost Optimization**: Enable intelligent provider selection
- **Flexibility**: Support multiple AI providers
- **Community Growth**: Plugin ecosystem for custom providers

---

## Phase 1: Foundation (Week 1)
**Goal**: Create provider abstraction layer without breaking existing functionality

### Story 11.1: Create Provider Interface & Base Structure
**Story Points**: 8
**Priority**: Critical
**Dependencies**: None

**Description**:
Define IAgentProvider interface and create base provider module structure.

**Tasks**:
- Create `gao_dev/core/providers/` module structure
- Define `IAgentProvider` abstract interface
- Create provider exception hierarchy
- Create provider models (AgentContext, enums)
- Write interface documentation
- Add type hints and validation

**Acceptance Criteria**:
- IAgentProvider interface complete with all methods defined
- Exception hierarchy covers all error cases
- Type checking passes (mypy strict mode)
- Documentation includes usage examples
- Unit tests for exception hierarchy

**Files Created**:
- `gao_dev/core/providers/__init__.py`
- `gao_dev/core/providers/base.py`
- `gao_dev/core/providers/exceptions.py`
- `gao_dev/core/providers/models.py`
- `tests/core/providers/test_base.py`
- `tests/core/providers/test_exceptions.py`

---

### Story 11.2: Implement ClaudeCodeProvider
**Story Points**: 13
**Priority**: Critical
**Dependencies**: Story 11.1

**Description**:
Extract current ProcessExecutor logic into ClaudeCodeProvider, maintaining exact behavior while conforming to IAgentProvider interface.

**Tasks**:
- Implement `ClaudeCodeProvider` class
- Extract subprocess logic from `ProcessExecutor`
- Maintain exact CLI flag behavior
- Implement model name translation mapping
- Add tool support checking
- Include CLI auto-detection from `cli_detector.py`
- Handle all error cases identically
- Add comprehensive logging

**Acceptance Criteria**:
- ClaudeCodeProvider produces identical output to current ProcessExecutor
- All 400+ existing tests pass without modification
- Performance within 5% of current implementation
- Error handling matches current behavior
- Type checking passes
- Unit tests achieve >90% coverage

**Files Created/Modified**:
- `gao_dev/core/providers/claude_code.py`
- `tests/core/providers/test_claude_code.py`
- `tests/integration/test_claude_code_integration.py`

---

### Story 11.3: Create Provider Factory
**Story Points**: 5
**Priority**: High
**Dependencies**: Story 11.1, Story 11.2

**Description**:
Implement ProviderFactory for centralized provider creation with plugin support.

**Tasks**:
- Implement `ProviderFactory` class
- Support provider registration (built-in and plugin)
- Validate provider classes implement IAgentProvider
- Create provider instances with configuration
- Handle duplicate registration errors
- Add provider discovery (list, exists, get_class)
- Register built-in providers

**Acceptance Criteria**:
- Factory creates ClaudeCodeProvider successfully
- Registration validates interface compliance
- Duplicate registration raises clear error
- list_providers() returns correct results
- Unit tests cover all public methods
- Type checking passes

**Files Created**:
- `gao_dev/core/providers/factory.py`
- `tests/core/providers/test_factory.py`

---

### Story 11.4: Refactor ProcessExecutor to Use Providers
**Story Points**: 8
**Priority**: Critical
**Dependencies**: Story 11.2, Story 11.3

**Description**:
Update ProcessExecutor to use provider abstraction while maintaining 100% backward compatibility.

**Tasks**:
- Update ProcessExecutor constructor to accept provider
- Support legacy constructor signature (cli_path, api_key)
- Default to "claude-code" provider
- Delegate execution to provider
- Update logging to be provider-agnostic
- Preserve timeout handling
- Add deprecation warnings for legacy usage
- Update all ProcessExecutor tests

**Acceptance Criteria**:
- All existing ProcessExecutor tests pass unchanged
- Legacy constructor (cli_path, api_key) works identically
- New provider-based constructor works
- No breaking API changes
- Performance unchanged (<5% variance)
- Type checking passes
- Documentation updated

**Files Modified**:
- `gao_dev/core/services/process_executor.py`
- `tests/core/services/test_process_executor.py`
- `tests/integration/test_process_executor_legacy.py`

---

### Story 11.5: Update Configuration Schema for Providers
**Story Points**: 5
**Priority**: High
**Dependencies**: Story 11.3

**Description**:
Extend agent YAML configuration schema to support provider selection while maintaining backward compatibility.

**Tasks**:
- Add optional `provider` field to agent YAML schema
- Add optional `provider_config` field
- Update JSON Schema validation
- Add provider registry to `defaults.yaml`
- Add model name mapping configuration
- Support canonical model names
- Document configuration changes
- Create migration examples

**Acceptance Criteria**:
- Schema validation passes for old and new configs
- Old configs work without any modification
- New provider field is optional (defaults to "claude-code")
- Provider-specific config validated per provider
- Model translation config working
- Documentation complete with examples
- Migration guide created

**Files Modified**:
- `gao_dev/config/defaults.yaml`
- `gao_dev/config/schemas/agent_schema.json`
- `tests/core/test_config_schema_validation.py`

**Files Created**:
- `docs/MIGRATION_PROVIDER.md`

---

## Phase 2: OpenCode Integration (Week 2)
**Goal**: Add OpenCode as alternative provider

### Story 11.6: OpenCode Research & CLI Mapping
**Story Points**: 5
**Priority**: High
**Dependencies**: None (can run in parallel with Phase 1)

**Description**:
Install and test OpenCode CLI to understand integration requirements and document findings.

**Tasks**:
- Install OpenCode and Bun runtime locally
- Document OpenCode CLI flags and options
- Test basic task execution
- Map OpenCode tools to GAO-Dev tools
- Test output format and parsing
- Document behavioral differences from Claude Code
- Test with multiple providers (Anthropic, OpenAI, Google)
- Create OpenCode setup guide

**Acceptance Criteria**:
- OpenCode successfully executes basic coding task
- CLI flags documented completely
- Tool mapping table created
- Output format documented with examples
- Known issues/limitations documented
- Setup guide tested by external reviewer
- Decision made: proceed with implementation or not

**Deliverables**:
- OpenCode research report (`docs/opencode-research.md`)
- Setup guide (`docs/opencode-setup-guide.md`)
- Tool compatibility matrix
- CLI reference document

---

### Story 11.7: Implement OpenCodeProvider
**Story Points**: 13
**Priority**: High
**Dependencies**: Story 11.1, Story 11.6

**Description**:
Implement full OpenCode provider supporting multiple AI backends (Anthropic, OpenAI, Google).

**Tasks**:
- Implement `OpenCodeProvider` class conforming to IAgentProvider
- Support provider selection (anthropic, openai, google)
- Handle CLI invocation with correct flags
- Parse OpenCode output format
- Implement model name translation
- Map GAO-Dev tools to OpenCode tools
- Handle errors and edge cases
- Add configuration validation
- Support timeout handling
- Add comprehensive logging

**Acceptance Criteria**:
- OpenCodeProvider executes tasks successfully
- Works with Anthropic and OpenAI backends
- Output parsed correctly
- Error handling matches ClaudeCodeProvider quality
- Integration tests pass
- Performance acceptable (<2x Claude Code latency)
- Type checking passes
- Unit tests >90% coverage

**Files Created**:
- `gao_dev/core/providers/opencode.py`
- `tests/core/providers/test_opencode.py`
- `tests/integration/test_opencode_integration.py`

---

### Story 11.8: Provider Comparison Test Suite
**Story Points**: 8
**Priority**: Medium
**Dependencies**: Story 11.2, Story 11.7

**Description**:
Create automated test suite that validates provider equivalence and documents differences.

**Tasks**:
- Create test cases that run against all providers
- Compare outputs for identical tasks
- Document behavioral differences
- Create compatibility matrix
- Performance benchmarks per provider
- Add tests to CI pipeline
- Generate comparison report

**Acceptance Criteria**:
- Test suite runs against ClaudeCode and OpenCode
- Compatibility matrix auto-generated
- Performance benchmarks documented
- CI integration complete
- Behavioral differences clearly documented
- Tests added to nightly CI run

**Files Created**:
- `tests/comparison/test_provider_comparison.py`
- `tests/comparison/test_provider_parity.py`
- `tests/comparison/fixtures/comparison_tasks.yaml`
- `scripts/generate_comparison_report.py`

---

### Story 11.9: Multi-Provider Documentation
**Story Points**: 5
**Priority**: High
**Dependencies**: Story 11.7

**Description**:
Comprehensive documentation for multi-provider setup and usage.

**Tasks**:
- Update CLAUDE.md with provider information
- Create provider selection decision tree
- Document provider configuration for each provider
- Update CLI command reference
- Create troubleshooting guide
- Add FAQ section
- Create video tutorial (optional)
- External review of documentation

**Acceptance Criteria**:
- CLAUDE.md updated and accurate
- Setup guide tested by external user
- Decision tree helps users choose provider
- Troubleshooting covers common issues
- All CLI commands documented
- FAQ addresses user questions
- Documentation reviewed and approved

**Files Created/Modified**:
- `CLAUDE.md` (updated)
- `docs/provider-selection-guide.md`
- `docs/provider-troubleshooting.md`
- `docs/provider-faq.md`
- `README.md` (updated with provider info)

---

## Phase 3: Advanced Features (Week 3)
**Goal**: Add advanced provider features and optimizations

### Story 11.10: Implement Direct API Provider
**Story Points**: 13
**Priority**: Medium
**Dependencies**: Story 11.1

**Description**:
Implement provider using direct API calls (no CLI subprocess) for better performance.

**Tasks**:
- Implement `DirectAPIProvider` using Anthropic SDK
- Support streaming responses via async generator
- Implement tool execution locally (no subprocess)
- Add retry logic with exponential backoff
- Add rate limiting to prevent API errors
- Optimize for performance (connection pooling)
- Support multiple API providers (Anthropic, OpenAI, Google)
- Handle API-specific errors

**Acceptance Criteria**:
- DirectAPIProvider works for basic tasks
- Performance improvement vs subprocess (>20% faster)
- Streaming works correctly
- Retry logic handles transient failures
- Rate limiting prevents 429 errors
- Integration tests pass
- Type checking passes
- Unit tests >90% coverage

**Files Created**:
- `gao_dev/core/providers/direct_api.py`
- `gao_dev/core/providers/api_client.py`
- `tests/core/providers/test_direct_api.py`
- `tests/integration/test_direct_api_integration.py`

---

### Story 11.11: Provider Selection Strategy
**Story Points**: 8
**Priority**: Medium
**Dependencies**: Story 11.2, Story 11.7, Story 11.10

**Description**:
Intelligent provider selection and fallback logic for reliability and optimization.

**Tasks**:
- Implement provider auto-detection
- Create fallback chain (primary → secondary → tertiary)
- Add cost-based routing (task type → cheapest provider)
- Add performance-based routing (critical path → fastest)
- Support user preference overrides
- Implement provider health checking
- Add provider selection logging
- Create selection strategy configuration

**Acceptance Criteria**:
- Auto-detection works for all providers
- Fallback activates automatically on primary failure
- Cost routing selects cheapest suitable provider
- Performance routing selects fastest provider
- User overrides respected
- Health checks prevent using broken providers
- Logging shows selection reasoning
- Configuration documented

**Files Created**:
- `gao_dev/core/providers/selector.py`
- `gao_dev/core/providers/health_check.py`
- `tests/core/providers/test_selector.py`
- `tests/integration/test_provider_fallback.py`

---

### Story 11.12: Provider Plugin System
**Story Points**: 8
**Priority**: Medium
**Dependencies**: Story 11.3

**Description**:
Extend existing plugin system to support custom provider plugins.

**Tasks**:
- Create `BaseProviderPlugin` interface
- Extend plugin discovery for providers
- Add provider plugin registration
- Add provider plugin validation
- Create example custom provider plugin
- Document provider plugin development
- Test plugin registration and usage
- Add plugin examples to repository

**Acceptance Criteria**:
- Example provider plugin works
- Plugin discovery finds provider plugins
- Registration automatic via plugin system
- Validation prevents broken plugins
- Documentation clear and complete
- Test plugin included in examples
- Integration tests pass

**Files Created**:
- `gao_dev/plugins/provider_plugin.py`
- `examples/custom-provider-plugin/`
- `docs/provider-plugin-development.md`
- `tests/plugins/test_provider_plugin.py`

---

### Story 11.13: Performance Optimization
**Story Points**: 5
**Priority**: Low
**Dependencies**: All providers implemented

**Description**:
Optimize provider system for production performance.

**Tasks**:
- Benchmark all providers (ClaudeCode, OpenCode, DirectAPI)
- Optimize subprocess handling (pooling exploration)
- Add provider-level caching where appropriate
- Reduce factory overhead
- Profile hot paths and optimize
- Document performance characteristics
- Create performance comparison chart

**Acceptance Criteria**:
- Benchmarks show <5% overhead vs direct implementation
- Caching improves repeat task performance (where applicable)
- Factory overhead <10ms
- Profile shows no major bottlenecks
- Performance comparison documented
- Optimizations don't break functionality

**Files Created**:
- `scripts/benchmark_providers.py`
- `docs/provider-performance.md`
- Performance comparison charts

---

## Phase 4: Production Readiness (Week 4)
**Goal**: Polish, test, and deploy to production

### Story 11.14: Comprehensive Testing & Quality Assurance
**Story Points**: 13
**Priority**: Critical
**Dependencies**: All features implemented

**Description**:
Full test coverage and validation for production deployment.

**Tasks**:
- End-to-end tests with all providers
- Stress testing (100+ concurrent tasks)
- Error handling tests (network failures, timeouts)
- API key validation tests
- Configuration validation tests
- Provider fallback tests
- Performance regression tests
- Security review
- External QA testing

**Acceptance Criteria**:
- Test coverage >90% for provider module
- All edge cases covered with tests
- Stress tests pass (100 concurrent tasks, no failures)
- Error handling comprehensive and tested
- No flaky tests in CI
- Security review passed
- External QA passed
- All 400+ existing tests still pass

**Files Created**:
- `tests/e2e/test_provider_workflows.py`
- `tests/stress/test_provider_concurrency.py`
- `tests/security/test_provider_security.py`
- CI/CD workflow updates

---

### Story 11.15: Migration Tooling & Commands
**Story Points**: 5
**Priority**: High
**Dependencies**: All features complete

**Description**:
CLI tools and documentation for migrating existing configurations to new provider system.

**Tasks**:
- Implement `gao-dev providers list` command
- Implement `gao-dev providers validate` command
- Implement `gao-dev providers migrate` command (optional)
- Create migration guide
- Test migration on real projects
- Add rollback instructions
- External user testing of migration

**Acceptance Criteria**:
- `list` command shows available/configured providers
- `validate` command checks configuration correctness
- `migrate` command updates configs (if needed)
- Migration guide tested by external user
- Zero data loss during migration
- Rollback instructions work
- Commands documented in CLI reference

**Files Created/Modified**:
- `gao_dev/cli/providers_commands.py`
- `docs/MIGRATION_PROVIDER.md` (updated)
- `tests/cli/test_providers_commands.py`

---

### Story 11.16: Production Documentation & Release
**Story Points**: 5
**Priority**: Critical
**Dependencies**: All stories complete

**Description**:
Complete production-ready documentation and prepare release.

**Tasks**:
- API reference for IAgentProvider complete
- Configuration reference (all providers)
- Troubleshooting guide comprehensive
- FAQ addresses common questions
- Security best practices documented
- Performance tuning guide created
- Update CHANGELOG with all changes
- Create release notes
- Version bump (minor version: 0.X.0 → 0.Y.0)
- Tag release in git
- Announcement blog post

**Acceptance Criteria**:
- Documentation complete and reviewed
- CHANGELOG comprehensive
- Release notes clear and exciting
- Version tagged correctly
- Announcement ready for publication
- External documentation review passed

**Files Created/Modified**:
- `CHANGELOG.md` (updated)
- `docs/api/provider-api-reference.md`
- `docs/provider-configuration-reference.md`
- `docs/provider-security.md`
- Release notes
- Announcement blog post

---

## Story Summary

### By Phase

**Phase 1: Foundation** (5 stories, 39 SP)
- 11.1: Provider Interface (8 SP)
- 11.2: ClaudeCodeProvider (13 SP)
- 11.3: Provider Factory (5 SP)
- 11.4: Refactor ProcessExecutor (8 SP)
- 11.5: Configuration Schema (5 SP)

**Phase 2: OpenCode** (4 stories, 31 SP)
- 11.6: OpenCode Research (5 SP)
- 11.7: OpenCodeProvider (13 SP)
- 11.8: Comparison Tests (8 SP)
- 11.9: Multi-Provider Docs (5 SP)

**Phase 3: Advanced** (4 stories, 34 SP)
- 11.10: Direct API Provider (13 SP)
- 11.11: Provider Selection (8 SP)
- 11.12: Plugin System (8 SP)
- 11.13: Performance Optimization (5 SP)

**Phase 4: Production** (3 stories, 23 SP)
- 11.14: Testing & QA (13 SP)
- 11.15: Migration Tooling (5 SP)
- 11.16: Documentation & Release (5 SP)

### By Priority

**Critical** (5 stories, 47 SP):
- 11.1, 11.2, 11.4, 11.14, 11.16

**High** (6 stories, 33 SP):
- 11.3, 11.5, 11.6, 11.7, 11.9, 11.15

**Medium** (5 stories, 42 SP):
- 11.8, 11.10, 11.11, 11.12

**Low** (1 story, 5 SP):
- 11.13

**Total**: 16 stories, 94 story points

---

## Dependencies Graph

```
Phase 1:
11.1 (Interface) ─┬─→ 11.2 (ClaudeCodeProvider) ─┬─→ 11.4 (ProcessExecutor)
                 │                                 │
                 └─→ 11.3 (Factory) ──────────────┴─→ 11.5 (Config Schema)

Phase 2:
11.6 (OpenCode Research) ─→ 11.7 (OpenCodeProvider) ─┬─→ 11.8 (Comparison)
                                                       └─→ 11.9 (Docs)

Phase 3:
11.1 ─→ 11.10 (DirectAPIProvider) ─┐
11.2 ─→ 11.11 (Selection) ─────────┤
11.7 ─→ 11.11 (Selection) ─────────┼─→ 11.13 (Optimization)
11.10 ─→ 11.11 (Selection) ────────┘
11.3 ─→ 11.12 (Plugin System)

Phase 4:
ALL ─→ 11.14 (Testing) ─→ 11.15 (Migration) ─→ 11.16 (Release)
```

---

## Risk Register

### High Risk

**Risk**: OpenCode CLI does not meet requirements
- **Impact**: High - Would block Phase 2
- **Probability**: Medium
- **Mitigation**: Early research (Story 11.6), fallback to DirectAPI only

**Risk**: Breaking existing functionality
- **Impact**: Critical - Would break all users
- **Probability**: Low (with proper testing)
- **Mitigation**: 100% backward compatibility, comprehensive testing, beta period

### Medium Risk

**Risk**: Performance degradation
- **Impact**: Medium - Could slow agent execution
- **Probability**: Medium
- **Mitigation**: Benchmarks at each phase, <5% acceptable, optimization story

**Risk**: Provider feature parity issues
- **Impact**: Medium - Limits provider switching
- **Probability**: High
- **Mitigation**: Feature compatibility matrix, graceful degradation

### Low Risk

**Risk**: Complex user migration
- **Impact**: Low - Can use defaults
- **Probability**: Low
- **Mitigation**: Backward compatible, migration tooling, clear documentation

---

## Success Criteria

### Technical Success
- ✅ All 400+ existing tests pass unchanged
- ✅ New test coverage >90% for provider module
- ✅ Performance overhead <5%
- ✅ 3+ working providers (ClaudeCode, OpenCode, DirectAPI)
- ✅ Zero breaking API changes

### User Success
- ✅ Existing users see no disruption
- ✅ 95%+ successful migrations (for those who migrate)
- ✅ Clear documentation rated 4.5+/5
- ✅ Provider switching works smoothly

### Business Success
- ✅ Eliminate single-provider risk
- ✅ Enable cost optimization (20-40% potential savings)
- ✅ Plugin ecosystem foundation established
- ✅ Community engagement increase

---

## Timeline

**Week 1 (Phase 1)**: Foundation
- Mon-Tue: Stories 11.1, 11.2
- Wed: Story 11.3
- Thu: Story 11.4
- Fri: Story 11.5

**Week 2 (Phase 2)**: OpenCode
- Mon: Story 11.6 (research)
- Tue-Wed: Story 11.7
- Thu: Story 11.8
- Fri: Story 11.9

**Week 3 (Phase 3)**: Advanced
- Mon-Tue: Story 11.10
- Wed: Story 11.11
- Thu: Story 11.12
- Fri: Story 11.13

**Week 4 (Phase 4)**: Production
- Mon-Tue: Story 11.14
- Wed: Story 11.15
- Thu: Story 11.16
- Fri: Release & celebration!

**Total**: 4 weeks, 94 story points

---

## Next Steps

1. **Review & Approve Epic Breakdown**
   - Product Manager (John) review
   - Technical Architect (Winston) review
   - Lead Developer (Amelia) review

2. **Create Individual Story Files**
   - Create `stories/epic-11/` folder
   - Create story markdown files (story-11.1.md through story-11.16.md)

3. **Update Sprint Planning**
   - Add to `docs/sprint-status.yaml`
   - Allocate stories to sprints

4. **Begin Phase 1 Implementation**
   - Start with Story 11.1 (Provider Interface)
   - Daily standups to track progress

---

**Epic Owner**: Bob (Scrum Master)
**Technical Lead**: Amelia (Lead Developer)
**Stakeholders**: All GAO-Dev users and contributors
