"""Document Structure Manager for GAO-Dev.

Manages document structure based on work type and scale level.
Creates scale-appropriate folder structures and templates for features.

Story 28.6: DocumentStructureManager (Critical Fix C4)
Story 33.1: Extend DocumentStructureManager (QA/, README.md, auto_commit)
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from jinja2 import Environment, FileSystemLoader

from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.lifecycle.models import DocumentType
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.core.git_manager import GitManager

logger = structlog.get_logger(__name__)


class DocumentStructureManager:
    """
    Manages document structure based on work type and scale level.

    Responsibilities:
    - Initialize feature folders with correct structure for each scale level
    - Create document templates (PRD, ARCHITECTURE, CHANGELOG, README)
    - Update global docs (PRD.md, CHANGELOG.md, ARCHITECTURE.md)
    - Enforce structure consistency across features
    - Integrate with DocumentLifecycleManager for tracking

    Scale Level Structures:
    - Level 0 (Chore): No folder created
    - Level 1 (Bug): docs/bugs/ directory
    - Level 2 (Small Feature): docs/features/<name>/ + PRD + QA/ + stories/
    - Level 3 (Medium Feature): + ARCHITECTURE + epics/ + retrospectives/
    - Level 4 (Greenfield): + ceremonies/ + MIGRATION_GUIDE + root docs

    Story 33.1 Enhancements:
    - QA/ folder created for all features
    - README.md generated from Jinja2 template
    - auto_commit parameter for GitIntegratedStateManager integration
    """

    def __init__(
        self,
        project_root: Path,
        doc_lifecycle: DocumentLifecycleManager,
        git_manager: GitManager,
    ):
        """
        Initialize DocumentStructureManager.

        Args:
            project_root: Root directory of the project
            doc_lifecycle: DocumentLifecycleManager for tracking documents
            git_manager: GitManager for committing changes

        Raises:
            ValueError: If project_root doesn't exist or isn't writable
        """
        if not project_root.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        self.project_root = project_root
        self.doc_lifecycle = doc_lifecycle
        self.git = git_manager

        # Initialize Jinja2 environment for templates (Story 33.1)
        template_dir = Path(__file__).parent.parent.parent / "config" / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

        logger.info(
            "document_structure_manager_initialized", project_root=str(project_root)
        )

    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel,
        description: Optional[str] = None,
        auto_commit: bool = True,
    ) -> Optional[Path]:
        """
        Initialize feature folder based on scale level.

        Creates appropriate folder structure and template files for the
        given scale level. All created documents are registered with
        DocumentLifecycleManager.

        EXISTING FUNCTIONALITY (Epic 28):
        - Creates docs/features/{feature_name}/
        - Generates PRD.md, ARCHITECTURE.md templates
        - Creates epics/, stories/, retrospectives/ (scale-dependent)
        - Registers with DocumentLifecycleManager
        - Commits to git

        NEW ENHANCEMENTS (Story 33.1):
        - Creates QA/ folder (all scale levels)
        - Generates README.md from Jinja2 template
        - Supports auto_commit parameter:
          - True (default): Commits to git (backward compatible)
          - False: Skips commit (for GitIntegratedStateManager)

        Args:
            feature_name: Name of the feature (kebab-case recommended)
            scale_level: Scale level determining folder structure
            description: Optional feature description
            auto_commit: Whether to commit to git (default: True)

        Returns:
            Path to created folder, or None for Level 0

        Raises:
            ValueError: If feature_name is empty or scale_level invalid
        """
        if not feature_name:
            raise ValueError("feature_name cannot be empty")

        logger.info(
            "initializing_feature_folder",
            feature_name=feature_name,
            scale_level=scale_level.name,
            auto_commit=auto_commit,
        )

        # Level 0: No folder created
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            logger.info("level_0_chore_skip_folder", feature_name=feature_name)
            return None

        # Level 1: Optional bug report directory
        if scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            bug_path = self.project_root / "docs" / "bugs"
            bug_path.mkdir(parents=True, exist_ok=True)

            self.git.add_all()
            self.git.commit("docs(bugs): initialize bugs directory")

            logger.info("bugs_directory_created", path=str(bug_path))
            return bug_path

        # Level 2+: Feature folder
        feature_path = self.project_root / "docs" / "features" / feature_name
        feature_path.mkdir(parents=True, exist_ok=True)

        # Create structure based on level
        if scale_level >= ScaleLevel.LEVEL_2_SMALL_FEATURE:
            # QA directory (Story 33.1)
            (feature_path / "QA").mkdir(exist_ok=True)

            # Lightweight PRD for Level 2
            prd_content = self._prd_template(feature_name, "lightweight")
            self._create_file(feature_path / "PRD.md", prd_content)

            # CHANGELOG
            changelog_content = "# Changelog\n\n## Unreleased\n\n"
            self._create_file(feature_path / "CHANGELOG.md", changelog_content)

            # README.md from Jinja2 template (Story 33.1)
            self._create_readme(feature_path, feature_name, description, scale_level)

        if scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # Additional directories
            (feature_path / "epics").mkdir(exist_ok=True)
            (feature_path / "retrospectives").mkdir(exist_ok=True)

            # Full architecture document
            arch_content = self._architecture_template(feature_name)
            self._create_file(feature_path / "ARCHITECTURE.md", arch_content)

            # Upgrade PRD to full template
            prd_content = self._prd_template(feature_name, "full")
            self._create_file(feature_path / "PRD.md", prd_content)

        if scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            # Greenfield-specific additions
            (feature_path / "ceremonies").mkdir(exist_ok=True)

            migration_content = "# Migration Guide\n\nTBD\n"
            self._create_file(feature_path / "MIGRATION_GUIDE.md", migration_content)

        # Register PRD with document lifecycle
        self.doc_lifecycle.register_document(
            path=feature_path / "PRD.md",
            doc_type=DocumentType.PRD.value,
            author="system",
            metadata={"feature": feature_name, "scale_level": scale_level.value},
        )

        # Conditional git commit (Story 33.1)
        if auto_commit:
            self.git.add_all()
            self.git.commit(
                f"docs({feature_name}): initialize feature folder (Level {scale_level.value})\n\n"
                f"Created feature structure with scale level {scale_level.value}.\n"
                f"Includes: PRD, Architecture, README, QA, and folder structure."
            )
            logger.info(
                "feature_folder_committed_to_git",
                feature_name=feature_name,
                scale_level=scale_level.name,
            )
        else:
            logger.info(
                "feature_folder_created_no_git_commit",
                feature_name=feature_name,
                scale_level=scale_level.name,
                message="Git commit delegated to caller",
            )

        logger.info(
            "feature_folder_initialized",
            feature_name=feature_name,
            scale_level=scale_level.name,
            path=str(feature_path),
            auto_commit=auto_commit,
        )

        return feature_path

    def update_global_docs(
        self,
        feature_name: str,
        epic_num: int,
        update_type: str,  # 'planned', 'architected', 'completed'
    ) -> None:
        """
        Update global PRD and ARCHITECTURE docs.

        Args:
            feature_name: Name of the feature
            epic_num: Epic number for the feature
            update_type: Type of update (planned/architected/completed)

        Raises:
            ValueError: If update_type is invalid
        """
        valid_types = ["planned", "architected", "completed"]
        if update_type not in valid_types:
            raise ValueError(
                f"Invalid update_type: {update_type}. Must be one of: {valid_types}"
            )

        logger.info(
            "updating_global_docs",
            feature_name=feature_name,
            epic_num=epic_num,
            update_type=update_type,
        )

        if update_type == "planned":
            self._update_global_prd(feature_name, epic_num, status="Planned")
        elif update_type == "architected":
            self._update_global_architecture(feature_name, epic_num)
        elif update_type == "completed":
            self._update_global_prd(feature_name, epic_num, status="Completed")
            self._update_changelog(feature_name, epic_num)

        # Git commit
        self.git.add_all()
        self.git.commit(f"docs(global): update {update_type} for {feature_name}")

    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================

    def _create_file(self, path: Path, content: str) -> None:
        """Create file with content and log creation.

        Args:
            path: Path to file to create
            content: Content to write to file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("file_created", path=str(path))

    def _create_readme(
        self,
        feature_path: Path,
        feature_name: str,
        description: Optional[str],
        scale_level: ScaleLevel,
    ) -> None:
        """
        Create README.md from Jinja2 template.

        Story 33.1: Generate README.md with feature metadata and structure diagram.

        Args:
            feature_path: Path to feature folder
            feature_name: Name of the feature
            description: Optional feature description
            scale_level: Scale level of the feature

        Template location: gao_dev/config/templates/feature-readme.md.j2
        """
        template = self.jinja_env.get_template("feature-readme.md.j2")

        content = template.render(
            feature_name=feature_name,
            description=description or f"Feature: {feature_name}",
            scale_level=scale_level.value,
            created_date=datetime.now().strftime("%Y-%m-%d"),
            has_ceremonies=(scale_level == ScaleLevel.LEVEL_4_GREENFIELD),
            has_retrospectives=(scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE),
        )

        readme_path = feature_path / "README.md"
        readme_path.write_text(content, encoding="utf-8")

        logger.info("readme_created", path=str(readme_path), feature_name=feature_name)

    def _prd_template(self, feature_name: str, template_type: str) -> str:
        """Generate PRD template (lightweight or full).

        Args:
            feature_name: Name of the feature
            template_type: Either 'lightweight' or 'full'

        Returns:
            PRD template content as string
        """
        if template_type == "lightweight":
            return f"""# {feature_name} - Product Requirements Document

## Summary
TBD

## User Stories
- As a user, I want...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Success Metrics
TBD
"""
        else:  # full
            return f"""# {feature_name} - Product Requirements Document

## Summary
TBD

## Problem Statement
TBD

## Solution Approach
TBD

## User Stories
- As a user, I want...

## Technical Requirements
TBD

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Dependencies
TBD

## Timeline
TBD

## Risk Assessment
TBD

## Success Metrics
TBD
"""

    def _architecture_template(self, feature_name: str) -> str:
        """Generate architecture template.

        Args:
            feature_name: Name of the feature

        Returns:
            Architecture template content as string
        """
        return f"""# {feature_name} - Architecture

## System Overview
TBD

## Component Diagram
```
[Diagram placeholder]
```

## Data Models
TBD

## API Design
TBD

## Integration Points
TBD

## Performance Considerations
TBD
"""

    def _update_global_prd(
        self, feature_name: str, epic_num: int, status: str
    ) -> None:
        """Update global PRD with feature status.

        Args:
            feature_name: Name of the feature
            epic_num: Epic number
            status: Status to set (e.g., 'Planned', 'Completed')
        """
        prd_path = self.project_root / "docs" / "PRD.md"

        if not prd_path.exists():
            content = "# Product Requirements\n\n"
        else:
            content = prd_path.read_text(encoding="utf-8")

        # Add/update feature entry
        feature_line = f"- Epic {epic_num}: {feature_name} - {status}\n"

        if f"Epic {epic_num}:" in content:
            # Update existing
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if f"Epic {epic_num}:" in line:
                    lines[i] = feature_line.rstrip()
                    break
            content = "\n".join(lines)
        else:
            # Add new
            content += feature_line

        prd_path.parent.mkdir(parents=True, exist_ok=True)
        prd_path.write_text(content, encoding="utf-8")
        logger.debug("global_prd_updated", feature_name=feature_name, status=status)

    def _update_global_architecture(self, feature_name: str, epic_num: int) -> None:
        """Update global ARCHITECTURE with feature section.

        Args:
            feature_name: Name of the feature
            epic_num: Epic number
        """
        arch_path = self.project_root / "docs" / "ARCHITECTURE.md"

        if not arch_path.exists():
            content = "# Architecture\n\n"
        else:
            content = arch_path.read_text(encoding="utf-8")

        # Add feature section
        section = f"""
## Epic {epic_num}: {feature_name}

See [Feature Architecture](features/{feature_name}/ARCHITECTURE.md) for details.

"""
        content += section
        arch_path.parent.mkdir(parents=True, exist_ok=True)
        arch_path.write_text(content, encoding="utf-8")
        logger.debug("global_architecture_updated", feature_name=feature_name)

    def _update_changelog(self, feature_name: str, epic_num: int) -> None:
        """Update CHANGELOG with epic completion.

        Args:
            feature_name: Name of the feature
            epic_num: Epic number
        """
        changelog_path = self.project_root / "docs" / "CHANGELOG.md"

        if not changelog_path.exists():
            content = "# Changelog\n\n## Unreleased\n\n"
        else:
            content = changelog_path.read_text(encoding="utf-8")

        # Add entry under Unreleased
        entry = f"- Epic {epic_num}: {feature_name} completed\n"

        if "## Unreleased" in content:
            content = content.replace("## Unreleased\n", f"## Unreleased\n{entry}")
        else:
            content += f"\n## Unreleased\n{entry}"

        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        changelog_path.write_text(content, encoding="utf-8")
        logger.debug("changelog_updated", feature_name=feature_name)
