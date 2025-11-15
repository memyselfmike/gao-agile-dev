# Story 36.4: Fixture System

**Story ID**: 1.4
**Epic**: 1 - Test Infrastructure
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 4
**Priority**: Critical

---

## User Story

**As a** test developer
**I want** to define test scenarios in YAML files with user inputs and expected outputs
**So that** I can create deterministic, repeatable E2E tests without calling real AI

---

## Business Value

Fixture-based testing enables:
- **Deterministic tests**: Same inputs always produce same outputs (no AI variance)
- **Fast execution**: No AI inference latency (responses pre-scripted)
- **Cost-free CI/CD**: Tests run without API calls
- **Easy test creation**: YAML format is human-readable and version-controllable
- **Regression prevention**: Capture real conversations as fixtures for future validation

**Estimated value**: Enables 20+ regression tests to run in <2 minutes with zero cost

---

## Acceptance Criteria

- [ ] **AC1**: FixtureLoader class loads YAML test scenario files
- [ ] **AC2**: YAML schema validated with clear error messages if malformed
- [ ] **AC3**: TestScenario and TestStep data models implemented
- [ ] **AC4**: AIResponseInjector provides scripted responses in test mode
- [ ] **AC5**: OutputMatcher validates actual output against expected patterns
- [ ] **AC6**: OutputMatcher strips ANSI codes before matching
- [ ] **AC7**: OutputMatcher generates diffs for failed matches
- [ ] **AC8**: 3+ example fixtures created (greenfield, brownfield, error handling)
- [ ] **AC9**: Fixture format documented with examples
- [ ] **AC10**: Schema validation prevents malformed fixtures

---

## Technical Context

### Architecture References

From Architecture document section 2.2 (FixtureLoader) and 2.3 (OutputMatcher):

**FixtureLoader**: Load and validate YAML test scenarios
**AIResponseInjector**: Inject pre-scripted responses in test mode
**OutputMatcher**: Verify subprocess output matches expected patterns

### Fixture Format Specification

```yaml
name: "test_scenario_name"
description: "Human-readable description of what this tests"

scenario:
  - user_input: "User types this"
    brian_response: |
      Brian responds with this.
      Multi-line responses supported.
    expect_output:
      - "regex pattern 1"
      - "regex pattern 2"
    timeout_ms: 5000  # Optional, default 5000

  - user_input: "Next input"
    brian_response: "Next response"
    expect_output:
      - "expected pattern"
```

### Implementation Details

**Data Models** (`tests/e2e/harness/models.py`):
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TestStep:
    """Single step in test scenario."""
    user_input: str
    expect_output: List[str]  # Regex patterns
    brian_response: Optional[str] = None  # For test mode
    timeout_ms: int = 5000

@dataclass
class TestScenario:
    """Test scenario loaded from YAML fixture."""
    name: str
    description: str
    steps: List[TestStep]
```

**FixtureLoader** (`tests/e2e/harness/fixture_loader.py`):
```python
import yaml
from pathlib import Path
from typing import Optional
from .models import TestScenario, TestStep

