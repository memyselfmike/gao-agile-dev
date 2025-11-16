# E2E Testing Guide - Running & Debugging

This guide shows you how to run and debug E2E tests with the live gao-dev chat REPL.

## Quick Start

### 1. Run a Simple E2E Test

```bash
# IMPORTANT (Windows): E2E tests require --capture=no flag due to pytest capture system conflicts
# Run all E2E tests (Windows)
python -m pytest tests/e2e/ --capture=no --tb=short -v

# Or use the provided script
run_e2e_tests.bat

# Run a simple fixture-based test
python -m pytest tests/e2e/test_fixture_system.py::TestFixtureExecution::test_simple_conversation_fixture -v --capture=no

# Run all fixture tests
python -m pytest tests/e2e/test_fixture_system.py -v --capture=no

# Run conversation instrumentation tests
python -m pytest tests/e2e/test_conversation_instrumentation.py -v --capture=no
```

**Windows Note**: E2E tests spawn subprocesses (gao-dev) which interfere with pytest's default stdout/stderr capture system. Always use `--capture=no` when running E2E tests on Windows, or use the provided `run_e2e_tests.bat` script.

### 2. Run Test Mode Manually (Interactive Debugging)

```bash
# Start gao-dev in test mode
gao-dev start --test-mode

# You'll see:
# [TEST MODE] AI responses will be injected for testing
# Enter scripted responses or 'exit' to quit test mode
```

Then interact with the REPL to see how test mode works.

### 3. Run ChatHarness Directly

```python
from pathlib import Path
from tests.e2e.harness.chat_harness import ChatHarness
from tests.e2e.harness.fixture_loader import FixtureLoader

# Load a fixture
fixture = FixtureLoader.load(Path("tests/e2e/fixtures/simple_conversation.yaml"))

# Run the test
harness = ChatHarness()
result = harness.execute(fixture)

print(f"Test Result: {'PASS' if result.success else 'FAIL'}")
print(f"Actual Output:\n{result.actual_output}")
```

---

## E2E Testing Architecture

### Components

1. **ChatHarness** (`tests/e2e/harness/chat_harness.py`)
   - Launches gao-dev as subprocess
   - Injects AI responses via test mode
   - Captures output and validates expectations

2. **FixtureLoader** (`tests/e2e/harness/fixture_loader.py`)
   - Loads YAML test scenarios
   - Validates fixture format
   - Provides test data to ChatHarness

3. **AIResponseInjector** (`tests/e2e/harness/ai_response_injector.py`)
   - Injects scripted AI responses during test mode
   - Queues responses for gao-dev to consume
   - No API calls needed (cost-free testing)

4. **OutputMatcher** (`tests/e2e/harness/output_matcher.py`)
   - Matches actual output against expected patterns
   - Strips ANSI codes for reliable comparison
   - Supports regex patterns

5. **TranscriptValidator** (`tests/e2e/harness/transcript_validator.py`)
   - Validates conversation transcript format
   - Generates statistics and summaries
   - Used for quality analysis

---

## Running E2E Tests

### Option 1: Pytest (Automated)

```bash
# Run all E2E tests
python -m pytest tests/e2e/ -v

# Run specific test file
python -m pytest tests/e2e/test_chat_harness.py -v

# Run with output visible (-s flag)
python -m pytest tests/e2e/test_fixture_system.py::TestFixtureExecution::test_simple_conversation_fixture -v -s

# Run and stop on first failure (-x flag)
python -m pytest tests/e2e/test_chat_harness.py -v -x
```

### Option 2: Direct Python Script

Create a test script:

```python
# test_my_scenario.py
from pathlib import Path
from tests.e2e.harness.chat_harness import ChatHarness
from tests.e2e.harness.fixture_loader import FixtureLoader

def run_test():
    fixture_path = Path("tests/e2e/fixtures/greenfield_init.yaml")

    # Load fixture
    fixture = FixtureLoader.load(fixture_path)

    # Execute test
    harness = ChatHarness()
    result = harness.execute(fixture)

    # Print results
    print("\n" + "=" * 60)
    print(f"Test: {fixture.name}")
    print(f"Result: {'✅ PASS' if result.success else '❌ FAIL'}")
    print(f"Duration: {result.execution_time_seconds:.2f}s")
    print("=" * 60)

    if not result.success:
        print("\nExpected Output:")
        for pattern in fixture.expected_output:
            print(f"  - {pattern}")

        print("\nActual Output:")
        print(result.actual_output)

        print("\nMismatches:")
        for mismatch in result.mismatches:
            print(f"  - {mismatch}")

    return result.success

if __name__ == "__main__":
    success = run_test()
    exit(0 if success else 1)
```

Run it:
```bash
python test_my_scenario.py
```

### Option 3: Interactive Manual Testing

