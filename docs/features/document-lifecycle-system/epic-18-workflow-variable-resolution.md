# Epic 18: Workflow Variable Resolution and Artifact Tracking

**Feature:** Document Lifecycle & Context Management
**Priority:** P0 (Critical - Fixes Core Workflow Execution Bug)
**Estimated Duration:** 2-3 weeks
**Story Points:** 35 points
**Dependencies:** Epic 10 (Prompt Abstraction), Epic 12 (Document Lifecycle), Epic 17 (Context Integration)

---

## Overview

The orchestrator currently bypasses `WorkflowExecutor`, causing workflow variables defined in `workflow.yaml` files to never be resolved before sending instructions to the LLM. This architectural flaw results in three critical failures:

**Problem**: Workflow variables are not resolved during execution:
- Variables like `{{prd_location}}`, `{{dev_story_location}}` remain as literal strings in LLM instructions
- Files are created in wrong locations (e.g., `PRD.md` in root instead of `docs/PRD.md`)
- No artifact detection occurs after workflow execution
- Created artifacts are never registered with `DocumentLifecycleManager`
- Project conventions are not enforced by design

**Current Broken Flow**:
```
[workflow.yaml defines: prd_location="docs/PRD.md"]
         ↓
[Orchestrator loads instructions.md RAW]  ← BYPASSES WorkflowExecutor
         ↓
[Only replaces hardcoded: {epic}, {story}, {{epic_num}}, {{story_num}}]
         ↓
[Sends "Path: {{prd_location}}" to LLM]  ← Variable NOT resolved!
         ↓
[LLM ignores variable, creates PRD.md in root]  ← Wrong location
         ↓
[No artifact detection or document registration]  ← Lost tracking
```

**Solution**: Integrate `WorkflowExecutor` into the orchestrator execution path to:
1. Resolve variables from `workflow.yaml` defaults, config, and parameters
2. Render instructions with resolved variables before sending to LLM
3. Detect artifacts created/modified during workflow execution
4. Register all artifacts with `DocumentLifecycleManager` automatically

**Target Fixed Flow**:
```
[workflow.yaml: variables + defaults]
         ↓
[WorkflowExecutor.resolve_variables()]  ← Resolve from workflow.yaml, params, config
         ↓
[WorkflowExecutor.render_instructions()]  ← Render {{variable}} → actual values
         ↓
[Orchestrator sends RESOLVED instructions to LLM]  ← All variables replaced
         ↓
[LLM creates files at correct locations]
         ↓
[Post-execution artifact detector]  ← NEW: Detect created/modified files
         ↓
[DocumentLifecycleManager.register_document()]  ← NEW: Track all artifacts
```

---

## Success Criteria

- ✅ All workflow variables ({{prd_location}}, {{dev_story_location}}, etc.) resolved before sending to LLM
- ✅ LLM receives instructions with all variables replaced with actual values
- ✅ Files created at locations defined in workflow.yaml defaults
- ✅ All created/modified files detected after workflow execution
- ✅ All artifacts registered with DocumentLifecycleManager
- ✅ Document types correctly inferred from workflow and path
- ✅ No regression in existing tests or benchmarks
- ✅ Performance overhead <5% for artifact detection
- ✅ Comprehensive logging for observability

---

## Epic Breakdown

### Story 18.1: WorkflowExecutor Integration
**Points:** 8 | **Priority:** P0

**Goal**: Integrate WorkflowExecutor into orchestrator for proper variable resolution

**Problem**: Orchestrator directly loads `instructions.md` and sends it raw to LLM without resolving workflow variables. The existing `WorkflowExecutor` has variable resolution logic but is only used by CLI commands, not the main orchestrator execution path.

**Tasks**:
- Add `WorkflowExecutor` instance to `GAODevOrchestrator.__init__()`
- Add `WorkflowExecutor` initialization in `_initialize_default_services()`
- Refactor `_execute_agent_task_static()` to use WorkflowExecutor
- Build parameters dict (epic, story, project_name, project_root) for variable resolution
- Call `workflow_executor.resolve_variables()` to resolve all variables
- Call `workflow_executor.render_template()` to render instructions with resolved variables
- Make `_resolve_variables()` and `_render_template()` public methods in WorkflowExecutor
- Add comprehensive logging: `workflow_variables_resolved`, `workflow_instructions_rendered`
- Update WorkflowCoordinator to accept optional `workflow_executor` parameter
- Update orchestrator factory methods to pass WorkflowExecutor instance

