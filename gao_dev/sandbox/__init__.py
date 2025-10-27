"""Sandbox management for GAO-Dev testing and benchmarking."""

from .manager import SandboxManager
from .models import ProjectMetadata, ProjectStatus, BenchmarkRun
from .exceptions import (
    SandboxError,
    ProjectExistsError,
    ProjectNotFoundError,
    InvalidProjectNameError,
    ProjectStateError,
    GitCloneError,
    InvalidGitUrlError,
    GitNotInstalledError,
)
from .benchmark import BenchmarkConfig, BenchmarkError, load_benchmark, validate_benchmark_file
from .git_cloner import GitCloner
from .template_scanner import TemplateScanner, TemplateVariable
from .template_substitutor import TemplateSubstitutor, SubstitutionResult, SubstitutionError

__all__ = [
    "SandboxManager",
    "ProjectMetadata",
    "ProjectStatus",
    "BenchmarkRun",
    "SandboxError",
    "ProjectExistsError",
    "ProjectNotFoundError",
    "InvalidProjectNameError",
    "ProjectStateError",
    "GitCloneError",
    "InvalidGitUrlError",
    "GitNotInstalledError",
    "BenchmarkConfig",
    "BenchmarkError",
    "load_benchmark",
    "validate_benchmark_file",
    "GitCloner",
    "TemplateScanner",
    "TemplateVariable",
    "TemplateSubstitutor",
    "SubstitutionResult",
    "SubstitutionError",
]
