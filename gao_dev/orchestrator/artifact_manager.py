"""Artifact detection and registration service for GAO-Dev.

This service manages the complete artifact lifecycle:
1. Snapshot project files before/after operations
2. Detect newly created or modified artifacts
3. Infer document types from paths and content
4. Register artifacts in document lifecycle

The ArtifactManager reduces orchestrator complexity and provides a focused service
for managing all document artifacts created during workflow execution.
"""

from pathlib import Path
from typing import List, Set, Dict, Any, Tuple, Optional
import structlog
import time

from ..lifecycle.document_manager import DocumentLifecycleManager

logger = structlog.get_logger()


class ArtifactManager:
    """
    Service for artifact detection and registration.

    Responsibilities:
    - Snapshot project files before/after workflow execution
    - Detect newly created or modified files
    - Infer document types from paths and workflow context
    - Register artifacts with DocumentLifecycleManager
    - Handle metadata extraction for artifacts

    Design Pattern: Service pattern with clear separation of concerns
    """

    def __init__(
        self,
        project_root: Path,
        document_lifecycle: Optional[DocumentLifecycleManager] = None,
        tracked_dirs: Optional[List[str]] = None,
    ):
        """
        Initialize the ArtifactManager.

        Args:
            project_root: Root directory of the project
            document_lifecycle: Optional document lifecycle manager for registration
            tracked_dirs: Optional list of directory names to track (defaults to ["docs", "src", "gao_dev"])
        """
        self.project_root = project_root
        self.doc_lifecycle = document_lifecycle
        self.tracked_dirs = tracked_dirs or ["docs", "src", "gao_dev"]

        # Directories to ignore (build artifacts, dependencies, internal state)
        self.ignored_dirs = {
            ".git",
            "node_modules",
            "__pycache__",
            ".gao-dev",
            ".archive",
            "venv",
            ".venv",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            "htmlcov",
        }

        logger.debug(
            "artifact_manager_initialized",
            project_root=str(project_root),
            tracked_dirs=self.tracked_dirs,
            has_lifecycle=document_lifecycle is not None,
        )

    def snapshot(self) -> Set[Tuple[str, float, int]]:
        """
        Snapshot current project files for artifact detection.

        Captures filesystem state by scanning tracked directories (docs/, src/, gao_dev/)
        and recording file metadata (path, mtime, size) for later comparison.

        This enables automatic detection of files created or modified during
        workflow execution without requiring the LLM to explicitly declare outputs.

        Returns:
            Set of (path, mtime, size) tuples for all tracked files

        Performance:
            Target: <50ms for typical projects (<1000 files)
            Uses efficient rglob with ignored directory filtering

        Example:
            >>> manager = ArtifactManager(Path("my-project"))
            >>> before = manager.snapshot()
            >>> # ... execute workflow ...
            >>> after = manager.snapshot()
            >>> artifacts = manager.detect(before, after)
        """
        snapshot_start = time.time()
        snapshot: Set[Tuple[str, float, int]] = set()

        # Build absolute paths for tracked directories
        tracked_paths = [self.project_root / dirname for dirname in self.tracked_dirs]

        for tracked_dir in tracked_paths:
            if not tracked_dir.exists():
                continue

            try:
                for file_path in tracked_dir.rglob("*"):
                    # Skip if any parent directory is in ignored_dirs
                    if any(part in self.ignored_dirs for part in file_path.parts):
                        continue

                    if file_path.is_file():
                        try:
                            stat = file_path.stat()
                            rel_path = str(file_path.relative_to(self.project_root))
                            snapshot.add((rel_path, stat.st_mtime, stat.st_size))
                        except (OSError, ValueError) as e:
                            # Log warning but continue
                            logger.warning(
                                "snapshot_file_error",
                                file=str(file_path),
                                error=str(e),
                                message="Skipping file in snapshot",
                            )
            except (OSError, PermissionError) as e:
                # Log warning if entire directory can't be scanned
                logger.warning(
                    "snapshot_directory_error",
                    directory=str(tracked_dir),
                    error=str(e),
                    message="Skipping directory in snapshot",
                )

        snapshot_duration = (time.time() - snapshot_start) * 1000  # Convert to ms
        logger.debug(
            "filesystem_snapshot_complete",
            files_count=len(snapshot),
            duration_ms=round(snapshot_duration, 2),
        )

        return snapshot

    def detect(
        self, before: Set[Tuple[str, float, int]], after: Set[Tuple[str, float, int]]
    ) -> List[Path]:
        """
        Detect artifacts created or modified during workflow execution.

        Compares before and after filesystem snapshots to identify files that
        were created (new files) or modified (changed mtime/size). This provides
        automatic artifact tracking without requiring explicit declarations.

        Args:
            before: Filesystem snapshot before execution (set of tuples)
            after: Filesystem snapshot after execution (set of tuples)

        Returns:
            List of artifact paths (relative to project root) that were created or modified

        Detection Logic:
            - New files: In after but not in before
            - Modified files: Same path, different mtime or size
            - Deleted files: Ignored (not considered artifacts)

        Example:
            >>> before = manager.snapshot()
            >>> # ... workflow creates docs/PRD.md ...
            >>> after = manager.snapshot()
            >>> artifacts = manager.detect(before, after)
            >>> print(artifacts)  # [Path('docs/PRD.md')]
        """
        detection_start = time.time()

        # New or modified files: in after but not in before
        # (different mtime or size means modified)
        all_artifacts = after - before

        # Convert tuples back to Path objects (relative to project root)
        artifact_paths = [Path(item[0]) for item in all_artifacts]

        detection_duration = (time.time() - detection_start) * 1000  # Convert to ms

        logger.info(
            "workflow_artifacts_detected",
            artifacts_count=len(artifact_paths),
            artifacts=[str(p) for p in artifact_paths],
            detection_duration_ms=round(detection_duration, 2),
        )

        return artifact_paths

    def infer_type(self, path: Path, workflow_name: str) -> str:
        """
        Infer document type from workflow name and file path.

        Uses a two-stage strategy:
        1. Primary: Map based on workflow name (most reliable)
        2. Fallback: Map based on file path patterns
        3. Default: Return "story" if no pattern matches

        Args:
            path: Path to artifact file (relative to project root)
            workflow_name: Name of the workflow that created the artifact

        Returns:
            Document type string (e.g., "prd", "architecture", "story")

        Examples:
            >>> # From workflow name
            >>> manager.infer_type(Path("docs/PRD.md"), "prd")
            "prd"

            >>> # From file path (fallback)
            >>> manager.infer_type(Path("docs/epic-1/story-1.md"), "dev")
            "story"

            >>> # Default for unknown
            >>> manager.infer_type(Path("docs/notes.md"), "research")
            "story"
        """
        path_lower = str(path).lower()
        workflow_lower = workflow_name.lower()

        # Strategy 1: Map based on workflow name (most reliable)
        # Use DocumentType enum values: prd, architecture, epic, story, adr, postmortem, runbook, qa_report, test_report
        workflow_type_mapping = {
            "prd": "prd",
            "architecture": "architecture",
            "tech-spec": "architecture",  # Map tech-spec to architecture
            "epic": "epic",
            "story": "story",
            "create-story": "story",
            "dev-story": "story",
            "implement": "story",  # Implementation stories
            "test": "test_report",
            "qa": "qa_report",
            "ux": "adr",  # Design decisions -> ADR
            "design": "adr",
            "research": "adr",  # Research findings -> ADR
            "brief": "adr",
            "postmortem": "postmortem",
            "runbook": "runbook",
        }

        for pattern, doc_type in workflow_type_mapping.items():
            if pattern in workflow_lower:
                return doc_type

        # Strategy 2: Map based on file path (fallback)
        path_type_mapping = {
            "prd": "prd",
            "architecture": "architecture",
            "arch": "architecture",
            "spec": "architecture",
            "epic": "epic",
            "story": "story",
            "test": "test_report",
            "qa": "qa_report",
            "adr": "adr",
            "decision": "adr",
            "postmortem": "postmortem",
            "runbook": "runbook",
        }

        for pattern, doc_type in path_type_mapping.items():
            if pattern in path_lower:
                return doc_type

        # Default: use story as generic document type (most flexible)
        return "story"

    def register(
        self,
        artifacts: List[Path],
        workflow_name: str,
        epic: int,
        story: int,
        agent: str,
        phase: str,
        variables: Dict[str, Any],
    ) -> None:
        """
        Register detected artifacts with DocumentLifecycleManager.

        This method automatically registers all workflow artifacts with comprehensive
        metadata including document type, author, workflow context, and resolved variables.
        Registration failures are handled gracefully - logged as warnings without breaking
        workflow execution.

        Args:
            artifacts: List of artifact paths (relative to project root)
            workflow_name: Name of the workflow that created the artifacts
            epic: Epic number for context
            story: Story number for context
            agent: Agent that executed the workflow (e.g., "john", "amelia")
            phase: Workflow phase (e.g., "planning", "implementation")
            variables: Resolved workflow variables from WorkflowExecutor

        Behavior:
            - Skips registration if DocumentLifecycleManager not available
            - Infers document type from workflow name (primary) or path (fallback)
            - Builds comprehensive metadata with workflow context
            - Logs successful registrations (artifact_registered)
            - Logs failed registrations as warnings (artifact_registration_failed)
            - Continues processing remaining artifacts after failures

        Example:
            >>> artifacts = [Path("docs/PRD.md"), Path("docs/epic-1.md")]
            >>> manager.register(
            ...     artifacts=artifacts,
            ...     workflow_name="prd",
            ...     epic=1,
            ...     story=1,
            ...     agent="john",
            ...     phase="planning",
            ...     variables={"project_name": "MyApp"}
            ... )
            # Logs: artifact_registered for PRD.md as "prd" by "john"
            # Logs: artifact_registered for epic-1.md as "epic" by "john"
        """
        if not self.doc_lifecycle:
            logger.warning(
                "document_lifecycle_not_available",
                message="Cannot register artifacts - DocumentLifecycleManager not initialized",
            )
            return

        for artifact_path in artifacts:
            try:
                # Determine document type from workflow and path
                doc_type = self.infer_type(artifact_path, workflow_name)

                # Build comprehensive metadata
                metadata = {
                    "workflow": workflow_name,
                    "epic": epic,
                    "story": story,
                    "phase": phase,
                    "created_by_workflow": True,
                    "variables": variables,
                    "workflow_phase": phase,
                }

                # Convert relative path to absolute for registration
                absolute_path = self.project_root / artifact_path

                # Register with document lifecycle manager
                doc = self.doc_lifecycle.register_document(
                    path=absolute_path, doc_type=doc_type, author=agent.lower(), metadata=metadata
                )

                logger.info(
                    "artifact_registered",
                    artifact=str(artifact_path),
                    doc_type=doc_type,
                    doc_id=doc.id,
                    author=agent.lower(),
                    workflow=workflow_name,
                )

            except Exception as e:
                # Log warning but don't fail workflow
                logger.warning(
                    "artifact_registration_failed",
                    artifact=str(artifact_path),
                    error=str(e),
                    error_type=type(e).__name__,
                    message="Continuing without registration",
                )
