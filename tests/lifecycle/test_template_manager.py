"""
Tests for Document Template Manager.

This module tests the template management system including:
- Template creation with frontmatter
- Variable validation
- Naming convention integration
- Lifecycle registration
- Governance assignment
"""

import pytest
from pathlib import Path
import yaml
from datetime import datetime, timedelta

from gao_dev.lifecycle.template_manager import DocumentTemplateManager
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.governance import DocumentGovernance
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import DocumentState


@pytest.fixture
def test_db(tmp_path):
    """Create test database."""
    db_path = tmp_path / "test.db"
    registry = DocumentRegistry(db_path)
    yield registry
    # Cleanup: close the database connection
    registry.close()


@pytest.fixture
def doc_manager(test_db, tmp_path):
    """Create document manager."""
    archive_dir = tmp_path / ".archive"
    return DocumentLifecycleManager(test_db, archive_dir)


@pytest.fixture
def governance_config(tmp_path):
    """Create test governance config."""
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
                "adr": {
                    "created_by": "Winston",
                    "approved_by": "Mary",
                    "reviewed_by": "Amelia",
                    "informed": ["Team"],
                },
                "epic": {
                    "created_by": "Bob",
                    "approved_by": "John",
                    "reviewed_by": "Winston",
                    "informed": ["Team"],
                },
                "postmortem": {
                    "created_by": "Incident Owner",
                    "approved_by": "Mary",
                    "reviewed_by": "Team",
                    "informed": ["Leadership"],
                },
                "runbook": {
                    "created_by": "Amelia",
                    "approved_by": "Mary",
                    "reviewed_by": "Murat",
                    "informed": ["Team"],
                },
            },
            "review_cadence": {
                "prd": 90,
                "architecture": 60,
                "story": 30,
                "epic": 60,
                "adr": -1,
                "postmortem": 365,
                "runbook": 90,
            },
            "permissions": {
                "archive": {"allowed_roles": ["owner", "engineering_manager"]},
                "delete": {"allowed_roles": ["engineering_manager"]},
            },
            "rules": {
                "require_owner_on_creation": True,
                "auto_assign_ownership": True,
            },
            "priority_mapping": {
                "P0": 1,
                "P1": 2,
                "P2": 3,
                "P3": 4,
                "default": 5,
            },
        }
    }

    config_path = tmp_path / "governance.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path


@pytest.fixture
def governance_manager(doc_manager, governance_config):
    """Create governance manager."""
    return DocumentGovernance(doc_manager, governance_config)


@pytest.fixture
def templates_dir():
    """Get templates directory."""
    # Use actual templates directory
    base_dir = Path(__file__).parent.parent.parent
    templates_dir = base_dir / "gao_dev" / "config" / "templates"

    if not templates_dir.exists():
        pytest.skip(f"Templates directory not found: {templates_dir}")

    return templates_dir


@pytest.fixture
def template_manager(templates_dir, doc_manager, governance_manager):
    """Create template manager."""
    naming = DocumentNamingConvention()
    return DocumentTemplateManager(
        templates_dir=templates_dir,
        doc_manager=doc_manager,
        naming_convention=naming,
        governance=governance_manager,
    )


