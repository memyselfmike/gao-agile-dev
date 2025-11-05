"""
Unit Tests for DocumentHealthMetrics.

This module provides comprehensive unit tests for the DocumentHealthMetrics class,
covering KPI collection, health report generation, and action item identification.
"""

import tempfile
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.governance import DocumentGovernance
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.health_metrics import DocumentHealthMetrics
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType, RelationshipType


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_archive_dir():
    """Create temporary archive directory."""
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir

    # Cleanup
    import shutil

    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_governance_config():
    """Create temporary governance configuration file."""
    config = {
        "document_governance": {
            "ownership": {
                "prd": {
                    "created_by": "John",
                    "approved_by": "Mary",
                    "reviewed_by": "Winston",
                    "informed": ["Team"],
                },
                "architecture": {
                    "created_by": "Winston",
                    "approved_by": "Mary",
                    "reviewed_by": "John",
                    "informed": ["Team"],
                },
                "story": {
                    "created_by": "Bob",
                    "approved_by": "John",
                    "reviewed_by": "Amelia",
                    "informed": ["Team"],
                },
            },
            "review_cadence": {
                "prd": 90,
                "architecture": 90,
                "story": 30,
                "adr": -1,  # Never stale
                "epic": 60,
                "postmortem": -1,
            },
        }
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(config, f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def health_metrics(temp_db, temp_archive_dir, temp_governance_config):
    """Create DocumentHealthMetrics instance for testing."""
    registry = DocumentRegistry(temp_db)
    doc_manager = DocumentLifecycleManager(registry, temp_archive_dir)
    governance = DocumentGovernance(doc_manager, temp_governance_config)
    naming_convention = DocumentNamingConvention()

    health = DocumentHealthMetrics(
        registry=registry,
        governance=governance,
        naming_convention=naming_convention,
    )

    yield health

    # Cleanup
    registry.close()


def update_document_timestamps(registry, doc_id, created_at, modified_at):
    """Helper to update document timestamps for testing."""
    import sqlite3
    conn = sqlite3.connect(str(registry.db_path))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET created_at = ?, modified_at = ? WHERE id = ?",
        (created_at, modified_at, doc_id)
    )
    conn.commit()
    conn.close()


class TestHealthMetricsBasics:
    """Test basic health metrics collection."""

    def test_collect_metrics_empty_database(self, health_metrics):
        """Test metrics collection with no documents."""
        metrics = health_metrics.collect_metrics()

        assert metrics["total_documents"] == 0
        assert metrics["stale_documents"] == 0
        assert metrics["documents_needing_review"] == 0
        assert metrics["orphaned_documents"] == 0
        assert metrics["documents_without_owners"] == 0
        assert metrics["avg_document_age_days"] == 0.0
        assert metrics["naming_compliance_rate"] == 100.0
        assert metrics["frontmatter_compliance_rate"] == 100.0

    def test_collect_metrics_with_documents(self, health_metrics):
        """Test metrics collection with sample documents."""
        # Add sample documents
        health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="John",
            state=DocumentState.ACTIVE,
            owner="John",
            metadata={"title": "Test PRD", "doc_type": "prd", "status": "active"},
        )

        health_metrics.registry.register_document(
            path="docs/architecture-test-1.0.md",
            doc_type="architecture",
            author="Winston",
            state=DocumentState.DRAFT,
            owner="Winston",
            metadata={"title": "Test Arch", "doc_type": "architecture", "status": "draft"},
        )

        metrics = health_metrics.collect_metrics()

        assert metrics["total_documents"] == 2
        assert "documents_by_state" in metrics
        assert metrics["documents_by_state"]["active"] == 1
        assert metrics["documents_by_state"]["draft"] == 1
        assert "documents_by_type" in metrics
        assert metrics["documents_by_type"]["prd"] == 1
        assert metrics["documents_by_type"]["architecture"] == 1

    def test_count_by_state(self, health_metrics):
        """Test counting documents by state."""
        # Add documents in different states
        for i, state in enumerate([DocumentState.ACTIVE, DocumentState.DRAFT, DocumentState.ACTIVE, DocumentState.OBSOLETE]):
            health_metrics.registry.register_document(
                path=f"docs/test-{i}.md",
                doc_type="prd",
                author="Test",
                state=state,
            )

        all_docs = health_metrics.registry.query_documents()
        state_counts = health_metrics._count_by_state(all_docs)

        assert state_counts["active"] == 2
        assert state_counts["draft"] == 1
        assert state_counts["obsolete"] == 1

    def test_count_by_type(self, health_metrics):
        """Test counting documents by type."""
        # Add documents of different types
        types = ["prd", "architecture", "prd", "story"]
        for i, doc_type in enumerate(types):
            health_metrics.registry.register_document(
                path=f"docs/test-{i}.md",
                doc_type=doc_type,
                author="Test",
                state=DocumentState.ACTIVE,
            )

        all_docs = health_metrics.registry.query_documents()
        type_counts = health_metrics._count_by_type(all_docs)

        assert type_counts["prd"] == 2
        assert type_counts["architecture"] == 1
        assert type_counts["story"] == 1


