"""
Schema validation for configuration files.

This module provides JSON Schema validation for agent configurations,
prompt templates, and workflow definitions. It offers clear error messages
with actionable fix suggestions.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import structlog

try:
    import jsonschema
    from jsonschema import ValidationError, Draft7Validator
except ImportError:
    raise ImportError(
        "jsonschema library is required for schema validation. "
        "Install it with: pip install jsonschema"
    )

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    """
    Result of schema validation.

    Attributes:
        is_valid: Whether validation passed
        errors: List of error messages (empty if valid)
        warnings: List of warning messages (non-blocking)
    """

    is_valid: bool
    errors: List[str]
    warnings: List[str] = None

    def __post_init__(self):
        """Initialize warnings list if None."""
        if self.warnings is None:
            self.warnings = []

    def __bool__(self) -> bool:
        """Allow boolean evaluation (True if valid)."""
        return self.is_valid

    def __str__(self) -> str:
        """String representation."""
        if self.is_valid:
            status = "VALID"
            if self.warnings:
                status += f" (with {len(self.warnings)} warnings)"
            return status
        return f"INVALID: {len(self.errors)} errors"


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""

    def __init__(self, result: ValidationResult):
        """
        Initialize with validation result.

        Args:
            result: ValidationResult containing error details
        """
        self.result = result
        error_summary = "\n".join(result.errors)
        super().__init__(f"Schema validation failed:\n{error_summary}")


class SchemaValidator:
    """
    JSON Schema validator for GAO-Dev configurations.

    Provides validation for:
    - Agent configurations (agent.schema.json)
    - Prompt templates (prompt.schema.json)
    - Workflow definitions (workflow.schema.json)

    Features:
    - Clear, actionable error messages
    - Fix suggestions for common mistakes
    - Schema caching for performance
    - Detailed error context (path, expected format)

    Example:
        ```python
        validator = SchemaValidator(Path("gao_dev/schemas"))

        # Validate agent config
        result = validator.validate(agent_data, "agent")
        if not result.is_valid:
            for error in result.errors:
                print(error)

        # Validate and raise on error
        validator.validate_or_raise(prompt_data, "prompt")
        ```
    """

    def __init__(self, schemas_dir: Path):
        """
        Initialize schema validator.

        Args:
            schemas_dir: Directory containing JSON Schema files
        """
        self.schemas_dir = Path(schemas_dir)
        self._schemas: Dict[str, Dict[str, Any]] = {}

        if not self.schemas_dir.exists():
            logger.warning(
                "schemas_directory_not_found",
                schemas_dir=str(self.schemas_dir)
            )

    def validate(
        self,
        data: Dict[str, Any],
        schema_name: str,
        context: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate data against a schema.

        Args:
            data: Data to validate
            schema_name: Schema name (e.g., "agent", "prompt", "workflow")
            context: Optional context for error messages (e.g., file path)

        Returns:
            ValidationResult with validation status and error messages

        Example:
            ```python
            result = validator.validate(config, "agent", "amelia.agent.yaml")
            if not result:
                print(f"Validation failed: {result.errors}")
            ```
        """
        try:
            schema = self._load_schema(schema_name)
        except FileNotFoundError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema not found: {e}"]
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid schema JSON: {e}"]
            )

        # Validate using jsonschema
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))

        if not errors:
            logger.debug(
                "validation_passed",
                schema_name=schema_name,
                context=context
            )
            return ValidationResult(is_valid=True, errors=[])

        # Format error messages
        formatted_errors = []
        for error in errors:
            formatted_error = self._format_error(error, schema_name, context)
            formatted_errors.append(formatted_error)

        logger.warning(
            "validation_failed",
            schema_name=schema_name,
            context=context,
            error_count=len(formatted_errors)
        )

        return ValidationResult(is_valid=False, errors=formatted_errors)

    def validate_or_raise(
        self,
        data: Dict[str, Any],
        schema_name: str,
        context: Optional[str] = None
    ) -> None:
        """
        Validate data and raise SchemaValidationError if invalid.

        Args:
            data: Data to validate
            schema_name: Schema name
            context: Optional context for error messages

        Raises:
            SchemaValidationError: If validation fails

        Example:
            ```python
            try:
                validator.validate_or_raise(config, "agent", "amelia.agent.yaml")
            except SchemaValidationError as e:
                print(f"Validation failed: {e}")
            ```
        """
        result = self.validate(data, schema_name, context)
        if not result.is_valid:
            raise SchemaValidationError(result)

    def _load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load JSON Schema from file.

        Args:
            schema_name: Schema name (e.g., "agent", "prompt", "workflow")

        Returns:
            Loaded schema dictionary

        Raises:
            FileNotFoundError: If schema file not found
            json.JSONDecodeError: If schema JSON is invalid
        """
        # Check cache first
        if schema_name in self._schemas:
            return self._schemas[schema_name]

        # Load schema file
        schema_path = self.schemas_dir / f"{schema_name}.schema.json"

        if not schema_path.exists():
            available = list(self.schemas_dir.glob("*.schema.json"))
            available_names = [s.name.replace(".schema.json", "") for s in available]
            raise FileNotFoundError(
                f"Schema file not found: {schema_path}. "
                f"Available schemas: {', '.join(available_names)}"
            )

        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in schema file {schema_path}: {e.msg}",
                e.doc,
                e.pos
            )

        # Cache schema
        self._schemas[schema_name] = schema

        logger.debug(
            "schema_loaded",
            schema_name=schema_name,
            path=str(schema_path)
        )

        return schema

    def _format_error(
        self,
        error: ValidationError,
        schema_name: str,
        context: Optional[str]
    ) -> str:
        """
        Format validation error with clear message and fix suggestions.

        Args:
            error: jsonschema ValidationError
            schema_name: Schema name for context
            context: Optional additional context

        Returns:
            Formatted error message with fix suggestions
        """
        # Build location path
        if error.path:
            location = " -> ".join(str(p) for p in error.path)
        else:
            location = "(root)"

        # Get error type and message
        error_type = error.validator
        error_msg = error.message

        # Build context prefix
        context_prefix = f"[{context}] " if context else ""

        # Get fix suggestion
        fix_suggestion = self._get_fix_suggestion(error, schema_name)

        # Format complete error message
        formatted = f"""
{context_prefix}Validation Error in '{schema_name}' schema:
  Location: {location}
  Error: {error_msg}
  Problem: {error_type} constraint violated
