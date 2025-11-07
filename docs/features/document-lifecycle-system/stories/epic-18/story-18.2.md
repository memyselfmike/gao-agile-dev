# Story 18.2: Artifact Detection System

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Story Points:** 8
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement a filesystem-based artifact detection system that captures snapshots of the project filesystem before and after workflow execution, then compares them to detect all files that were created or modified during the workflow. This enables automatic tracking of workflow outputs without requiring the LLM or workflow to explicitly declare what files they created. The system focuses on tracked directories (docs/, src/, gao_dev/) and ignores build artifacts and dependencies.

---

## Business Value

This story enables automatic artifact tracking:

- **Zero Configuration**: No need for workflows to declare outputs explicitly
- **Complete Coverage**: Detects all created/modified files automatically
- **Documentation Tracking**: All documentation artifacts tracked for lifecycle management
- **Code Tracking**: Source code changes detected and registered
- **Audit Trail**: Complete record of what each workflow produced
- **Quality Assurance**: Can verify workflows create expected artifacts
- **Performance Analysis**: Understand workflow productivity (files per hour)
- **Debugging Aid**: See exactly what files changed during execution
- **Foundation for Registration**: Detected artifacts fed to Story 18.3
- **Compliance Ready**: Full audit trail of artifact creation

---

## Acceptance Criteria

### Filesystem Snapshotting
- [ ] `_snapshot_project_files()` returns set of (path, mtime, size) tuples
- [ ] Snapshot includes all files in tracked directories (docs/, src/, gao_dev/)
- [ ] Snapshot excludes files in ignored directories (.git/, node_modules/, __pycache__/, .gao-dev/, .archive/)
- [ ] Snapshot handles filesystem errors gracefully (log warning, skip file)
- [ ] Snapshot uses relative paths (relative to project root)
- [ ] Snapshot performance: <50ms for typical project (<1000 files)

### Artifact Detection
- [ ] New files detected correctly (in after but not in before)
- [ ] Modified files detected correctly (same path, different mtime or size)
- [ ] Deleted files NOT flagged as artifacts (ignore deletions)
- [ ] Files outside project root ignored
- [ ] Empty directories ignored (files only)
- [ ] Artifact list returned as List[Path] (relative to project root)

### Execution Integration
- [ ] Snapshot taken immediately before workflow execution
- [ ] Snapshot taken immediately after workflow execution
- [ ] `_detect_artifacts()` called with before/after snapshots
- [ ] Detected artifacts passed to next step (Story 18.3)

