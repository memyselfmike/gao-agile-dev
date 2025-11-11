"""Tests for DocumentStructureManager.

Story 28.6: DocumentStructureManager unit tests
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from gao_dev.core.services.document_structure_manager import DocumentStructureManager
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.lifecycle.models import DocumentType


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project root."""
    return tmp_path


@pytest.fixture
def mock_doc_lifecycle():
    """Mock DocumentLifecycleManager."""
    return Mock()


@pytest.fixture
def mock_git():
    """Mock GitManager."""
    git = Mock()
    git.add_all = Mock()
    git.commit = Mock()
    return git


@pytest.fixture
def manager(temp_project, mock_doc_lifecycle, mock_git):
    """Create DocumentStructureManager instance."""
    return DocumentStructureManager(
        project_root=temp_project,
        doc_lifecycle=mock_doc_lifecycle,
        git_manager=mock_git,
    )


def test_init_validates_project_root(mock_doc_lifecycle, mock_git):
    """Test that initialization validates project root exists."""
    nonexistent_path = Path("/nonexistent/path/that/doesnt/exist")
    with pytest.raises(ValueError, match="Project root does not exist"):
        DocumentStructureManager(
            project_root=nonexistent_path,
            doc_lifecycle=mock_doc_lifecycle,
            git_manager=mock_git,
        )


def test_initialize_feature_folder_empty_name_raises(manager):
    """Test that empty feature name raises ValueError."""
    with pytest.raises(ValueError, match="feature_name cannot be empty"):
        manager.initialize_feature_folder("", ScaleLevel.LEVEL_2_SMALL_FEATURE)


def test_initialize_level_0_returns_none(manager, mock_git):
    """Level 0 should return None without creating folders."""
    result = manager.initialize_feature_folder("quick-fix", ScaleLevel.LEVEL_0_CHORE)

    assert result is None
    # No git commit
    mock_git.commit.assert_not_called()


def test_initialize_level_1_creates_bugs_dir(manager, temp_project, mock_git):
    """Level 1 should create bugs directory."""
    result = manager.initialize_feature_folder("bug-123", ScaleLevel.LEVEL_1_BUG_FIX)

    bugs_dir = temp_project / "docs" / "bugs"
    assert bugs_dir.exists()
    assert result == bugs_dir

    # Verify git commit
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once_with("docs(bugs): initialize bugs directory")


def test_initialize_level_1_idempotent(manager, temp_project, mock_git):
    """Level 1 initialization should be idempotent."""
    # First call
    result1 = manager.initialize_feature_folder("bug-1", ScaleLevel.LEVEL_1_BUG_FIX)
    # Second call
    result2 = manager.initialize_feature_folder("bug-2", ScaleLevel.LEVEL_1_BUG_FIX)

    bugs_dir = temp_project / "docs" / "bugs"
    assert result1 == bugs_dir
    assert result2 == bugs_dir
    assert bugs_dir.exists()
    # Should have been called twice (once per call)
    assert mock_git.commit.call_count == 2


def test_initialize_level_2_small_feature(
    manager, temp_project, mock_doc_lifecycle, mock_git
):
    """Level 2 should create feature folder with PRD and stories."""
    manager.initialize_feature_folder("my-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "my-feature"
    assert feature_path.exists()
    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "CHANGELOG.md").exists()
    assert (feature_path / "stories").exists()
    assert (feature_path / "stories").is_dir()

    # Verify PRD content is lightweight
    prd_content = (feature_path / "PRD.md").read_text()
    assert "# my-feature - Product Requirements Document" in prd_content
    assert "## Summary" in prd_content
    assert "## User Stories" in prd_content
    # Should NOT have full template sections
    assert "## Problem Statement" not in prd_content
    assert "## Solution Approach" not in prd_content

    # Verify CHANGELOG content
    changelog_content = (feature_path / "CHANGELOG.md").read_text()
    assert "# Changelog" in changelog_content
    assert "## Unreleased" in changelog_content

    # Verify registration
    mock_doc_lifecycle.register_document.assert_called_once()
    call_args = mock_doc_lifecycle.register_document.call_args
    assert call_args[1]["path"] == feature_path / "PRD.md"
    assert call_args[1]["doc_type"] == DocumentType.PRD.value
    assert call_args[1]["metadata"]["feature"] == "my-feature"
    assert call_args[1]["metadata"]["scale_level"] == 2

    # Verify git commit (Story 33.1: Enhanced commit message)
    mock_git.add_all.assert_called_once()
    commit_message = mock_git.commit.call_args[0][0]
    assert "docs(my-feature): initialize feature folder (Level 2)" in commit_message
    assert "Created feature structure with scale level 2" in commit_message
    assert "Includes: PRD, Architecture, README, QA, and folder structure" in commit_message


