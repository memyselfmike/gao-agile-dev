"""System health check."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config_loader import ConfigLoader
from .workflow_registry import WorkflowRegistry


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details or {},
            "remediation": self.remediation,
        }


@dataclass
class HealthCheckResult:
    """Overall health check result."""

    status: HealthStatus
    checks: List[CheckResult]
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthCheck:
    """Perform system health checks."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize health check.

        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader
        self.project_root = config_loader.project_root

    def run_all_checks(self) -> HealthCheckResult:
        """
        Run all health checks.

        Returns:
            HealthCheckResult with overall status
        """
        checks: List[CheckResult] = []

        # Run individual checks
        checks.append(self.check_project_structure())
        checks.append(self.check_workflows())
        checks.append(self.check_git())
        checks.append(self.check_configuration())

        # Determine overall status
        statuses = [c.status for c in checks]
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        # Generate summary
        total = len(checks)
        healthy = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
        warnings = sum(1 for c in checks if c.status == HealthStatus.WARNING)
        critical = sum(1 for c in checks if c.status == HealthStatus.CRITICAL)

        summary = f"{healthy}/{total} checks passed"
        if warnings > 0:
            summary += f", {warnings} warnings"
        if critical > 0:
            summary += f", {critical} critical issues"

        return HealthCheckResult(
            status=overall_status,
            checks=checks,
            summary=summary
        )

    def check_project_structure(self) -> CheckResult:
        """Check project structure exists."""
        docs_folder = self.config_loader.get_output_folder()

        if docs_folder.exists():
            return CheckResult(
                name="Project Structure",
                status=HealthStatus.HEALTHY,
                message="Project structure exists"
            )
        else:
            return CheckResult(
                name="Project Structure",
                status=HealthStatus.WARNING,
                message="Project structure not initialized",
                remediation="Run 'gao-dev init' to initialize project"
            )

    def check_workflows(self) -> CheckResult:
        """Check workflows are available."""
        registry = WorkflowRegistry(self.config_loader)
        registry.index_workflows()
        workflows = registry.get_all_workflows()

        if len(workflows) >= 3:
            return CheckResult(
                name="Workflows",
                status=HealthStatus.HEALTHY,
                message=f"Found {len(workflows)} workflows",
                details={"workflow_count": len(workflows)}
            )
        elif len(workflows) > 0:
            return CheckResult(
                name="Workflows",
                status=HealthStatus.WARNING,
                message=f"Only {len(workflows)} workflows found",
                details={"workflow_count": len(workflows)}
            )
        else:
            return CheckResult(
                name="Workflows",
                status=HealthStatus.CRITICAL,
                message="No workflows found",
                remediation="Check that workflows are properly installed"
            )

    def check_git(self) -> CheckResult:
        """Check git repository status."""
        git_dir = self.project_root / ".git"

        if git_dir.exists():
            return CheckResult(
                name="Git Repository",
                status=HealthStatus.HEALTHY,
                message="Git repository initialized"
            )
        else:
            return CheckResult(
                name="Git Repository",
                status=HealthStatus.WARNING,
                message="Git not initialized",
                remediation="Run 'git init' to initialize repository"
            )

    def check_configuration(self) -> CheckResult:
        """Check configuration is valid."""
        config = self.config_loader.to_dict()

        if config:
            return CheckResult(
                name="Configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration loaded successfully",
                details={"config_keys": len(config)}
            )
        else:
            return CheckResult(
                name="Configuration",
                status=HealthStatus.CRITICAL,
                message="Configuration failed to load",
                remediation="Check gao-dev.yaml syntax"
            )
