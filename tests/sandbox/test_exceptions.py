"""Tests for sandbox custom exceptions."""

import pytest

from gao_dev.sandbox.exceptions import (
    GitCloneError,
    GitNotInstalledError,
    InvalidGitUrlError,
    InvalidProjectNameError,
    ProjectExistsError,
    ProjectNotFoundError,
    ProjectStateError,
    SandboxError,
)


class TestSandboxError:
    """Tests for base SandboxError."""

    def test_is_exception(self):
        """Test that SandboxError is an Exception."""
        error = SandboxError("test error")
        assert isinstance(error, Exception)

    def test_error_message(self):
        """Test error message is preserved."""
        error = SandboxError("custom message")
        assert str(error) == "custom message"

    def test_can_be_raised_and_caught(self):
        """Test that SandboxError can be raised and caught."""
        with pytest.raises(SandboxError) as exc_info:
            raise SandboxError("test")

        assert str(exc_info.value) == "test"

    def test_all_exceptions_inherit_from_sandbox_error(self):
        """Test that all custom exceptions inherit from SandboxError."""
        exceptions = [
            ProjectExistsError("test"),
            ProjectNotFoundError("test"),
            InvalidProjectNameError("test", "reason"),
            ProjectStateError("test", "active", "completed"),
            GitCloneError("url", "reason"),
            InvalidGitUrlError("url", "reason"),
            GitNotInstalledError(),
        ]

        for error in exceptions:
            assert isinstance(error, SandboxError)
            assert isinstance(error, Exception)


class TestProjectExistsError:
    """Tests for ProjectExistsError."""

    def test_create_with_project_name(self):
        """Test creating error with project name."""
        error = ProjectExistsError("my-project")

        assert error.project_name == "my-project"
        assert "my-project" in str(error)
        assert "already exists" in str(error)

    def test_error_message_format(self):
        """Test error message follows expected format."""
        error = ProjectExistsError("test-project")

        assert str(error) == "Project 'test-project' already exists"

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise ProjectExistsError("test")

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(ProjectExistsError) as exc_info:
            raise ProjectExistsError("my-project")

        assert exc_info.value.project_name == "my-project"


class TestProjectNotFoundError:
    """Tests for ProjectNotFoundError."""

    def test_create_with_project_name(self):
        """Test creating error with project name."""
        error = ProjectNotFoundError("my-project")

        assert error.project_name == "my-project"
        assert "my-project" in str(error)
        assert "not found" in str(error)

    def test_error_message_format(self):
        """Test error message follows expected format."""
        error = ProjectNotFoundError("test-project")

        assert str(error) == "Project 'test-project' not found"

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise ProjectNotFoundError("test")

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(ProjectNotFoundError) as exc_info:
            raise ProjectNotFoundError("my-project")

        assert exc_info.value.project_name == "my-project"


class TestInvalidProjectNameError:
    """Tests for InvalidProjectNameError."""

    def test_create_with_name_and_reason(self):
        """Test creating error with project name and reason."""
        error = InvalidProjectNameError("My Project", "contains spaces")

        assert error.project_name == "My Project"
        assert error.reason == "contains spaces"
        assert "My Project" in str(error)
        assert "contains spaces" in str(error)

    def test_error_message_format(self):
        """Test error message follows expected format."""
        error = InvalidProjectNameError("bad-name", "too short")

        assert str(error) == "Invalid project name 'bad-name': too short"

    def test_with_various_reasons(self):
        """Test error with different validation reasons."""
        reasons = [
            "too short",
            "too long",
            "contains invalid characters",
            "starts with hyphen",
        ]

        for reason in reasons:
            error = InvalidProjectNameError("test", reason)
            assert error.reason == reason
            assert reason in str(error)

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise InvalidProjectNameError("test", "invalid")

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(InvalidProjectNameError) as exc_info:
            raise InvalidProjectNameError("my-project", "bad format")

        assert exc_info.value.project_name == "my-project"
        assert exc_info.value.reason == "bad format"


class TestProjectStateError:
    """Tests for ProjectStateError."""

    def test_create_with_all_fields(self):
        """Test creating error with all required fields."""
        error = ProjectStateError("my-project", "active", "completed")

        assert error.project_name == "my-project"
        assert error.current_state == "active"
        assert error.required_state == "completed"
        assert "my-project" in str(error)
        assert "active" in str(error)
        assert "completed" in str(error)

    def test_error_message_format(self):
        """Test error message follows expected format."""
        error = ProjectStateError("test-project", "failed", "active")

        expected = (
            "Project 'test-project' is in state 'failed', "
            "but 'active' is required for this operation"
        )
        assert str(error) == expected

    def test_with_various_states(self):
        """Test error with different state combinations."""
        state_combinations = [
            ("active", "completed"),
            ("completed", "archived"),
            ("failed", "active"),
            ("archived", "active"),
        ]

        for current, required in state_combinations:
            error = ProjectStateError("test", current, required)
            assert error.current_state == current
            assert error.required_state == required

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise ProjectStateError("test", "active", "completed")

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(ProjectStateError) as exc_info:
            raise ProjectStateError("my-project", "active", "completed")

        assert exc_info.value.project_name == "my-project"
        assert exc_info.value.current_state == "active"
        assert exc_info.value.required_state == "completed"