def test_initialize_level_3_medium_feature(
    manager, temp_project, mock_doc_lifecycle, mock_git
):
    """Level 3 should create feature folder with additional structure."""
    manager.initialize_feature_folder(
        "auth-feature", ScaleLevel.LEVEL_3_MEDIUM_FEATURE
    )

    feature_path = temp_project / "docs" / "features" / "auth-feature"
    assert feature_path.exists()

    # Level 2 structure
    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "CHANGELOG.md").exists()
    assert (feature_path / "stories").exists()

    # Level 3 additions
    assert (feature_path / "ARCHITECTURE.md").exists()
    assert (feature_path / "epics").exists()
    assert (feature_path / "retrospectives").exists()
    assert (feature_path / "epics").is_dir()
    assert (feature_path / "retrospectives").is_dir()

    # Verify PRD is full template
    prd_content = (feature_path / "PRD.md").read_text()
    assert "## Problem Statement" in prd_content
    assert "## Solution Approach" in prd_content
    assert "## Technical Requirements" in prd_content
    assert "## Dependencies" in prd_content
    assert "## Timeline" in prd_content
    assert "## Risk Assessment" in prd_content

    # Verify ARCHITECTURE content
    arch_content = (feature_path / "ARCHITECTURE.md").read_text()
    assert "# auth-feature - Architecture" in arch_content
    assert "## System Overview" in arch_content
    assert "## Component Diagram" in arch_content
    assert "## Data Models" in arch_content
    assert "## API Design" in arch_content

    # Verify registration
    mock_doc_lifecycle.register_document.assert_called_once()

    # Verify git commit (Story 33.1: Enhanced commit message)
    commit_message = mock_git.commit.call_args[0][0]
    assert "docs(auth-feature): initialize feature folder (Level 3)" in commit_message
    assert "Created feature structure with scale level 3" in commit_message
    assert "Includes: PRD, Architecture, README, QA, and folder structure" in commit_message


def test_initialize_level_4_greenfield(
    manager, temp_project, mock_doc_lifecycle, mock_git
):
    """Level 4 should create feature folder with ceremonies and migration guide."""
    manager.initialize_feature_folder("new-app", ScaleLevel.LEVEL_4_GREENFIELD)

    feature_path = temp_project / "docs" / "features" / "new-app"
    assert feature_path.exists()

    # Level 2 + 3 structure
    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "CHANGELOG.md").exists()
    assert (feature_path / "stories").exists()
    assert (feature_path / "ARCHITECTURE.md").exists()
    assert (feature_path / "epics").exists()
    assert (feature_path / "retrospectives").exists()

    # Level 4 additions
    assert (feature_path / "ceremonies").exists()
    assert (feature_path / "MIGRATION_GUIDE.md").exists()
    assert (feature_path / "ceremonies").is_dir()

    # Verify MIGRATION_GUIDE content
    migration_content = (feature_path / "MIGRATION_GUIDE.md").read_text()
    assert "# Migration Guide" in migration_content
    assert "TBD" in migration_content

    # Verify registration
    mock_doc_lifecycle.register_document.assert_called_once()

    # Verify git commit (Story 33.1: Enhanced commit message)
    commit_message = mock_git.commit.call_args[0][0]
    assert "docs(new-app): initialize feature folder (Level 4)" in commit_message
    assert "Created feature structure with scale level 4" in commit_message
    assert "Includes: PRD, Architecture, README, QA, and folder structure" in commit_message


def test_update_global_docs_invalid_type_raises(manager):
    """Test that invalid update_type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid update_type"):
        manager.update_global_docs("feature", 1, "invalid")


def test_update_global_docs_planned(manager, temp_project, mock_git):
    """Test update_global_docs with 'planned' type."""
    # Create initial PRD
    prd_path = temp_project / "docs" / "PRD.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text("# Product Requirements\n\n")

    manager.update_global_docs("my-feature", 1, "planned")

    # Verify PRD updated
    prd_content = prd_path.read_text()
    assert "- Epic 1: my-feature - Planned\n" in prd_content

    # Verify git commit
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once_with(
        "docs(global): update planned for my-feature"
    )


def test_update_global_docs_planned_creates_prd_if_missing(
    manager, temp_project, mock_git
):
    """Test that update_global_docs creates PRD if it doesn't exist."""
    prd_path = temp_project / "docs" / "PRD.md"
    assert not prd_path.exists()

    manager.update_global_docs("my-feature", 1, "planned")

    # Verify PRD created
    assert prd_path.exists()
    prd_content = prd_path.read_text()
    assert "# Product Requirements" in prd_content
    assert "- Epic 1: my-feature - Planned\n" in prd_content


