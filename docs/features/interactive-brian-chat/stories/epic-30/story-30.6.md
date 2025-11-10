# Story 30.6: Greenfield & Brownfield Project Initialization

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.6
**Priority**: P1 (Important - New User Experience)
**Estimate**: 5 story points
**Duration**: 1-2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 30.1 (REPL), Story 30.2 (Status)
**Updated**: 2025-11-10 (Expanded to include brownfield initialization)

---

## Story Description

Create a guided, conversational flow for initializing GAO-Dev projects. Handle two scenarios:

1. **Greenfield**: No existing code, help user start from scratch
2. **Brownfield**: Existing code without `.gao-dev/`, help add GAO-Dev tracking

When Brian detects no `.gao-dev/` directory, determine if it's a greenfield or brownfield scenario, then guide the user through appropriate setup with questions, create the directory structure, initialize git (if needed), and create initial documents - all conversationally.

This story dramatically improves the user experience for both new projects and existing codebases by making initialization feel like a conversation rather than a configuration chore.

---

## User Story

**As a** user with a new or existing project
**I want** Brian to guide me through setting up GAO-Dev tracking
**So that** I can use GAO-Dev whether starting fresh or adding to existing code

---

## Acceptance Criteria

### Greenfield (New Projects)
- [ ] Detects greenfield projects (no `.gao-dev/`, no existing code)
- [ ] Conversational initialization flow (not just prompts)
- [ ] Asks for project name, type, description
- [ ] Creates `.gao-dev/` directory structure
- [ ] Initializes git repository
- [ ] Creates initial documents: README.md, .gitignore
- [ ] Creates standard directories (docs/, src/, tests/)
- [ ] Offers to create first feature (optional)

### Brownfield (Existing Projects)
- [ ] Detects brownfield projects (no `.gao-dev/`, existing code detected)
- [ ] Scans existing codebase for project structure
- [ ] Infers project type from existing files (package.json, requirements.txt, etc.)
- [ ] Offers: "I see you have an existing project. Would you like me to add GAO-Dev tracking?"
- [ ] Creates `.gao-dev/` directory structure
- [ ] Initializes git if not present (optional)
- [ ] Generates initial documentation based on existing code
- [ ] Does NOT overwrite existing files
- [ ] Creates first retrospective/status documenting current state

### Common
- [ ] Graceful cancellation: User can exit without completing
- [ ] 10+ unit tests for initialization flow (greenfield + brownfield)
- [ ] Integration test: Full greenfield initialization
- [ ] Integration test: Full brownfield initialization

---

## Files to Create/Modify

### New Files
- `gao_dev/cli/greenfield_initializer.py` (~450 LOC)
  - `GreenfieldInitializer` class
  - `BrownfieldInitializer` class (or integrated into Greenfield class)
  - Conversational initialization flow for both scenarios
  - Project structure creation
  - Git initialization
  - Codebase scanning for brownfield
  - Documentation generation from existing code

- `tests/cli/test_greenfield_initializer.py` (~350 LOC)
  - Tests for greenfield initialization flow
  - Tests for brownfield detection and initialization
  - Tests for directory creation
  - Tests for git initialization
  - Tests for codebase scanning
  - Tests for cancellation

### Modified Files
- `gao_dev/orchestrator/conversational_brian.py` (~40 LOC modified)
  - Integrate greenfield initialization
  - Detect "init" command in user input

- `gao_dev/cli/project_status.py` (~20 LOC modified)
  - Enhance greenfield detection message
  - Point to initialization flow

---

## Technical Design

### GreenfieldInitializer Class

**Location**: `gao_dev/cli/greenfield_initializer.py`

