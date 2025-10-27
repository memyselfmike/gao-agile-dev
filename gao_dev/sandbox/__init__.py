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
from .benchmark import BenchmarkConfig, SuccessCriteria, WorkflowPhaseConfig
from .git_cloner import GitCloner
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
    "SuccessCriteria",
    "WorkflowPhaseConfig",
    "GitCloner",
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
