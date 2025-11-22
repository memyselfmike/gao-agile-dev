# Architecture Document: Streamlined Startup & Web-Based Onboarding

**Author**: Winston (Technical Architect Agent)
**Date**: 2025-11-19
**Status**: Draft
**Version**: 1.0

---

## Overview

This document defines the technical architecture for the Streamlined Onboarding feature, with particular focus on Docker deployment, headless environments, and credential security.

---

## Design Principles

1. **Environment-aware** - Auto-detect and adapt to deployment context (Docker, SSH, WSL, desktop)
2. **Credentials via environment** - Environment variables are the PRIMARY credential mechanism
3. **Graceful degradation** - Always provide a working path, even in constrained environments
4. **Zero mandatory GUI** - Full functionality available without browser/display server
5. **Stateless-friendly** - Work well in ephemeral containers with mounted config

---

## Environment Detection

### Detection Matrix

The system detects two orthogonal dimensions:

**Dimension 1: Global State (User History)**
| State | Indicator | Implication |
|-------|-----------|-------------|
| First-time | No `~/.gao-dev/` | Need full onboarding |
| Returning | Has `~/.gao-dev/config.yaml` | Can use saved preferences |

**Dimension 2: Project State (Current Directory)**
| State | Indicator | Implication |
|-------|-----------|-------------|
| Empty | No files | Greenfield project |
| Code only | Has code, no `.gao-dev/` | Brownfield project |
| GAO-Dev project | Has `.gao-dev/` | Skip project init |

**Dimension 3: Environment Type (Runtime Context)**
| Environment | Detection Method | Default Mode |
|-------------|------------------|--------------|
| Desktop GUI | `$DISPLAY` set (Linux/Mac) or always (Windows) | Web wizard |
| SSH session | `$SSH_CLIENT` or `$SSH_TTY` set | TUI wizard |
| Docker container | `/.dockerenv` exists or `$GAO_DEV_DOCKER=1` | TUI wizard |
| WSL | `/proc/version` contains "Microsoft" | TUI wizard |
| CI/CD | `$CI=true` or `$GAO_DEV_HEADLESS=1` | No wizard (env vars only) |
| VS Code Remote | `$VSCODE_IPC_HOOK_CLI` set | TUI wizard |

### Detection Priority

```python
def detect_environment() -> EnvironmentType:
    # Explicit override always wins
    if os.getenv('GAO_DEV_HEADLESS'):
        return EnvironmentType.HEADLESS

    if os.getenv('GAO_DEV_GUI'):
        return EnvironmentType.DESKTOP

    # CI/CD detection
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or os.getenv('GITLAB_CI'):
        return EnvironmentType.HEADLESS

    # Container detection
    if Path('/.dockerenv').exists() or os.getenv('GAO_DEV_DOCKER'):
        return EnvironmentType.CONTAINER

    # Remote development detection
    if os.getenv('SSH_CLIENT') or os.getenv('SSH_TTY'):
        return EnvironmentType.SSH

    if os.getenv('VSCODE_IPC_HOOK_CLI'):
        return EnvironmentType.REMOTE_DEV

    # WSL detection
    if Path('/proc/version').exists():
        with open('/proc/version') as f:
            if 'microsoft' in f.read().lower():
                return EnvironmentType.WSL

    # Desktop detection
    if sys.platform == 'win32':
        return EnvironmentType.DESKTOP

    if os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY'):
        return EnvironmentType.DESKTOP

    # Default to TUI for safety
    return EnvironmentType.HEADLESS
```

---

## Credential Storage Architecture

### Storage Priority (Highest to Lowest)

1. **Environment Variables** (PRIMARY)
   - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.
   - `AGENT_PROVIDER` for provider selection
   - Most secure (per-process, not persisted)
   - Required for Docker/CI/CD
   - **This is the recommended approach**

2. **Mounted Config File** (Docker-friendly)
   - Mount `~/.gao-dev/` as volume in Docker
   - Config persists across container restarts
   - Keys stored in `credentials.yaml` (not git-tracked)

3. **System Keychain** (Desktop convenience)
   - macOS Keychain, Windows Credential Manager, Linux SecretService
   - Only available on desktop with GUI
   - Convenient for developers on local machines

