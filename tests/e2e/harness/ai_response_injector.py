"""AI Response Injector for test mode.

Provides scripted AI responses for deterministic testing.

Story: 36.2 - Test Mode Support in ChatREPL (Minimal implementation)
Story: 36.4 - Fixture System (Enhanced with FixtureLoader and models)
Epic: 36 - Test Infrastructure
"""

from typing import Optional
from pathlib import Path
import structlog

from .fixture_loader import FixtureLoader
from .models import TestScenario

logger = structlog.get_logger()


class FixtureExhausted(Exception):
    """Raised when all fixture responses have been consumed."""

    pass


class AIResponseInjector:
    """
    Load and provide scripted AI responses from fixture files.

    Enables deterministic testing by replacing real AI calls with
    pre-scripted responses from YAML fixture files.

    Enhanced in Story 36.4 to use FixtureLoader and TestScenario models
    for comprehensive validation and better error messages.

    Attributes:
        fixture_path: Path to YAML fixture file
        scenario: Loaded TestScenario with all steps
        current_step: Index of next step to return
        logger: Structured logger
    """

    def __init__(self, fixture_path: Path):
        """
        Initialize AI response injector.

        Args:
            fixture_path: Path to YAML fixture file

        Raises:
            FileNotFoundError: If fixture file doesn't exist
            ValueError: If fixture file is malformed
        """
        self.fixture_path = fixture_path
        self.current_step = 0
        self.logger = logger.bind(
            component="ai_response_injector", fixture=str(fixture_path)
        )

        # Load fixture using FixtureLoader (Story 36.4)
        self.scenario = FixtureLoader.load(fixture_path)

        self.logger.info(
            "injector_initialized",
            scenario_name=self.scenario.name,
            step_count=self.scenario.step_count(),
        )

    def get_next_response(self) -> str:
        """
        Get next scripted response from fixture.

        Returns:
            Next Brian response from current step

        Raises:
            FixtureExhausted: If all responses have been consumed
            ValueError: If current step missing brian_response
        """
        if self.current_step >= self.scenario.step_count():
            self.logger.error(
                "fixture_exhausted",
                requested_step=self.current_step,
                total_steps=self.scenario.step_count(),
            )
            raise FixtureExhausted(
                f"Fixture exhausted: requested step {self.current_step}, "
                f"but only {self.scenario.step_count()} steps in scenario '{self.scenario.name}'"
            )

        step = self.scenario.get_step(self.current_step)
        self.current_step += 1

        if step.brian_response is None:
            raise ValueError(
                f"Step {self.current_step} in scenario '{self.scenario.name}' "
                f"missing 'brian_response' (required in test mode)"
            )

        self.logger.debug(
            "response_injected",
            step_index=self.current_step - 1,
            response_length=len(step.brian_response),
        )

        return step.brian_response

    def has_more_responses(self) -> bool:
        """
        Check if more responses are available.

        Returns:
            True if more responses available, False otherwise
        """
        return self.current_step < self.scenario.step_count()

    def reset(self) -> None:
        """
        Reset to beginning of fixture.

        Resets current step index to 0, allowing scenario to be replayed.
        """
        self.current_step = 0
        self.logger.info("injector_reset", scenario_name=self.scenario.name)

    def get_remaining_count(self) -> int:
        """
        Get number of remaining responses.

        Returns:
            Number of responses not yet consumed
        """
        return self.scenario.step_count() - self.current_step

    def get_scenario(self) -> TestScenario:
        """
        Get loaded test scenario.

        Returns:
            TestScenario instance
        """
        return self.scenario
