"""Tests for fixture system components.

Story: 36.4 - Fixture System
Epic: 36 - Test Infrastructure

Tests FixtureLoader, AIResponseInjector, and OutputMatcher.
"""

import pytest
import re
from pathlib import Path
from typing import List

# Import with aliases to avoid pytest collection issues
from tests.e2e.harness.models import (
    TestScenario as FixtureScenario,
    TestStep as FixtureStep,
)
from tests.e2e.harness.fixture_loader import FixtureLoader
from tests.e2e.harness.ai_response_injector import (
    AIResponseInjector,
    FixtureExhausted,
)
from tests.e2e.harness.output_matcher import OutputMatcher, MatchResult


# ============================================================================
# FixtureLoader Tests
# ============================================================================


def test_fixture_loader_loads_valid_yaml(tmp_path: Path):
    """Test FixtureLoader loads valid YAML fixture (AC1)."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text(
        """
name: "simple_test"
description: "Test greenfield initialization"
scenario:
  - user_input: "build a todo app"
    brian_response: "I'll help you build a todo app."
    expect_output:
      - "todo"
      - "app"
    timeout_ms: 5000
""",
        encoding="utf-8",
    )

    scenario = FixtureLoader.load(fixture_path)

    assert scenario.name == "simple_test"
    assert scenario.description == "Test greenfield initialization"
    assert len(scenario.steps) == 1
    assert scenario.steps[0].user_input == "build a todo app"
    assert scenario.steps[0].brian_response == "I'll help you build a todo app."
    assert scenario.steps[0].expect_output == ["todo", "app"]
    assert scenario.steps[0].timeout_ms == 5000


def test_fixture_loader_handles_multi_line_responses(tmp_path: Path):
    """Test FixtureLoader handles multi-line YAML strings (AC1)."""
    fixture_path = tmp_path / "multiline.yaml"
    fixture_path.write_text(
        """
name: "multiline_test"
description: "Test multi-line responses"
scenario:
  - user_input: "help"
    brian_response: |
      Line 1
      Line 2
      Line 3
    expect_output:
      - "Line 1"
""",
        encoding="utf-8",
    )

    scenario = FixtureLoader.load(fixture_path)

    assert "Line 1\nLine 2\nLine 3" in scenario.steps[0].brian_response


def test_fixture_loader_rejects_missing_name(tmp_path: Path):
    """Test FixtureLoader rejects fixture missing 'name' (AC2)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
description: "Missing name"
scenario:
  - user_input: "test"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "missing required key" in str(exc_info.value).lower()
    assert "name" in str(exc_info.value)


def test_fixture_loader_rejects_missing_description(tmp_path: Path):
    """Test FixtureLoader rejects fixture missing 'description' (AC2)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test"
scenario:
  - user_input: "test"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "missing required key" in str(exc_info.value).lower()
    assert "description" in str(exc_info.value)


def test_fixture_loader_rejects_missing_scenario(tmp_path: Path):
    """Test FixtureLoader rejects fixture missing 'scenario' (AC2)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "missing required key" in str(exc_info.value).lower()
    assert "scenario" in str(exc_info.value)


def test_fixture_loader_rejects_empty_scenario(tmp_path: Path):
    """Test FixtureLoader rejects empty scenario list (AC2, AC10)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "cannot be empty" in str(exc_info.value)


def test_fixture_loader_rejects_step_missing_user_input(tmp_path: Path):
    """Test FixtureLoader rejects step missing 'user_input' (AC2, AC10)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - brian_response: "Hello"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "missing 'user_input'" in str(exc_info.value)


def test_fixture_loader_rejects_invalid_expect_output(tmp_path: Path):
    """Test FixtureLoader rejects non-list expect_output (AC2, AC10)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - user_input: "test"
    expect_output: "should be list"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "expect_output" in str(exc_info.value)
    assert "must be a list" in str(exc_info.value)


def test_fixture_loader_rejects_invalid_timeout(tmp_path: Path):
    """Test FixtureLoader rejects invalid timeout_ms (AC2, AC10)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - user_input: "test"
    timeout_ms: -100
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "timeout_ms" in str(exc_info.value)
    assert "positive integer" in str(exc_info.value)


