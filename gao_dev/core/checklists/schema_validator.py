"""
Checklist schema validator for GAO-Dev.

Validates checklist YAML files against the JSON Schema specification,
ensuring consistency and data integrity across all checklists.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jsonschema
import yaml


class ChecklistSchemaValidator:
    """Validates checklist YAML files against JSON Schema."""

    def __init__(self, schema_path: Path):
        """
        Initialize validator with schema file.

        Args:
            schema_path: Path to JSON Schema file

        Raises:
            FileNotFoundError: If schema file does not exist
            json.JSONDecodeError: If schema file is not valid JSON

        Example:
            >>> schema_path = Path("gao_dev/config/schemas/checklist_schema.json")
            >>> validator = ChecklistSchemaValidator(schema_path)
        """
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
        self.validator = jsonschema.Draft7Validator(self.schema)

    def validate(self, checklist_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate checklist data against schema.

        Args:
            checklist_data: Parsed checklist dictionary

        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: True if checklist is valid, False otherwise
            - error_messages: List of validation error messages (empty if valid)

        Example:
            >>> validator = ChecklistSchemaValidator(schema_path)
            >>> checklist_data = {"checklist": {"name": "Test", ...}}
            >>> is_valid, errors = validator.validate(checklist_data)
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"Validation error: {error}")
        """
        errors = []
        for error in self.validator.iter_errors(checklist_data):
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return (len(errors) == 0, errors)

    def validate_file(self, checklist_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate checklist YAML file.

        Args:
            checklist_path: Path to checklist YAML file

        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: True if checklist is valid, False otherwise
            - error_messages: List of validation error messages (empty if valid)

        Example:
            >>> validator = ChecklistSchemaValidator(schema_path)
            >>> checklist_path = Path("gao_dev/config/checklists/testing/unit-test-standards.yaml")
            >>> is_valid, errors = validator.validate_file(checklist_path)
            >>> if is_valid:
            ...     print("Checklist is valid!")
        """
        try:
            with open(checklist_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return self.validate(data)
        except yaml.YAMLError as e:
            return (False, [f"YAML parsing error: {e}"])
        except FileNotFoundError:
            return (False, [f"File not found: {checklist_path}"])
        except Exception as e:
            return (False, [f"Unexpected error: {e}"])

    def validate_directory(
        self, checklists_dir: Path
    ) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all checklist files in directory.

        Recursively searches for all .yaml files in the directory
        and validates each one against the schema.

        Args:
            checklists_dir: Directory containing checklist YAML files

        Returns:
            Dict mapping file path to (is_valid, errors) tuple

        Example:
            >>> validator = ChecklistSchemaValidator(schema_path)
            >>> checklists_dir = Path("gao_dev/config/checklists")
            >>> results = validator.validate_directory(checklists_dir)
            >>> for file_path, (is_valid, errors) in results.items():
            ...     if not is_valid:
            ...         print(f"{file_path}: {errors}")
        """
        results = {}
        for checklist_file in checklists_dir.rglob("*.yaml"):
            results[str(checklist_file)] = self.validate_file(checklist_file)
        return results
