# Story 41.4: CredentialManager with Environment-First Storage

## User Story

As a developer deploying GAO-Dev in Docker or CI/CD,
I want credentials to be read from environment variables first,
So that I can follow security best practices and avoid storing secrets in files.

## Acceptance Criteria

- [ ] AC1: CredentialManager checks environment variables as PRIMARY source
- [ ] AC2: Falls back to mounted config file (`~/.gao-dev/credentials.yaml`) as secondary
- [ ] AC3: Falls back to system keychain (Keychain/Credential Manager/SecretService) as tertiary
- [ ] AC4: Falls back to encrypted file with user password as last resort
- [ ] AC5: Backend selection is based on detected environment (container vs desktop)
- [ ] AC6: `get_credential()` tries backends in priority order until found
- [ ] AC7: `store_credential()` stores in first available writable backend
- [ ] AC8: Credentials never written to git-tracked files
- [ ] AC9: Encrypted file uses AES-256-GCM with PBKDF2 key derivation (600,000 iterations)
- [ ] AC10: Environment variable names follow pattern: `{PROVIDER}_API_KEY`
- [ ] AC11: Clear error messages when no backend can store credentials
- [ ] AC12: Logging never includes actual credential values

## Technical Notes

### Implementation Details

Create `gao_dev/core/credential_manager.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional, List
import os
from pathlib import Path

class CredentialBackend(ABC):
    """Abstract base for credential storage backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieve credential by key."""
        pass

    @abstractmethod
    def store(self, key: str, value: str) -> bool:
        """Store credential. Returns True on success."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available in current environment."""
        pass

    @abstractmethod
    def is_writable(self) -> bool:
        """Check if backend can store new credentials."""
        pass

class EnvironmentVariableBackend(CredentialBackend):
    """Read credentials from environment variables."""

    def get(self, key: str) -> Optional[str]:
        env_var = self._key_to_env_var(key)
        return os.getenv(env_var)

    def _key_to_env_var(self, key: str) -> str:
        # anthropic_api_key -> ANTHROPIC_API_KEY
        return key.upper()

class MountedConfigBackend(CredentialBackend):
    """Read/write credentials from mounted config file."""
    pass

class KeychainBackend(CredentialBackend):
    """System keychain (macOS/Windows/Linux)."""
    pass

class EncryptedFileBackend(CredentialBackend):
    """Encrypted file fallback with user password."""
    pass

class CredentialManager:
    """Manages credential storage across multiple backends."""

    def __init__(self, environment: EnvironmentType):
        self.backends = self._select_backends(environment)

    def get_credential(self, key: str) -> Optional[str]:
        """Try each backend in priority order."""
        for backend in self.backends:
            if value := backend.get(key):
                return value
        return None

    def store_credential(self, key: str, value: str) -> bool:
        """Store in first available writable backend."""
        for backend in self.backends:
            if backend.is_available() and backend.is_writable():
                return backend.store(key, value)
        return False
```

### Backend Selection by Environment

| Environment | Backends (in order) |
|-------------|---------------------|
| Desktop | EnvVar, Keychain, EncryptedFile |
| Container | EnvVar, MountedConfig, EncryptedFile |
| SSH | EnvVar, MountedConfig, EncryptedFile |
| CI/CD | EnvVar only |

### Environment Variable Mapping

| Provider | Environment Variable |
|----------|---------------------|
| Claude/Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| OpenCode | `OPENCODE_API_KEY` |
| Ollama | N/A (local) |

### Encrypted File Specification

- Algorithm: AES-256-GCM (authenticated encryption)
- Key derivation: PBKDF2-SHA256
- Iterations: 600,000 (OWASP 2023 recommendation)
- Salt: 32 bytes, randomly generated per file
- Nonce: 12 bytes, randomly generated per encryption
- Location: `~/.gao-dev/.credentials.enc` (dotfile, not tracked)

## Test Scenarios

1. **Environment variable priority**: Given `$ANTHROPIC_API_KEY` set, When `get_credential("anthropic_api_key")` called, Then returns env var value without checking other backends

2. **Mounted config fallback**: Given no env var but mounted config exists, When `get_credential()` called, Then returns value from config file

3. **Keychain fallback**: Given desktop environment with no env var or config, When `get_credential()` called, Then returns value from keychain

4. **Store to first writable**: Given desktop environment, When `store_credential()` called, Then stores to keychain (first writable)

5. **Container backend selection**: Given container environment, When CredentialManager initialized, Then backends are [EnvVar, MountedConfig, EncryptedFile]

6. **Encrypted file password**: Given encrypted file backend, When `store_credential()` called, Then prompts for password

7. **No backend available**: Given CI/CD with no env vars, When `get_credential()` called, Then returns None

8. **Secure logging**: Given any credential operation, When logged, Then actual values are never in logs

9. **Encryption security**: Given encrypted file created, When inspected, Then content is not readable without password

10. **Key derivation**: Given password "test", When key derived, Then uses 600,000 PBKDF2 iterations

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for each backend
- [ ] Security review for encryption implementation
- [ ] Cross-platform testing (keychain on all OS)
- [ ] Code reviewed
- [ ] Documentation updated with security notes
- [ ] Type hints complete (no `Any`)

## Story Points: 8

## Dependencies

- Story 40.1: Environment Detection (for environment-aware backend selection)
- `keyring` library (for system keychain)
- `cryptography` library (for AES encryption)

## Notes

- Never log actual credential values (use "***" placeholder)
- Consider using `secrets` module for secure comparison
- Test keychain failure scenarios (locked keychain, permission denied)
- Encrypted file password is NOT stored - user must provide each time
- Document the security model in user documentation
- Consider credential rotation/expiry features for future enhancement