### Logging & Observability
- [ ] Logs show `workflow_artifacts_detected` with count and list
- [ ] Logs show artifact paths (relative to project root)
- [ ] Logs show artifact detection timing
- [ ] Filesystem errors logged as warnings (don't fail workflow)

### Testing
- [ ] Unit tests verify snapshot logic with mock filesystem
- [ ] Unit tests verify new file detection
- [ ] Unit tests verify modified file detection
- [ ] Unit tests verify ignored directories excluded
- [ ] Integration test: Workflow artifacts detected correctly
- [ ] Performance test: Snapshot overhead <100ms for 1000 files

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/orchestrator/orchestrator.py`

**Add two new helper methods:**

```python
def _snapshot_project_files(self) -> set:
    """
    Snapshot current project files for artifact detection.

    Returns:
        Set of (path, mtime, size) tuples for all tracked files
    """
    snapshot = set()

    # Only track docs/, src/, and gao_dev/ directories
    tracked_dirs = [
        self.project_root / "docs",
        self.project_root / "src",
        self.project_root / "gao_dev",  # For internal development
    ]

    # Directories to ignore
    ignored_dirs = {".git", "node_modules", "__pycache__", ".gao-dev", ".archive", "venv", ".venv"}

    for tracked_dir in tracked_dirs:
        if not tracked_dir.exists():
            continue

        for file_path in tracked_dir.rglob("*"):
            # Skip if any parent directory is in ignored_dirs
            if any(part in ignored_dirs for part in file_path.parts):
                continue

            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    rel_path = str(file_path.relative_to(self.project_root))
                    snapshot.add((rel_path, stat.st_mtime, stat.st_size))
                except (OSError, ValueError) as e:
                    # Log warning but continue
                    logger.warning(
                        "snapshot_file_error",
                        file=str(file_path),
                        error=str(e),
                        message="Skipping file in snapshot"
                    )
                    pass

    return snapshot

def _detect_artifacts(self, before: set, after: set) -> List[Path]:
    """
    Detect artifacts created or modified during workflow execution.

    Args:
        before: Filesystem snapshot before execution
        after: Filesystem snapshot after execution

    Returns:
        List of artifact paths (relative to project root)
    """
    # New or modified files: in after but not in before
    # (different mtime or size means modified)
    all_artifacts = after - before

    # Convert tuples back to Path objects
    artifact_paths = [self.project_root / item[0] for item in all_artifacts]

    logger.info(
        "workflow_artifacts_detected",
        artifacts_count=len(artifact_paths),
        artifacts=[str(p.relative_to(self.project_root)) for p in artifact_paths]
    )

    return artifact_paths
```

**Integrate into `_execute_agent_task_static()`:**

```python
async def _execute_agent_task_static(
    self, workflow_info: "WorkflowInfo", epic: int = 1, story: int = 1
) -> AsyncGenerator[str, None]:
    # ... existing variable resolution code from Story 18.1 ...

    # STEP 5: Snapshot filesystem before execution
    files_before = self._snapshot_project_files()

    logger.debug(
        "filesystem_snapshot_before",
        workflow=workflow_info.name,
        files_count=len(files_before)
    )

    # STEP 6: Execute via ProcessExecutor
    execution_output = []
    async for output in self.process_executor.execute_agent_task(
        task=task_prompt,
        tools=["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob", "TodoWrite"],
        timeout=None
    ):
        execution_output.append(output)
        yield output

    # STEP 7: Snapshot filesystem after execution
    files_after = self._snapshot_project_files()

    logger.debug(
        "filesystem_snapshot_after",
        workflow=workflow_info.name,
        files_count=len(files_after)
    )

    # STEP 8: Detect artifacts created during execution
    artifacts = self._detect_artifacts(files_before, files_after)

    # NOTE: Story 18.3 will add artifact registration here
```

---

## Dependencies

- Story 18.1 (WorkflowExecutor Integration) - Must resolve variables first
- pathlib.Path for file operations
- os.stat for file metadata

---

## Tasks

### Implementation Tasks
- [ ] Implement _snapshot_project_files() method
- [ ] Define tracked directories list (docs/, src/, gao_dev/)
- [ ] Define ignored directories set (.git, node_modules, etc.)
- [ ] Implement recursive file scanning with rglob
- [ ] Capture file metadata (path, mtime, size)
- [ ] Handle filesystem errors gracefully
- [ ] Implement _detect_artifacts() method
- [ ] Calculate set difference (after - before)
- [ ] Convert tuples back to Path objects
- [ ] Add comprehensive logging
- [ ] Integrate snapshot calls into _execute_agent_task_static()
- [ ] Take snapshot before execution
- [ ] Take snapshot after execution
- [ ] Call _detect_artifacts() with snapshots

### Testing Tasks
- [ ] Write unit test: test_snapshot_project_files_basic()
- [ ] Write unit test: test_snapshot_excludes_ignored_dirs()
- [ ] Write unit test: test_snapshot_handles_missing_dirs()
- [ ] Write unit test: test_snapshot_handles_filesystem_errors()
- [ ] Write unit test: test_detect_artifacts_new_files()
- [ ] Write unit test: test_detect_artifacts_modified_files()
- [ ] Write unit test: test_detect_artifacts_deleted_files_ignored()
- [ ] Write unit test: test_detect_artifacts_empty_diff()
- [ ] Write integration test: test_workflow_artifacts_detected_e2e()
- [ ] Write performance test: test_snapshot_performance_1000_files()

### Documentation Tasks
- [ ] Document snapshot mechanism in method docstrings
- [ ] Document tracked vs. ignored directories
- [ ] Document artifact detection logic
- [ ] Add logging examples to troubleshooting guide

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] All tasks completed
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Performance tests pass (snapshot <100ms)
- [ ] Code review approved
- [ ] Logging implemented and verified
- [ ] Documentation updated
- [ ] Manual testing with multiple workflows successful
- [ ] Merged to feature branch

---

## Files to Modify

1. `gao_dev/orchestrator/orchestrator.py` (~100 LOC additions)
   - Add _snapshot_project_files() method (~40 LOC)
   - Add _detect_artifacts() method (~20 LOC)
   - Integrate into _execute_agent_task_static() (~20 LOC)
   - Add logging (~20 LOC)

2. `tests/orchestrator/test_artifact_detection.py` (new file, ~150 LOC)
   - Unit tests for snapshot logic
   - Unit tests for artifact detection
   - Performance tests

3. `tests/integration/test_workflow_artifact_tracking.py` (new file, ~100 LOC)
   - Integration tests for end-to-end artifact detection

---

## Success Metrics

- **Detection Accuracy**: >95% of created/modified files detected
- **Performance**: Snapshot overhead <50ms for typical projects
- **False Positives**: <1% false positive rate (files incorrectly flagged)
- **False Negatives**: 0% false negative rate (files missed)
- **Test Coverage**: >80% coverage for artifact detection code
- **Reliability**: No crashes due to filesystem errors

---

## Risk Assessment

**Risks:**
- Performance degradation from filesystem scanning
- Race conditions if LLM modifies files during snapshot
- Large projects (10,000+ files) might be slow
- Symbolic links could cause issues

**Mitigations:**
- Benchmark performance on various project sizes
- Add small delay (100ms) before post-execution snapshot
- Implement timeout for snapshot operation
- Skip symlinks or handle carefully
- Cache directory listings where possible

---

## Notes

- Snapshot timing is critical - take post-snapshot immediately after execution completes
- Consider adding configurable delay before post-snapshot for file system sync
- Track both new and modified files (both are "artifacts")
- Don't track deleted files as artifacts (deletions are not outputs)
- Performance acceptable if <5% of total workflow execution time
- Consider adding metrics for artifact detection (count, size, types)

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
**Author:** Bob (Scrum Master)
