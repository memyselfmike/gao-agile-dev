# Story 18.5: Comprehensive Testing

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Add comprehensive unit and integration tests for all new functionality introduced in Epic 18 (variable resolution, artifact detection, and document registration). This is a critical architectural change affecting core workflow execution, requiring extensive testing to ensure correctness, prevent regressions, and validate performance. Tests must cover all code paths, edge cases, error conditions, and integration points with existing systems.

---

## Business Value

This story ensures system reliability and quality:

- **Regression Prevention**: Comprehensive tests catch breaking changes early
- **Confidence**: High test coverage gives confidence in critical code paths
- **Documentation**: Tests serve as executable documentation of behavior
- **Refactoring Safety**: Can refactor with confidence tests will catch issues
- **Edge Case Coverage**: Tests validate behavior in unusual scenarios
- **Performance Validation**: Tests ensure acceptable performance overhead
- **Integration Validation**: Tests verify correct interaction with other systems
- **Production Readiness**: High test coverage required for production deployment
- **Quality Gates**: >80% coverage enforces quality standards
- **Debugging Aid**: Tests help isolate issues and validate fixes

---

## Acceptance Criteria

### Test Coverage
- [ ] >80% test coverage for all new code
- [ ] All unit tests pass (workflow_executor, artifact_detection, document_registration)
- [ ] All integration tests pass (workflow_artifact_tracking)
- [ ] Test coverage measured and reported
- [ ] All edge cases covered by tests
- [ ] All error paths covered by tests

### Variable Resolution Tests
- [ ] Test variable resolution from workflow.yaml defaults
- [ ] Test parameter override of defaults
- [ ] Test config override of defaults
- [ ] Test variable resolution priority: params > workflow > config > common
- [ ] Test required variables raise ValueError if missing
- [ ] Test template rendering replaces all {{variables}}
- [ ] Test template rendering preserves markdown formatting
- [ ] Test nested variable references (up to 2 levels)
- [ ] Test common variables (date, timestamp) added automatically
- [ ] Test invalid variable names handled gracefully

### Artifact Detection Tests
- [ ] Test filesystem snapshot includes all tracked files
- [ ] Test snapshot excludes ignored directories
- [ ] Test snapshot handles missing directories
- [ ] Test snapshot handles filesystem errors gracefully
- [ ] Test new file detection (in after, not in before)
- [ ] Test modified file detection (different mtime or size)
- [ ] Test deleted files NOT flagged as artifacts
- [ ] Test empty diff returns empty artifact list
- [ ] Test artifact paths relative to project root
- [ ] Test snapshot performance <100ms for 1000 files

### Document Registration Tests
- [ ] Test document type inference from workflow name
- [ ] Test document type inference from file path
- [ ] Test document type default fallback
- [ ] Test author determination from workflow agent
- [ ] Test metadata construction with all required fields
- [ ] Test metadata includes resolved variables
- [ ] Test registration failure handling (log warning, continue)
- [ ] Test partial registration (some succeed, some fail)
- [ ] Test registration when DocumentLifecycleManager not available

### Integration Tests
- [ ] E2E test: PRD workflow creates file at docs/PRD.md (not root)
- [ ] E2E test: PRD registered with DocumentLifecycleManager
- [ ] E2E test: PRD has correct type (product-requirements)
- [ ] E2E test: Story workflow uses dev_story_location variable
- [ ] E2E test: Story artifacts tracked in .gao-dev/documents.db
- [ ] E2E test: Multiple artifacts registered correctly
- [ ] E2E test: Query registered documents via DocumentLifecycleManager
- [ ] E2E test: Variables resolved and used in execution

### Regression Tests
- [ ] All existing orchestrator tests still pass
- [ ] All existing workflow executor tests still pass
- [ ] Benchmark suite runs successfully (workflow-driven-todo.yaml)
- [ ] No performance regression (<5% overhead)
- [ ] No breaking changes in existing workflows

---

## Technical Notes

### Test File Structure

**File:** `tests/core/test_workflow_executor_variables.py` (new, ~200 LOC)

