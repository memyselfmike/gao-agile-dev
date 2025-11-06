"""
Performance Tests for Context System Integration.

This module validates performance requirements for the context system:
- Document load <50ms (p95)
- Context save <50ms (p95)
- Lineage query <100ms (p95)

These tests ensure the context system meets the performance targets
defined in Epic 17 requirements.
"""

import time
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from statistics import median
from typing import List

import pytest

from gao_dev.core.context.context_api import (
    AgentContextAPI,
    _reset_global_instances,
)
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_lineage import ContextLineageTracker
from gao_dev.core.context.context_persistence import ContextPersistence
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import DocumentState, DocumentType
from gao_dev.lifecycle.registry import DocumentRegistry


# ============================================================================
# Performance Test Utilities
# ============================================================================


def measure_execution_time(func, iterations: int = 100) -> List[float]:
    """
    Measure execution time over multiple iterations.

    Args:
        func: Callable to measure
        iterations: Number of iterations to run

    Returns:
        List of execution times in milliseconds
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    return times


def calculate_percentile(times: List[float], percentile: int) -> float:
    """
    Calculate percentile from list of times.

    Args:
        times: List of times in milliseconds
        percentile: Percentile to calculate (e.g., 95 for p95)

    Returns:
        Percentile value in milliseconds
    """
    sorted_times = sorted(times)
    index = int(len(sorted_times) * (percentile / 100))
    return sorted_times[min(index, len(sorted_times) - 1)]


def print_performance_stats(name: str, times: List[float], target_ms: float):
    """
    Print performance statistics.

    Args:
        name: Name of operation
        times: List of execution times in milliseconds
        target_ms: Target time in milliseconds
    """
    p50 = calculate_percentile(times, 50)
    p95 = calculate_percentile(times, 95)
    p99 = calculate_percentile(times, 99)
    avg = sum(times) / len(times)
    med = median(times)

    print(f"\n{name} Performance:")
    print(f"  Samples: {len(times)}")
    print(f"  Average: {avg:.2f}ms")
    print(f"  Median:  {med:.2f}ms")
    print(f"  p50:     {p50:.2f}ms")
    print(f"  p95:     {p95:.2f}ms {'✓' if p95 <= target_ms else '✗ FAILED'}")
    print(f"  p99:     {p99:.2f}ms")
    print(f"  Min:     {min(times):.2f}ms")
    print(f"  Max:     {max(times):.2f}ms")
    print(f"  Target:  <{target_ms}ms")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_workspace():
    """Create temporary workspace with sample documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create feature directory
        feature_dir = workspace / "docs" / "features" / "test-feature"
        epics_dir = feature_dir / "epics"
        stories_dir = feature_dir / "stories" / "epic-1"

        feature_dir.mkdir(parents=True, exist_ok=True)
        epics_dir.mkdir(parents=True, exist_ok=True)
        stories_dir.mkdir(parents=True, exist_ok=True)

        # Create PRD (medium size document)
        prd_path = feature_dir / "PRD.md"
        prd_content = "# Product Requirements Document\n\n" + ("Lorem ipsum dolor sit amet.\n" * 100)
        prd_path.write_text(prd_content, encoding="utf-8")

        # Create Architecture (medium size document)
        arch_path = feature_dir / "ARCHITECTURE.md"
        arch_content = "# System Architecture\n\n" + ("Architecture details here.\n" * 100)
        arch_path.write_text(arch_content, encoding="utf-8")

        # Create Epic
        epic_path = epics_dir / "epic-1.md"
        epic_content = "# Epic 1: Test\n\n" + ("Epic details.\n" * 50)
        epic_path.write_text(epic_content, encoding="utf-8")

        # Create Story
        story_path = stories_dir / "story-1.1.md"
        story_content = "# Story 1.1: Test\n\n" + ("Story details.\n" * 50)
        story_path.write_text(story_content, encoding="utf-8")

        # Create .gao directory
        gao_dir = workspace / ".gao"
        gao_dir.mkdir(parents=True, exist_ok=True)

        yield workspace


@pytest.fixture
def document_registry(temp_workspace):
    """Create DocumentRegistry with test database."""
    db_path = temp_workspace / ".gao" / "documents.db"
    registry = DocumentRegistry(db_path)
    yield registry
    registry.close()


@pytest.fixture
def lifecycle_manager(document_registry, temp_workspace):
    """Create DocumentLifecycleManager."""
    archive_dir = temp_workspace / ".gao" / ".archive"
    return DocumentLifecycleManager(
        registry=document_registry, archive_dir=archive_dir
    )