"""

        if fix_suggestion:
            formatted += f"  Fix: {fix_suggestion}\n"

        return formatted.strip()

    def _get_fix_suggestion(
        self,
        error: ValidationError,
        schema_name: str
    ) -> Optional[str]:
        """
        Generate fix suggestion based on error type and schema.

        Args:
            error: ValidationError from jsonschema
            schema_name: Schema name for context-specific suggestions

        Returns:
            Fix suggestion string or None
        """
        error_type = error.validator

        # Required field missing
        if error_type == "required":
            missing_field = error.message.split("'")[1]
            if schema_name == "agent":
                if missing_field == "name":
                    return "Add 'name' field under agent.metadata (e.g., name: Amelia)"
                elif missing_field == "role":
                    return "Add 'role' field under agent.metadata (e.g., role: Software Developer)"
                elif missing_field == "tools":
                    return "Add 'tools' array with at least one tool (e.g., tools: [Read, Write])"
                elif missing_field in ["persona_file", "persona"]:
                    return "Add either 'persona_file' (e.g., ./amelia.md) or inline 'persona' text"
            elif schema_name == "prompt":
                if missing_field == "name":
                    return "Add 'name' field (e.g., name: prd)"
                elif missing_field == "description":
                    return "Add 'description' field explaining the prompt's purpose"
                elif missing_field == "user_prompt":
                    return "Add 'user_prompt' field with the prompt text"
            elif schema_name == "workflow":
                if missing_field == "name":
                    return "Add 'name' field in kebab-case (e.g., name: dev-story)"
                elif missing_field == "description":
                    return "Add 'description' field explaining the workflow"
                elif missing_field == "phase":
                    return "Add 'phase' field (1=Analysis, 2=Planning, 3=Solutioning, 4=Implementation)"

        # Type mismatch
        elif error_type == "type":
            expected_type = error.schema.get("type", "unknown")
            field_path = " -> ".join(str(p) for p in error.path) if error.path else "value"
            return f"Ensure '{field_path}' is a {expected_type}"

        # Minimum items (e.g., tools array)
        elif error_type == "minItems":
            min_items = error.schema.get("minItems", 1)
            return f"Array must have at least {min_items} item(s)"

        # Minimum length (e.g., non-empty string)
        elif error_type == "minLength":
            return "String cannot be empty"

        # Pattern mismatch (e.g., version, workflow name)
        elif error_type == "pattern":
            pattern = error.schema.get("pattern", "")
            if "^[a-z0-9-]+$" in pattern:
                return "Use lowercase letters, numbers, and hyphens only (kebab-case)"
            elif r"^\d+\.\d+\.\d+$" in pattern:
                return "Use semantic versioning format (e.g., 1.0.0)"

        # Enum mismatch
        elif error_type == "enum":
            allowed = error.schema.get("enum", [])
            return f"Must be one of: {', '.join(str(v) for v in allowed)}"

        # Additional properties not allowed
        elif error_type == "additionalProperties":
            return "Remove unexpected properties or check for typos in field names"

        # oneOf validation (e.g., persona_file or persona)
        elif error_type == "oneOf":
            if schema_name == "agent":
                return "Must have exactly one of: 'persona_file' or 'persona' (not both, not neither)"

        return None

    def list_schemas(self) -> List[str]:
        """
        List available schemas.

        Returns:
            List of schema names (without .schema.json extension)
        """
        if not self.schemas_dir.exists():
            return []

        schema_files = list(self.schemas_dir.glob("*.schema.json"))
        return sorted([s.name.replace(".schema.json", "") for s in schema_files])

    def clear_cache(self) -> None:
        """Clear cached schemas."""
        self._schemas.clear()
        logger.debug("schema_cache_cleared")
