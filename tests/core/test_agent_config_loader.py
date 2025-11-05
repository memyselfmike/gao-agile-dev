"""
Unit tests for AgentConfigLoader.

Tests the loading of agent configurations from YAML files,
including error handling, validation, and discovery.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
import copy

from gao_dev.core.agent_config_loader import AgentConfigLoader
from gao_dev.core.models.agent_config import AgentConfig


@pytest.fixture
def temp_agents_dir(tmp_path):
    """Create a temporary agents directory with test files."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    return agents_dir


@pytest.fixture
def sample_agent_yaml():
    """Sample agent YAML configuration."""
    return {
        "agent": {
            "metadata": {
                "name": "TestAgent",
                "role": "Test Role",
                "icon": "🧪",
                "version": "1.0.0",
            },
            "persona_file": "./testagent.md",
            "tools": ["Read", "Write", "Edit"],
            "capabilities": ["testing", "implementation"],
            "model": "claude-sonnet-4-5-20250929",
            "workflows": ["test-workflow"],
        }
    }


@pytest.fixture
def sample_persona():
    """Sample persona text."""
    return "# TestAgent\n\nYou are a test agent for testing purposes."


@pytest.fixture
def create_agent_files(temp_agents_dir, sample_agent_yaml, sample_persona):
    """Helper to create agent YAML and persona files."""
    def _create(agent_name: str, yaml_data=None, persona_text=None):
        if yaml_data is None:
            yaml_data = copy.deepcopy(sample_agent_yaml)
        if persona_text is None:
            persona_text = sample_persona

        # Update persona_file reference to match agent name
        if "agent" in yaml_data and "persona_file" in yaml_data["agent"]:
            yaml_data["agent"]["persona_file"] = f"./{agent_name}.md"

        # Write YAML file
        yaml_path = temp_agents_dir / f"{agent_name}.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f)

        # Write persona file
        persona_path = temp_agents_dir / f"{agent_name}.md"
        persona_path.write_text(persona_text, encoding="utf-8")

        return yaml_path, persona_path

    return _create


class TestAgentConfigLoaderInit:
    """Tests for AgentConfigLoader initialization."""

    def test_init_with_valid_directory(self, temp_agents_dir):
        """Test initialization with valid directory."""
        loader = AgentConfigLoader(temp_agents_dir)
        assert loader.agents_dir == temp_agents_dir

    def test_init_with_nonexistent_directory(self):
        """Test initialization with non-existent directory logs warning."""
        loader = AgentConfigLoader(Path("/nonexistent/directory"))
        assert loader.agents_dir == Path("/nonexistent/directory")
        # Should not raise exception, just log warning