```python
"""Greenfield project initialization for GAO-Dev."""

from typing import AsyncIterator, Optional, Dict, Any
from pathlib import Path
import subprocess
import structlog

logger = structlog.get_logger()


class GreenfieldInitializer:
    """
    Guide users through new GAO-Dev project initialization.

    Provides conversational flow for creating .gao-dev/ structure,
    initializing git, and creating initial documents.
    """

    def __init__(self, project_root: Path):
        """
        Initialize greenfield initializer.

        Args:
            project_root: Directory to initialize as GAO-Dev project
        """
        self.project_root = project_root
        self.logger = logger.bind(component="greenfield_initializer")

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
            yield "✓ Project directories created"

        except Exception as e:
            self.logger.exception("failed_to_create_directories", error=str(e))
            yield f"✗ Failed to create directories: {str(e)}"
            return

        # Step 3: Initialize git (if needed)
        if not self._is_git_initialized():
            yield "\nInitializing git repository..."
            try:
                self._initialize_git()
                yield "✓ Git repository initialized"
            except Exception as e:
                self.logger.warning("git_init_failed", error=str(e))
                yield f"⚠ Git initialization failed: {str(e)}"
                yield "  (You can initialize git manually later)"

        else:
            yield "\n✓ Git repository already initialized"

        # Step 4: Create initial documents
        yield "\nCreating initial documents..."
        try:
            self._create_initial_documents(project_info)
            yield "✓ README.md created"
            yield "✓ .gitignore created"
        except Exception as e:
            self.logger.exception("failed_to_create_documents", error=str(e))
            yield f"✗ Failed to create documents: {str(e)}"
            return

        # Step 5: Initial git commit
        if self._is_git_initialized():
            try:
                self._create_initial_commit(project_info['name'])
                yield "✓ Initial commit created"
            except Exception as e:
                self.logger.warning("initial_commit_failed", error=str(e))
                yield f"⚠ Initial commit failed: {str(e)}"

        # Step 6: Success message
        yield f"\n🎉 Project '{project_info['name']}' initialized successfully!"
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

    def _create_directory_structure(self):
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
        from gao_dev.core.state.git_integrated_state_manager import GitIntegratedStateManager

        state_manager = GitIntegratedStateManager(self.project_root)
        # Database auto-created on initialization

        # Create metrics directory
        metrics_dir = gao_dev_dir / "metrics"
        metrics_dir.mkdir(exist_ok=True)

        # Create standard project directories
        (self.project_root / "docs").mkdir(exist_ok=True)
        (self.project_root / "src").mkdir(exist_ok=True)
        (self.project_root / "tests").mkdir(exist_ok=True)

        self.logger.info("directory_structure_created")

    def _is_git_initialized(self) -> bool:
        """Check if git repository is initialized."""
        git_dir = self.project_root / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def _initialize_git(self):
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

    def _create_initial_documents(self, project_info: Dict[str, str]):
        """
        Create initial project documents.

        Args:
            project_info: Project information
        """
        self.logger.info("creating_initial_documents")

        # Create README.md
        readme_content = self._generate_readme(project_info)
        readme_path = self.project_root / "README.md"
        readme_path.write_text(readme_content)

        # Create .gitignore
        gitignore_content = self._generate_gitignore()
        gitignore_path = self.project_root / ".gitignore"
        gitignore_path.write_text(gitignore_content)

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

    def _create_initial_commit(self, project_name: str):
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
```

---

### Brownfield Detection & Initialization

Add these methods to `GreenfieldInitializer` class for brownfield support:

```python
class GreenfieldInitializer:
    """Initialize GAO-Dev tracking for greenfield and brownfield projects."""

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
            (self.project_root / dir_name).exists()
            for dir_name in code_directories
        )

        if has_project_files or has_code_dirs:
            return "brownfield"
        return "greenfield"

    async def initialize_brownfield(
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
            yield "OK README.md generated (existing file preserved as README.md.bak)"
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
        analysis = {
            "type": "unknown",
            "file_count": 0,
            "directory_count": 0,
            "dependencies": [],
            "structure": {}
        }

        # Infer type from project files
        if (self.project_root / "package.json").exists():
            analysis["type"] = "node"
        elif (self.project_root / "requirements.txt").exists():
            analysis["type"] = "python"
        elif (self.project_root / "pyproject.toml").exists():
            analysis["type"] = "python"
        elif (self.project_root / "Cargo.toml").exists():
            analysis["type"] = "rust"
        elif (self.project_root / "go.mod").exists():
            analysis["type"] = "go"

        # Count files and directories
        for item in self.project_root.rglob("*"):
            if item.is_file():
                analysis["file_count"] += 1
            elif item.is_dir():
                analysis["directory_count"] += 1

        return analysis

    def _generate_brownfield_documentation(self, analysis: Dict[str, Any]):
        """
        Generate initial documentation for brownfield project.

        - Preserves existing README.md (backs up as README.md.bak)
        - Creates PROJECT_STATUS.md with current state
        """
        # Backup existing README if present
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            backup_path = self.project_root / "README.md.bak"
            readme_path.rename(backup_path)
            self.logger.info("backed_up_existing_readme")

        # Generate new README with GAO-Dev intro
        readme_content = self._generate_brownfield_readme(analysis)
        readme_path.write_text(readme_content)

        # Create PROJECT_STATUS.md
        status_content = self._generate_project_status(analysis)
        status_path = self.project_root / "docs" / "PROJECT_STATUS.md"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(status_content)

    def _generate_brownfield_readme(self, analysis: Dict[str, Any]) -> str:
        """Generate README for brownfield project."""
        return f"""# {self.project_root.name}

Existing {analysis['type']} project now managed by GAO-Dev.

## Overview

This project has been onboarded to GAO-Dev for autonomous development orchestration.

**Project Type**: {analysis['type']}
**Files**: {analysis['file_count']}
**Directories**: {analysis['directory_count']}

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
- `src/` - Source code
- `tests/` - Test suite (if present)
- `.gao-dev/` - GAO-Dev project metadata

## Development

This project now follows GAO-Dev's adaptive agile methodology.
Brian coordinates the specialized agent team for autonomous development.

For original README content, see `README.md.bak`.
        """.strip()

    def _generate_project_status(self, analysis: Dict[str, Any]) -> str:
        """Generate PROJECT_STATUS.md for brownfield project."""
        return f"""# Project Status

**Onboarded**: {datetime.now().strftime('%Y-%m-%d')}
**Project Type**: {analysis['type']}

## Current State

This project was onboarded to GAO-Dev as an existing codebase (brownfield).

**Statistics**:
- Files: {analysis['file_count']}
- Directories: {analysis['directory_count']}

## Next Steps

1. Review existing codebase structure
2. Create initial epic for documentation
3. Define feature backlog
4. Begin autonomous development

## History

- **{datetime.now().strftime('%Y-%m-%d')}**: GAO-Dev tracking initialized
        """.strip()

    def _create_brownfield_retrospective(self, analysis: Dict[str, Any]):
        """Create initial retrospective documenting brownfield state."""
        retro_content = f"""# Initial Project State Retrospective

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Type**: Brownfield Onboarding

## Overview

This retrospective documents the state of the project at the time of GAO-Dev onboarding.

## Project Analysis

**Type**: {analysis['type']}
**Files**: {analysis['file_count']}
**Directories**: {analysis['directory_count']}

## Observations

### What Exists
- Existing codebase with {analysis['file_count']} files
- Project type identified as {analysis['type']}

### What's Needed
- Comprehensive documentation
- Automated testing strategy
- Development workflow definition

## Action Items

1. Create documentation epic
2. Define testing strategy
3. Establish development workflows
4. Begin feature backlog grooming

## Notes

This is the baseline for GAO-Dev management. All future retrospectives will measure progress from this point.
        """.strip()

        retro_path = self.project_root / "docs" / "retrospectives" / "initial-state.md"
        retro_path.parent.mkdir(parents=True, exist_ok=True)
        retro_path.write_text(retro_content)
```

### ConversationalBrian Integration

**Location**: `gao_dev/orchestrator/conversational_brian.py` (modify)

```python
class ConversationalBrian:
    """Conversational wrapper around BrianOrchestrator."""

    async def handle_input(
        self,
        user_input: str,
        session: 'ChatSession'
    ) -> AsyncIterator[str]:
        """Handle user input conversationally."""
        # ... (existing code)

        # NEW: Check for initialization command
        if self._is_init_command(user_input):
            async for response in self._handle_initialization(session):
                yield response
            return

        # ... (rest of existing handlers)

    def _is_init_command(self, user_input: str) -> bool:
        """Check if input is initialization command."""
        user_lower = user_input.lower().strip()
        return user_lower in ["init", "initialize", "setup", "start new project"]

    async def _handle_initialization(
        self,
        session: 'ChatSession'
    ) -> AsyncIterator[str]:
        """Handle project initialization."""
        from gao_dev.cli.greenfield_initializer import GreenfieldInitializer

        # Check if project already exists
        gao_dev_dir = session.context.project_root / ".gao-dev"
        if gao_dev_dir.exists():
            yield "This directory already has a GAO-Dev project."
            yield "Would you like to reinitialize? (This will overwrite existing setup)"
            # NOTE: Reinitialize flow could be added in future
            return

        # Initialize greenfield project
        initializer = GreenfieldInitializer(session.context.project_root)

        async for message in initializer.initialize(interactive=True):
            yield message
```

### ProjectStatusReporter Enhancement