class FixtureLoader:
    """Load and validate YAML test fixtures."""

    @staticmethod
    def load(fixture_path: Path) -> TestScenario:
        """
        Load fixture from YAML file.

        Args:
            fixture_path: Path to YAML fixture file

        Returns:
            TestScenario with validated steps

        Raises:
            ValueError: If fixture schema invalid
            FileNotFoundError: If fixture file doesn't exist
        """
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")

        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Validate schema
        FixtureLoader._validate_schema(data, fixture_path)

        # Parse into TestScenario
        steps = [
            TestStep(
                user_input=step["user_input"],
                expect_output=step.get("expect_output", []),
                brian_response=step.get("brian_response"),
                timeout_ms=step.get("timeout_ms", 5000)
            )
            for step in data["scenario"]
        ]

        return TestScenario(
            name=data["name"],
            description=data["description"],
            steps=steps
        )

    @staticmethod
    def _validate_schema(data: dict, fixture_path: Path) -> None:
        """
        Validate fixture schema.

        Raises:
            ValueError: If schema invalid with helpful error message
        """
        # Check required top-level keys
        required_keys = ["name", "description", "scenario"]
        for key in required_keys:
            if key not in data:
                raise ValueError(
                    f"Fixture {fixture_path.name} missing required key: '{key}'\n"
                    f"Required: {required_keys}"
                )

        # Validate scenario is list
        if not isinstance(data["scenario"], list):
            raise ValueError(
                f"Fixture {fixture_path.name}: 'scenario' must be a list of steps"
            )

        if len(data["scenario"]) == 0:
            raise ValueError(
                f"Fixture {fixture_path.name}: 'scenario' cannot be empty"
            )

        # Validate each step
        for i, step in enumerate(data["scenario"]):
            if not isinstance(step, dict):
                raise ValueError(
                    f"Fixture {fixture_path.name}: Step {i+1} must be a dictionary"
                )

            if "user_input" not in step:
                raise ValueError(
                    f"Fixture {fixture_path.name}: Step {i+1} missing 'user_input'"
                )

            # Validate expect_output is list if present
            if "expect_output" in step:
                if not isinstance(step["expect_output"], list):
                    raise ValueError(
                        f"Fixture {fixture_path.name}: Step {i+1} 'expect_output' must be a list"
                    )
```

**AIResponseInjector** (`tests/e2e/harness/ai_response_injector.py`):
```python
from pathlib import Path
from typing import Optional
from .fixture_loader import FixtureLoader
from .models import TestScenario

class AIResponseInjector:
    """Inject scripted AI responses in test mode."""

    def __init__(self, fixture_path: Path):
        self.scenario = FixtureLoader.load(fixture_path)
        self.current_step = 0

    def get_next_response(self) -> str:
        """
        Get next scripted response from fixture.

        Returns:
            Brian's scripted response

        Raises:
            IndexError: If no more responses available
        """
        if self.current_step >= len(self.scenario.steps):
            raise IndexError(
                f"No more scripted responses. "
                f"Step {self.current_step + 1} requested but only "
                f"{len(self.scenario.steps)} steps in fixture."
            )

        step = self.scenario.steps[self.current_step]
        self.current_step += 1

        if step.brian_response is None:
            raise ValueError(
                f"Step {self.current_step} missing 'brian_response' in test mode"
            )

        return step.brian_response

    def reset(self):
        """Reset to beginning of scenario."""
        self.current_step = 0
```

**OutputMatcher** (`tests/e2e/harness/output_matcher.py`):
```python
import re
import difflib
from typing import List
from dataclasses import dataclass

@dataclass
class MatchResult:
    """Output pattern matching result."""
    success: bool
    matches: List[dict]
    actual_output: str

class OutputMatcher:
    """Match output against expected patterns with ANSI stripping."""

    def __init__(self):
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes."""
        return self.ansi_escape.sub('', text)

    def match(
        self,
        actual: str,
        expected_patterns: List[str],
        strict: bool = False
    ) -> MatchResult:
        """
        Match actual output against expected patterns.

        Args:
            actual: Actual output from subprocess
            expected_patterns: List of regex patterns to match
            strict: If True, all patterns must match in order

        Returns:
            MatchResult with success flag and details
        """
        clean_actual = self.strip_ansi(actual)

        matches = []
        for pattern in expected_patterns:
            match = re.search(pattern, clean_actual, re.DOTALL | re.MULTILINE)
            matches.append({
                "pattern": pattern,
                "matched": match is not None,
                "match_text": match.group(0) if match else None
            })

        all_matched = all(m["matched"] for m in matches)

        return MatchResult(
            success=all_matched,
            matches=matches,
            actual_output=clean_actual
        )

    def diff(self, actual: str, expected: str) -> str:
        """
        Generate diff between actual and expected.

        Args:
            actual: Actual output (may contain ANSI)
            expected: Expected output (plain text)

        Returns:
            Unified diff string
        """
        clean_actual = self.strip_ansi(actual)

        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            clean_actual.splitlines(keepends=True),
            fromfile="expected",
            tofile="actual"
        )

        return ''.join(diff)
```

### Dependencies

- **Depends On**: None (can be developed in parallel with Story 36.3)
- **Blocks**: Story 36.2 (AIResponseInjector used in ChatSession)
- pyyaml library (already installed in GAO-Dev)

---

## Test Scenarios

### Test 1: Load Valid Fixture
```python
def test_fixture_loader_loads_valid_yaml(tmp_path):
    """Test FixtureLoader loads valid YAML fixture."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text("""
