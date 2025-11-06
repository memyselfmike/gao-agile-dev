# Epic 19: OpenCode SDK Integration

## Epic Breakdown

**Feature**: OpenCode SDK Provider
**Total Story Points**: 21
**Estimated Duration**: 1 week
**Priority**: High
**Status**: Planning

---

## Epic Overview

Replace the problematic CLI-based OpenCode provider with a robust SDK-based implementation using OpenCode's Python SDK and HTTP API architecture, eliminating subprocess hanging issues and enabling reliable multi-provider support.

**Strategic Value**:
- **Reliability**: Eliminate blocking subprocess issues
- **Performance**: Direct API access vs CLI subprocess overhead
- **Extensibility**: Enable advanced OpenCode features
- **User Experience**: Seamless provider switching

---

## Story Breakdown

### Story 19.1: Add OpenCode SDK Dependency
**Story Points**: 2
**Priority**: Critical
**Dependencies**: None

**Description**:
Add `opencode-ai` Python SDK to project dependencies and verify installation.

**Tasks**:
- Add `opencode-ai` to `pyproject.toml` dependencies
- Update `poetry.lock` or `requirements.txt`
- Verify SDK imports successfully
- Document SDK version and compatibility

**Acceptance Criteria**:
- SDK added to dependencies with version `^0.1.0a36`
- `pip install -e .` works without errors
- `from opencode_ai import Opencode` imports successfully
- Documentation notes SDK is pre-release

**Files Modified**:
- `pyproject.toml`

**Testing**:
- Manual: `python -c "from opencode_ai import Opencode; print('OK')"`
- CI: Dependency installation test

---

### Story 19.2: Implement OpenCodeSDKProvider Core
**Story Points**: 8
**Priority**: Critical
**Dependencies**: Story 19.1

**Description**:
Implement core `OpenCodeSDKProvider` class with session management and task execution using the OpenCode SDK.

**Tasks**:
- Create `opencode_sdk.py` in `gao_dev/core/providers/`
- Implement `OpenCodeSDKProvider` class inheriting from `IAgentProvider`
- Implement `execute_task()` method using SDK's session.chat API
- Add model name translation (canonical → provider_id/model_id)
- Implement `supports_tool()` and `get_supported_models()`
- Add comprehensive logging with structlog
- Handle SDK exceptions and translate to provider exceptions

**Acceptance Criteria**:
- Class implements all `IAgentProvider` interface methods
- `execute_task()` successfully creates session, sends chat, returns response
- Model translation works for all standard models
- Type checking passes (mypy strict mode)
- Logging covers all operations

**Files Created**:
- `gao_dev/core/providers/opencode_sdk.py`

**Testing**:
- Unit tests for all methods
- Mock SDK client for isolated testing
- Integration test with real SDK

---

### Story 19.3: Server Lifecycle Management
**Story Points**: 5
**Priority**: High
**Dependencies**: Story 19.2

**Description**:
Implement robust OpenCode server lifecycle management including auto-start, health checks, and graceful shutdown.

**Tasks**:
- Add server startup logic in `initialize()` method
- Implement health check using SDK or HTTP request
- Add server shutdown logic in `cleanup()` method
- Handle server startup failures with retries
- Add configurable port support
- Implement server process management
- Add timeout handling for server operations

**Acceptance Criteria**:
- Server starts automatically on provider initialization
- Health check confirms server readiness before task execution
- Server shuts down gracefully on cleanup
- Retries server startup on failure (max 3 attempts)
- Port configurable via constructor parameter
- Clear error messages for server failures
- Server process cleanup on Python exit

**Files Modified**:
- `gao_dev/core/providers/opencode_sdk.py`

**Testing**:
- Unit tests for server management methods
- Integration test: server lifecycle
- Error case: port already in use
- Error case: server crash during execution

---

### Story 19.4: Integration Testing and Validation
**Story Points**: 3
**Priority**: High
**Dependencies**: Story 19.2, Story 19.3

**Description**:
Create comprehensive test suite for SDK provider and validate with existing test infrastructure.

