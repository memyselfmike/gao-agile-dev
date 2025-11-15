"""Fixture loader for E2E test scenarios.

Story: 36.4 - Fixture System
Epic: 36 - Test Infrastructure

Loads and validates YAML test fixtures with comprehensive error messages.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List
import structlog

from .models import TestScenario, TestStep

logger = structlog.get_logger()


class FixtureLoader:
    """
    Load and validate YAML test fixtures.

    Provides schema validation with helpful error messages and parses
    YAML files into TestScenario data models.

    Example:
        >>> loader = FixtureLoader()
        >>> scenario = loader.load(Path("tests/e2e/fixtures/test.yaml"))
        >>> assert scenario.name == "test_scenario"
    """

    # Maximum file size (10MB) to prevent memory exhaustion
    MAX_FILE_SIZE = 10 * 1024 * 1024

    @staticmethod
    def load(fixture_path: Path) -> TestScenario:
        """
        Load fixture from YAML file.

        Args:
            fixture_path: Path to YAML fixture file

        Returns:
            TestScenario with validated steps

        Raises:
            FileNotFoundError: If fixture file doesn't exist
            ValueError: If fixture schema invalid
            yaml.YAMLError: If YAML syntax error

        Example:
            >>> scenario = FixtureLoader.load(Path("test.yaml"))
        """
        if not fixture_path.exists():
            raise FileNotFoundError(
                f"Fixture not found: {fixture_path}\n"
                f"Please ensure the fixture file exists at the specified path."
            )

        # Check file size
        file_size = fixture_path.stat().st_size
        if file_size > FixtureLoader.MAX_FILE_SIZE:
            raise ValueError(
                f"Fixture file too large: {file_size} bytes "
                f"(max: {FixtureLoader.MAX_FILE_SIZE} bytes)\n"
                f"Large fixtures may indicate a configuration error."
            )

        logger.info(
            "loading_fixture",
            path=str(fixture_path),
            size_bytes=file_size,
        )

        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Invalid YAML syntax in {fixture_path.name}:\n{e}\n\n"
                f"Please check the YAML syntax. Common issues:\n"
                f"- Incorrect indentation (use spaces, not tabs)\n"
                f"- Missing colons after keys\n"
                f"- Unmatched quotes or brackets"
            ) from e
        except UnicodeDecodeError as e:
            raise ValueError(
                f"File encoding error in {fixture_path.name}: {e}\n"
                f"Please ensure the file is UTF-8 encoded."
            ) from e

        if data is None:
            raise ValueError(
                f"Fixture {fixture_path.name} is empty\n"
                f"Expected YAML file with 'name', 'description', and 'scenario' keys."
            )

        # Validate schema
        FixtureLoader._validate_schema(data, fixture_path)

        # Parse into TestScenario
        steps = []
        for i, step_data in enumerate(data["scenario"]):
            try:
                step = TestStep(
                    user_input=step_data["user_input"],
                    expect_output=step_data.get("expect_output", []),
                    brian_response=step_data.get("brian_response"),
                    timeout_ms=step_data.get("timeout_ms", 5000),
                )
                steps.append(step)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Error creating TestStep from scenario step {i+1}: {e}"
                ) from e

        scenario = TestScenario(
            name=data["name"],
            description=data["description"],
            steps=steps,
        )

        logger.info(
            "fixture_loaded",
            name=scenario.name,
            step_count=len(steps),
        )

        return scenario

    @staticmethod
    def _validate_schema(data: Any, fixture_path: Path) -> None:
        """
        Validate fixture schema.

        Performs comprehensive validation with helpful error messages.

        Args:
            data: Parsed YAML data
            fixture_path: Path to fixture (for error messages)

        Raises:
            ValueError: If schema invalid with specific guidance

        Example:
            >>> FixtureLoader._validate_schema(data, Path("test.yaml"))
        """
        fixture_name = fixture_path.name

        # Check data is dict
        if not isinstance(data, dict):
            raise ValueError(
                f"Fixture {fixture_name} must be a YAML dictionary, got {type(data).__name__}\n"
                f"Expected format:\n"
                f"  name: 'test_name'\n"
                f"  description: 'Description'\n"
                f"  scenario:\n"
                f"    - user_input: 'Input'"
            )

        # Check required top-level keys
        required_keys = ["name", "description", "scenario"]
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            raise ValueError(
                f"Fixture {fixture_name} missing required keys: {missing_keys}\n"
                f"Required keys: {required_keys}\n"
                f"Found keys: {list(data.keys())}\n\n"
                f"Expected format:\n"
                f"  name: 'test_name'\n"
                f"  description: 'Test description'\n"
                f"  scenario:\n"
                f"    - user_input: 'Input'\n"
                f"      brian_response: 'Response'"
            )

        # Validate name
        if not isinstance(data["name"], str) or not data["name"]:
            raise ValueError(
                f"Fixture {fixture_name}: 'name' must be a non-empty string\n"
                f"Got: {data.get('name')!r}"
            )

        # Validate description
        if not isinstance(data["description"], str):
            raise ValueError(
                f"Fixture {fixture_name}: 'description' must be a string\n"
                f"Got: {data.get('description')!r}"
            )

        # Validate scenario is list
        if not isinstance(data["scenario"], list):
            raise ValueError(
                f"Fixture {fixture_name}: 'scenario' must be a list of steps\n"
                f"Got: {type(data['scenario']).__name__}\n\n"
                f"Expected format:\n"
                f"  scenario:\n"
                f"    - user_input: 'First input'\n"
                f"      brian_response: 'First response'\n"
                f"    - user_input: 'Second input'\n"
                f"      brian_response: 'Second response'"
            )

        if len(data["scenario"]) == 0:
            raise ValueError(
                f"Fixture {fixture_name}: 'scenario' cannot be empty\n"
                f"Add at least one step with 'user_input' and 'brian_response'"
            )

        # Validate each step
        for i, step in enumerate(data["scenario"]):
            step_num = i + 1

            if not isinstance(step, dict):
                raise ValueError(
                    f"Fixture {fixture_name}: Step {step_num} must be a dictionary\n"
                    f"Got: {type(step).__name__}\n\n"
                    f"Expected format:\n"
                    f"  - user_input: 'Input text'\n"
                    f"    brian_response: 'Response text'\n"
                    f"    expect_output: ['pattern1', 'pattern2']\n"
                    f"    timeout_ms: 5000"
                )

            # Check user_input
            if "user_input" not in step:
                raise ValueError(
                    f"Fixture {fixture_name}: Step {step_num} missing 'user_input'\n"
                    f"Found keys: {list(step.keys())}\n"
                    f"Required: 'user_input'\n"
                    f"Optional: 'brian_response', 'expect_output', 'timeout_ms'"
                )

            if not isinstance(step["user_input"], str):
                raise ValueError(
                    f"Fixture {fixture_name}: Step {step_num} 'user_input' must be a string\n"
                    f"Got: {type(step['user_input']).__name__}"
                )

            # Validate expect_output if present
            if "expect_output" in step:
                if not isinstance(step["expect_output"], list):
                    raise ValueError(
                        f"Fixture {fixture_name}: Step {step_num} 'expect_output' must be a list\n"
                        f"Got: {type(step['expect_output']).__name__}\n\n"
                        f"Expected format:\n"
                        f"  expect_output:\n"
                        f"    - 'regex pattern 1'\n"
                        f"    - 'regex pattern 2'"
                    )

                # Validate each pattern is a string
                for j, pattern in enumerate(step["expect_output"]):
                    if not isinstance(pattern, str):
                        raise ValueError(
                            f"Fixture {fixture_name}: Step {step_num} expect_output[{j}] must be a string\n"
                            f"Got: {type(pattern).__name__}"
                        )

            # Validate brian_response if present
            if "brian_response" in step and step["brian_response"] is not None:
                if not isinstance(step["brian_response"], str):
                    raise ValueError(
                        f"Fixture {fixture_name}: Step {step_num} 'brian_response' must be a string\n"
                        f"Got: {type(step['brian_response']).__name__}"
                    )

            # Validate timeout_ms if present
            if "timeout_ms" in step:
                if not isinstance(step["timeout_ms"], int) or step["timeout_ms"] <= 0:
                    raise ValueError(
                        f"Fixture {fixture_name}: Step {step_num} 'timeout_ms' must be a positive integer\n"
                        f"Got: {step['timeout_ms']!r}"
                    )

        logger.debug("schema_validated", fixture=fixture_name, steps=len(data["scenario"]))
