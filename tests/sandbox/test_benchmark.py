"""Tests for benchmark configuration loading and validation."""

from pathlib import Path

import pytest
import yaml

from gao_dev.sandbox.benchmark import (
    BenchmarkConfig,
    BenchmarkError,
    load_benchmark,
    validate_benchmark_file,
)


class TestBenchmarkConfig:
    """Tests for BenchmarkConfig class."""

    @pytest.fixture
    def minimal_config(self):
        """Create minimal valid benchmark configuration."""
        return {
            "benchmark": {
                "name": "test-benchmark",
                "version": "1.0.0",
                "description": "Test benchmark",
                "initial_prompt": "Create a simple test application",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

    @pytest.fixture
    def full_config(self):
        """Create complete benchmark configuration with all fields."""
        return {
            "benchmark": {
                "name": "todo-app-baseline",
                "version": "1.0.0",
                "description": "Baseline todo application benchmark",
                "initial_prompt": "Create a todo list application with CRUD operations",
                "complexity_level": 2,
                "estimated_duration_minutes": 60,
                "tech_stack": {
                    "framework": "Next.js",
                    "styling": "Tailwind CSS",
                    "database": "SQLite",
                },
                "success_criteria": [
                    "Application runs without errors",
                    "All CRUD operations work",
                ],
                "expected_outcomes": {
                    "interventions": 0,
                    "duration_minutes": 60,
                },
                "phases": [
                    {"name": "setup", "duration_minutes": 10},
                    {"name": "development", "duration_minutes": 40},
                    {"name": "testing", "duration_minutes": 10},
                ],
                "constraints": {
                    "no_human_intervention": True,
                },
                "boilerplate": {
                    "url": "https://github.com/webventurer/simple-nextjs-starter",
                },
            }
        }

    def test_create_with_minimal_config(self, minimal_config, tmp_path):
        """Test creating BenchmarkConfig with minimal required fields."""
        test_file = tmp_path / "test.yaml"

        config = BenchmarkConfig(minimal_config, test_file)

        assert config.name == "test-benchmark"
        assert config.version == "1.0.0"
        assert config.description == "Test benchmark"
        assert config.initial_prompt == "Create a simple test application"
        assert config.complexity_level == 1
        assert config.estimated_duration_minutes == 30
        assert config.file_path == test_file
        assert config.tech_stack == {}
        assert config.success_criteria == []
        assert config.expected_outcomes == {}
        assert config.phases == []

    def test_create_with_full_config(self, full_config, tmp_path):
        """Test creating BenchmarkConfig with all fields."""
        test_file = tmp_path / "test.yaml"

        config = BenchmarkConfig(full_config, test_file)

        assert config.name == "todo-app-baseline"
        assert config.version == "1.0.0"
        assert config.complexity_level == 2
        assert config.tech_stack["framework"] == "Next.js"
        assert len(config.success_criteria) == 2
        assert config.expected_outcomes["interventions"] == 0
        assert len(config.phases) == 3
        assert config.constraints["no_human_intervention"] is True
        assert config.boilerplate["url"] == "https://github.com/webventurer/simple-nextjs-starter"

    def test_prompt_hash_calculation(self, minimal_config, tmp_path):
        """Test that prompt hash is calculated correctly."""
        test_file = tmp_path / "test.yaml"

        config = BenchmarkConfig(minimal_config, test_file)

        assert config.prompt_hash is not None
        assert config.prompt_hash.startswith("sha256:")
        assert len(config.prompt_hash) > 10

    def test_prompt_hash_is_deterministic(self, minimal_config, tmp_path):
        """Test that same prompt produces same hash."""
        test_file = tmp_path / "test.yaml"

        config1 = BenchmarkConfig(minimal_config, test_file)
        config2 = BenchmarkConfig(minimal_config, test_file)

        assert config1.prompt_hash == config2.prompt_hash

    def test_prompt_hash_normalizes_whitespace(self, tmp_path):
        """Test that prompt hash normalizes whitespace."""
        test_file = tmp_path / "test.yaml"

        config1_data = {
            "benchmark": {
                "name": "test",
                "version": "1.0.0",
                "description": "Test",
                "initial_prompt": "Create a simple   test    application",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        config2_data = {
            "benchmark": {
                "name": "test",
                "version": "1.0.0",
                "description": "Test",
                "initial_prompt": "Create  a  simple test application",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        config1 = BenchmarkConfig(config1_data, test_file)
        config2 = BenchmarkConfig(config2_data, test_file)

        # Normalized whitespace should produce same hash
        assert config1.prompt_hash == config2.prompt_hash

    def test_missing_benchmark_section_raises_error(self, tmp_path):
        """Test that missing 'benchmark' section raises error."""
        test_file = tmp_path / "test.yaml"
        config = {"wrong_key": {}}

        with pytest.raises(BenchmarkError) as exc_info:
            BenchmarkConfig(config, test_file)

        assert "Missing 'benchmark' section" in str(exc_info.value)

    def test_missing_required_field_raises_error(self, minimal_config, tmp_path):
        """Test that missing required field raises error."""
        test_file = tmp_path / "test.yaml"

        # Remove required field
        del minimal_config["benchmark"]["name"]

        with pytest.raises(BenchmarkError) as exc_info:
            BenchmarkConfig(minimal_config, test_file)

        assert "Missing required field 'name'" in str(exc_info.value)

    def test_wrong_type_for_field_raises_error(self, minimal_config, tmp_path):
        """Test that wrong type for field raises error."""
        test_file = tmp_path / "test.yaml"

        # Use wrong type for name (should be string)
        minimal_config["benchmark"]["name"] = 123

        with pytest.raises(BenchmarkError) as exc_info:
            BenchmarkConfig(minimal_config, test_file)

        assert "must be str" in str(exc_info.value)

    def test_invalid_name_format_raises_error(self, minimal_config, tmp_path):
        """Test that invalid name format raises error."""
        test_file = tmp_path / "test.yaml"

        invalid_names = [
            "Invalid Name",  # Has spaces
            "UPPERCASE",  # Has uppercase
            "test_underscore",  # Has underscore
            "-starts-with-hyphen",  # Starts with hyphen
            "ends-with-hyphen-",  # Ends with hyphen
            "test..double",  # Double dots
        ]

        for invalid_name in invalid_names:
            config_copy = minimal_config.copy()
            config_copy["benchmark"] = minimal_config["benchmark"].copy()
            config_copy["benchmark"]["name"] = invalid_name

            with pytest.raises(BenchmarkError) as exc_info:
                BenchmarkConfig(config_copy, test_file)

            assert "must be lowercase alphanumeric" in str(exc_info.value)

    def test_valid_name_formats(self, minimal_config, tmp_path):
        """Test that valid name formats are accepted."""
        test_file = tmp_path / "test.yaml"

        valid_names = [
            "test",
            "test-benchmark",
            "todo-app-baseline",
            "benchmark123",
            "123benchmark",
            "test-123-name",
        ]

        for valid_name in valid_names:
            config_copy = minimal_config.copy()
            config_copy["benchmark"] = minimal_config["benchmark"].copy()
            config_copy["benchmark"]["name"] = valid_name

            config = BenchmarkConfig(config_copy, test_file)
            assert config.name == valid_name

    def test_invalid_complexity_level_raises_error(self, minimal_config, tmp_path):
        """Test that invalid complexity level raises error."""
        test_file = tmp_path / "test.yaml"

        invalid_levels = [0, 4, 5, -1, 10]

        for invalid_level in invalid_levels:
            config_copy = minimal_config.copy()
            config_copy["benchmark"] = minimal_config["benchmark"].copy()
            config_copy["benchmark"]["complexity_level"] = invalid_level

            with pytest.raises(BenchmarkError) as exc_info:
                BenchmarkConfig(config_copy, test_file)

            assert "Complexity level must be 1, 2, or 3" in str(exc_info.value)

    def test_valid_complexity_levels(self, minimal_config, tmp_path):
        """Test that valid complexity levels are accepted."""
        test_file = tmp_path / "test.yaml"

        for level in [1, 2, 3]:
            config_copy = minimal_config.copy()
            config_copy["benchmark"] = minimal_config["benchmark"].copy()
            config_copy["benchmark"]["complexity_level"] = level

            config = BenchmarkConfig(config_copy, test_file)
            assert config.complexity_level == level

    def test_get_run_id_prefix(self, minimal_config, tmp_path):
        """Test getting run ID prefix."""
        test_file = tmp_path / "test.yaml"

        config = BenchmarkConfig(minimal_config, test_file)

        assert config.get_run_id_prefix() == "test-benchmark"

    def test_to_dict(self, minimal_config, tmp_path):
        """Test serialization to dictionary."""
        test_file = tmp_path / "test.yaml"

        config = BenchmarkConfig(minimal_config, test_file)
        data = config.to_dict()

        assert data["name"] == "test-benchmark"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test benchmark"
        assert data["prompt_hash"].startswith("sha256:")
        assert data["complexity_level"] == 1
        assert data["estimated_duration_minutes"] == 30
        assert data["file_path"] == str(test_file)

    def test_raw_config_preserved(self, full_config, tmp_path):
        """Test that raw config is preserved."""
        test_file = tmp_path / "test.yaml"

        config = BenchmarkConfig(full_config, test_file)

        assert config.raw_config == full_config


class TestLoadBenchmark:
    """Tests for load_benchmark function."""

    @pytest.fixture
    def valid_benchmark_file(self, tmp_path):
        """Create a valid benchmark YAML file."""
        content = {
            "benchmark": {
                "name": "test-benchmark",
                "version": "1.0.0",
                "description": "Test benchmark",
                "initial_prompt": "Create a test application",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        file_path = tmp_path / "benchmark.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)

        return file_path

    def test_load_valid_benchmark(self, valid_benchmark_file):
        """Test loading a valid benchmark file."""
        config = load_benchmark(valid_benchmark_file)

        assert isinstance(config, BenchmarkConfig)
        assert config.name == "test-benchmark"
        assert config.version == "1.0.0"

    def test_load_with_yml_extension(self, tmp_path):
        """Test loading benchmark with .yml extension."""
        content = {
            "benchmark": {
                "name": "test",
                "version": "1.0.0",
                "description": "Test",
                "initial_prompt": "Test",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        file_path = tmp_path / "benchmark.yml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)

        config = load_benchmark(file_path)
        assert config.name == "test"

    def test_load_nonexistent_file_raises_error(self, tmp_path):
        """Test that loading nonexistent file raises error."""
        file_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(file_path)

        assert "not found" in str(exc_info.value)

    def test_load_directory_raises_error(self, tmp_path):
        """Test that loading directory raises error."""
        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(tmp_path)

        assert "Not a file" in str(exc_info.value)

    def test_load_wrong_extension_raises_error(self, tmp_path):
        """Test that wrong file extension raises error."""
        file_path = tmp_path / "benchmark.txt"
        file_path.write_text("content")

        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(file_path)

        assert ".yaml or .yml extension" in str(exc_info.value)

    def test_load_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML raises error."""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text("invalid: yaml: content: [")

        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(file_path)

        assert "Failed to parse YAML" in str(exc_info.value)

    def test_load_non_dict_yaml_raises_error(self, tmp_path):
        """Test that non-dictionary YAML raises error."""
        file_path = tmp_path / "list.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(["item1", "item2"], f)

        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(file_path)

        assert "must contain a YAML dictionary" in str(exc_info.value)

    def test_load_empty_file_raises_error(self, tmp_path):
        """Test that empty file raises error."""
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("")

        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(file_path)

        assert "dictionary" in str(exc_info.value)

    def test_load_missing_required_fields_raises_error(self, tmp_path):
        """Test that missing required fields raises error."""
        content = {
            "benchmark": {
                "name": "test",
                # Missing other required fields
            }
        }

        file_path = tmp_path / "incomplete.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)

        with pytest.raises(BenchmarkError) as exc_info:
            load_benchmark(file_path)

        assert "Missing required field" in str(exc_info.value)

    def test_load_resolves_path(self, tmp_path):
        """Test that load_benchmark resolves relative paths."""
        content = {
            "benchmark": {
                "name": "test",
                "version": "1.0.0",
                "description": "Test",
                "initial_prompt": "Test",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        file_path = tmp_path / "benchmark.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)

        config = load_benchmark(file_path)

        # File path should be resolved to absolute
        assert config.file_path.is_absolute()


class TestValidateBenchmarkFile:
    """Tests for validate_benchmark_file function."""

    @pytest.fixture
    def valid_benchmark_file(self, tmp_path):
        """Create a valid benchmark YAML file."""
        content = {
            "benchmark": {
                "name": "test-benchmark",
                "version": "1.0.0",
                "description": "Test benchmark",
                "initial_prompt": "Create a test application",
                "complexity_level": 1,
                "estimated_duration_minutes": 30,
            }
        }

        file_path = tmp_path / "benchmark.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)

        return file_path

    def test_validate_valid_file_returns_true(self, valid_benchmark_file):
        """Test that validating valid file returns True."""
        assert validate_benchmark_file(valid_benchmark_file) is True

    def test_validate_invalid_file_returns_false(self, tmp_path):
        """Test that validating invalid file returns False."""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text("invalid: yaml")

        assert validate_benchmark_file(file_path) is False

    def test_validate_nonexistent_file_returns_false(self, tmp_path):
        """Test that validating nonexistent file returns False."""
        file_path = tmp_path / "nonexistent.yaml"

        assert validate_benchmark_file(file_path) is False

    def test_validate_does_not_raise_exception(self, tmp_path):
        """Test that validate_benchmark_file doesn't raise exceptions."""
        file_path = tmp_path / "bad.yaml"
        file_path.write_text("completely invalid")

        # Should return False, not raise
        result = validate_benchmark_file(file_path)
        assert result is False


class TestBenchmarkError:
    """Tests for BenchmarkError exception."""

    def test_benchmark_error_is_sandbox_error(self):
        """Test that BenchmarkError inherits from SandboxError."""
        from gao_dev.sandbox.exceptions import SandboxError

        error = BenchmarkError("test error")
        assert isinstance(error, SandboxError)

    def test_benchmark_error_message(self):
        """Test that BenchmarkError preserves message."""
        error = BenchmarkError("custom message")
        assert str(error) == "custom message"

    def test_can_be_raised_and_caught(self):
        """Test that BenchmarkError can be raised and caught."""
        with pytest.raises(BenchmarkError) as exc_info:
            raise BenchmarkError("test")

        assert str(exc_info.value) == "test"