class TestStaleDocuments:
    """Test stale document detection."""

    def test_count_stale_documents_none(self, health_metrics):
        """Test stale count with recently modified documents."""
        # Add recently modified document
        health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        stale_count = health_metrics._count_stale_documents()
        assert stale_count == 0

    def test_count_stale_documents_old(self, health_metrics):
        """Test stale count with old documents."""
        # Add document modified 100 days ago (cadence is 90 for PRD)
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        doc = health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Update timestamps directly in database
        update_document_timestamps(health_metrics.registry, doc.id, old_date, old_date)

        stale_count = health_metrics._count_stale_documents()
        assert stale_count == 1

    def test_count_stale_documents_never_stale(self, health_metrics):
        """Test that documents with -1 cadence are never stale."""
        # ADR has cadence -1 (never stale)
        old_date = (datetime.now() - timedelta(days=365)).isoformat()
        doc = health_metrics.registry.register_document(
            path="docs/adr-001-test-1.0.md",
            doc_type="adr",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Update timestamps directly in database
        update_document_timestamps(health_metrics.registry, doc.id, old_date, old_date)

        stale_count = health_metrics._count_stale_documents()
        assert stale_count == 0

    def test_count_stale_only_active_documents(self, health_metrics):
        """Test that only ACTIVE documents are counted as stale."""
        # Add old document in DRAFT state
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        doc = health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.DRAFT,
        )

        # Update timestamps directly in database
        update_document_timestamps(health_metrics.registry, doc.id, old_date, old_date)

        stale_count = health_metrics._count_stale_documents()
        assert stale_count == 0


