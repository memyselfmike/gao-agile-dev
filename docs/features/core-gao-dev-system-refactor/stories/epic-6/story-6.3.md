# Story 6.3: Extract ProcessExecutor Service

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 3
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Ready

---

## Overview

Extract subprocess execution logic (Claude CLI calls) from `GAODevOrchestrator` into a dedicated `ProcessExecutor` service.

---

## User Story

**As a** GAO-Dev architect
**I want** subprocess execution logic isolated
**So that** process handling is testable and can be mocked

---

## Acceptance Criteria

1. **Service Created**
   - [ ] `gao_dev/core/services/process_executor.py` created
   - [ ] Class `ProcessExecutor` < 150 lines
   - [ ] Single responsibility: Execute subprocesses

2. **Functionality**
   - [ ] Executes Claude CLI via subprocess
   - [ ] Streams output to caller
   - [ ] Handles process timeouts
   - [ ] Captures exit codes and errors
   - [ ] Logs process execution details

3. **Testing**
   - [ ] Unit tests with process mocking
   - [ ] Timeout handling tests
   - [ ] Error capture tests
   - [ ] Output streaming tests

---

## Technical Details

```python
class ProcessExecutor:
    """Execute external processes (Claude CLI)."""

    async def execute_agent_task(
        self,
        agent: IAgent,
        task: str,
        context: AgentContext,
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task via Claude CLI.

        Yields: Output lines from process
        Raises: ProcessExecutionError on failure
        """
        pass
```

---

## Implementation Steps

1. Create service file
2. Extract subprocess logic from orchestrator
3. Add timeout handling
4. Add error handling
5. Write tests with mock processes
6. Update orchestrator to use service

---

## Definition of Done

- [ ] ProcessExecutor created (< 150 lines)
- [ ] All acceptance criteria met
- [ ] Unit tests (80%+ coverage)
- [ ] Orchestrator updated
- [ ] Tests pass

---

**Related Stories**: 6.1, 6.2, 6.5
**Estimated Time**: Half day
