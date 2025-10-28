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
# Import benchmark loader (from benchmark_loader.py)
from .benchmark_loader import BenchmarkConfig, load_benchmark
from .git_cloner import GitCloner
from .git_manager import GitManager
from .template_scanner import TemplateScanner, TemplateVariable
from .template_substitutor import TemplateSubstitutor, SubstitutionResult, SubstitutionError
from .dependency_installer import DependencyInstaller, PackageManager, DependencyInstallError
from .boilerplate_validator import BoilerplateValidator, ValidationReport, ValidationIssue, ValidationLevel

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
    "load_benchmark",
    "GitCloner",
    "GitManager",
    "TemplateScanner",
    "TemplateVariable",
    "TemplateSubstitutor",
    "SubstitutionResult",
    "SubstitutionError",
    "DependencyInstaller",
    "PackageManager",
    "DependencyInstallError",
    "BoilerplateValidator",
    "ValidationReport",
    "ValidationIssue",
    "ValidationLevel",
]