@pytest.fixture
def context_persistence(temp_workspace):
    """Create ContextPersistence with test database."""
    db_path = temp_workspace / ".gao" / "gao_dev.db"
    return ContextPersistence(db_path=db_path)


@pytest.fixture
def lineage_tracker(temp_workspace):
    """Create ContextLineageTracker with test database."""
    db_path = temp_workspace / ".gao" / "gao_dev.db"
    return ContextLineageTracker(db_path=db_path)


@pytest.fixture
def usage_tracker(temp_workspace):
    """Create ContextUsageTracker with test database."""
    db_path = temp_workspace / ".gao" / "context_usage.db"
    return ContextUsageTracker(db_path)


@pytest.fixture(autouse=True)
def reset_context():
    """Reset global context instances."""
    _reset_global_instances()
    yield
    _reset_global_instances()


# ============================================================================
# Performance Test 1: Document Load <50ms (p95)
# ============================================================================


class TestDocumentLoadPerformance:
    """Test document loading performance."""

    def test_document_load_from_registry_under_50ms(
        self,
        temp_workspace,
        lifecycle_manager,
        monkeypatch,
    ):
        """
        Performance Test: Document load <50ms (p95).

        Validates that loading documents from the registry meets
        the <50ms p95 requirement.
        """
        monkeypatch.chdir(temp_workspace)

        # Register documents
        prd_path = temp_workspace / "docs" / "features" / "test-feature" / "PRD.md"
        prd_doc = lifecycle_manager.register_document(
            path=prd_path, doc_type=DocumentType.PRD.value, author="john"
        )
        lifecycle_manager.transition_state(
            prd_doc.id, DocumentState.ACTIVE, reason="Ready"
        )

        arch_path = (
            temp_workspace / "docs" / "features" / "test-feature" / "ARCHITECTURE.md"
        )
        arch_doc = lifecycle_manager.register_document(
            path=arch_path, doc_type=DocumentType.ARCHITECTURE.value, author="winston"
        )
        lifecycle_manager.transition_state(
            arch_doc.id, DocumentState.ACTIVE, reason="Ready"
        )

        # Create context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test",
        )

        # Create API without cache (test raw load performance)
        cache = ContextCache(ttl=timedelta(seconds=1), max_size=0)  # Effectively disabled
        api = AgentContextAPI(context, cache=cache)

        # Measure document load times
        def load_prd():
            api.cache.clear()  # Force reload
            return api.get_prd()

        times = measure_execution_time(load_prd, iterations=100)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Document Load (PRD)", times, target_ms=50.0)

        # Verify p95 < 50ms
        assert p95 < 50.0, f"Document load p95 {p95:.2f}ms exceeds 50ms target"

    def test_document_load_from_cache_under_10ms(
        self,
        temp_workspace,
        monkeypatch,
    ):
        """
        Performance Test: Cached document load <10ms (p95).

        Validates that loading from cache is extremely fast.
        """
        monkeypatch.chdir(temp_workspace)

        # Create context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test",
        )

        # Create API with cache
        cache = ContextCache(ttl=timedelta(minutes=5), max_size=100)
        api = AgentContextAPI(context, cache=cache)

        # Prime cache
        api.get_prd()

        # Measure cached load times
        def load_cached_prd():
            return api.get_prd()

        times = measure_execution_time(load_cached_prd, iterations=1000)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Cached Document Load", times, target_ms=10.0)

        # Verify p95 < 10ms (cache should be very fast)
        assert p95 < 10.0, f"Cached load p95 {p95:.2f}ms exceeds 10ms target"


# ============================================================================
# Performance Test 2: Context Save <50ms (p95)
# ============================================================================