**Acceptance Criteria**:
- [ ] Orchestrator has `WorkflowExecutor` instance initialized
- [ ] `_execute_agent_task_static()` calls `resolve_variables()` before execution
- [ ] Parameters dict includes epic, story, project_name, project_root
- [ ] All workflow variables resolved from workflow.yaml, config, and defaults
- [ ] Instructions template rendered with resolved variables
- [ ] LLM receives fully resolved instructions (no {{variables}} remain)
- [ ] Logs show `workflow_variables_resolved` with variable list
- [ ] Logs show `workflow_instructions_rendered` with prompt length
- [ ] Unit tests verify variable resolution from workflow.yaml defaults
- [ ] Unit tests verify parameter override of defaults
- [ ] Integration test: PRD workflow creates file at correct location (docs/PRD.md)
- [ ] Integration test: Story workflow uses resolved dev_story_location
- [ ] No regression in existing orchestrator tests

**Files to Modify**:
- `gao_dev/orchestrator/orchestrator.py` (~150 LOC changes in `_execute_agent_task_static()`, `__init__`, `_initialize_default_services`)
- `gao_dev/core/workflow_executor.py` (~20 LOC additions to expose public methods)
- `gao_dev/core/services/workflow_coordinator.py` (~10 LOC to add optional executor param)

**Technical Details**:
```python
# In orchestrator._execute_agent_task_static():
# STEP 1: Build parameters
params = {
    "epic_num": epic,
    "story_num": story,
    "epic": epic,
    "story": story,
    "project_name": self.project_root.name,
    "project_root": str(self.project_root),
}

# STEP 2: Resolve variables
variables = self.workflow_executor.resolve_variables(workflow_info, params)

# STEP 3: Load instructions
task_prompt = instructions_file.read_text(encoding="utf-8")

# STEP 4: Render with resolved variables
task_prompt = self.workflow_executor.render_template(task_prompt, variables)
```

---

### Story 18.2: Artifact Detection System
**Points:** 8 | **Priority:** P0

**Goal**: Detect files created or modified during workflow execution

**Problem**: After a workflow executes, we have no way to know what files were created or modified. This prevents us from tracking artifacts and registering them with the document lifecycle system.

**Tasks**:
- Implement `_snapshot_project_files()` to capture filesystem state
- Snapshot includes (path, mtime, size) tuples for all tracked files
- Track only relevant directories: `docs/`, `src/`, `gao_dev/`
- Ignore directories: `.git/`, `node_modules/`, `__pycache__/`, `.gao-dev/`, `.archive/`
- Implement `_detect_artifacts()` to compare before/after snapshots
- Detect new files (in after but not in before)
- Detect modified files (same path, different mtime or size)
- Take filesystem snapshot before workflow execution
- Take filesystem snapshot after workflow execution
- Call `_detect_artifacts()` to find created/modified files
- Add comprehensive logging: `workflow_artifacts_detected` with artifact list
- Handle filesystem errors gracefully (skip inaccessible files)

**Acceptance Criteria**:
- [ ] `_snapshot_project_files()` returns set of (path, mtime, size) tuples
- [ ] Snapshot includes all files in tracked directories
- [ ] Snapshot excludes files in ignored directories
- [ ] New files detected correctly (in after, not in before)
- [ ] Modified files detected correctly (different mtime or size)
- [ ] Files outside project root ignored
- [ ] Snapshot before execution captured
- [ ] Snapshot after execution captured
- [ ] Artifact list returned as List[Path] (relative to project root)
- [ ] Logs show `workflow_artifacts_detected` with count and list
- [ ] Filesystem errors handled gracefully (logged, not raised)
- [ ] Unit tests verify snapshot logic with mock filesystem
- [ ] Unit tests verify new file detection
- [ ] Unit tests verify modified file detection
- [ ] Integration test: Workflow artifacts detected correctly
- [ ] Performance: Snapshot overhead <100ms for typical project

**Files to Modify**:
- `gao_dev/orchestrator/orchestrator.py` (~100 LOC additions for snapshot and detection methods)

