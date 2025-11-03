# Story 1.4: Sandbox init Command

**Epic**: Epic 1 - Sandbox Infrastructure
**Status**: Done
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Completed**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev
**I want** to initialize new sandbox projects with a single command
**So that** I can quickly create isolated development environments for testing

---

## Acceptance Criteria

### AC1: Basic Initialization
- ✅ Can initialize sandbox with project name only
- ✅ Creates project directory structure
- ✅ Creates `.sandbox.yaml` metadata file
- ✅ Initializes Git repository
- ✅ Sets up proper directory permissions

### AC2: Boilerplate Support
- ✅ Can initialize with boilerplate URL (--boilerplate flag)
- ✅ Can specify boilerplate branch (--branch flag)
- ✅ Validates boilerplate URL before cloning
- ✅ Handles boilerplate cloning errors gracefully

### AC3: Configuration Options
- ✅ Can specify custom description (--description flag)
- ✅ Can set initial tags (--tags flag)
- ✅ Can override default sandbox location
- ✅ Validates all configuration inputs

### AC4: User Feedback
- ✅ Shows clear progress messages during initialization
- ✅ Reports successful initialization with project details
- ✅ Provides helpful error messages on failure
- ✅ Includes next steps in success message

### AC5: Error Handling
- ✅ Prevents duplicate project names
- ✅ Validates project name format (alphanumeric, hyphens, underscores)
- ✅ Handles filesystem errors gracefully
- ✅ Cleans up partial initialization on failure

---

## Technical Details

### Implementation Approach

**Command Definition**: Add to `gao_dev/cli/sandbox_commands.py`

```python
@sandbox_group.command("init")
@click.argument("project_name")
@click.option("--boilerplate", "-b", help="Git repository URL for boilerplate")
@click.option("--branch", default=None, help="Boilerplate branch to use")
@click.option("--description", "-d", help="Project description")
@click.option("--tags", help="Comma-separated tags")
def sandbox_init(
    project_name: str,
    boilerplate: Optional[str],
    branch: Optional[str],
    description: Optional[str],
    tags: Optional[str],
) -> None:
    """
    Initialize a new sandbox project.

    Creates project directory, metadata, and optionally clones boilerplate.
    """
    pass
```

### Workflow

1. **Validate Input**: Check project name format and uniqueness
2. **Create Project**: Use `SandboxManager.create_project()`
3. **Clone Boilerplate**: If provided, clone repository
4. **Initialize Git**: Create git repository
5. **Save Metadata**: Write `.sandbox.yaml`
6. **Report Success**: Display project details and next steps

### Metadata Structure

The `.sandbox.yaml` file created:

```yaml
name: "project-name"
description: "Project description"
created_at: "2025-10-27T10:30:00Z"
status: "active"
tags: ["tag1", "tag2"]
boilerplate:
  url: "https://github.com/user/repo"
  branch: "main"
  cloned_at: "2025-10-27T10:30:15Z"
git:
  initialized: true
  initial_commit: "abc123"
```

---

## Testing Requirements

### Unit Tests

```python
def test_sandbox_init_basic():
    """Test basic sandbox initialization without boilerplate."""
    pass

def test_sandbox_init_with_boilerplate():
    """Test initialization with boilerplate cloning."""
    pass

def test_sandbox_init_duplicate_name():
    """Test that duplicate project names are rejected."""
    pass

def test_sandbox_init_invalid_name():
    """Test that invalid project names are rejected."""
    pass

def test_sandbox_init_with_options():
    """Test initialization with description and tags."""
    pass

def test_sandbox_init_cleanup_on_failure():
    """Test cleanup when initialization fails."""
    pass

def test_sandbox_init_git_initialization():
    """Test that git repository is properly initialized."""
    pass
```

### Integration Tests

- Test with real boilerplate repository
- Test with non-existent boilerplate
- Test creating multiple projects
- Test filesystem permission issues

---

## Definition of Done

- [X] `sandbox init` command implemented
- [X] All unit tests passing (>80% coverage)
- [X] Integration tests passing
- [X] Boilerplate cloning working
- [X] Git initialization working
- [X] Metadata file created correctly
- [X] Error handling comprehensive
- [X] User feedback clear and helpful
- [X] Documentation updated
- [X] Code reviewed
- [X] Type hints complete
- [X] Committed with proper message

---

## Dependencies

- **Requires**: Story 1.1 (CLI structure), Story 1.2 (SandboxManager), Story 1.3 (State management)
- **Blocks**: Story 1.5, Story 1.6, Story 2.1

---

## Notes

### Project Name Validation

Valid project names:
- Alphanumeric characters
- Hyphens and underscores
- 3-50 characters long
- Must start with letter or number

Invalid examples:
- `my project` (spaces)
- `test!` (special characters)
- `ab` (too short)

### Success Output Example

```
[OK] Sandbox project initialized successfully!

Project: my-todo-app
Location: D:\GAO Agile Dev\sandbox\projects\my-todo-app
Status: active

Boilerplate: https://github.com/vercel/next.js/tree/canary/examples/hello-world
Branch: canary

Next steps:
  1. cd sandbox/projects/my-todo-app
  2. gao-dev sandbox run <benchmark-config>
  3. gao-dev sandbox list (to see all projects)

Run 'gao-dev sandbox --help' for more commands.
```

### Error Scenarios

1. **Duplicate Project**: "Project 'my-todo-app' already exists. Use 'sandbox clean' to remove it first."
2. **Invalid Name**: "Project name must contain only letters, numbers, hyphens, and underscores."
3. **Boilerplate Clone Failed**: "Failed to clone boilerplate. Check URL and network connection."
4. **Filesystem Error**: "Failed to create project directory. Check permissions."

---

*Created as part of Epic 1: Sandbox Infrastructure*