class TestContextSavePerformance:
    """Test context persistence performance."""

    def test_context_save_under_50ms(
        self,
        temp_workspace,
        context_persistence,
    ):
        """
        Performance Test: Context save <50ms (p95).

        Validates that persisting context to database meets
        the <50ms p95 requirement.
        """
        # Create contexts to save
        contexts = []
        for i in range(100):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=1,
                story_num=1,
                feature="test-feature",
                workflow_name=f"test-{i}",
            )
            context.metadata["test_data"] = "x" * 1000  # Add some data
            contexts.append(context)

        # Measure save times
        def save_context(ctx):
            def _save():
                context_persistence.save_context(ctx)
            return _save

        all_times = []
        for ctx in contexts:
            times = measure_execution_time(save_context(ctx), iterations=1)
            all_times.extend(times)

        # Calculate p95
        p95 = calculate_percentile(all_times, 95)

        # Print stats
        print_performance_stats("Context Save", all_times, target_ms=50.0)

        # Verify p95 < 50ms
        assert p95 < 50.0, f"Context save p95 {p95:.2f}ms exceeds 50ms target"

    def test_context_load_under_50ms(
        self,
        temp_workspace,
        context_persistence,
    ):
        """
        Performance Test: Context load <50ms (p95).

        Validates that loading context from database meets
        the <50ms p95 requirement.
        """
        # Create and save contexts
        context_ids = []
        for i in range(100):
            context = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=1,
                story_num=1,
                feature="test-feature",
                workflow_name=f"test-{i}",
            )
            context.metadata["test_data"] = "x" * 1000
            context_persistence.save_context(context)
            context_ids.append(context.workflow_id)

        # Measure load times
        def load_context(ctx_id):
            def _load():
                context_persistence.load_context(ctx_id)
            return _load

        all_times = []
        for ctx_id in context_ids:
            times = measure_execution_time(load_context(ctx_id), iterations=1)
            all_times.extend(times)

        # Calculate p95
        p95 = calculate_percentile(all_times, 95)

        # Print stats
        print_performance_stats("Context Load", all_times, target_ms=50.0)

        # Verify p95 < 50ms
        assert p95 < 50.0, f"Context load p95 {p95:.2f}ms exceeds 50ms target"


# ============================================================================
# Performance Test 3: Lineage Query <100ms (p95)
# ============================================================================


class TestLineageQueryPerformance:
    """Test lineage query performance."""

    def test_lineage_query_under_100ms(
        self,
        temp_workspace,
        lineage_tracker,
    ):
        """
        Performance Test: Lineage query <100ms (p95).

        Validates that querying lineage data meets
        the <100ms p95 requirement.
        """
        import hashlib

        # Create lineage data
        for epic in range(1, 11):  # 10 epics
            for story in range(1, 11):  # 10 stories per epic
                # Record multiple document usages per story
                for doc_type in ["prd", "architecture", "epic", "story"]:
                    lineage_tracker.record_usage(
                        artifact_type="story",
                        artifact_id=f"{epic}.{story}",
                        document_id=epic * 100 + story,
                        document_path=f"docs/features/test/{doc_type}.md",
                        document_type=doc_type,
                        document_version=hashlib.sha256(
                            f"{doc_type}_v1".encode()
                        ).hexdigest()[:16],
                        workflow_id=f"wf-{epic}-{story}",
                        epic=epic,
                        story=f"{epic}.{story}",
                    )

        # Measure artifact context query times
        def query_artifact_context():
            lineage_tracker.get_artifact_context("story", "5.5")

        times = measure_execution_time(query_artifact_context, iterations=100)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Artifact Context Query", times, target_ms=100.0)

        # Verify p95 < 100ms
        assert p95 < 100.0, f"Artifact context query p95 {p95:.2f}ms exceeds 100ms target"

    def test_lineage_report_generation_under_500ms(
        self,
        temp_workspace,
        lineage_tracker,
    ):
        """
        Performance Test: Lineage report generation <500ms.

        Validates that generating lineage reports is reasonably fast.
        """
        import hashlib

        # Create lineage data for epic 1
        for story in range(1, 21):  # 20 stories
            for doc_type in ["prd", "architecture", "epic", "story"]:
                lineage_tracker.record_usage(
                    artifact_type="story",
                    artifact_id=f"1.{story}",
                    document_id=100 + story,
                    document_path=f"docs/features/test/{doc_type}.md",
                    document_type=doc_type,
                    document_version=hashlib.sha256(
                        f"{doc_type}_v1".encode()
                    ).hexdigest()[:16],
                    workflow_id=f"wf-1-{story}",
                    epic=1,
                    story=f"1.{story}",
                )

        # Measure report generation times
        def generate_report():
            lineage_tracker.generate_lineage_report(epic=1, output_format="markdown")

        times = measure_execution_time(generate_report, iterations=50)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Lineage Report Generation", times, target_ms=500.0)

        # Verify p95 < 500ms
        assert p95 < 500.0, f"Report generation p95 {p95:.2f}ms exceeds 500ms target"


# ============================================================================
# Performance Test 4: Usage Tracking <20ms (p95)
# ============================================================================


class TestUsageTrackingPerformance:
    """Test usage tracking performance."""

    def test_usage_tracking_under_20ms(
        self,
        temp_workspace,
        usage_tracker,
    ):
        """
        Performance Test: Usage tracking <20ms (p95).

        Validates that recording usage is very fast and doesn't
        slow down document access.
        """
        # Measure tracking times
        def record_usage():
            usage_tracker.record_usage(
                context_key="prd",
                content_hash="abc123def456",
                cache_hit=False,
                workflow_id="test-workflow",
                epic=1,
                story="1.1",
            )

        times = measure_execution_time(record_usage, iterations=100)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Usage Tracking", times, target_ms=20.0)

        # Verify p95 < 20ms
        assert p95 < 20.0, f"Usage tracking p95 {p95:.2f}ms exceeds 20ms target"


