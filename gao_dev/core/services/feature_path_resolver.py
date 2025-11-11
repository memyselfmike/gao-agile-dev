"""Feature Path Resolver - Intelligent 6-level priority resolution.

This service provides intelligent feature name resolution and feature-scoped
path generation with WorkflowContext integration.

Epic: 32 - State Service Integration
Story: 32.4 - Create FeaturePathResolver

Design Pattern: Service with priority-based resolution
Dependencies: FeatureStateService, WorkflowContext
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from gao_dev.core.services.feature_state_service import FeatureStateService
from gao_dev.core.models.workflow_context import WorkflowContext

logger = structlog.get_logger(__name__)


class FeaturePathResolver:
    """
    Resolve feature names and generate feature-scoped paths.

    Integrates with WorkflowExecutor to provide feature_name
    variable resolution with intelligent auto-detection.

    Features:
    - 6-level priority resolution
    - WorkflowContext integration (context.metadata.feature_name)
    - Co-located epic-story path generation
    - Comprehensive error messages

    Example:
        ```python
        resolver = FeaturePathResolver(
            project_root=Path("."),
            feature_service=FeatureStateService(Path("."))
        )

        # Resolve feature name
        feature_name = resolver.resolve_feature_name(
            params={"feature_name": "user-auth"},
            context=None
        )

        # Generate paths
        prd_path = resolver.generate_feature_path("user-auth", "prd")
        # => Path("docs/features/user-auth/PRD.md")

        story_path = resolver.generate_feature_path(
            "user-auth", "story_location",
            epic="2", epic_name="oauth", story="3"
        )
        # => Path("docs/features/user-auth/epics/2-oauth/stories/story-2.3.md")
        ```
    """

    def __init__(self, project_root: Path, feature_service: FeatureStateService):
        """
        Initialize feature path resolver.

        Args:
            project_root: Project root directory
            feature_service: FeatureStateService for querying available features
        """
        self.project_root = Path(project_root)
        self.features_dir = self.project_root / "docs" / "features"
        self.feature_service = feature_service
        self.logger = logger.bind(service="feature_path_resolver")

    def resolve_feature_name(
        self, params: Dict[str, Any], context: Optional[WorkflowContext] = None
    ) -> str:
        """
        Resolve feature name from multiple sources.

        Priority (highest to lowest):
        1. Explicit parameter: params["feature_name"]
        2. WorkflowContext: context.metadata.get("feature_name")
        3. Current working directory (if in feature folder)
        4. Single feature detection (if only one besides mvp)
        5. MVP detection (if mvp exists and no other features)
        6. Error (if ambiguous)

        Args:
            params: Workflow parameters
            context: Optional WorkflowContext

        Returns:
            Feature name (e.g., "mvp", "user-auth")

        Raises:
            ValueError: If feature_name cannot be resolved (with helpful message)

        Examples:
            # Priority 1: Explicit parameter
            >>> resolve_feature_name({"feature_name": "user-auth"}, None)
            "user-auth"

            # Priority 2: WorkflowContext
            >>> ctx = WorkflowContext(
            ...     initial_prompt="test",
            ...     metadata={"feature_name": "mvp"}
            ... )
            >>> resolve_feature_name({}, ctx)
            "mvp"

            # Priority 3: CWD in feature folder
            >>> os.chdir("docs/features/user-auth")
            >>> resolve_feature_name({}, None)
            "user-auth"

            # Priority 4: Single feature
            >>> # Only "user-auth" exists (besides mvp)
            >>> resolve_feature_name({}, None)
            "user-auth"

            # Priority 6: Error (multiple features)
            >>> # Both "user-auth" and "payment" exist
            >>> resolve_feature_name({}, None)
            ValueError: Cannot resolve feature_name. Multiple features exist: ...
        """
        # Priority 1: Explicit parameter (highest priority)
        if "feature_name" in params:
            name = params["feature_name"]
            feature = self.feature_service.get_feature(name)
            if not feature:
                available = self._list_feature_names()
                raise ValueError(
                    f"Feature '{name}' does not exist.\n"
                    f"Available features: {', '.join(available)}\n\n"
                    f"Create it with: gao-dev create-feature {name}"
                )
            self.logger.info(
                "Resolved feature_name from explicit parameter", feature_name=name, priority=1
            )
            return name

        # Priority 2: WorkflowContext (NEW!)
        if context and context.metadata.get("feature_name"):
            name = context.metadata["feature_name"]
            self.logger.info(
                "Resolved feature_name from WorkflowContext", feature_name=name, priority=2
            )
            return name

        # Priority 3: Current working directory
        cwd = Path.cwd()
        try:
            if cwd.is_relative_to(self.features_dir):
                relative = cwd.relative_to(self.features_dir)
                if relative.parts:
                    feature_name = relative.parts[0]
                    feature = self.feature_service.get_feature(feature_name)
                    if feature:
                        self.logger.info(
                            "Resolved feature_name from cwd", feature_name=feature_name, priority=3
                        )
                        return feature_name
        except ValueError:
            # is_relative_to raises ValueError if not relative (Python 3.9+)
            pass

        # Priority 4: Single feature detection (exclude MVP)
        features = self._list_feature_names(exclude_mvp=True)
        if len(features) == 1:
            self.logger.info(
                "Resolved feature_name (single feature)", feature_name=features[0], priority=4
            )
            return features[0]

        # Priority 5: MVP detection
        mvp_exists = self.feature_service.get_feature("mvp") is not None
        if mvp_exists and len(features) == 0:
            self.logger.info("Resolved feature_name to mvp (only feature)", priority=5)
            return "mvp"

        # Priority 6: Error (ambiguous)
        all_features = self._list_feature_names()
        if not all_features:
            raise ValueError(
                "No features exist in this project.\n\n"
                "Create a feature with:\n"
                "  gao-dev create-feature <name>\n\n"
                "Or create MVP:\n"
                "  gao-dev create-feature mvp"
            )

        raise ValueError(
            "Cannot resolve feature_name. Multiple features exist:\n"
            f"  {', '.join(all_features)}\n\n"
            "Please specify explicitly:\n"
            "  --feature-name <name>\n\n"
            "Or run from feature directory:\n"
            "  cd docs/features/<name> && gao-dev <command>\n\n"
            "Available features:\n" + "\n".join(f"  - {name}" for name in all_features)
        )

    def generate_feature_path(
        self,
        feature_name: str,
        path_type: str,
        epic: Optional[str] = None,
        epic_name: Optional[str] = None,
        story: Optional[str] = None,
    ) -> Path:
        """
        Generate feature-scoped path using co-located structure.

        Args:
            feature_name: Feature name (e.g., "user-auth", "mvp")
            path_type: Path type identifier
            epic: Epic number (e.g., "1")
            epic_name: Epic name (e.g., "foundation")
            story: Story number (e.g., "2")

        Returns:
            Path relative to project root

        Supported path_types:
            Feature-level documents:
            - prd: docs/features/{feature}/PRD.md
            - architecture: docs/features/{feature}/ARCHITECTURE.md
            - readme: docs/features/{feature}/README.md
            - epics_overview: docs/features/{feature}/EPICS.md

            Feature-level folders:
            - qa_folder: docs/features/{feature}/QA
            - retrospectives_folder: docs/features/{feature}/retrospectives

            Epic-level (co-located with stories!):
            - epic_folder: docs/features/{feature}/epics/{epic}-{epic_name}
            - epic_location: docs/features/{feature}/epics/{epic}-{epic_name}/README.md

            Story-level (inside epic folder!):
            - story_folder: docs/features/{feature}/epics/{epic}-{epic_name}/stories
            - story_location: docs/features/{feature}/epics/{epic}-{epic_name}/stories/story-{epic}.{story}.md
            - context_xml_folder: docs/features/{feature}/epics/{epic}-{epic_name}/context

            Ceremony artifacts:
            - retrospective_location: docs/features/{feature}/retrospectives/epic-{epic}-retro.md
            - standup_location: docs/features/{feature}/standups/standup-{date}.md

        Examples:
            >>> generate_feature_path("user-auth", "prd")
            Path("docs/features/user-auth/PRD.md")

            >>> generate_feature_path("mvp", "epic_location", epic="1", epic_name="foundation")
            Path("docs/features/mvp/epics/1-foundation/README.md")

            >>> generate_feature_path("user-auth", "story_location",
            ...                      epic="2", epic_name="oauth", story="3")
            Path("docs/features/user-auth/epics/2-oauth/stories/story-2.3.md")

        Raises:
            ValueError: If path_type is unknown
        """
        # Co-located path templates (v3.0)
        templates = {
            # Feature-level documents
            "prd": "docs/features/{feature_name}/PRD.md",
            "architecture": "docs/features/{feature_name}/ARCHITECTURE.md",
            "readme": "docs/features/{feature_name}/README.md",
            "epics_overview": "docs/features/{feature_name}/EPICS.md",
            # Feature-level folders
            "qa_folder": "docs/features/{feature_name}/QA",
            "retrospectives_folder": "docs/features/{feature_name}/retrospectives",
            "standups_folder": "docs/features/{feature_name}/standups",
            # Epic-level (CO-LOCATED with stories!)
            "epic_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}",
            "epic_location": "docs/features/{feature_name}/epics/{epic}-{epic_name}/README.md",
            # Story-level (INSIDE epic folder!)
            "story_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}/stories",
            "story_location": "docs/features/{feature_name}/epics/{epic}-{epic_name}/stories/story-{epic}.{story}.md",
            "context_xml_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}/context",
            # Ceremony artifacts
            "retrospective_location": "docs/features/{feature_name}/retrospectives/epic-{epic}-retro.md",
            "standup_location": "docs/features/{feature_name}/standups/standup-{date}.md",
            # Legacy (for backward compatibility)
            "feature_dir": "docs/features/{feature_name}",
        }

        template = templates.get(path_type)
        if not template:
            raise ValueError(
                f"Unknown path_type: '{path_type}'\n\n"
                f"Supported types: {', '.join(sorted(templates.keys()))}"
            )

        # Generate path from template
        path_str = template.format(
            feature_name=feature_name,
            epic=epic or "",
            epic_name=epic_name or "",
            story=story or "",
            date=datetime.now().strftime("%Y-%m-%d"),
        )

        self.logger.debug(
            "Generated feature path", feature_name=feature_name, path_type=path_type, path=path_str
        )

        return Path(path_str)

    def _list_feature_names(self, exclude_mvp: bool = False) -> list[str]:
        """List all feature names (helper method).

        Args:
            exclude_mvp: If True, exclude 'mvp' from results

        Returns:
            Sorted list of feature names
        """
        features = self.feature_service.list_features()
        names = [f.name for f in features]

        if exclude_mvp:
            names = [n for n in names if n != "mvp"]

        return sorted(names)