4. **Encrypted File Fallback** (Last resort)
   - Only when keychain unavailable AND no env vars
   - Requires user-provided password on each start
   - Uses AES-256-GCM with PBKDF2 key derivation

### Credential Manager Interface

```python
class CredentialManager:
    """Abstract credential storage with environment-aware backend selection."""

    def __init__(self, environment: EnvironmentType):
        self.backends = self._select_backends(environment)

    def _select_backends(self, env: EnvironmentType) -> List[CredentialBackend]:
        """Select backends based on environment, in priority order."""
        backends = [EnvironmentVariableBackend()]  # Always first

        if env == EnvironmentType.DESKTOP:
            backends.append(KeychainBackend())

        if env in (EnvironmentType.CONTAINER, EnvironmentType.SSH):
            backends.append(MountedConfigBackend())

        backends.append(EncryptedFileBackend())  # Always last resort

        return backends

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

### Encrypted File Specification

When encrypted file fallback is used:

```python
class EncryptedFileBackend:
    """
    Encrypted credential storage for environments without keychain.

    Security properties:
    - Algorithm: AES-256-GCM (authenticated encryption)
    - Key derivation: PBKDF2-SHA256, 600,000 iterations
    - Salt: 32 bytes, randomly generated per file
    - Nonce: 12 bytes, randomly generated per encryption

    User must provide password on each start (not stored).
    """

    ITERATIONS = 600_000  # OWASP 2023 recommendation

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str, password: str) -> bytes:
        salt = os.urandom(32)
        nonce = os.urandom(12)
        key = self._derive_key(password, salt)

        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)

        # Format: salt (32) + nonce (12) + ciphertext (variable)
        return salt + nonce + ciphertext
```

### Docker Deployment Pattern

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install GAO-Dev
RUN pip install gao-dev

# Create mount point for persistent config
RUN mkdir -p /root/.gao-dev
VOLUME /root/.gao-dev

# Default to headless mode
ENV GAO_DEV_DOCKER=1

WORKDIR /workspace
ENTRYPOINT ["gao-dev"]
CMD ["start"]
```

```yaml
# docker-compose.yml
services:
  gao-dev:
    build: .
    volumes:
      - ./project:/workspace
      - gao-dev-config:/root/.gao-dev
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AGENT_PROVIDER=claude-code
    ports:
      - "3000:3000"

volumes:
  gao-dev-config:
```

---

## Startup Flow Architecture

### State Machine

```
                    +------------------+
                    |   gao-dev start  |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Detect Environment|
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
        +-----v-----+  +-----v-----+  +-----v-----+
        |  Desktop  |  |  Docker/  |  |   CI/CD   |
        |    GUI    |  |  SSH/WSL  |  | Headless  |
        +-----+-----+  +-----+-----+  +-----+-----+
              |              |              |
              v              v              v
        +----------+   +----------+   +----------+
        |   Web    |   |   TUI    |   |   Env    |
        |  Wizard  |   |  Wizard  |   | Vars Only|
        +----+-----+   +----+-----+   +----+-----+
              |              |              |
              +--------------+--------------+
                             |
                    +--------v---------+
                    | Load/Create Config|
                    +--------+---------+
                             |
                    +--------v---------+
                    |  Validate Creds  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
        +-----v-----+  +-----v-----+  +-----v-----+
        |   Valid   |  |  Invalid  |  |  Missing  |
        +-----------+  +-----+-----+  +-----+-----+
                             |              |
                       +-----v-----+  +-----v-----+
                       |Show Error |  |  Prompt   |
                       |with Fix   |  | for Input |
                       +-----------+  +-----------+
                             |              |
              +--------------+--------------+
                             |
                    +--------v---------+
                    |  Initialize Proj |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Start Brian    |
                    +------------------+
```

### Startup Orchestrator