**Technical Details**:
```python
def _snapshot_project_files(self) -> set:
    """Snapshot current project files for artifact detection."""
    snapshot = set()
    tracked_dirs = [
        self.project_root / "docs",
        self.project_root / "src",
        self.project_root / "gao_dev",
    ]
    for tracked_dir in tracked_dirs:
        if not tracked_dir.exists():
            continue
        for file_path in tracked_dir.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    rel_path = str(file_path.relative_to(self.project_root))
                    snapshot.add((rel_path, stat.st_mtime, stat.st_size))
                except (OSError, ValueError):
                    pass
    return snapshot

def _detect_artifacts(self, before: set, after: set) -> List[Path]:
    """Detect artifacts created or modified during execution."""
    # New files: in after but not before
    # Modified files: same path but different mtime/size
    all_artifacts = (after - before)
    return [self.project_root / item[0] for item in all_artifacts]
```

---

### Story 18.3: Document Lifecycle Integration
**Points:** 8 | **Priority:** P0

**Goal**: Register detected artifacts with DocumentLifecycleManager

**Problem**: Even if we detect artifacts, they're useless unless registered with the document lifecycle system. We need to infer document types, determine authors, and register with proper metadata.

**Tasks**:
- Implement `_register_artifacts()` to register with DocumentLifecycleManager
- Implement `_infer_document_type()` to map artifacts to document types
- Map based on workflow name (prd → product-requirements, architecture → architecture)
- Map based on file path (contains "prd" → product-requirements, "story" → story)
- Determine author from workflow using `_get_agent_for_workflow()`
- Build metadata dict with workflow, epic, story, phase, variables
- Call `doc_lifecycle.register_document()` for each artifact
- Handle registration failures gracefully (log warning, continue execution)
- Support all document types: product-requirements, architecture, technical-specification, epic, story, design, test-plan, document
- Add comprehensive logging: `artifact_registered` for each successful registration
- Add warning logs: `artifact_registration_failed` for failures

**Acceptance Criteria**:
- [ ] `_register_artifacts()` iterates through all detected artifacts
- [ ] `_infer_document_type()` returns correct type based on workflow name
- [ ] `_infer_document_type()` returns correct type based on file path
- [ ] Default document type is "document" if no match found
- [ ] Author inferred from workflow agent (john, winston, bob, amelia, etc.)
- [ ] Metadata includes workflow name, epic, story, phase, created_by_workflow flag
- [ ] Metadata includes resolved variables used in workflow
- [ ] DocumentLifecycleManager.register_document() called for each artifact
- [ ] Registration failures logged but don't break workflow execution
- [ ] Logs show `artifact_registered` with artifact path, type, doc_id, author
- [ ] Logs show `artifact_registration_failed` with error for failures
- [ ] Unit tests verify document type inference for all workflow types
- [ ] Unit tests verify author determination
- [ ] Unit tests verify metadata construction
- [ ] Integration test: PRD registered as product-requirements
- [ ] Integration test: Story registered as story with correct epic/story numbers
- [ ] Integration test: Artifacts appear in `.gao-dev/documents.db`
- [ ] Integration test: Query registered documents via DocumentLifecycleManager

**Files to Modify**:
- `gao_dev/orchestrator/orchestrator.py` (~80 LOC additions for registration methods)

**Technical Details**:
```python
def _register_artifacts(
    self,
    artifacts: List[Path],
    workflow_info: "WorkflowInfo",
    epic: int,
    story: int,
    variables: Dict[str, Any]
) -> None:
    """Register detected artifacts with DocumentLifecycleManager."""
    for artifact_path in artifacts:
        try:
            doc_type = self._infer_document_type(artifact_path, workflow_info)
            author = self._get_agent_for_workflow(workflow_info).lower()
            metadata = {
                "workflow": workflow_info.name,
                "epic": epic,
                "story": story,
                "phase": workflow_info.phase,
                "created_by_workflow": True,
                "variables": variables,
            }
            doc = self.doc_lifecycle.register_document(
                path=artifact_path,
                doc_type=doc_type,
                author=author,
                metadata=metadata
            )
            logger.info("artifact_registered", artifact=str(artifact_path), doc_id=doc.id)
        except Exception as e:
            logger.warning("artifact_registration_failed", artifact=str(artifact_path), error=str(e))

def _infer_document_type(self, path: Path, workflow_info: "WorkflowInfo") -> str:
    """Infer document type from path and workflow."""
    path_lower = str(path).lower()
    workflow_lower = workflow_info.name.lower()

    # Map based on workflow name first (more reliable)
    if "prd" in workflow_lower:
        return "product-requirements"
    elif "architecture" in workflow_lower:
        return "architecture"
    # ... more mappings ...

    # Fallback to path-based detection
    if "prd" in path_lower:
        return "product-requirements"
    # ... more mappings ...

    return "document"  # Default
```

