"""AI Response Injector for test mode.

Provides scripted AI responses for deterministic testing.

Story: 36.2 - Test Mode Support in ChatREPL
Epic: 36 - Test Infrastructure
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import structlog

logger = structlog.get_logger()


class FixtureExhausted(Exception):
    """Raised when all fixture responses have been consumed."""

    pass


class AIResponseInjector:
    """
    Load and provide scripted AI responses from fixture files.

    Enables deterministic testing by replacing real AI calls with
    pre-scripted responses from YAML fixture files.

    This is a minimal implementation for Story 36.2. The full
    FixtureLoader with validation will be implemented in Story 36.4.

    Attributes:
        fixture_path: Path to YAML fixture file
        responses: List of pre-scripted responses
        current_index: Index of next response to return
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
        self.current_index = 0
        self.logger = logger.bind(
            component="ai_response_injector", fixture=str(fixture_path)
        )

        # Load fixture file
        self.responses = self._load_fixture()

        self.logger.info(
            "injector_initialized", response_count=len(self.responses)
        )

    def _load_fixture(self) -> List[str]:
        """
        Load responses from YAML fixture file.

        Expected format:
        ```yaml
        name: "fixture_name"
        description: "Description"
        scenario:
          - user_input: "hello"
            brian_response: "Hello! How can I help?"
          - user_input: "create a todo app"
            brian_response: "I'll help you create a todo app..."
        ```

        Returns:
            List of Brian responses

        Raises:
            FileNotFoundError: If fixture doesn't exist
            ValueError: If YAML is malformed
        """
        if not self.fixture_path.exists():
            raise FileNotFoundError(
                f"Fixture file not found: {self.fixture_path}"
            )

        try:
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise ValueError("Fixture file is empty")

            if "scenario" not in data:
                raise ValueError(
                    "Fixture must contain 'scenario' key with list of turns"
                )

            scenario = data["scenario"]
            if not isinstance(scenario, list):
                raise ValueError("'scenario' must be a list")

            # Extract Brian responses
            responses = []
            for i, turn in enumerate(scenario):
                if not isinstance(turn, dict):
                    raise ValueError(
                        f"Turn {i} must be a dictionary with 'brian_response'"
                    )

                if "brian_response" not in turn:
                    raise ValueError(f"Turn {i} missing 'brian_response' key")

                responses.append(turn["brian_response"])

            if not responses:
                raise ValueError("Fixture scenario is empty")

            self.logger.info(
                "fixture_loaded",
                name=data.get("name", "unknown"),
                response_count=len(responses),
            )

            return responses

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in fixture file: {e}")

    def get_next_response(self) -> str:
        """
        Get next scripted response from fixture.

        Returns:
            Next Brian response

        Raises:
            FixtureExhausted: If all responses have been consumed
        """
        if self.current_index >= len(self.responses):
            self.logger.error(
                "fixture_exhausted",
                requested_index=self.current_index,
                total_responses=len(self.responses),
            )
            raise FixtureExhausted(
                f"Fixture exhausted: requested index {self.current_index}, "
                f"but only {len(self.responses)} responses available"
            )

        response = self.responses[self.current_index]
        self.current_index += 1

        self.logger.debug(
            "response_injected",
            index=self.current_index - 1,
            response_length=len(response),
        )

        return response

    def has_more_responses(self) -> bool:
        """
        Check if more responses are available.

        Returns:
            True if more responses available, False otherwise
        """
        return self.current_index < len(self.responses)

    def reset(self) -> None:
        """Reset to beginning of fixture."""
        self.current_index = 0
        self.logger.info("injector_reset")

    def get_remaining_count(self) -> int:
        """
        Get number of remaining responses.

        Returns:
            Number of responses not yet consumed
        """
        return len(self.responses) - self.current_index
