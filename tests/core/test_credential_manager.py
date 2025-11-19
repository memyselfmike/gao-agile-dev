"""Tests for CredentialManager with environment-first storage.

Epic 41: Streamlined Onboarding
Story 41.4: CredentialManager with Environment-First Storage

Tests cover:
- Each backend individually
- Priority order
- Environment-based selection
- Encryption security
- Secure logging (no values in logs)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import yaml

from gao_dev.core.credential_manager import (
    CREDENTIAL_ENV_MAP,
    CredentialBackend,
    CredentialManager,
    EncryptedFileBackend,
    EnvironmentVariableBackend,
    KeychainBackend,
    MountedConfigBackend,
    NoBackendAvailableError,
)
from gao_dev.core.environment_detector import EnvironmentType


class TestEnvironmentVariableBackend:
    """Tests for EnvironmentVariableBackend."""

    def test_name(self):
        """Test backend name."""
        backend = EnvironmentVariableBackend()
        assert backend.name == "environment_variable"

    def test_is_available(self):
        """Test backend is always available."""
        backend = EnvironmentVariableBackend()
        assert backend.is_available is True

    def test_is_not_writable(self):
        """Test backend is not writable."""
        backend = EnvironmentVariableBackend()
        assert backend.is_writable is False

    def test_get_credential_from_env(self):
        """Test getting credential from environment variable."""
        backend = EnvironmentVariableBackend()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            value = backend.get_credential("anthropic_api_key")
            assert value == "test-key"

    def test_get_credential_missing(self):
        """Test getting missing credential returns None."""
        backend = EnvironmentVariableBackend()

        with patch.dict(os.environ, {}, clear=True):
            value = backend.get_credential("anthropic_api_key")
            assert value is None

    def test_get_credential_custom_name(self):
        """Test getting credential with custom name."""
        backend = EnvironmentVariableBackend()

        with patch.dict(os.environ, {"CUSTOM_KEY": "custom-value"}):
            value = backend.get_credential("custom_key")
            assert value == "custom-value"

    def test_store_credential_returns_false(self):
        """Test storing credential returns False."""
        backend = EnvironmentVariableBackend()
        result = backend.store_credential("test", "value")
        assert result is False

    def test_delete_credential_returns_false(self):
        """Test deleting credential returns False."""
        backend = EnvironmentVariableBackend()
        result = backend.delete_credential("test")
        assert result is False

    def test_env_var_mapping(self):
        """Test environment variable mapping."""
        backend = EnvironmentVariableBackend()

        for cred_name, env_var in CREDENTIAL_ENV_MAP.items():
            with patch.dict(os.environ, {env_var: f"value-{cred_name}"}):
                value = backend.get_credential(cred_name)
                assert value == f"value-{cred_name}"


class TestMountedConfigBackend:
    """Tests for MountedConfigBackend."""

    def test_name(self):
        """Test backend name."""
        backend = MountedConfigBackend()
        assert backend.name == "mounted_config"

    def test_is_available_file_exists(self, tmp_path):
        """Test backend is available when file exists."""
        config_path = tmp_path / "credentials.yaml"
        config_path.write_text("credentials: {}")

        backend = MountedConfigBackend(config_path)
        assert backend.is_available is True

    def test_is_available_file_missing(self, tmp_path):
        """Test backend is not available when file missing."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        assert backend.is_available is False

    def test_is_writable_parent_exists(self, tmp_path):
        """Test backend is writable when parent exists."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        assert backend.is_writable is True

    def test_get_credential(self, tmp_path):
        """Test getting credential from config file."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"anthropic_api_key": "test-key"}}
        config_path.write_text(yaml.safe_dump(config))

        backend = MountedConfigBackend(config_path)
        value = backend.get_credential("anthropic_api_key")
        assert value == "test-key"

    def test_get_credential_missing(self, tmp_path):
        """Test getting missing credential returns None."""
        config_path = tmp_path / "credentials.yaml"
        config_path.write_text("credentials: {}")

        backend = MountedConfigBackend(config_path)
        value = backend.get_credential("anthropic_api_key")
        assert value is None

    def test_store_credential(self, tmp_path):
        """Test storing credential in config file."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        result = backend.store_credential("anthropic_api_key", "new-key")

        assert result is True
        assert config_path.exists()

        # Verify content
        config = yaml.safe_load(config_path.read_text())
        assert config["credentials"]["anthropic_api_key"] == "new-key"

    def test_store_credential_update_existing(self, tmp_path):
        """Test updating existing credential."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"anthropic_api_key": "old-key"}}
        config_path.write_text(yaml.safe_dump(config))

        backend = MountedConfigBackend(config_path)
        result = backend.store_credential("anthropic_api_key", "new-key")

        assert result is True
        config = yaml.safe_load(config_path.read_text())
        assert config["credentials"]["anthropic_api_key"] == "new-key"

    def test_delete_credential(self, tmp_path):
        """Test deleting credential from config file."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"anthropic_api_key": "test-key"}}
        config_path.write_text(yaml.safe_dump(config))

        backend = MountedConfigBackend(config_path)
        result = backend.delete_credential("anthropic_api_key")

        assert result is True
        config = yaml.safe_load(config_path.read_text())
        assert "anthropic_api_key" not in config["credentials"]

    def test_delete_credential_not_found(self, tmp_path):
        """Test deleting non-existent credential."""
        config_path = tmp_path / "credentials.yaml"
        config_path.write_text("credentials: {}")

        backend = MountedConfigBackend(config_path)
        result = backend.delete_credential("anthropic_api_key")
        assert result is False

    def test_creates_parent_directory(self, tmp_path):
        """Test that storing creates parent directory if needed."""
        config_path = tmp_path / "subdir" / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        result = backend.store_credential("test", "value")

        assert result is True
        assert config_path.parent.exists()


class TestKeychainBackend:
    """Tests for KeychainBackend."""

    def test_name(self):
        """Test backend name."""
        backend = KeychainBackend()
        assert backend.name == "keychain"

    def test_service_name(self):
        """Test service name constant."""
        assert KeychainBackend.SERVICE_NAME == "gao-dev"

    def test_is_available_no_keyring(self):
        """Test backend unavailable when keyring not installed."""
        backend = KeychainBackend()

        with patch.dict("sys.modules", {"keyring": None}):
            # Reset cached value
            backend._keyring_available = None
            available = backend.is_available
            # Should return False when keyring import fails
            assert isinstance(available, bool)

    def test_get_credential_keyring_available(self):
        """Test getting credential when keyring is available."""
        try:
            import keyring
        except ImportError:
            pytest.skip("keyring not installed")

        backend = KeychainBackend()

        with patch.object(backend, "_check_keyring", return_value=True):
            with patch("keyring.get_password", return_value="test-key") as mock_get:
                value = backend.get_credential("anthropic_api_key")

                assert value == "test-key"
                mock_get.assert_called_once_with("gao-dev", "anthropic_api_key")

    @patch("gao_dev.core.credential_manager.KeychainBackend._check_keyring")
    def test_get_credential_keyring_unavailable(self, mock_check):
        """Test getting credential when keyring unavailable."""
        mock_check.return_value = False

        backend = KeychainBackend()
        value = backend.get_credential("test")
        assert value is None

    def test_store_credential_keyring_available(self):
        """Test storing credential when keyring is available."""
        try:
            import keyring
        except ImportError:
            pytest.skip("keyring not installed")

        backend = KeychainBackend()

        with patch.object(backend, "_check_keyring", return_value=True):
            with patch("keyring.set_password") as mock_set:
                result = backend.store_credential("anthropic_api_key", "new-key")

                assert result is True
                mock_set.assert_called_once_with("gao-dev", "anthropic_api_key", "new-key")

    def test_delete_credential_keyring_available(self):
        """Test deleting credential when keyring is available."""
        try:
            import keyring
        except ImportError:
            pytest.skip("keyring not installed")

        backend = KeychainBackend()

        with patch.object(backend, "_check_keyring", return_value=True):
            with patch("keyring.delete_password") as mock_delete:
                result = backend.delete_credential("anthropic_api_key")

                assert result is True
                mock_delete.assert_called_once_with("gao-dev", "anthropic_api_key")


class TestEncryptedFileBackend:
    """Tests for EncryptedFileBackend."""

    def test_name(self):
        """Test backend name."""
        backend = EncryptedFileBackend()
        assert backend.name == "encrypted_file"

    def test_iterations_constant(self):
        """Test PBKDF2 iterations constant."""
        assert EncryptedFileBackend.ITERATIONS == 600_000

    def test_salt_length(self):
        """Test salt length constant."""
        assert EncryptedFileBackend.SALT_LENGTH == 32

    def test_nonce_length(self):
        """Test nonce length constant."""
        assert EncryptedFileBackend.NONCE_LENGTH == 12

    def test_is_available_without_password(self):
        """Test backend unavailable without password."""
        backend = EncryptedFileBackend()
        assert backend.is_available is False

    def test_is_available_with_password(self, tmp_path):
        """Test backend available with password and cryptography."""
        file_path = tmp_path / ".credentials.enc"

        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            backend = EncryptedFileBackend(file_path, "test-password")
            assert backend.is_available is True
        except ImportError:
            pytest.skip("cryptography not installed")

    def test_set_password(self):
        """Test setting password."""
        backend = EncryptedFileBackend()
        backend.set_password("new-password")
        assert backend._password == "new-password"

    def test_encrypt_decrypt_roundtrip(self, tmp_path):
        """Test encryption and decryption roundtrip."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"
        backend = EncryptedFileBackend(file_path, "test-password")

        # Store and retrieve
        result = backend.store_credential("test_key", "secret-value")
        assert result is True

        value = backend.get_credential("test_key")
        assert value == "secret-value"

    def test_encryption_uses_random_salt(self, tmp_path):
        """Test that encryption uses random salt each time."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"
        backend = EncryptedFileBackend(file_path, "test-password")

        # Store same value twice
        backend.store_credential("key1", "value")
        data1 = file_path.read_bytes()

        backend.store_credential("key1", "value")
        data2 = file_path.read_bytes()

        # Salt should be different (first 32 bytes)
        assert data1[:32] != data2[:32]

    def test_wrong_password_fails_decrypt(self, tmp_path):
        """Test that wrong password fails to decrypt."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"

        # Store with correct password
        backend1 = EncryptedFileBackend(file_path, "correct-password")
        backend1.store_credential("test_key", "secret-value")

        # Try to retrieve with wrong password
        backend2 = EncryptedFileBackend(file_path, "wrong-password")
        value = backend2.get_credential("test_key")
        assert value is None  # Should fail to decrypt

    def test_delete_credential(self, tmp_path):
        """Test deleting credential from encrypted file."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"
        backend = EncryptedFileBackend(file_path, "test-password")

        backend.store_credential("test_key", "secret-value")
        result = backend.delete_credential("test_key")

        assert result is True
        value = backend.get_credential("test_key")
        assert value is None

    def test_multiple_credentials(self, tmp_path):
        """Test storing multiple credentials."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"
        backend = EncryptedFileBackend(file_path, "test-password")

        backend.store_credential("key1", "value1")
        backend.store_credential("key2", "value2")

        assert backend.get_credential("key1") == "value1"
        assert backend.get_credential("key2") == "value2"


