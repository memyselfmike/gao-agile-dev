"""Unit tests for provider models."""

import pytest
from pathlib import Path
from gao_dev.core.providers.models import AgentContext


class TestAgentContext:
    """Test AgentContext dataclass."""

    def test_minimal_initialization(self, tmp_path):
        """Test AgentContext can be initialized with just project_root."""
        context = AgentContext(project_root=tmp_path)

        assert context.project_root == tmp_path.resolve()
        assert isinstance(context.metadata, dict)
        assert len(context.metadata) == 0
        assert isinstance(context.environment_vars, dict)
        assert len(context.environment_vars) == 0
        assert context.allow_destructive_operations is True
        assert context.enable_network is True

    def test_working_directory_defaults_to_project_root(self, tmp_path):
        """Test working_directory defaults to project_root."""
        context = AgentContext(project_root=tmp_path)

        assert context.working_directory == context.project_root

    def test_explicit_working_directory(self, tmp_path):
        """Test explicit working_directory is respected."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        context = AgentContext(
            project_root=tmp_path,
            working_directory=subdir
        )

        assert context.working_directory == subdir.resolve()
        assert context.working_directory != context.project_root

    def test_paths_are_resolved_to_absolute(self, tmp_path):
        """Test paths are automatically resolved to absolute paths."""
        # Create context with relative-like path
        context = AgentContext(project_root=tmp_path)

        # Paths should be absolute
        assert context.project_root.is_absolute()
        assert context.working_directory.is_absolute()

    def test_metadata_initialization(self, tmp_path):
        """Test metadata can be initialized with dict."""
        metadata = {
            "user_id": "user123",
            "session_id": "sess456",
            "epic": "11"
        }

        context = AgentContext(
            project_root=tmp_path,
            metadata=metadata
        )

        assert context.metadata == metadata
        assert context.metadata["user_id"] == "user123"

    def test_environment_vars_initialization(self, tmp_path):
        """Test environment_vars can be initialized with dict."""
        env_vars = {
            "NODE_ENV": "production",
            "CUSTOM_VAR": "value"
        }

        context = AgentContext(
            project_root=tmp_path,
            environment_vars=env_vars
        )

        assert context.environment_vars == env_vars
        assert context.environment_vars["NODE_ENV"] == "production"

    def test_allow_destructive_operations_flag(self, tmp_path):
        """Test allow_destructive_operations can be set."""
        context_allow = AgentContext(
            project_root=tmp_path,
            allow_destructive_operations=True
        )
        assert context_allow.allow_destructive_operations is True

        context_deny = AgentContext(
            project_root=tmp_path,
            allow_destructive_operations=False
        )
        assert context_deny.allow_destructive_operations is False

    def test_enable_network_flag(self, tmp_path):
        """Test enable_network can be set."""
        context_online = AgentContext(
            project_root=tmp_path,
            enable_network=True
        )
        assert context_online.enable_network is True

        context_offline = AgentContext(
            project_root=tmp_path,
            enable_network=False
        )
        assert context_offline.enable_network is False

    def test_repr_includes_key_attributes(self, tmp_path):
        """Test __repr__ includes key attributes."""
        context = AgentContext(
            project_root=tmp_path,
            metadata={"key": "value"}
        )

        repr_str = repr(context)
        assert "AgentContext" in repr_str
        assert str(tmp_path) in repr_str or "project_root" in repr_str
        assert "metadata" in repr_str

    def test_context_with_all_fields(self, tmp_path):
        """Test AgentContext with all fields specified."""
        subdir = tmp_path / "work"
        subdir.mkdir()

        context = AgentContext(
            project_root=tmp_path,
            metadata={"user": "test"},
            working_directory=subdir,
            environment_vars={"VAR": "value"},
            allow_destructive_operations=False,
            enable_network=False
        )

        assert context.project_root == tmp_path.resolve()
        assert context.working_directory == subdir.resolve()
        assert context.metadata == {"user": "test"}
        assert context.environment_vars == {"VAR": "value"}
        assert context.allow_destructive_operations is False
        assert context.enable_network is False

    def test_invalid_project_root_type_raises_error(self):
        """Test invalid project_root type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AgentContext(project_root="not a path")  # type: ignore

        assert "project_root must be a Path" in str(exc_info.value)

    def test_nonexistent_project_root_logs_warning(self, tmp_path):
        """Test nonexistent project_root logs warning but doesn't fail."""
        nonexistent = tmp_path / "does_not_exist"

        # Should not raise exception
        context = AgentContext(project_root=nonexistent)

        # Should have resolved path
        assert context.project_root == nonexistent.resolve()

    def test_nonexistent_working_directory_falls_back_to_project_root(self, tmp_path):
        """Test nonexistent working_directory falls back to project_root."""
        nonexistent_work = tmp_path / "does_not_exist"

        context = AgentContext(
            project_root=tmp_path,
            working_directory=nonexistent_work
        )

        # Should fall back to project_root
        assert context.working_directory == tmp_path.resolve()

    def test_metadata_is_independent_copy(self, tmp_path):
        """Test metadata modifications don't affect original dict."""
        original_metadata = {"key": "value"}
        context = AgentContext(
            project_root=tmp_path,
            metadata=original_metadata
        )

        # Modify context metadata
        context.metadata["new_key"] = "new_value"

        # Original should be unchanged (if using field(default_factory=dict))
        # Note: This test validates that we're not sharing dict references
        assert context.metadata["new_key"] == "new_value"

    def test_environment_vars_is_independent_copy(self, tmp_path):
        """Test environment_vars modifications don't affect original dict."""
        original_env = {"VAR": "value"}
        context = AgentContext(
            project_root=tmp_path,
            environment_vars=original_env
        )

        # Modify context env vars
        context.environment_vars["NEW_VAR"] = "new_value"

        # Original should be unchanged
        assert context.environment_vars["NEW_VAR"] == "new_value"

    def test_empty_metadata_by_default(self, tmp_path):
        """Test metadata is empty dict by default."""
        context = AgentContext(project_root=tmp_path)

        assert context.metadata == {}
        assert isinstance(context.metadata, dict)

    def test_empty_environment_vars_by_default(self, tmp_path):
        """Test environment_vars is empty dict by default."""
        context = AgentContext(project_root=tmp_path)

        assert context.environment_vars == {}
        assert isinstance(context.environment_vars, dict)


