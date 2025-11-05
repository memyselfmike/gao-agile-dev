"""
Tests for schema validator.

Tests JSON Schema validation for agent configs, prompt templates,
and workflow definitions with clear error messages.
"""

import json
import pytest
from pathlib import Path

from gao_dev.core.schema_validator import (
    SchemaValidator,
    ValidationResult,
    SchemaValidationError
)


@pytest.fixture
def schemas_dir(tmp_path):
    """Create temporary schemas directory with test schemas."""
    schemas = tmp_path / "schemas"
    schemas.mkdir()

    # Create minimal agent schema
    agent_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["agent"],
        "properties": {
            "agent": {
                "type": "object",
                "required": ["metadata", "tools"],
                "properties": {
                    "metadata": {
                        "type": "object",
                        "required": ["name", "role"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "role": {"type": "string", "minLength": 1}
                        }
                    },
                    "tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    }
                }
            }
        }
    }

    # Create minimal prompt schema
    prompt_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "description", "user_prompt"],
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "description": {"type": "string", "minLength": 1},
            "user_prompt": {"type": "string", "minLength": 1},
            "variables": {"type": "object"}
        }
    }

    # Write schemas
    with open(schemas / "agent.schema.json", "w") as f:
        json.dump(agent_schema, f)

    with open(schemas / "prompt.schema.json", "w") as f:
        json.dump(prompt_schema, f)

    return schemas


@pytest.fixture
def validator(schemas_dir):
    """Create SchemaValidator instance."""
    return SchemaValidator(schemas_dir)


class TestSchemaValidator:
    """Test SchemaValidator class."""

    def test_init(self, schemas_dir):
        """Test validator initialization."""
        validator = SchemaValidator(schemas_dir)
        assert validator.schemas_dir == schemas_dir
        assert validator._schemas == {}

    def test_init_nonexistent_dir(self, tmp_path):
        """Test initialization with non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        validator = SchemaValidator(nonexistent)
        # Should not raise, just warn
        assert validator.schemas_dir == nonexistent

    def test_list_schemas(self, validator):
        """Test listing available schemas."""
        schemas = validator.list_schemas()
        assert "agent" in schemas
        assert "prompt" in schemas
        assert len(schemas) == 2

    def test_list_schemas_empty_dir(self, tmp_path):
        """Test listing schemas in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        validator = SchemaValidator(empty_dir)
        assert validator.list_schemas() == []

    def test_clear_cache(self, validator):
        """Test clearing schema cache."""
        # Load a schema to populate cache
        validator._load_schema("agent")
        assert "agent" in validator._schemas

        # Clear cache
        validator.clear_cache()
        assert validator._schemas == {}


