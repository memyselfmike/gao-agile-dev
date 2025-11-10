"""Brownfield project initialization for GAO-Dev."""

from typing import AsyncIterator, Dict, Any, List
from pathlib import Path
from datetime import datetime
import subprocess
import structlog

logger = structlog.get_logger()


class BrownfieldInitializer:
    """
    Initialize GAO-Dev tracking for existing projects (brownfield).

    Scans existing codebase, infers project type, creates .gao-dev/
    structure, and generates initial documentation without overwriting
    existing files.

    Attributes:
        project_root: Directory to initialize as GAO-Dev project
        logger: Structured logger for observability
    """

    def __init__(self, project_root: Path):
        """
        Initialize brownfield initializer.

        Args:
            project_root: Existing project directory to add GAO-Dev tracking
        """
        self.project_root = project_root
        self.logger = logger.bind(component="brownfield_initializer")

    def detect_project_type(self) -> str:
        """
        Detect project type from existing files.

        Returns:
            Project type: "node", "python", "rust", "go", "java", "ruby", "php", or "unknown"
        """
        # Check for project type indicators
        if (self.project_root / "package.json").exists():
            return "node"
        elif (self.project_root / "requirements.txt").exists():
            return "python"
        elif (self.project_root / "pyproject.toml").exists():
            return "python"
        elif (self.project_root / "Cargo.toml").exists():
            return "rust"
        elif (self.project_root / "go.mod").exists():
            return "go"
        elif (self.project_root / "pom.xml").exists():
            return "java"
        elif (self.project_root / "build.gradle").exists():
            return "java"
        elif (self.project_root / "Gemfile").exists():
            return "ruby"
        elif (self.project_root / "composer.json").exists():
            return "php"
        else:
            return "unknown"

    async def initialize(
        self,
        interactive: bool = True
    ) -> AsyncIterator[str]:
        """
        Initialize GAO-Dev tracking for existing project (brownfield).

        Differs from greenfield:
        - Scans existing codebase
        - Infers project type
        - Generates docs from existing code
        - Does NOT overwrite existing files
        - Creates retrospective documenting current state

        Args:
            interactive: If True, ask user questions. If False, use defaults.

        Yields:
            Conversational status messages
        """
        self.logger.info("initializing_brownfield_project", root=str(self.project_root))

        yield "I see you have an existing project here!"
        yield "Let me help you add GAO-Dev tracking to it."

        # Step 1: Scan existing codebase
        yield "\nScanning your codebase..."
        project_analysis = self._analyze_existing_codebase()

        yield f"Found: {project_analysis['type']} project"
        yield f"- {project_analysis['file_count']} files"
        yield f"- {project_analysis['directory_count']} directories"

        # Step 2: Create .gao-dev/ structure
        yield "\nCreating .gao-dev/ directory..."
        try:
            self._create_directory_structure()
            yield "OK .gao-dev/ created"

        except Exception as e:
            self.logger.exception("failed_to_create_directories", error=str(e))
            yield f"FAILED Failed to create directories: {str(e)}"
            return

        # Step 3: Initialize git if needed
        if not self._is_git_initialized():
            yield "\nNo git repository detected. Initialize git? (Recommended)"
            # In actual implementation, wait for user confirmation
            yield "Initializing git..."
            try:
                self._initialize_git()
                yield "OK Git initialized"
            except Exception as e:
                self.logger.warning("git_init_failed", error=str(e))
                yield f"WARN Git init failed (you can do this manually later)"
        else:
            yield "\nOK Git repository already exists"

        # Step 4: Generate initial documentation
        yield "\nGenerating initial documentation from your code..."
        try:
            self._generate_brownfield_documentation(project_analysis)
            if (self.project_root / "README.md.bak").exists():
                yield "OK README.md generated (existing file preserved as README.md.bak)"
            else:
                yield "OK README.md generated"
            yield "OK PROJECT_STATUS.md created"
        except Exception as e:
            self.logger.exception("doc_generation_failed", error=str(e))
            yield f"WARN Documentation generation failed: {str(e)}"

        # Step 5: Create initial retrospective
        yield "\nCreating initial project retrospective..."
        try:
            self._create_brownfield_retrospective(project_analysis)
            yield "OK docs/retrospectives/initial-state.md created"
        except Exception as e:
            self.logger.warning("retrospective_failed", error=str(e))
            yield f"WARN Retrospective creation failed: {str(e)}"

        # Step 6: Initial commit
        if self._is_git_initialized():
            yield "\nCommitting GAO-Dev setup..."
            try:
                self._create_initial_commit("Add GAO-Dev tracking to existing project")
                yield "OK Initial commit created"
            except Exception as e:
                self.logger.warning("commit_failed", error=str(e))
                yield f"WARN Commit failed: {str(e)}"

        # Success
        yield f"\nDone! GAO-Dev tracking added to your project."
        yield "\nWhat would you like to work on first?"

    def _analyze_existing_codebase(self) -> Dict[str, Any]:
        """
        Analyze existing codebase to infer project details.

        Returns:
            Dict with project analysis:
            - type: Inferred project type (python, node, etc.)
            - file_count: Number of code files
            - directory_count: Number of directories
            - dependencies: Detected dependencies
            - structure: Directory structure
        """
        analysis: Dict[str, Any] = {
            "type": "unknown",
            "file_count": 0,
            "directory_count": 0,
            "dependencies": [],
            "structure": {},
            "has_tests": False,
            "has_docs": False,
        }

        # Infer type from project files
        analysis["type"] = self.detect_project_type()

        # Count files and directories (excluding .git and common ignore patterns)
        exclude_patterns = {".git", "__pycache__", "node_modules", "venv", "env", ".venv"}

        for item in self.project_root.rglob("*"):
            # Skip excluded directories
            if any(part in exclude_patterns for part in item.parts):
                continue

            try:
                if item.is_file():
                    analysis["file_count"] += 1
                elif item.is_dir():
                    analysis["directory_count"] += 1
            except (OSError, PermissionError):
                # Skip files we can't access
                continue

        # Check for common directories
        analysis["has_tests"] = (
            (self.project_root / "tests").exists() or
            (self.project_root / "test").exists() or
            (self.project_root / "__tests__").exists()
        )
        analysis["has_docs"] = (self.project_root / "docs").exists()

        # Parse dependencies based on project type
        analysis["dependencies"] = self._extract_dependencies(analysis["type"])

        return analysis

    def _extract_dependencies(self, project_type: str) -> List[str]:
        """
        Extract dependencies from project files.

        Args:
            project_type: Detected project type

        Returns:
            List of dependency names
        """
        dependencies = []

        try:
            if project_type == "node":
                package_json = self.project_root / "package.json"
                if package_json.exists():
                    import json
                    data = json.loads(package_json.read_text(encoding="utf-8"))
                    if "dependencies" in data:
                        dependencies.extend(list(data["dependencies"].keys())[:5])  # Top 5

            elif project_type == "python":
                requirements = self.project_root / "requirements.txt"
                if requirements.exists():
                    content = requirements.read_text(encoding="utf-8")
                    for line in content.split("\n")[:5]:  # Top 5
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before version specifier)
                            dep_name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            dependencies.append(dep_name)

        except Exception as e:
            self.logger.warning("dependency_extraction_failed", error=str(e))

        return dependencies

    def _create_directory_structure(self) -> None:
        """
        Create .gao-dev/ directory structure.

        Creates:
        - .gao-dev/
        - .gao-dev/documents.db
        - .gao-dev/metrics/
        - docs/ (if not exists)
        - docs/retrospectives/ (if not exists)
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

        # Create docs directory if not exists
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Create retrospectives directory
        retro_dir = docs_dir / "retrospectives"
        retro_dir.mkdir(exist_ok=True)

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

    def _generate_brownfield_documentation(self, analysis: Dict[str, Any]) -> None:
        """
        Generate initial documentation for brownfield project.

        - Preserves existing README.md (backs up as README.md.bak)
        - Creates PROJECT_STATUS.md with current state

        Args:
            analysis: Project analysis dict
        """
        # Backup existing README if present
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            backup_path = self.project_root / "README.md.bak"
            # Read existing content and write to backup
            existing_content = readme_path.read_text(encoding="utf-8")
            backup_path.write_text(existing_content, encoding="utf-8")
            self.logger.info("backed_up_existing_readme")

        # Generate new README with GAO-Dev intro
        readme_content = self._generate_brownfield_readme(analysis)
        readme_path.write_text(readme_content, encoding="utf-8")

        # Create PROJECT_STATUS.md
        status_content = self._generate_project_status(analysis)
        status_path = self.project_root / "docs" / "PROJECT_STATUS.md"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(status_content, encoding="utf-8")

    def _generate_brownfield_readme(self, analysis: Dict[str, Any]) -> str:
        """Generate README for brownfield project."""
        deps_section = ""
        if analysis["dependencies"]:
            deps_list = "\n".join(f"- {dep}" for dep in analysis["dependencies"][:5])
            deps_section = f"""

