"""Tests for PromptTemplate model."""

import pytest
from pathlib import Path
import yaml

from gao_dev.core.models.prompt_template import PromptTemplate


def test_prompt_template_creation():
    """Test basic prompt template creation."""
    template = PromptTemplate(
        name="test",
        description="Test prompt",
        system_prompt="You are a test assistant",
        user_prompt="Hello {{name}}",
        variables={"name": "World"}
    )

    assert template.name == "test"
    assert template.description == "Test prompt"
    assert template.system_prompt == "You are a test assistant"
    assert template.user_prompt == "Hello {{name}}"
    assert template.variables == {"name": "World"}
    assert template.max_tokens == 4000
    assert template.temperature == 0.7


def test_prompt_template_validation():
    """Test prompt template validation."""
    # Empty name
    with pytest.raises(ValueError, match="name cannot be empty"):
        PromptTemplate(
            name="",
            description="Test",
            system_prompt=None,
            user_prompt="Hello",
            variables={}
        )

    # Empty user_prompt
    with pytest.raises(ValueError, match="User prompt cannot be empty"):
        PromptTemplate(
            name="test",
            description="Test",
            system_prompt=None,
            user_prompt="",
            variables={}
        )

    # Invalid temperature
    with pytest.raises(ValueError, match="Temperature must be"):
        PromptTemplate(
            name="test",
            description="Test",
            system_prompt=None,
            user_prompt="Hello",
            variables={},
            temperature=1.5
        )

    # Invalid max_tokens
    with pytest.raises(ValueError, match="Max tokens must be"):
        PromptTemplate(
            name="test",
            description="Test",
            system_prompt=None,
            user_prompt="Hello",
            variables={},
            max_tokens=0
        )


def test_variable_substitution():
    """Test basic variable substitution."""
    template = PromptTemplate(
        name="greeting",
        description="Greeting template",
        system_prompt=None,
        user_prompt="Hello {{name}}!",
        variables={"name": "World"}
    )

    # Use provided value
    rendered = template.render({"name": "Alice"})
    assert rendered == "Hello Alice!"

    # Use default value
    rendered = template.render({})
    assert rendered == "Hello World!"


def test_multiple_variable_substitution():
    """Test substitution with multiple variables."""
    template = PromptTemplate(
        name="greeting",
        description="Greeting template",
        system_prompt=None,
        user_prompt="Hello {{name}}, welcome to {{place}}!",
        variables={"name": "User", "place": "GAO-Dev"}
    )

    rendered = template.render({"name": "Alice", "place": "Wonderland"})
    assert rendered == "Hello Alice, welcome to Wonderland!"

    # Partial override
    rendered = template.render({"name": "Bob"})
    assert rendered == "Hello Bob, welcome to GAO-Dev!"


def test_variable_substitution_with_types():
    """Test variable substitution with different types."""
    template = PromptTemplate(
        name="stats",
        description="Stats template",
        system_prompt=None,
        user_prompt="Count: {{count}}, Enabled: {{enabled}}",
        variables={"count": 0, "enabled": False}
    )

    rendered = template.render({"count": 42, "enabled": True})
    assert rendered == "Count: 42, Enabled: True"


def test_system_prompt_rendering():
    """Test system prompt rendering."""
    template = PromptTemplate(
        name="test",
        description="Test",
        system_prompt="You are {{role}}",
        user_prompt="Do {{task}}",
        variables={"role": "assistant", "task": "something"}
    )

    system = template.render_system_prompt({"role": "developer"})
    assert system == "You are developer"

    user = template.render({"task": "coding"})
    assert user == "Do coding"


def test_system_prompt_none():
    """Test handling of None system prompt."""
    template = PromptTemplate(
        name="test",
        description="Test",
        system_prompt=None,
        user_prompt="Hello",
        variables={}
    )

    system = template.render_system_prompt({})
    assert system is None


def test_from_yaml_basic(tmp_path):
    """Test loading from YAML file."""
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """
name: test_prompt
description: Test prompt template
system_prompt: You are a test assistant
user_prompt: Hello {{name}}
variables:
  name: World
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    template = PromptTemplate.from_yaml(yaml_file)

    assert template.name == "test_prompt"
    assert template.description == "Test prompt template"
    assert template.system_prompt == "You are a test assistant"
    assert template.user_prompt == "Hello {{name}}"
    assert template.variables == {"name": "World"}


def test_from_yaml_with_response_config(tmp_path):
    """Test loading YAML with response configuration."""
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """
name: structured_prompt
description: Prompt with structured response
user_prompt: Generate data for {{entity}}
variables:
  entity: User
response:
  schema:
    type: object
    properties:
      data: { type: string }
  max_tokens: 2000
  temperature: 0.5
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    template = PromptTemplate.from_yaml(yaml_file)

    assert template.schema == {"type": "object", "properties": {"data": {"type": "string"}}}
    assert template.max_tokens == 2000
    assert template.temperature == 0.5