**Tasks**:
- Write unit tests for `OpenCodeSDKProvider`
- Create integration tests with real OpenCode server
- Add provider validation tests
- Verify all existing tests still pass
- Achieve >85% test coverage for new code
- Test edge cases and error conditions

**Acceptance Criteria**:
- Unit tests cover all public methods
- Integration test runs end-to-end with real server
- Provider validation tests pass
- All 400+ existing tests pass without modification
- Test coverage >85% for opencode_sdk.py
- Mock tests don't require running server

**Files Created**:
- `tests/core/providers/test_opencode_sdk.py`
- `tests/integration/test_opencode_sdk_integration.py`

**Testing**:
- `pytest tests/core/providers/test_opencode_sdk.py`
- `pytest tests/integration/test_opencode_sdk_integration.py`
- `pytest --cov=gao_dev.core.providers.opencode_sdk`

---

### Story 19.5: Provider Registration and Documentation
**Story Points**: 3
**Priority**: High
**Dependencies**: Story 19.2, Story 19.3, Story 19.4

**Description**:
Register SDK provider in factory, update configuration, and complete documentation.

**Tasks**:
- Register `opencode-sdk` provider in `ProviderFactory`
- Update `ProcessExecutor` to support `opencode-sdk` provider name
- Add `AGENT_PROVIDER=opencode-sdk` environment variable support
- Rename `OpenCodeProvider` → `OpenCodeCLIProvider` (deprecate)
- Update documentation (README, ARCHITECTURE, API docs)
- Create migration guide from CLI to SDK provider
- Run full benchmark test with SDK provider

**Acceptance Criteria**:
- `ProviderFactory` creates SDK provider for `opencode-sdk` name
- Environment variable `AGENT_PROVIDER=opencode-sdk` works
- CLI provider still accessible as `opencode-cli`
- Documentation clearly explains SDK vs CLI differences
- Migration guide helps users switch providers
- Benchmark completes successfully with SDK provider
- Zero errors or warnings during benchmark run

**Files Modified**:
- `gao_dev/core/providers/__init__.py`
- `gao_dev/core/providers/factory.py`
- `gao_dev/core/providers/opencode.py` (rename to opencode_cli.py)
- `gao_dev/core/services/process_executor.py`
- `docs/features/opencode-sdk-integration/ARCHITECTURE.md`
- `docs/features/opencode-sdk-integration/README.md`
- `.env` (example)

**Testing**:
- Provider factory test
- Environment variable test
- Full benchmark run
- Verify CLI provider still works

---

## Dependencies and Constraints

### External Dependencies
- **OpenCode CLI**: Must be installed and accessible
- **OpenCode SDK**: Pre-release version (0.1.0a36)
- **Anthropic API**: Valid API key required

### Technical Constraints
- Must maintain backward compatibility with `IAgentProvider`
- Server port must be configurable (default: 4096)
- Must work on Windows, Linux, and macOS

---

## Success Metrics

### Code Quality
- Type checking: 100% pass rate
- Test coverage: >85% for new code
- Lint errors: 0 (ruff)
- Documentation: Complete API docs

### Functional Metrics
- Task execution success rate: 100%
- Server startup time: <3 seconds
- Benchmark completion: 100% success
- Zero subprocess hanging issues

---

## Rollout Plan

### Phase 1: Implementation (Days 1-3)
- Stories 19.1-19.3
- Core functionality complete
- Basic testing done

### Phase 2: Testing (Day 4)
- Story 19.4
- Comprehensive test coverage
- Bug fixes

### Phase 3: Integration (Day 5)
- Story 19.5
- Full system integration
- Benchmark validation
- Documentation complete

---

## Risk Management

| Risk | Mitigation |
|------|------------|
| SDK API breaking changes | Pin SDK version, monitor releases |
| Server startup failures | Retry logic, clear error messages, fallback to CLI |
| Port conflicts | Configurable port, random port selection |
| Performance degradation | Benchmark comparison, optimize if needed |

---

## Related Work

- **Epic 11**: Agent Provider Abstraction (Foundation)
- **Epic 12**: Document Lifecycle System (Parallel work)
- **OpenCode CLI Provider**: Original implementation (deprecated)

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-06 | GAO-Dev | Initial epic breakdown |
