"""Tests for FeaturePathResolver.

Epic: 32 - State Service Integration
Story: 32.4 - Create FeaturePathResolver

Coverage:
- 6-level priority resolution
- WorkflowContext integration
- Path generation (15+ path types)
- Error handling
- Cross-platform paths
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from gao_dev.core.services.feature_path_resolver import FeaturePathResolver
from gao_dev.core.services.feature_state_service import (
    FeatureStateService,
    Feature,
    FeatureScope,
    FeatureStatus,
)
from gao_dev.core.models.workflow_context import WorkflowContext


@pytest.fixture
def mock_feature_service():
    """Mock FeatureStateService for testing."""
    service = Mock(spec=FeatureStateService)
    return service


@pytest.fixture
def resolver(mock_feature_service, tmp_path):
    """Create FeaturePathResolver instance."""
    return FeaturePathResolver(project_root=tmp_path, feature_service=mock_feature_service)


class TestResolveFeatureName:
    """Test resolve_feature_name() - 6-level priority resolution."""

    # ========================================
    # Priority 1: Explicit parameter
    # ========================================

    def test_priority_1_explicit_parameter_valid(self, resolver, mock_feature_service):
        """Priority 1: Explicit parameter (valid feature)."""
        # Arrange
        mock_feature_service.get_feature.return_value = {"name": "user-auth"}
        params = {"feature_name": "user-auth"}

        # Act
        result = resolver.resolve_feature_name(params, None)

        # Assert
        assert result == "user-auth"
        mock_feature_service.get_feature.assert_called_once_with("user-auth")

    def test_priority_1_explicit_parameter_invalid(self, resolver, mock_feature_service):
        """Priority 1: Explicit parameter (invalid feature raises error)."""
        # Arrange
        mock_feature_service.get_feature.return_value = None
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
            Feature(
                name="payments",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]
        params = {"feature_name": "nonexistent"}

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            resolver.resolve_feature_name(params, None)

        error_msg = str(exc_info.value)
        assert "Feature 'nonexistent' does not exist" in error_msg
        assert "mvp, payments" in error_msg
        assert "gao-dev create-feature nonexistent" in error_msg

    # ========================================
    # Priority 2: WorkflowContext
    # ========================================

    def test_priority_2_workflow_context(self, resolver):
        """Priority 2: WorkflowContext.metadata['feature_name']."""
        # Arrange
        context = WorkflowContext(initial_prompt="test", metadata={"feature_name": "mvp"})
        params = {}

        # Act
        result = resolver.resolve_feature_name(params, context)

        # Assert
        assert result == "mvp"

    def test_priority_2_context_overrides_cwd(self, resolver, tmp_path, mock_feature_service):
        """Priority 2: Context takes precedence over CWD."""
        # Arrange - Create feature directory structure
        feature_dir = tmp_path / "docs" / "features" / "user-auth"
        feature_dir.mkdir(parents=True)

        context = WorkflowContext(initial_prompt="test", metadata={"feature_name": "mvp"})
        params = {}

        # Act - Even if we're in user-auth directory, context wins
        with patch("pathlib.Path.cwd", return_value=feature_dir):
            result = resolver.resolve_feature_name(params, context)

        # Assert
        assert result == "mvp"  # Context value, not CWD value

    # ========================================
    # Priority 3: Current working directory
    # ========================================

    def test_priority_3_cwd_in_feature_folder(self, resolver, tmp_path, mock_feature_service):
        """Priority 3: CWD in feature folder."""
        # Arrange
        feature_dir = tmp_path / "docs" / "features" / "user-auth"
        feature_dir.mkdir(parents=True)

        mock_feature_service.get_feature.return_value = {"name": "user-auth"}
        params = {}

        # Act
        with patch("pathlib.Path.cwd", return_value=feature_dir):
            result = resolver.resolve_feature_name(params, None)

        # Assert
        assert result == "user-auth"
        mock_feature_service.get_feature.assert_called_once_with("user-auth")

    def test_priority_3_cwd_not_in_feature_folder(self, resolver, tmp_path, mock_feature_service):
        """Priority 3: CWD not in feature folder (skips to next priority)."""
        # Arrange - CWD is project root, not in features/
        mock_feature_service.list_features.return_value = [
            Feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]
        params = {}

        # Act
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = resolver.resolve_feature_name(params, None)

        # Assert - Should skip to Priority 4 (single feature detection)
        assert result == "user-auth"

    # ========================================
    # Priority 4: Single feature detection
    # ========================================

    def test_priority_4_single_feature(self, resolver, mock_feature_service):
        """Priority 4: Single feature detection (excluding MVP)."""
        # Arrange - Only one non-MVP feature
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
            Feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]
        params = {}

        # Act
        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            result = resolver.resolve_feature_name(params, None)

        # Assert
        assert result == "user-auth"

    def test_priority_4_multiple_features_skips_to_error(self, resolver, mock_feature_service):
        """Priority 4: Multiple features (skips to error)."""
        # Arrange - Multiple non-MVP features
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
            Feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
            Feature(
                name="payments",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]
        mock_feature_service.get_feature.return_value = None  # For MVP check
        params = {}

        # Act & Assert
        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_feature_name(params, None)

        error_msg = str(exc_info.value)
        assert "Cannot resolve feature_name. Multiple features exist" in error_msg
        assert "mvp, payments, user-auth" in error_msg

    # ========================================
    # Priority 5: MVP detection
    # ========================================

    def test_priority_5_mvp_only_feature(self, resolver, mock_feature_service):
        """Priority 5: MVP detection (only feature)."""
        # Arrange - Only MVP exists
        mock_feature_service.get_feature.return_value = {"name": "mvp"}
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
        ]
        params = {}

        # Act
        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            result = resolver.resolve_feature_name(params, None)

        # Assert
        assert result == "mvp"

    def test_priority_5_mvp_plus_other_features_returns_single_feature(
        self, resolver, mock_feature_service
    ):
        """Priority 4 catches single non-MVP feature (MVP + user-auth => user-auth)."""
        # Arrange - MVP + single other feature
        # This should be caught by Priority 4, not reach Priority 5
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
            Feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]
        params = {}

        # Act
        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            result = resolver.resolve_feature_name(params, None)

        # Assert - Priority 4 catches this (single non-MVP feature)
        assert result == "user-auth"

    # ========================================
    # Priority 6: Error with helpful message
    # ========================================

    def test_priority_6_error_no_features(self, resolver, mock_feature_service):
        """Priority 6: Error when no features exist."""
        # Arrange
        mock_feature_service.get_feature.return_value = None
        mock_feature_service.list_features.return_value = []
        params = {}

        # Act & Assert
        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_feature_name(params, None)

        error_msg = str(exc_info.value)
        assert "No features exist in this project" in error_msg
        assert "gao-dev create-feature" in error_msg

    def test_priority_6_error_multiple_features_helpful_message(
        self, resolver, mock_feature_service
    ):
        """Priority 6: Error with helpful message for multiple features."""
        # Arrange
        mock_feature_service.get_feature.return_value = None
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
            Feature(
                name="payments",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
            Feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]
        params = {}

        # Act & Assert
        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_feature_name(params, None)

        error_msg = str(exc_info.value)
        assert "Cannot resolve feature_name. Multiple features exist" in error_msg
        assert "--feature-name <name>" in error_msg
        assert "cd docs/features/<name>" in error_msg
        assert "- mvp" in error_msg
        assert "- payments" in error_msg
        assert "- user-auth" in error_msg


class TestGenerateFeaturePath:
    """Test generate_feature_path() - Path generation."""

    # ========================================
    # Feature-level documents
    # ========================================

    def test_feature_level_prd_path(self, resolver):
        """Generate PRD path."""
        path = resolver.generate_feature_path("user-auth", "prd")
        assert path == Path("docs/features/user-auth/PRD.md")

    def test_feature_level_architecture_path(self, resolver):
        """Generate Architecture path."""
        path = resolver.generate_feature_path("mvp", "architecture")
        assert path == Path("docs/features/mvp/ARCHITECTURE.md")

    def test_feature_level_readme_path(self, resolver):
        """Generate README path."""
        path = resolver.generate_feature_path("payments", "readme")
        assert path == Path("docs/features/payments/README.md")

    def test_feature_level_epics_overview_path(self, resolver):
        """Generate EPICS overview path."""
        path = resolver.generate_feature_path("user-auth", "epics_overview")
        assert path == Path("docs/features/user-auth/EPICS.md")

    # ========================================
    # Feature-level folders
    # ========================================

    def test_feature_level_qa_folder_path(self, resolver):
        """Generate QA folder path."""
        path = resolver.generate_feature_path("user-auth", "qa_folder")
        assert path == Path("docs/features/user-auth/QA")

    def test_feature_level_retrospectives_folder_path(self, resolver):
        """Generate retrospectives folder path."""
        path = resolver.generate_feature_path("mvp", "retrospectives_folder")
        assert path == Path("docs/features/mvp/retrospectives")

    def test_feature_level_feature_directory_path(self, resolver):
        """Generate feature directory path (legacy)."""
        path = resolver.generate_feature_path("payments", "feature_dir")
        assert path == Path("docs/features/payments")

    def test_unknown_path_type_raises_error(self, resolver):
        """Unknown path_type raises error."""
        with pytest.raises(ValueError) as exc_info:
            resolver.generate_feature_path("user-auth", "unknown_type")

        error_msg = str(exc_info.value)
        assert "Unknown path_type: 'unknown_type'" in error_msg
        assert "Supported types:" in error_msg

    # ========================================
    # Epic-level paths (co-located)
    # ========================================

    def test_epic_level_epic_folder_path(self, resolver):
        """Generate epic folder path (co-located)."""
        path = resolver.generate_feature_path(
            "user-auth", "epic_folder", epic="2", epic_name="oauth"
        )
        assert path == Path("docs/features/user-auth/epics/2-oauth")

    def test_epic_level_epic_location_readme(self, resolver):
        """Generate epic location (README.md)."""
        path = resolver.generate_feature_path(
            "mvp", "epic_location", epic="1", epic_name="foundation"
        )
        assert path == Path("docs/features/mvp/epics/1-foundation/README.md")

    def test_epic_level_with_number_and_name(self, resolver):
        """Epic with number and name."""
        path = resolver.generate_feature_path(
            "payments", "epic_folder", epic="3", epic_name="stripe-integration"
        )
        assert path == Path("docs/features/payments/epics/3-stripe-integration")

    def test_epic_level_multiple_epics_same_feature(self, resolver):
        """Multiple epics in same feature."""
        path1 = resolver.generate_feature_path(
            "user-auth", "epic_folder", epic="1", epic_name="foundation"
        )
        path2 = resolver.generate_feature_path(
            "user-auth", "epic_folder", epic="2", epic_name="oauth"
        )

        assert path1 == Path("docs/features/user-auth/epics/1-foundation")
        assert path2 == Path("docs/features/user-auth/epics/2-oauth")

    def test_epic_level_context_xml_folder(self, resolver):
        """Generate context XML folder (inside epic)."""
        path = resolver.generate_feature_path(
            "user-auth", "context_xml_folder", epic="2", epic_name="oauth"
        )
        assert path == Path("docs/features/user-auth/epics/2-oauth/context")

    # ========================================
    # Story-level paths (inside epic)
    # ========================================

    def test_story_level_story_folder_path(self, resolver):
        """Generate story folder path (inside epic)."""
        path = resolver.generate_feature_path(
            "user-auth", "story_folder", epic="2", epic_name="oauth"
        )
        assert path == Path("docs/features/user-auth/epics/2-oauth/stories")

    def test_story_level_story_location(self, resolver):
        """Generate story location (story-X.Y.md)."""
        path = resolver.generate_feature_path(
            "user-auth", "story_location", epic="2", epic_name="oauth", story="3"
        )
        assert path == Path("docs/features/user-auth/epics/2-oauth/stories/story-2.3.md")

    def test_story_level_with_epic_number_and_name(self, resolver):
        """Story with epic number and name."""
        path = resolver.generate_feature_path(
            "mvp", "story_location", epic="1", epic_name="foundation", story="1"
        )
        assert path == Path("docs/features/mvp/epics/1-foundation/stories/story-1.1.md")

    def test_story_level_multiple_stories_same_epic(self, resolver):
        """Multiple stories in same epic."""
        path1 = resolver.generate_feature_path(
            "user-auth", "story_location", epic="2", epic_name="oauth", story="1"
        )
        path2 = resolver.generate_feature_path(
            "user-auth", "story_location", epic="2", epic_name="oauth", story="2"
        )

        assert path1 == Path("docs/features/user-auth/epics/2-oauth/stories/story-2.1.md")
        assert path2 == Path("docs/features/user-auth/epics/2-oauth/stories/story-2.2.md")

    def test_story_level_numbering_across_epics(self, resolver):
        """Story numbering across different epics."""
        path1 = resolver.generate_feature_path(
            "payments", "story_location", epic="1", epic_name="core", story="1"
        )
        path2 = resolver.generate_feature_path(
            "payments", "story_location", epic="2", epic_name="integrations", story="1"
        )

        assert path1 == Path("docs/features/payments/epics/1-core/stories/story-1.1.md")
        assert path2 == Path("docs/features/payments/epics/2-integrations/stories/story-2.1.md")

    # ========================================
    # Ceremony artifacts
    # ========================================

    def test_ceremony_retrospective_location(self, resolver):
        """Generate retrospective location."""
        path = resolver.generate_feature_path("user-auth", "retrospective_location", epic="2")
        assert path == Path("docs/features/user-auth/retrospectives/epic-2-retro.md")

    def test_ceremony_standup_location_with_date(self, resolver):
        """Generate standup location (with date)."""
        with patch("gao_dev.core.services.feature_path_resolver.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 11, 11)
            path = resolver.generate_feature_path("mvp", "standup_location")

        assert path == Path("docs/features/mvp/standups/standup-2025-11-11.md")

    def test_ceremony_date_formatting(self, resolver):
        """Date formatting in ceremony paths."""
        with patch("gao_dev.core.services.feature_path_resolver.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 5)
            path = resolver.generate_feature_path("payments", "standup_location")

        assert path == Path("docs/features/payments/standups/standup-2025-01-05.md")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_feature_not_found_explicit_parameter(self, resolver, mock_feature_service):
        """Feature not found in explicit parameter."""
        mock_feature_service.get_feature.return_value = None
        mock_feature_service.list_features.return_value = []

        with pytest.raises(ValueError) as exc_info:
            resolver.resolve_feature_name({"feature_name": "nonexistent"}, None)

        error_msg = str(exc_info.value)
        assert "Feature 'nonexistent' does not exist" in error_msg

    def test_ambiguous_resolution_multiple_features(self, resolver, mock_feature_service):
        """Ambiguous resolution (multiple features)."""
        mock_feature_service.get_feature.return_value = None
        mock_feature_service.list_features.return_value = [
            Feature(
                name="feature1",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
            Feature(
                name="feature2",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]

        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_feature_name({}, None)

        error_msg = str(exc_info.value)
        assert "Cannot resolve feature_name. Multiple features exist" in error_msg

    def test_invalid_path_type(self, resolver):
        """Invalid path_type."""
        with pytest.raises(ValueError) as exc_info:
            resolver.generate_feature_path("user-auth", "invalid_type")

        error_msg = str(exc_info.value)
        assert "Unknown path_type: 'invalid_type'" in error_msg

    def test_error_messages_are_helpful(self, resolver, mock_feature_service):
        """Error messages provide actionable solutions when multiple non-MVP features exist."""
        # Need multiple non-MVP features to trigger error
        mock_feature_service.get_feature.return_value = None
        mock_feature_service.list_features.return_value = [
            Feature(name="mvp", scope=FeatureScope.MVP, status=FeatureStatus.ACTIVE, scale_level=4),
            Feature(
                name="feature1",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
            Feature(
                name="feature2",
                scope=FeatureScope.FEATURE,
                status=FeatureStatus.ACTIVE,
                scale_level=3,
            ),
        ]

        with patch("pathlib.Path.cwd", return_value=Path("/somewhere/else")):
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_feature_name({}, None)

        error_msg = str(exc_info.value)
        # Check for actionable solutions
        assert "--feature-name" in error_msg
        assert "cd docs/features" in error_msg
        assert "Available features:" in error_msg


class TestCrossPlatform:
    """Test cross-platform path handling."""

    def test_windows_style_paths(self, resolver):
        """Windows-style paths work correctly."""
        path = resolver.generate_feature_path(
            "user-auth", "story_location", epic="2", epic_name="oauth", story="3"
        )

        # Path should use forward slashes internally
        path_str = str(path)
        # On Windows, Path converts to backslashes, but we check the parts
        assert path.parts == (
            "docs",
            "features",
            "user-auth",
            "epics",
            "2-oauth",
            "stories",
            "story-2.3.md",
        )

    def test_unix_style_paths(self, resolver):
        """Unix-style paths work correctly."""
        path = resolver.generate_feature_path(
            "mvp", "epic_location", epic="1", epic_name="foundation"
        )

        assert path.parts == ("docs", "features", "mvp", "epics", "1-foundation", "README.md")

    def test_path_parts_are_consistent(self, resolver):
        """Path parts are consistent across platforms."""
        paths = [
            resolver.generate_feature_path("user-auth", "prd"),
            resolver.generate_feature_path("mvp", "epic_folder", epic="1", epic_name="test"),
            resolver.generate_feature_path(
                "payments", "story_location", epic="2", epic_name="core", story="1"
            ),
        ]

        for path in paths:
            # All paths should start with docs/features
            assert path.parts[0] == "docs"
            assert path.parts[1] == "features"