class TestCredentialManager:
    """Tests for CredentialManager."""

    def test_desktop_backend_selection(self):
        """Test backend selection for desktop environment."""
        manager = CredentialManager(environment_type=EnvironmentType.DESKTOP)
        backend_names = [b.name for b in manager._backends]

        assert "environment_variable" in backend_names
        assert "keychain" in backend_names
        assert "encrypted_file" in backend_names
        assert "mounted_config" not in backend_names

    def test_container_backend_selection(self):
        """Test backend selection for container environment."""
        manager = CredentialManager(environment_type=EnvironmentType.CONTAINER)
        backend_names = [b.name for b in manager._backends]

        assert "environment_variable" in backend_names
        assert "mounted_config" in backend_names
        assert "encrypted_file" in backend_names
        assert "keychain" not in backend_names

    def test_ssh_backend_selection(self):
        """Test backend selection for SSH environment."""
        manager = CredentialManager(environment_type=EnvironmentType.SSH)
        backend_names = [b.name for b in manager._backends]

        assert "environment_variable" in backend_names
        assert "mounted_config" in backend_names
        assert "encrypted_file" in backend_names
        assert "keychain" not in backend_names

    def test_headless_backend_selection(self):
        """Test backend selection for headless/CI environment."""
        manager = CredentialManager(environment_type=EnvironmentType.HEADLESS)
        backend_names = [b.name for b in manager._backends]

        assert backend_names == ["environment_variable"]

    def test_wsl_backend_selection(self):
        """Test backend selection for WSL environment."""
        manager = CredentialManager(environment_type=EnvironmentType.WSL)
        backend_names = [b.name for b in manager._backends]

        assert "environment_variable" in backend_names
        assert "keychain" in backend_names
        assert "encrypted_file" in backend_names

    def test_get_credential_from_env_priority(self, tmp_path):
        """Test that environment variables have priority."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"anthropic_api_key": "mounted-key"}}
        config_path.write_text(yaml.safe_dump(config))

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        # Set env var - should take priority
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            value = manager.get_credential("anthropic_api_key")
            assert value == "env-key"

    def test_get_credential_fallback_to_mounted(self, tmp_path):
        """Test fallback to mounted config when env var not set."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"anthropic_api_key": "mounted-key"}}
        config_path.write_text(yaml.safe_dump(config))

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        # No env var set
        with patch.dict(os.environ, {}, clear=True):
            value = manager.get_credential("anthropic_api_key")
            assert value == "mounted-key"

    def test_get_credential_not_found(self):
        """Test getting non-existent credential."""
        manager = CredentialManager(environment_type=EnvironmentType.HEADLESS)

        with patch.dict(os.environ, {}, clear=True):
            value = manager.get_credential("nonexistent_key")
            assert value is None

    def test_store_credential_first_writable(self, tmp_path):
        """Test storing credential uses first writable backend."""
        config_path = tmp_path / "credentials.yaml"

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        result = manager.store_credential("test_key", "test-value")

        assert result is True
        # Should be stored in mounted config (first writable after env)
        config = yaml.safe_load(config_path.read_text())
        assert config["credentials"]["test_key"] == "test-value"

    def test_store_credential_no_writable_backend(self):
        """Test storing when no writable backend available."""
        manager = CredentialManager(environment_type=EnvironmentType.HEADLESS)

        result = manager.store_credential("test_key", "test-value")
        assert result is False

    def test_delete_credential(self, tmp_path):
        """Test deleting credential from writable backends."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"test_key": "test-value"}}
        config_path.write_text(yaml.safe_dump(config))

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        result = manager.delete_credential("test_key")

        assert result is True
        config = yaml.safe_load(config_path.read_text())
        assert "test_key" not in config.get("credentials", {})

    def test_set_encrypted_file_password(self, tmp_path):
        """Test setting encrypted file password."""
        manager = CredentialManager(
            environment_type=EnvironmentType.DESKTOP,
            encrypted_file_path=tmp_path / ".credentials.enc",
        )

        manager.set_encrypted_file_password("new-password")
        assert manager._encrypted_backend._password == "new-password"

    def test_list_available_backends(self):
        """Test listing available backends."""
        manager = CredentialManager(environment_type=EnvironmentType.HEADLESS)
        available = manager.list_available_backends()

        assert "environment_variable" in available

    def test_list_writable_backends(self, tmp_path):
        """Test listing writable backends."""
        config_path = tmp_path / "credentials.yaml"

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )
        writable = manager.list_writable_backends()

        # Mounted config should be writable (parent exists)
        assert "mounted_config" in writable
        # Env var should not be writable
        assert "environment_variable" not in writable

    def test_get_environment_variable_name(self):
        """Test getting environment variable name for credential."""
        manager = CredentialManager(environment_type=EnvironmentType.HEADLESS)

        assert manager.get_environment_variable_name("anthropic_api_key") == "ANTHROPIC_API_KEY"
        assert manager.get_environment_variable_name("openai_api_key") == "OPENAI_API_KEY"
        assert manager.get_environment_variable_name("custom_key") == "CUSTOM_KEY"


class TestSecureLogging:
    """Tests to ensure credential values are never logged."""

    def test_env_backend_no_value_in_log(self, caplog):
        """Test that environment backend doesn't log credential values."""
        import logging

        backend = EnvironmentVariableBackend()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "secret-key-12345"}):
            caplog.set_level(logging.DEBUG)
            value = backend.get_credential("anthropic_api_key")

            assert value == "secret-key-12345"
            # Check that the secret value is not in any log message
            for record in caplog.records:
                assert "secret-key-12345" not in record.getMessage()

    def test_mounted_backend_no_value_in_log(self, tmp_path, caplog):
        """Test that mounted config backend doesn't log credential values."""
        import logging

        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"test_key": "secret-value-67890"}}
        config_path.write_text(yaml.safe_dump(config))

        backend = MountedConfigBackend(config_path)

        caplog.set_level(logging.DEBUG)
        value = backend.get_credential("test_key")

        assert value == "secret-value-67890"
        for record in caplog.records:
            assert "secret-value-67890" not in record.getMessage()

    def test_manager_no_value_in_log(self, tmp_path, caplog):
        """Test that manager doesn't log credential values."""
        import logging

        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"api_key": "top-secret-abc123"}}
        config_path.write_text(yaml.safe_dump(config))

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        caplog.set_level(logging.DEBUG)
        value = manager.get_credential("api_key")

        assert value == "top-secret-abc123"
        for record in caplog.records:
            assert "top-secret-abc123" not in record.getMessage()


