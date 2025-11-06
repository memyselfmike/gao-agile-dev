# Story 17.7: End-to-End Integration Tests

**Epic:** 17 - Context System Integration
**Story Points:** 3
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Comprehensive integration tests verifying the entire context system works end-to-end. These tests validate the complete workflow from document creation through context tracking, agent access, lineage generation, and performance benchmarks. The tests ensure all Epic 16 and Epic 17 components work together seamlessly in real-world scenarios, providing confidence for production deployment.

---

## Business Value

This story ensures the context system is production-ready:

- **Quality Assurance**: Comprehensive testing validates all components work together
- **Confidence**: Tests prove system works in real-world scenarios
- **Regression Prevention**: Tests catch breakages in future changes
- **Performance Validation**: Benchmarks ensure acceptable performance
- **Documentation**: Tests serve as executable documentation
- **Debugging**: Test failures pinpoint integration issues
- **Production Ready**: Passing E2E tests required for deployment
- **Continuous Integration**: Tests run in CI/CD pipeline
- **Developer Experience**: Tests show how to use the system correctly
- **Foundation for Growth**: Tests enable confident refactoring

---

## Acceptance Criteria

### Document Loading E2E Test
- [ ] E2E test: Create PRD, workflow loads it via context
- [ ] Test creates PRD file in test project
- [ ] Test creates workflow with context tracking
- [ ] Test agent accesses PRD via get_workflow_context()
- [ ] Test PRD content matches created document
- [ ] Test context persisted to database

### Story Implementation E2E Test
- [ ] E2E test: Implement story, context tracks document usage
- [ ] Test creates epic and story files
- [ ] Test workflow accesses epic definition
- [ ] Test workflow accesses story definition
- [ ] Test context usage recorded in database
- [ ] Test usage includes agent name and document type

### Lineage Generation E2E Test
- [ ] E2E test: Generate lineage report showing PRD -> Architecture -> Story flow
- [ ] Test creates full document hierarchy
- [ ] Test workflow accesses documents in order
- [ ] Test lineage tracker records relationships
- [ ] Test lineage report includes all document accesses
- [ ] Test lineage shows correct flow (PRD -> Arch -> Epic -> Story)

### Cache Performance E2E Test
- [ ] E2E test: Cache hit rate >80% for repeated document access
- [ ] Test accesses same document multiple times
- [ ] Test first access loads from file
- [ ] Test subsequent accesses use cache
- [ ] Test cache hit rate calculated correctly
- [ ] Test cache statistics accurate

### Concurrent Workflows E2E Test
- [ ] E2E test: Concurrent workflows don't interfere with each other
- [ ] Test runs 5 workflows simultaneously
- [ ] Test each workflow has isolated context
- [ ] Test no data corruption or race conditions
- [ ] Test thread-local storage works correctly
- [ ] Test all workflows complete successfully

### Error Handling E2E Test
- [ ] E2E test: Missing documents handled gracefully (no errors)
- [ ] Test workflow with missing PRD
- [ ] Test workflow with missing architecture
- [ ] Test context returns None for missing documents
- [ ] Test workflow continues despite missing documents
- [ ] Test error logged (not raised)

### Performance Tests
- [ ] Performance test: Document load <50ms (p95)
- [ ] Performance test: Context save <50ms (p95)
- [ ] Performance test: Lineage query <100ms (p95)
- [ ] Performance measured across 100+ operations
- [ ] Percentiles calculated correctly (p50, p95, p99)

### Test Reliability
- [ ] All E2E tests pass consistently (no flaky tests)
- [ ] Tests run in <2 minutes total
- [ ] Tests clean up after themselves (no leftover data)
- [ ] Tests can run in parallel
- [ ] Tests work on CI/CD environment

---

## Technical Notes

### Implementation Approach

**File:** `tests/integration/test_context_e2e.py`

Create comprehensive E2E tests:

```python
import pytest
from pathlib import Path
from gao_dev.core.context import (
    WorkflowContext, ContextPersistence, ContextUsageTracker,
    ContextLineageTracker, set_workflow_context, get_workflow_context
)
from gao_dev.core.document_lifecycle_manager import DocumentLifecycleManager, DocumentType
from gao_dev.orchestrator import GAODevOrchestrator
import time
import asyncio

class TestContextE2E:
    """End-to-end integration tests for context system."""

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create test project with documents."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Create document structure
        docs_dir = project_root / "docs" / "features" / "test-feature"
        docs_dir.mkdir(parents=True)

        # Create PRD
        prd = docs_dir / "PRD.md"
        prd.write_text("# Test Feature PRD\n\nThis is a test feature.")

        # Create Architecture
        arch = docs_dir / "ARCHITECTURE.md"
        arch.write_text("# Test Feature Architecture\n\nSystem design.")

        # Create Epic
        epic_dir = docs_dir / "epics"
        epic_dir.mkdir()
        epic = epic_dir / "epic-1.md"
        epic.write_text("# Epic 1\n\nTest epic definition.")

        # Create Story
        story_dir = docs_dir / "stories" / "epic-1"
        story_dir.mkdir(parents=True)
        story = story_dir / "story-1.1.md"
        story.write_text("# Story 1.1\n\nTest story definition.")

        return project_root

    @pytest.mark.asyncio
    async def test_document_loading_e2e(self, test_project):
        """E2E: Create PRD, workflow loads it via context."""
        # Setup
        doc_manager = DocumentLifecycleManager(test_project)
        persistence = ContextPersistence()

        # Create workflow context
        context = WorkflowContext(
            workflow_id="test-workflow-1",
            feature_name="test-feature",
            epic_number=1,
            story_number=1,
            phase="planning",
            status="in_progress"
        )

        # Load PRD via context (should use DocumentLifecycleManager)
        prd_content = context.get_prd()

        # Assertions
        assert prd_content is not None
        assert "Test Feature PRD" in prd_content
        assert "This is a test feature" in prd_content

        # Verify context persisted
        persistence.save_context(context)
        loaded_context = persistence.get_context("test-workflow-1")
        assert loaded_context is not None
        assert loaded_context.feature_name == "test-feature"

    @pytest.mark.asyncio
    async def test_story_implementation_e2e(self, test_project):
        """E2E: Implement story, context tracks document usage."""
        # Setup
        persistence = ContextPersistence()
        usage_tracker = ContextUsageTracker()

        # Create and set context
        context = WorkflowContext(
            workflow_id="test-workflow-2",
            feature_name="test-feature",
            epic_number=1,
            story_number=1,
            phase="implementation",
            status="in_progress"
        )
        persistence.save_context(context)
        set_workflow_context(context)

        # Simulate agent accessing documents
        epic_def = context.get_epic_definition()
        story_def = context.get_story_definition()
        architecture = context.get_architecture()

        # Assertions
        assert epic_def is not None
        assert "Epic 1" in epic_def
        assert story_def is not None
        assert "Story 1.1" in story_def
        assert architecture is not None
        assert "Architecture" in architecture

        # Verify usage tracked
        usage = usage_tracker.get_usage_for_context("test-workflow-2")
        assert len(usage) >= 3  # epic, story, architecture
        assert any(u['document_type'] == 'epic' for u in usage)
        assert any(u['document_type'] == 'story' for u in usage)
        assert any(u['document_type'] == 'architecture' for u in usage)

    @pytest.mark.asyncio
    async def test_lineage_generation_e2e(self, test_project):
        """E2E: Generate lineage report showing document flow."""
        # Setup
        persistence = ContextPersistence()
        lineage_tracker = ContextLineageTracker()

        # Create workflow with document access sequence
        context = WorkflowContext(
            workflow_id="test-workflow-3",
            feature_name="test-feature",
            epic_number=1,
            story_number=1,
            phase="planning",
            status="in_progress"
        )
        persistence.save_context(context)
        set_workflow_context(context)

        # Access documents in order: PRD -> Architecture -> Epic -> Story
        prd = context.get_prd()
        architecture = context.get_architecture()
        epic = context.get_epic_definition()
        story = context.get_story_definition()

        assert all([prd, architecture, epic, story])

        # Generate lineage report
        report = lineage_tracker.generate_lineage_report(epic_number=1)

        # Assertions
        assert report is not None
        assert 'document_accesses' in report
        accesses = report['document_accesses']
        assert len(accesses) >= 4

        # Verify flow: PRD -> Architecture -> Epic -> Story
        doc_types = [a['document_type'] for a in accesses]
        assert 'prd' in doc_types
        assert 'architecture' in doc_types
        assert 'epic' in doc_types
        assert 'story' in doc_types

    @pytest.mark.asyncio
    async def test_cache_performance_e2e(self, test_project):
        """E2E: Cache hit rate >80% for repeated document access."""
        # Setup
        context = WorkflowContext(
            workflow_id="test-workflow-4",
            feature_name="test-feature",
            epic_number=1,
            story_number=1,
            phase="implementation",
            status="in_progress"
        )
        set_workflow_context(context)

        # Access PRD 10 times
        for i in range(10):
            prd = context.get_prd()
            assert prd is not None

        # Check cache statistics
        # (Assuming ContextCache is used internally)
        # First access: miss, next 9: hits
        # Hit rate should be 90% (9/10)

        # Note: This test assumes ContextCache exposes statistics
        # If not exposed, we can measure performance instead
        # (first access slow, subsequent fast)

    @pytest.mark.asyncio
    async def test_concurrent_workflows_e2e(self, test_project):
        """E2E: Concurrent workflows don't interfere."""
        # Setup
        persistence = ContextPersistence()

        async def run_workflow(workflow_id: str, story_number: int):
            """Run a single workflow."""
            context = WorkflowContext(
                workflow_id=workflow_id,
                feature_name="test-feature",
                epic_number=1,
                story_number=story_number,
                phase="implementation",
                status="in_progress"
            )
            persistence.save_context(context)
            set_workflow_context(context)

            # Access documents
            prd = context.get_prd()
            epic = context.get_epic_definition()

            assert prd is not None
            assert epic is not None

            # Verify context is correct
            retrieved = get_workflow_context()
            assert retrieved.workflow_id == workflow_id
            assert retrieved.story_number == story_number

            # Clear context
            set_workflow_context(None)

        # Run 5 workflows concurrently
        workflows = [
            run_workflow(f"workflow-{i}", i)
            for i in range(5)
        ]

        await asyncio.gather(*workflows)

        # Verify all contexts persisted correctly
        for i in range(5):
            context = persistence.get_context(f"workflow-{i}")
            assert context is not None
            assert context.story_number == i

    @pytest.mark.asyncio
    async def test_missing_documents_e2e(self, test_project):
        """E2E: Missing documents handled gracefully."""
        # Setup
        context = WorkflowContext(
            workflow_id="test-workflow-5",
            feature_name="non-existent-feature",  # Missing feature
            epic_number=99,  # Missing epic
            story_number=99,  # Missing story
            phase="implementation",
            status="in_progress"
        )
        set_workflow_context(context)

        # Access missing documents (should return None, not raise)
        prd = context.get_prd()
        architecture = context.get_architecture()
        epic = context.get_epic_definition()
        story = context.get_story_definition()

        # Assertions: All should be None
        assert prd is None
        assert architecture is None
        assert epic is None
        assert story is None

        # Workflow should continue (no exception)

    @pytest.mark.asyncio
    async def test_performance_document_load(self, test_project):
        """Performance: Document load <50ms (p95)."""
        context = WorkflowContext(
            workflow_id="perf-test-1",
            feature_name="test-feature",
            epic_number=1,
            story_number=1,
            phase="implementation",
            status="in_progress"
        )
        set_workflow_context(context)

        # Measure 100 document loads
        load_times = []
        for _ in range(100):
            start = time.perf_counter()
            prd = context.get_prd()
            end = time.perf_counter()
            load_times.append((end - start) * 1000)  # Convert to ms

            assert prd is not None

        # Calculate p95
        load_times.sort()
        p95_index = int(len(load_times) * 0.95)
        p95 = load_times[p95_index]

        # Assertion: p95 < 50ms
        assert p95 < 50, f"p95 document load time: {p95:.2f}ms (expected <50ms)"

    @pytest.mark.asyncio
    async def test_performance_context_save(self, test_project):
        """Performance: Context save <50ms (p95)."""
        persistence = ContextPersistence()

        # Measure 100 context saves
        save_times = []
        for i in range(100):
            context = WorkflowContext(
                workflow_id=f"perf-save-{i}",
                feature_name="test-feature",
                epic_number=1,
                story_number=1,
                phase="implementation",
                status="in_progress"
            )

            start = time.perf_counter()
            persistence.save_context(context)
            end = time.perf_counter()
            save_times.append((end - start) * 1000)  # Convert to ms

        # Calculate p95
        save_times.sort()
        p95_index = int(len(save_times) * 0.95)
        p95 = save_times[p95_index]

        # Assertion: p95 < 50ms
        assert p95 < 50, f"p95 context save time: {p95:.2f}ms (expected <50ms)"

    @pytest.mark.asyncio
    async def test_performance_lineage_query(self, test_project):
        """Performance: Lineage query <100ms (p95)."""
        # Setup: Create some context and usage data
        persistence = ContextPersistence()
        lineage_tracker = ContextLineageTracker()

        # Create 10 contexts with usage
        for i in range(10):
            context = WorkflowContext(
                workflow_id=f"lineage-test-{i}",
                feature_name="test-feature",
                epic_number=1,
                story_number=i,
                phase="implementation",
                status="completed"
            )
            persistence.save_context(context)
            set_workflow_context(context)

            # Access some documents
            context.get_prd()
            context.get_epic_definition()

        # Measure 100 lineage queries
        query_times = []
        for _ in range(100):
            start = time.perf_counter()
            report = lineage_tracker.generate_lineage_report(epic_number=1)
            end = time.perf_counter()
            query_times.append((end - start) * 1000)  # Convert to ms

            assert report is not None

        # Calculate p95
        query_times.sort()
        p95_index = int(len(query_times) * 0.95)
        p95 = query_times[p95_index]

        # Assertion: p95 < 100ms
        assert p95 < 100, f"p95 lineage query time: {p95:.2f}ms (expected <100ms)"
```