class TestAgentValidation:
    """Test agent configuration validation."""

    def test_valid_agent_config(self, validator):
        """Test validation of valid agent config."""
        valid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent",
                    "role": "Tester"
                },
                "tools": ["Read", "Write"]
            }
        }

        result = validator.validate(valid_config, "agent")
        assert result.is_valid
        assert len(result.errors) == 0
        assert bool(result) is True

    def test_missing_agent_key(self, validator):
        """Test validation fails when top-level 'agent' key missing."""
        invalid_config = {
            "metadata": {
                "name": "TestAgent",
                "role": "Tester"
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "agent" in result.errors[0].lower()

    def test_missing_required_metadata(self, validator):
        """Test validation fails when required metadata missing."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent"
                    # Missing 'role'
                },
                "tools": ["Read"]
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "role" in result.errors[0]

    def test_missing_tools(self, validator):
        """Test validation fails when tools array missing."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent",
                    "role": "Tester"
                }
                # Missing 'tools'
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        assert "tools" in result.errors[0]

    def test_empty_tools_array(self, validator):
        """Test validation fails when tools array is empty."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent",
                    "role": "Tester"
                },
                "tools": []  # Empty array
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        assert "tools" in result.errors[0] or "minItems" in result.errors[0]

    def test_empty_name(self, validator):
        """Test validation fails when name is empty string."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "",  # Empty string
                    "role": "Tester"
                },
                "tools": ["Read"]
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid

    def test_wrong_type(self, validator):
        """Test validation fails when field has wrong type."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent",
                    "role": "Tester"
                },
                "tools": "Read"  # Should be array, not string
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        assert "type" in result.errors[0].lower() or "array" in result.errors[0].lower()


class TestPromptValidation:
    """Test prompt template validation."""

    def test_valid_prompt(self, validator):
        """Test validation of valid prompt template."""
        valid_prompt = {
            "name": "test-prompt",
            "description": "A test prompt",
            "user_prompt": "Do something with {{variable}}"
        }

        result = validator.validate(valid_prompt, "prompt")
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_prompt_with_variables(self, validator):
        """Test validation with variables."""
        valid_prompt = {
            "name": "test-prompt",
            "description": "A test prompt",
            "user_prompt": "Hello {{name}}",
            "variables": {
                "name": "World"
            }
        }

        result = validator.validate(valid_prompt, "prompt")
        assert result.is_valid

    def test_missing_required_fields(self, validator):
        """Test validation fails when required fields missing."""
        invalid_prompt = {
            "name": "test-prompt"
            # Missing 'description' and 'user_prompt'
        }

        result = validator.validate(invalid_prompt, "prompt")
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_empty_name(self, validator):
        """Test validation fails when name is empty."""
        invalid_prompt = {
            "name": "",  # Empty string
            "description": "A test prompt",
            "user_prompt": "Do something"
        }

        result = validator.validate(invalid_prompt, "prompt")
        assert not result.is_valid


class TestValidationResult:
    """Test ValidationResult class."""

    def test_valid_result(self):
        """Test creating valid result."""
        result = ValidationResult(is_valid=True, errors=[])
        assert result.is_valid
        assert len(result.errors) == 0
        assert bool(result) is True
        assert "VALID" in str(result)

    def test_invalid_result(self):
        """Test creating invalid result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"]
        )
        assert not result.is_valid
        assert len(result.errors) == 2
        assert bool(result) is False
        assert "INVALID" in str(result)

    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Warning 1"]
        )
        assert result.is_valid
        assert len(result.warnings) == 1
        assert "warning" in str(result).lower()


class TestValidateOrRaise:
    """Test validate_or_raise method."""

    def test_validate_or_raise_valid(self, validator):
        """Test validate_or_raise with valid config."""
        valid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent",
                    "role": "Tester"
                },
                "tools": ["Read"]
            }
        }

        # Should not raise
        validator.validate_or_raise(valid_config, "agent")

    def test_validate_or_raise_invalid(self, validator):
        """Test validate_or_raise with invalid config."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent"
                    # Missing 'role'
                },
                "tools": ["Read"]
            }
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate_or_raise(invalid_config, "agent")

        assert "role" in str(exc_info.value)
        assert exc_info.value.result.is_valid is False

    def test_validate_or_raise_with_context(self, validator):
        """Test validate_or_raise includes context in error."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent"
                },
                "tools": ["Read"]
            }
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate_or_raise(
                invalid_config,
                "agent",
                context="test.agent.yaml"
            )

        assert "test.agent.yaml" in str(exc_info.value)