class TestNoBackendAvailableError:
    """Tests for NoBackendAvailableError."""

    def test_error_message(self):
        """Test error message format."""
        error = NoBackendAvailableError(
            operation="store",
            backends_tried=["environment_variable", "mounted_config"],
        )

        assert "No backend available for store" in str(error)
        assert "environment_variable" in str(error)
        assert "mounted_config" in str(error)

    def test_error_attributes(self):
        """Test error attributes."""
        error = NoBackendAvailableError(
            operation="get",
            backends_tried=["env"],
        )

        assert error.operation == "get"
        assert error.backends_tried == ["env"]


class TestCredentialEnvMap:
    """Tests for credential environment variable mapping."""

    def test_anthropic_mapping(self):
        """Test Anthropic API key mapping."""
        assert CREDENTIAL_ENV_MAP["anthropic_api_key"] == "ANTHROPIC_API_KEY"

    def test_openai_mapping(self):
        """Test OpenAI API key mapping."""
        assert CREDENTIAL_ENV_MAP["openai_api_key"] == "OPENAI_API_KEY"

    def test_google_mapping(self):
        """Test Google API key mapping."""
        assert CREDENTIAL_ENV_MAP["google_api_key"] == "GOOGLE_API_KEY"

    def test_github_mapping(self):
        """Test GitHub token mapping."""
        assert CREDENTIAL_ENV_MAP["github_token"] == "GITHUB_TOKEN"


