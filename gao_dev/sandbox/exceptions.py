"""Custom exceptions for sandbox operations."""


class SandboxError(Exception):
    """Base exception for all sandbox operations."""

    pass


class ProjectExistsError(SandboxError):
    """Raised when attempting to create a project that already exists."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        super().__init__(f"Project '{project_name}' already exists")


class ProjectNotFoundError(SandboxError):
    """Raised when attempting to access a project that doesn't exist."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        super().__init__(f"Project '{project_name}' not found")


class InvalidProjectNameError(SandboxError):
    """Raised when project name doesn't meet requirements."""

    def __init__(self, project_name: str, reason: str):
        self.project_name = project_name
        self.reason = reason
        super().__init__(f"Invalid project name '{project_name}': {reason}")


class ProjectStateError(SandboxError):
    """Raised when project is in invalid state for requested operation."""

    def __init__(self, project_name: str, current_state: str, required_state: str):
        self.project_name = project_name
        self.current_state = current_state
        self.required_state = required_state
        super().__init__(
            f"Project '{project_name}' is in state '{current_state}', "
            f"but '{required_state}' is required for this operation"
        )


class GitCloneError(SandboxError):
    """Raised when git clone operation fails."""

    def __init__(self, repo_url: str, reason: str):
        self.repo_url = repo_url
        self.reason = reason
        super().__init__(f"Failed to clone repository '{repo_url}': {reason}")


class InvalidGitUrlError(SandboxError):
    """Raised when git URL is invalid or unsupported."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Invalid git URL '{url}': {reason}")


class GitNotInstalledError(SandboxError):
    """Raised when git is not installed on the system."""

    def __init__(self):
        super().__init__(
            "Git is not installed or not available in PATH. "
            "Please install Git and try again."
        )