```python
"""
Unit tests for WorkflowExecutor variable resolution.

Tests cover:
- Variable resolution from workflow.yaml defaults
- Parameter override of defaults
- Config override of defaults
- Priority order (params > workflow > config)
- Required variable validation
- Template rendering
- Common variables
"""

import pytest
from pathlib import Path
from gao_dev.core.workflow_executor import WorkflowExecutor
from gao_dev.core.config_loader import ConfigLoader
from gao_dev.core.models.workflow import WorkflowInfo


class TestWorkflowVariableResolution:
    """Test variable resolution from multiple sources."""

    def test_resolve_variables_from_workflow_yaml_defaults(self):
        """Test variables resolved from workflow.yaml defaults."""
        workflow = WorkflowInfo(
            name="prd",
            variables={
                "prd_location": {"default": "docs/PRD.md"},
                "output_folder": {"default": "docs"}
            }
        )

        executor = WorkflowExecutor(config_loader=mock_config_loader)
        variables = executor.resolve_variables(workflow, params={})

        assert variables["prd_location"] == "docs/PRD.md"
        assert variables["output_folder"] == "docs"

    def test_resolve_variables_param_override(self):
        """Test parameters override workflow defaults."""
        workflow = WorkflowInfo(
            name="prd",
            variables={"prd_location": {"default": "docs/PRD.md"}}
        )

        executor = WorkflowExecutor(config_loader=mock_config_loader)
        params = {"prd_location": "custom/PRD.md"}
        variables = executor.resolve_variables(workflow, params)

        assert variables["prd_location"] == "custom/PRD.md"

    def test_resolve_variables_config_override(self):
        """Test config defaults override workflow defaults."""
        # Config provides: prd_location = "docs/PRD.md"
        # Workflow provides: prd_location = "custom/PRD.md"
        # Expected: params > config > workflow
        pass

    def test_resolve_variables_priority_order(self):
        """Test priority: params > workflow > config > common."""
        pass

    def test_required_variable_missing_raises_error(self):
        """Test required variable raises ValueError if missing."""
        workflow = WorkflowInfo(
            name="prd",
            variables={
                "prd_location": {"required": True}
            }
        )

        executor = WorkflowExecutor(config_loader=mock_config_loader)

        with pytest.raises(ValueError, match="Required variable 'prd_location' not provided"):
            executor.resolve_variables(workflow, params={})

    def test_common_variables_added_automatically(self):
        """Test common variables (date, timestamp) added automatically."""
        workflow = WorkflowInfo(name="prd", variables={})
        executor = WorkflowExecutor(config_loader=mock_config_loader)
        variables = executor.resolve_variables(workflow, params={})

        assert "date" in variables
        assert "timestamp" in variables
        assert "project_name" in variables


class TestTemplateRendering:
    """Test template rendering with variables."""

    def test_render_template_replaces_variables(self):
        """Test all {{variable}} placeholders replaced."""
        template = "Create PRD at {{prd_location}}"
        variables = {"prd_location": "docs/PRD.md"}

        executor = WorkflowExecutor(config_loader=mock_config_loader)
        rendered = executor.render_template(template, variables)

        assert rendered == "Create PRD at docs/PRD.md"
        assert "{{" not in rendered

    def test_render_template_preserves_markdown(self):
        """Test template rendering preserves markdown formatting."""
        template = "# Header\n\nCreate file at {{path}}\n\n- Item 1\n- Item 2"
        variables = {"path": "docs/file.md"}

        executor = WorkflowExecutor(config_loader=mock_config_loader)
        rendered = executor.render_template(template, variables)

        assert "# Header" in rendered
        assert "- Item 1" in rendered

    def test_render_template_nested_variables(self):
        """Test nested variable references work."""
        pass
```

**File:** `tests/orchestrator/test_artifact_detection.py` (new, ~150 LOC)