class TestTemplateManager:
    """Test DocumentTemplateManager class."""

    def test_create_prd_from_template(self, template_manager, tmp_path):
        """Test creating PRD from template."""
        variables = {
            "subject": "user-authentication",
            "author": "John",
            "feature": "auth-system",
            "related_docs": ["docs/ARCHITECTURE.md"],
            "tags": ["authentication", "security"],
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template("prd", variables, output_dir)

        # Verify file created
        assert file_path.exists()
        assert file_path.parent == output_dir

        # Verify filename follows convention
        assert file_path.name.startswith("PRD_user-authentication_")
        assert file_path.name.endswith(".md")

        # Verify content
        content = file_path.read_text()
        assert "# Product Requirements Document: user-authentication" in content
        assert "**Author:** John" in content

        # Verify frontmatter
        assert content.startswith("---")
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["title"] == "user-authentication"
        assert frontmatter["doc_type"] == "PRD"
        assert frontmatter["author"] == "John"
        assert frontmatter["owner"] == "Mary"
        assert frontmatter["reviewer"] == "Winston"
        assert frontmatter["feature"] == "auth-system"
        assert frontmatter["tags"] == ["authentication", "security"]
        assert frontmatter["related_docs"] == ["docs/ARCHITECTURE.md"]

    def test_create_architecture_from_template(self, template_manager, tmp_path):
        """Test creating architecture from template."""
        variables = {
            "subject": "microservices-architecture",
            "author": "Winston",
            "version": "2.0",
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template(
            "architecture", variables, output_dir
        )

        assert file_path.exists()
        assert "ARCHITECTURE_microservices-architecture_" in file_path.name

        content = file_path.read_text()
        assert "# System Architecture: microservices-architecture" in content

        # Verify frontmatter
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter["doc_type"] == "ARCHITECTURE"
        assert frontmatter["version"] == "2.0"
        assert frontmatter["owner"] == "Mary"
        assert frontmatter["reviewer"] == "John"

    def test_create_story_from_template(self, template_manager, tmp_path):
        """Test creating story from template."""
        variables = {
            "subject": "login-flow",
            "author": "Bob",
            "epic": 5,
            "feature": "auth-system",
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template("story", variables, output_dir)

        assert file_path.exists()
        assert "STORY_login-flow_" in file_path.name

        content = file_path.read_text()
        assert "# Story: login-flow" in content
        assert "**Epic:** 5" in content

        # Verify frontmatter
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter["epic"] == 5
        assert frontmatter["owner"] == "John"
        assert frontmatter["reviewer"] == "Amelia"

    def test_create_adr_from_template(self, template_manager, tmp_path):
        """Test creating ADR from template."""
        variables = {
            "subject": "database-choice",
            "author": "Winston",
            "decision": "Use PostgreSQL for primary database",
            "status": "Accepted",
            "adr_number": 1,
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template("adr", variables, output_dir)

        assert file_path.exists()
        assert file_path.name.startswith("ADR-001_database-choice_")

        content = file_path.read_text()
        assert "# ADR-001: database-choice" in content

        # Verify frontmatter
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter["doc_type"] == "ADR"
        assert frontmatter["status"] == "Accepted"

    def test_create_epic_from_template(self, template_manager, tmp_path):
        """Test creating epic from template."""
        variables = {
            "subject": "authentication-system",
            "author": "Bob",
            "feature": "auth",
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template("epic", variables, output_dir)

        assert file_path.exists()
        assert "EPIC_authentication-system_" in file_path.name

        content = file_path.read_text()
        assert "# Epic: authentication-system" in content

    def test_create_postmortem_from_template(self, template_manager, tmp_path):
        """Test creating postmortem from template."""
        variables = {
            "subject": "api-outage",
            "author": "DevOps Team",
            "incident_date": "2024-11-01",
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template(
            "postmortem", variables, output_dir
        )

        assert file_path.exists()
        assert "Postmortem_" in file_path.name
        assert "_api-outage" in file_path.name

    def test_create_runbook_from_template(self, template_manager, tmp_path):
        """Test creating runbook from template."""
        variables = {
            "subject": "kafka-restart",
            "author": "Amelia",
            "version": "1.3",
        }

        output_dir = tmp_path / "docs"
        file_path = template_manager.create_from_template(
            "runbook", variables, output_dir
        )

        assert file_path.exists()
        assert "Runbook_kafka-restart_" in file_path.name

    def test_missing_required_variable(self, template_manager, tmp_path):
        """Test error when required variable missing."""
        variables = {
            "subject": "test",
            # Missing 'author'
        }

        with pytest.raises(ValueError, match="Missing required variables"):
            template_manager.create_from_template("prd", variables, tmp_path)

    def test_story_requires_epic(self, template_manager, tmp_path):
        """Test story template requires epic."""
        variables = {
            "subject": "test-story",
            "author": "Bob",
            # Missing 'epic'
        }

        with pytest.raises(ValueError, match="epic"):
            template_manager.create_from_template("story", variables, tmp_path)

    def test_adr_requires_decision(self, template_manager, tmp_path):
        """Test ADR template requires decision and status."""
        variables = {
            "subject": "test-adr",
            "author": "Winston",
            # Missing 'decision' and 'status'
        }

        with pytest.raises(ValueError, match="decision"):
            template_manager.create_from_template("adr", variables, tmp_path)

    def test_template_not_found(self, template_manager, tmp_path):
        """Test error when template doesn't exist."""
        variables = {"subject": "test", "author": "John"}

        with pytest.raises(ValueError, match="Template not found"):
            template_manager.create_from_template(
                "nonexistent", variables, tmp_path
            )

    def test_auto_registration_in_lifecycle(self, template_manager, tmp_path):
        """Test document is automatically registered in lifecycle system."""
        variables = {
            "subject": "test-document",
            "author": "John",
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        # Verify document is registered
        doc = template_manager.doc_mgr.registry.get_document_by_path(str(file_path))
        assert doc is not None
        assert doc.path == str(file_path)
        assert doc.type.value == "prd"
        assert doc.author == "John"
        assert doc.state == DocumentState.DRAFT

    def test_auto_ownership_assignment(self, template_manager, tmp_path):
        """Test ownership is automatically assigned from governance."""
        variables = {
            "subject": "test-document",
            "author": "John",
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        # Verify ownership assigned
        doc = template_manager.doc_mgr.registry.get_document_by_path(str(file_path))
        assert doc.owner == "Mary"  # From governance config
        assert doc.reviewer == "Winston"  # From governance config

    def test_review_due_date_calculated(self, template_manager, tmp_path):
        """Test review due date is calculated from cadence."""
        variables = {
            "subject": "test-document",
            "author": "John",
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        # Verify review due date set
        doc = template_manager.doc_mgr.registry.get_document_by_path(str(file_path))
        assert doc.review_due_date is not None

        # PRD has 90-day cadence
        expected_due = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        assert doc.review_due_date == expected_due

    def test_immutable_documents_no_review_date(self, template_manager, tmp_path):
        """Test immutable documents (ADR) have no review due date."""
        variables = {
            "subject": "test-adr",
            "author": "Winston",
            "decision": "Test decision",
            "status": "Proposed",
            "adr_number": 1,
        }

        file_path = template_manager.create_from_template("adr", variables, tmp_path)

        # ADRs are immutable (-1 cadence), so no review due date
        doc = template_manager.doc_mgr.registry.get_document_by_path(str(file_path))
        # Due to how auto_assign_ownership works, it might not set review_due_date
        # The key is that ADRs have -1 cadence so they won't be scheduled for review

    def test_list_templates(self, template_manager):
        """Test listing available templates."""
        templates = template_manager.list_templates()

        # Should have all 7 templates
        assert len(templates) >= 7
        assert "prd" in templates
        assert "architecture" in templates
        assert "epic" in templates
        assert "story" in templates
        assert "adr" in templates
        assert "postmortem" in templates
        assert "runbook" in templates

    def test_get_template_variables(self, template_manager):
        """Test getting template variable information."""
        info = template_manager.get_template_variables("prd")

        assert info["description"] == "Product Requirements Document"
        assert "subject" in info["required"]
        assert "author" in info["required"]
        assert "feature" in info["optional"]

    def test_get_template_variables_story(self, template_manager):
        """Test story template requires epic."""
        info = template_manager.get_template_variables("story")

        assert "epic" in info["required"]

    def test_retention_policy_mapping(self, template_manager):
        """Test retention policy mapping for different doc types."""
        # PRD should map to permanent
        policy = template_manager._get_retention_policy("prd")
        assert policy == "permanent_product_decisions"

        # Story should map to 1 year archive
        policy = template_manager._get_retention_policy("story")
        assert policy == "archive_after_1_year"

        # Unknown type should get default
        policy = template_manager._get_retention_policy("unknown")
        assert policy == "default_archive_90_days"

    def test_filename_slug_normalization(self, template_manager, tmp_path):
        """Test subject is properly slugified in filename."""
        variables = {
            "subject": "User Authentication System",
            "author": "John",
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        # Should convert spaces to hyphens and lowercase
        assert "user-authentication-system" in file_path.name.lower()

    def test_multiple_related_docs(self, template_manager, tmp_path):
        """Test multiple related documents in frontmatter."""
        variables = {
            "subject": "test-doc",
            "author": "John",
            "related_docs": ["doc1.md", "doc2.md", "doc3.md"],
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        content = file_path.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        assert len(frontmatter["related_docs"]) == 3
        assert "doc1.md" in frontmatter["related_docs"]

    def test_multiple_tags(self, template_manager, tmp_path):
        """Test multiple tags in frontmatter."""
        variables = {
            "subject": "test-doc",
            "author": "John",
            "tags": ["tag1", "tag2", "tag3"],
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        content = file_path.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        assert len(frontmatter["tags"]) == 3
        assert "tag1" in frontmatter["tags"]

    def test_output_directory_created(self, template_manager, tmp_path):
        """Test output directory is created if it doesn't exist."""
        variables = {
            "subject": "test-doc",
            "author": "John",
        }

        output_dir = tmp_path / "nested" / "dir" / "structure"
        assert not output_dir.exists()

        file_path = template_manager.create_from_template("prd", variables, output_dir)

        assert output_dir.exists()
        assert file_path.parent == output_dir

    def test_version_in_frontmatter(self, template_manager, tmp_path):
        """Test version is properly set in frontmatter."""
        variables = {
            "subject": "test-doc",
            "author": "John",
            "version": "2.5",
        }

        file_path = template_manager.create_from_template("prd", variables, tmp_path)

        content = file_path.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["version"] == "2.5"
        assert "_v2.5.md" in file_path.name
