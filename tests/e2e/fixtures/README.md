# E2E Test Fixtures

**Story**: 36.4 - Fixture System
**Epic**: 36 - Test Infrastructure
**Feature**: e2e-testing-ux-quality

## Overview

Fixtures are YAML files that define test scenarios for E2E testing of Brian's chat interface. Each fixture contains a sequence of user inputs, expected Brian responses, and output patterns to validate.

## Purpose

Fixtures enable:
- **Deterministic testing**: Same inputs always produce same outputs (no AI variance)
- **Fast execution**: No AI inference latency (responses pre-scripted)
- **Cost-free CI/CD**: Tests run without API calls
- **Easy test creation**: YAML format is human-readable and version-controllable
- **Regression prevention**: Capture real conversations as fixtures for future validation

## Format Specification

### Basic Structure

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

### Field Descriptions

#### Top-Level Fields

- **name** (required, string): Unique identifier for the scenario
  - Use lowercase with underscores (e.g., `greenfield_init`)
  - Should be descriptive and concise

- **description** (required, string): Human-readable description
  - Explain what the scenario tests
  - Include context about edge cases or special conditions

- **scenario** (required, list): Ordered list of test steps
  - Must contain at least one step
  - Steps execute in order

#### Step Fields

- **user_input** (required, string): Text user types in this step
  - Can be empty string (to test empty input handling)
  - Simulates user typing and pressing Enter

- **brian_response** (optional, string): Brian's scripted response
  - Required when using fixtures in test mode (`--test-mode`)
  - Supports multi-line strings using YAML `|` syntax
  - This is what Brian will respond with (injected by AIResponseInjector)

- **expect_output** (optional, list of strings): Regex patterns to validate
  - Each pattern is a Python regex
  - All patterns must match for step to pass
  - Patterns are matched against ANSI-stripped output
  - Use `.*` for flexible matching across lines (DOTALL mode enabled)

- **timeout_ms** (optional, integer): Timeout in milliseconds
  - Default: 5000ms (5 seconds)
  - Must be positive integer
  - Applies to both sending input and receiving output

### YAML Tips

**Multi-line strings**:
```yaml
brian_response: |
  Line 1
  Line 2
  Line 3
```

**Literal strings (preserve formatting)**:
```yaml
brian_response: |
  Exactly as typed.
    Indentation preserved.
```

**Folded strings (wrap lines)**:
```yaml
brian_response: >
  This is a long paragraph
  that will be wrapped
  into a single line.
```

**Regex patterns**:
```yaml
expect_output:
  - "Scale Level.*4"           # Match "Scale Level: 4" or "Scale Level 4"
  - "greenfield"               # Literal match
  - "(?i)welcome"              # Case-insensitive
  - "Step [0-9]+ of [0-9]+"    # Match "Step 1 of 5"
```

## Available Fixtures

### 1. simple_conversation.yaml
Simple greeting conversation demonstrating basic interaction.
- **Use case**: Smoke test for test mode
- **Steps**: 3 (greeting, capabilities, exit)
- **Duration**: ~5 seconds

### 2. greenfield_init.yaml
Vague user input leading to detailed requirements gathering and project initialization.
- **Use case**: Greenfield project flow (Scale Level 4)
- **Steps**: 4 (vague request, clarification, initialization, exit)
- **Duration**: ~15 seconds
- **Tests**: Requirement elicitation, scale detection, project setup

### 3. brownfield_analysis.yaml
Analysis of existing codebase and enhancement planning.
- **Use case**: Brownfield enhancement flow (Scale Level 3)
- **Steps**: 3 (enhancement request, planning, exit)
- **Duration**: ~12 seconds
- **Tests**: Codebase analysis, feature planning, story breakdown

### 4. error_recovery.yaml
Error handling and graceful recovery from edge cases.
- **Use case**: Error handling and help system
- **Steps**: 5 (empty input, vague input, unknown command, help, exit)
- **Duration**: ~10 seconds
- **Tests**: Input validation, error messages, help command

## Creating New Fixtures

### Step-by-Step Guide

1. **Start from template**:
   ```yaml
   name: "my_test_scenario"
   description: "Tests [specific behavior]"
   scenario:
     - user_input: "hello"
       brian_response: "Hello!"
       expect_output:
         - "Hello"
   ```

2. **Define user inputs**: What the user will type at each step

3. **Add Brian responses**: What Brian should respond (for test mode)

4. **Add validation patterns**: Regex patterns to verify output

5. **Test the fixture**:
   ```bash
   # Test in test mode (uses brian_response)
   gao-dev start --test-mode --fixture my_test_scenario.yaml

   # Run automated test
   pytest tests/e2e/ -k my_test_scenario
   ```

6. **Iterate**: Refine patterns based on actual output

### Best Practices

**DO**:
- ✅ Use descriptive scenario names
- ✅ Cover both happy path and error cases
- ✅ Keep fixtures focused (one scenario per file)
- ✅ Use flexible regex patterns (not brittle exact matches)
- ✅ Document what each fixture tests
- ✅ Test fixtures after creating them
- ✅ Use multi-line strings for readability
- ✅ Add comments to explain complex patterns