**Location**: `gao_dev/cli/project_status.py` (modify)

```python
def format_status(self, status: ProjectStatus) -> str:
    """Format status for display in chat greeting."""
    if status.is_greenfield:
        return """
No GAO-Dev project detected in this directory.

Would you like me to initialize a new project?
**Type 'init' to get started**, or just tell me what you want to build!
        """.strip()

    # ... (rest of existing formatting)
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/cli/test_greenfield_initializer.py`

**Greenfield Test Cases**:

1. **test_detect_greenfield**
   - Empty directory → Detected as greenfield
   - No project files present

2. **test_initialize_greenfield_creates_directories**
   - Initialize → `.gao-dev/` created
   - Standard directories created (docs, src, tests)

3. **test_initialize_greenfield_creates_database**
   - Initialize → `documents.db` created
   - Database is valid SQLite file

4. **test_initialize_greenfield_creates_git**
   - No git → Initialize → `.git/` created
   - Git repository valid

5. **test_initialize_greenfield_creates_readme**
   - Initialize → README.md created
   - Contains project name and GAO-Dev intro

6. **test_initialize_greenfield_creates_gitignore**
   - Initialize → .gitignore created
   - Contains standard patterns

7. **test_initialize_greenfield_creates_initial_commit**
   - Initialize with git → Initial commit created
   - Commit message correct

**Brownfield Test Cases**:

8. **test_detect_brownfield_node_project**
   - package.json present → Detected as brownfield
   - Project type inferred as "node"

9. **test_detect_brownfield_python_project**
   - requirements.txt present → Detected as brownfield
   - Project type inferred as "python"

10. **test_analyze_existing_codebase**
    - Existing files scanned correctly
    - File count and directory count accurate
    - Project type inferred correctly

11. **test_initialize_brownfield_preserves_files**
    - Existing README.md → Backed up as README.md.bak
    - Existing files NOT overwritten
    - New README.md references backup

12. **test_initialize_brownfield_creates_documentation**
    - PROJECT_STATUS.md created
    - Contains project statistics
    - Retrospective created in docs/retrospectives/

13. **test_initialize_brownfield_skips_existing_git**
    - Git exists → Not reinitialized
    - No error thrown

14. **test_brownfield_retrospective_content**
    - Retrospective includes project analysis
    - Action items present
    - Baseline state documented

**Common Test Cases**:

15. **test_is_init_command**
    - "init" → Detected as init command
    - "initialize" → Detected
    - "build app" → Not detected

**Example Test**:
```python
import pytest
from pathlib import Path
from gao_dev.cli.greenfield_initializer import GreenfieldInitializer


@pytest.mark.asyncio
async def test_initialize_creates_directories(tmp_path):
    """Test that initialization creates required directories."""
    # Create initializer
    initializer = GreenfieldInitializer(tmp_path)

    # Initialize (non-interactive)
    messages = []
    async for message in initializer.initialize(interactive=False):
        messages.append(message)

    # Assert directories created
    assert (tmp_path / ".gao-dev").exists()
    assert (tmp_path / ".gao-dev" / "documents.db").exists()
    assert (tmp_path / "docs").exists()
    assert (tmp_path / "src").exists()
    assert (tmp_path / "tests").exists()

    # Assert success message
    assert any("initialized successfully" in msg for msg in messages)


@pytest.mark.asyncio
async def test_initialize_creates_git(tmp_path):
    """Test that initialization creates git repository."""
    initializer = GreenfieldInitializer(tmp_path)

    # Initialize
    async for message in initializer.initialize(interactive=False):
        pass

    # Assert git initialized
    assert (tmp_path / ".git").exists()

    # Verify git repo is valid
    import subprocess
    result = subprocess.run(
        ["git", "status"],
        cwd=tmp_path,
        capture_output=True
    )
    assert result.returncode == 0
```

---

## Definition of Done

