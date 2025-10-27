# Story 2.1: Git Repository Cloning

**Epic**: Epic 2 - Boilerplate Integration
**Status**: Done
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Completed**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev sandbox
**I want** to automatically clone Git repositories as boilerplates
**So that** I can quickly initialize sandbox projects from existing templates

---

## Acceptance Criteria

### AC1: Git Repository Cloning
- ✅ Can clone repositories via HTTPS URL
- ✅ Can clone repositories via SSH URL
- ✅ Can specify branch to clone
- ✅ Can clone to specific destination directory
- ✅ Validates URL format before cloning

### AC2: Error Handling
- ✅ Handles invalid Git URLs gracefully
- ✅ Handles network errors with retry logic
- ✅ Handles authentication failures with clear messages
- ✅ Handles non-existent branches
- ✅ Cleans up partial clones on failure

### AC3: Progress Reporting
- ✅ Shows cloning progress to user
- ✅ Reports clone completion
- ✅ Logs clone operations for debugging

### AC4: Integration
- ✅ Integrated with SandboxManager
- ✅ Used by `sandbox init --boilerplate` command
- ✅ Metadata updated with boilerplate info

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/git_cloner.py`

```python
"""Git repository cloning functionality."""

import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

class GitCloner:
    """
    Handles cloning Git repositories for boilerplate integration.
    """

    def clone_repository(
        self,
        repo_url: str,
        destination: Path,
        branch: Optional[str] = None,
    ) -> bool:
        """
        Clone Git repository to destination.

        Args:
            repo_url: Git repository URL (HTTPS or SSH)
            destination: Target directory for clone
            branch: Specific branch to clone (default: main/master)

        Returns:
            True if successful, False otherwise

        Raises:
            GitCloneError: If cloning fails
        """
        pass

    def validate_git_url(self, url: str) -> bool:
        """Validate Git repository URL format."""
        pass

    def get_default_branch(self, repo_url: str) -> str:
        """Determine default branch (main or master)."""
        pass
```

### Dependencies

- Use `subprocess` to run `git clone` commands
- Parse URLs with `urllib.parse`
- Validate Git availability on system

### Error Scenarios

1. **Invalid URL**: Return clear error message
2. **Network Failure**: Retry up to 3 times with exponential backoff
3. **Authentication Failure**: Provide guidance on SSH keys or tokens
4. **Partial Clone**: Clean up destination directory on failure

---

## Testing Requirements

### Unit Tests

```python
def test_clone_https_repository():
    """Test cloning via HTTPS."""
    pass

def test_clone_ssh_repository():
    """Test cloning via SSH."""
    pass

def test_clone_specific_branch():
    """Test cloning specific branch."""
    pass

def test_invalid_url_raises_error():
    """Test that invalid URLs are rejected."""
    pass

def test_network_error_retry():
    """Test retry logic on network errors."""
    pass

def test_cleanup_on_failure():
    """Test cleanup of partial clones."""
    pass
```

### Integration Tests

- Test with real public repository (e.g., Next.js starter)
- Test with non-existent repository
- Test with invalid branch name

---

## Definition of Done

- [X] GitCloner class implemented
- [X] All unit tests passing (92% coverage)
- [X] Integration tests passing
- [X] Error handling comprehensive
- [X] Progress reporting working
- [X] Integrated with SandboxManager
- [X] Documentation updated
- [X] Code reviewed
- [X] Type hints complete
- [X] Committed with proper message

---

## Dependencies

- **Requires**: Story 1.2 (SandboxManager exists)
- **Blocks**: Story 2.2, 2.3, 2.4

---

## Notes

- Git must be installed on system (check in prerequisites)
- Consider supporting git submodules in future
- May need to handle large repositories differently (shallow clone)

---

*Created as part of Epic 2: Boilerplate Integration*
