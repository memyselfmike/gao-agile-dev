"""
Integration tests for AgentConfigLoader with schema validation.

Tests that agent configurations are properly validated when loaded.
"""

import pytest
from pathlib import Path

from gao_dev.core.agent_config_loader import AgentConfigLoader
from gao_dev.core.schema_validator import SchemaValidator


@pytest.fixture
def test_agents_dir(tmp_path):
    """Create temporary agents directory with test configs."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Create valid agent config
    valid_agent = """agent:
  metadata:
    name: TestAgent
    role: Software Developer
    version: 1.0.0

  persona_file: ./test.md

  tools:
    - Read
    - Write

  capabilities:
    - implementation

  model: claude-sonnet-4-5-20250929
"""
    (agents_dir / "test.agent.yaml").write_text(valid_agent)

    # Create persona file
    (agents_dir / "test.md").write_text("# TestAgent\n\nTest persona")

    # Create invalid agent config (missing required fields)
    invalid_agent = """agent:
  metadata:
    name: InvalidAgent
    # Missing 'role'

  persona_file: ./invalid.md

  # Missing 'tools'
"""
    (agents_dir / "invalid.agent.yaml").write_text(invalid_agent)
    (agents_dir / "invalid.md").write_text("# Invalid\n\nInvalid persona")

    return agents_dir


@pytest.fixture
def real_schemas_dir():
    """Get path to real schemas directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "gao_dev" / "schemas"


@pytest.fixture
def validator(real_schemas_dir):
    """Create validator with real schemas."""
    if not real_schemas_dir.exists():
        pytest.skip("Real schemas directory not found")
    return SchemaValidator(real_schemas_dir)


class TestAgentConfigLoaderValidation:
    """Test AgentConfigLoader with schema validation."""

    def test_load_agent_without_validator(self, test_agents_dir):
        """Test loading agent without validator (no validation)."""
        loader = AgentConfigLoader(test_agents_dir)
        # Should load successfully (no validation)
        config = loader.load_agent("test")
        assert config.name == "TestAgent"

    def test_load_valid_agent_with_validator(self, test_agents_dir, validator):
        """Test loading valid agent with validator."""
        loader = AgentConfigLoader(test_agents_dir, validator=validator)
        config = loader.load_agent("test")
        assert config.name == "TestAgent"
        assert config.role == "Software Developer"

    def test_load_invalid_agent_with_validator(self, test_agents_dir, validator):
        """Test loading invalid agent with validator raises error."""
        loader = AgentConfigLoader(test_agents_dir, validator=validator)

        with pytest.raises(ValueError) as exc_info:
            loader.load_agent("invalid")

        error_msg = str(exc_info.value)
        assert "validation failed" in error_msg.lower()
        # Should mention what's wrong
        assert "role" in error_msg.lower() or "tools" in error_msg.lower()

    def test_validation_error_includes_context(self, test_agents_dir, validator):
        """Test validation error includes file context."""
        loader = AgentConfigLoader(test_agents_dir, validator=validator)

        with pytest.raises(ValueError) as exc_info:
            loader.load_agent("invalid")

        error_msg = str(exc_info.value)
        assert "invalid.agent.yaml" in error_msg

    def test_validation_error_is_clear(self, test_agents_dir, validator):
        """Test validation error message is clear and actionable."""
        loader = AgentConfigLoader(test_agents_dir, validator=validator)

        with pytest.raises(ValueError) as exc_info:
            loader.load_agent("invalid")

        error_msg = str(exc_info.value)
        # Should have clear structure
        assert "Error" in error_msg or "error" in error_msg
        # Should mention location
        assert "Location:" in error_msg or "metadata" in error_msg.lower()


class TestRealAgentConfigs:
    """Test validation of real agent configs."""

    @pytest.fixture
    def real_agents_dir(self):
        """Get path to real agents directory."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "gao_dev" / "agents"

    def test_amelia_config_valid(self, real_agents_dir, validator):
        """Test Amelia's config validates successfully."""
        if not real_agents_dir.exists():
            pytest.skip("Real agents directory not found")

        loader = AgentConfigLoader(real_agents_dir, validator=validator)
        config = loader.load_agent("amelia")
        assert config.name == "Amelia"
        assert config.role == "Software Developer"

    def test_all_real_agents_validate(self, real_agents_dir, validator):
        """Test all real agent configs validate successfully."""
        if not real_agents_dir.exists():
            pytest.skip("Real agents directory not found")

        loader = AgentConfigLoader(real_agents_dir, validator=validator)
        agent_names = loader.discover_agents()

        if not agent_names:
            pytest.skip("No agents found")

        # All agents should load without validation errors
        for agent_name in agent_names:
            config = loader.load_agent(agent_name)
            assert config.name is not None
            assert config.role is not None
            assert len(config.tools) > 0


class TestValidatorIntegration:
    """Test validator integration patterns."""

    def test_loader_with_validator_none(self, test_agents_dir):
        """Test loader works with validator=None."""
        loader = AgentConfigLoader(test_agents_dir, validator=None)
        config = loader.load_agent("test")
        assert config.name == "TestAgent"

    def test_validator_optional_parameter(self, test_agents_dir, validator):
        """Test validator is truly optional."""
        # Without validator
        loader1 = AgentConfigLoader(test_agents_dir)
        config1 = loader1.load_agent("test")

        # With validator
        loader2 = AgentConfigLoader(test_agents_dir, validator=validator)
        config2 = loader2.load_agent("test")

        # Both should succeed for valid config
        assert config1.name == config2.name

    def test_load_all_agents_with_validator(self, test_agents_dir, validator):
        """Test load_all_agents with validator."""
        loader = AgentConfigLoader(test_agents_dir, validator=validator)

        # Should fail because 'invalid' agent doesn't validate
        with pytest.raises(ValueError):
            loader.load_all_agents()

    def test_validate_agent_file_method(self, test_agents_dir, validator):
        """Test validate_agent_file method with validator."""
        loader = AgentConfigLoader(test_agents_dir, validator=validator)

        # Valid agent should validate
        assert loader.validate_agent_file("test") is True

        # Invalid agent should not validate
        assert loader.validate_agent_file("invalid") is False