```python
class StartupOrchestrator:
    """
    Coordinates the entire startup flow based on environment detection.
    """

    def __init__(self):
        self.environment = detect_environment()
        self.credential_manager = CredentialManager(self.environment)
        self.config_manager = ConfigManager()

    async def start(self, project_path: Optional[Path] = None) -> None:
        # Phase 1: Determine context
        global_state = self._detect_global_state()
        project_state = self._detect_project_state(project_path or Path.cwd())

        # Phase 2: Determine required onboarding
        needs_onboarding = self._needs_onboarding(global_state, project_state)

        # Phase 3: Run appropriate wizard or skip
        if needs_onboarding:
            config = await self._run_onboarding()
        else:
            config = self.config_manager.load()

        # Phase 4: Validate credentials
        if not self._validate_credentials(config):
            await self._handle_invalid_credentials(config)

        # Phase 5: Initialize project if needed
        if project_state != ProjectState.GAO_DEV_PROJECT:
            await self._initialize_project(config)

        # Phase 6: Launch interface
        await self._launch_interface(config)

    async def _run_onboarding(self) -> Config:
        """Run environment-appropriate onboarding wizard."""
        if self.environment == EnvironmentType.HEADLESS:
            return self._load_from_environment()
        elif self.environment == EnvironmentType.DESKTOP:
            return await self._run_web_wizard()
        else:  # Docker, SSH, WSL, Remote
            return await self._run_tui_wizard()
```

### Web Server Bootstrap Mode

The web server can start without a project context for onboarding:

```python
class WebServer:
    """
    FastAPI server that supports two modes:
    1. Bootstrap mode: No project, serves only onboarding wizard
    2. Normal mode: Full project context, serves all features
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root
        self.mode = 'normal' if project_root else 'bootstrap'
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        app = FastAPI()

        # Always available
        app.include_router(onboarding_router)
        app.include_router(health_router)

        # Only in normal mode
        if self.mode == 'normal':
            app.include_router(chat_router)
            app.include_router(project_router)
            app.include_router(git_router)
            # ... other routers

        return app

    async def transition_to_normal(self, project_root: Path) -> None:
        """
        Called after onboarding completes to add full functionality.
        Hot-reloads the application with project context.
        """
        self.project_root = project_root
        self.mode = 'normal'
        # Reinitialize services with project context
        await self._initialize_services()
```

---

## TUI Wizard Architecture

For Docker, SSH, WSL, and headless environments, provide a terminal-based wizard using Rich:

```python
class TUIWizard:
    """
    Terminal User Interface wizard using Rich library.
    Provides equivalent functionality to web wizard.
    """

    def __init__(self, console: Console):
        self.console = console

    async def run(self) -> Config:
        """Run the 4-step TUI wizard."""
        self.console.print(Panel.fit(
            "[bold blue]GAO-Dev Setup Wizard[/bold blue]\n\n"
            "Let's configure your project.",
            border_style="blue"
        ))

        # Step 1: Project configuration
        project_config = await self._project_step()

        # Step 2: Git configuration
        git_config = await self._git_step()

        # Step 3: Provider selection
        provider_config = await self._provider_step()

        # Step 4: Credentials
        credentials = await self._credentials_step(provider_config)

        return Config(
            project=project_config,
            git=git_config,
            provider=provider_config,
            credentials=credentials
        )

    async def _provider_step(self) -> ProviderConfig:
        """Provider selection with Rich table display."""
        table = Table(title="Available Providers")
        table.add_column("Option", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Description")

        table.add_row("1", "Claude Code", "Anthropic's Claude via CLI")
        table.add_row("2", "OpenCode SDK", "OpenCode with local/cloud models")
        table.add_row("3", "Direct API", "Direct Anthropic API calls")

        self.console.print(table)

        choice = Prompt.ask(
            "Select provider",
            choices=["1", "2", "3"],
            default="1"
        )

        return self._parse_provider_choice(choice)

    async def _credentials_step(self, provider: ProviderConfig) -> Credentials:
        """Credential entry with validation."""
        # Check environment first
        env_key = self._get_env_var_name(provider)
        if env_value := os.getenv(env_key):
            self.console.print(f"[green]Found {env_key} in environment[/green]")
            if await self._validate_credential(provider, env_value):
                return Credentials(source='environment', key=env_key)

        # Prompt for key
        self.console.print(f"\nEnter your API key for {provider.name}")
        self.console.print(f"[dim](or set {env_key} environment variable)[/dim]\n")

        api_key = Prompt.ask("API Key", password=True)

        # Validate
        with self.console.status("Validating..."):
            if await self._validate_credential(provider, api_key):
                self.console.print("[green]Key validated successfully![/green]")
                return Credentials(source='input', value=api_key)
            else:
                self.console.print("[red]Validation failed. Check your key.[/red]")
                # Retry or skip logic...
```

