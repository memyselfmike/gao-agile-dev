"""
System Health Check for GAO-Dev

Post-update health validation to ensure installation is working correctly.

Story 36.10: Health Check System
"""

import sqlite3
import structlog
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


logger = structlog.get_logger(__name__)


@dataclass
class HealthCheckResult:
    """
    Result of a health check.

    Attributes:
        check_name: Name of the check
        passed: Whether check passed
        message: Description of result
        fix_suggestion: Optional suggestion for fixing issue
    """

    check_name: str
    passed: bool
    message: str
    fix_suggestion: Optional[str] = None


@dataclass
class HealthCheckReport:
    """
    Complete health check report.

    Attributes:
        all_passed: Whether all checks passed
        results: List of individual check results
        failed_checks: List of failed check names
    """

    all_passed: bool
    results: List[HealthCheckResult] = field(default_factory=list)

    @property
    def failed_checks(self) -> List[str]:
        """Get list of failed check names."""
        return [r.check_name for r in self.results if not r.passed]

    @property
    def passed_count(self) -> int:
        """Count of passed checks."""
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        """Count of failed checks."""
        return sum(1 for r in self.results if not r.passed)


class SystemHealthCheck:
    """
    Perform post-update health checks.

    Checks:
    - Config files exist and are valid
    - Database schema is correct
    - Workflows are loadable
    - Agent configurations are valid
    - Git repository is accessible
    """

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize health checker.

        Args:
            project_path: Optional path to project. If None, uses current directory.
        """
        self.project_path = project_path or Path.cwd()
        self.logger = logger.bind(component="SystemHealthCheck")

    def run_post_update_check(self, verbose: bool = False) -> HealthCheckReport:
        """
        Run complete post-update health check.

        Args:
            verbose: Include detailed output

        Returns:
            HealthCheckReport with all check results
        """
        self.logger.info("running_health_check", project_path=str(self.project_path))

        results: List[HealthCheckResult] = []

        # Run all checks
        results.append(self.check_config_files())
        results.append(self.check_database_schema())
        results.append(self.check_workflows())
        results.append(self.check_agents())
        results.append(self.check_git_repository())

        all_passed = all(r.passed for r in results)

        report = HealthCheckReport(all_passed=all_passed, results=results)

        if verbose:
            self._log_report(report)

        return report

    def check_config_files(self) -> HealthCheckResult:
        """
        Check that config files exist and are valid.

        Returns:
            HealthCheckResult for config files check
        """
        try:
            # Check for .gao-dev directory
            gaodev_dir = self.project_path / ".gao-dev"

            if not gaodev_dir.exists():
                return HealthCheckResult(
                    check_name="config_files",
                    passed=False,
                    message=".gao-dev directory not found",
                    fix_suggestion="Run 'gao-dev init' to initialize project",
                )

            # Check for required files
            required_files = ["documents.db"]
            missing_files = []

            for filename in required_files:
                file_path = gaodev_dir / filename
                if not file_path.exists():
                    missing_files.append(filename)

            if missing_files:
                return HealthCheckResult(
                    check_name="config_files",
                    passed=False,
                    message=f"Missing files: {', '.join(missing_files)}",
                    fix_suggestion="Run 'gao-dev init' to recreate missing files",
                )

            return HealthCheckResult(
                check_name="config_files", passed=True, message="All config files present"
            )

        except Exception as e:
            self.logger.error("config_check_failed", error=str(e))
            return HealthCheckResult(
                check_name="config_files",
                passed=False,
                message=f"Config check failed: {e}",
                fix_suggestion="Check file permissions and directory structure",
            )

    def check_database_schema(self) -> HealthCheckResult:
        """
        Check that database schema is correct.

        Returns:
            HealthCheckResult for database schema check
        """
        try:
            db_path = self.project_path / ".gao-dev" / "documents.db"

            if not db_path.exists():
                return HealthCheckResult(
                    check_name="database_schema",
                    passed=False,
                    message="Database not found",
                    fix_suggestion="Run 'gao-dev migrate' to create database",
                )

            # Connect and check tables
            conn = sqlite3.connect(db_path)
            try:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = {row[0] for row in cursor.fetchall()}

                # Required tables
                required_tables = {
                    "epics",
                    "stories",
                    "tasks",
                    "documents",
                    "features",
                    "schema_version",
                }

                missing_tables = required_tables - tables

                if missing_tables:
                    return HealthCheckResult(
                        check_name="database_schema",
                        passed=False,
                        message=f"Missing tables: {', '.join(sorted(missing_tables))}",
                        fix_suggestion="Run 'gao-dev migrate' to update schema",
                    )

                return HealthCheckResult(
                    check_name="database_schema",
                    passed=True,
                    message="Database schema is correct",
                )

            finally:
                conn.close()

        except Exception as e:
            self.logger.error("database_check_failed", error=str(e))
            return HealthCheckResult(
                check_name="database_schema",
                passed=False,
                message=f"Database check failed: {e}",
                fix_suggestion="Run 'gao-dev migrate' to repair database",
            )

    def check_workflows(self) -> HealthCheckResult:
        """
        Check that workflows are loadable.

        Returns:
            HealthCheckResult for workflows check
        """
        try:
            from gao_dev.workflows import get_available_workflows

            workflows = get_available_workflows()

            if not workflows:
                return HealthCheckResult(
                    check_name="workflows",
                    passed=False,
                    message="No workflows found",
                    fix_suggestion="Reinstall GAO-Dev: pip install --force-reinstall gao-dev",
                )

            return HealthCheckResult(
                check_name="workflows",
                passed=True,
                message=f"{len(workflows)} workflows loaded successfully",
            )

        except Exception as e:
            self.logger.error("workflows_check_failed", error=str(e))
            return HealthCheckResult(
                check_name="workflows",
                passed=False,
                message=f"Workflows check failed: {e}",
                fix_suggestion="Reinstall GAO-Dev: pip install --force-reinstall gao-dev",
            )

    def check_agents(self) -> HealthCheckResult:
        """
        Check that agent configurations are valid.

        Returns:
            HealthCheckResult for agents check
        """
        try:
            from gao_dev.config.agent_loader import AgentLoader

            loader = AgentLoader()
            agents = loader.get_available_agents()

            if not agents:
                return HealthCheckResult(
                    check_name="agents",
                    passed=False,
                    message="No agents found",
                    fix_suggestion="Reinstall GAO-Dev: pip install --force-reinstall gao-dev",
                )

            # Expected agents
            expected_agents = {"brian", "john", "winston", "sally", "bob", "amelia", "murat", "mary"}
            found_agents = set(agents)

            missing_agents = expected_agents - found_agents

            if missing_agents:
                return HealthCheckResult(
                    check_name="agents",
                    passed=False,
                    message=f"Missing agents: {', '.join(sorted(missing_agents))}",
                    fix_suggestion="Reinstall GAO-Dev: pip install --force-reinstall gao-dev",
                )

            return HealthCheckResult(
                check_name="agents", passed=True, message=f"{len(agents)} agents configured"
            )

        except Exception as e:
            self.logger.error("agents_check_failed", error=str(e))
            return HealthCheckResult(
                check_name="agents",
                passed=False,
                message=f"Agents check failed: {e}",
                fix_suggestion="Reinstall GAO-Dev: pip install --force-reinstall gao-dev",
            )

    def check_git_repository(self) -> HealthCheckResult:
        """
        Check that git repository is accessible.

        Returns:
            HealthCheckResult for git check
        """
        try:
            from git import Repo
            from git.exc import InvalidGitRepositoryError

            try:
                repo = Repo(self.project_path, search_parent_directories=True)

                # Check if repo is valid
                if repo.bare:
                    return HealthCheckResult(
                        check_name="git_repository",
                        passed=False,
                        message="Git repository is bare",
                        fix_suggestion="Clone the repository properly with 'git clone'",
                    )

                return HealthCheckResult(
                    check_name="git_repository",
                    passed=True,
                    message=f"Git repository accessible (branch: {repo.active_branch.name})",
                )

            except InvalidGitRepositoryError:
                # Not a git repo - that's OK for some projects
                return HealthCheckResult(
                    check_name="git_repository",
                    passed=True,
                    message="Not a git repository (optional)",
                )

        except Exception as e:
            self.logger.error("git_check_failed", error=str(e))
            return HealthCheckResult(
                check_name="git_repository",
                passed=False,
                message=f"Git check failed: {e}",
                fix_suggestion="Install git or check git configuration",
            )

    def _log_report(self, report: HealthCheckReport) -> None:
        """
        Log health check report.

        Args:
            report: HealthCheckReport to log
        """
        if report.all_passed:
            self.logger.info(
                "health_check_passed",
                passed_count=report.passed_count,
                total_checks=len(report.results),
            )
        else:
            self.logger.warning(
                "health_check_failed",
                passed_count=report.passed_count,
                failed_count=report.failed_count,
                failed_checks=report.failed_checks,
            )

            for result in report.results:
                if not result.passed:
                    self.logger.warning(
                        "failed_check",
                        check=result.check_name,
                        message=result.message,
                        fix=result.fix_suggestion,
                    )