class TestErrorMessages:
    """Test error message formatting."""

    def test_error_message_has_location(self, validator):
        """Test error message includes location path."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent"
                    # Missing 'role'
                },
                "tools": ["Read"]
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        error = result.errors[0]
        assert "metadata" in error or "role" in error

    def test_error_message_has_fix_suggestion(self, validator):
        """Test error message includes fix suggestion."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent"
                },
                "tools": ["Read"]
            }
        }

        result = validator.validate(invalid_config, "agent")
        error = result.errors[0]
        # Should contain a fix suggestion
        assert "Fix:" in error or "Add" in error

    def test_multiple_errors(self, validator):
        """Test multiple validation errors."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": ""  # Empty name
                    # Missing 'role'
                },
                "tools": []  # Empty tools array
            }
        }

        result = validator.validate(invalid_config, "agent")
        assert not result.is_valid
        # Should have multiple errors
        assert len(result.errors) >= 2


class TestSchemaLoading:
    """Test schema loading and caching."""

    def test_load_schema(self, validator):
        """Test loading schema from file."""
        schema = validator._load_schema("agent")
        assert schema is not None
        assert "$schema" in schema
        assert "type" in schema

    def test_load_schema_caches(self, validator):
        """Test schema is cached after first load."""
        schema1 = validator._load_schema("agent")
        schema2 = validator._load_schema("agent")
        # Should return same cached instance
        assert schema1 is schema2

    def test_load_nonexistent_schema(self, validator):
        """Test loading non-existent schema raises error."""
        with pytest.raises(FileNotFoundError) as exc_info:
            validator._load_schema("nonexistent")

        assert "nonexistent" in str(exc_info.value)
        assert "Available schemas" in str(exc_info.value)

    def test_load_invalid_json_schema(self, tmp_path):
        """Test loading invalid JSON schema raises error."""
        schemas = tmp_path / "schemas"
        schemas.mkdir()

        # Write invalid JSON
        with open(schemas / "bad.schema.json", "w") as f:
            f.write("{invalid json")

        validator = SchemaValidator(schemas)

        with pytest.raises(json.JSONDecodeError):
            validator._load_schema("bad")


class TestFixSuggestions:
    """Test fix suggestion generation."""

    def test_fix_suggestion_for_missing_name(self, validator):
        """Test fix suggestion for missing name field."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "role": "Tester"
                    # Missing 'name'
                },
                "tools": ["Read"]
            }
        }

        result = validator.validate(invalid_config, "agent")
        error = result.errors[0]
        assert "name" in error.lower()
        assert "fix:" in error.lower() or "add" in error.lower()

    def test_fix_suggestion_for_empty_array(self, validator):
        """Test fix suggestion for empty tools array."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester"
                },
                "tools": []
            }
        }

        result = validator.validate(invalid_config, "agent")
        error = result.errors[0]
        assert "tools" in error.lower() or "array" in error.lower()

    def test_fix_suggestion_for_type_mismatch(self, validator):
        """Test fix suggestion for type mismatch."""
        invalid_config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester"
                },
                "tools": "Read"  # Should be array
            }
        }

        result = validator.validate(invalid_config, "agent")
        error = result.errors[0]
        assert "type" in error.lower() or "array" in error.lower()


class TestRealSchemas:
    """Test with real GAO-Dev schemas."""

    @pytest.fixture
    def real_schemas_dir(self):
        """Get path to real schemas directory."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "gao_dev" / "schemas"

    def test_real_agent_schema_exists(self, real_schemas_dir):
        """Test real agent schema file exists."""
        if not real_schemas_dir.exists():
            pytest.skip("Real schemas directory not found")

        agent_schema = real_schemas_dir / "agent.schema.json"
        assert agent_schema.exists()

    def test_real_prompt_schema_exists(self, real_schemas_dir):
        """Test real prompt schema file exists."""
        if not real_schemas_dir.exists():
            pytest.skip("Real schemas directory not found")

        prompt_schema = real_schemas_dir / "prompt.schema.json"
        assert prompt_schema.exists()

    def test_real_workflow_schema_exists(self, real_schemas_dir):
        """Test real workflow schema file exists."""
        if not real_schemas_dir.exists():
            pytest.skip("Real schemas directory not found")

        workflow_schema = real_schemas_dir / "workflow.schema.json"
        assert workflow_schema.exists()

    def test_validate_with_real_schemas(self, real_schemas_dir):
        """Test validation with real schemas."""
        if not real_schemas_dir.exists():
            pytest.skip("Real schemas directory not found")

        validator = SchemaValidator(real_schemas_dir)

        valid_config = {
            "agent": {
                "metadata": {
                    "name": "TestAgent",
                    "role": "Tester"
                },
                "persona_file": "./test.md",
                "tools": ["Read", "Write"]
            }
        }

        result = validator.validate(valid_config, "agent")
        assert result.is_valid