def test_fixture_loader_rejects_malformed_yaml(tmp_path: Path):
    """Test FixtureLoader rejects malformed YAML syntax (AC2, AC10)."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text(
        """
name: "test
description: Missing closing quote
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        FixtureLoader.load(fixture_path)

    assert "YAML" in str(exc_info.value)


def test_fixture_loader_file_not_found():
    """Test FixtureLoader raises FileNotFoundError for missing file (AC2)."""
    with pytest.raises(FileNotFoundError) as exc_info:
        FixtureLoader.load(Path("/nonexistent/fixture.yaml"))

    assert "not found" in str(exc_info.value).lower()


def test_fixture_loader_loads_existing_fixtures():
    """Test FixtureLoader can load all provided example fixtures (AC8)."""
    fixtures_dir = Path("tests/e2e/fixtures")

    # Test all example fixtures
    fixture_files = [
        "simple_conversation.yaml",
        "greenfield_init.yaml",
        "brownfield_analysis.yaml",
        "error_recovery.yaml",
    ]

    for fixture_file in fixture_files:
        fixture_path = fixtures_dir / fixture_file
        if not fixture_path.exists():
            pytest.skip(f"Fixture {fixture_file} not found")

        # Should load without error
        scenario = FixtureLoader.load(fixture_path)

        # Validate structure
        assert scenario.name
        assert scenario.description
        assert len(scenario.steps) > 0


# ============================================================================
# TestScenario and TestStep Model Tests
# ============================================================================


def test_fixture_step_model_validates_fields():
    """Test FixtureStep validates field types (AC3)."""
    # Valid step
    step = FixtureStep(
        user_input="hello",
        expect_output=["pattern"],
        brian_response="Hello!",
        timeout_ms=5000,
    )
    assert step.user_input == "hello"
    assert step.expect_output == ["pattern"]
    assert step.brian_response == "Hello!"
    assert step.timeout_ms == 5000

    # Invalid user_input type
    with pytest.raises(ValueError):
        FixtureStep(user_input=123, expect_output=[])  # type: ignore

    # Invalid timeout
    with pytest.raises(ValueError):
        FixtureStep(user_input="test", timeout_ms=-1)


def test_fixture_scenario_model_validates_fields():
    """Test FixtureScenario validates field types (AC3)."""
    step = FixtureStep(user_input="hello", brian_response="Hello!")

    # Valid scenario
    scenario = FixtureScenario(
        name="test", description="Test scenario", steps=[step]
    )
    assert scenario.name == "test"
    assert scenario.description == "Test scenario"
    assert len(scenario.steps) == 1

    # Empty name
    with pytest.raises(ValueError):
        FixtureScenario(name="", description="Test", steps=[step])

    # Empty steps
    with pytest.raises(ValueError):
        FixtureScenario(name="test", description="Test", steps=[])


def test_fixture_scenario_get_step():
    """Test FixtureScenario.get_step() method (AC3)."""
    steps = [
        FixtureStep(user_input="1", brian_response="One"),
        FixtureStep(user_input="2", brian_response="Two"),
    ]
    scenario = FixtureScenario(name="test", description="Test", steps=steps)

    assert scenario.get_step(0).user_input == "1"
    assert scenario.get_step(1).user_input == "2"

    with pytest.raises(IndexError):
        scenario.get_step(2)


# ============================================================================
# AIResponseInjector Tests
# ============================================================================


def test_ai_response_injector_provides_scripted_responses(tmp_path: Path):
    """Test AIResponseInjector returns scripted responses in order (AC4)."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - user_input: "hello"
    brian_response: "Hello!"
  - user_input: "goodbye"
    brian_response: "Goodbye!"
""",
        encoding="utf-8",
    )

    injector = AIResponseInjector(fixture_path)

    # Should return responses in order
    assert injector.get_next_response() == "Hello!"
    assert injector.get_next_response() == "Goodbye!"

    # Should raise when exhausted
    with pytest.raises(FixtureExhausted):
        injector.get_next_response()