class TestOrphanedDocuments:
    """Test orphaned document detection."""

    def test_count_orphaned_none(self, health_metrics):
        """Test orphaned count with related documents."""
        # Add parent and child documents
        parent_doc = health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        child_doc = health_metrics.registry.register_document(
            path="docs/architecture-test-1.0.md",
            doc_type="architecture",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Add relationship using doc.id
        health_metrics.registry.add_relationship(
            parent_doc.id, child_doc.id, RelationshipType.DERIVED_FROM
        )

        orphaned_count = health_metrics._count_orphaned()
        assert orphaned_count == 0

    def test_count_orphaned_with_orphan(self, health_metrics):
        """Test orphaned count with orphaned document."""
        # Add orphaned document
        health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        orphaned_count = health_metrics._count_orphaned()
        assert orphaned_count == 1

    def test_count_orphaned_excludes_temp(self, health_metrics):
        """Test that temp documents are not counted as orphaned."""
        # Add temp document
        health_metrics.registry.register_document(
            path="docs/temp-notes.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
            metadata={"5s_classification": "temp"},
        )

        orphaned_count = health_metrics._count_orphaned()
        assert orphaned_count == 0

    def test_count_orphaned_excludes_draft(self, health_metrics):
        """Test that draft documents are not counted as orphaned."""
        # Add draft document
        health_metrics.registry.register_document(
            path="docs/draft-prd.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.DRAFT,
        )

        orphaned_count = health_metrics._count_orphaned()
        assert orphaned_count == 0


class TestComplianceMetrics:
    """Test compliance metrics calculation."""

    def test_naming_compliance_all_compliant(self, health_metrics):
        """Test naming compliance with all compliant documents."""
        # Add documents with valid names following naming convention
        # Pattern: {DocType}_{subject}_{date}_v{version}.{ext}
        for i in range(5):
            health_metrics.registry.register_document(
                path=f"docs/PRD_test-{i}_2024-11-05_v1.0.md",
                doc_type="prd",
                author="Test",
                state=DocumentState.ACTIVE,
            )

        all_docs = health_metrics.registry.query_documents()
        compliance = health_metrics._calculate_naming_compliance(all_docs)
        assert compliance == 100.0

    def test_naming_compliance_partial(self, health_metrics):
        """Test naming compliance with some non-compliant documents."""
        # Add compliant document following naming convention
        health_metrics.registry.register_document(
            path="docs/PRD_test_2024-11-05_v1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Add non-compliant document
        health_metrics.registry.register_document(
            path="docs/invalid_name.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        all_docs = health_metrics.registry.query_documents()
        compliance = health_metrics._calculate_naming_compliance(all_docs)
        assert compliance == 50.0

    def test_frontmatter_compliance_all_compliant(self, health_metrics):
        """Test frontmatter compliance with all complete documents."""
        # Add documents with complete frontmatter
        for i in range(5):
            health_metrics.registry.register_document(
                path=f"docs/PRD_test-{i}_2024-11-05_v1.0.md",
                doc_type="prd",
                author="Test",
                state=DocumentState.ACTIVE,
                owner="John",
                metadata={
                    "title": f"Test PRD {i}",
                    "doc_type": "prd",
                    "status": "active",
                    "owner": "John",  # Owner should be in metadata too
                },
            )

        all_docs = health_metrics.registry.query_documents()
        compliance = health_metrics._calculate_frontmatter_compliance(all_docs)
        assert compliance == 100.0

    def test_frontmatter_compliance_partial(self, health_metrics):
        """Test frontmatter compliance with incomplete documents."""
        # Add complete document
        health_metrics.registry.register_document(
            path="docs/PRD_test-1_2024-11-05_v1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
            owner="John",
            metadata={
                "title": "Test PRD",
                "doc_type": "prd",
                "status": "active",
                "owner": "John",  # Owner in metadata
            },
        )

        # Add incomplete document (missing owner in metadata)
        health_metrics.registry.register_document(
            path="docs/PRD_test-2_2024-11-05_v1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
            metadata={"title": "Test PRD 2", "doc_type": "prd", "status": "active"},
        )

        all_docs = health_metrics.registry.query_documents()
        compliance = health_metrics._calculate_frontmatter_compliance(all_docs)
        assert compliance == 50.0


class TestAgeMetrics:
    """Test document age metrics."""

    def test_average_age_calculation(self, health_metrics):
        """Test average age calculation."""
        # Add documents with known ages
        now = datetime.now()
        doc1 = health_metrics.registry.register_document(
            path="docs/prd-1.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )
        doc2 = health_metrics.registry.register_document(
            path="docs/prd-2.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Update timestamps directly in database
        created1 = (now - timedelta(days=10)).isoformat()
        created2 = (now - timedelta(days=20)).isoformat()
        update_document_timestamps(health_metrics.registry, doc1.id, created1, created1)
        update_document_timestamps(health_metrics.registry, doc2.id, created2, created2)

        all_docs = health_metrics.registry.query_documents()
        avg_age = health_metrics._calculate_avg_age(all_docs)

        # Average should be 15 days (10 + 20) / 2
        assert 14.0 <= avg_age <= 16.0

    def test_oldest_document_age(self, health_metrics):
        """Test oldest document age calculation."""
        now = datetime.now()
        doc1 = health_metrics.registry.register_document(
            path="docs/prd-1.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )
        doc2 = health_metrics.registry.register_document(
            path="docs/prd-2.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Update timestamps directly in database
        created1 = (now - timedelta(days=100)).isoformat()
        created2 = (now - timedelta(days=50)).isoformat()
        update_document_timestamps(health_metrics.registry, doc1.id, created1, created1)
        update_document_timestamps(health_metrics.registry, doc2.id, created2, created2)

        all_docs = health_metrics.registry.query_documents()
        oldest_age = health_metrics._get_oldest_document_age(all_docs)

        assert 99 <= oldest_age <= 101

    def test_newest_document_age(self, health_metrics):
        """Test newest document age calculation."""
        now = datetime.now()
        doc1 = health_metrics.registry.register_document(
            path="docs/prd-1.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )
        doc2 = health_metrics.registry.register_document(
            path="docs/prd-2.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        # Update timestamps directly in database
        created1 = (now - timedelta(days=100)).isoformat()
        created2 = (now - timedelta(days=5)).isoformat()
        update_document_timestamps(health_metrics.registry, doc1.id, created1, created1)
        update_document_timestamps(health_metrics.registry, doc2.id, created2, created2)

        all_docs = health_metrics.registry.query_documents()
        newest_age = health_metrics._get_newest_document_age(all_docs)

        assert 4 <= newest_age <= 6


class TestHealthReport:
    """Test health report generation."""

    def test_generate_health_report_empty(self, health_metrics):
        """Test health report generation with no documents."""
        report = health_metrics.generate_health_report()

        assert "# Document Lifecycle Health Report" in report
        assert "Summary Metrics" in report
        assert "Documents by State" in report
        assert "Documents by Type" in report
        assert "Action Items" in report

    def test_generate_health_report_with_data(self, health_metrics):
        """Test health report generation with sample data."""
        # Add sample documents
        for i in range(5):
            health_metrics.registry.register_document(
                path=f"docs/prd-test-{i}-1.0.md",
                doc_type="prd",
                author="Test",
                state=DocumentState.ACTIVE,
                owner="John",
                metadata={
                    "title": f"Test PRD {i}",
                    "doc_type": "prd",
                    "status": "active",
                },
            )

        report = health_metrics.generate_health_report()

        assert "Total Documents** | 5" in report
        assert "active | 5" in report
        assert "prd | 5" in report

    def test_generate_action_items(self, health_metrics):
        """Test action items generation."""
        # Add document without owner
        health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        metrics = health_metrics.collect_metrics()
        action_items = health_metrics._generate_action_items(metrics)

        assert len(action_items) > 0
        assert any("owner" in item.lower() for item in action_items)


class TestActionItemsAPI:
    """Test structured action items API."""

    def test_get_action_items_only_empty(self, health_metrics):
        """Test action items API with healthy system."""
        # Add fully compliant documents following naming convention
        docs = []
        for i in range(3):
            doc = health_metrics.registry.register_document(
                path=f"docs/PRD_test-{i}_2024-11-05_v1.0.md",
                doc_type="prd",
                author="Test",
                state=DocumentState.ACTIVE,
                owner="John",
                metadata={
                    "title": f"Test PRD {i}",
                    "doc_type": "prd",
                    "status": "active",
                    "owner": "John",  # Add owner to metadata too
                },
            )
            docs.append(doc)

            # Add relationships to avoid orphans using doc.id
            if i > 0:
                health_metrics.registry.add_relationship(
                    docs[i-1].id, doc.id, RelationshipType.REFERENCES
                )

        action_items = health_metrics.get_action_items_only()
        assert len(action_items) == 0

    def test_get_action_items_only_with_issues(self, health_metrics):
        """Test action items API with issues."""
        # Add document without owner
        health_metrics.registry.register_document(
            path="docs/prd-test-1.0.md",
            doc_type="prd",
            author="Test",
            state=DocumentState.ACTIVE,
        )

        action_items = health_metrics.get_action_items_only()

        assert len(action_items) > 0

        # Check structure
        for item in action_items:
            assert "type" in item
            assert "count" in item
            assert "severity" in item
            assert "description" in item
            assert "resolution_steps" in item
            assert item["severity"] in ["high", "medium", "low"]
            assert isinstance(item["resolution_steps"], list)


class TestPerformance:
    """Test performance requirements."""

    def test_collect_metrics_performance(self, health_metrics):
        """Test that metrics collection for 1000 documents takes <1 second."""
        # Add 1000 documents
        for i in range(1000):
            health_metrics.registry.register_document(
                path=f"docs/doc-{i}.md",
                doc_type="prd" if i % 2 == 0 else "story",
                author="Test",
                state=DocumentState.ACTIVE if i % 3 == 0 else DocumentState.DRAFT,
                owner="Test" if i % 2 == 0 else None,
            )

        # Measure time
        start_time = time.time()
        metrics = health_metrics.collect_metrics()
        elapsed_time = time.time() - start_time

        # Should complete in less than 1 second
        assert elapsed_time < 1.0
        assert metrics["total_documents"] == 1000

    def test_generate_report_performance(self, health_metrics):
        """Test that report generation is fast."""
        # Add 100 documents
        for i in range(100):
            health_metrics.registry.register_document(
                path=f"docs/doc-{i}.md",
                doc_type="prd",
                author="Test",
                state=DocumentState.ACTIVE,
                owner="Test",
            )

        # Measure time
        start_time = time.time()
        report = health_metrics.generate_health_report()
        elapsed_time = time.time() - start_time

        # Should be fast
        assert elapsed_time < 0.5
        assert len(report) > 0
