"""Quality metrics tracking.

This module provides the QualityTracker class, which wraps MetricsCollector
to extract and track quality metrics from external tools like pytest, ruff,
mypy, and bandit.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from .collector import MetricsCollector


class QualityTracker:
    """
    Tracks quality metrics during benchmark execution.

    This class integrates with various code quality tools to extract metrics
    including test results, code coverage, linting errors, type errors, and
    security vulnerabilities. It wraps a MetricsCollector instance to store
    the extracted metrics.

    Attributes:
        collector: MetricsCollector instance for storing metrics

    Example:
        tracker = QualityTracker()
        project_path = Path("sandbox/projects/todo-app-001")

        # Track all quality metrics
        tracker.track_tests(project_path)
        tracker.track_linting(project_path)
        tracker.track_type_errors(project_path)
        tracker.track_security(project_path)
        tracker.track_functional_completeness(criteria_met=8, criteria_total=10)

        # Get metrics
        metrics = tracker.collector.get_current_metrics()
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize quality tracker.

        Args:
            collector: Optional MetricsCollector instance. If not provided,
                      creates a new singleton instance.
        """
        self.collector = collector or MetricsCollector()

    def track_tests(self, project_path: Path) -> None:
        """
        Extract test metrics from test results.

        Attempts to run pytest and extract test counts and pass rates.
        Also attempts to extract code coverage if available.

        Args:
            project_path: Path to the project directory to test
        """
        # Try pytest
        pytest_result = self._run_pytest(project_path)
        if pytest_result:
            self.collector.set_value("tests_written", pytest_result["total"])
            self.collector.set_value("tests_passing", pytest_result["passed"])
            self.collector.set_value("tests_failing", pytest_result["failed"])

            # Calculate pass rate
            total = pytest_result["total"]
            if total > 0:
                pass_rate = (pytest_result["passed"] / total) * 100
                self.collector.set_value("test_pass_rate", pass_rate)

        # Try coverage
        coverage_result = self._get_coverage(project_path)
        if coverage_result is not None:
            self.collector.set_value("code_coverage", coverage_result)

    def track_linting(self, project_path: Path) -> None:
        """
        Extract linting metrics from linter output.

        Attempts to run linting tools (ruff for Python, eslint for JS/TS)
        and extract error counts by severity.

        Args:
            project_path: Path to the project directory to lint
        """
        # Try ruff for Python
        ruff_result = self._run_ruff(project_path)
        if ruff_result:
            self.collector.set_value("linting_errors", ruff_result["total"])
            self.collector.set_value("linting_by_severity", ruff_result["by_severity"])

        # Try eslint for JS/TS
        eslint_result = self._run_eslint(project_path)
        if eslint_result:
            errors = eslint_result.get("errorCount", 0)
            warnings = eslint_result.get("warningCount", 0)
            total = errors + warnings

            # Add to existing linting errors if any
            existing = self.collector.get_value("linting_errors", 0)
            self.collector.set_value("linting_errors", existing + total)

            # Merge severity counts
            existing_severity = self.collector.get_value("linting_by_severity", {})
            existing_severity["error"] = existing_severity.get("error", 0) + errors
            existing_severity["warning"] = existing_severity.get("warning", 0) + warnings
            self.collector.set_value("linting_by_severity", existing_severity)

    def track_type_errors(self, project_path: Path) -> None:
        """
        Extract type checking errors.

        Attempts to run type checkers (mypy for Python, tsc for TypeScript)
        and extract error counts.

        Args:
            project_path: Path to the project directory to type check
        """
        # Try MyPy for Python
        mypy_result = self._run_mypy(project_path)
        if mypy_result:
            self.collector.set_value("type_errors_python", mypy_result["errors"])

        # Try tsc for TypeScript
        tsc_result = self._run_tsc(project_path)
        if tsc_result:
            self.collector.set_value("type_errors_typescript", tsc_result["errors"])

        # Calculate total type errors
        python_errors = self.collector.get_value("type_errors_python", 0)
        ts_errors = self.collector.get_value("type_errors_typescript", 0)
        self.collector.set_value("type_errors_total", python_errors + ts_errors)

    def track_security(self, project_path: Path) -> None:
        """
        Extract security vulnerability metrics.

        Attempts to run security scanners (bandit for Python) and extract
        vulnerability counts by severity.

        Args:
            project_path: Path to the project directory to scan
        """
        # Try bandit for Python
        bandit_result = self._run_bandit(project_path)
        if bandit_result:
            self.collector.set_value(
                "security_vulnerabilities", bandit_result["total"]
            )
            self.collector.set_value(
                "security_by_severity", bandit_result["by_severity"]
            )

    def track_functional_completeness(
        self, criteria_met: int, criteria_total: int
    ) -> None:
        """
        Track acceptance criteria completion.

        Calculates the percentage of acceptance criteria that have been met
        and stores it along with the raw counts.

        Args:
            criteria_met: Number of acceptance criteria met
            criteria_total: Total number of acceptance criteria
        """
        percentage = (
            (criteria_met / criteria_total * 100) if criteria_total > 0 else 0.0
        )
        self.collector.set_value("functional_completeness", percentage)
        self.collector.set_value("criteria_met", criteria_met)
        self.collector.set_value("criteria_total", criteria_total)

    def _run_pytest(self, project_path: Path) -> Optional[Dict[str, int]]:
        """
        Run pytest and extract results.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with total, passed, and failed counts, or None if failed
        """
        try:
            # Try with json-report plugin first
            result = subprocess.run(
                [
                    "pytest",
                    "--json-report",
                    "--json-report-file=.pytest-report.json",
                    "--tb=no",
                    "-q",
                ],
                cwd=project_path,
                capture_output=True,
                timeout=300,
                text=True,
            )

            report_path = project_path / ".pytest-report.json"
            if report_path.exists():
                with open(report_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                summary = data.get("summary", {})
                return {
                    "total": summary.get("total", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                }

            # Fallback: parse pytest output
            return self._parse_pytest_output(result.stdout)

        except FileNotFoundError:
            # pytest not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _parse_pytest_output(self, output: str) -> Optional[Dict[str, int]]:
        """
        Parse pytest console output to extract test counts.

        Args:
            output: pytest stdout text

        Returns:
            Dictionary with test counts, or None if parsing failed
        """
        try:
            # Look for patterns like "5 passed, 2 failed in 1.23s"
            import re

            pattern = r"(\d+)\s+passed"
            passed_match = re.search(pattern, output)
            passed = int(passed_match.group(1)) if passed_match else 0

            pattern = r"(\d+)\s+failed"
            failed_match = re.search(pattern, output)
            failed = int(failed_match.group(1)) if failed_match else 0

            if passed > 0 or failed > 0:
                return {
                    "total": passed + failed,
                    "passed": passed,
                    "failed": failed,
                }

            return None
        except Exception:
            return None

    def _get_coverage(self, project_path: Path) -> Optional[float]:
        """
        Get code coverage percentage.

        Args:
            project_path: Path to the project directory

        Returns:
            Coverage percentage (0.0-100.0), or None if not available
        """
        try:
            # Try JSON format first
            result = subprocess.run(
                ["coverage", "json", "-o", ".coverage.json"],
                cwd=project_path,
                capture_output=True,
                timeout=60,
                text=True,
            )

            coverage_path = project_path / ".coverage.json"
            if coverage_path.exists():
                with open(coverage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("totals", {}).get("percent_covered", 0.0)

            # Fallback: try report format
            result = subprocess.run(
                ["coverage", "report"],
                cwd=project_path,
                capture_output=True,
                timeout=60,
                text=True,
            )

            if result.returncode == 0:
                return self._parse_coverage_output(result.stdout)

            return None

        except FileNotFoundError:
            # coverage not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _parse_coverage_output(self, output: str) -> Optional[float]:
        """
        Parse coverage report output to extract percentage.

        Args:
            output: coverage report stdout text

        Returns:
            Coverage percentage, or None if parsing failed
        """
        try:
            # Look for "TOTAL" line with percentage
            import re

            # Pattern: "TOTAL    123    45    67%"
            pattern = r"TOTAL\s+\d+\s+\d+\s+(\d+)%"
            match = re.search(pattern, output)

            if match:
                return float(match.group(1))

            return None
        except Exception:
            return None

    def _run_ruff(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """
        Run ruff linter.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with total and by_severity counts, or None if failed
        """
        try:
            result = subprocess.run(
                ["ruff", "check", ".", "--output-format=json"],
                cwd=project_path,
                capture_output=True,
                timeout=60,
                text=True,
            )

            if result.stdout:
                errors = json.loads(result.stdout)
                by_severity: Dict[str, int] = {}

                for error in errors:
                    # Ruff uses "code" field, map first letter to severity
                    code = error.get("code", "")
                    if code.startswith("E") or code.startswith("F"):
                        severity = "error"
                    else:
                        severity = "warning"

                    by_severity[severity] = by_severity.get(severity, 0) + 1

                return {"total": len(errors), "by_severity": by_severity}

            return None

        except FileNotFoundError:
            # ruff not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _run_eslint(self, project_path: Path) -> Optional[Dict[str, int]]:
        """
        Run eslint.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with errorCount and warningCount, or None if failed
        """
        try:
            # Check if eslint config exists
            config_files = [
                ".eslintrc.js",
                ".eslintrc.json",
                "eslint.config.js",
                "package.json",
            ]

            has_config = any((project_path / f).exists() for f in config_files)
            if not has_config:
                return None

            result = subprocess.run(
                ["npx", "eslint", ".", "--format=json"],
                cwd=project_path,
                capture_output=True,
                timeout=120,
                text=True,
            )

            if result.stdout:
                data = json.loads(result.stdout)

                # ESLint returns array of file results
                total_errors = 0
                total_warnings = 0

                for file_result in data:
                    total_errors += file_result.get("errorCount", 0)
                    total_warnings += file_result.get("warningCount", 0)

                return {"errorCount": total_errors, "warningCount": total_warnings}

            return None

        except FileNotFoundError:
            # eslint or npx not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _run_mypy(self, project_path: Path) -> Optional[Dict[str, int]]:
        """
        Run MyPy type checker.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with error count, or None if failed
        """
        try:
            # Check if mypy config exists or if it's a Python project
            has_python = any((project_path / "**" / "*.py").glob("*"))
            if not has_python:
                return None

            result = subprocess.run(
                ["mypy", ".", "--no-error-summary"],
                cwd=project_path,
                capture_output=True,
                timeout=120,
                text=True,
            )

            # MyPy returns non-zero if errors found
            # Parse output to count errors
            error_count = self._parse_mypy_output(result.stdout + result.stderr)

            return {"errors": error_count}

        except FileNotFoundError:
            # mypy not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _parse_mypy_output(self, output: str) -> int:
        """
        Parse mypy output to count errors.

        Args:
            output: mypy stdout/stderr text

        Returns:
            Number of errors found
        """
        try:
            # Count lines with "error:" in them
            import re

            error_lines = re.findall(r"^.+:\d+: error:", output, re.MULTILINE)
            return len(error_lines)
        except Exception:
            return 0

    def _run_tsc(self, project_path: Path) -> Optional[Dict[str, int]]:
        """
        Run TypeScript compiler.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with error count, or None if failed
        """
        try:
            # Check if tsconfig.json exists
            if not (project_path / "tsconfig.json").exists():
                return None

            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=project_path,
                capture_output=True,
                timeout=120,
                text=True,
            )

            # tsc returns non-zero if errors found
            error_count = self._parse_tsc_output(result.stdout + result.stderr)

            return {"errors": error_count}

        except FileNotFoundError:
            # tsc or npx not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

    def _parse_tsc_output(self, output: str) -> int:
        """
        Parse tsc output to count errors.

        Args:
            output: tsc stdout/stderr text

        Returns:
            Number of errors found
        """
        try:
            # Look for pattern like "Found 5 errors."
            import re

            pattern = r"Found (\d+) error"
            match = re.search(pattern, output)

            if match:
                return int(match.group(1))

            # Fallback: count lines with error markers
            error_lines = re.findall(r":\d+:\d+\s+-\s+error\s+TS\d+:", output)
            return len(error_lines)
        except Exception:
            return 0

    def _run_bandit(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """
        Run Bandit security scanner.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with total and by_severity counts, or None if failed
        """
        try:
            # Check if it's a Python project
            python_files = list((project_path).rglob("*.py"))
            if not python_files:
                return None

            result = subprocess.run(
                ["bandit", "-r", ".", "-f", "json"],
                cwd=project_path,
                capture_output=True,
                timeout=120,
                text=True,
            )

            if result.stdout:
                data = json.loads(result.stdout)
                results = data.get("results", [])

                by_severity: Dict[str, int] = {}
                for issue in results:
                    severity = issue.get("issue_severity", "UNDEFINED").lower()
                    by_severity[severity] = by_severity.get(severity, 0) + 1

                return {"total": len(results), "by_severity": by_severity}

            return None

        except FileNotFoundError:
            # bandit not installed
            return None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None