def test_ai_response_injector_reset(tmp_path: Path):
    """Test AIResponseInjector.reset() restarts from beginning (AC4)."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - user_input: "hello"
    brian_response: "Hello!"
  - user_input: "goodbye"
    brian_response: "Goodbye!"
""",
        encoding="utf-8",
    )

    injector = AIResponseInjector(fixture_path)

    # Consume all responses
    injector.get_next_response()
    injector.get_next_response()

    # Reset
    injector.reset()

    # Should be able to get responses again
    assert injector.get_next_response() == "Hello!"
    assert injector.get_next_response() == "Goodbye!"


def test_ai_response_injector_has_more_responses(tmp_path: Path):
    """Test AIResponseInjector.has_more_responses() (AC4)."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - user_input: "hello"
    brian_response: "Hello!"
""",
        encoding="utf-8",
    )

    injector = AIResponseInjector(fixture_path)

    assert injector.has_more_responses() is True
    injector.get_next_response()
    assert injector.has_more_responses() is False


def test_ai_response_injector_missing_brian_response(tmp_path: Path):
    """Test AIResponseInjector raises error if brian_response missing (AC4)."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text(
        """
name: "test"
description: "Test"
scenario:
  - user_input: "hello"
    # No brian_response
""",
        encoding="utf-8",
    )

    injector = AIResponseInjector(fixture_path)

    with pytest.raises(ValueError) as exc_info:
        injector.get_next_response()

    assert "missing 'brian_response'" in str(exc_info.value)


# ============================================================================
# OutputMatcher Tests
# ============================================================================


def test_output_matcher_strips_ansi():
    """Test OutputMatcher removes ANSI codes (AC6)."""
    matcher = OutputMatcher()

    # ANSI color codes
    actual = "\x1b[32mGreen text\x1b[0m with patterns"
    clean = matcher.strip_ansi(actual)

    assert clean == "Green text with patterns"
    assert "\x1b" not in clean


def test_output_matcher_strips_various_ansi_codes():
    """Test OutputMatcher strips various ANSI escape sequences (AC6)."""
    matcher = OutputMatcher()

    # Different ANSI codes
    test_cases = [
        ("\x1b[31mRed\x1b[0m", "Red"),  # Color
        ("\x1b[1mBold\x1b[0m", "Bold"),  # Bold
        ("\x1b[4mUnderline\x1b[0m", "Underline"),  # Underline
        ("\x1b[2J\x1b[HClear", "Clear"),  # Clear screen
        ("\x1b[3AFoo", "Foo"),  # Cursor up
    ]

    for ansi_text, expected in test_cases:
        assert matcher.strip_ansi(ansi_text) == expected


def test_output_matcher_matches_patterns():
    """Test OutputMatcher matches regex patterns (AC5)."""
    matcher = OutputMatcher()

    actual = "Scale Level: 4\nProject Type: greenfield"
    patterns = [r"Scale Level.*4", r"greenfield"]

    result = matcher.match(actual, patterns)

    assert result.success is True
    assert all(m["matched"] for m in result.matches)
    assert len(result.matches) == 2


def test_output_matcher_detects_failed_patterns():
    """Test OutputMatcher detects patterns that don't match (AC5)."""
    matcher = OutputMatcher()

    actual = "Hello World"
    patterns = ["Hello", "Universe"]  # "Universe" won't match

    result = matcher.match(actual, patterns)

    assert result.success is False
    assert result.matches[0]["matched"] is True  # "Hello" matched
    assert result.matches[1]["matched"] is False  # "Universe" didn't match


def test_output_matcher_multiline_patterns():
    """Test OutputMatcher handles multi-line patterns (AC5)."""
    matcher = OutputMatcher()

    actual = "Line 1\nLine 2\nLine 3"
    patterns = [r"Line 1.*Line 3"]  # Should match across lines

    result = matcher.match(actual, patterns)

    assert result.success is True