def test_update_global_docs_planned_updates_existing_epic(
    manager, temp_project, mock_git
):
    """Test that update_global_docs updates existing epic entry."""
    # Create PRD with existing epic
    prd_path = temp_project / "docs" / "PRD.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(
        "# Product Requirements\n\n- Epic 1: my-feature - In Progress\n"
    )

    manager.update_global_docs("my-feature", 1, "planned")

    # Verify epic updated (not duplicated)
    prd_content = prd_path.read_text()
    assert prd_content.count("Epic 1:") == 1
    assert "- Epic 1: my-feature - Planned" in prd_content
    assert "In Progress" not in prd_content


def test_update_global_docs_architected(manager, temp_project, mock_git):
    """Test update_global_docs with 'architected' type."""
    # Create initial ARCHITECTURE
    arch_path = temp_project / "docs" / "ARCHITECTURE.md"
    arch_path.parent.mkdir(parents=True, exist_ok=True)
    arch_path.write_text("# Architecture\n\n")

    manager.update_global_docs("my-feature", 1, "architected")

    # Verify ARCHITECTURE updated
    arch_content = arch_path.read_text()
    assert "## Epic 1: my-feature" in arch_content
    assert "See [Feature Architecture](features/my-feature/ARCHITECTURE.md)" in arch_content

    # Verify git commit
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once_with(
        "docs(global): update architected for my-feature"
    )


def test_update_global_docs_completed(manager, temp_project, mock_git):
    """Test update_global_docs with 'completed' type."""
    # Create initial docs
    prd_path = temp_project / "docs" / "PRD.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text("# Product Requirements\n\n- Epic 1: my-feature - In Progress\n")

    changelog_path = temp_project / "docs" / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## Unreleased\n\n")

    manager.update_global_docs("my-feature", 1, "completed")

    # Verify PRD updated to Completed
    prd_content = prd_path.read_text()
    assert "- Epic 1: my-feature - Completed" in prd_content

    # Verify CHANGELOG updated
    changelog_content = changelog_path.read_text()
    assert "## Unreleased\n- Epic 1: my-feature completed\n" in changelog_content

    # Verify git commit
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once_with(
        "docs(global): update completed for my-feature"
    )


def test_update_global_docs_completed_creates_changelog_if_missing(
    manager, temp_project, mock_git
):
    """Test that completed update creates CHANGELOG if it doesn't exist."""
    prd_path = temp_project / "docs" / "PRD.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text("# Product Requirements\n\n")

    changelog_path = temp_project / "docs" / "CHANGELOG.md"
    assert not changelog_path.exists()

    manager.update_global_docs("my-feature", 1, "completed")

    # Verify CHANGELOG created
    assert changelog_path.exists()
    changelog_content = changelog_path.read_text()
    assert "# Changelog" in changelog_content
    assert "## Unreleased" in changelog_content
    assert "- Epic 1: my-feature completed" in changelog_content


def test_template_rendering_lightweight(manager):
    """Test that lightweight PRD template is generated correctly."""
    template = manager._prd_template("test-feature", "lightweight")

    assert "# test-feature - Product Requirements Document" in template
    assert "## Summary" in template
    assert "## User Stories" in template
    assert "## Acceptance Criteria" in template
    assert "## Success Metrics" in template

    # Should NOT have full template sections
    assert "## Problem Statement" not in template
    assert "## Solution Approach" not in template
    assert "## Technical Requirements" not in template


def test_template_rendering_full(manager):
    """Test that full PRD template is generated correctly."""
    template = manager._prd_template("test-feature", "full")

    assert "# test-feature - Product Requirements Document" in template
    # All lightweight sections
    assert "## Summary" in template
    assert "## User Stories" in template
    assert "## Acceptance Criteria" in template
    assert "## Success Metrics" in template

    # Additional full template sections
    assert "## Problem Statement" in template
    assert "## Solution Approach" in template
    assert "## Technical Requirements" in template
    assert "## Dependencies" in template
    assert "## Timeline" in template
    assert "## Risk Assessment" in template


def test_template_rendering_architecture(manager):
    """Test that architecture template is generated correctly."""
    template = manager._architecture_template("test-feature")

    assert "# test-feature - Architecture" in template
    assert "## System Overview" in template
    assert "## Component Diagram" in template
    assert "## Data Models" in template
    assert "## API Design" in template
    assert "## Integration Points" in template
    assert "## Performance Considerations" in template


