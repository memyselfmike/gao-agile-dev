# Story 7.4: Update Metrics Collection

**Epic**: Epic 7 - Autonomous Artifact Creation & Git Integration
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-28

---

## User Story

**As a** benchmark system
**I want** to collect metrics around GAO-Dev command execution
**So that** I can measure performance, cost, and artifact creation

---

## Context

After Stories 7.1-7.3, we're using GAODevOrchestrator and creating artifacts with git commits. Now we need to ensure metrics are collected around these operations.

---

## Acceptance Criteria

### AC1: Command Execution Metrics
- [ ] Duration per command (create-prd, implement-story, etc.)
- [ ] Token usage per command
- [ ] API cost per command
- [ ] Success/failure status

### AC2: Artifact Metrics
- [ ] Number of artifacts created per command
- [ ] Total file size of artifacts
- [ ] File types created (py, ts, md, etc.)
- [ ] Lines of code generated

### AC3: Git Metrics
- [ ] Commit SHAs recorded
- [ ] Commit timestamps
- [ ] Number of commits per phase
- [ ] Files changed per commit

### AC4: Integration with Existing Metrics System
- [ ] Uses existing MetricsCollector
- [ ] Stores in existing database schema
- [ ] Links to benchmark run ID
- [ ] Queryable for reports

---

## Technical Details

### Metrics Wrapper

```python
class CommandMetricsCollector:
    """Collect metrics around GAODevOrchestrator command execution."""

    def __init__(self, metrics_collector: MetricsCollector, run_id: str):
        self.metrics = metrics_collector
        self.run_id = run_id

    async def execute_with_metrics(
        self,
        orchestrator: GAODevOrchestrator,
        command: str,
        **kwargs
    ) -> CommandResult:
        """Execute command and collect metrics."""

        start_time = time.time()
        start_tokens = self._get_current_token_count()

        try:
            result = await orchestrator.execute_command(command, **kwargs)

            # Collect metrics
            duration = time.time() - start_time
            tokens_used = result.tokens_used or 0
            cost = self._calculate_cost(tokens_used)

            # Record metrics
            self.metrics.record_command_execution(
                run_id=self.run_id,
                command=command,
                duration=duration,
                tokens_used=tokens_used,
                cost=cost,
                success=result.success,
                artifacts_created=len(result.artifacts),
                commit_sha=result.commit_sha
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_command_failure(
                run_id=self.run_id,
                command=command,
                duration=duration,
                error=str(e)
            )
            raise
```

---

## Files to Modify

**Modify**:
- `gao_dev/sandbox/metrics/collector.py` - Add command metrics methods
- `gao_dev/sandbox/metrics/models.py` - Add CommandMetrics model
- `gao_dev/sandbox/benchmark/orchestrator.py` - Wrap commands with metrics
- `tests/sandbox/metrics/test_collector.py` - Add tests

---

## Dependencies

**Requires**:
- Story 7.1 (GAODevOrchestrator) - complete
- Story 7.2 (ArtifactParser) - complete
- Story 7.3 (Git Commits) - complete
- Existing metrics system from Epic 3

**Blocks**:
- None (can be done in parallel with 7.5)

---

## Implementation Steps

1. **Extend MetricsCollector**
   - Add command execution metrics
   - Add artifact metrics
   - Add git metrics

2. **Create Metrics Wrapper**
   - Wrap orchestrator calls
   - Record start/end times
   - Extract token usage
   - Calculate costs

3. **Update Database Schema** (if needed)
   - Add command_metrics table
   - Foreign key to benchmark_run
   - Indexes for queries

4. **Integrate with BenchmarkRunner**
   - Use wrapper for all commands
   - Pass metrics collector
   - Link to run ID

5. **Write Tests**
   - Unit tests for wrapper
   - Integration tests with real metrics
   - Validate data in database

---

## Definition of Done

- [ ] Command metrics collected
- [ ] Artifact metrics tracked
- [ ] Git commit info recorded
- [ ] Integration with orchestrator complete
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Committed with atomic commit

---

**Created by**: Bob (Scrum Master)
**Estimated Completion**: 1-2 hours