class TestGitCloneError:
    """Tests for GitCloneError."""

    def test_create_with_url_and_reason(self):
        """Test creating error with repo URL and reason."""
        error = GitCloneError("https://github.com/test/repo.git", "network timeout")

        assert error.repo_url == "https://github.com/test/repo.git"
        assert error.reason == "network timeout"
        assert "https://github.com/test/repo.git" in str(error)
        assert "network timeout" in str(error)

    def test_error_message_format(self):
        """Test error message follows expected format."""
        error = GitCloneError("https://example.com/repo.git", "authentication failed")

        expected = "Failed to clone repository 'https://example.com/repo.git': authentication failed"
        assert str(error) == expected

    def test_with_various_reasons(self):
        """Test error with different failure reasons."""
        reasons = [
            "connection timeout",
            "repository not found",
            "authentication failed",
            "network unreachable",
        ]

        for reason in reasons:
            error = GitCloneError("https://example.com/repo.git", reason)
            assert error.reason == reason
            assert reason in str(error)

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise GitCloneError("url", "reason")

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(GitCloneError) as exc_info:
            raise GitCloneError("https://example.com/repo.git", "failed")

        assert exc_info.value.repo_url == "https://example.com/repo.git"
        assert exc_info.value.reason == "failed"


class TestInvalidGitUrlError:
    """Tests for InvalidGitUrlError."""

    def test_create_with_url_and_reason(self):
        """Test creating error with URL and reason."""
        error = InvalidGitUrlError("not-a-url", "invalid format")

        assert error.url == "not-a-url"
        assert error.reason == "invalid format"
        assert "not-a-url" in str(error)
        assert "invalid format" in str(error)

    def test_error_message_format(self):
        """Test error message follows expected format."""
        error = InvalidGitUrlError("ftp://example.com", "unsupported protocol")

        expected = "Invalid git URL 'ftp://example.com': unsupported protocol"
        assert str(error) == expected

    def test_with_various_reasons(self):
        """Test error with different validation reasons."""
        reasons = [
            "invalid format",
            "unsupported protocol",
            "missing host",
            "malformed",
        ]

        for reason in reasons:
            error = InvalidGitUrlError("bad-url", reason)
            assert error.reason == reason
            assert reason in str(error)

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise InvalidGitUrlError("url", "invalid")

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(InvalidGitUrlError) as exc_info:
            raise InvalidGitUrlError("bad-url", "wrong format")

        assert exc_info.value.url == "bad-url"
        assert exc_info.value.reason == "wrong format"


class TestGitNotInstalledError:
    """Tests for GitNotInstalledError."""

    def test_create_without_arguments(self):
        """Test creating error without arguments."""
        error = GitNotInstalledError()

        assert "git" in str(error).lower()
        assert "install" in str(error).lower()

    def test_error_message_is_helpful(self):
        """Test that error message provides helpful information."""
        error = GitNotInstalledError()

        message = str(error)
        assert "Git is not installed" in message or "git" in message.lower()
        assert "install" in message.lower()
        assert "PATH" in message or "path" in message.lower()

    def test_can_be_caught_as_sandbox_error(self):
        """Test that error can be caught as SandboxError."""
        with pytest.raises(SandboxError):
            raise GitNotInstalledError()

    def test_can_be_caught_specifically(self):
        """Test that error can be caught by specific type."""
        with pytest.raises(GitNotInstalledError):
            raise GitNotInstalledError()


class TestExceptionHierarchy:
    """Tests for exception hierarchy and inheritance."""

    def test_catch_all_with_sandbox_error(self):
        """Test that all exceptions can be caught with SandboxError."""
        exceptions = [
            ProjectExistsError("test"),
            ProjectNotFoundError("test"),
            InvalidProjectNameError("test", "reason"),
            ProjectStateError("test", "active", "completed"),
            GitCloneError("url", "reason"),
            InvalidGitUrlError("url", "reason"),
            GitNotInstalledError(),
        ]

        for exception in exceptions:
            with pytest.raises(SandboxError):
                raise exception

    def test_catch_specific_exception_types(self):
        """Test that specific exception types can be caught individually."""
        exceptions_and_types = [
            (ProjectExistsError("test"), ProjectExistsError),
            (ProjectNotFoundError("test"), ProjectNotFoundError),
            (InvalidProjectNameError("test", "reason"), InvalidProjectNameError),
            (ProjectStateError("test", "active", "completed"), ProjectStateError),
            (GitCloneError("url", "reason"), GitCloneError),
            (InvalidGitUrlError("url", "reason"), InvalidGitUrlError),
            (GitNotInstalledError(), GitNotInstalledError),
        ]

        for exception, exception_type in exceptions_and_types:
            with pytest.raises(exception_type):
                raise exception

    def test_exception_types_are_distinct(self):
        """Test that exception types are distinct and don't overlap."""
        exceptions = [
            ProjectExistsError("test"),
            ProjectNotFoundError("test"),
            InvalidProjectNameError("test", "reason"),
            ProjectStateError("test", "active", "completed"),
            GitCloneError("url", "reason"),
            InvalidGitUrlError("url", "reason"),
            GitNotInstalledError(),
        ]

        # Each exception should only be an instance of its own type (and base types)
        for i, exc1 in enumerate(exceptions):
            for j, exc2 in enumerate(exceptions):
                if i != j:
                    assert type(exc1) != type(exc2)
