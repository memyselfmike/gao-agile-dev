"""Tests for quality metrics tracker.

Tests the QualityTracker class including all tool integrations,
metric extraction, and error handling for missing tools.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from gao_dev.sandbox.metrics.quality_tracker import QualityTracker
from gao_dev.sandbox.metrics.collector import MetricsCollector


@pytest.fixture
def mock_collector():
    """Create a mock collector for testing."""
    collector = Mock(spec=MetricsCollector)
    collector.set_value = Mock()
    collector.get_value = Mock(return_value=0)
    collector.increment_counter = Mock()
    return collector


@pytest.fixture
def tracker(mock_collector):
    """Create tracker with mock collector."""
    return QualityTracker(collector=mock_collector)


@pytest.fixture
def real_collector():
    """Create a real collector for integration tests."""
    collector = MetricsCollector()
    collector.reset()
    yield collector
    collector.reset()


@pytest.fixture
def real_tracker(real_collector):
    """Create tracker with real collector."""
    return QualityTracker(collector=real_collector)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


class TestQualityTrackerInit:
    """Tests for QualityTracker initialization."""

    def test_init_with_collector(self, mock_collector):
        """Test initialization with provided collector."""
        tracker = QualityTracker(collector=mock_collector)
        assert tracker.collector is mock_collector

    def test_init_without_collector(self):
        """Test initialization creates singleton collector."""
        tracker = QualityTracker()
        assert tracker.collector is not None
        assert isinstance(tracker.collector, MetricsCollector)


class TestTestTracking:
    """Tests for test metrics tracking."""

    def test_track_tests_with_json_report(self, tracker, mock_collector, temp_project):
        """Test pytest with JSON report."""
        # Create mock pytest report
        report_data = {
            "summary": {"total": 10, "passed": 8, "failed": 2}
        }
        report_path = temp_project / ".pytest-report.json"
        report_path.write_text(json.dumps(report_data))

        # Mock subprocess to succeed
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            tracker.track_tests(temp_project)

        # Verify metrics were set
        assert mock_collector.set_value.call_count >= 4
        mock_collector.set_value.assert_any_call("tests_written", 10)
        mock_collector.set_value.assert_any_call("tests_passing", 8)
        mock_collector.set_value.assert_any_call("tests_failing", 2)
        mock_collector.set_value.assert_any_call("test_pass_rate", 80.0)

    def test_track_tests_fallback_parsing(self, tracker, mock_collector, temp_project):
        """Test pytest output parsing fallback."""
        pytest_output = "5 passed, 2 failed in 1.23s"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout=pytest_output, stderr=""
            )

            tracker.track_tests(temp_project)

        # Should parse from output
        mock_collector.set_value.assert_any_call("tests_written", 7)
        mock_collector.set_value.assert_any_call("tests_passing", 5)
        mock_collector.set_value.assert_any_call("tests_failing", 2)

    def test_track_tests_pytest_not_found(self, tracker, mock_collector, temp_project):
        """Test graceful handling when pytest not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            tracker.track_tests(temp_project)

        # Should not crash, just skip
        # Collector might have been called for coverage, but not for tests
        pass

    def test_track_tests_timeout(self, tracker, mock_collector, temp_project):
        """Test handling of pytest timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 300)):
            tracker.track_tests(temp_project)

        # Should not crash
        pass

    def test_get_coverage_json(self, tracker, mock_collector, temp_project):
        """Test coverage extraction from JSON."""
        coverage_data = {
            "totals": {"percent_covered": 85.5}
        }
        coverage_path = temp_project / ".coverage.json"
        coverage_path.write_text(json.dumps(coverage_data))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            tracker.track_tests(temp_project)

        mock_collector.set_value.assert_any_call("code_coverage", 85.5)

    def test_get_coverage_report_parsing(self, tracker, mock_collector, temp_project):
        """Test coverage extraction from report output."""
        coverage_output = """
Name                      Stmts   Miss  Cover
---------------------------------------------
mymodule.py                 123     15    88%
tests/test_mymodule.py      45      5     89%
---------------------------------------------
TOTAL                       168     20    88%
"""

        with patch("subprocess.run") as mock_run:
            # First call for pytest (no report), second for coverage JSON (fails), third for report
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),  # pytest
                Mock(returncode=1, stdout="", stderr=""),  # coverage JSON fails
                Mock(returncode=0, stdout=coverage_output, stderr=""),  # coverage report works
            ]

            tracker.track_tests(temp_project)

        mock_collector.set_value.assert_any_call("code_coverage", 88.0)

    def test_get_coverage_not_found(self, tracker, mock_collector, temp_project):
        """Test graceful handling when coverage not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            tracker.track_tests(temp_project)

        # Should not crash
        pass


