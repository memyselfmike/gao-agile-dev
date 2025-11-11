"""Tests for validate-structure CLI command.

Epic: 33 - Atomic Feature Operations
Story: 33.3 - CLI Commands
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from gao_dev.cli.validate_structure_command import validate_structure


@pytest.fixture
def test_project(tmp_path):
    """Create temporary test project with features."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create .gao-dev directory
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()

    # Create git repo
    git_dir = project_root / ".git"
    git_dir.mkdir()

    # Create features directory
    features_dir = project_root / "docs" / "features"
    features_dir.mkdir(parents=True)

    # Create compliant feature
    compliant = features_dir / "compliant-feature"
    compliant.mkdir()
    (compliant / "PRD.md").write_text("# PRD")
    (compliant / "ARCHITECTURE.md").write_text("# Architecture")
    (compliant / "README.md").write_text("# README")
    (compliant / "epics").mkdir()
    (compliant / "QA").mkdir()

    # Create non-compliant feature (missing files)
    non_compliant = features_dir / "non-compliant"
    non_compliant.mkdir()
    (non_compliant / "PRD.md").write_text("# PRD")
    # Missing ARCHITECTURE.md, README.md, epics/, QA/

    # Create partially compliant feature
    partial = features_dir / "partial"
    partial.mkdir()
    (partial / "PRD.md").write_text("# PRD")
    (partial / "ARCHITECTURE.md").write_text("# Architecture")
    (partial / "README.md").write_text("# README")
    (partial / "epics").mkdir()
    # Missing QA/

    return project_root


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestValidateStructureCommand:
    """Tests for validate-structure command."""

    def test_validate_compliant_feature(self, test_project, runner, monkeypatch):
        """Test validating a compliant feature."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "compliant-feature"])

        assert result.exit_code == 0
        assert "compliant" in result.output.lower()
        assert "compliant-feature" in result.output

    def test_validate_non_compliant_feature(self, test_project, runner, monkeypatch):
        """Test validating a non-compliant feature."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        assert "violation" in result.output.lower() or "missing" in result.output.lower()
        assert "non-compliant" in result.output

    def test_validate_all_features(self, test_project, runner, monkeypatch):
        """Test validating all features."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--all"])

        # Should show all three features
        assert "compliant-feature" in result.output
        assert "non-compliant" in result.output
        assert "partial" in result.output

        # Exit code 1 because not all are compliant
        assert result.exit_code == 1

    def test_validate_all_features_all_compliant(self, tmp_path, runner, monkeypatch):
        """Test validating all features when all are compliant."""
        # Create project with only compliant features
        project_root = tmp_path / "all_compliant_project"
        project_root.mkdir()

        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        git_dir = project_root / ".git"
        git_dir.mkdir()

        features_dir = project_root / "docs" / "features"
        features_dir.mkdir(parents=True)

        # Create two compliant features
        for name in ["feature1", "feature2"]:
            feature_dir = features_dir / name
            feature_dir.mkdir()
            (feature_dir / "PRD.md").write_text("# PRD")
            (feature_dir / "ARCHITECTURE.md").write_text("# Architecture")
            (feature_dir / "README.md").write_text("# README")
            (feature_dir / "epics").mkdir()
            (feature_dir / "QA").mkdir()

        monkeypatch.chdir(project_root)

        result = runner.invoke(validate_structure, ["--all"])

        assert result.exit_code == 0
        assert "All features are compliant" in result.output

    def test_validate_feature_not_found(self, test_project, runner, monkeypatch):
        """Test error when feature doesn't exist."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_validate_auto_detect_from_cwd(self, test_project, runner, monkeypatch):
        """Test auto-detecting feature from current directory."""
        feature_dir = test_project / "docs" / "features" / "compliant-feature"
        monkeypatch.chdir(feature_dir)

        result = runner.invoke(validate_structure, [])

        assert result.exit_code == 0
        assert "compliant" in result.output.lower()

    def test_validate_auto_detect_non_compliant(self, test_project, runner, monkeypatch):
        """Test auto-detecting non-compliant feature from CWD."""
        feature_dir = test_project / "docs" / "features" / "non-compliant"
        monkeypatch.chdir(feature_dir)

        result = runner.invoke(validate_structure, [])

        assert result.exit_code == 1
        assert "violation" in result.output.lower() or "missing" in result.output.lower()

    def test_validate_missing_required_files(self, test_project, runner, monkeypatch):
        """Test violation messages for missing files."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        assert "ARCHITECTURE.md" in result.output or "architecture" in result.output.lower()
        assert "README.md" in result.output or "readme" in result.output.lower()

    def test_validate_missing_required_folders(self, test_project, runner, monkeypatch):
        """Test violation messages for missing folders."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        assert "epics" in result.output.lower()
        assert "QA" in result.output or "qa" in result.output.lower()

    def test_validate_rich_output_violations(self, test_project, runner, monkeypatch):
        """Test Rich formatted output for violations."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        assert "violation" in result.output.lower() or "missing" in result.output.lower()
        # Check for suggested fixes
        assert "fix" in result.output.lower() or "suggest" in result.output.lower()

    def test_validate_suggested_fixes(self, test_project, runner, monkeypatch):
        """Test suggested fixes are provided."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        assert "missing files" in result.output.lower() or "add missing" in result.output.lower()


