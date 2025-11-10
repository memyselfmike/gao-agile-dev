"""Greenfield project initialization for GAO-Dev."""

from typing import AsyncIterator, Dict, Any
from pathlib import Path
from datetime import datetime
import subprocess
import structlog

logger = structlog.get_logger()


class GreenfieldInitializer:
    """
    Guide users through new GAO-Dev project initialization.

    Provides conversational flow for creating .gao-dev/ structure,
    initializing git, and creating initial documents.

    Attributes:
        project_root: Directory to initialize as GAO-Dev project
        logger: Structured logger for observability
    """

    def __init__(self, project_root: Path):
        """
        Initialize greenfield initializer.

        Args:
            project_root: Directory to initialize as GAO-Dev project
        """
        self.project_root = project_root
        self.logger = logger.bind(component="greenfield_initializer")

    def detect_project_type(self) -> str:
        """
        Detect if project is greenfield or brownfield.

        Returns:
            "greenfield" - No existing code detected
            "brownfield" - Existing code without .gao-dev/ detected
        """
        # Check for common project files
        project_indicators = [
            "package.json",  # Node.js
            "requirements.txt",  # Python
            "pyproject.toml",  # Python
            "Cargo.toml",  # Rust
            "go.mod",  # Go
            "pom.xml",  # Java Maven
            "build.gradle",  # Java Gradle
            "Gemfile",  # Ruby
            "composer.json",  # PHP
        ]

        # Check for directories
        code_directories = ["src", "lib", "app", "pkg", "cmd"]

        has_project_files = any(
            (self.project_root / indicator).exists()
            for indicator in project_indicators
        )

        has_code_dirs = any(
            (self.project_root / dir_name).exists() and (self.project_root / dir_name).is_dir()
            for dir_name in code_directories
        )

        if has_project_files or has_code_dirs:
            return "brownfield"
        return "greenfield"

    async def initialize(
        self,
        interactive: bool = True
    ) -> AsyncIterator[str]:
        """
        Initialize new GAO-Dev project conversationally.

        Args:
            interactive: If True, ask user questions. If False, use defaults.

        Yields:
            Conversational status messages
        """
        self.logger.info("initializing_greenfield_project", root=str(self.project_root))

        yield "Welcome! Let's set up your new GAO-Dev project."

        # Step 1: Gather information
        if interactive:
            project_info = await self._gather_project_info()
        else:
            project_info = self._get_default_project_info()

        # Step 2: Create directory structure
        yield f"\nCreating project structure for '{project_info['name']}'..."

        try:
            self._create_directory_structure()
            yield "OK Project directories created"

        except Exception as e:
            self.logger.exception("failed_to_create_directories", error=str(e))
            yield f"FAILED Failed to create directories: {str(e)}"
            return

        # Step 3: Initialize git (if needed)
        if not self._is_git_initialized():
            yield "\nInitializing git repository..."
            try:
                self._initialize_git()
                yield "OK Git repository initialized"
            except Exception as e:
                self.logger.warning("git_init_failed", error=str(e))
                yield f"WARN Git initialization failed: {str(e)}"
                yield "  (You can initialize git manually later)"

        else:
            yield "\nOK Git repository already initialized"

        # Step 4: Create initial documents
        yield "\nCreating initial documents..."
        try:
            self._create_initial_documents(project_info)
            yield "OK README.md created"
            yield "OK .gitignore created"
        except Exception as e:
            self.logger.exception("failed_to_create_documents", error=str(e))
            yield f"FAILED Failed to create documents: {str(e)}"
            return

        # Step 5: Initial git commit
        if self._is_git_initialized():
            try:
                self._create_initial_commit(project_info['name'])
                yield "OK Initial commit created"
            except Exception as e:
                self.logger.warning("initial_commit_failed", error=str(e))
                yield f"WARN Initial commit failed: {str(e)}"

        # Step 6: Success message
        yield f"\nDone! Project '{project_info['name']}' initialized successfully!"
        yield "\nYou're all set! What would you like to build first?"

    async def _gather_project_info(self) -> Dict[str, str]:
        """
        Gather project information from user.

        NOTE: In actual implementation, this would use
        prompt_toolkit to get user input. For this design,
        we'll use a simplified approach.

        Returns:
            Project information dict
        """
        # For Story 30.6, we'll use defaults and enhancement
        # with real interactive prompts comes in future stories

        project_name = self.project_root.name or "my-project"

        return {
            "name": project_name,
            "type": "application",
            "description": f"A new GAO-Dev project: {project_name}"
        }

    def _get_default_project_info(self) -> Dict[str, str]:
        """Get default project information."""
        project_name = self.project_root.name or "my-project"

        return {
            "name": project_name,
            "type": "application",
            "description": f"A new GAO-Dev project: {project_name}"
        }

    def _create_directory_structure(self) -> None:
        """
        Create .gao-dev/ directory structure.

        Creates:
        - .gao-dev/
        - .gao-dev/documents.db (empty)
        - .gao-dev/metrics/
        - docs/
        - src/
        - tests/
        """
        self.logger.info("creating_directory_structure")

        # Create .gao-dev/
        gao_dev_dir = self.project_root / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Create documents.db (initialize database)
        # We need to create an empty database file first, then initialize it
        db_path = gao_dev_dir / "documents.db"

        # Create the database using StateTracker's initialization
        import sqlite3
        conn = sqlite3.connect(str(db_path))

        # Create tables using StateTracker's schema
        from gao_dev.core.state.state_tracker import StateTracker

        # Initialize with StateTracker to create schema
        # Note: StateTracker expects the file to exist
        conn.close()

        # Now initialize properly with StateTracker
        try:
            state_tracker = StateTracker(db_path)
        except Exception as e:
            # If StateTracker fails, database is at least created
            self.logger.warning("state_tracker_init_warning", error=str(e))

        # Create metrics directory
        metrics_dir = gao_dev_dir / "metrics"
        metrics_dir.mkdir(exist_ok=True)

        # Create .gitkeep for metrics
        gitkeep = metrics_dir / ".gitkeep"
        gitkeep.touch()

        # Create standard project directories
        (self.project_root / "docs").mkdir(exist_ok=True)
        (self.project_root / "src").mkdir(exist_ok=True)
        (self.project_root / "tests").mkdir(exist_ok=True)

        self.logger.info("directory_structure_created")

    def _is_git_initialized(self) -> bool:
        """Check if git repository is initialized."""
        git_dir = self.project_root / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def _initialize_git(self) -> None:
        """Initialize git repository."""
        self.logger.info("initializing_git")

        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )
            self.logger.info("git_initialized")

        except subprocess.CalledProcessError as e:
            self.logger.error("git_init_failed", error=e.stderr.decode())
            raise RuntimeError(f"Git initialization failed: {e.stderr.decode()}")

    def _create_initial_documents(self, project_info: Dict[str, str]) -> None:
        """
        Create initial project documents.

        Args:
            project_info: Project information
        """
        self.logger.info("creating_initial_documents")

        # Create README.md
        readme_content = self._generate_readme(project_info)
        readme_path = self.project_root / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        # Create .gitignore
        gitignore_content = self._generate_gitignore()
        gitignore_path = self.project_root / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding="utf-8")

        self.logger.info("initial_documents_created")

    def _generate_readme(self, project_info: Dict[str, str]) -> str:
        """Generate README.md content."""
        return f"""# {project_info['name']}

{project_info['description']}

## Overview

This project is managed by GAO-Dev, an autonomous AI development orchestration system.

## Getting Started

```bash
# Start interactive chat with Brian (AI Engineering Manager)
gao-dev start

# Check project status
gao-dev status

# List workflows
gao-dev list-workflows
```

## Project Structure

- `docs/` - Project documentation
- `src/` - Source code
- `tests/` - Test suite
- `.gao-dev/` - GAO-Dev project metadata (do not modify manually)

## Development

This project follows GAO-Dev's adaptive agile methodology with scale-adaptive routing.
Brian, your AI Engineering Manager, coordinates the specialized agent team:

- **John** - Product Manager (PRDs, features)
- **Winston** - Technical Architect (system design)
- **Sally** - UX Designer (user experience)
- **Bob** - Scrum Master (story management)
- **Amelia** - Software Developer (implementation)
- **Murat** - Test Architect (quality assurance)

## License

[Add your license here]
""".strip()

    def _generate_gitignore(self) -> str:
        """Generate .gitignore content."""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Environment
.env
.env.local

# GAO-Dev (keep metadata)
# .gao-dev/documents.db is tracked
.gao-dev/metrics/*
!.gao-dev/metrics/.gitkeep
""".strip()

    def _create_initial_commit(self, project_name: str) -> None:
        """
        Create initial git commit.

        Args:
            project_name: Name of project
        """
        self.logger.info("creating_initial_commit")

        try:
            # Add files
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            # Create commit
            commit_message = f"chore: Initialize GAO-Dev project '{project_name}'"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            self.logger.info("initial_commit_created")

        except subprocess.CalledProcessError as e:
            self.logger.error("commit_failed", error=e.stderr.decode())
            raise RuntimeError(f"Initial commit failed: {e.stderr.decode()}")