# ============================================================================
# Performance Test 5: Cache Operations <1ms (p95)
# ============================================================================


class TestCachePerformance:
    """Test cache operation performance."""

    def test_cache_get_under_1ms(self):
        """
        Performance Test: Cache get <1ms (p95).

        Validates that cache lookups are extremely fast.
        """
        cache = ContextCache(ttl=timedelta(minutes=5), max_size=1000)

        # Prime cache
        for i in range(100):
            cache.set(f"key-{i}", f"value-{i}" * 100)

        # Measure get times
        def cache_get():
            cache.get("key-50")

        times = measure_execution_time(cache_get, iterations=10000)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Cache Get", times, target_ms=1.0)

        # Verify p95 < 1ms
        assert p95 < 1.0, f"Cache get p95 {p95:.2f}ms exceeds 1ms target"

    def test_cache_set_under_1ms(self):
        """
        Performance Test: Cache set <1ms (p95).

        Validates that cache writes are extremely fast.
        """
        cache = ContextCache(ttl=timedelta(minutes=5), max_size=1000)

        # Measure set times
        times = []
        for i in range(1000):
            start = time.perf_counter()
            cache.set(f"key-{i}", f"value-{i}" * 100)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Cache Set", times, target_ms=1.0)

        # Verify p95 < 1ms
        assert p95 < 1.0, f"Cache set p95 {p95:.2f}ms exceeds 1ms target"


# ============================================================================
# Performance Test 6: End-to-End Performance
# ============================================================================


class TestE2EPerformance:
    """Test end-to-end performance of complete workflows."""

    def test_full_document_access_workflow_under_200ms(
        self,
        temp_workspace,
        lifecycle_manager,
        usage_tracker,
        monkeypatch,
    ):
        """
        Performance Test: Full document access workflow <200ms (p95).

        Tests complete workflow:
        1. Load document from registry
        2. Cache document
        3. Track usage
        4. Return to agent

        This simulates realistic agent usage.
        """
        monkeypatch.chdir(temp_workspace)

        # Register documents
        prd_path = temp_workspace / "docs" / "features" / "test-feature" / "PRD.md"
        prd_doc = lifecycle_manager.register_document(
            path=prd_path, doc_type=DocumentType.PRD.value, author="john"
        )
        lifecycle_manager.transition_state(
            prd_doc.id, DocumentState.ACTIVE, reason="Ready"
        )

        # Create context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=1,
            story_num=1,
            feature="test-feature",
            workflow_name="test",
        )

        # Measure full workflow
        def full_workflow():
            cache = ContextCache()
            api = AgentContextAPI(context, cache=cache, tracker=usage_tracker)
            api.get_prd()
            api.get_architecture()
            api.get_epic_definition()
            api.get_story_definition()

        times = measure_execution_time(full_workflow, iterations=50)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Full Document Access Workflow", times, target_ms=200.0)

        # Verify p95 < 200ms
        assert p95 < 200.0, f"Full workflow p95 {p95:.2f}ms exceeds 200ms target"


# ============================================================================
# Performance Test 7: Concurrent Access Performance
# ============================================================================


class TestConcurrentAccessPerformance:
    """Test performance under concurrent access."""

    def test_cache_concurrent_access_performance(self):
        """
        Performance Test: Cache handles concurrent access efficiently.

        Validates that cache remains fast under concurrent load.
        """
        import threading

        cache = ContextCache(ttl=timedelta(minutes=5), max_size=1000)

        # Prime cache
        for i in range(100):
            cache.set(f"key-{i}", f"value-{i}" * 100)

        # Measure concurrent access
        results = []

        def access_cache():
            times = []
            for _ in range(100):
                start = time.perf_counter()
                cache.get("key-50")
                end = time.perf_counter()
                times.append((end - start) * 1000)
            results.append(times)

        # Run 10 threads concurrently
        threads = [threading.Thread(target=access_cache) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Combine all results
        all_times = [t for times in results for t in times]

        # Calculate p95
        p95 = calculate_percentile(all_times, 95)

        # Print stats
        print_performance_stats("Concurrent Cache Access", all_times, target_ms=5.0)

        # Verify p95 < 5ms (slightly higher than single-threaded due to locking)
        assert p95 < 5.0, f"Concurrent cache access p95 {p95:.2f}ms exceeds 5ms target"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