---

## Configuration Schema

### Global Configuration (`~/.gao-dev/config.yaml`)

```yaml
version: "1.0"

# User identity (used for git if not configured)
user:
  name: "Alex Developer"
  email: "alex@example.com"

# Default provider settings
provider:
  default: "claude-code"
  model: "sonnet-4.5"

# Credential storage preference
credentials:
  # Priority: environment > keychain > encrypted_file
  # Only stores WHERE credentials are, never the credentials themselves
  storage: "environment"  # or "keychain" or "encrypted_file"
  env_var: "ANTHROPIC_API_KEY"

# User preferences
preferences:
  auto_open_browser: true
  default_wizard: "auto"  # "web", "tui", or "auto" (detect)

# Metadata
metadata:
  created_at: "2025-01-15T10:30:00Z"
  last_updated: "2025-01-15T10:30:00Z"
  onboarding_completed: true
```

### Project Configuration (`<project>/.gao-dev/config.yaml`)

```yaml
version: "1.0"

project:
  name: "my-app"
  type: "greenfield"  # or "brownfield"
  created_at: "2025-01-15T10:30:00Z"

# Override global provider (optional)
provider:
  override: null  # or specific provider config

# Override credential source (optional)
credentials:
  override: null  # or specific source

# Project-specific settings
settings:
  scale_level: 2
  git_auto_commit: true
```

---

## API Endpoints

### Onboarding API (`/api/onboarding/`)

```python
@router.get("/status")
async def get_onboarding_status() -> OnboardingStatus:
    """Get current onboarding state."""
    return OnboardingStatus(
        completed=config_manager.is_onboarding_complete(),
        current_step=state_manager.get_current_step(),
        environment=detect_environment().value,
        available_wizards=["web", "tui"]
    )

@router.post("/project")
async def configure_project(config: ProjectConfig) -> ProjectConfigResponse:
    """Step 1: Configure project name and type."""
    validated = validate_project_config(config)
    state_manager.save_step("project", validated)
    return ProjectConfigResponse(success=True, next_step="git")

@router.post("/git")
async def configure_git(config: GitConfig) -> GitConfigResponse:
    """Step 2: Configure git user information."""
    # Validate and optionally set git config
    if config.set_global:
        subprocess.run(["git", "config", "--global", "user.name", config.name])
        subprocess.run(["git", "config", "--global", "user.email", config.email])
    state_manager.save_step("git", config)
    return GitConfigResponse(success=True, next_step="provider")

@router.post("/provider")
async def select_provider(config: ProviderConfig) -> ProviderConfigResponse:
    """Step 3: Select AI provider."""
    state_manager.save_step("provider", config)
    return ProviderConfigResponse(
        success=True,
        next_step="credentials",
        requires_api_key=config.requires_api_key
    )

@router.post("/credentials")
async def configure_credentials(config: CredentialsConfig) -> CredentialsResponse:
    """Step 4: Configure and validate credentials."""
    # Validate with provider
    if config.api_key:
        valid = await validate_api_key(config.provider, config.api_key)
        if not valid:
            raise HTTPException(400, "Invalid API key")

        # Store credential
        credential_manager.store_credential(
            key=f"{config.provider}_api_key",
            value=config.api_key
        )

    state_manager.save_step("credentials", config)
    return CredentialsResponse(success=True, onboarding_complete=True)

@router.post("/complete")
async def complete_onboarding() -> CompleteResponse:
    """Finalize onboarding and initialize project."""
    config = state_manager.get_all_steps()

    # Initialize project
    await initialize_project(config)

    # Mark complete
    config_manager.set_onboarding_complete()

    # Transition server to normal mode
    await app.state.server.transition_to_normal(config.project.path)

    return CompleteResponse(
        success=True,
        project_path=str(config.project.path),
        message="Ready to start building!"
    )
```

---

## Deprecated Command Behavior

| Command | Current Behavior | New Behavior | Deprecation Period |
|---------|------------------|--------------|-------------------|
| `gao-dev init` | Creates basic structure | Shows warning, redirects to `gao-dev start` | 6 months |
| `gao-dev web start` | Launches web server | Shows warning, redirects to `gao-dev start` | 6 months |
| `gao-dev start` | CLI REPL only | Unified entry point with auto-detection | N/A (enhanced) |

