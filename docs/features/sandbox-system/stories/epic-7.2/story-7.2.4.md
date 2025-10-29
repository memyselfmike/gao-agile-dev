# Story 7.2.4: Add Clarification Dialog

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 2
**Status**: Done
**Priority**: Medium

---

## User Story

As **GAO-Dev**, I want to **ask clarifying questions when initial prompt is ambiguous**, so that **I can select the appropriate workflow and understand user requirements before starting work**.

---

## Context

When GAO-Dev receives an ambiguous initial prompt (e.g., "Fix it" or "Build an app"), it needs to ask clarifying questions to select the right workflow. The behavior differs between CLI mode (interactive) and benchmark mode (automated).

**Problem**:
- WorkflowSelector may not have enough context to choose workflow
- Initial prompts can be vague or incomplete
- No mechanism to ask user for clarification
- Benchmark mode needs different behavior than CLI mode

**Solution**:
Add clarification dialog capability to GAODevOrchestrator that:
- Detects when clarification is needed
- In CLI mode: Prompts user interactively
- In benchmark mode: Uses sensible defaults or fails gracefully
- Logs clarification interactions

---

## Acceptance Criteria

### AC1: Clarification Detection
- [ ] WorkflowSelector returns `clarifying_questions` when workflow unclear
- [ ] GAODevOrchestrator detects need for clarification
- [ ] Structured questions format (multiple choice or text)

### AC2: CLI Mode - Interactive Clarification
- [ ] Add `ask_clarification(questions: List[Question])` method
- [ ] Display questions to user via CLI
- [ ] Collect user responses
- [ ] Re-run workflow selection with additional context

### AC3: Benchmark Mode - Automated Handling
- [ ] Detect when running in benchmark mode
- [ ] Use default answers based on question type
- [ ] OR fail gracefully with clear error message
- [ ] Log that defaults were used

### AC4: Execution Mode Detection
- [ ] Add `mode` attribute to GAODevOrchestrator ("cli", "benchmark", "api")
- [ ] Automatically detect mode based on context
- [ ] Allow explicit mode override

### AC5: Enhanced Prompt Building
- [ ] Combine initial_prompt + clarification_answers into enhanced_prompt
- [ ] Pass enhanced_prompt to workflow selection
- [ ] Log full context used for selection

### AC6: Logging
- [ ] Log clarification questions asked
- [ ] Log user/default answers
- [ ] Log workflow selected after clarification
- [ ] Structured logging for analysis

### AC7: Tests
- [ ] Unit tests for ask_clarification() in both modes
- [ ] Test default answer generation
- [ ] Test prompt enhancement
- [ ] Mock user input for CLI mode tests
- [ ] >80% code coverage

---

## Technical Details

### Question Data Model

```python
# gao_dev/orchestrator/workflow_selector.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum

class QuestionType(Enum):
    """Type of clarification question."""
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    YES_NO = "yes_no"

@dataclass
class ClarificationQuestion:
    """A clarification question to ask user."""
    question: str
    question_type: QuestionType
    options: Optional[List[str]] = None  # For multiple choice
    default: Optional[str] = None  # Default answer for benchmark mode
    key: str = ""  # Identifier for this question

@dataclass
class ClarificationAnswer:
    """Answer to a clarification question."""
    question_key: str
    answer: str
    source: str  # "user", "default", "config"
```

### Clarification Dialog Implementation