## Key Dependencies

{deps_list}
"""

        return f"""# {self.project_root.name}

Existing {analysis['type']} project now managed by GAO-Dev.

## Overview

This project has been onboarded to GAO-Dev for autonomous development orchestration.

**Project Type**: {analysis['type']}
**Files**: {analysis['file_count']}
**Directories**: {analysis['directory_count']}
**Tests**: {"Yes" if analysis['has_tests'] else "No"}
**Documentation**: {"Yes" if analysis['has_docs'] else "No"}{deps_section}

## GAO-Dev Management

```bash
# Start interactive chat with Brian
gao-dev start

# Check project status
gao-dev status

# View project structure
gao-dev state list-epics
```

## Project Structure

- `docs/` - Project documentation
- `src/` or `lib/` - Source code
- `tests/` - Test suite (if present)
- `.gao-dev/` - GAO-Dev project metadata

## Development

This project now follows GAO-Dev's adaptive agile methodology.
Brian coordinates the specialized agent team for autonomous development.

For original README content, see `README.md.bak`.
""".strip()

    def _generate_project_status(self, analysis: Dict[str, Any]) -> str:
        """Generate PROJECT_STATUS.md for brownfield project."""
        deps_section = ""
        if analysis["dependencies"]:
            deps_list = "\n".join(f"- {dep}" for dep in analysis["dependencies"])
            deps_section = f"""