### Deprecation Warning Implementation

```python
@click.command('init')
def init_command():
    """[DEPRECATED] Initialize a GAO-Dev project."""
    console.print(Panel.fit(
        "[yellow]DEPRECATION WARNING[/yellow]\n\n"
        "The 'gao-dev init' command is deprecated and will be removed in v2.0.\n\n"
        "Use 'gao-dev start' instead - it will automatically initialize\n"
        "your project with a guided setup wizard.\n\n"
        "[dim]This command will redirect to 'gao-dev start' in 5 seconds...[/dim]",
        border_style="yellow"
    ))
    time.sleep(5)
    # Redirect to start
    ctx = click.get_current_context()
    ctx.invoke(start_command)
```

---

## Error Handling & Recovery

### Validation Error Messages

```python
class OnboardingError:
    """Actionable error messages with fix instructions."""

    @staticmethod
    def git_not_installed() -> str:
        return (
            "Git is not installed or not in PATH.\n\n"
            "To fix:\n"
            "  - Windows: Download from https://git-scm.com/download/win\n"
            "  - macOS: Run 'xcode-select --install'\n"
            "  - Linux: Run 'sudo apt install git' or equivalent\n\n"
            "After installing, restart your terminal and try again."
        )

    @staticmethod
    def api_key_invalid(provider: str) -> str:
        return (
            f"The API key for {provider} is invalid.\n\n"
            "To fix:\n"
            f"  1. Get a valid key from the {provider} dashboard\n"
            "  2. Check for extra spaces or missing characters\n"
            "  3. Ensure the key has the required permissions\n\n"
            "You can also set the key as an environment variable:\n"
            f"  export ANTHROPIC_API_KEY='your-key-here'"
        )

    @staticmethod
    def keychain_unavailable() -> str:
        return (
            "System keychain is not available in this environment.\n\n"
            "This is normal for Docker containers and SSH sessions.\n\n"
            "Recommended: Set credentials as environment variables:\n"
            "  export ANTHROPIC_API_KEY='your-key-here'\n\n"
            "Or mount a config volume in Docker:\n"
            "  -v gao-dev-config:/root/.gao-dev"
        )
```

### Recovery from Interrupted Onboarding

```python
class OnboardingStateManager:
    """Persist onboarding progress for recovery."""

    def __init__(self, config_path: Path):
        self.state_file = config_path / "onboarding_state.yaml"

    def save_step(self, step: str, data: dict) -> None:
        state = self._load_state()
        state['steps_completed'].append(step)
        state['step_data'][step] = data
        state['last_updated'] = datetime.utcnow().isoformat()
        self._save_state(state)

    def can_resume(self) -> bool:
        """Check if there's an interrupted onboarding to resume."""
        if not self.state_file.exists():
            return False
        state = self._load_state()
        return not state.get('completed', False)

    def resume(self) -> Tuple[str, dict]:
        """Get the next step and accumulated data."""
        state = self._load_state()
        completed = state.get('steps_completed', [])

        all_steps = ['project', 'git', 'provider', 'credentials']
        for step in all_steps:
            if step not in completed:
                return step, state.get('step_data', {})

        return 'complete', state.get('step_data', {})
```

---

## Testing Strategy

### Environment Simulation

```python
@pytest.fixture
def docker_environment(monkeypatch):
    """Simulate Docker container environment."""
    # Create /.dockerenv marker
    (Path('/') / '.dockerenv').touch()
    monkeypatch.delenv('DISPLAY', raising=False)
    monkeypatch.setenv('GAO_DEV_DOCKER', '1')
    yield
    (Path('/') / '.dockerenv').unlink()

@pytest.fixture
def ssh_environment(monkeypatch):
    """Simulate SSH session environment."""
    monkeypatch.setenv('SSH_CLIENT', '192.168.1.1 54321 22')
    monkeypatch.setenv('SSH_TTY', '/dev/pts/0')
    monkeypatch.delenv('DISPLAY', raising=False)
    yield

def test_environment_detection_docker(docker_environment):
    env = detect_environment()
    assert env == EnvironmentType.CONTAINER

def test_tui_wizard_selected_for_docker(docker_environment):
    orchestrator = StartupOrchestrator()
    assert orchestrator.get_wizard_type() == WizardType.TUI
```