```python
"""
Unit tests for artifact detection system.

Tests cover:
- Filesystem snapshot creation
- New file detection
- Modified file detection
- Ignored directories excluded
- Filesystem error handling
"""

import pytest
from pathlib import Path
from gao_dev.orchestrator.orchestrator import GAODevOrchestrator


class TestFilesystemSnapshot:
    """Test filesystem snapshot functionality."""

    def test_snapshot_includes_tracked_files(self, orchestrator, tmp_path):
        """Test snapshot includes all files in tracked directories."""
        # Create test files
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "PRD.md").write_text("test")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("test")

        orchestrator.project_root = tmp_path
        snapshot = orchestrator._snapshot_project_files()

        assert any("docs/PRD.md" in item[0] for item in snapshot)
        assert any("src/main.py" in item[0] for item in snapshot)

    def test_snapshot_excludes_ignored_dirs(self, orchestrator, tmp_path):
        """Test snapshot excludes files in ignored directories."""
        # Create files in ignored directory
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("test")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.json").write_text("test")

        orchestrator.project_root = tmp_path
        snapshot = orchestrator._snapshot_project_files()

        assert not any(".git" in item[0] for item in snapshot)
        assert not any("node_modules" in item[0] for item in snapshot)

    def test_snapshot_handles_missing_dirs(self, orchestrator, tmp_path):
        """Test snapshot handles missing tracked directories."""
        # Don't create docs/ or src/ directories
        orchestrator.project_root = tmp_path
        snapshot = orchestrator._snapshot_project_files()

        # Should return empty set, not crash
        assert isinstance(snapshot, set)

    def test_snapshot_handles_filesystem_errors(self, orchestrator):
        """Test snapshot handles filesystem errors gracefully."""
        # Mock file that raises OSError on stat()
        pass


class TestArtifactDetection:
    """Test artifact detection logic."""

    def test_detect_new_files(self, orchestrator, tmp_path):
        """Test new files detected correctly."""
        orchestrator.project_root = tmp_path

        # Before: empty
        before = set()

        # After: one file added
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "PRD.md").write_text("test")
        after = orchestrator._snapshot_project_files()

        artifacts = orchestrator._detect_artifacts(before, after)

        assert len(artifacts) == 1
        assert artifacts[0].name == "PRD.md"

    def test_detect_modified_files(self, orchestrator, tmp_path):
        """Test modified files detected correctly."""
        orchestrator.project_root = tmp_path
        (tmp_path / "docs").mkdir()
        file_path = tmp_path / "docs" / "PRD.md"

        # Before: file exists
        file_path.write_text("original")
        before = orchestrator._snapshot_project_files()

        # After: file modified
        import time
        time.sleep(0.01)  # Ensure mtime changes
        file_path.write_text("modified")
        after = orchestrator._snapshot_project_files()

        artifacts = orchestrator._detect_artifacts(before, after)

        assert len(artifacts) == 1
        assert artifacts[0].name == "PRD.md"

    def test_deleted_files_not_flagged(self, orchestrator, tmp_path):
        """Test deleted files NOT flagged as artifacts."""
        orchestrator.project_root = tmp_path
        (tmp_path / "docs").mkdir()
        file_path = tmp_path / "docs" / "PRD.md"

        # Before: file exists
        file_path.write_text("test")
        before = orchestrator._snapshot_project_files()

        # After: file deleted
        file_path.unlink()
        after = orchestrator._snapshot_project_files()

        artifacts = orchestrator._detect_artifacts(before, after)

        # Deleted files should not appear in artifacts
        assert len(artifacts) == 0
```

**File:** `tests/orchestrator/test_document_registration.py` (new, ~150 LOC)

**File:** `tests/integration/test_workflow_artifact_tracking.py` (new, ~200 LOC)

```python
"""
Integration tests for workflow artifact tracking end-to-end.

Tests cover:
- PRD workflow creates file at correct location
- PRD registered with DocumentLifecycleManager
- Story workflow artifacts tracked
- Multiple artifacts registered
- Database queries work
"""

import pytest
from pathlib import Path
from gao_dev.orchestrator.orchestrator import GAODevOrchestrator


@pytest.mark.integration
class TestWorkflowArtifactTracking:
    """Integration tests for workflow artifact tracking."""

    async def test_prd_workflow_creates_file_at_correct_location(self, orchestrator):
        """Test PRD workflow creates file at docs/PRD.md (not root)."""
        workflow = orchestrator.workflow_registry.get_workflow("prd")

        # Execute workflow
        async for _ in orchestrator._execute_agent_task_static(workflow, epic=1, story=1):
            pass

        # Verify file created at correct location
        prd_path = orchestrator.project_root / "docs" / "PRD.md"
        assert prd_path.exists()

        # Verify file NOT created at wrong location
        wrong_path = orchestrator.project_root / "PRD.md"
        assert not wrong_path.exists()

    async def test_prd_registered_with_document_lifecycle(self, orchestrator):
        """Test PRD registered with DocumentLifecycleManager."""
        workflow = orchestrator.workflow_registry.get_workflow("prd")

        # Execute workflow
        async for _ in orchestrator._execute_agent_task_static(workflow, epic=1, story=1):
            pass

        # Query document lifecycle manager
        docs = orchestrator.doc_lifecycle.list_documents(doc_type="product-requirements")

        assert len(docs) >= 1
        prd_doc = docs[0]
        assert prd_doc.doc_type == "product-requirements"
        assert prd_doc.author == "john"
        assert prd_doc.metadata["workflow"] == "prd"
        assert prd_doc.metadata["created_by_workflow"] is True

    async def test_story_workflow_uses_dev_story_location(self, orchestrator):
        """Test story workflow uses resolved dev_story_location variable."""
        pass

    async def test_multiple_artifacts_registered(self, orchestrator):
        """Test workflow creating multiple files registers all."""
        pass
```