**DON'T**:
- ❌ Create overly long scenarios (>10 steps)
- ❌ Use exact string matching (brittle)
- ❌ Duplicate existing test coverage
- ❌ Include ANSI codes in expect_output (they're stripped)
- ❌ Use tabs for indentation (YAML requires spaces)
- ❌ Forget to test edge cases

### Example: Creating a Bug Fix Fixture

When you find a bug, capture it as a fixture:

```yaml
name: "bug_123_empty_project_name"
description: "Regression test for Bug #123: Empty project name causes crash"

scenario:
  # Step 1: Trigger bug
  - user_input: "init "
    brian_response: |
      I notice you didn't provide a project name.

      Please provide a name: init <project-name>

      Example: init my-todo-app
    expect_output:
      - "didn't provide.*name"
      - "init <project-name>"

  # Step 2: Correct usage
  - user_input: "init my-app"
    brian_response: "Initializing project 'my-app'..."
    expect_output:
      - "Initializing.*my-app"
```

## Running Tests with Fixtures

### Manual Testing

```bash
# Test mode (uses brian_response from fixture)
gao-dev start --test-mode --fixture greenfield_init.yaml

# Capture mode (records actual Brian responses)
gao-dev start --capture-mode --output captured_conversation.yaml
```

### Automated Testing

```bash
# Run all fixture tests
pytest tests/e2e/test_fixture_system.py

# Run specific fixture
pytest tests/e2e/test_fixture_system.py -k greenfield

# Run with verbose output
pytest tests/e2e/test_fixture_system.py -v

# Run with output capture
pytest tests/e2e/test_fixture_system.py -s
```

### Test Framework Integration

The fixture system integrates with pytest via:
- **FixtureLoader**: Loads and validates YAML files
- **AIResponseInjector**: Provides scripted responses in test mode
- **OutputMatcher**: Validates output against expected patterns
- **ChatHarness**: Spawns subprocess and manages interaction

Example test:
```python
def test_greenfield_initialization():
    """Test greenfield project initialization flow."""
    fixture_path = Path("tests/e2e/fixtures/greenfield_init.yaml")

    # Load fixture
    scenario = FixtureLoader.load(fixture_path)

    # Run test with ChatHarness
    with ChatHarness(test_mode=True, fixture_path=fixture_path) as harness:
        for step in scenario.steps:
            # Send user input
            harness.send(step.user_input)

            # Validate output
            output = harness.read_until_prompt(timeout=step.timeout_ms // 1000)
            matcher = OutputMatcher()
            result = matcher.match(output, step.expect_output)

            assert result.success, f"Step failed: {result.get_failed_patterns()}"
```

## Troubleshooting

### Common Issues

**Issue**: Fixture validation fails with "missing required key"
- **Solution**: Ensure all required fields (name, description, scenario) are present
- **Check**: YAML syntax, indentation (use spaces, not tabs)

**Issue**: Pattern doesn't match even though text is in output
- **Solution**: Output contains ANSI codes - patterns are matched against stripped output
- **Debug**: Print `OutputMatcher().strip_ansi(output)` to see clean text

**Issue**: Regex pattern error
- **Solution**: Escape special characters: `\.`, `\[`, `\]`, `\(`, `\)`, `\*`, `\+`
- **Example**: `"Step \[1\]"` not `"Step [1]"`

**Issue**: Test times out
- **Solution**: Increase `timeout_ms` or check if Brian's response is delayed
- **Debug**: Run manually with `gao-dev start --test-mode --fixture <file>`

**Issue**: YAML syntax error
- **Solution**: Validate YAML at https://www.yamllint.com/
- **Common**: Missing colons, wrong indentation, unmatched quotes

### Validation

Validate fixture schema:
```python
from tests.e2e.harness.fixture_loader import FixtureLoader
from pathlib import Path

try:
    scenario = FixtureLoader.load(Path("my_fixture.yaml"))
    print(f"✓ Valid: {scenario.name} ({scenario.step_count()} steps)")
except ValueError as e:
    print(f"✗ Invalid: {e}")
```

## Maintenance

### Versioning

Fixtures should be versioned alongside code:
- Create `v1/`, `v2/` subdirectories for major prompt changes
- Keep old fixtures as regression tests
- Update fixtures when Brian's behavior intentionally changes

### Updating Fixtures

When Brian's prompts change:

1. **Identify affected fixtures**: Run all tests, note failures
2. **Decide if intentional**: Is new behavior better?
3. **Update or revert**:
   - If intentional: Update `brian_response` and `expect_output`
   - If regression: Fix code to match original behavior
4. **Re-test**: Ensure all fixtures pass

### Fixture Conversion (Future)

Story 3.4 will add a tool to convert real conversations to fixtures:

```bash
# Record conversation
gao-dev start --capture-mode

# Convert to fixture
gao-dev convert-capture conversation.log fixtures/new_test.yaml
```

## Related Documentation

- **Story 36.4**: Fixture System (this implementation)
- **Story 36.2**: Test Mode Support in ChatREPL
- **Story 36.3**: ChatHarness Implementation
- **Architecture**: `docs/features/e2e-testing-ux-quality/ARCHITECTURE.md`
- **PRD**: `docs/features/e2e-testing-ux-quality/PRD.md`

## Questions?

For questions or issues:
1. Check troubleshooting section above
2. Review existing fixtures as examples
3. Consult architecture documentation
4. Run `pytest tests/e2e/ -v` to see test details
