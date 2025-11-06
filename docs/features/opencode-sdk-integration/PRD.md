# Product Requirements Document: OpenCode SDK Integration

**Version**: 1.0.0
**Date**: 2025-11-06
**Status**: Draft
**Epic**: 19
**Owner**: GAO-Dev Team

---

## Executive Summary

### Problem
The current OpenCode CLI provider experiences subprocess hanging issues during task execution, blocking benchmark completion and preventing reliable multi-provider support. OpenCode was designed with a client-server architecture and Python SDK, making CLI subprocess execution suboptimal.

### Solution
Implement `OpenCodeSDKProvider` using the `opencode-ai` Python SDK to directly interact with OpenCode's HTTP API, eliminating subprocess issues and enabling reliable execution.

### Business Value
- **Reliability**: Eliminate hanging issues affecting benchmarks
- **Performance**: Direct API access faster than CLI subprocess
- **Maintainability**: Cleaner code using native SDK patterns
- **Extensibility**: Enable future OpenCode features (streaming, agents, tools)

---

## Background

### Current State (OpenCodeProvider - CLI-based)
- Uses subprocess to call `opencode run` CLI command
- Passes task via command argument with `--format json`
- Hangs during model fetching from Anthropic API
- Successfully validated: CLI works manually, fails in subprocess

### Discovery (Session Investigation)
- ✅ OpenCode Python SDK (`opencode-ai`) exists and works
- ✅ Successfully tested: Session creation + chat API
- ✅ Server mode: `opencode serve --port 4096`
- ✅ Response format: Structured parts (text, tools, costs, tokens)

---

## Goals and Objectives

### Primary Goals
1. **Eliminate Hanging**: Achieve reliable task execution without subprocess blocks
2. **SDK Integration**: Properly integrate `opencode-ai` SDK with provider interface
3. **Server Management**: Implement robust server lifecycle management
4. **Backward Compatibility**: Maintain provider abstraction interface

### Success Metrics
- Benchmark completion rate: 100% (vs current 0%)
- Task execution reliability: 100%
- Server startup time: <3 seconds
- Zero subprocess-related errors

---

## Stakeholders

### Primary
- **Development Team**: Needs reliable multi-provider support
- **Benchmark System**: Requires successful autonomous execution
- **Users**: Benefit from provider flexibility

### Secondary
- **OpenCode Community**: Validates SDK usage patterns
- **Plugin Developers**: Reference implementation for custom providers

---

## Requirements

### Functional Requirements

#### FR1: SDK Provider Implementation
- **FR1.1**: Implement `OpenCodeSDKProvider` class conforming to `IAgentProvider`
- **FR1.2**: Support all standard provider methods (execute_task, validate_configuration)
- **FR1.3**: Handle session creation and management
- **FR1.4**: Parse SDK responses and extract text output

#### FR2: Server Lifecycle Management
- **FR2.1**: Start OpenCode server on provider initialization
- **FR2.2**: Perform health checks before execution
- **FR2.3**: Gracefully shut down server on cleanup
- **FR2.4**: Handle server errors and restart if needed

#### FR3: Model Translation
- **FR3.1**: Translate canonical model names to OpenCode format
- **FR3.2**: Support provider_id + model_id parameter format
- **FR3.3**: Validate model support before execution

#### FR4: Configuration
- **FR4.1**: Read configuration from environment and config files
- **FR4.2**: Support configurable server port (default: 4096)
- **FR4.3**: Validate API key availability
- **FR4.4**: Provide clear error messages for configuration issues

### Non-Functional Requirements

#### NFR1: Reliability
- Zero subprocess hanging issues
- Automatic error recovery where possible
- Clear error messages for failures

#### NFR2: Performance
- Server startup: <3 seconds
- Task execution overhead: <500ms
- Memory usage: <100MB for server

#### NFR3: Maintainability
- Follow existing provider patterns
- Comprehensive logging with structlog
- Type hints throughout (mypy strict mode)
- >85% test coverage

#### NFR4: Compatibility
- Works with existing provider factory
- Compatible with all workflow types
- Supports same models as CLI provider

---

## Technical Specifications

### Dependencies
```toml
[tool.poetry.dependencies]
opencode-ai = "^0.1.0a36"  # Pre-release SDK
```

