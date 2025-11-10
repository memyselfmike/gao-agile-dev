# Story 30.2: Project Auto-Detection & Status Check

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.2
**Priority**: P0 (Critical - Foundation)
**Estimate**: 3 story points
**Duration**: 0.5-1 day
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 30.1 (REPL must exist)

---

## Story Description

Enhance Brian's greeting with automatic project detection and comprehensive status reporting. When `gao-dev start` launches, Brian should automatically detect if user is in a GAO-Dev project, load project status, and present a helpful summary in the greeting.

For greenfield projects (no `.gao-dev/`), Brian should detect this and offer to initialize.

---

## User Story

**As a** developer
**I want** Brian to automatically detect my project and show status on startup
**So that** I know where I am and what's been done without manually querying

---

## Acceptance Criteria

- [ ] Auto-detects `.gao-dev/` in current directory
- [ ] Auto-detects `.gao-dev/` in parent directories (up to 5 levels)
- [ ] Loads project status in <500ms
- [ ] Displays epic count, story count, recent commits
- [ ] Shows current epic in progress (if any)
- [ ] Detects greenfield projects (no `.gao-dev/`)
- [ ] Greeting includes status summary
- [ ] Status formatted beautifully with Rich
- [ ] 8+ unit tests for status detection and formatting
- [ ] Integration test: Status displayed on REPL startup

---

## Files to Create/Modify

### New Files
- `gao_dev/cli/project_status.py` (~250 LOC)
  - `ProjectStatusReporter` class
  - Auto-detection logic
  - Status querying via FastContextLoader
  - Status formatting for display

- `tests/cli/test_project_status.py` (~200 LOC)
  - Tests for auto-detection
  - Tests for status querying
  - Tests for formatting
  - Tests for greenfield detection

### Modified Files
- `gao_dev/cli/chat_repl.py` (~30 LOC modified)
  - Integrate `ProjectStatusReporter` in `__init__()`
  - Display status in `_show_greeting()`

---

## Technical Design

### ProjectStatusReporter Class

**Location**: `gao_dev/cli/project_status.py`

```python
"""Project detection and status reporting for interactive chat."""

from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import structlog

from gao_dev.core.state.fast_context_loader import FastContextLoader
from gao_dev.core.git.git_manager import GitManager

logger = structlog.get_logger()


@dataclass
class ProjectStatus:
    """
    Project status information.

    Attributes:
        exists: Whether .gao-dev/ project exists
        project_name: Name of project
        project_root: Path to project root
        epic_count: Number of epics
        story_count: Number of stories
        recent_commits: List of recent commit messages
        current_epic: Current epic in progress (if any)
        is_greenfield: True if no .gao-dev/ found
    """
    exists: bool
    project_name: Optional[str] = None
    project_root: Optional[Path] = None
    epic_count: int = 0
    story_count: int = 0
    recent_commits: list[str] = None
    current_epic: Optional[str] = None
    is_greenfield: bool = False


class ProjectStatusReporter:
    """
    Detect and report GAO-Dev project status.

    Auto-detects .gao-dev/ directory, queries project state,
    and formats status summary for display in chat.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize reporter.

        Args:
            project_root: Optional explicit project root.
                         If None, auto-detects from current directory.
        """
        self.project_root = project_root or self._auto_detect()
        self.logger = logger.bind(component="project_status")

    def _auto_detect(self) -> Optional[Path]:
        """
        Auto-detect project root by searching for .gao-dev/

        Searches current directory and up to 5 parent directories.

        Returns:
            Path to project root if found, None otherwise
        """
        self.logger.info("auto_detecting_project")

        current = Path.cwd()
        max_levels = 5

        for _ in range(max_levels):
            gao_dev_dir = current / ".gao-dev"
            if gao_dev_dir.exists() and gao_dev_dir.is_dir():
                self.logger.info("project_detected", path=str(current))
                return current

            # Move to parent
            parent = current.parent
            if parent == current:
                # Reached filesystem root
                break
            current = parent

        self.logger.info("no_project_detected")
        return None

    def get_status(self) -> ProjectStatus:
        """
        Get comprehensive project status.

        Returns:
            ProjectStatus with all available information
        """
        if not self.project_root:
            return ProjectStatus(exists=False, is_greenfield=True)

        self.logger.info("getting_project_status", project_root=str(self.project_root))

        try:
            # Load context from FastContextLoader
            db_path = self.project_root / ".gao-dev" / "documents.db"
            context_loader = FastContextLoader(db_path)

            # Get epics and stories
            epics = context_loader.get_epics()
            stories = context_loader.get_all_stories()

            # Get recent commits
            git_manager = GitManager(self.project_root)
            recent_commits = self._get_recent_commits(git_manager, count=5)

            # Determine current epic
            current_epic = self._determine_current_epic(epics)

            return ProjectStatus(
                exists=True,
                project_name=self._get_project_name(),
                project_root=self.project_root,
                epic_count=len(epics),
                story_count=len(stories),
                recent_commits=recent_commits,
                current_epic=current_epic,
                is_greenfield=False
            )

        except Exception as e:
            self.logger.exception("failed_to_get_status", error=str(e))
            # Return minimal status on error
            return ProjectStatus(
                exists=True,
                project_name=self._get_project_name(),
                project_root=self.project_root
            )

    def _get_project_name(self) -> str:
        """Get project name from directory."""
        if not self.project_root:
            return "Unknown"
        return self.project_root.name

    def _get_recent_commits(
        self,
        git_manager: GitManager,
        count: int = 5
    ) -> list[str]:
        """
        Get recent commit messages.

        Args:
            git_manager: GitManager instance
            count: Number of commits to retrieve

        Returns:
            List of commit messages (most recent first)
        """
        try:
            # Get commit log
            log = git_manager.get_log(max_count=count)
            return [commit["message"].split("\n")[0] for commit in log]
        except Exception as e:
            self.logger.warning("failed_to_get_commits", error=str(e))
            return []

    def _determine_current_epic(self, epics: list) -> Optional[str]:
        """
        Determine current epic in progress.

        Looks for epics with status "in_progress" or most recent epic.

        Args:
            epics: List of epic records

        Returns:
            Epic identifier (e.g., "Epic 30") or None
        """
        if not epics:
            return None

        # Look for in_progress epic
        for epic in epics:
            if epic.get("status") == "in_progress":
                return f"Epic {epic['epic_num']}: {epic['title']}"

        # Return most recent epic
        latest = max(epics, key=lambda e: e.get("created_at", ""))
        return f"Epic {latest['epic_num']}: {latest['title']}"

    def format_status(self, status: ProjectStatus) -> str:
        """
        Format status for display in chat greeting.

        Args:
            status: ProjectStatus to format

        Returns:
            Formatted status message (markdown)
        """
        if status.is_greenfield:
            return """
No GAO-Dev project detected in this directory.

Would you like me to initialize a new project?
Type 'init' to get started, or type your request and I'll help!
            """.strip()

        if not status.exists:
            return "Unable to load project status."

        # Format commit list
        commit_section = ""
        if status.recent_commits:
            commits_formatted = "\n".join(
                f"  - {commit}" for commit in status.recent_commits
            )
            commit_section = f"\n\n**Recent Activity**:\n{commits_formatted}"

        # Format current epic
        epic_section = ""
        if status.current_epic:
            epic_section = f"\n**Current Epic**: {status.current_epic}"

        return f"""
**Project**: {status.project_name}
**Epics**: {status.epic_count} | **Stories**: {status.story_count}{epic_section}{commit_section}
        """.strip()
```