---

### Story 18.4: Configuration Defaults
**Points:** 3 | **Priority:** P1

**Goal**: Add default workflow variable values in configuration system

**Problem**: Workflow variables need sensible defaults that match project conventions. These should be configurable but have good defaults.

**Tasks**:
- Create or update `gao_dev/config/defaults.yaml` with workflow_defaults section
- Add common workflow variables with default paths:
  - `prd_location: "docs/PRD.md"`
  - `architecture_location: "docs/ARCHITECTURE.md"`
  - `tech_spec_location: "docs/TECHNICAL_SPEC.md"`
  - `dev_story_location: "docs/stories"`
  - `epic_location: "docs/epics.md"`
  - `output_folder: "docs"`
- Update `ConfigLoader` to load workflow defaults section
- Make workflow defaults available via `config_loader.get_workflow_defaults()`
- Update `WorkflowExecutor._resolve_variables()` to use config defaults
- Document configuration options in YAML comments
- Add validation for path variables (must be strings)

**Acceptance Criteria**:
- [ ] `defaults.yaml` exists with `workflow_defaults` section
- [ ] All common workflow variables defined with sensible defaults
- [ ] Defaults match GAO-Dev project conventions (docs/ folder structure)
- [ ] ConfigLoader loads workflow_defaults section
- [ ] ConfigLoader provides `get_workflow_defaults()` method
- [ ] WorkflowExecutor uses config defaults when resolving variables
- [ ] YAML file has clear comments explaining each default
- [ ] Validation ensures path variables are strings
- [ ] Unit tests verify config loading
- [ ] Unit tests verify defaults used when variable not in params
- [ ] Documentation explains how to override defaults
- [ ] Integration test: Workflow uses config default when no param provided

**Files to Create/Modify**:
- `gao_dev/config/defaults.yaml` (create or update with workflow_defaults section)
- `gao_dev/core/config_loader.py` (add get_workflow_defaults() method, ~10 LOC)
- `gao_dev/core/workflow_executor.py` (update _resolve_variables() to use config, ~5 LOC)

**Technical Details**:
```yaml
# defaults.yaml
workflow_defaults:
  # Document locations follow GAO-Dev conventions
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"
  tech_spec_location: "docs/TECHNICAL_SPEC.md"
  dev_story_location: "docs/stories"
  epic_location: "docs/epics.md"
  output_folder: "docs"

document_lifecycle:
  archive_dir: ".archive"
  auto_register: true
```

---

### Story 18.5: Comprehensive Testing
**Points:** 5 | **Priority:** P0

**Goal**: Add comprehensive unit and integration tests for all new functionality

**Problem**: This is a critical architectural change affecting core workflow execution. We need extensive testing to ensure correctness and prevent regressions.

**Tasks**:
- Create `tests/core/test_workflow_executor_variables.py`
  - Test variable resolution from workflow.yaml defaults
  - Test parameter override of defaults
  - Test config override of defaults
  - Test required variables raise error if missing
  - Test template rendering with variables
  - Test common variables (date, timestamp) added automatically
- Create `tests/orchestrator/test_artifact_detection.py`
  - Test filesystem snapshot creation
  - Test new file detection
  - Test modified file detection
  - Test ignored directories excluded
  - Test filesystem errors handled gracefully
- Create `tests/orchestrator/test_document_registration.py`
  - Test document type inference from workflow name
  - Test document type inference from file path
  - Test author determination from workflow
  - Test metadata construction
  - Test registration failure handling
- Create `tests/integration/test_workflow_artifact_tracking.py`
  - E2E test: PRD workflow creates file at correct location (docs/PRD.md)
  - E2E test: PRD registered with DocumentLifecycleManager
  - E2E test: Story workflow uses dev_story_location variable
  - E2E test: Story artifacts tracked in .gao-dev/documents.db
  - E2E test: Multiple artifacts registered correctly
- Run regression tests with existing benchmark suite
- Validate no breaking changes in existing tests

