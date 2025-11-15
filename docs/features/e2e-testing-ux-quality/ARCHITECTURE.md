# E2E Testing & UX Quality Analysis System - Architecture

**Feature**: e2e-testing-ux-quality
**Author**: Winston (Technical Architect)
**Status**: Planning
**Created**: 2025-11-15
**Updated**: 2025-11-15

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Models](#data-models)
5. [API Design](#api-design)
6. [Integration Points](#integration-points)
7. [Testing Infrastructure](#testing-infrastructure)
8. [Performance Considerations](#performance-considerations)
9. [Security Considerations](#security-considerations)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The E2E Testing & UX Quality Analysis System is a comprehensive testing framework that enables:
- **Cost-free E2E testing** using local AI models (opencode/ollama/deepseek-r1)
- **Interactive debugging** where AI (Claude Code) can programmatically test Brian
- **Conversation quality analysis** with actionable UX improvement reports
- **Automated regression testing** with fixture-based scenarios for CI/CD

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Test Execution Layer                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │   Mode 1:    │   │   Mode 2:    │   │   Mode 3:    │          │
│  │ Interactive  │   │  Quality     │   │  Regression  │          │
│  │   Debug      │   │  Analysis    │   │   Tests      │          │
│  └───────┬──────┘   └───────┬──────┘   └───────┬──────┘          │
│          │                  │                  │                  │
└──────────┼──────────────────┼──────────────────┼──────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Core Testing Infrastructure                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │ ChatHarness  │   │  Fixture     │   │   Output     │          │
│  │  (pexpect/   │   │  Loader      │   │   Matcher    │          │
│  │   wexpect)   │   │  (YAML)      │   │   (ANSI)     │          │
│  └───────┬──────┘   └───────┬──────┘   └───────┬──────┘          │
│          │                  │                  │                  │
└──────────┼──────────────────┼──────────────────┼──────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  GAO-Dev Interactive Chat (SUT)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  gao-dev start [--test-mode] [--capture-mode] [--fixture FILE]     │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │  ChatREPL    │──▶│ ChatSession  │──▶│Conversational│          │
│  │              │   │              │   │    Brian     │          │
│  └──────────────┘   └──────────────┘   └───────┬──────┘          │
│                                                 │                  │
│                                                 ▼                  │
│                         ┌──────────────────────────────┐          │
│                         │   Provider Abstraction       │          │
│                         │  (opencode/ollama/deepseek)  │          │
│                         └──────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Conversation Logging Layer                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  .gao-dev/test_transcripts/                                         │
│  ├── session_2025-11-15_09-30-45.json                              │
│  └── session_2025-11-15_10-15-20.json                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Principles

### 1. Cost-First Design
- **ALL tests default to opencode/ollama/deepseek-r1**
- Zero API costs for development and CI/CD
- Environment variable override for occasional Claude API testing

### 2. Provider Abstraction
- Leverage existing Epic 21 provider architecture
- No hardcoded provider dependencies
- Testable with any AI backend

### 3. Separation of Concerns
- Test infrastructure isolated from production code
- Minimal invasive changes to ChatREPL/ChatSession
- Clean interfaces between components

### 4. Observability
- Full conversation logging in capture mode
- Detailed quality analysis reports
- Actionable recommendations with examples

### 5. Maintainability
- YAML-based fixtures (human-readable)
- Clear error messages
- Comprehensive documentation

---

## Component Architecture

### 1. Test Execution Layer

#### 1.1 ClaudeTester (Interactive Debug - Mode 1)

**Purpose**: Framework for Claude Code to programmatically interact with Brian

**Responsibilities**:
- Spawn `gao-dev start` subprocess
- Send user inputs
- Receive Brian responses
- Analyze conversation quality
- Generate UX improvement reports

**Key Methods**:
```python
class ClaudeTester:
    def __init__(self, scenario: str):
        """Initialize tester for given scenario."""

    def start_session(self) -> None:
        """Spawn gao-dev start --capture-mode subprocess."""

    def send(self, message: str) -> str:
        """Send message to Brian, return response."""

    def end_session_and_analyze(self) -> QualityReport:
        """End session, analyze conversation, generate report."""

    def _display_report(self, report: QualityReport):
        """Display UX quality report with recommendations."""
```

**Dependencies**:
- ChatHarness (subprocess management)
- ConversationAnalyzer (quality analysis)
- ReportGenerator (report formatting)

#### 1.2 RegressionTestRunner (Regression Tests - Mode 3)

**Purpose**: Execute fixture-based tests for CI/CD

**Responsibilities**:
- Load test scenarios from YAML fixtures
- Execute tests with scripted AI responses
- Validate outputs against expected patterns
- Report pass/fail with diffs

**Key Methods**:
```python
class RegressionTestRunner:
    def __init__(self, fixture_path: Path):
        """Initialize with fixture file."""

    def run_test(self) -> TestResult:
        """Execute test scenario, return result."""

    def validate_output(self, actual: str, expected: List[str]) -> bool:
        """Validate output matches expected patterns."""
```

**Dependencies**:
- FixtureLoader (load YAML scenarios)
- ChatHarness (subprocess execution)
- OutputMatcher (pattern matching with ANSI stripping)

### 2. Core Testing Infrastructure

#### 2.1 ChatHarness

**Purpose**: Spawn and interact with `gao-dev start` subprocess

**Responsibilities**:
- Cross-platform subprocess spawning (pexpect/wexpect)
- Send user input via stdin
- Capture output from stdout/stderr
- Handle timeouts and errors
- Clean subprocess termination

**Implementation**:
```python
class ChatHarness:
    """Spawn and interact with gao-dev start subprocess."""

    def __init__(
        self,
        test_mode: bool = False,
        capture_mode: bool = False,
        fixture_path: Optional[Path] = None,
        timeout: int = 30
    ):
        self.test_mode = test_mode
        self.capture_mode = capture_mode
        self.fixture_path = fixture_path
        self.timeout = timeout
        self.process = None
        self._platform = self._detect_platform()

    def start(self) -> None:
        """Spawn gao-dev start subprocess."""
        cmd = self._build_command()

        if self._platform == "windows":
            import wexpect
            self.process = wexpect.spawn(cmd, timeout=self.timeout)
        else:
            import pexpect
            self.process = pexpect.spawn(cmd, timeout=self.timeout)

        # Wait for greeting
        self.expect(["Welcome to GAO-Dev"])

    def send(self, text: str) -> None:
        """Send input to chat."""
        self.process.sendline(text)

    def expect(
        self,
        patterns: List[str],
        timeout: Optional[int] = None
    ) -> str:
        """Wait for output matching patterns."""
        output = self.read_until_prompt(timeout or self.timeout)
        clean_output = self._strip_ansi(output)

        for pattern in patterns:
            if not re.search(pattern, clean_output, re.DOTALL | re.MULTILINE):
                raise AssertionError(
                    f"Expected pattern not found: {pattern}\n"
                    f"Actual output:\n{clean_output}"
                )

        return clean_output

    def read_until_prompt(self, timeout: int) -> str:
        """Read output until Brian prompt appears."""
        output = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = self.process.read_nonblocking(size=1024, timeout=0.1)
                output += chunk

                # Check for Brian prompt
                if self._has_prompt(output):
                    break
            except:
                pass

        return output

    def close(self) -> None:
        """Terminate subprocess."""
        if self.process:
            self.process.sendline("exit")
            self.process.terminate()

    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _build_command(self) -> str:
        """Build gao-dev start command with flags."""
        cmd = "gao-dev start"

        if self.test_mode:
            cmd += " --test-mode"
        if self.capture_mode:
            cmd += " --capture-mode"
        if self.fixture_path:
            cmd += f" --fixture {self.fixture_path}"

        return cmd

    def _detect_platform(self) -> str:
        """Detect OS platform."""
        import platform
        system = platform.system().lower()
        return "windows" if system == "windows" else "unix"

    def _has_prompt(self, output: str) -> bool:
        """Check if output contains Brian prompt."""
        return "You: " in output or ">" in output
```

**Platform-Specific Notes**:
- **Unix/macOS**: Use `pexpect`
- **Windows**: Use `wexpect` (pexpect port for Windows)
- Both have similar APIs, abstracted in ChatHarness

#### 2.2 FixtureLoader

**Purpose**: Load and validate YAML test scenarios

**Implementation**:
```python
class FixtureLoader:
    """Load and validate YAML test fixtures."""

    @staticmethod
    def load(fixture_path: Path) -> TestScenario:
        """Load fixture from YAML file."""
        with open(fixture_path, 'r') as f:
            data = yaml.safe_load(f)

        # Validate schema
        FixtureLoader._validate_schema(data)

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
    def _validate_schema(data: dict) -> None:
        """Validate fixture schema."""
        required_keys = ["name", "description", "scenario"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")

        if not isinstance(data["scenario"], list):
            raise ValueError("scenario must be a list")

        for step in data["scenario"]:
            if "user_input" not in step:
                raise ValueError("Each step must have user_input")
```

**Fixture Format**:
```yaml
name: "greenfield_initialization"
description: "Test greenfield project initialization flow"

scenario:
  - user_input: "I want to build a todo app"
    brian_response: |
      I'll help you create a todo app. Based on your requirements,
      I detect this is a greenfield project (Scale Level 4).

      Would you like me to initialize the project structure?
    expect_output:
      - "Scale Level.*4"
      - "greenfield"
      - "initialize"
    timeout_ms: 5000

  - user_input: "yes"
    brian_response: |
      Great! Initializing project structure...
      ✓ Created docs/
      ✓ Created .gao-dev/
      Project initialized successfully!
    expect_output:
      - "initialized successfully"
      - "Created docs"
    timeout_ms: 10000
```

#### 2.3 OutputMatcher

**Purpose**: Verify subprocess output matches expected patterns

**Implementation**:
```python
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
        """Generate diff between actual and expected."""
        import difflib

        clean_actual = self.strip_ansi(actual)

        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            clean_actual.splitlines(keepends=True),
            fromfile="expected",
            tofile="actual"
        )

        return ''.join(diff)
```

### 3. Conversation Analysis Layer (Mode 2)

#### 3.1 ConversationAnalyzer

**Purpose**: Analyze conversation transcripts for UX quality issues

**Implementation**:
```python
class ConversationAnalyzer:
    """
    Analyze conversation quality and identify UX deficiencies.

    Detects:
    - Intent understanding issues
    - Missed probing opportunities
    - Unused context
    - Poor response relevance
    """

    def __init__(self, ai_service: Optional[AIAnalysisService] = None):
        """Initialize with optional AI service for deep analysis."""
        self.ai_service = ai_service or self._create_default_service()

    def analyze_conversation(
        self,
        transcript_path: Path
    ) -> QualityReport:
        """Analyze a conversation transcript."""
        transcript = self._load_transcript(transcript_path)

        issues = []

        for turn_num, turn in enumerate(transcript):
            # Pattern-based detection
            issues.extend(self._detect_intent_issues(turn_num, turn))
            issues.extend(self._detect_probing_issues(turn_num, turn))
            issues.extend(self._detect_context_issues(turn_num, turn))

            # AI-powered deep analysis (optional)
            if self.ai_service:
                issues.extend(self._ai_analyze_turn(turn_num, turn))

        # Calculate quality score
        quality_score = self._calculate_score(issues, len(transcript))

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        return QualityReport(
            transcript_path=transcript_path,
            total_turns=len(transcript),
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations
        )

    def _detect_intent_issues(
        self,
        turn_num: int,
        turn: ConversationTurn
    ) -> List[QualityIssue]:
        """Detect intent understanding issues using patterns."""
        issues = []

        response = turn["brian_response"].lower()

        # Check for understanding signals
        understanding_signals = [
            "i understand", "got it", "i'll help you",
            "you want to", "you're looking to",
            "based on your request", "from what you've described"
        ]

        has_understanding_signal = any(
            signal in response for signal in understanding_signals
        )

        if not has_understanding_signal:
            issues.append(QualityIssue(
                turn_num=turn_num,
                issue_type="missing_intent_confirmation",
                severity="medium",
                description="Brian didn't explicitly confirm understanding of user intent",
                suggestion="Add explicit confirmation: 'I understand you want to...'"
            ))

        return issues

    def _detect_probing_issues(
        self,
        turn_num: int,
        turn: ConversationTurn
    ) -> List[QualityIssue]:
        """Detect missed probing opportunities."""
        issues = []

        user_input = turn["user_input"]
        brian_response = turn["brian_response"]

        # Check if user input is vague
        vague_patterns = [
            r"^(build|create|make) (a|an) \w+$",  # "build a app"
            r"^(i want|i need) \w+",  # "i want something"
            r"^help",  # Just "help"
            r"^\w{1,3}$",  # Very short input
        ]

        is_vague = any(
            re.match(p, user_input.lower()) for p in vague_patterns
        )

        # Check if Brian asked questions
        asked_question = "?" in brian_response

        if is_vague and not asked_question:
            issues.append(QualityIssue(
                turn_num=turn_num,
                issue_type="missed_probing_opportunity",
                severity="high",
                description=f"User input vague ('{user_input}'), but Brian didn't probe for details",
                suggestion="Ask clarifying questions: What features? What users? What tech stack?"
            ))

        return issues

    def _detect_context_issues(
        self,
        turn_num: int,
        turn: ConversationTurn
    ) -> List[QualityIssue]:
        """Detect unused context."""
        issues = []

        context_used = turn.get("context_used", {})
        brian_response = turn["brian_response"]

        # Check if context was available but not referenced
        if context_used:
            referenced_context = False

            for context_key, context_value in context_used.items():
                if str(context_value).lower() in brian_response.lower():
                    referenced_context = True
                    break

            if not referenced_context:
                issues.append(QualityIssue(
                    turn_num=turn_num,
                    issue_type="unused_context",
                    severity="low",
                    description=f"Context available ({list(context_used.keys())}) but not referenced",
                    suggestion="Reference available context to show continuity"
                ))

        return issues

    def _calculate_score(
        self,
        issues: List[QualityIssue],
        total_turns: int
    ) -> float:
        """Calculate quality score (0-100)."""
        if total_turns == 0:
            return 0.0

        # Weight issues by severity
        severity_weights = {
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0
        }

        total_penalty = sum(
            severity_weights[issue.severity] for issue in issues
        )

        # Maximum penalty per turn
        max_penalty_per_turn = 10.0
        max_total_penalty = total_turns * max_penalty_per_turn

        # Calculate score (0-100)
        if max_total_penalty == 0:
            return 100.0

        score = max(0.0, 100.0 * (1.0 - (total_penalty / max_total_penalty)))

        return round(score, 1)

    def _generate_recommendations(
        self,
        issues: List[QualityIssue]
    ) -> List[str]:
        """Generate actionable recommendations."""
        # Group issues by type
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)

        recommendations = []

        # Generate recommendations per issue type
        for issue_type, type_issues in issue_types.items():
            count = len(type_issues)
            example = type_issues[0]

            recommendations.append(
                f"Fix {count} instance(s) of {issue_type}: {example.suggestion}"
            )

        return recommendations

    def _load_transcript(self, path: Path) -> List[ConversationTurn]:
        """Load conversation transcript from JSON."""
        with open(path, 'r') as f:
            return json.load(f)

    def _create_default_service(self) -> AIAnalysisService:
        """Create default AI service with opencode/ollama."""
        from gao_dev.core.services.ai_analysis_service import AIAnalysisService
        from gao_dev.core.services.process_executor import ProcessExecutor

        # Use opencode/ollama/deepseek-r1 (cost-free)
        executor = ProcessExecutor(
            project_root=Path.cwd(),
            provider_name="opencode",
            provider_config={
                "ai_provider": "ollama",
                "use_local": True,
                "model": "deepseek-r1"
            }
        )

        return AIAnalysisService(executor)
```

#### 3.2 ReportGenerator

**Purpose**: Generate formatted quality reports

**Implementation**:
```python
class ReportGenerator:
    """Generate formatted quality reports."""

    def generate(self, report: QualityReport) -> str:
        """Generate human-readable report."""
        output = []

        output.append("=" * 60)
        output.append("CONVERSATION QUALITY REPORT")
        output.append("=" * 60)
        output.append("")
        output.append(f"Transcript: {report.transcript_path.name}")
        output.append(f"Total Turns: {report.total_turns}")
        output.append(f"Quality Score: {report.quality_score:.1f}%")
        output.append(f"Issues Found: {len(report.issues)}")
        output.append("")

        if report.issues:
            output.append("-" * 60)
            output.append("ISSUES IDENTIFIED")
            output.append("-" * 60)
            output.append("")

            for issue in report.issues:
                output.append(f"Turn {issue.turn_num + 1}: {issue.issue_type}")
                output.append(f"  Severity: {issue.severity.upper()}")
                output.append(f"  Issue: {issue.description}")
                output.append(f"  💡 Suggestion: {issue.suggestion}")
                output.append("")

        output.append("-" * 60)
        output.append("RECOMMENDATIONS")
        output.append("-" * 60)
        output.append("")

        for i, rec in enumerate(report.recommendations, 1):
            output.append(f"{i}. {rec}")

        output.append("")
        output.append("=" * 60)

        return "\n".join(output)
```

### 4. Integration with ChatREPL

#### 4.1 Test Mode Support

Add flags to `gao-dev start` command:

```python
# gao_dev/cli/commands.py

@cli.command("start")
@click.option("--project", type=Path, help="Project root (default: auto-detect)")
@click.option("--test-mode", is_flag=True, help="Enable test mode with fixture responses")
@click.option("--capture-mode", is_flag=True, help="Enable conversation capture logging")
@click.option("--fixture", type=Path, help="Fixture file for test mode")
def start_chat(
    project: Optional[Path],
    test_mode: bool,
    capture_mode: bool,
    fixture: Optional[Path]
):
    """Start interactive chat with Brian."""
    from .chat_repl import ChatREPL

    # Create REPL with test flags
    repl = ChatREPL(
        project_root=project,
        test_mode=test_mode,
        capture_mode=capture_mode,
        fixture_path=fixture
    )

    # Start async loop
    try:
        asyncio.run(repl.start())
    except Exception as e:
        click.echo(f"[ERROR] Failed to start REPL: {e}", err=True)
        sys.exit(1)
```

#### 4.2 ChatREPL Modifications

```python
# gao_dev/cli/chat_repl.py

class ChatREPL:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        test_mode: bool = False,
        capture_mode: bool = False,
        fixture_path: Optional[Path] = None
    ):
        self.project_root = project_root or Path.cwd()
        self.test_mode = test_mode
        self.capture_mode = capture_mode
        self.fixture_path = fixture_path

        # Load fixture if in test mode
        if self.test_mode and self.fixture_path:
            from tests.e2e.harness.ai_response_injector import AIResponseInjector
            self.ai_injector = AIResponseInjector(self.fixture_path)
        else:
            self.ai_injector = None

        # ... existing initialization ...
```

#### 4.3 ChatSession Modifications

```python
# gao_dev/orchestrator/chat_session.py

class ChatSession:
    def __init__(
        self,
        conversational_brian,
        command_router,
        project_root: Path,
        capture_mode: bool = False
    ):
        # ... existing initialization ...

        self.capture_mode = capture_mode
        self.conversation_transcript = []

        if self.capture_mode:
            self.transcript_path = self._init_transcript()

    async def handle_input(self, user_input: str):
        """Handle user input with optional capture."""
        # Capture turn start
        if self.capture_mode:
            turn = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "brian_response": None,
                "context_used": self._get_active_context(),
            }

        # Get Brian's response
        response = await self.conversational_brian.handle_message(user_input)

        # Capture turn end
        if self.capture_mode:
            turn["brian_response"] = response
            self.conversation_transcript.append(turn)
            self._save_transcript()

        return response

    def _init_transcript(self) -> Path:
        """Initialize transcript file."""
        gao_dev_dir = self.project_root / ".gao-dev" / "test_transcripts"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return gao_dev_dir / f"session_{timestamp}.json"

    def _save_transcript(self):
        """Save transcript to disk."""
        with open(self.transcript_path, 'w') as f:
            json.dump(self.conversation_transcript, f, indent=2)
```

---

## Data Models

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class TestScenario:
    """Test scenario loaded from YAML fixture."""
    name: str
    description: str
    steps: List['TestStep']

@dataclass
class TestStep:
    """Single step in test scenario."""
    user_input: str
    expect_output: List[str]  # Regex patterns
    brian_response: Optional[str] = None  # For test mode
    timeout_ms: int = 5000

@dataclass
class ConversationTurn:
    """Single turn in conversation."""
    timestamp: str
    user_input: str
    brian_response: str
    context_used: Dict[str, Any]
    internal_reasoning: Optional[str] = None

@dataclass
class QualityIssue:
    """UX quality issue detected in conversation."""
    turn_num: int
    issue_type: str  # intent_misunderstanding, missed_probing_opportunity, etc.
    severity: str  # high, medium, low
    description: str
    suggestion: str

@dataclass
class QualityReport:
    """Conversation quality analysis report."""
    transcript_path: Path
    total_turns: int
    quality_score: float  # 0-100
    issues: List[QualityIssue]
    recommendations: List[str]

@dataclass
class MatchResult:
    """Output pattern matching result."""
    success: bool
    matches: List[Dict[str, Any]]
    actual_output: str

@dataclass
class TestResult:
    """E2E test execution result."""
    scenario_name: str
    passed: bool
    duration_ms: float
    failures: List[str]
    transcript_path: Optional[Path] = None
```

---

## API Design

### Public APIs

#### ChatHarness

```python
# Start interactive session
harness = ChatHarness(capture_mode=True)
harness.start()

# Send input
harness.send("I want to build a todo app")

# Expect patterns in output
harness.expect(["Scale Level", "greenfield"])

# Close session
harness.close()
```

#### ClaudeTester

```python
# Start interactive testing session
tester = ClaudeTester(scenario="greenfield_vague_request")
tester.start_session()

# Interact with Brian
response = tester.send("build a app")
response = tester.send("a todo app")

# End and analyze
report = tester.end_session_and_analyze()

# Display report
print(f"Quality Score: {report.quality_score}%")
for issue in report.issues:
    print(f"- {issue.description}")
```

#### ConversationAnalyzer

```python
# Analyze transcript
analyzer = ConversationAnalyzer()
report = analyzer.analyze_conversation(
    Path(".gao-dev/test_transcripts/session_2025-11-15_09-30-45.json")
)

# Generate formatted report
generator = ReportGenerator()
formatted = generator.generate(report)
print(formatted)
```

---

## Integration Points

### 1. Provider System (Epic 21, Epic 35)

**Integration**: Use existing provider abstraction for cost-free testing

```python
# Default to opencode/ollama/deepseek-r1
executor = ProcessExecutor(
    project_root=Path.cwd(),
    provider_name="opencode",
    provider_config={
        "ai_provider": "ollama",
        "use_local": True,
        "model": "deepseek-r1"
    }
)

# Override with environment variable
import os
if os.getenv("E2E_TEST_PROVIDER") == "claude-code":
    executor = ProcessExecutor(
        project_root=Path.cwd(),
        provider_name="claude-code"
    )
```

### 2. ChatREPL (Epic 30)

**Integration**: Add test mode and capture mode flags

- Minimal changes to existing code
- Flags passed through to ChatSession
- Provider override respected

### 3. ChatSession (Epic 30)

**Integration**: Add conversation logging

- Capture turns in capture_mode
- Persist to `.gao-dev/test_transcripts/`
- Include context and metadata

### 4. ConversationalBrian (Epic 30)

**Integration**: Support fixture response injection

- If test_mode enabled, load responses from fixture
- Otherwise, use normal AI provider flow
- Transparent to caller

---

## Testing Infrastructure

### Directory Structure

```
tests/e2e/
├── __init__.py
│
├── chat/                          # E2E chat tests
│   ├── __init__.py
│   ├── test_chat_subprocess.py    # Subprocess-based tests
│   ├── test_chat_workflows.py     # Full workflow tests
│   └── test_chat_error_handling.py
│
├── fixtures/                       # Test scenarios
│   ├── greenfield_init.yaml
│   ├── brownfield_analysis.yaml
│   ├── error_recovery.yaml
│   ├── multi_turn_conversation.yaml
│   └── README.md                  # Fixture documentation
│
├── harness/                        # Test infrastructure
│   ├── __init__.py
│   ├── chat_harness.py             # pexpect wrapper
│   ├── fixture_loader.py           # YAML loader
│   ├── output_matcher.py           # Pattern matching
│   └── ai_response_injector.py     # Response injection
│
├── analysis/                       # Quality analysis
│   ├── __init__.py
│   ├── conversation_analyzer.py    # Quality analyzer
│   ├── quality_scorer.py           # Scoring algorithm
│   └── report_generator.py         # Report formatting
│
├── interactive/                    # Interactive testing
│   ├── __init__.py
│   ├── claude_tester.py            # ClaudeTester framework
│   └── test_claude_tester.py       # Tests for ClaudeTester
│
└── conftest.py                     # Pytest fixtures
```

### Pytest Configuration

```python
# tests/e2e/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def fixture_dir() -> Path:
    """Return fixture directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def chat_harness():
    """Create ChatHarness with opencode/deepseek-r1."""
    from tests.e2e.harness.chat_harness import ChatHarness

    harness = ChatHarness(capture_mode=True)
    yield harness
    harness.close()

@pytest.fixture(autouse=True)
def set_test_provider(monkeypatch):
    """Ensure all tests use opencode/ollama/deepseek-r1."""
    monkeypatch.setenv("E2E_TEST_PROVIDER", "opencode")
    monkeypatch.setenv("OPENCODE_AI_PROVIDER", "ollama")
    monkeypatch.setenv("OPENCODE_MODEL", "deepseek-r1")
```

---

## Performance Considerations

### 1. Test Execution Speed

**Target**: <2s per test with local model

**Optimizations**:
- Parallel test execution (pytest-xdist)
- Subprocess pooling (reuse processes)
- Caching of common setups
- Timeout optimization

### 2. Conversation Capture Overhead

**Target**: <5% overhead vs normal execution

**Optimizations**:
- Asynchronous logging (non-blocking)
- Buffered writes
- Minimal serialization overhead

### 3. Quality Analysis Performance

**Target**: <10s per conversation

**Optimizations**:
- Pattern-based detection first (fast)
- AI analysis only for ambiguous cases (slower)
- Parallel issue detection
- Result caching

### 4. CI/CD Performance

**Target**: <5 minutes full test suite

**Strategies**:
- Parallel test execution across workers
- Fixture-based tests only (no live AI)
- Incremental testing (only changed code)
- Fast-fail on critical errors

---

## Security Considerations

### 1. Subprocess Safety

- Sanitize all inputs to subprocess
- Timeout enforcement to prevent hung processes
- Resource cleanup on test failure
- No shell injection vulnerabilities

### 2. Conversation Privacy

- Transcripts stored locally (`.gao-dev/test_transcripts/`)
- No external logging
- Gitignore test transcripts
- Option to disable capture mode

### 3. Fixture Security

- YAML safe_load (no code execution)
- Schema validation
- Input sanitization
- No sensitive data in fixtures (use placeholders)

### 4. Provider Security

- Respect existing provider security (Epic 21, 35)
- Environment variable validation
- No API keys in fixtures or transcripts
- Local model usage by default (no network calls)

---

## Deployment Architecture

### Local Development

```
Developer Machine
├── GAO-Dev installed (pip install -e .)
├── ollama running with deepseek-r1 model
├── opencode CLI on PATH
├── pytest installed
└── Tests run locally: pytest tests/e2e/
```

### CI/CD Pipeline

```
GitHub Actions
├── Setup Python 3.10+
├── Install GAO-Dev (pip install .)
├── Install ollama
├── Download deepseek-r1 model
├── Install opencode CLI
├── Run tests: pytest tests/e2e/ -n auto
└── Generate coverage report
```

### Test Artifacts

```
.gao-dev/test_transcripts/        # Conversation logs (gitignored)
.gao-dev/test_reports/            # Quality reports (gitignored)
tests/e2e/fixtures/               # Test scenarios (committed)
htmlcov/                          # Coverage reports (gitignored)
```

---

## Migration & Rollout Strategy

### Phase 1: Infrastructure (Week 1)
1. Add pexpect/wexpect dependencies
2. Implement ChatHarness
3. Implement FixtureLoader and OutputMatcher
4. Add --test-mode and --capture-mode flags to ChatREPL
5. Create 5 basic E2E tests

### Phase 2: Quality Analysis (Week 2)
1. Implement ConversationAnalyzer with pattern detection
2. Implement quality scoring algorithm
3. Implement ReportGenerator
4. Add conversation capture to ChatSession
5. Create ClaudeTester framework
6. Document 1 full interactive test session

### Phase 3: Regression Testing (Week 3)
1. Create 20+ fixture-based test scenarios
2. Integrate with CI/CD (GitHub Actions)
3. Enable parallel test execution
4. Create fixture conversion tool
5. Validate all tests passing in CI

### Phase 4: Polish (Week 4)
1. User guide for writing E2E tests
2. Developer guide for ClaudeTester
3. Quality analysis interpretation guide
4. Example conversation analyses
5. Performance optimization
6. Final QA and documentation

---

## Appendix

### Dependencies

**Runtime:**
- `pexpect` (Unix/macOS) - subprocess interaction
- `wexpect` (Windows) - pexpect port for Windows
- `pyyaml` - fixture loading (already installed)
- `pytest-timeout` - test timeout management

**Development:**
- `pytest` - test framework (already installed)
- `pytest-xdist` - parallel test execution
- `pytest-cov` - coverage reporting (already installed)

### References

- pexpect docs: https://pexpect.readthedocs.io/
- wexpect: https://pypi.org/project/wexpect/
- pytest-xdist: https://pytest-xdist.readthedocs.io/
- Epic 21: AI Analysis Service & Provider Abstraction
- Epic 30: Interactive Brian Chat Interface
- Epic 35: Interactive Provider Selection

### Glossary

- **E2E**: End-to-end testing from user perspective
- **UX**: User experience
- **ANSI codes**: Terminal formatting escape sequences
- **Fixture**: Pre-defined test scenario
- **Capture mode**: Instrumented execution with logging
- **Test mode**: Execution with scripted AI responses
- **SUT**: System Under Test (gao-dev start)
