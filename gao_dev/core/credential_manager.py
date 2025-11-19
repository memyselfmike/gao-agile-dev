"""Credential management with environment-first storage.

This module provides secure credential storage with multiple backends and
environment-first priority for API key management.

Epic 41: Streamlined Onboarding
Story 41.4: CredentialManager with Environment-First Storage

Backends (in priority order):
1. Environment variables (PRIMARY - always checked first)
2. Mounted config file (~/.gao-dev/credentials.yaml) - for containers
3. System keychain (Keychain/Credential Manager/SecretService) - for desktop
4. Encrypted file with AES-256-GCM - last resort

Security:
- Credentials NEVER written to git-tracked files
- Logging NEVER includes actual credential values
- Encrypted files use AES-256-GCM with PBKDF2 (600,000 iterations)
"""

import base64
import os
import platform
import stat
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import structlog
import yaml

from gao_dev.core.environment_detector import EnvironmentType, detect_environment

logger = structlog.get_logger()

# Credential name to environment variable mapping
CREDENTIAL_ENV_MAP = {
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "google_api_key": "GOOGLE_API_KEY",
    "github_token": "GITHUB_TOKEN",
    "opencode_api_key": "OPENCODE_API_KEY",
}


class CredentialBackend(ABC):
    """Abstract base class for credential storage backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name for logging."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available in the current environment."""
        pass

    @property
    @abstractmethod
    def is_writable(self) -> bool:
        """Check if this backend supports writing credentials."""
        pass

    @abstractmethod
    def get_credential(self, name: str) -> Optional[str]:
        """Get credential by name.

        Args:
            name: Credential name (e.g., 'anthropic_api_key')

        Returns:
            Credential value or None if not found
        """
        pass

    @abstractmethod
    def store_credential(self, name: str, value: str) -> bool:
        """Store credential.

        Args:
            name: Credential name
            value: Credential value

        Returns:
            True if stored successfully, False otherwise
        """
        pass

    @abstractmethod
    def delete_credential(self, name: str) -> bool:
        """Delete credential.

        Args:
            name: Credential name

        Returns:
            True if deleted successfully, False otherwise
        """
        pass


class EnvironmentVariableBackend(CredentialBackend):
    """Backend that reads credentials from environment variables.

    This is always the PRIMARY backend - environment variables take precedence.
    Environment variable names follow pattern: {PROVIDER}_API_KEY

    Example:
        anthropic_api_key -> ANTHROPIC_API_KEY
        openai_api_key -> OPENAI_API_KEY
    """

    @property
    def name(self) -> str:
        return "environment_variable"

    @property
    def is_available(self) -> bool:
        return True  # Always available

    @property
    def is_writable(self) -> bool:
        return False  # Cannot write to env vars from Python

    def get_credential(self, name: str) -> Optional[str]:
        """Get credential from environment variable."""
        env_var = CREDENTIAL_ENV_MAP.get(name)
        if not env_var:
            # Try to construct the env var name
            env_var = name.upper()

        value = os.environ.get(env_var)
        if value:
            logger.debug(
                "credential_retrieved",
                backend=self.name,
                credential_name=name,
                env_var=env_var,
            )
        return value

    def store_credential(self, name: str, value: str) -> bool:
        """Cannot store credentials in environment variables."""
        logger.debug(
            "store_not_supported",
            backend=self.name,
            credential_name=name,
        )
        return False

    def delete_credential(self, name: str) -> bool:
        """Cannot delete credentials from environment variables."""
        logger.debug(
            "delete_not_supported",
            backend=self.name,
            credential_name=name,
        )
        return False


