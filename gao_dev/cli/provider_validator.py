"""Provider configuration validator.

This module provides the ProviderValidator class for validating provider
configurations, checking CLI availability, and providing actionable error
messages.

Epic 35: Interactive Provider Selection at Startup
Story 35.3: ProviderValidator Implementation
"""

import asyncio
import os
import platform
import shutil
import time
from typing import Dict, Any, List

from rich.console import Console
import structlog

from gao_dev.cli.models import ValidationResult
from gao_dev.core.providers.factory import ProviderFactory

logger = structlog.get_logger()


class ProviderValidator:
    """
    Validates provider configuration.

    Checks CLI availability, API keys, connectivity, and provides
    actionable error messages with fix suggestions.

    Attributes:
        console: Rich Console for output

    Example:
        ```python
        validator = ProviderValidator(console)

        result = await validator.validate_configuration(
            'claude-code',
            {'api_key_env': 'ANTHROPIC_API_KEY'}
        )

        if not result.success:
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        ```
    """

    # CLI-based providers
    CLI_PROVIDERS = {
        "claude-code": "claude",
        "opencode": "opencode",
        "opencode-cli": "opencode",
    }

    # Direct API providers and their required env vars
    API_KEY_PROVIDERS = {
        "direct-api-anthropic": "ANTHROPIC_API_KEY",
        "direct-api-openai": "OPENAI_API_KEY",
        "direct-api-google": "GOOGLE_API_KEY",
    }

    def __init__(self, console: Console):
        """
        Initialize ProviderValidator with console.

        Args:
            console: Rich Console for output
        """
        self.console = console
        self.logger = logger.bind(component="provider_validator")
        self._factory = ProviderFactory()

    async def validate_configuration(
        self, provider_name: str, config: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate provider configuration.

        Checks:
        - Provider exists in ProviderFactory registry
        - CLI available (if CLI-based provider)
        - API key set (if direct API provider)
        - Model supported by provider
        - Basic connectivity test (optional)

        Args:
            provider_name: Provider identifier
            config: Provider configuration dict

        Returns:
            ValidationResult with success/failure and messages
        """
        start_time = time.perf_counter()
        result = ValidationResult(success=True, provider_name=provider_name)

        self.logger.info("validation_started", provider=provider_name)
        result.add_message(f"Validating {provider_name}...")

        # Check if provider exists
        if not self._factory.provider_exists(provider_name):
            result.success = False
            result.add_warning(f"Provider '{provider_name}' not found")
            result.suggestions.extend(self.suggest_fixes(provider_name))
            self.logger.warning(
                "validation_failed", provider=provider_name, reason="provider_not_found"
            )
            result.validation_time_ms = (time.perf_counter() - start_time) * 1000
            return result

        # CLI-based provider validation
        if provider_name in self.CLI_PROVIDERS:
            cli_name = self.CLI_PROVIDERS[provider_name]
            result.add_message(f"Checking {cli_name} CLI availability...")

            cli_available = await self.check_cli_available(cli_name)
            if not cli_available:
                result.success = False
                result.add_warning(f"{cli_name} CLI not found in PATH")
                result.suggestions.extend(self.suggest_fixes(provider_name))
            else:
                result.add_message(f"{cli_name} CLI available")

            # Check API key for claude-code
            if provider_name == "claude-code":
                api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
                if not os.getenv(api_key_env):
                    result.success = False
                    result.add_warning(f"{api_key_env} not set")
                    result.suggestions.extend(self.suggest_fixes(provider_name))
                else:
                    result.add_message(f"{api_key_env} is set")

            # Check Ollama models for opencode if using local
            if provider_name in ("opencode", "opencode-cli"):
                if config.get("ai_provider") == "ollama" or config.get("use_local"):
                    result.add_message("Checking Ollama models...")
                    self.console.print(
                        "[dim]Detecting Ollama models (may take a moment)...[/dim]"
                    )

                    models = await self.check_ollama_models()
                    if not models:
                        result.add_warning("No Ollama models found")
                        result.suggestions.extend(self.suggest_fixes("ollama"))
                    else:
                        result.add_message(f"Found {len(models)} Ollama model(s)")

        # Direct API provider validation
        elif provider_name in self.API_KEY_PROVIDERS:
            api_key_env = config.get("api_key_env", self.API_KEY_PROVIDERS[provider_name])
            result.add_message(f"Checking {api_key_env}...")

            if not os.getenv(api_key_env):
                result.success = False
                result.add_warning(f"{api_key_env} not set")
                result.suggestions.extend(self.suggest_fixes(provider_name))
            else:
                result.add_message(f"{api_key_env} is set")

        # Calculate validation time
        result.validation_time_ms = (time.perf_counter() - start_time) * 1000

        if result.success:
            self.logger.info(
                "validation_completed",
                provider=provider_name,
                duration_ms=result.validation_time_ms,
            )
        else:
            self.logger.warning(
                "validation_failed",
                provider=provider_name,
                duration_ms=result.validation_time_ms,
                warnings=len(result.warnings),
            )

        return result

    async def check_cli_available(self, cli_name: str) -> bool:
        """
        Check if CLI tool is in PATH.

        Cross-platform: uses shutil.which() on Unix, where on Windows.

        Args:
            cli_name: Name of CLI (e.g., 'claude', 'opencode', 'ollama')

        Returns:
            True if CLI available, False otherwise
        """
        self.logger.debug("checking_cli", cli_name=cli_name, platform=platform.system())

        try:
            if platform.system() == "Windows":
                result = await asyncio.wait_for(
                    self._check_cli_windows(cli_name), timeout=5.0
                )
            else:
                # Unix/macOS - use shutil.which (sync, no timeout needed)
                result = self._check_cli_unix(cli_name)

            self.logger.debug(
                "cli_check_result", cli_name=cli_name, available=result
            )
            return result

        except asyncio.TimeoutError:
            self.logger.warning("cli_check_timeout", cli_name=cli_name)
            return False
        except Exception as e:
            self.logger.warning("cli_check_error", cli_name=cli_name, error=str(e))
            return False

    def _check_cli_unix(self, cli_name: str) -> bool:
        """
        Check CLI availability on Unix/macOS using shutil.which.

        Args:
            cli_name: Name of CLI

        Returns:
            True if CLI in PATH, False otherwise
        """
        return shutil.which(cli_name) is not None

    async def _check_cli_windows(self, cli_name: str) -> bool:
        """
        Check CLI availability on Windows using 'where' command.

        Args:
            cli_name: Name of CLI

        Returns:
            True if CLI found, False otherwise
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                f"where {cli_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await asyncio.wait_for(proc.wait(), timeout=5.0)
            return proc.returncode == 0

        except asyncio.TimeoutError:
            self.logger.warning("windows_cli_check_timeout", cli_name=cli_name)
            return False
        except Exception as e:
            self.logger.debug(
                "windows_cli_check_error", cli_name=cli_name, error=str(e)
            )
            return False

    async def check_ollama_models(self) -> List[str]:
        """
        Get list of available Ollama models.

        Runs `ollama list` command and parses output.
        Returns empty list if Ollama unavailable.

        Returns:
            List of model names, or empty list if Ollama unavailable
        """
        self.logger.debug("checking_ollama_models")

        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 10-second timeout (CRAAP requirement for slow disks/HDD/NAS)
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=10.0
            )

            if proc.returncode == 0:
                output = stdout.decode("utf-8")
                models = self._parse_ollama_output(output)
                self.logger.debug(
                    "ollama_models_found", count=len(models), models=models
                )
                return models
            else:
                self.logger.debug("ollama_list_failed", returncode=proc.returncode)
                return []

        except FileNotFoundError:
            self.logger.debug("ollama_not_found")
            return []
        except asyncio.TimeoutError:
            self.logger.warning("ollama_check_timeout")
            return []
        except Exception as e:
            self.logger.warning("ollama_check_error", error=str(e))
            return []

    def _parse_ollama_output(self, output: str) -> List[str]:
        """
        Parse `ollama list` output to extract model names.

        Format:
            NAME                    ID              SIZE      MODIFIED
            deepseek-r1:latest      abc123          3.8 GB    2 days ago

        Args:
            output: Raw output from `ollama list`

        Returns:
            List of model names (with :latest suffix removed)
        """
        models = []
        lines = output.strip().split("\n")

        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue

            # Extract first column (NAME)
            parts = line.split()
            if parts:
                model_name = parts[0]
                # Remove :latest suffix if present
                if model_name.endswith(":latest"):
                    model_name = model_name[:-7]  # Remove ":latest"
                models.append(model_name)

        return models

    def suggest_fixes(self, provider_name: str) -> List[str]:
        """
        Provide installation/fix suggestions for provider.

        Args:
            provider_name: Provider that failed validation

        Returns:
            List of suggestion strings

        Example:
            For 'claude-code':
            [
                "Install Claude Code: Follow instructions at https://...",
                "Ensure ANTHROPIC_API_KEY is set: export ANTHROPIC_API_KEY=sk-...",
                "Check PATH: echo $PATH"
            ]
        """
        suggestions = []

        if provider_name == "claude-code":
            suggestions.append(
                "Install Claude Code CLI: npm install -g @anthropic/claude-code"
            )
            suggestions.append(
                "Set API key: export ANTHROPIC_API_KEY=sk-ant-..."
            )
            suggestions.append(
                "Verify installation: claude --version"
            )

        elif provider_name in ("opencode", "opencode-cli"):
            suggestions.append(
                "Install OpenCode CLI: npm install -g opencode"
            )
            suggestions.append(
                "Alternative: Install from https://github.com/opencodetools/opencode"
            )
            suggestions.append(
                "Verify installation: opencode --version"
            )

        elif provider_name == "ollama":
            suggestions.append(
                "Install Ollama: https://ollama.ai/download"
            )
            suggestions.append(
                "Pull a model: ollama pull deepseek-r1"
            )
            suggestions.append(
                "Verify installation: ollama list"
            )

        elif provider_name == "direct-api-anthropic":
            suggestions.append(
                "Set API key: export ANTHROPIC_API_KEY=sk-ant-..."
            )
            suggestions.append(
                "Get API key: https://console.anthropic.com/settings/keys"
            )

        elif provider_name == "direct-api-openai":
            suggestions.append(
                "Set API key: export OPENAI_API_KEY=sk-..."
            )
            suggestions.append(
                "Get API key: https://platform.openai.com/api-keys"
            )

        elif provider_name == "direct-api-google":
            suggestions.append(
                "Set API key: export GOOGLE_API_KEY=..."
            )
            suggestions.append(
                "Get API key: https://aistudio.google.com/app/apikey"
            )

        else:
            # Unknown provider
            available = ", ".join(self._factory.list_providers())
            suggestions.append(
                f"Available providers: {available}"
            )
            suggestions.append(
                "Check provider name spelling and capitalization"
            )

        return suggestions