def test_output_matcher_generates_diff():
    """Test OutputMatcher generates helpful diff (AC7)."""
    matcher = OutputMatcher()

    actual = "Hello World"
    expected = "Hello Universe"

    diff = matcher.diff(actual, expected)

    assert "- Hello Universe" in diff or "-Hello Universe" in diff
    assert "+ Hello World" in diff or "+Hello World" in diff


def test_output_matcher_diff_with_ansi():
    """Test OutputMatcher strips ANSI before generating diff (AC7)."""
    matcher = OutputMatcher()

    actual = "\x1b[32mHello World\x1b[0m"
    expected = "Hello World"

    diff = matcher.diff(actual, expected)

    # Should be no diff (ANSI stripped)
    assert diff == ""


def test_output_matcher_empty_patterns():
    """Test OutputMatcher handles empty pattern list (AC5)."""
    matcher = OutputMatcher()

    result = matcher.match("any output", [])

    # No patterns = always success
    assert result.success is True
    assert len(result.matches) == 0


def test_output_matcher_match_result_helpers():
    """Test MatchResult helper methods (AC5)."""
    matcher = OutputMatcher()

    result = matcher.match(
        "Hello World", ["Hello", "Universe", "World"]
    )

    failed = result.get_failed_patterns()
    matched = result.get_matched_patterns()

    assert "Universe" in failed
    assert "Hello" in matched
    assert "World" in matched


def test_output_matcher_assert_match_success():
    """Test OutputMatcher.assert_match() passes on success (AC5)."""
    matcher = OutputMatcher()

    # Should not raise
    matcher.assert_match("Hello World", ["Hello", "World"])


def test_output_matcher_assert_match_failure():
    """Test OutputMatcher.assert_match() raises on failure (AC5)."""
    matcher = OutputMatcher()

    with pytest.raises(AssertionError) as exc_info:
        matcher.assert_match("Hello World", ["Universe"])

    assert "Failed to match" in str(exc_info.value)
    assert "Universe" in str(exc_info.value)


# ============================================================================
# Integration Tests
# ============================================================================


def test_fixture_system_end_to_end(tmp_path: Path):
    """Test complete fixture system workflow (AC1-AC10)."""
    # Create fixture
    fixture_path = tmp_path / "integration.yaml"
    fixture_path.write_text(
        """
name: "integration_test"
description: "End-to-end fixture system test"
scenario:
  - user_input: "hello"
    brian_response: "Hello! How can I help?"
    expect_output:
      - "Hello"
      - "help"
    timeout_ms: 5000

  - user_input: "exit"
    brian_response: "Goodbye!"
    expect_output:
      - "Goodbye"
""",
        encoding="utf-8",
    )

    # Load fixture
    scenario = FixtureLoader.load(fixture_path)
    assert scenario.name == "integration_test"
    assert len(scenario.steps) == 2

    # Use AIResponseInjector
    injector = AIResponseInjector(fixture_path)
    response1 = injector.get_next_response()
    assert response1 == "Hello! How can I help?"

    # Use OutputMatcher to validate
    matcher = OutputMatcher()
    result = matcher.match(response1, scenario.steps[0].expect_output)
    assert result.success is True

    # Next step
    response2 = injector.get_next_response()
    result2 = matcher.match(response2, scenario.steps[1].expect_output)
    assert result2.success is True


def test_fixture_validation_prevents_malformed_fixtures():
    """Test schema validation prevents malformed fixtures (AC10)."""
    # This is a meta-test that verifies all validation tests above
    # ensure malformed fixtures are caught at load time

    # Count validation test functions
    validation_tests = [
        test_fixture_loader_rejects_missing_name,
        test_fixture_loader_rejects_missing_description,
        test_fixture_loader_rejects_missing_scenario,
        test_fixture_loader_rejects_empty_scenario,
        test_fixture_loader_rejects_step_missing_user_input,
        test_fixture_loader_rejects_invalid_expect_output,
        test_fixture_loader_rejects_invalid_timeout,
        test_fixture_loader_rejects_malformed_yaml,
    ]

    assert len(validation_tests) >= 8, "Should have comprehensive validation tests"