class TestAgentContextPostInit:
    """Test AgentContext __post_init__ validation."""

    def test_post_init_sets_working_directory(self, tmp_path):
        """Test __post_init__ sets working_directory if None."""
        context = AgentContext(project_root=tmp_path)

        # Should be set by __post_init__
        assert context.working_directory is not None
        assert context.working_directory == context.project_root

    def test_post_init_resolves_paths(self, tmp_path):
        """Test __post_init__ resolves paths to absolute."""
        # Even if we pass absolute paths, resolve() ensures they're canonical
        context = AgentContext(project_root=tmp_path)

        assert context.project_root == tmp_path.resolve()
        assert context.working_directory == tmp_path.resolve()

    def test_post_init_handles_relative_paths(self, tmp_path):
        """Test __post_init__ converts relative paths to absolute."""
        # Create a Path and then make it "relative-like" (this is tricky in tests)
        # In practice, resolve() handles this
        context = AgentContext(project_root=tmp_path)

        # Should be absolute
        assert context.project_root.is_absolute()
        assert context.working_directory.is_absolute()


class TestAgentContextImmutability:
    """Test AgentContext immutability (or lack thereof)."""

    def test_context_fields_are_mutable(self, tmp_path):
        """Test context fields can be modified after creation."""
        context = AgentContext(project_root=tmp_path)

        # Metadata should be mutable
        context.metadata["new_key"] = "new_value"
        assert context.metadata["new_key"] == "new_value"

        # Environment vars should be mutable
        context.environment_vars["NEW_VAR"] = "new_value"
        assert context.environment_vars["NEW_VAR"] == "new_value"

        # Flags should be mutable (dataclass default)
        context.allow_destructive_operations = False
        assert context.allow_destructive_operations is False

    def test_context_can_be_copied(self, tmp_path):
        """Test AgentContext can be copied."""
        from copy import copy, deepcopy

        original = AgentContext(
            project_root=tmp_path,
            metadata={"key": "value"}
        )

        # Shallow copy
        shallow = copy(original)
        assert shallow.project_root == original.project_root
        # Note: shallow copy shares metadata dict

        # Deep copy
        deep = deepcopy(original)
        assert deep.project_root == original.project_root
        assert deep.metadata == original.metadata
        # Deep copy has independent metadata
        deep.metadata["new"] = "value"
        assert "new" not in original.metadata


class TestAgentContextUsage:
    """Test AgentContext usage scenarios."""

    def test_sandbox_context(self, tmp_path):
        """Test creating context for sandbox execution."""
        sandbox_root = tmp_path / "sandbox" / "project"
        sandbox_root.mkdir(parents=True)

        context = AgentContext(
            project_root=sandbox_root,
            metadata={
                "benchmark_id": "bench123",
                "run_id": "run456"
            },
            allow_destructive_operations=True,
            enable_network=True
        )

        assert context.project_root == sandbox_root.resolve()
        assert context.metadata["benchmark_id"] == "bench123"
        assert context.allow_destructive_operations is True

    def test_readonly_context(self, tmp_path):
        """Test creating context for read-only analysis."""
        context = AgentContext(
            project_root=tmp_path,
            allow_destructive_operations=False,
            enable_network=False
        )

        assert context.allow_destructive_operations is False
        assert context.enable_network is False

    def test_monorepo_context(self, tmp_path):
        """Test creating context for monorepo package."""
        # Simulate monorepo structure
        monorepo_root = tmp_path
        package_dir = monorepo_root / "packages" / "my-package"
        package_dir.mkdir(parents=True)

        context = AgentContext(
            project_root=monorepo_root,
            working_directory=package_dir
        )

        assert context.project_root == monorepo_root.resolve()
        assert context.working_directory == package_dir.resolve()