def test_create_file_creates_parent_dirs(manager, temp_project):
    """Test that _create_file creates parent directories."""
    nested_path = (
        temp_project / "docs" / "deeply" / "nested" / "structure" / "file.md"
    )

    manager._create_file(nested_path, "test content")

    assert nested_path.exists()
    assert nested_path.read_text() == "test content"
    assert nested_path.parent.exists()


def test_update_changelog_without_unreleased_section(manager, temp_project):
    """Test that _update_changelog adds Unreleased section if missing."""
    changelog_path = temp_project / "docs" / "CHANGELOG.md"
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    changelog_path.write_text("# Changelog\n\n## v1.0.0\n- Initial release\n")

    manager._update_changelog("my-feature", 1)

    changelog_content = changelog_path.read_text()
    assert "## Unreleased\n- Epic 1: my-feature completed\n" in changelog_content
    assert "## v1.0.0" in changelog_content  # Old section preserved


# ============================================================================
# STORY 33.1: QA/ FOLDER, README.md, AND auto_commit TESTS
# ============================================================================


def test_qa_folder_created_level_2(manager, temp_project):
    """Story 33.1: QA/ folder should be created for Level 2 features."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    qa_path = feature_path / "QA"

    # AC1: QA/ folder created
    assert qa_path.exists()
    assert qa_path.is_dir()


def test_qa_folder_created_level_3(manager, temp_project):
    """Story 33.1: QA/ folder should be created for Level 3 features."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    qa_path = feature_path / "QA"

    # AC1: QA/ folder created for Level 3
    assert qa_path.exists()
    assert qa_path.is_dir()


def test_qa_folder_created_level_4(manager, temp_project):
    """Story 33.1: QA/ folder should be created for Level 4 features."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_4_GREENFIELD)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    qa_path = feature_path / "QA"

    # AC1: QA/ folder created for Level 4
    assert qa_path.exists()
    assert qa_path.is_dir()


def test_qa_folder_committed_with_auto_commit_true(manager, temp_project, mock_git):
    """Story 33.1: QA/ folder should be included in git commit when auto_commit=True."""
    manager.initialize_feature_folder(
        "test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE, auto_commit=True
    )

    # Verify git commit was called
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once()

    # Verify QA/ folder exists
    feature_path = temp_project / "docs" / "features" / "test-feature"
    assert (feature_path / "QA").exists()


def test_readme_created_level_2(manager, temp_project):
    """Story 33.1: README.md should be created for Level 2 features."""
    manager.initialize_feature_folder("my-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "my-feature"
    readme_path = feature_path / "README.md"

    # AC2: README.md exists
    assert readme_path.exists()


def test_readme_contains_feature_name(manager, temp_project):
    """Story 33.1: README.md should contain feature name."""
    manager.initialize_feature_folder("auth-system", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "auth-system"
    readme_content = (feature_path / "README.md").read_text()

    # AC2: README contains feature name
    assert "auth-system" in readme_content
    assert "# auth-system" in readme_content


def test_readme_contains_description(manager, temp_project):
    """Story 33.1: README.md should contain description."""
    manager.initialize_feature_folder(
        "payment-gateway",
        ScaleLevel.LEVEL_2_SMALL_FEATURE,
        description="Payment processing integration",
    )

    feature_path = temp_project / "docs" / "features" / "payment-gateway"
    readme_content = (feature_path / "README.md").read_text()

    # AC2: README contains description
    assert "Payment processing integration" in readme_content
    assert "**Description:**" in readme_content


def test_readme_contains_scale_level(manager, temp_project):
    """Story 33.1: README.md should contain scale level."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    readme_content = (feature_path / "README.md").read_text()

    # AC2: README contains scale level
    assert "**Scale Level:** 3" in readme_content


def test_readme_contains_structure_diagram(manager, temp_project):
    """Story 33.1: README.md should contain structure diagram."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    readme_content = (feature_path / "README.md").read_text()

    # AC2: README contains structure diagram
    assert "## Structure" in readme_content
    assert "test-feature/" in readme_content
    assert "QA/" in readme_content
    assert "epics/" in readme_content


def test_readme_sections_match_template(manager, temp_project):
    """Story 33.1: README.md sections should match template."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    readme_content = (feature_path / "README.md").read_text()

    # AC2: All required sections present
    assert "## Overview" in readme_content
    assert "## Documents" in readme_content
    assert "## Structure" in readme_content
    assert "## Epics" in readme_content
    assert "## Contributing" in readme_content
    assert "## Quality Assurance" in readme_content