class MountedConfigBackend(CredentialBackend):
    """Backend that reads/writes credentials from mounted YAML config file.

    Ideal for container environments where credentials are mounted.
    Location: ~/.gao-dev/credentials.yaml

    File format:
        credentials:
          anthropic_api_key: sk-ant-...
          openai_api_key: sk-...
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with config file path.

        Args:
            config_path: Path to credentials.yaml (defaults to ~/.gao-dev/credentials.yaml)
        """
        if config_path:
            self._config_path = config_path
        else:
            self._config_path = Path.home() / ".gao-dev" / "credentials.yaml"
        self._logger = logger.bind(backend="mounted_config")

    @property
    def name(self) -> str:
        return "mounted_config"

    @property
    def is_available(self) -> bool:
        """Check if config file exists and is readable."""
        return self._config_path.exists() and os.access(self._config_path, os.R_OK)

    @property
    def is_writable(self) -> bool:
        """Check if config file or parent directory is writable."""
        if self._config_path.exists():
            return os.access(self._config_path, os.W_OK)
        # Check if parent directory is writable
        parent = self._config_path.parent
        return parent.exists() and os.access(parent, os.W_OK)

    def _load_config(self) -> dict:
        """Load config file.

        Returns:
            Config dict or empty dict if file doesn't exist
        """
        if not self._config_path.exists():
            return {}

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except (OSError, yaml.YAMLError) as e:
            self._logger.warning(
                "config_load_failed",
                path=str(self._config_path),
                error=str(e),
            )
            return {}

    def _save_config(self, config: dict) -> bool:
        """Save config file with secure permissions.

        Args:
            config: Config dict to save

        Returns:
            True if saved successfully
        """
        try:
            # Ensure parent directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(self._config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            # Set secure permissions (owner read/write only)
            if platform.system() != "Windows":
                os.chmod(self._config_path, stat.S_IRUSR | stat.S_IWUSR)

            self._logger.debug("config_saved", path=str(self._config_path))
            return True

        except OSError as e:
            self._logger.error(
                "config_save_failed",
                path=str(self._config_path),
                error=str(e),
            )
            return False

    def get_credential(self, name: str) -> Optional[str]:
        """Get credential from config file."""
        config = self._load_config()
        credentials = config.get("credentials", {})
        value = credentials.get(name)

        if value:
            self._logger.debug(
                "credential_retrieved",
                backend=self.name,
                credential_name=name,
            )
        return value

    def store_credential(self, name: str, value: str) -> bool:
        """Store credential in config file."""
        config = self._load_config()
        if "credentials" not in config:
            config["credentials"] = {}

        config["credentials"][name] = value

        if self._save_config(config):
            self._logger.info(
                "credential_stored",
                backend=self.name,
                credential_name=name,
            )
            return True
        return False

    def delete_credential(self, name: str) -> bool:
        """Delete credential from config file."""
        config = self._load_config()
        credentials = config.get("credentials", {})

        if name in credentials:
            del credentials[name]
            if self._save_config(config):
                self._logger.info(
                    "credential_deleted",
                    backend=self.name,
                    credential_name=name,
                )
                return True
        return False


class KeychainBackend(CredentialBackend):
    """Backend that uses system keychain.

    Uses the keyring library to access:
    - macOS: Keychain
    - Windows: Credential Manager
    - Linux: Secret Service (GNOME Keyring, KWallet)

    Service name: gao-dev
    """

    SERVICE_NAME = "gao-dev"

    def __init__(self):
        """Initialize keychain backend."""
        self._logger = logger.bind(backend="keychain")
        self._keyring_available: Optional[bool] = None

    @property
    def name(self) -> str:
        return "keychain"

    def _check_keyring(self) -> bool:
        """Check if keyring library is available and functional.

        Returns:
            True if keyring is available and working
        """
        if self._keyring_available is not None:
            return self._keyring_available

        try:
            import keyring
            from keyring.errors import NoKeyringError

            # Try to get the current keyring backend
            backend = keyring.get_keyring()
            if backend is None:
                self._keyring_available = False
            else:
                # Check it's not the fail backend
                backend_name = type(backend).__name__
                self._keyring_available = "Fail" not in backend_name
                self._logger.debug(
                    "keyring_detected",
                    backend=backend_name,
                    available=self._keyring_available,
                )

        except ImportError:
            self._logger.debug("keyring_not_installed")
            self._keyring_available = False
        except NoKeyringError:
            self._logger.debug("no_keyring_backend")
            self._keyring_available = False
        except Exception as e:
            self._logger.debug("keyring_check_failed", error=str(e))
            self._keyring_available = False

        return self._keyring_available

    @property
    def is_available(self) -> bool:
        """Check if keychain is available."""
        return self._check_keyring()

    @property
    def is_writable(self) -> bool:
        """Keychain is writable if available."""
        return self._check_keyring()

    def get_credential(self, name: str) -> Optional[str]:
        """Get credential from system keychain."""
        if not self._check_keyring():
            return None

        try:
            import keyring

            value = keyring.get_password(self.SERVICE_NAME, name)
            if value:
                self._logger.debug(
                    "credential_retrieved",
                    backend=self.name,
                    credential_name=name,
                )
            return value

        except Exception as e:
            self._logger.warning(
                "keychain_get_failed",
                credential_name=name,
                error=str(e),
            )
            return None

    def store_credential(self, name: str, value: str) -> bool:
        """Store credential in system keychain."""
        if not self._check_keyring():
            return False

        try:
            import keyring

            keyring.set_password(self.SERVICE_NAME, name, value)
            self._logger.info(
                "credential_stored",
                backend=self.name,
                credential_name=name,
            )
            return True

        except Exception as e:
            self._logger.error(
                "keychain_store_failed",
                credential_name=name,
                error=str(e),
            )
            return False

    def delete_credential(self, name: str) -> bool:
        """Delete credential from system keychain."""
        if not self._check_keyring():
            return False

        try:
            import keyring

            keyring.delete_password(self.SERVICE_NAME, name)
            self._logger.info(
                "credential_deleted",
                backend=self.name,
                credential_name=name,
            )
            return True

        except Exception as e:
            self._logger.warning(
                "keychain_delete_failed",
                credential_name=name,
                error=str(e),
            )
            return False