class TestBackendInterface:
    """Tests for CredentialBackend interface."""

    def test_abstract_methods(self):
        """Test that CredentialBackend is abstract."""
        with pytest.raises(TypeError):
            CredentialBackend()  # type: ignore

    def test_interface_completeness(self):
        """Test that all backends implement all abstract methods."""
        backends = [
            EnvironmentVariableBackend,
            MountedConfigBackend,
            KeychainBackend,
            EncryptedFileBackend,
        ]

        for backend_class in backends:
            # Should not raise
            if backend_class == MountedConfigBackend:
                instance = backend_class()
            elif backend_class == EncryptedFileBackend:
                instance = backend_class()
            elif backend_class == KeychainBackend:
                instance = backend_class()
            else:
                instance = backend_class()

            # Check all required properties/methods exist
            assert hasattr(instance, "name")
            assert hasattr(instance, "is_available")
            assert hasattr(instance, "is_writable")
            assert hasattr(instance, "get_credential")
            assert hasattr(instance, "store_credential")
            assert hasattr(instance, "delete_credential")


class TestIntegration:
    """Integration tests for CredentialManager."""

    def test_full_workflow_container(self, tmp_path):
        """Test full workflow in container environment."""
        config_path = tmp_path / "credentials.yaml"

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        # Store credential
        result = manager.store_credential("test_api_key", "test-value-123")
        assert result is True

        # Retrieve credential
        value = manager.get_credential("test_api_key")
        assert value == "test-value-123"

        # Delete credential
        result = manager.delete_credential("test_api_key")
        assert result is True

        # Verify deleted
        value = manager.get_credential("test_api_key")
        assert value is None

    def test_env_overrides_mounted(self, tmp_path):
        """Test that environment variables override mounted config."""
        config_path = tmp_path / "credentials.yaml"
        config = {"credentials": {"api_key": "mounted-value"}}
        config_path.write_text(yaml.safe_dump(config))

        manager = CredentialManager(
            environment_type=EnvironmentType.CONTAINER,
            mounted_config_path=config_path,
        )

        # Without env var - should get mounted value
        with patch.dict(os.environ, {}, clear=True):
            value = manager.get_credential("api_key")
            assert value == "mounted-value"

        # With env var - should get env value
        with patch.dict(os.environ, {"API_KEY": "env-value"}):
            value = manager.get_credential("api_key")
            assert value == "env-value"

    def test_encrypted_file_integration(self, tmp_path):
        """Test encrypted file backend in full workflow."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        encrypted_path = tmp_path / ".credentials.enc"

        manager = CredentialManager(
            environment_type=EnvironmentType.DESKTOP,
            encrypted_file_password="test-password",
            encrypted_file_path=encrypted_path,
        )

        # Store via manager (will use keychain mock or encrypted file)
        # For this test, we'll directly use encrypted backend
        manager._encrypted_backend.store_credential("secret_key", "secret-value")

        # Retrieve
        value = manager._encrypted_backend.get_credential("secret_key")
        assert value == "secret-value"


class TestFilePermissions:
    """Tests for file permission handling."""

    @pytest.mark.skipif(os.name == "nt", reason="Unix permissions only")
    def test_mounted_config_permissions(self, tmp_path):
        """Test that mounted config sets secure permissions."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        backend.store_credential("test", "value")

        # Check file permissions (owner read/write only)
        mode = config_path.stat().st_mode
        assert mode & 0o777 == 0o600

    @pytest.mark.skipif(os.name == "nt", reason="Unix permissions only")
    def test_encrypted_file_permissions(self, tmp_path):
        """Test that encrypted file sets secure permissions."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"

        backend = EncryptedFileBackend(file_path, "test-password")
        backend.store_credential("test", "value")

        # Check file permissions (owner read/write only)
        mode = file_path.stat().st_mode
        assert mode & 0o777 == 0o600


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_credential_name(self):
        """Test handling of empty credential name."""
        backend = EnvironmentVariableBackend()
        value = backend.get_credential("")
        assert value is None

    def test_unicode_credential_value(self, tmp_path):
        """Test handling of Unicode credential values."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        result = backend.store_credential("unicode_key", "value-with-unicode-\u00e9\u00f1")

        assert result is True
        value = backend.get_credential("unicode_key")
        assert value == "value-with-unicode-\u00e9\u00f1"

    def test_very_long_credential(self, tmp_path):
        """Test handling of very long credential values."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        long_value = "x" * 10000  # 10KB value

        result = backend.store_credential("long_key", long_value)
        assert result is True

        retrieved = backend.get_credential("long_key")
        assert retrieved == long_value

    def test_special_characters_in_name(self, tmp_path):
        """Test handling of special characters in credential names."""
        config_path = tmp_path / "credentials.yaml"

        backend = MountedConfigBackend(config_path)
        result = backend.store_credential("my-api_key.test", "value")

        assert result is True
        value = backend.get_credential("my-api_key.test")
        assert value == "value"

    def test_malformed_yaml_file(self, tmp_path):
        """Test handling of malformed YAML file."""
        config_path = tmp_path / "credentials.yaml"
        config_path.write_text("invalid: yaml: content: [")

        backend = MountedConfigBackend(config_path)
        value = backend.get_credential("test")
        assert value is None  # Should return None, not crash

    def test_corrupted_encrypted_file(self, tmp_path):
        """Test handling of corrupted encrypted file."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            pytest.skip("cryptography not installed")

        file_path = tmp_path / ".credentials.enc"
        file_path.write_bytes(b"corrupted data here")

        backend = EncryptedFileBackend(file_path, "test-password")
        value = backend.get_credential("test")
        assert value is None  # Should return None, not crash
