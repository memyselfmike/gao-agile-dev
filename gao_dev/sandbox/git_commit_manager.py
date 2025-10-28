"""Git commit management for benchmark artifact creation."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import structlog

from ..core.git_manager import GitManager

logger = structlog.get_logger()


class GitCommitManager:
    """
    Handles atomic commits for benchmark artifacts.

    Creates conventional commits after each phase with proper
    metadata and tracking.
    """

    def __init__(self, project_root: Path, run_id: str):
        """
        Initialize commit manager.

        Args:
            project_root: Root directory of the project
            run_id: Benchmark run ID for commit metadata
        """
        self.project_root = Path(project_root)
        self.run_id = run_id
        self.logger = logger.bind(component="GitCommitManager", run_id=run_id)

        # Initialize git manager (will handle config loading)
        from ..core import ConfigLoader
        config = ConfigLoader(self.project_root)
        self.git_manager = GitManager(config)

    def commit_artifacts(
        self,
        phase: str,
        artifact_paths: List[str],
        agent_name: str,
        description: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create atomic commit for phase artifacts.

        Args:
            phase: Phase name (e.g., "Product Requirements", "create-prd")
            artifact_paths: List of file paths created in this phase
            agent_name: Name of agent that created artifacts
            description: Optional custom description

        Returns:
            Commit SHA if successful, None otherwise
        """
        if not artifact_paths:
            self.logger.info("no_artifacts_to_commit", phase=phase)
            return None

        try:
            # Ensure git repo is initialized
            if not self.git_manager.is_git_repo():
                self.logger.info("initializing_git_repo")
                if not self.git_manager.git_init():
                    self.logger.error("git_init_failed")
                    return None

            # Stage the artifact files
            for path in artifact_paths:
                file_path = self.project_root / path
                if file_path.exists():
                    self.git_manager.stage_file(file_path)
                    self.logger.debug("file_staged", path=path)

            # Check if there are changes to commit
            if not self._has_staged_changes():
                self.logger.info("no_staged_changes", phase=phase)
                return None

            # Generate commit message
            if not description:
                description = self._generate_description(phase, agent_name)

            commit_msg = self._format_commit_message(
                phase=phase,
                description=description,
                agent_name=agent_name,
                artifact_count=len(artifact_paths),
            )

            # Create commit
            commit_sha = self._create_commit(commit_msg)

            if commit_sha:
                self.logger.info(
                    "artifacts_committed",
                    phase=phase,
                    agent=agent_name,
                    commit_sha=commit_sha[:8],
                    artifact_count=len(artifact_paths),
                )

            return commit_sha

        except Exception as e:
            self.logger.error(
                "commit_failed",
                phase=phase,
                error=str(e),
            )
            return None

    def _has_staged_changes(self) -> bool:
        """
        Check if there are staged changes ready to commit.

        Returns:
            True if changes are staged
        """
        try:
            # Use git diff --cached to check for staged changes
            import subprocess
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.project_root,
                capture_output=True,
            )
            # Exit code 1 means there are differences (staged changes)
            return result.returncode != 0
        except Exception:
            return False

    def _generate_description(self, phase: str, agent_name: str) -> str:
        """
        Generate a description for the commit based on phase.

        Args:
            phase: Phase name
            agent_name: Agent name

        Returns:
            Commit description
        """
        phase_lower = phase.lower()

        if "prd" in phase_lower or "product requirements" in phase_lower:
            return "Create Product Requirements Document"
        elif "architecture" in phase_lower:
            return "Create system architecture design"
        elif "story creation" in phase_lower:
            return "Create user stories"
        elif "implementation" in phase_lower:
            return "Implement features and tests"
        else:
            return f"Complete {phase} phase"

    def _phase_to_scope(self, phase: str) -> str:
        """
        Map phase name to conventional commit scope.

        Args:
            phase: Phase name

        Returns:
            Commit scope
        """
        phase_lower = phase.lower()

        if "prd" in phase_lower or "product requirements" in phase_lower:
            return "prd"
        elif "architecture" in phase_lower:
            return "architecture"
        elif "story" in phase_lower:
            return "stories"
        elif "implementation" in phase_lower:
            return "implementation"
        else:
            # Sanitize phase name for scope
            scope = phase_lower.replace(" ", "-")
            scope = "".join(c for c in scope if c.isalnum() or c == "-")
            return scope

    def _format_commit_message(
        self,
        phase: str,
        description: str,
        agent_name: str,
        artifact_count: int,
    ) -> str:
        """
        Format conventional commit message.

        Args:
            phase: Phase name
            description: Commit description
            agent_name: Agent that created artifacts
            artifact_count: Number of artifacts created

        Returns:
            Formatted commit message
        """
        scope = self._phase_to_scope(phase)

        # Build commit message
        message = f"feat({scope}): {description}\n\n"
        message += f"Benchmark Run: {self.run_id}\n"
        message += f"Phase: {phase}\n"
        message += f"Agent: {agent_name}\n"
        message += f"Artifacts: {artifact_count} file(s)\n"
        message += "\n"
        message += "Generated by GAO-Dev Benchmark\n"

        return message

    def _create_commit(self, message: str) -> Optional[str]:
        """
        Create git commit with message.

        Args:
            message: Commit message

        Returns:
            Commit SHA if successful, None otherwise
        """
        try:
            import subprocess

            # Set author for benchmark commits
            author = "GAO-Dev Benchmark <benchmark@gao-dev>"

            result = subprocess.run(
                ["git", "commit", "-m", message, "--author", author],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Extract commit SHA from output
                # Git commit output typically has commit SHA in first line
                for line in result.stdout.split("\n"):
                    if "commit" in line.lower() or len(line) == 40:
                        return line.strip().split()[-1]

                # Fallback: get latest commit SHA
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if sha_result.returncode == 0:
                    return sha_result.stdout.strip()

            return None

        except Exception as e:
            self.logger.error("create_commit_failed", error=str(e))
            return None