```bash
# Start gao-dev in test mode
gao-dev start --test-mode

# Enter responses when prompted:
# > User: I want to build a todo app
# [TEST MODE] Enter Brian's response: I'll help you build a todo app. Let me create a PRD...
```

---

## Debugging E2E Tests

### 1. Enable Verbose Logging

```python
import structlog

# Enable debug logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)
```

### 2. Inspect Captured Output

```python
from tests.e2e.harness.chat_harness import ChatHarness

harness = ChatHarness()
result = harness.execute(fixture)

# Print raw output
print("=== RAW OUTPUT ===")
print(result.actual_output)

# Print cleaned output (ANSI stripped)
print("\n=== CLEANED OUTPUT ===")
from tests.e2e.harness.output_matcher import OutputMatcher
matcher = OutputMatcher()
print(matcher._strip_ansi(result.actual_output))
```

### 3. Check Transcript Files

When running in capture mode, transcripts are saved to `.gao-dev/test_transcripts/`:

```python
from pathlib import Path
from tests.e2e.harness.transcript_validator import TranscriptValidator

transcript_path = Path(".gao-dev/test_transcripts/session_2025-11-15_16-30-00.json")
validator = TranscriptValidator(transcript_path)

# Validate format
validator.validate_all()

# Print summary
validator.print_summary()
```

### 4. Debug Test Mode Issues

```bash
# Check if test mode is working
gao-dev start --test-mode

# If gao-dev doesn't start:
# 1. Check installed version: pip show gao-dev
# 2. Reinstall: pip install -e .
# 3. Check Python path: which python
```

### 5. Debug Fixture Issues

```python
from tests.e2e.harness.fixture_loader import FixtureLoader
from pathlib import Path

# Load and inspect fixture
fixture = FixtureLoader.load(Path("tests/e2e/fixtures/simple_conversation.yaml"))

print(f"Name: {fixture.name}")
print(f"Turns: {len(fixture.conversation_turns)}")
print(f"Expected Output Patterns: {len(fixture.expected_output)}")

# Print conversation
for i, turn in enumerate(fixture.conversation_turns):
    print(f"\nTurn {i}:")
    print(f"  User: {turn.user_input}")
    print(f"  AI: {turn.ai_response}")
```

---

## Creating New E2E Test Scenarios

### 1. Create a Fixture YAML

```yaml
# tests/e2e/fixtures/my_test.yaml
name: "My Test Scenario"
description: "Test description"

scenario_type: "interactive"  # or "regression"

conversation_turns:
  - user_input: "I want to build an API"
    ai_response: "I'll help you build an API. What kind of API?"

  - user_input: "A REST API for users"
    ai_response: "Great! I'll create a PRD for a REST API with user endpoints."

expected_output:
  - "PRD"
  - "REST API"
  - "user endpoints"

validation_rules:
  check_project_created: true
  check_files_exist:
    - "docs/PRD.md"
```

### 2. Run Your Fixture

```bash
python -m pytest tests/e2e/test_fixture_system.py -v -k "my_test"
```

### 3. Create a Test Function

```python
# tests/e2e/test_my_feature.py
from pathlib import Path
from tests.e2e.harness.chat_harness import ChatHarness
from tests.e2e.harness.fixture_loader import FixtureLoader

def test_my_scenario(tmp_path):
    """Test my custom scenario."""
    fixture_path = Path("tests/e2e/fixtures/my_test.yaml")

    fixture = FixtureLoader.load(fixture_path)

    harness = ChatHarness(project_root=tmp_path)
    result = harness.execute(fixture)

    assert result.success, f"Test failed: {result.mismatches}"
```

---

## Quality Analysis Workflow

### 1. Capture Conversations

```bash
# Run gao-dev with capture mode enabled (automatic in test mode)
gao-dev start --test-mode
```

Transcripts saved to: `.gao-dev/test_transcripts/session_TIMESTAMP.json`

### 2. Analyze Quality

```python
from pathlib import Path
from tests.e2e.analyzer.conversation_analyzer import ConversationAnalyzer
from tests.e2e.reporting.quality_report_generator import ReportGenerator

# Analyze conversation
analyzer = ConversationAnalyzer()
report = analyzer.analyze_conversation(
    Path(".gao-dev/test_transcripts/session_2025-11-15_16-30-00.json")
)

print(f"Quality Score: {report.quality_score}%")
print(f"Issues Found: {len(report.issues)}")

# Generate detailed report
generator = ReportGenerator()
report_text = generator.generate(report)
print(report_text)

# Save report
generator.save_to_file(report, Path("quality_report.txt"))
```

### 3. View Example Report

See: `docs/features/e2e-testing-ux-quality/EXAMPLE_QUALITY_REPORT.txt`

---

## Common Issues & Solutions

### Issue: "ValueError: I/O operation on closed file" (Windows)

**Symptom:**
```
collected 166 items
no tests ran in 1.50s
ValueError: I/O operation on closed file.
```