**Files to Create:**
- `tests/integration/test_context_e2e.py` - E2E integration tests
- `tests/integration/test_context_performance.py` - Performance benchmarks
- `tests/integration/test_context_concurrency.py` - Concurrency tests

**Files to Modify:**
- `pytest.ini` - Add integration test markers
- `.github/workflows/tests.yml` - Run E2E tests in CI

**Dependencies:**
- All previous Epic 17 stories (17.1-17.6)
- All Epic 16 stories (context persistence layer)

---

## Testing Requirements

### E2E Test Categories

**Document Loading:**
- [ ] Test full document loading workflow
- [ ] Test with real DocumentLifecycleManager
- [ ] Test all document types (PRD, architecture, epic, story)

**Context Tracking:**
- [ ] Test context creation and persistence
- [ ] Test context updates through workflow
- [ ] Test usage tracking for all document accesses

**Lineage:**
- [ ] Test lineage generation with real data
- [ ] Test document flow visualization
- [ ] Test lineage query performance

**Performance:**
- [ ] Document load <50ms (p95)
- [ ] Context save <50ms (p95)
- [ ] Lineage query <100ms (p95)
- [ ] 100+ operations per benchmark

**Concurrency:**
- [ ] 5+ workflows in parallel
- [ ] No race conditions
- [ ] Context isolation verified