def test_readme_conditional_retrospectives_level_3(manager, temp_project):
    """Story 33.1: README.md should include retrospectives section for Level 3."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    readme_content = (feature_path / "README.md").read_text()

    # Retrospectives should be present for Level 3
    assert "retrospectives/" in readme_content


def test_readme_conditional_ceremonies_level_4(manager, temp_project):
    """Story 33.1: README.md should include ceremonies section for Level 4."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_4_GREENFIELD)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    readme_content = (feature_path / "README.md").read_text()

    # Ceremonies should be present for Level 4
    assert "ceremonies/" in readme_content


def test_readme_no_ceremonies_level_2(manager, temp_project):
    """Story 33.1: README.md should not include ceremonies section for Level 2."""
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    feature_path = temp_project / "docs" / "features" / "test-feature"
    readme_content = (feature_path / "README.md").read_text()

    # Ceremonies should NOT be present for Level 2
    assert "ceremonies/" not in readme_content


def test_auto_commit_true_commits_to_git(manager, temp_project, mock_git):
    """Story 33.1: auto_commit=True should commit to git."""
    manager.initialize_feature_folder(
        "test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE, auto_commit=True
    )

    # AC3: Git commit called when auto_commit=True
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once()

    # Verify commit message format
    commit_message = mock_git.commit.call_args[0][0]
    assert "docs(test-feature):" in commit_message
    assert "initialize feature folder" in commit_message


def test_auto_commit_false_skips_git_commit(manager, temp_project, mock_git):
    """Story 33.1: auto_commit=False should skip git commit."""
    manager.initialize_feature_folder(
        "test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE, auto_commit=False
    )

    # AC3: Git commit NOT called when auto_commit=False
    mock_git.add_all.assert_not_called()
    mock_git.commit.assert_not_called()


def test_auto_commit_false_still_creates_files(manager, temp_project):
    """Story 33.1: auto_commit=False should still create all files."""
    result = manager.initialize_feature_folder(
        "test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE, auto_commit=False
    )

    feature_path = temp_project / "docs" / "features" / "test-feature"

    # AC3: All files created even when auto_commit=False
    assert result == feature_path
    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "README.md").exists()
    assert (feature_path / "CHANGELOG.md").exists()
    assert (feature_path / "QA").exists()
    assert (feature_path / "stories").exists()


def test_auto_commit_returns_feature_path_both_cases(manager, temp_project):
    """Story 33.1: Feature path should be returned for both auto_commit values."""
    # With auto_commit=True
    result_true = manager.initialize_feature_folder(
        "feature-1", ScaleLevel.LEVEL_2_SMALL_FEATURE, auto_commit=True
    )

    # With auto_commit=False
    result_false = manager.initialize_feature_folder(
        "feature-2", ScaleLevel.LEVEL_2_SMALL_FEATURE, auto_commit=False
    )

    # AC3: Both return valid feature paths
    assert result_true is not None
    assert result_false is not None
    assert result_true.name == "feature-1"
    assert result_false.name == "feature-2"


def test_backward_compatibility_default_auto_commit(manager, temp_project, mock_git):
    """Story 33.1: auto_commit should default to True for backward compatibility."""
    # Call without auto_commit parameter (should default to True)
    manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)

    # AC4: Git commit should be called by default
    mock_git.add_all.assert_called_once()
    mock_git.commit.assert_called_once()


def test_backward_compatibility_no_description_parameter(manager, temp_project):
    """Story 33.1: description parameter should be optional for backward compatibility."""
    # Call without description parameter
    result = manager.initialize_feature_folder(
        "test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE
    )

    # AC4: Should work without description
    assert result is not None
    feature_path = temp_project / "docs" / "features" / "test-feature"
    assert (feature_path / "README.md").exists()

    # Default description should be used
    readme_content = (feature_path / "README.md").read_text()
    assert "Feature: test-feature" in readme_content


def test_backward_compatibility_commit_message_format(manager, temp_project, mock_git):
    """Story 33.1: Git commit message format should be maintained."""
    manager.initialize_feature_folder("my-feature", ScaleLevel.LEVEL_3_MEDIUM_FEATURE)

    # AC4: Commit message should follow expected format
    mock_git.commit.assert_called_once()
    commit_message = mock_git.commit.call_args[0][0]

    assert "docs(my-feature):" in commit_message
    assert "initialize feature folder" in commit_message
    assert "Level 3" in commit_message