**Root Cause:**
Pytest's stdout/stderr capture system conflicts with ChatHarness subprocess spawning on Windows.

**Solution:**
Always use `--capture=no` flag when running E2E tests:
```bash
python -m pytest tests/e2e/ --capture=no --tb=short -v
```

Or use the provided script:
```bash
run_e2e_tests.bat
```

### Issue: "gao-dev not found"

**Solution:**
```bash
pip install -e .
```

### Issue: "Test mode not working"

**Solution:**
Check ChatREPL implementation:
```python
# gao_dev/cli/chat_repl.py should have:
if self.test_mode:
    # Test mode enabled
```

Verify with:
```bash
gao-dev start --test-mode
```

### Issue: "Fixture validation fails"

**Solution:**
Check YAML format:
```bash
python -c "
from tests.e2e.harness.fixture_loader import FixtureLoader
from pathlib import Path
FixtureLoader.load(Path('tests/e2e/fixtures/my_test.yaml'))
print('✅ Fixture valid!')
"
```

### Issue: "Output doesn't match expected"

**Solution:**
1. Check for ANSI codes in output
2. Use regex patterns instead of exact strings
3. Enable verbose output: `pytest -v -s`

```python
# Instead of exact match:
expected_output:
  - "Creating PRD"

# Use pattern:
expected_output:
  - "Creating.*PRD"
```

### Issue: "Process doesn't terminate"

**Solution:**
Add timeout:
```python
harness = ChatHarness(timeout_seconds=30)
```

---

## Advanced Usage

### 1. Custom AI Injector

```python
from tests.e2e.harness.ai_response_injector import AIResponseInjector

# Create custom injector
injector = AIResponseInjector()
injector.add_response("I'll create that for you")
injector.add_response("Done!")

# Use in ChatSession
session = ChatSession(ai_injector=injector, test_mode=True)
```

### 2. Programmatic Testing

```python
from tests.e2e.harness.chat_harness import ChatHarness

# Create harness
harness = ChatHarness(capture_mode=True)

# Execute multiple fixtures
fixtures = [
    "greenfield_init.yaml",
    "brownfield_analysis.yaml",
    "error_recovery.yaml"
]

results = []
for fixture_name in fixtures:
    fixture = FixtureLoader.load(Path(f"tests/e2e/fixtures/{fixture_name}"))
    result = harness.execute(fixture)
    results.append(result)

# Analyze results
passed = sum(1 for r in results if r.success)
print(f"Passed: {passed}/{len(results)}")
```

### 3. Batch Quality Analysis

```python
from pathlib import Path
from tests.e2e.analyzer.conversation_analyzer import ConversationAnalyzer

transcript_dir = Path(".gao-dev/test_transcripts")
analyzer = ConversationAnalyzer()

scores = []
for transcript_path in transcript_dir.glob("*.json"):
    report = analyzer.analyze_conversation(transcript_path)
    scores.append(report.quality_score)
    print(f"{transcript_path.name}: {report.quality_score}%")

print(f"\nAverage Quality: {sum(scores)/len(scores):.2f}%")
```

---

## Continuous Integration

### Run in CI/CD

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest

      - name: Run E2E tests
        run: |
          python -m pytest tests/e2e/ -v --tb=short
```

---

## Next Steps

1. **Start Simple**: Run existing fixtures to understand the flow
2. **Create Custom Fixtures**: Add your own test scenarios
3. **Analyze Quality**: Use the quality analysis system to measure UX
4. **Iterate**: Improve Brian based on quality reports

**Example Workflow:**
```bash
# 1. Run a test
python -m pytest tests/e2e/test_fixture_system.py::TestFixtureExecution::test_simple_conversation_fixture -v -s

# 2. Capture conversation
# (automatic in test mode)

# 3. Analyze quality
python -c "
from pathlib import Path
from tests.e2e.analyzer.conversation_analyzer import ConversationAnalyzer
from tests.e2e.reporting.quality_report_generator import ReportGenerator

analyzer = ConversationAnalyzer()
report = analyzer.analyze_conversation(Path('.gao-dev/test_transcripts/session_*.json'))

generator = ReportGenerator()
print(generator.generate(report))
"

# 4. Fix issues and repeat
```

---

## Resources

- **Fixtures**: `tests/e2e/fixtures/*.yaml`
- **Sample Transcripts**: `tests/e2e/sample_transcripts/*.json`
- **Example Report**: `docs/features/e2e-testing-ux-quality/EXAMPLE_QUALITY_REPORT.txt`
- **Architecture**: `docs/features/e2e-testing-ux-quality/ARCHITECTURE.md`
- **PRD**: `docs/features/e2e-testing-ux-quality/PRD.md`

---

**Need Help?** Check the test files in `tests/e2e/test_*.py` for working examples!