**Acceptance Criteria**:
- [ ] >80% test coverage for all new code
- [ ] All unit tests pass (workflow_executor, artifact_detection, document_registration)
- [ ] All integration tests pass (workflow_artifact_tracking)
- [ ] Test variable resolution priority: params > config > defaults
- [ ] Test template rendering replaces all {{variables}}
- [ ] Test filesystem snapshot includes all tracked files
- [ ] Test artifact detection finds new and modified files
- [ ] Test document type inference for all workflow types
- [ ] Test metadata includes all required fields
- [ ] E2E test verifies PRD created at docs/PRD.md (not root)
- [ ] E2E test verifies PRD registered in documents.db
- [ ] E2E test verifies story artifacts tracked correctly
- [ ] Regression tests show no breaking changes
- [ ] Benchmark suite runs successfully (workflow-driven-todo.yaml)
- [ ] All tests documented with clear docstrings

**Files to Create**:
- `tests/core/test_workflow_executor_variables.py` (~200 LOC)
- `tests/orchestrator/test_artifact_detection.py` (~150 LOC)
- `tests/orchestrator/test_document_registration.py` (~150 LOC)
- `tests/integration/test_workflow_artifact_tracking.py` (~200 LOC)

---

### Story 18.6: Documentation and Migration
**Points:** 3 | **Priority:** P1

**Goal**: Document architecture changes and provide migration guidance

**Problem**: This is a significant architectural change. Users, contributors, and future maintainers need clear documentation explaining how variable resolution works, how to use it, and how to migrate.

**Tasks**:
- Create `docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md`
  - Explain variable resolution flow (workflow.yaml → params → config → defaults)
  - Document template syntax ({{variable}} vs {variable})
  - Show examples of workflow.yaml with variables section
  - Explain artifact detection system
  - Show document lifecycle integration
  - Provide troubleshooting guide
- Create `docs/MIGRATION_GUIDE_EPIC_18.md`
  - Explain what changed and why
  - List breaking changes (variables now enforced)
  - Provide migration steps for existing workflows
  - Show before/after examples
  - Explain impact on existing code
- Update `CLAUDE.md`
  - Update architecture section with new variable resolution flow
  - Update orchestrator description with artifact tracking
  - Add section on workflow variable conventions
  - Update troubleshooting with variable resolution issues
- Update workflow authoring guide
  - Explain how to define variables in workflow.yaml
  - Document variable types and validation
  - Show best practices for variable naming
  - Explain default values and required flags
- Add logging guide
  - Document new log events (workflow_variables_resolved, workflow_artifacts_detected, etc.)
  - Explain how to troubleshoot variable resolution issues
  - Show log examples for debugging

**Acceptance Criteria**:
- [ ] VARIABLE_RESOLUTION.md explains complete variable resolution flow
- [ ] Documentation includes architecture diagram showing new flow
- [ ] Examples show workflow.yaml variable definitions
- [ ] Template syntax clearly documented ({{mustache}} style)
- [ ] Artifact detection system explained with examples
- [ ] Troubleshooting section covers common issues
- [ ] MIGRATION_GUIDE_EPIC_18.md lists all breaking changes
- [ ] Migration guide provides step-by-step migration instructions
- [ ] Before/after examples show impact of changes
- [ ] CLAUDE.md updated with new architecture
- [ ] Workflow authoring guide explains variable system
- [ ] Best practices documented for variable naming and defaults
- [ ] New log events documented with examples
- [ ] All documentation has working code examples
- [ ] Documentation reviewed and approved

**Files to Create**:
- `docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md` (new, ~400 LOC)
- `docs/MIGRATION_GUIDE_EPIC_18.md` (new, ~300 LOC)

**Files to Modify**:
- `CLAUDE.md` (update architecture section, ~50 LOC changes)
- `docs/workflow-authoring-guide.md` (add variables section if exists)

---

## Story Dependencies

```
Story 18.4 (Config Defaults)
         │
         ├─→ Story 18.1 (WorkflowExecutor Integration)
         │            │
         │            ├─→ Story 18.2 (Artifact Detection)
         │            │            │
         │            │            └─→ Story 18.3 (Document Lifecycle)
         │            │                         │
         │            └─────────────────────────┤
         │                                      │
         └─────────────────────→ Story 18.5 (Testing)
                                              │
                                              └─→ Story 18.6 (Documentation)
```

**Critical Path**: 18.4 → 18.1 → 18.2 → 18.3 → 18.5 → 18.6

**Parallel Work Possible**:
- Story 18.4 (Config) can start immediately
- Story 18.1 (Executor) depends on 18.4
- Story 18.2 (Artifacts) depends on 18.1
- Story 18.3 (Lifecycle) depends on 18.2
- Story 18.5 (Testing) can start after 18.1-18.3 complete, runs in parallel with 18.6
- Story 18.6 (Docs) can start after 18.3, runs in parallel with 18.5