def test_from_yaml_with_metadata(tmp_path):
    """Test loading YAML with metadata."""
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """
name: prd
description: Create PRD
user_prompt: Create PRD for {{project}}
variables:
  project: MyProject
metadata:
  category: planning
  phase: 2
  tags:
    - prd
    - planning
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    template = PromptTemplate.from_yaml(yaml_file)

    assert template.metadata == {
        "category": "planning",
        "phase": 2,
        "tags": ["prd", "planning"]
    }


def test_from_yaml_file_not_found():
    """Test loading non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        PromptTemplate.from_yaml(Path("/nonexistent/file.yaml"))


def test_from_yaml_invalid_yaml(tmp_path):
    """Test loading invalid YAML."""
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("invalid: yaml: content:", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid YAML"):
        PromptTemplate.from_yaml(yaml_file)


def test_from_yaml_missing_required_fields(tmp_path):
    """Test loading YAML with missing required fields."""
    # Missing name
    yaml_file = tmp_path / "missing_name.yaml"
    yaml_file.write_text("description: Test\nuser_prompt: Hello", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing 'name' field"):
        PromptTemplate.from_yaml(yaml_file)

    # Missing description
    yaml_file = tmp_path / "missing_desc.yaml"
    yaml_file.write_text("name: test\nuser_prompt: Hello", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing 'description' field"):
        PromptTemplate.from_yaml(yaml_file)

    # Missing user_prompt
    yaml_file = tmp_path / "missing_prompt.yaml"
    yaml_file.write_text("name: test\ndescription: Test", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing 'user_prompt' field"):
        PromptTemplate.from_yaml(yaml_file)


def test_from_yaml_empty_file(tmp_path):
    """Test loading empty YAML file."""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Empty YAML file"):
        PromptTemplate.from_yaml(yaml_file)


def test_to_dict():
    """Test converting to dictionary."""
    template = PromptTemplate(
        name="test",
        description="Test",
        system_prompt="System",
        user_prompt="User {{var}}",
        variables={"var": "value"},
        schema={"type": "object"},
        max_tokens=2000,
        temperature=0.5,
        metadata={"category": "test"}
    )

    data = template.to_dict()

    assert data["name"] == "test"
    assert data["description"] == "Test"
    assert data["system_prompt"] == "System"
    assert data["user_prompt"] == "User {{var}}"
    assert data["variables"] == {"var": "value"}
    assert data["schema"] == {"type": "object"}
    assert data["max_tokens"] == 2000
    assert data["temperature"] == 0.5
    assert data["metadata"] == {"category": "test"}


def test_to_yaml(tmp_path):
    """Test saving to YAML file."""
    template = PromptTemplate(
        name="test",
        description="Test prompt",
        system_prompt="System",
        user_prompt="User {{var}}",
        variables={"var": "value"},
        max_tokens=2000,
        temperature=0.5,
        metadata={"category": "test"}
    )

    yaml_file = tmp_path / "output.yaml"
    template.to_yaml(yaml_file)

    # Load and verify
    with open(yaml_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["name"] == "test"
    assert data["description"] == "Test prompt"
    assert data["system_prompt"] == "System"
    assert data["user_prompt"] == "User {{var}}"
    assert data["variables"] == {"var": "value"}
    assert data["response"]["max_tokens"] == 2000
    assert data["response"]["temperature"] == 0.5
    assert data["metadata"] == {"category": "test"}


def test_to_yaml_defaults(tmp_path):
    """Test saving to YAML with default values."""
    template = PromptTemplate(
        name="simple",
        description="Simple prompt",
        system_prompt=None,
        user_prompt="Hello",
        variables={}
    )

    yaml_file = tmp_path / "simple.yaml"
    template.to_yaml(yaml_file)

    # Load and verify
    with open(yaml_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["name"] == "simple"
    assert "system_prompt" not in data
    assert "response" not in data  # No response section for defaults


def test_str_and_repr():
    """Test string representations."""
    template = PromptTemplate(
        name="test",
        description="Test prompt",
        system_prompt=None,
        user_prompt="Hello",
        variables={}
    )

    assert str(template) == "PromptTemplate('test')"
    assert repr(template) == "PromptTemplate(name='test', description='Test prompt')"


def test_roundtrip_yaml(tmp_path):
    """Test YAML save and load roundtrip."""
    original = PromptTemplate(
        name="roundtrip",
        description="Roundtrip test",
        system_prompt="System {{var1}}",
        user_prompt="User {{var2}}",
        variables={"var1": "value1", "var2": "value2"},
        schema={"type": "object"},
        max_tokens=3000,
        temperature=0.8,
        metadata={"category": "test", "phase": 2}
    )

    # Save
    yaml_file = tmp_path / "roundtrip.yaml"
    original.to_yaml(yaml_file)

    # Load
    loaded = PromptTemplate.from_yaml(yaml_file)

    # Verify
    assert loaded.name == original.name
    assert loaded.description == original.description
    assert loaded.system_prompt == original.system_prompt
    assert loaded.user_prompt == original.user_prompt
    assert loaded.variables == original.variables
    assert loaded.schema == original.schema
    assert loaded.max_tokens == original.max_tokens
    assert loaded.temperature == original.temperature
    assert loaded.metadata == original.metadata