class EncryptedFileBackend(CredentialBackend):
    """Backend that uses encrypted file storage.

    Encryption: AES-256-GCM (authenticated encryption)
    Key derivation: PBKDF2-SHA256 with 600,000 iterations
    Salt: 32 bytes, stored with encrypted data
    Location: ~/.gao-dev/.credentials.enc

    This is the last resort backend when keychain is unavailable.
    Requires user password for encryption/decryption.
    """

    ITERATIONS = 600_000
    SALT_LENGTH = 32
    NONCE_LENGTH = 12

    def __init__(
        self,
        file_path: Optional[Path] = None,
        password: Optional[str] = None,
    ):
        """Initialize encrypted file backend.

        Args:
            file_path: Path to encrypted file (defaults to ~/.gao-dev/.credentials.enc)
            password: Encryption password (if not provided, will prompt)
        """
        if file_path:
            self._file_path = file_path
        else:
            self._file_path = Path.home() / ".gao-dev" / ".credentials.enc"
        self._password = password
        self._logger = logger.bind(backend="encrypted_file")
        self._cryptography_available: Optional[bool] = None

    @property
    def name(self) -> str:
        return "encrypted_file"

    def _check_cryptography(self) -> bool:
        """Check if cryptography library is available.

        Returns:
            True if cryptography is available
        """
        if self._cryptography_available is not None:
            return self._cryptography_available

        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

            self._cryptography_available = True
        except ImportError:
            self._logger.debug("cryptography_not_installed")
            self._cryptography_available = False

        return self._cryptography_available

    @property
    def is_available(self) -> bool:
        """Check if encrypted file backend is available."""
        if not self._check_cryptography():
            return False
        # Also need password
        return self._password is not None

    @property
    def is_writable(self) -> bool:
        """Check if encrypted file can be written."""
        if not self._check_cryptography() or not self._password:
            return False
        # Check if parent directory is writable
        parent = self._file_path.parent
        if self._file_path.exists():
            return os.access(self._file_path, os.W_OK)
        return parent.exists() and os.access(parent, os.W_OK)

    def set_password(self, password: str) -> None:
        """Set the encryption password.

        Args:
            password: Encryption password
        """
        self._password = password

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2.

        Args:
            password: User password
            salt: Salt bytes

        Returns:
            32-byte derived key
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend(),
        )
        return kdf.derive(password.encode("utf-8"))

    def _encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data with AES-256-GCM.

        Returns:
            salt (32) + nonce (12) + ciphertext
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if not self._password:
            raise ValueError("Password not set")

        salt = os.urandom(self.SALT_LENGTH)
        nonce = os.urandom(self.NONCE_LENGTH)
        key = self._derive_key(self._password, salt)

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return salt + nonce + ciphertext

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt data with AES-256-GCM.

        Args:
            data: salt (32) + nonce (12) + ciphertext

        Returns:
            Decrypted plaintext
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if not self._password:
            raise ValueError("Password not set")

        salt = data[: self.SALT_LENGTH]
        nonce = data[self.SALT_LENGTH : self.SALT_LENGTH + self.NONCE_LENGTH]
        ciphertext = data[self.SALT_LENGTH + self.NONCE_LENGTH :]

        key = self._derive_key(self._password, salt)
        aesgcm = AESGCM(key)

        return aesgcm.decrypt(nonce, ciphertext, None)

    def _load_credentials(self) -> dict:
        """Load and decrypt credentials file.

        Returns:
            Credentials dict or empty dict
        """
        if not self._file_path.exists():
            return {}

        try:
            with open(self._file_path, "rb") as f:
                encrypted = f.read()

            plaintext = self._decrypt(encrypted)
            data = yaml.safe_load(plaintext.decode("utf-8"))
            return data if data else {}

        except Exception as e:
            self._logger.warning(
                "decrypt_failed",
                path=str(self._file_path),
                error=str(e),
            )
            return {}

    def _save_credentials(self, credentials: dict) -> bool:
        """Encrypt and save credentials file.

        Args:
            credentials: Credentials dict

        Returns:
            True if saved successfully
        """
        try:
            # Ensure parent directory exists
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            plaintext = yaml.safe_dump(credentials).encode("utf-8")
            encrypted = self._encrypt(plaintext)

            with open(self._file_path, "wb") as f:
                f.write(encrypted)

            # Set secure permissions (owner read/write only)
            if platform.system() != "Windows":
                os.chmod(self._file_path, stat.S_IRUSR | stat.S_IWUSR)

            self._logger.debug("credentials_saved", path=str(self._file_path))
            return True

        except Exception as e:
            self._logger.error(
                "save_failed",
                path=str(self._file_path),
                error=str(e),
            )
            return False

    def get_credential(self, name: str) -> Optional[str]:
        """Get credential from encrypted file."""
        if not self.is_available:
            return None

        credentials = self._load_credentials()
        value = credentials.get(name)

        if value:
            self._logger.debug(
                "credential_retrieved",
                backend=self.name,
                credential_name=name,
            )
        return value

    def store_credential(self, name: str, value: str) -> bool:
        """Store credential in encrypted file."""
        if not self.is_writable:
            return False

        credentials = self._load_credentials()
        credentials[name] = value

        if self._save_credentials(credentials):
            self._logger.info(
                "credential_stored",
                backend=self.name,
                credential_name=name,
            )
            return True
        return False

    def delete_credential(self, name: str) -> bool:
        """Delete credential from encrypted file."""
        if not self.is_writable:
            return False

        credentials = self._load_credentials()
        if name in credentials:
            del credentials[name]
            if self._save_credentials(credentials):
                self._logger.info(
                    "credential_deleted",
                    backend=self.name,
                    credential_name=name,
                )
                return True
        return False