---

## Dependencies

- Stories 18.1, 18.2, 18.3 must be complete
- pytest, pytest-cov for testing
- mock/unittest.mock for mocking

---

## Tasks

### Implementation Tasks
- [ ] Create tests/core/test_workflow_executor_variables.py
- [ ] Create tests/orchestrator/test_artifact_detection.py
- [ ] Create tests/orchestrator/test_document_registration.py
- [ ] Create tests/integration/test_workflow_artifact_tracking.py
- [ ] Write all unit tests for variable resolution
- [ ] Write all unit tests for artifact detection
- [ ] Write all unit tests for document registration
- [ ] Write all integration tests for E2E workflows
- [ ] Add test fixtures and helpers
- [ ] Add mock objects for dependencies
- [ ] Configure pytest coverage reporting
- [ ] Run all tests and fix failures

### Testing Tasks
- [ ] Achieve >80% test coverage for new code
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All regression tests pass (existing tests)
- [ ] Performance tests validate <100ms overhead
- [ ] Benchmark suite runs successfully

### Documentation Tasks
- [ ] Add docstrings to all test classes and methods
- [ ] Document test strategy and coverage goals
- [ ] Add comments explaining complex test scenarios
- [ ] Document how to run tests
- [ ] Document how to measure coverage

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] All tasks completed
- [ ] >80% test coverage achieved and measured
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All regression tests pass
- [ ] Performance tests pass
- [ ] Code review approved
- [ ] Test documentation complete
- [ ] CI/CD integration configured (if applicable)
- [ ] Merged to feature branch

---

## Files to Create

1. `tests/core/test_workflow_executor_variables.py` (~200 LOC)
   - TestWorkflowVariableResolution class
   - TestTemplateRendering class
   - Test fixtures and helpers

2. `tests/orchestrator/test_artifact_detection.py` (~150 LOC)
   - TestFilesystemSnapshot class
   - TestArtifactDetection class
   - Mock filesystem helpers

3. `tests/orchestrator/test_document_registration.py` (~150 LOC)
   - TestDocumentTypeInference class
   - TestAuthorDetermination class
   - TestMetadataConstruction class
   - TestRegistrationErrorHandling class

4. `tests/integration/test_workflow_artifact_tracking.py` (~200 LOC)
   - TestWorkflowArtifactTracking class
   - E2E test scenarios
   - Database verification helpers

---

## Success Metrics

- **Test Coverage**: >80% coverage for all new code
- **Pass Rate**: 100% of tests pass
- **Regression Prevention**: 0 breaking changes to existing tests
- **Performance**: Tests run in <60 seconds total
- **Reliability**: Tests pass consistently (no flaky tests)
- **Documentation**: All tests have clear docstrings

---

## Risk Assessment

**Risks:**
- Test coverage might be difficult to achieve
- Integration tests might be flaky
- Performance tests might fail on slow machines
- Mock objects might not match real behavior

**Mitigations:**
- Use pytest-cov to measure coverage accurately
- Add retries for flaky integration tests
- Use relative performance thresholds (not absolute)
- Keep mocks simple and test with real objects too
- Add smoke tests for critical paths
- Document known test limitations

---

## Notes

- Tests are critical for this epic - don't skimp on coverage
- Integration tests should use real DocumentLifecycleManager, not mocks
- Performance tests should be repeatable and consistent
- Consider adding property-based tests for variable resolution
- Add tests for all error paths and edge cases
- Keep tests fast - mock slow operations (file I/O, database)
- Use pytest fixtures to share setup code
- Group tests logically by functionality
- Add regression tests for any bugs found during development

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
**Author:** Bob (Scrum Master)