### ChatREPL Integration

**Location**: `gao_dev/cli/chat_repl.py` (modify existing)

```python
class ChatREPL:
    """Interactive REPL for conversational chat with Brian."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize ChatREPL with project status."""
        self.project_root = project_root or Path.cwd()
        self.console = Console()
        self.history = InMemoryHistory()
        self.prompt_session = PromptSession(history=self.history)
        self.logger = logger.bind(component="chat_repl")

        # NEW: Initialize status reporter
        self.status_reporter = ProjectStatusReporter(self.project_root)

    async def _show_greeting(self) -> None:
        """Display welcome greeting with project status."""
        # Get project status
        status = self.status_reporter.get_status()

        # Format greeting with status
        greeting_text = f"""
# Welcome to GAO-Dev!

I'm Brian, your AI Engineering Manager.

{self.status_reporter.format_status(status)}

Type your requests in natural language, or type 'help' for available commands.
Type 'exit', 'quit', or 'bye' to end the session.
        """.strip()

        self.console.print()
        self.console.print(Panel(
            Markdown(greeting_text),
            title="[bold green]Brian[/bold green]",
            border_style="green"
        ))
        self.console.print()
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/cli/test_project_status.py`

**Test Cases**:

1. **test_auto_detect_current_directory**
   - `.gao-dev/` in current directory → Detected
   - Returns current directory as project root

2. **test_auto_detect_parent_directory**
   - `.gao-dev/` in parent directory → Detected
   - Returns parent directory as project root

3. **test_auto_detect_multiple_levels**
   - `.gao-dev/` 3 levels up → Detected
   - Returns correct ancestor directory

4. **test_auto_detect_not_found**
   - No `.gao-dev/` in hierarchy → Returns None
   - is_greenfield = True

5. **test_get_status_with_project**
   - Valid project → Returns full status
   - Epic count, story count correct

6. **test_get_status_greenfield**
   - No project → Returns greenfield status
   - exists = False, is_greenfield = True

7. **test_format_status_with_project**
   - Full status → Beautiful formatted output
   - Includes epics, stories, commits, current epic

8. **test_format_status_greenfield**
   - Greenfield status → Offers initialization
   - Message includes "init" suggestion

9. **test_recent_commits**
   - Git log → Returns last 5 commits
   - Format: commit message first line only