name: "simple_test"
description: "Test greenfield initialization"
scenario:
  - user_input: "build a todo app"
    brian_response: "I'll help you build a todo app."
    expect_output:
      - "todo"
      - "app"
    timeout_ms: 5000
""")

    scenario = FixtureLoader.load(fixture_path)

    assert scenario.name == "simple_test"
    assert len(scenario.steps) == 1
    assert scenario.steps[0].user_input == "build a todo app"
    assert scenario.steps[0].brian_response == "I'll help you build a todo app."
    assert len(scenario.steps[0].expect_output) == 2
```

### Test 2: Validate Schema Errors
```python
def test_fixture_loader_rejects_invalid_schema(tmp_path):
    """Test FixtureLoader rejects malformed fixtures."""
    fixture_path = tmp_path / "bad.yaml"
    fixture_path.write_text("""
name: "bad_fixture"
# Missing description and scenario
""")

    with pytest.raises(ValueError, match="missing required key"):
        FixtureLoader.load(fixture_path)
```

### Test 3: AIResponseInjector
```python
def test_ai_response_injector_provides_scripted_responses(tmp_path):
    """Test AIResponseInjector returns scripted responses in order."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text("""
name: "test"
description: "Test"
scenario:
  - user_input: "hello"
    brian_response: "Hello!"
  - user_input: "goodbye"
    brian_response: "Goodbye!"