---

## Recommended Sprint Breakdown

### Sprint 1 (Week 1): Foundation
- **Story 18.4**: Configuration Defaults (3 pts)
- **Story 18.1**: WorkflowExecutor Integration (8 pts)
- **Total: 11 points**
- **Goal**: Variable resolution working end-to-end

### Sprint 2 (Week 2): Artifact Tracking
- **Story 18.2**: Artifact Detection System (8 pts)
- **Story 18.3**: Document Lifecycle Integration (8 pts)
- **Total: 16 points**
- **Goal**: Artifacts detected and tracked

### Sprint 3 (Week 3): Validation & Documentation
- **Story 18.5**: Comprehensive Testing (5 pts)
- **Story 18.6**: Documentation and Migration (3 pts)
- **Total: 8 points**
- **Goal**: System validated and documented

---

## Total Effort Summary

| Story | Points | Duration | Priority | Dependencies |
|-------|--------|----------|----------|--------------|
| 18.1: WorkflowExecutor Integration | 8 | 1.5 weeks | P0 | 18.4 |
| 18.2: Artifact Detection | 8 | 1.5 weeks | P0 | 18.1 |
| 18.3: Document Lifecycle Integration | 8 | 1.5 weeks | P0 | 18.2 |
| 18.4: Configuration Defaults | 3 | 0.5 weeks | P1 | None |
| 18.5: Comprehensive Testing | 5 | 1 week | P0 | 18.1-18.3 |
| 18.6: Documentation | 3 | 0.5 weeks | P1 | 18.3 |
| **TOTAL** | **35 points** | **2-3 weeks** | - | - |

---

## Risks & Mitigations

### Risk 1: Breaking Changes to Existing Workflows
**Likelihood:** High | **Impact:** Critical

**Description**: Variables that were previously ignored will now be enforced. Workflows relying on LLM "guessing" locations will break.

**Mitigation**:
- Add defaults for all common variables in config
- Extensive regression testing with benchmark suite
- Clear migration guide with before/after examples
- Gradual rollout with feature flag
- Provide backward compatibility mode (disable variable enforcement)

### Risk 2: Performance Degradation from Filesystem Scanning
**Likelihood:** Medium | **Impact:** Medium

**Description**: Scanning entire project filesystem twice (before/after) could add significant overhead to workflow execution.

**Mitigation**:
- Limit scanning to tracked directories only (docs/, src/)
- Use efficient file scanning (avoid walking ignored directories)
- Implement caching for unchanged directory trees
- Performance tests validate <100ms overhead
- Profile and optimize hot paths

### Risk 3: Artifact Detection Misses Files
**Likelihood:** Low | **Impact:** High

**Description**: Race conditions or timing issues could cause artifact detection to miss files created by LLM.

**Mitigation**:
- Add small delay before post-execution snapshot (100ms)
- Use modification time AND file size for detection
- Log all detected artifacts for verification
- Integration tests validate artifact detection accuracy
- Manual verification in benchmark runs

### Risk 4: Document Type Inference Incorrect
**Likelihood:** Medium | **Impact:** Medium

**Description**: Heuristic-based document type inference might misclassify artifacts.

**Mitigation**:
- Use workflow name as primary signal (more reliable)
- Fall back to path-based detection
- Allow manual override via metadata
- Comprehensive test cases for all document types
- Add configuration to customize inference rules

### Risk 5: DocumentLifecycleManager Not Ready
**Likelihood:** Low | **Impact:** Critical

**Description**: Epic 12 DocumentLifecycleManager might not be production-ready or have API changes.