```python
# gao_dev/orchestrator/orchestrator.py

from enum import Enum
from typing import List, Dict, Optional
from .workflow_selector import ClarificationQuestion, ClarificationAnswer

class ExecutionMode(Enum):
    """Execution mode for GAO-Dev."""
    CLI = "cli"  # Interactive CLI
    BENCHMARK = "benchmark"  # Automated benchmark
    API = "api"  # API service

class GAODevOrchestrator:

    def __init__(
        self,
        project_root: Optional[Path] = None,
        api_key: Optional[str] = None,
        mode: Optional[ExecutionMode] = None
    ):
        # Existing initialization...

        # Detect execution mode
        self.mode = mode or self._detect_mode()

    def _detect_mode(self) -> ExecutionMode:
        """Auto-detect execution mode based on context."""
        # Check for interactive terminal
        import sys
        if sys.stdin.isatty():
            return ExecutionMode.CLI
        else:
            return ExecutionMode.BENCHMARK

    async def ask_clarification(
        self,
        questions: List[ClarificationQuestion]
    ) -> List[ClarificationAnswer]:
        """
        Ask clarifying questions based on execution mode.

        In CLI mode: Prompt user interactively
        In benchmark mode: Use default answers
        In API mode: Return questions to caller

        Args:
            questions: List of questions to ask

        Returns:
            List of answers with source information
        """
        self.logger.info(
            "clarification_requested",
            num_questions=len(questions),
            mode=self.mode.value
        )

        if self.mode == ExecutionMode.CLI:
            return await self._ask_interactive(questions)

        elif self.mode == ExecutionMode.BENCHMARK:
            return self._use_defaults(questions)

        elif self.mode == ExecutionMode.API:
            # In API mode, raise exception with questions
            # Caller should handle and return questions to API client
            raise ClarificationNeededException(questions)

    async def _ask_interactive(
        self,
        questions: List[ClarificationQuestion]
    ) -> List[ClarificationAnswer]:
        """
        Ask questions interactively via CLI.

        Uses click.prompt or similar for user input.
        """
        import click

        answers = []

        click.echo("\nClarification needed to proceed:\n")

        for i, question in enumerate(questions, 1):
            click.echo(f"{i}. {question.question}")

            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                # Display options
                for j, option in enumerate(question.options, 1):
                    click.echo(f"   {j}. {option}")

                # Get selection
                choice = click.prompt(
                    "Select option",
                    type=click.IntRange(1, len(question.options))
                )
                answer_text = question.options[choice - 1]

            elif question.question_type == QuestionType.YES_NO:
                answer_bool = click.confirm(question.question, default=True)
                answer_text = "yes" if answer_bool else "no"

            else:  # TEXT
                answer_text = click.prompt("Answer")

            answers.append(ClarificationAnswer(
                question_key=question.key,
                answer=answer_text,
                source="user"
            ))

            self.logger.info(
                "clarification_answered",
                question=question.key,
                answer=answer_text,
                source="user"
            )

        return answers

    def _use_defaults(
        self,
        questions: List[ClarificationQuestion]
    ) -> List[ClarificationAnswer]:
        """
        Use default answers for benchmark mode.

        If question doesn't have default, use heuristic.
        """
        answers = []

        for question in questions:
            # Use provided default if available
            if question.default:
                answer_text = question.default

            # Otherwise use heuristic defaults
            elif question.question_type == QuestionType.YES_NO:
                answer_text = "yes"  # Default to yes for features

            elif question.question_type == QuestionType.MULTIPLE_CHOICE:
                # Use first option as default
                answer_text = question.options[0] if question.options else ""

            else:
                # For text questions, use generic answer
                answer_text = "default"

            answers.append(ClarificationAnswer(
                question_key=question.key,
                answer=answer_text,
                source="default"
            ))

            self.logger.warning(
                "clarification_defaulted",
                question=question.key,
                answer=answer_text,
                message="Used default answer in benchmark mode"
            )

        return answers

    async def _enhance_prompt_with_clarifications(
        self,
        initial_prompt: str,
        answers: List[ClarificationAnswer]
    ) -> str:
        """
        Enhance initial prompt with clarification answers.

        Combines initial request with answers to create full context.
        """
        enhanced = initial_prompt

        if answers:
            enhanced += "\n\nAdditional Context:\n"
            for answer in answers:
                enhanced += f"- {answer.question_key}: {answer.answer}\n"

        return enhanced
```

### Updated execute_workflow with Clarification

```python
# gao_dev/orchestrator/orchestrator.py (updated)

async def execute_workflow(
    self,
    initial_prompt: str,
    workflow: Optional[Workflow] = None,
    max_clarification_rounds: int = 3
) -> WorkflowResult:
    """
    Execute workflow with clarification support.

    Args:
        initial_prompt: User's initial request
        workflow: Optional pre-selected workflow
        max_clarification_rounds: Max rounds of clarification (prevent loops)

    Returns:
        WorkflowResult
    """
    current_prompt = initial_prompt
    clarification_history = []

    # Clarification loop (max 3 rounds)
    for round_num in range(max_clarification_rounds):

        # Select workflow
        if workflow is None:
            selection = await self.select_workflow_for_prompt(current_prompt)

            # Check if clarification needed
            if selection.workflow is None and selection.clarifying_questions:
                self.logger.info(
                    "clarification_needed",
                    round=round_num + 1,
                    num_questions=len(selection.clarifying_questions)
                )

                # Ask clarifying questions
                answers = await self.ask_clarification(
                    selection.clarifying_questions
                )

                clarification_history.extend(answers)

                # Enhance prompt with answers
                current_prompt = await self._enhance_prompt_with_clarifications(
                    initial_prompt,
                    clarification_history
                )

                # Try again with enhanced prompt
                continue

            elif selection.workflow is None:
                # No workflow and no questions - error
                raise ValueError("Could not select workflow and no clarification questions available")

            workflow = selection.workflow

        # Workflow selected, break clarification loop
        break

    # Execute workflow (existing logic from Story 7.2.2)
    result = await self._execute_workflow_steps(workflow, current_prompt)

    return result
```