- [ ] Code written and follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] 10+ unit tests written and passing (greenfield + brownfield)
- [ ] Integration test: Full greenfield initialization
- [ ] Integration test: Full brownfield initialization
- [ ] Manual testing: Greenfield init flow works conversationally
- [ ] Manual testing: Brownfield init flow works conversationally
- [ ] Directories created correctly for both scenarios
- [ ] Git initialized properly (or skipped if present)
- [ ] Initial documents created appropriately
- [ ] Brownfield: Existing files preserved and backed up
- [ ] Brownfield: Project analysis accurate
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.6 - Greenfield & Brownfield Init (5 pts)`
- [ ] Documentation updated (inline docstrings)

---

## Dependencies

### Internal Dependencies
- Story 30.1 (ChatREPL must exist)
- Story 30.2 (ProjectStatusReporter for detection)
- Story 30.3 (ConversationalBrian for integration)
- GitIntegratedStateManager (Epic 27)

### No New External Dependencies

---

## Implementation Notes

### Interactive vs Non-Interactive

**Story 30.6 (This Story)**: Non-interactive (uses defaults)
- Project name from directory name
- Default project type: "application"
- Default description

**Future Enhancement**: Interactive prompts
- Use `prompt_toolkit` to ask questions
- Multi-choice for project type
- Optional description

### Directory Structure

**Standard Structure**:
```
my-project/
├── .gao-dev/
│   ├── documents.db
│   └── metrics/
├── docs/
├── src/
├── tests/
├── README.md
└── .gitignore
```

**Rationale**:
- `.gao-dev/` - GAO-Dev metadata (tracked in git)
- `docs/` - Documentation (PRDs, architecture, etc.)
- `src/` - Source code
- `tests/` - Test suite

### Git Initialization Safety

**Checks**:
1. Check if `.git/` exists before initializing
2. If exists, skip git initialization (no error)
3. If git init fails, warn but continue (non-blocking)

**Rationale**: Some users may initialize git manually or clone

### Initial Commit

**Contents**:
- All created files (README, .gitignore, .gao-dev/)
- Message: "chore: Initialize GAO-Dev project '{name}'"

**Optional**: If git initialization fails, skip commit (no error)

---

## Manual Testing Checklist

### Greenfield Scenario

- [ ] Create new empty directory
- [ ] `cd` into directory
- [ ] Run `gao-dev start`
  - [ ] Brian detects greenfield
  - [ ] Greeting offers initialization: "Type 'init' to get started"
- [ ] Type: "init"
  - [ ] Initialization flow starts
  - [ ] Progress messages shown
  - [ ] Directories created (docs, src, tests)
  - [ ] Git initialized
  - [ ] README and .gitignore created
  - [ ] Initial commit created
  - [ ] Success message shown
- [ ] Check created structure
  - [ ] `.gao-dev/` exists with `documents.db`
  - [ ] `docs/`, `src/`, `tests/` exist
  - [ ] `README.md` contains project name
  - [ ] `.gitignore` has standard patterns
  - [ ] `git log` shows initial commit
- [ ] Exit and restart `gao-dev start`
  - [ ] Brian detects existing project
  - [ ] Shows status (not greenfield message)

### Brownfield Scenario

- [ ] Create directory with existing code
  - [ ] Add `package.json` or `requirements.txt`
  - [ ] Add `src/` directory with some files
  - [ ] Add existing `README.md` with content
- [ ] `cd` into directory
- [ ] Run `gao-dev start`
  - [ ] Brian detects brownfield
  - [ ] Offers: "I see you have an existing project. Add GAO-Dev tracking?"
- [ ] Type: "init" (or "yes")
  - [ ] Scans existing codebase
  - [ ] Reports project type (node/python/etc)
  - [ ] Reports file/directory count
  - [ ] Creates `.gao-dev/` directory
  - [ ] Backs up existing README.md as README.md.bak
  - [ ] Creates new README.md with GAO-Dev intro
  - [ ] Creates PROJECT_STATUS.md
  - [ ] Creates docs/retrospectives/initial-state.md
  - [ ] Git initialized if not present
  - [ ] Initial commit created
  - [ ] Success message shown
- [ ] Check created structure
  - [ ] `.gao-dev/` exists with `documents.db`
  - [ ] `README.md.bak` contains original content
  - [ ] New `README.md` references backup
  - [ ] `docs/PROJECT_STATUS.md` exists
  - [ ] `docs/retrospectives/initial-state.md` exists
  - [ ] `git log` shows "Add GAO-Dev tracking" commit
- [ ] Exit and restart `gao-dev start`
  - [ ] Brian detects existing GAO-Dev project
  - [ ] Shows status with file counts

---

## Next Steps

After Story 30.6 is complete:

**Story 30.7**: Testing and documentation for entire Epic 30

---

**Created**: 2025-11-10
**Updated**: 2025-11-10 (Expanded to include brownfield initialization)
**Status**: Ready to Implement