class TestValidateStructureEdgeCases:
    """Edge case tests for validate-structure command."""

    def test_validate_outside_project(self, tmp_path, runner, monkeypatch):
        """Test error when not in a GAO-Dev project."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        result = runner.invoke(validate_structure, ["--feature", "test"])

        assert result.exit_code != 0
        assert "error" in result.output.lower() or "not in a gao-dev project" in result.output.lower()

    def test_validate_no_features_directory(self, tmp_path, runner, monkeypatch):
        """Test behavior when no features directory exists."""
        project_root = tmp_path / "no_features_project"
        project_root.mkdir()

        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        git_dir = project_root / ".git"
        git_dir.mkdir()

        monkeypatch.chdir(project_root)

        result = runner.invoke(validate_structure, ["--all"])

        # Should handle gracefully
        assert result.exit_code == 0
        assert "No features" in result.output or "not found" in result.output.lower()

    def test_validate_without_arguments(self, test_project, runner, monkeypatch):
        """Test error when no arguments provided outside feature directory."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, [])

        # Should prompt for --feature or --all
        assert "Specify --feature" in result.output or "specify" in result.output.lower()

    def test_validate_exit_codes(self, test_project, runner, monkeypatch):
        """Test correct exit codes."""
        monkeypatch.chdir(test_project)

        # Compliant: exit 0
        result1 = runner.invoke(validate_structure, ["--feature", "compliant-feature"])
        assert result1.exit_code == 0

        # Non-compliant: exit 1
        result2 = runner.invoke(validate_structure, ["--feature", "non-compliant"])
        assert result2.exit_code == 1

    def test_validate_partial_compliance(self, test_project, runner, monkeypatch):
        """Test feature with some violations."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "partial"])

        assert result.exit_code == 1
        assert "QA" in result.output or "qa" in result.output.lower()
        # Should NOT complain about files that exist
        assert "PRD" not in result.output or "prd.md" not in result.output.lower() or "missing required file: prd" not in result.output.lower()

    def test_validate_auto_detect_subdirectory(self, test_project, runner, monkeypatch):
        """Test auto-detection from subdirectory of feature."""
        epic_dir = test_project / "docs" / "features" / "compliant-feature" / "epics"
        epic_dir.mkdir(exist_ok=True)
        monkeypatch.chdir(epic_dir)

        result = runner.invoke(validate_structure, [])

        # Should detect parent feature
        assert result.exit_code == 0
        assert "compliant" in result.output.lower()


class TestValidateStructureOutput:
    """Tests for output formatting."""

    def test_validate_clear_violation_messages(self, test_project, runner, monkeypatch):
        """Test violation messages are clear."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        # Should list each violation
        assert "ARCHITECTURE" in result.output or "architecture" in result.output.lower()
        assert "README" in result.output or "readme" in result.output.lower()

    def test_validate_actionable_suggestions(self, test_project, runner, monkeypatch):
        """Test suggestions are actionable."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "non-compliant"])

        assert result.exit_code == 1
        # Should provide next steps
        assert "add" in result.output.lower() or "create" in result.output.lower() or "missing" in result.output.lower()

    def test_validate_success_message_format(self, test_project, runner, monkeypatch):
        """Test success message formatting."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(validate_structure, ["--feature", "compliant-feature"])

        assert result.exit_code == 0
        assert "compliant" in result.output.lower()
        assert "compliant-feature" in result.output