### Provider Interface Implementation
```python
class OpenCodeSDKProvider(IAgentProvider):
    def __init__(
        self,
        server_url: Optional[str] = None,
        server_port: int = 4096,
        api_key: Optional[str] = None,
        auto_start_server: bool = True
    ):
        ...

    async def execute_task(...) -> AsyncGenerator[str, None]:
        # 1. Ensure server is running
        # 2. Create session
        # 3. Send chat message with task
        # 4. Parse and yield response parts
        # 5. Clean up session
        ...
```

### Server Management
- Start: `subprocess.Popen(['opencode', 'serve', '--port', str(port)])`
- Health: `GET http://localhost:4096/health`
- Stop: `process.terminate()` with timeout

### Session Flow
1. Create session: `client.session.create(extra_body={})`
2. Send chat: `client.session.chat(id, provider_id, model_id, parts)`
3. Parse response: Extract text from parts
4. Return: Yield text output

---

## User Stories

### Story 19.1: Add OpenCode SDK Dependency
**As a** developer
**I want** opencode-ai SDK added to project dependencies
**So that** I can use the SDK in the provider implementation

**Acceptance Criteria**:
- SDK added to pyproject.toml
- Installation works on Windows/Linux/Mac
- SDK imports successfully

### Story 19.2: Implement OpenCodeSDKProvider Core
**As a** GAO-Dev system
**I want** a working OpenCodeSDKProvider class
**So that** I can execute tasks via OpenCode SDK

**Acceptance Criteria**:
- Class implements IAgentProvider interface
- execute_task() method works end-to-end
- Model translation working
- Type checking passes

### Story 19.3: Server Lifecycle Management
**As a** provider
**I want** to manage OpenCode server lifecycle automatically
**So that** users don't need to manually start/stop servers

**Acceptance Criteria**:
- Server starts on initialization
- Health checks working
- Graceful shutdown on cleanup
- Error handling for server failures

### Story 19.4: Integration and Testing
**As a** developer
**I want** comprehensive tests for SDK provider
**So that** I can trust the implementation

**Acceptance Criteria**:
- Unit tests for all methods
- Integration test with real server
- >85% test coverage
- All existing tests still pass

### Story 19.5: Provider Registration and Documentation
**As a** user
**I want** to easily switch to OpenCode SDK provider
**So that** I can benefit from the reliability improvements

**Acceptance Criteria**:
- Provider registered in factory
- Environment variable support (AGENT_PROVIDER=opencode-sdk)
- Documentation updated
- Benchmark runs successfully

---

## Success Criteria

### Must Have
- ✅ SDK provider executes tasks without hanging
- ✅ Benchmark completes successfully
- ✅ All tests pass (400+ existing + new tests)
- ✅ Documentation complete

### Should Have
- ✅ Server auto-restart on failure
- ✅ Streaming support for long responses
- ✅ Cost and token tracking

### Nice to Have
- Session reuse for multi-step workflows
- Custom agent support
- Advanced OpenCode features (tools, modes)

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SDK API changes | High | Low | Pin SDK version, monitor releases |
| Server startup failures | High | Medium | Retry logic, clear error messages |
| Port conflicts | Medium | Medium | Configurable port, random port fallback |
| API key issues | High | Low | Validation on init, clear error messages |

---

## Timeline

**Epic Duration**: 1 week (5 stories)

**Phase 1** (Days 1-2): Core Implementation
- Story 19.1: Dependencies
- Story 19.2: SDK Provider Core

**Phase 2** (Days 3-4): Lifecycle & Testing
- Story 19.3: Server Management
- Story 19.4: Integration Tests

**Phase 3** (Day 5): Integration & Documentation
- Story 19.5: Registration & Docs
- Benchmark validation

---

## Appendix

### References
- OpenCode SDK: https://opencode.ai/docs/sdk/
- Python SDK: https://github.com/sst/opencode-sdk-python
- OpenCode Server: https://opencode.ai/docs/server/
- Provider Interface: `gao_dev/core/providers/base.py`

### Related Features
- Epic 11: Agent Provider Abstraction
- Epic 12: Document Lifecycle System

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-06 | GAO-Dev | Initial PRD creation |
