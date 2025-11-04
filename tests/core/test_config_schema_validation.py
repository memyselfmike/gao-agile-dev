"""Tests for configuration schema validation with provider support."""

import pytest
from pathlib import Path
import yaml
import json
import jsonschema


class TestAgentSchemaWithProviders:
    """Test agent schema validation with provider fields."""

    def setup_method(self):
        """Load the agent schema."""
        schema_path = Path("gao_dev/config/schemas/agent_schema.json")
        with open(schema_path) as f:
            self.schema = json.load(f)

    def test_schema_loaded(self):
        """Test that schema loads successfully."""
        assert self.schema is not None
        assert "properties" in self.schema
        assert "agent" in self.schema["properties"]

    def test_agent_config_without_provider_valid(self):
        """Test agent config without provider field is valid (backward compat)."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Should not raise
        jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_with_provider_valid(self):
        """Test agent config with provider field is valid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "provider": "claude-code",
                    "provider_config": {
                        "cli_path": "/usr/bin/claude"
                    },
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Should not raise
        jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_with_provider_config_only(self):
        """Test agent config with provider_config but no provider name."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "provider_config": {
                        "api_key": "test"
                    },
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Should be valid (provider_config without provider is allowed)
        jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_missing_required_fields_invalid(self):
        """Test agent config missing required fields is invalid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    # Missing model, max_tokens, temperature
                    "provider": "claude-code"
                }
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_invalid_temperature_range(self):
        """Test agent config with temperature out of range is invalid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 2.0  # Invalid: > 1.0
                }
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_invalid_max_tokens(self):
        """Test agent config with invalid max_tokens is invalid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "model": "sonnet-4.5",
                    "max_tokens": -100,  # Invalid: < 1
                    "temperature": 0.7
                }
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_with_empty_provider_config(self):
        """Test agent config with empty provider_config is valid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "provider": "claude-code",
                    "provider_config": {},  # Empty but valid
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Should not raise
        jsonschema.validate(instance=config, schema=self.schema)

    def test_agent_config_with_complex_provider_config(self):
        """Test agent config with complex provider_config is valid."""
        config = {
            "agent": {
                "metadata": {
                    "name": "Test",
                    "role": "Tester",
                    "version": "1.0.0"
                },
                "persona": {
                    "background": "Test persona"
                },
                "tools": ["Read", "Write"],
                "configuration": {
                    "provider": "opencode",
                    "provider_config": {
                        "ai_provider": "anthropic",
                        "timeout": 7200,
                        "max_retries": 3,
                        "nested": {
                            "key": "value"
                        }
                    },
                    "model": "sonnet-4.5",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        }

        # Should not raise (provider_config accepts any structure)
        jsonschema.validate(instance=config, schema=self.schema)


class TestDefaultsYAMLProviderConfig:
    """Test defaults.yaml provider configuration."""

    def test_defaults_yaml_loads(self):
        """Test that defaults.yaml loads successfully."""
        defaults_path = Path("gao_dev/config/defaults.yaml")
        with open(defaults_path) as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert "providers" in config
        assert "models" in config

    def test_providers_config_structure(self):
        """Test providers configuration structure."""
        defaults_path = Path("gao_dev/config/defaults.yaml")
        with open(defaults_path) as f:
            config = yaml.safe_load(f)

        providers = config["providers"]
        assert "default" in providers
        assert "claude-code" in providers
        assert "fallback_chain" in providers

    def test_model_registry_structure(self):
        """Test model registry structure."""
        defaults_path = Path("gao_dev/config/defaults.yaml")
        with open(defaults_path) as f:
            config = yaml.safe_load(f)

        models = config["models"]
        assert "registry" in models
        assert len(models["registry"]) > 0

        # Check first model entry structure
        first_model = models["registry"][0]
        assert "canonical" in first_model
        assert "description" in first_model
        assert "providers" in first_model

    def test_feature_flag_present(self):
        """Test provider abstraction feature flag is present."""
        defaults_path = Path("gao_dev/config/defaults.yaml")
        with open(defaults_path) as f:
            config = yaml.safe_load(f)

        assert "features" in config
        assert "provider_abstraction_enabled" in config["features"]
        # Should default to False for gradual rollout
        assert config["features"]["provider_abstraction_enabled"] is False