10. **test_determine_current_epic**
    - In-progress epic exists → Returns that epic
    - No in-progress → Returns most recent epic

**Example Test**:
```python
import pytest
from pathlib import Path
from gao_dev.cli.project_status import ProjectStatusReporter, ProjectStatus


def test_auto_detect_current_directory(tmp_path):
    """Test auto-detection in current directory."""
    # Create .gao-dev/ directory
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    # Change to project directory
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Auto-detect should find project
        reporter = ProjectStatusReporter()
        assert reporter.project_root == tmp_path
    finally:
        os.chdir(old_cwd)


def test_format_status_greenfield():
    """Test formatting for greenfield project."""
    reporter = ProjectStatusReporter(project_root=None)
    status = ProjectStatus(exists=False, is_greenfield=True)

    formatted = reporter.format_status(status)

    assert "No GAO-Dev project detected" in formatted
    assert "initialize a new project" in formatted
    assert "init" in formatted
```

### Integration Tests

**Location**: `tests/cli/test_chat_repl.py` (add to existing)

**Test Case**:

```python
@pytest.mark.asyncio
async def test_greeting_includes_status(tmp_path):
    """Test that greeting includes project status."""
    # Create mock project
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    # Create REPL
    repl = ChatREPL(project_root=tmp_path)

    # Capture greeting output
    from io import StringIO
    from rich.console import Console

    output = StringIO()
    console = Console(file=output, width=120)
    repl.console = console

    # Show greeting
    await repl._show_greeting()

    # Check output
    greeting_text = output.getvalue()
    assert "Welcome to GAO-Dev" in greeting_text
    assert "Brian" in greeting_text
    assert "Project:" in greeting_text or "No GAO-Dev project" in greeting_text
```

---

## Definition of Done

- [ ] Code written and follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] 8+ unit tests written and passing
- [ ] Integration test: Status displayed in greeting
- [ ] Manual testing: Status accurate for real project
- [ ] Performance: Status loads in <500ms
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.2 - Project Auto-Detection & Status Check (3 pts)`
- [ ] Documentation updated (inline docstrings)

---

## Dependencies

### Internal Dependencies
- Story 30.1 (ChatREPL must exist)
- FastContextLoader (Epic 25) - Query project state
- GitManager (Epic 23) - Get commit log
- Project detection utilities (Epic 20) - Pattern reference

### No New External Dependencies
All required libraries already in use:
- `structlog` - Logging
- `rich` - Formatting
- `pathlib` - Path handling

---

## Implementation Notes

### Auto-Detection Logic

**Search Order**:
1. Current directory: Check for `.gao-dev/`
2. Parent directory: Move up one level
3. Grandparent: Move up again
4. Continue up to 5 levels max
5. Stop at filesystem root

**Why 5 levels?**: Balance between finding deeply nested projects and performance.

### Status Query Performance

**Optimizations**:
- FastContextLoader has <5ms cache hit rate
- GitManager commit log is cached
- Status is computed once on startup, not per message

**Target**: <500ms from auto-detect to status displayed

### Greenfield Detection

**Pattern**:
- No `.gao-dev/` found → Greenfield
- Offer to initialize (Story 30.6)
- User can type "init" or just make a request

### Status Formatting

**Use Rich Markdown**:
- Bold for section headers
- Bullet points for commits
- Clean, scannable layout

**Example Output**:
```
Project: gao-agile-dev
Epics: 30 | Stories: 185
Current Epic: Epic 30: Interactive Brian Chat

Recent Activity:
  - feat(epic-30): Story 30.1 - Brian REPL Command (5 pts)
  - Merge Epic 29: Self-Learning Feedback Loop
  - feat(epic-29): Story 29.6 - Learning Decay & Confidence
  - feat(epic-29): Story 29.5 - Action Items Integration
  - feat(epic-29): Story 29.4 - Workflow Adjustment Engine
```

### Error Handling

**Graceful Degradation**:
- If status query fails, show minimal info
- Never crash REPL on status error
- Log errors for debugging

---

## Manual Testing Checklist

- [ ] Run `gao-dev start` in existing project
  - [ ] Status displayed in greeting
  - [ ] Epic count correct
  - [ ] Story count correct
  - [ ] Recent commits shown (last 5)
  - [ ] Current epic shown (if in progress)

- [ ] Run `gao-dev start` in parent of project
  - [ ] Auto-detects project (walks up tree)
  - [ ] Status still accurate

- [ ] Run `gao-dev start` in new directory (no project)
  - [ ] Detects greenfield
  - [ ] Offers to initialize
  - [ ] Doesn't crash

- [ ] Startup performance
  - [ ] <2 seconds from command to greeting
  - [ ] Status loads fast (<500ms)

---

## Next Steps

After Story 30.2 is complete:

**Story 30.5**: Add ChatSession for session state management (can be parallel)
**Story 30.3**: Add conversational Brian integration (builds on 30.1 + 30.2)

---

**Created**: 2025-11-10
**Status**: Ready to Implement