class CredentialManager:
    """Manage credentials with environment-first priority.

    Coordinates multiple backends and selects appropriate ones based on
    detected environment:

    Desktop: EnvVar -> Keychain -> EncryptedFile
    Container/SSH: EnvVar -> MountedConfig -> EncryptedFile
    Headless/CI: EnvVar only

    Example:
        ```python
        manager = CredentialManager()

        # Get credential (tries backends in priority order)
        api_key = manager.get_credential("anthropic_api_key")

        # Store credential (uses first writable backend)
        manager.store_credential("anthropic_api_key", "sk-ant-...")
        ```
    """

    def __init__(
        self,
        environment_type: Optional[EnvironmentType] = None,
        encrypted_file_password: Optional[str] = None,
        mounted_config_path: Optional[Path] = None,
        encrypted_file_path: Optional[Path] = None,
    ):
        """Initialize credential manager.

        Args:
            environment_type: Override detected environment
            encrypted_file_password: Password for encrypted file backend
            mounted_config_path: Override mounted config path
            encrypted_file_path: Override encrypted file path
        """
        self._logger = logger.bind(component="credential_manager")

        # Detect or use provided environment
        if environment_type:
            self._env_type = environment_type
        else:
            self._env_type = detect_environment()

        self._logger.debug("environment_detected", type=self._env_type.value)

        # Initialize backends
        self._env_backend = EnvironmentVariableBackend()
        self._mounted_backend = MountedConfigBackend(mounted_config_path)
        self._keychain_backend = KeychainBackend()
        self._encrypted_backend = EncryptedFileBackend(
            encrypted_file_path,
            encrypted_file_password,
        )

        # Select backends based on environment
        self._backends = self._select_backends()
        self._logger.info(
            "backends_selected",
            backends=[b.name for b in self._backends],
            environment=self._env_type.value,
        )

    def _select_backends(self) -> list[CredentialBackend]:
        """Select backends based on environment type.

        Returns:
            List of backends in priority order
        """
        # Environment variables always first
        backends: list[CredentialBackend] = [self._env_backend]

        if self._env_type == EnvironmentType.HEADLESS:
            # CI/CD: Only environment variables
            pass
        elif self._env_type in (EnvironmentType.CONTAINER, EnvironmentType.SSH):
            # Container/SSH: EnvVar -> MountedConfig -> EncryptedFile
            backends.append(self._mounted_backend)
            backends.append(self._encrypted_backend)
        else:
            # Desktop/WSL/Remote: EnvVar -> Keychain -> EncryptedFile
            backends.append(self._keychain_backend)
            backends.append(self._encrypted_backend)

        return backends

    def get_credential(self, name: str) -> Optional[str]:
        """Get credential by trying backends in priority order.

        Args:
            name: Credential name (e.g., 'anthropic_api_key')

        Returns:
            Credential value or None if not found in any backend
        """
        self._logger.debug("getting_credential", credential_name=name)

        for backend in self._backends:
            if not backend.is_available:
                self._logger.debug(
                    "backend_unavailable",
                    backend=backend.name,
                    credential_name=name,
                )
                continue

            value = backend.get_credential(name)
            if value:
                self._logger.info(
                    "credential_found",
                    backend=backend.name,
                    credential_name=name,
                )
                return value

        self._logger.warning(
            "credential_not_found",
            credential_name=name,
            backends_tried=[b.name for b in self._backends],
        )
        return None

    def store_credential(self, name: str, value: str) -> bool:
        """Store credential in first available writable backend.

        Args:
            name: Credential name
            value: Credential value

        Returns:
            True if stored successfully, False if no writable backend available
        """
        self._logger.debug("storing_credential", credential_name=name)

        for backend in self._backends:
            if not backend.is_writable:
                self._logger.debug(
                    "backend_not_writable",
                    backend=backend.name,
                    credential_name=name,
                )
                continue

            if backend.store_credential(name, value):
                self._logger.info(
                    "credential_stored",
                    backend=backend.name,
                    credential_name=name,
                )
                return True

        self._logger.error(
            "no_writable_backend",
            credential_name=name,
            backends_tried=[b.name for b in self._backends],
        )
        return False

    def delete_credential(self, name: str) -> bool:
        """Delete credential from all backends that have it.

        Args:
            name: Credential name

        Returns:
            True if deleted from at least one backend
        """
        self._logger.debug("deleting_credential", credential_name=name)
        deleted = False

        for backend in self._backends:
            if backend.is_writable and backend.delete_credential(name):
                deleted = True

        if deleted:
            self._logger.info("credential_deleted", credential_name=name)
        else:
            self._logger.warning("credential_delete_failed", credential_name=name)

        return deleted

    def set_encrypted_file_password(self, password: str) -> None:
        """Set password for encrypted file backend.

        Args:
            password: Encryption password
        """
        self._encrypted_backend.set_password(password)
        self._logger.debug("encrypted_file_password_set")

    def list_available_backends(self) -> list[str]:
        """List available backends.

        Returns:
            List of available backend names
        """
        return [b.name for b in self._backends if b.is_available]

    def list_writable_backends(self) -> list[str]:
        """List writable backends.

        Returns:
            List of writable backend names
        """
        return [b.name for b in self._backends if b.is_writable]

    def get_environment_variable_name(self, credential_name: str) -> str:
        """Get the environment variable name for a credential.

        Args:
            credential_name: Credential name (e.g., 'anthropic_api_key')

        Returns:
            Environment variable name (e.g., 'ANTHROPIC_API_KEY')
        """
        return CREDENTIAL_ENV_MAP.get(credential_name, credential_name.upper())


class CredentialError(Exception):
    """Raised when credential operations fail."""

    pass


class NoBackendAvailableError(CredentialError):
    """Raised when no backend is available for the operation."""

    def __init__(self, operation: str, backends_tried: list[str]):
        self.operation = operation
        self.backends_tried = backends_tried
        message = (
            f"No backend available for {operation}. "
            f"Backends tried: {', '.join(backends_tried)}. "
            "Please set credentials via environment variables or configure a storage backend."
        )
        super().__init__(message)