class TestLintingTracking:
    """Tests for linting metrics tracking."""

    def test_track_linting_ruff(self, tracker, mock_collector, temp_project):
        """Test ruff linting extraction."""
        ruff_output = [
            {"code": "E501", "message": "Line too long"},
            {"code": "F401", "message": "Unused import"},
            {"code": "W291", "message": "Trailing whitespace"},
        ]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout=json.dumps(ruff_output), stderr=""
            )

            tracker.track_linting(temp_project)

        mock_collector.set_value.assert_any_call("linting_errors", 3)
        # Should categorize by severity
        severity_arg = None
        for call in mock_collector.set_value.call_args_list:
            if call[0][0] == "linting_by_severity":
                severity_arg = call[0][1]
                break
        assert severity_arg is not None
        assert "error" in severity_arg or "warning" in severity_arg

    def test_track_linting_eslint(self, tracker, mock_collector, temp_project):
        """Test eslint linting extraction."""
        # Create package.json to indicate JS project
        (temp_project / "package.json").write_text("{}")

        eslint_output = [
            {"errorCount": 5, "warningCount": 3},
            {"errorCount": 2, "warningCount": 1},
        ]

        with patch("subprocess.run") as mock_run:
            # First call is ruff (not found), second is eslint
            mock_run.side_effect = [
                FileNotFoundError,  # ruff
                Mock(returncode=1, stdout=json.dumps(eslint_output), stderr=""),  # eslint
            ]

            # Mock get_value to return proper values
            def get_value_side_effect(key, default=None):
                if key == "linting_errors":
                    return 0
                elif key == "linting_by_severity":
                    return {}
                return default

            mock_collector.get_value.side_effect = get_value_side_effect

            tracker.track_linting(temp_project)

        # Should have called set_value with total (7 errors + 4 warnings = 11)
        found_call = False
        for call in mock_collector.set_value.call_args_list:
            if call[0][0] == "linting_errors" and call[0][1] == 11:
                found_call = True
                break
        assert found_call

    def test_track_linting_no_tools(self, tracker, mock_collector, temp_project):
        """Test graceful handling when no linting tools installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            tracker.track_linting(temp_project)

        # Should not crash
        pass

    def test_track_linting_ruff_timeout(self, tracker, mock_collector, temp_project):
        """Test handling of ruff timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ruff", 60)):
            tracker.track_linting(temp_project)

        # Should not crash
        pass


class TestTypeErrorTracking:
    """Tests for type error tracking."""

    def test_track_type_errors_mypy(self, tracker, mock_collector, temp_project):
        """Test mypy type checking."""
        # Create a Python file
        py_file = temp_project / "test.py"
        py_file.write_text("x: int = 'string'")

        mypy_output = """
test.py:1: error: Incompatible types in assignment
test.py:5: error: Argument 1 has incompatible type
Found 2 errors in 1 file
"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout=mypy_output, stderr=""
            )

            # Track what was set so we can return it in get_value
            set_values = {}

            def set_value_side_effect(key, value):
                set_values[key] = value

            def get_value_side_effect(key, default=0):
                return set_values.get(key, default)

            mock_collector.set_value.side_effect = set_value_side_effect
            mock_collector.get_value.side_effect = get_value_side_effect

            # Mock glob to find Python files
            with patch.object(Path, "glob") as mock_glob:
                mock_glob.return_value = [py_file]

                tracker.track_type_errors(temp_project)

        # Check that values were set
        assert set_values.get("type_errors_python") == 2
        assert set_values.get("type_errors_total") == 2

    def test_track_type_errors_tsc(self, tracker, mock_collector, temp_project):
        """Test TypeScript type checking."""
        # Create tsconfig.json
        tsconfig = temp_project / "tsconfig.json"
        tsconfig.write_text("{}")

        tsc_output = "Found 5 errors."

        # Track what was set so we can return it in get_value
        set_values = {}

        def set_value_side_effect(key, value):
            set_values[key] = value

        def get_value_side_effect(key, default=0):
            return set_values.get(key, default)

        mock_collector.set_value.side_effect = set_value_side_effect
        mock_collector.get_value.side_effect = get_value_side_effect

        # Mock subprocess and Path operations
        with patch("subprocess.run") as mock_run:
            with patch.object(Path, "glob") as mock_glob:
                # No Python files for mypy
                mock_glob.return_value = []

                # tsc will be called and succeed
                mock_run.return_value = Mock(returncode=1, stdout=tsc_output, stderr="")

                tracker.track_type_errors(temp_project)

        # Check that values were set
        assert set_values.get("type_errors_typescript") == 5
        assert set_values.get("type_errors_total") == 5

    def test_track_type_errors_both(self, tracker, mock_collector, temp_project):
        """Test tracking both Python and TypeScript errors."""
        # Create both Python and TypeScript markers
        (temp_project / "test.py").write_text("x = 1")
        (temp_project / "tsconfig.json").write_text("{}")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stdout="test.py:1: error: test\n", stderr=""),  # mypy
                Mock(returncode=1, stdout="Found 3 errors.", stderr=""),  # tsc
            ]

            mock_collector.get_value.side_effect = lambda k, d=0: {
                "type_errors_python": 1,
                "type_errors_typescript": 3,
            }.get(k, d)

            tracker.track_type_errors(temp_project)

        mock_collector.set_value.assert_any_call("type_errors_total", 4)

    def test_track_type_errors_no_tools(self, tracker, mock_collector, temp_project):
        """Test graceful handling when type checkers not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            tracker.track_type_errors(temp_project)

        # Should not crash
        pass