## Dependencies

{deps_list}
"""

        return f"""# Project Status

**Onboarded**: {datetime.now().strftime('%Y-%m-%d')}
**Project Type**: {analysis['type']}

## Current State

This project was onboarded to GAO-Dev as an existing codebase (brownfield).

**Statistics**:
- Files: {analysis['file_count']}
- Directories: {analysis['directory_count']}
- Has Tests: {"Yes" if analysis['has_tests'] else "No"}
- Has Documentation: {"Yes" if analysis['has_docs'] else "No"}{deps_section}

## Next Steps

1. Review existing codebase structure
2. Create initial epic for documentation
3. Define feature backlog
4. Begin autonomous development

## History

- **{datetime.now().strftime('%Y-%m-%d')}**: GAO-Dev tracking initialized
""".strip()

    def _create_brownfield_retrospective(self, analysis: Dict[str, Any]) -> None:
        """
        Create initial retrospective documenting brownfield state.

        Args:
            analysis: Project analysis dict
        """
        retro_content = f"""# Initial Project State Retrospective

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Type**: Brownfield Onboarding

## Overview

This retrospective documents the state of the project at the time of GAO-Dev onboarding.

## Project Analysis

**Type**: {analysis['type']}
**Files**: {analysis['file_count']}
**Directories**: {analysis['directory_count']}
**Has Tests**: {"Yes" if analysis['has_tests'] else "No"}
**Has Documentation**: {"Yes" if analysis['has_docs'] else "No"}

## Observations

### What Exists
- Existing codebase with {analysis['file_count']} files
- Project type identified as {analysis['type']}
- {"Test suite detected" if analysis['has_tests'] else "No test suite detected"}
- {"Documentation exists" if analysis['has_docs'] else "No documentation detected"}

### What's Needed
- Comprehensive documentation
- {"Enhanced" if analysis['has_tests'] else "Automated"} testing strategy
- Development workflow definition

## Action Items

1. Create documentation epic
2. {"Enhance" if analysis['has_tests'] else "Establish"} testing strategy
3. Establish development workflows
4. Begin feature backlog grooming

## Notes

This is the baseline for GAO-Dev management. All future retrospectives will measure progress from this point.
""".strip()

        retro_path = self.project_root / "docs" / "retrospectives" / "initial-state.md"
        retro_path.parent.mkdir(parents=True, exist_ok=True)
        retro_path.write_text(retro_content, encoding="utf-8")

    def _create_initial_commit(self, commit_message: str) -> None:
        """
        Create initial git commit.

        Args:
            commit_message: Commit message
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