**Reliability:**
- [ ] Tests pass consistently (100 runs)
- [ ] No flaky tests
- [ ] Tests clean up properly

**Test Coverage:** 100% of E2E scenarios

---

## Documentation Requirements

- [ ] E2E testing guide
- [ ] How to run E2E tests locally
- [ ] Performance benchmarking guide
- [ ] CI/CD integration documentation
- [ ] Test data setup documentation
- [ ] Troubleshooting guide for test failures
- [ ] Performance baseline documentation
- [ ] Add E2E test results to sprint reports

---

## Implementation Details

### Development Approach

**Phase 1: Core E2E Tests**
1. Create test project fixture
2. Implement document loading E2E test
3. Implement story implementation E2E test
4. Implement lineage generation E2E test

**Phase 2: Performance Tests**
1. Implement document load performance test
2. Implement context save performance test
3. Implement lineage query performance test
4. Establish performance baselines

**Phase 3: Concurrency Tests**
1. Implement concurrent workflow test
2. Test thread-local storage isolation
3. Test no race conditions

**Phase 4: CI Integration**
1. Add E2E tests to pytest configuration
2. Update CI workflow to run E2E tests
3. Set up performance monitoring
4. Add test result reporting

### Quality Gates
- [ ] All E2E tests pass consistently
- [ ] Performance benchmarks met
- [ ] Concurrency tests pass
- [ ] Tests run in CI/CD
- [ ] Test coverage 100% for E2E scenarios
- [ ] Documentation complete

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] E2E test: Document loading workflow complete
- [ ] E2E test: Story implementation with context tracking
- [ ] E2E test: Lineage generation showing document flow
- [ ] E2E test: Cache hit rate >80%
- [ ] E2E test: Concurrent workflows isolated
- [ ] E2E test: Missing documents handled gracefully
- [ ] Performance test: Document load <50ms (p95)
- [ ] Performance test: Context save <50ms (p95)
- [ ] Performance test: Lineage query <100ms (p95)
- [ ] All E2E tests pass consistently (no flaky tests)
- [ ] Tests run in <2 minutes total
- [ ] Tests integrated in CI/CD pipeline
- [ ] Code reviewed and approved
- [ ] Documentation complete with guides
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.7 - E2E Integration Tests

  - Create comprehensive E2E integration tests
  - Test document loading workflow (PRD, architecture, epic, story)
  - Test story implementation with context tracking
  - Test lineage generation and document flow
  - Test cache performance (hit rate >80%)
  - Test concurrent workflow isolation
  - Test graceful handling of missing documents
  - Add performance benchmarks (document load, context save, lineage query)
  - Verify p95 performance targets met (<50ms, <100ms)
  - Integrate E2E tests in CI/CD pipeline
  - Create test fixtures and data setup utilities

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