class TestSecurityTracking:
    """Tests for security vulnerability tracking."""

    def test_track_security_bandit(self, tracker, mock_collector, temp_project):
        """Test bandit security scanning."""
        # Create Python files
        (temp_project / "app.py").write_text("import os")
        (temp_project / "utils.py").write_text("import sys")

        bandit_output = {
            "results": [
                {"issue_severity": "HIGH"},
                {"issue_severity": "MEDIUM"},
                {"issue_severity": "LOW"},
                {"issue_severity": "HIGH"},
            ]
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout=json.dumps(bandit_output), stderr=""
            )

            # Mock rglob to find Python files
            with patch.object(Path, "rglob") as mock_rglob:
                mock_rglob.return_value = [Path("app.py"), Path("utils.py")]

                tracker.track_security(temp_project)

        mock_collector.set_value.assert_any_call("security_vulnerabilities", 4)

        # Check severity breakdown
        severity_arg = None
        for call in mock_collector.set_value.call_args_list:
            if call[0][0] == "security_by_severity":
                severity_arg = call[0][1]
                break

        assert severity_arg is not None
        assert severity_arg.get("high", 0) == 2
        assert severity_arg.get("medium", 0) == 1
        assert severity_arg.get("low", 0) == 1

    def test_track_security_no_python_files(self, tracker, mock_collector, temp_project):
        """Test bandit skipped when no Python files."""
        with patch.object(Path, "rglob") as mock_rglob:
            mock_rglob.return_value = []

            tracker.track_security(temp_project)

        # Should not run bandit
        mock_collector.set_value.assert_not_called()

    def test_track_security_bandit_not_found(self, tracker, mock_collector, temp_project):
        """Test graceful handling when bandit not installed."""
        # Create Python file
        (temp_project / "app.py").write_text("import os")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with patch.object(Path, "rglob") as mock_rglob:
                mock_rglob.return_value = [Path("app.py")]

                tracker.track_security(temp_project)

        # Should not crash
        pass

    def test_track_security_timeout(self, tracker, mock_collector, temp_project):
        """Test handling of bandit timeout."""
        (temp_project / "app.py").write_text("import os")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("bandit", 120)):
            with patch.object(Path, "rglob") as mock_rglob:
                mock_rglob.return_value = [Path("app.py")]

                tracker.track_security(temp_project)

        # Should not crash
        pass


class TestFunctionalCompletenessTracking:
    """Tests for functional completeness tracking."""

    def test_track_functional_completeness_full(self, tracker, mock_collector):
        """Test tracking with all criteria met."""
        tracker.track_functional_completeness(criteria_met=10, criteria_total=10)

        mock_collector.set_value.assert_any_call("functional_completeness", 100.0)
        mock_collector.set_value.assert_any_call("criteria_met", 10)
        mock_collector.set_value.assert_any_call("criteria_total", 10)

    def test_track_functional_completeness_partial(self, tracker, mock_collector):
        """Test tracking with partial completion."""
        tracker.track_functional_completeness(criteria_met=7, criteria_total=10)

        mock_collector.set_value.assert_any_call("functional_completeness", 70.0)
        mock_collector.set_value.assert_any_call("criteria_met", 7)
        mock_collector.set_value.assert_any_call("criteria_total", 10)

    def test_track_functional_completeness_none(self, tracker, mock_collector):
        """Test tracking with no criteria met."""
        tracker.track_functional_completeness(criteria_met=0, criteria_total=10)

        mock_collector.set_value.assert_any_call("functional_completeness", 0.0)

    def test_track_functional_completeness_zero_total(self, tracker, mock_collector):
        """Test tracking with zero total criteria."""
        tracker.track_functional_completeness(criteria_met=0, criteria_total=0)

        mock_collector.set_value.assert_any_call("functional_completeness", 0.0)