### Cross-Platform Test Matrix

| Environment | Credential Storage | Wizard Type | Test Method |
|-------------|-------------------|-------------|-------------|
| Windows Desktop | Keychain | Web | Windows CI runner |
| macOS Desktop | Keychain | Web | macOS CI runner |
| Linux Desktop | Keychain | Web | Linux CI + DISPLAY |
| Docker | Env vars / File | TUI | Docker CI job |
| SSH Session | Env vars / File | TUI | SSH into CI runner |
| GitHub Codespaces | Env vars | TUI | Codespaces CI |
| WSL2 | Env vars / File | TUI | Windows CI + WSL |

---

## Migration from Existing Installations

### Existing `.gao-dev/` Detection

```python
def detect_existing_installation(project_path: Path) -> Optional[LegacyConfig]:
    """Detect and load configuration from pre-onboarding installations."""
    gao_dev_dir = project_path / '.gao-dev'

    if not gao_dev_dir.exists():
        return None

    # Check for old config format
    old_config = gao_dev_dir / 'gao-dev.yaml'
    if old_config.exists():
        return LegacyConfig.from_file(old_config)

    # Check for preference file from Epic 35
    prefs = gao_dev_dir / 'provider_preferences.yaml'
    if prefs.exists():
        return LegacyConfig.from_preferences(prefs)

    return LegacyConfig.minimal()

def migrate_legacy_config(legacy: LegacyConfig) -> Config:
    """Convert legacy configuration to new format."""
    return Config(
        project=ProjectConfig(
            name=legacy.project_name or Path.cwd().name,
            type='brownfield'  # Existing project
        ),
        provider=ProviderConfig(
            default=legacy.provider or 'claude-code',
            model=legacy.model or 'sonnet-4.5'
        ),
        credentials=CredentialsConfig(
            storage='environment',  # Default to env vars
            migrated_from=legacy.credential_source
        )
    )
```

---

## Revised Epic Structure

Based on Docker-first design and CRAAP review feedback, consolidate to 3 epics:

### Epic 40: Startup & Detection
**Focus**: Environment detection, unified command, context detection

- Story 40.1: Environment detection (Docker/SSH/WSL/Desktop/CI)
- Story 40.2: Global and project state detection
- Story 40.3: StartupOrchestrator implementation
- Story 40.4: Unified `gao-dev start` command
- Story 40.5: Deprecated command handling

### Epic 41: Onboarding Wizards
**Focus**: Both TUI and Web wizards, credential storage

- Story 41.1: TUI Wizard implementation (Rich-based)
- Story 41.2: Web Wizard backend API
- Story 41.3: Web Wizard frontend components
- Story 41.4: CredentialManager with environment-first storage
- Story 41.5: Onboarding state persistence and recovery
- Story 41.6: API key validation (with offline/skip support)

### Epic 42: Integration & Polish
**Focus**: Testing, migration, documentation

- Story 42.1: Existing installation migration
- Story 42.2: Cross-platform testing (Docker, SSH, WSL)
- Story 42.3: Error messages and recovery flows
- Story 42.4: Documentation and Docker deployment guide
- Story 42.5: Deprecation warnings and migration guide

---

## Success Metrics (Revised)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to first Brian response** | <3 min (P50), <5 min (P95) | Timestamp diff |
| **Docker deployment success** | >95% | Docker CI pass rate |
| **Credential validation success** | >90% | Validation endpoint logs |
| **Environment detection accuracy** | >99% | Automated test suite |
| **Onboarding completion** | >85% | State manager logs |

---

## Open Questions Resolved

1. **CLI deprecation**: CLI remains with `--headless` flag. TUI wizard for terminal users.

2. **Keychain fallback**: Environment variables are PRIMARY. Keychain is convenience for desktop. Encrypted file is last resort requiring password.

3. **Docker support**: First-class citizen with dedicated detection, TUI wizard, and env var credentials.

4. **Web server bootstrap**: Server starts in "bootstrap mode" without project, transitions after onboarding.

5. **Existing user migration**: Auto-detect legacy config, migrate to new format, skip unnecessary onboarding steps.