---

## Testing Strategy

### Unit Tests (`tests/test_clarification_dialog.py`)

```python
import pytest
from unittest.mock import Mock, patch
from gao_dev.orchestrator import GAODevOrchestrator, ExecutionMode
from gao_dev.orchestrator.workflow_selector import (
    ClarificationQuestion,
    QuestionType
)

@pytest.mark.asyncio
async def test_clarification_benchmark_mode():
    """Test clarification uses defaults in benchmark mode."""
    orchestrator = GAODevOrchestrator(
        mode=ExecutionMode.BENCHMARK
    )

    questions = [
        ClarificationQuestion(
            question="Is this a new project?",
            question_type=QuestionType.YES_NO,
            key="project_type",
            default="yes"
        )
    ]

    answers = await orchestrator.ask_clarification(questions)

    assert len(answers) == 1
    assert answers[0].answer == "yes"
    assert answers[0].source == "default"

@pytest.mark.asyncio
@patch('click.confirm')
async def test_clarification_cli_mode(mock_confirm):
    """Test clarification prompts user in CLI mode."""
    mock_confirm.return_value = True

    orchestrator = GAODevOrchestrator(
        mode=ExecutionMode.CLI
    )

    questions = [
        ClarificationQuestion(
            question="Is this a new project?",
            question_type=QuestionType.YES_NO,
            key="project_type"
        )
    ]

    answers = await orchestrator.ask_clarification(questions)

    assert len(answers) == 1
    assert answers[0].answer == "yes"
    assert answers[0].source == "user"
    mock_confirm.assert_called_once()

@pytest.mark.asyncio
async def test_prompt_enhancement():
    """Test prompt is enhanced with clarification answers."""
    orchestrator = GAODevOrchestrator()

    initial = "Build an app"
    answers = [
        ClarificationAnswer(
            question_key="project_type",
            answer="greenfield",
            source="user"
        )
    ]

    enhanced = await orchestrator._enhance_prompt_with_clarifications(
        initial,
        answers
    )

    assert "Build an app" in enhanced
    assert "project_type: greenfield" in enhanced
```

---

## Dependencies

- **Story 7.2.1**: Workflow Selector must return clarifying_questions
- **Story 7.2.2**: execute_workflow needs clarification loop
- **Click library**: For CLI prompts (already used in project)

---

## Definition of Done

- [ ] ClarificationQuestion and ClarificationAnswer data models created
- [ ] ExecutionMode enum added (CLI, BENCHMARK, API)
- [ ] ask_clarification() method implemented with mode-specific behavior
- [ ] CLI mode prompts user interactively
- [ ] Benchmark mode uses defaults
- [ ] Prompt enhancement with clarification answers
- [ ] execute_workflow updated with clarification loop
- [ ] Structured logging for clarifications
- [ ] Unit tests for both modes (>80% coverage)
- [ ] Type hints complete (mypy passes)
- [ ] Docstrings complete
- [ ] Code review completed
- [ ] Story committed atomically to git

---

## Out of Scope

- Multi-turn conversation (advanced clarification)
- Clarification question generation (AI generates questions) - Story 7.2.1 handles this
- Web UI for clarification (future enhancement)
- Clarification history persistence (future)

---

## Notes

- Keep defaults simple and sensible - prefer "yes" for features, first option for choices
- Clarification loop prevents infinite loops (max 3 rounds)
- Logging is critical for understanding clarification patterns
- This enables GAO-Dev to handle vague prompts gracefully
- In benchmark mode, defaulting is acceptable for automated testing
