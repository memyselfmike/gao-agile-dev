"""Service for managing boilerplate cloning and template processing."""

import shutil
from pathlib import Path
from typing import Optional

import structlog

from gao_dev.sandbox.git_cloner import GitCloner

logger = structlog.get_logger(__name__)


class BoilerplateService:
    """
    Manages boilerplate repository cloning and integration.

    Responsible for:
    - Cloning Git repositories as boilerplate
    - Merging boilerplate contents into project directories
    - Processing template variables and substitution

    Attributes:
        git_cloner: GitCloner instance for repository operations
    """

    def __init__(self, git_cloner: Optional[GitCloner] = None):
        """
        Initialize boilerplate service.

        Args:
            git_cloner: Optional GitCloner instance (creates default if not provided)
        """
        self.git_cloner = git_cloner or GitCloner()

    def set_git_cloner(self, git_cloner: GitCloner) -> None:
        """
        Set or update the GitCloner instance.

        Useful for testing or dynamic configuration.

        Args:
            git_cloner: New GitCloner instance to use
        """
        self.git_cloner = git_cloner

    def clone_boilerplate(
        self,
        boilerplate_url: str,
        target_path: Path,
    ) -> None:
        """
        Clone boilerplate repository and merge into target directory.

        Creates a temporary clone, merges its contents into the target
        directory, then cleans up the .git directory and temporary clone.

        Args:
            boilerplate_url: Git repository URL of boilerplate
            target_path: Directory to merge boilerplate into

        Raises:
            InvalidGitUrlError: If URL format is invalid
            GitCloneError: If cloning fails
        """
        target_path = Path(target_path)

        logger.info(
            "cloning_boilerplate",
            boilerplate_url=boilerplate_url,
            target_path=str(target_path),
        )

        try:
            # Clone into a temporary directory first
            temp_clone_dir = target_path / ".boilerplate_clone"

            self.git_cloner.clone_repository(boilerplate_url, temp_clone_dir)

            logger.info("boilerplate_cloned_to_temp", temp_dir=str(temp_clone_dir))

            # Merge boilerplate contents into target directory
            self._merge_boilerplate_contents(temp_clone_dir, target_path)

            # Remove .git directory
            git_dir = target_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
                logger.debug("removed_git_directory", path=str(git_dir))

            # Remove temp clone dir
            if temp_clone_dir.exists():
                shutil.rmtree(temp_clone_dir)
                logger.debug("removed_temp_directory", path=str(temp_clone_dir))

            logger.info(
                "boilerplate_integration_complete",
                target_path=str(target_path),
            )

        except Exception as e:
            logger.error(
                "boilerplate_cloning_failed",
                boilerplate_url=boilerplate_url,
                target_path=str(target_path),
                error=str(e),
            )
            raise

    def process_template(
        self,
        project_path: Path,
        variables: dict,
    ) -> None:
        """
        Process template variables in project files.

        Scans project files for template variables ({{ variable_name }})
        and substitutes them with provided values.

        Args:
            project_path: Root directory of project
            variables: Dictionary of variable name -> value mappings

        Raises:
            Exception: If template processing fails
        """
        project_path = Path(project_path)

        logger.info(
            "processing_template_variables",
            project_path=str(project_path),
            variable_count=len(variables),
        )

        try:
            # Scan and process files
            processed_count = 0

            for file_path in project_path.rglob("*"):
                # Skip directories and special files
                if file_path.is_dir():
                    continue
                if file_path.name.startswith("."):
                    continue

                # Try to process as text file
                try:
                    self._process_file_templates(file_path, variables)
                    processed_count += 1
                except (UnicodeDecodeError, IsADirectoryError):
                    # Skip binary files and directories
                    continue

            logger.info(
                "template_processing_complete",
                project_path=str(project_path),
                files_processed=processed_count,
            )

        except Exception as e:
            logger.error(
                "template_processing_failed",
                project_path=str(project_path),
                error=str(e),
            )
            raise

    def _merge_boilerplate_contents(self, source: Path, dest: Path) -> None:
        """
        Merge contents from boilerplate clone into project directory.

        Moves all files and directories from source to dest, excluding .git.

        Args:
            source: Source directory (boilerplate clone)
            dest: Destination directory (project root)
        """
        logger.debug(
            "merging_boilerplate_contents",
            source=str(source),
            dest=str(dest),
        )

        for item in source.iterdir():
            # Skip .git directory
            if item.name == ".git":
                continue

            dest_item = dest / item.name

            if item.is_dir():
                # Move directory
                if dest_item.exists():
                    # Merge if directory exists
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.move(str(item), str(dest_item))
            else:
                # Move file
                shutil.move(str(item), str(dest_item))

        logger.debug("merge_complete", dest=str(dest))

    def _process_file_templates(self, file_path: Path, variables: dict) -> None:
        """
        Process template variables in a single file.

        Args:
            file_path: Path to file to process
            variables: Dictionary of variable mappings
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace template variables
            modified = False
            for var_name, var_value in variables.items():
                template_str = f"{{{{ {var_name} }}}}"
                if template_str in content:
                    content = content.replace(template_str, str(var_value))
                    modified = True

            # Write back if modified
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.debug("template_file_processed", file_path=str(file_path))

        except (UnicodeDecodeError, IsADirectoryError):
            # Skip binary files and directories
            raise