""")

    injector = AIResponseInjector(fixture_path)

    assert injector.get_next_response() == "Hello!"
    assert injector.get_next_response() == "Goodbye!"

    # Should raise when exhausted
    with pytest.raises(IndexError):
        injector.get_next_response()
```

### Test 4: OutputMatcher ANSI Stripping
```python
def test_output_matcher_strips_ansi():
    """Test OutputMatcher removes ANSI codes before matching."""
    matcher = OutputMatcher()

    actual = "\x1b[32mGreen text\x1b[0m with patterns"
    patterns = ["Green text", "patterns"]

    result = matcher.match(actual, patterns)

    assert result.success is True
    assert "\x1b" not in result.actual_output
```

### Test 5: OutputMatcher Pattern Matching
```python
def test_output_matcher_matches_patterns():
    """Test OutputMatcher matches regex patterns."""
    matcher = OutputMatcher()

    actual = "Scale Level: 4\nProject Type: greenfield"
    patterns = [r"Scale Level.*4", r"greenfield"]

    result = matcher.match(actual, patterns)

    assert result.success is True
    assert all(m["matched"] for m in result.matches)
```

### Test 6: OutputMatcher Diff Generation
```python
def test_output_matcher_generates_diff():
    """Test OutputMatcher generates helpful diff."""
    matcher = OutputMatcher()

    actual = "Hello World"
    expected = "Hello Universe"

    diff = matcher.diff(actual, expected)

    assert "- Hello Universe" in diff
    assert "+ Hello World" in diff
```

---

## Definition of Done

- [ ] FixtureLoader implemented and tested
- [ ] AIResponseInjector implemented and tested
- [ ] OutputMatcher implemented and tested
- [ ] Data models (TestScenario, TestStep) implemented
- [ ] Schema validation working with helpful errors
- [ ] 3+ example fixtures created
- [ ] Unit tests passing (6+ tests)
- [ ] Fixture format documented
- [ ] Code reviewed and approved
- [ ] README updated with fixture usage guide

---

## Implementation Notes

### Files to Create

**New Files**:
- `tests/e2e/harness/models.py` - Data models
- `tests/e2e/harness/fixture_loader.py` - YAML loader
- `tests/e2e/harness/ai_response_injector.py` - Response injection
- `tests/e2e/harness/output_matcher.py` - Pattern matching
- `tests/e2e/fixtures/greenfield_init.yaml` - Example fixture
- `tests/e2e/fixtures/brownfield_analysis.yaml` - Example fixture
- `tests/e2e/fixtures/error_recovery.yaml` - Example fixture
- `tests/e2e/fixtures/README.md` - Fixture documentation

### Example Fixtures

**greenfield_init.yaml**:
```yaml
name: "greenfield_initialization"
description: "Test vague user input leading to detailed requirements gathering"

scenario:
  - user_input: "build a app"
    brian_response: |
      I'd be happy to help you build an app! To provide the best guidance,
      I need to understand more about your vision.

      What type of app are you looking to build?
    expect_output:
      - "happy to help"
      - "type of app"
    timeout_ms: 5000

  - user_input: "a todo app"
    brian_response: |
      Great! A todo app is a solid project. Let me analyze the requirements.

      Based on your input, I detect this is a greenfield project (Scale Level 4).

      Would you like me to initialize the project structure?
    expect_output:
      - "Scale Level.*4"
      - "greenfield"
      - "initialize"
```

**error_recovery.yaml**:
```yaml
name: "error_recovery"
description: "Test error handling and recovery"

scenario:
  - user_input: ""
    brian_response: |
      I didn't receive any input. How can I help you today?
    expect_output:
      - "didn't receive.*input"
      - "How can I help"
```

### Fixture Documentation Template

Create `tests/e2e/fixtures/README.md`:
```markdown
# E2E Test Fixtures

## Overview

Fixtures are YAML files that define test scenarios for E2E testing of Brian's chat interface.

## Format

...yaml
name: "test_scenario_name"
description: "What this tests"
scenario:
  - user_input: "User input"
    brian_response: "Brian's response"
    expect_output:
      - "regex pattern"
...

## Creating New Fixtures

1. Start from template above
2. Define user inputs and expected Brian responses
3. Add regex patterns for output validation
4. Save in `tests/e2e/fixtures/`
5. Run: `pytest tests/e2e/ -k fixture_name`

## Best Practices

- Use descriptive names
- Cover happy path + error cases
- Keep fixtures focused (1 scenario per file)
- Use regex for flexible matching
- Document what each fixture tests
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| YAML schema validation misses edge cases | Medium | Medium | Comprehensive schema tests, real fixture validation |
| Regex patterns too strict (brittle tests) | High | High | Document best practices, use flexible patterns |
| Fixtures become stale as prompts evolve | High | Medium | Automated validation tool (future story), version fixtures |
| YAML injection vulnerability | Low | Low | yaml.safe_load, input sanitization, max file size |

---

## Related Stories

- **Depends On**: None (foundation story)
- **Blocks**: Story 36.2 (AIResponseInjector integration)
- **Related**: Story 36.3 (ChatHarness uses OutputMatcher)
- **Future**: Story 3.4 (Fixture Conversion Tool uses FixtureLoader)

---

## References

- PRD Section: FR5 (Regression Testing)
- Architecture Section: 2.2 FixtureLoader, 2.3 OutputMatcher
- YAML specification: https://yaml.org/spec/1.2/spec.html
- CRAAP Review: Critique #5 (Fixture Maintenance Strategy)
