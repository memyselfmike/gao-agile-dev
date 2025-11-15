"""Data models for E2E test fixtures.

Story: 36.4 - Fixture System
Epic: 36 - Test Infrastructure

Defines data classes for test scenarios and steps loaded from YAML fixtures.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TestStep:
    """
    Single step in a test scenario.

    Represents one user input and expected output pair, with optional
    Brian response for test mode.

    Attributes:
        user_input: Text user types in this step
        expect_output: List of regex patterns to match in output
        brian_response: Brian's scripted response (for test mode)
        timeout_ms: Timeout in milliseconds (default: 5000)

    Example:
        >>> step = TestStep(
        ...     user_input="hello",
        ...     expect_output=["Hello", "Brian"],
        ...     brian_response="Hello! I'm Brian.",
        ...     timeout_ms=5000
        ... )
    """

    user_input: str
    expect_output: List[str] = field(default_factory=list)
    brian_response: Optional[str] = None
    timeout_ms: int = 5000

    def __post_init__(self) -> None:
        """Validate step after initialization."""
        if not isinstance(self.user_input, str):
            raise ValueError("user_input must be a string")

        if not isinstance(self.expect_output, list):
            raise ValueError("expect_output must be a list")

        if self.brian_response is not None and not isinstance(
            self.brian_response, str
        ):
            raise ValueError("brian_response must be a string or None")

        if not isinstance(self.timeout_ms, int) or self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")


@dataclass
class TestScenario:
    """
    Test scenario loaded from YAML fixture.

    Represents a complete test scenario with metadata and steps.

    Attributes:
        name: Scenario name (unique identifier)
        description: Human-readable description
        steps: List of test steps to execute

    Example:
        >>> scenario = TestScenario(
        ...     name="simple_test",
        ...     description="Test simple conversation",
        ...     steps=[
        ...         TestStep(user_input="hello", brian_response="Hello!")
        ...     ]
        ... )
    """

    name: str
    description: str
    steps: List[TestStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate scenario after initialization."""
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name must be a non-empty string")

        if not isinstance(self.description, str):
            raise ValueError("description must be a string")

        if not isinstance(self.steps, list):
            raise ValueError("steps must be a list")

        if len(self.steps) == 0:
            raise ValueError("steps cannot be empty")

        # Validate all steps
        for i, step in enumerate(self.steps):
            if not isinstance(step, TestStep):
                raise ValueError(
                    f"Step {i} must be a TestStep instance, got {type(step)}"
                )

    def get_step(self, index: int) -> TestStep:
        """
        Get step by index.

        Args:
            index: Step index (0-based)

        Returns:
            TestStep at index

        Raises:
            IndexError: If index out of range
        """
        if index < 0 or index >= len(self.steps):
            raise IndexError(
                f"Step index {index} out of range (0-{len(self.steps)-1})"
            )
        return self.steps[index]

    def step_count(self) -> int:
        """
        Get number of steps in scenario.

        Returns:
            Number of steps
        """
        return len(self.steps)