class TestLoadAgent:
    """Tests for loading individual agents."""

    def test_load_agent_success(self, temp_agents_dir, create_agent_files):
        """Test successfully loading an agent."""
        create_agent_files("testagent")

        loader = AgentConfigLoader(temp_agents_dir)
        config = loader.load_agent("testagent")

        assert isinstance(config, AgentConfig)
        assert config.name == "TestAgent"
        assert config.role == "Test Role"
        assert config.icon == "🧪"
        assert config.version == "1.0.0"
        assert config.tools == ["Read", "Write", "Edit"]
        assert config.capabilities == ["testing", "implementation"]
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.workflows == ["test-workflow"]
        assert config.persona == "# TestAgent\n\nYou are a test agent for testing purposes."

    def test_load_agent_file_not_found(self, temp_agents_dir):
        """Test loading non-existent agent raises FileNotFoundError."""
        loader = AgentConfigLoader(temp_agents_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_agent("nonexistent")

        assert "Agent config not found" in str(exc_info.value)
        assert "nonexistent.agent.yaml" in str(exc_info.value)

    def test_load_agent_invalid_yaml(self, temp_agents_dir):
        """Test loading agent with invalid YAML raises ValueError."""
        # Create invalid YAML file
        yaml_path = temp_agents_dir / "invalid.agent.yaml"
        yaml_path.write_text("invalid: yaml: content: [[[", encoding="utf-8")

        loader = AgentConfigLoader(temp_agents_dir)

        with pytest.raises(ValueError) as exc_info:
            loader.load_agent("invalid")

        assert "Failed to parse YAML" in str(exc_info.value)

    def test_load_agent_missing_agent_key(self, temp_agents_dir):
        """Test loading agent with missing 'agent' key raises ValueError."""
        # Create YAML without 'agent' key
        yaml_path = temp_agents_dir / "missing.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump({"wrong_key": {"name": "Test"}}, f)

        loader = AgentConfigLoader(temp_agents_dir)

        with pytest.raises(ValueError) as exc_info:
            loader.load_agent("missing")

        assert "Invalid agent YAML structure" in str(exc_info.value)

    def test_load_agent_missing_metadata(self, temp_agents_dir):
        """Test loading agent with missing metadata raises ValueError."""
        yaml_data = {
            "agent": {
                "tools": ["Read"],
                "capabilities": ["testing"],
            }
        }
        yaml_path = temp_agents_dir / "nometa.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f)

        loader = AgentConfigLoader(temp_agents_dir)

        with pytest.raises(ValueError) as exc_info:
            loader.load_agent("nometa")

        # Error occurs during persona loading or metadata parsing
        assert "metadata" in str(exc_info.value).lower() or "persona" in str(exc_info.value).lower()

    def test_load_agent_persona_file_not_found(self, temp_agents_dir, sample_agent_yaml):
        """Test loading agent when persona file doesn't exist."""
        # Create YAML without persona file
        yaml_path = temp_agents_dir / "nopersona.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_agent_yaml, f)
        # Don't create persona file

        loader = AgentConfigLoader(temp_agents_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_agent("nopersona")

        assert "Persona file not found" in str(exc_info.value)

    def test_load_agent_with_inline_persona(self, temp_agents_dir):
        """Test loading agent with inline persona instead of file."""
        yaml_data = {
            "agent": {
                "metadata": {
                    "name": "InlineAgent",
                    "role": "Inline Role",
                },
                "persona": "This is an inline persona.",
                "tools": ["Read"],
                "capabilities": ["testing"],
                "model": "claude-sonnet-4-5-20250929",
            }
        }
        yaml_path = temp_agents_dir / "inline.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f)

        loader = AgentConfigLoader(temp_agents_dir)
        config = loader.load_agent("inline")

        assert config.name == "InlineAgent"
        assert config.persona == "This is an inline persona."

    def test_load_agent_with_default_persona_file(self, temp_agents_dir):
        """Test loading agent with default {agent_name}.md file."""
        yaml_data = {
            "agent": {
                "metadata": {
                    "name": "DefaultAgent",
                    "role": "Default Role",
                },
                "tools": ["Read"],
                "capabilities": ["testing"],
                "model": "claude-sonnet-4-5-20250929",
            }
        }
        yaml_path = temp_agents_dir / "default.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f)

        # Create default persona file
        persona_path = temp_agents_dir / "default.md"
        persona_path.write_text("Default persona text", encoding="utf-8")

        loader = AgentConfigLoader(temp_agents_dir)
        config = loader.load_agent("default")

        assert config.name == "DefaultAgent"
        assert config.persona == "Default persona text"


class TestDiscoverAgents:
    """Tests for agent discovery."""

    def test_discover_agents_empty_directory(self, temp_agents_dir):
        """Test discovering agents in empty directory."""
        loader = AgentConfigLoader(temp_agents_dir)
        agents = loader.discover_agents()

        assert agents == []

    def test_discover_agents_with_agents(self, temp_agents_dir, create_agent_files):
        """Test discovering multiple agents."""
        create_agent_files("agent1")
        create_agent_files("agent2")
        create_agent_files("agent3")

        loader = AgentConfigLoader(temp_agents_dir)
        agents = loader.discover_agents()

        assert sorted(agents) == ["agent1", "agent2", "agent3"]

    def test_discover_agents_sorted(self, temp_agents_dir, create_agent_files):
        """Test that discovered agents are sorted alphabetically."""
        create_agent_files("zebra")
        create_agent_files("alpha")
        create_agent_files("mike")

        loader = AgentConfigLoader(temp_agents_dir)
        agents = loader.discover_agents()

        assert agents == ["alpha", "mike", "zebra"]

    def test_discover_agents_nonexistent_directory(self):
        """Test discovering agents in non-existent directory."""
        loader = AgentConfigLoader(Path("/nonexistent/directory"))
        agents = loader.discover_agents()

        assert agents == []


class TestLoadAllAgents:
    """Tests for loading all agents at once."""

    def test_load_all_agents_success(self, temp_agents_dir, create_agent_files):
        """Test loading all agents successfully."""
        create_agent_files("agent1")
        create_agent_files("agent2")

        loader = AgentConfigLoader(temp_agents_dir)
        configs = loader.load_all_agents()

        assert len(configs) == 2
        assert "agent1" in configs
        assert "agent2" in configs
        assert isinstance(configs["agent1"], AgentConfig)
        assert isinstance(configs["agent2"], AgentConfig)

    def test_load_all_agents_empty_directory(self, temp_agents_dir):
        """Test loading all agents from empty directory."""
        loader = AgentConfigLoader(temp_agents_dir)
        configs = loader.load_all_agents()

        assert configs == {}

    def test_load_all_agents_with_invalid_agent(self, temp_agents_dir, create_agent_files):
        """Test loading all agents when one is invalid raises ValueError."""
        create_agent_files("valid")

        # Create invalid agent (no persona)
        yaml_data = {
            "agent": {
                "metadata": {"name": "Invalid", "role": "Role"},
                "tools": ["Read"],
            }
        }
        yaml_path = temp_agents_dir / "invalid.agent.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f)

        loader = AgentConfigLoader(temp_agents_dir)

        with pytest.raises(ValueError) as exc_info:
            loader.load_all_agents()

        assert "Failed to load agent 'invalid'" in str(exc_info.value)


class TestValidateAgentFile:
    """Tests for agent file validation."""

    def test_validate_agent_file_valid(self, temp_agents_dir, create_agent_files):
        """Test validating a valid agent file."""
        create_agent_files("valid")

        loader = AgentConfigLoader(temp_agents_dir)
        result = loader.validate_agent_file("valid")

        assert result is True

    def test_validate_agent_file_invalid(self, temp_agents_dir):
        """Test validating an invalid agent file."""
        # Create invalid YAML
        yaml_path = temp_agents_dir / "invalid.agent.yaml"
        yaml_path.write_text("invalid: [[[", encoding="utf-8")

        loader = AgentConfigLoader(temp_agents_dir)
        result = loader.validate_agent_file("invalid")

        assert result is False

    def test_validate_agent_file_not_found(self, temp_agents_dir):
        """Test validating a non-existent agent file."""
        loader = AgentConfigLoader(temp_agents_dir)
        result = loader.validate_agent_file("nonexistent")

        assert result is False


class TestRealAgents:
    """Integration tests with real agent files."""

    @pytest.fixture
    def real_agents_dir(self):
        """Get the real agents directory."""
        return Path(__file__).parent.parent.parent / "gao_dev" / "agents"

    def test_load_real_amelia(self, real_agents_dir):
        """Test loading the real Amelia agent."""
        if not real_agents_dir.exists():
            pytest.skip("Real agents directory not found")

        loader = AgentConfigLoader(real_agents_dir)
        config = loader.load_agent("amelia")

        assert config.name == "Amelia"
        assert config.role == "Software Developer"
        assert "Read" in config.tools
        assert "Write" in config.tools
        assert "Edit" in config.tools
        assert "implementation" in config.capabilities
        assert config.persona  # Non-empty

    def test_discover_all_real_agents(self, real_agents_dir):
        """Test discovering all real agents."""
        if not real_agents_dir.exists():
            pytest.skip("Real agents directory not found")

        loader = AgentConfigLoader(real_agents_dir)
        agents = loader.discover_agents()

        expected_agents = ["amelia", "bob", "brian", "john", "mary", "murat", "sally", "winston"]
        assert sorted(agents) == expected_agents

    def test_load_all_real_agents(self, real_agents_dir):
        """Test loading all real agents."""
        if not real_agents_dir.exists():
            pytest.skip("Real agents directory not found")

        loader = AgentConfigLoader(real_agents_dir)
        configs = loader.load_all_agents()

        assert len(configs) == 8
        assert all(isinstance(config, AgentConfig) for config in configs.values())

        # Verify key agents
        assert configs["amelia"].role == "Software Developer"
        assert configs["john"].role == "Product Manager"
        assert configs["winston"].role == "Technical Architect"