**Mitigation**:
- Verify Epic 12 status before starting Epic 18
- Review DocumentLifecycleManager API contract
- Add integration tests with DocumentLifecycleManager
- Handle registration failures gracefully (log, don't crash)
- Create mock DocumentLifecycleManager for testing

---

## Success Metrics

### Functional Metrics
- ✅ All workflow variables resolved correctly (100% of defined variables)
- ✅ Files created at locations defined in workflow.yaml (100% compliance)
- ✅ All created/modified files detected as artifacts (>95% detection rate)
- ✅ All artifacts registered with DocumentLifecycleManager (>95% registration rate)
- ✅ Document types inferred correctly (>90% accuracy)
- ✅ No regression in existing tests (100% passing)
- ✅ Benchmark suite runs successfully (all benchmarks pass)

### Performance Metrics
- ✅ Variable resolution overhead <10ms (p95)
- ✅ Filesystem snapshot overhead <50ms (p95)
- ✅ Artifact detection overhead <100ms (p95)
- ✅ Total workflow overhead <5% of execution time
- ✅ No memory leaks in artifact detection
- ✅ Scales to projects with 1000+ files

### Quality Metrics
- ✅ >80% test coverage for new code
- ✅ Zero critical bugs in production
- ✅ All P0 stories complete
- ✅ Code review approved
- ✅ Documentation complete and accurate
- ✅ Migration guide validated with real workflows

### Observability Metrics
- ✅ All variable resolutions logged
- ✅ All artifact detections logged
- ✅ All document registrations logged
- ✅ Failures logged with context
- ✅ Performance metrics collected
- ✅ Troubleshooting guide effective

---

## Post-Epic 18 State

**What Will Work**:
1. ✅ All workflow variables resolved from workflow.yaml definitions
2. ✅ LLM receives instructions with fully resolved paths and values
3. ✅ Files created at correct locations matching project conventions
4. ✅ All workflow artifacts automatically detected after execution
5. ✅ All artifacts registered with DocumentLifecycleManager
6. ✅ Document types, authors, and metadata tracked correctly
7. ✅ Complete observability via structured logging
8. ✅ Configuration defaults enforce project conventions

**What Will Be Fixed**:
- ❌ **BEFORE**: Variables like {{prd_location}} sent raw to LLM
- ✅ **AFTER**: Variables resolved to actual paths (e.g., "docs/PRD.md")
- ❌ **BEFORE**: Files created in wrong locations (PRD.md in root)
- ✅ **AFTER**: Files created at correct locations (docs/PRD.md)
- ❌ **BEFORE**: No artifact tracking or document lifecycle integration
- ✅ **AFTER**: All artifacts tracked in .gao-dev/documents.db

**Production Ready**: **100%**
- ✅ Architecture fixed by design
- ✅ All variables resolved correctly
- ✅ All artifacts tracked automatically
- ✅ Comprehensive testing
- ✅ Full documentation
- ✅ Migration guide available

---

## Impact Analysis

### Components Affected
- **GAODevOrchestrator**: Major changes (~300 LOC added)
- **WorkflowExecutor**: Minor changes (expose public methods)
- **WorkflowCoordinator**: Minor changes (accept executor)
- **ConfigLoader**: Minor changes (load workflow defaults)
- **All Workflows**: Benefit from variable resolution
- **DocumentLifecycleManager**: Integration usage increases

### Backwards Compatibility
- **Breaking**: Variables now enforced (were ignored before)
- **Breaking**: Files must be created at resolved locations
- **Compatible**: Existing workflows without variables work unchanged
- **Compatible**: Default values maintain existing behavior where possible
- **Compatible**: CLI commands unchanged

### Testing Strategy
1. **Unit Tests**: Test each component in isolation
2. **Integration Tests**: Test end-to-end workflow execution
3. **Regression Tests**: Ensure existing functionality unchanged
4. **Performance Tests**: Validate overhead acceptable
5. **Manual Tests**: Run benchmarks and verify results

---

## Next Steps After Epic 18

After Epic 18, the workflow variable resolution system will be fully operational. This unblocks:

- **Epic 19**: Advanced Workflow Features (conditional variables, expressions)
- **Epic 20**: Workflow Templates System (reusable workflow fragments)
- **Epic 21**: Meta-Prompt Variable Integration (use workflow variables in meta-prompts)
- **Continuous Improvement**: Monitor variable usage patterns, optimize performance

---

**Epic Owner**: TBD
**Start Date**: TBD
**Target Completion**: 3 weeks from start
**Status**: PROPOSED

---

**Dependencies Summary**:
- **Requires**: Epic 10 (complete), Epic 12 (complete), Epic 17 (in progress)
- **Blocks**: Advanced workflow features, meta-prompt integration
- **Integrates With**: Orchestrator, WorkflowExecutor, DocumentLifecycleManager, ConfigLoader

---

**Notes**:
- This epic fixes a critical architectural flaw discovered during production testing
- Priority P0 because it affects core workflow execution correctness
- Should be prioritized before new feature development
- Requires careful testing due to impact on all workflows
- Migration guide critical for smooth rollout