class TestIntegration:
    """Integration tests with real collector."""

    def test_real_collector_integration(self, real_tracker, real_collector):
        """Test integration with real MetricsCollector."""
        # Track functional completeness (doesn't require external tools)
        real_tracker.track_functional_completeness(criteria_met=8, criteria_total=10)

        # Verify values are stored
        assert real_collector.get_value("functional_completeness") == 80.0
        assert real_collector.get_value("criteria_met") == 8
        assert real_collector.get_value("criteria_total") == 10

    def test_multiple_tracking_calls(self, real_tracker, real_collector):
        """Test multiple tracking calls accumulate correctly."""
        # Track different metrics
        real_tracker.track_functional_completeness(criteria_met=5, criteria_total=10)

        # Simulate some metrics manually
        real_collector.set_value("tests_written", 20)
        real_collector.set_value("tests_passing", 18)

        # Get current metrics
        assert real_collector.get_value("functional_completeness") == 50.0
        assert real_collector.get_value("tests_written") == 20
        assert real_collector.get_value("tests_passing") == 18

    def test_tracking_with_missing_tools(self, real_tracker, temp_project):
        """Test that tracking gracefully handles all missing tools."""
        # This should not crash even if no tools are installed
        real_tracker.track_tests(temp_project)
        real_tracker.track_linting(temp_project)
        real_tracker.track_type_errors(temp_project)
        real_tracker.track_security(temp_project)

        # Should complete without errors
        assert True


class TestParsingHelpers:
    """Tests for output parsing helper methods."""

    def test_parse_pytest_output_passed_only(self, real_tracker):
        """Test parsing pytest output with only passed tests."""
        output = "5 passed in 1.23s"
        result = real_tracker._parse_pytest_output(output)

        assert result is not None
        assert result["passed"] == 5
        assert result["failed"] == 0
        assert result["total"] == 5

    def test_parse_pytest_output_mixed(self, real_tracker):
        """Test parsing pytest output with mixed results."""
        output = "10 passed, 3 failed in 2.5s"
        result = real_tracker._parse_pytest_output(output)

        assert result is not None
        assert result["passed"] == 10
        assert result["failed"] == 3
        assert result["total"] == 13

    def test_parse_pytest_output_invalid(self, real_tracker):
        """Test parsing invalid pytest output."""
        output = "Some random text without test results"
        result = real_tracker._parse_pytest_output(output)

        assert result is None

    def test_parse_coverage_output_valid(self, real_tracker):
        """Test parsing coverage report output."""
        output = """
Name                      Stmts   Miss  Cover
---------------------------------------------
mymodule.py                 100     10    90%
tests/test_mymodule.py      50      5     90%
---------------------------------------------
TOTAL                       150     15    90%
"""
        result = real_tracker._parse_coverage_output(output)

        assert result == 90.0

    def test_parse_coverage_output_invalid(self, real_tracker):
        """Test parsing invalid coverage output."""
        output = "No coverage data available"
        result = real_tracker._parse_coverage_output(output)

        assert result is None

    def test_parse_mypy_output(self, real_tracker):
        """Test parsing mypy output."""
        output = """
mymodule.py:10: error: Incompatible types in assignment
mymodule.py:15: error: Argument 1 has incompatible type
mymodule.py:20: note: This is a note, not an error
utils.py:5: error: Name 'foo' is not defined
"""
        result = real_tracker._parse_mypy_output(output)

        assert result == 3  # Should count only errors, not notes

    def test_parse_tsc_output_with_count(self, real_tracker):
        """Test parsing tsc output with error count."""
        output = "Found 7 errors."
        result = real_tracker._parse_tsc_output(output)

        assert result == 7

    def test_parse_tsc_output_fallback(self, real_tracker):
        """Test parsing tsc output with error lines."""
        output = """
src/app.ts:10:5 - error TS2322: Type 'string' is not assignable
src/app.ts:15:3 - error TS2345: Argument of type 'number'
src/utils.ts:5:1 - error TS7006: Parameter 'x' implicitly has
"""
        result = real_tracker._parse_tsc_output(output)

        assert result == 3

    def test_parse_tsc_output_no_errors(self, real_tracker):
        """Test parsing tsc output with no errors."""
        output = "Compilation complete. Watching for file changes."
        result = real_tracker._parse_tsc_output(output)

        assert result == 0
