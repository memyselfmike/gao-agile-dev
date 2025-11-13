"""Tests for ProviderValidator.

Epic 35: Interactive Provider Selection at Startup
Story 35.3: ProviderValidator Implementation
"""

import asyncio
import os
import platform
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from rich.console import Console

from gao_dev.cli.exceptions import ProviderValidationFailed
from gao_dev.cli.models import ValidationResult
from gao_dev.cli.provider_validator import ProviderValidator


@pytest.fixture
def console() -> Console:
    """Create Rich Console for tests."""
    return Console()


@pytest.fixture
def validator(console: Console) -> ProviderValidator:
    """Create ProviderValidator instance."""
    return ProviderValidator(console)


class TestValidateConfiguration:
    """Tests for validate_configuration method."""

    @pytest.mark.asyncio
    async def test_validate_claude_code_available(self, validator: ProviderValidator) -> None:
        """Claude Code validation passes when CLI available."""
        with patch.object(validator, "check_cli_available", return_value=True):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                result = await validator.validate_configuration(
                    "claude-code", {"api_key_env": "ANTHROPIC_API_KEY"}
                )

        assert result.success is True
        assert result.provider_name == "claude-code"
        assert "CLI available" in " ".join(result.messages)
        assert result.validation_time_ms > 0

    @pytest.mark.asyncio
    async def test_validate_claude_code_missing_cli(self, validator: ProviderValidator) -> None:
        """Claude Code validation fails when CLI missing."""
        with patch.object(validator, "check_cli_available", return_value=False):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                result = await validator.validate_configuration(
                    "claude-code", {"api_key_env": "ANTHROPIC_API_KEY"}
                )

        assert result.success is False
        assert result.provider_name == "claude-code"
        assert any("not found" in msg.lower() for msg in result.warnings)
        assert any("install" in sug.lower() for sug in result.suggestions)

    @pytest.mark.asyncio
    async def test_validate_claude_code_missing_api_key(
        self, validator: ProviderValidator
    ) -> None:
        """Claude Code validation fails when API key missing."""
        with patch.object(validator, "check_cli_available", return_value=True):
            with patch.dict(os.environ, {}, clear=True):
                result = await validator.validate_configuration(
                    "claude-code", {"api_key_env": "ANTHROPIC_API_KEY"}
                )

        assert result.success is False
        assert any("api key" in msg.lower() or "ANTHROPIC_API_KEY" in msg for msg in result.warnings)
        assert any("ANTHROPIC_API_KEY" in sug for sug in result.suggestions)

    @pytest.mark.asyncio
    async def test_validate_opencode_available(self, validator: ProviderValidator) -> None:
        """OpenCode validation passes when CLI available."""
        with patch.object(validator, "check_cli_available", return_value=True):
            with patch.object(validator, "check_ollama_models", return_value=["deepseek-r1"]):
                result = await validator.validate_configuration(
                    "opencode", {"ai_provider": "ollama", "use_local": True}
                )

        assert result.success is True
        assert result.provider_name == "opencode"

    @pytest.mark.asyncio
    async def test_validate_opencode_missing_cli(self, validator: ProviderValidator) -> None:
        """OpenCode validation fails when CLI missing."""
        with patch.object(validator, "check_cli_available", return_value=False):
            result = await validator.validate_configuration(
                "opencode", {"ai_provider": "ollama"}
            )

        assert result.success is False
        assert any("opencode" in sug.lower() for sug in result.suggestions)

    @pytest.mark.asyncio
    async def test_validate_direct_api_with_key(self, validator: ProviderValidator) -> None:
        """Direct API validation passes with API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            result = await validator.validate_configuration(
                "direct-api-anthropic", {"api_key_env": "ANTHROPIC_API_KEY"}
            )

        assert result.success is True
        assert result.provider_name == "direct-api-anthropic"

    @pytest.mark.asyncio
    async def test_validate_direct_api_no_key(self, validator: ProviderValidator) -> None:
        """Direct API validation fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = await validator.validate_configuration(
                "direct-api-anthropic", {"api_key_env": "ANTHROPIC_API_KEY"}
            )

        assert result.success is False
        assert any("api key" in msg.lower() or "ANTHROPIC_API_KEY" in msg for msg in result.warnings)
        assert any("ANTHROPIC_API_KEY" in sug for sug in result.suggestions)

    @pytest.mark.asyncio
    async def test_validate_unknown_provider(self, validator: ProviderValidator) -> None:
        """Validation fails for unknown provider."""
        result = await validator.validate_configuration("unknown-provider", {})

        assert result.success is False
        assert any("not found" in msg.lower() for msg in result.warnings)

    @pytest.mark.asyncio
    async def test_validation_timing_recorded(self, validator: ProviderValidator) -> None:
        """Validation time is recorded."""
        with patch.object(validator, "check_cli_available", return_value=True):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                result = await validator.validate_configuration("claude-code", {})

        assert result.validation_time_ms > 0
        assert isinstance(result.validation_time_ms, float)


class TestCheckCliAvailable:
    """Tests for check_cli_available method."""

    @pytest.mark.asyncio
    async def test_check_cli_available_unix(self, validator: ProviderValidator) -> None:
        """CLI detection works on Unix/macOS."""
        with patch("platform.system", return_value="Linux"):
            with patch.object(validator, "_check_cli_unix", return_value=True):
                result = await validator.check_cli_available("opencode")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_cli_unavailable_unix(self, validator: ProviderValidator) -> None:
        """CLI detection handles missing CLI on Unix."""
        with patch("platform.system", return_value="Linux"):
            with patch.object(validator, "_check_cli_unix", return_value=False):
                result = await validator.check_cli_available("opencode")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_cli_available_windows(self, validator: ProviderValidator) -> None:
        """CLI detection works on Windows."""
        with patch("platform.system", return_value="Windows"):
            with patch.object(validator, "_check_cli_windows", return_value=True):
                result = await validator.check_cli_available("opencode")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_cli_unavailable_windows(self, validator: ProviderValidator) -> None:
        """CLI detection handles missing CLI on Windows."""
        with patch("platform.system", return_value="Windows"):
            with patch.object(validator, "_check_cli_windows", return_value=False):
                result = await validator.check_cli_available("opencode")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_cli_timeout(self, validator: ProviderValidator) -> None:
        """CLI check times out after 5 seconds."""
        with patch("platform.system", return_value="Windows"):
            mock_proc = AsyncMock()
            mock_proc.wait = AsyncMock(side_effect=asyncio.TimeoutError)

            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await validator.check_cli_available("opencode")

        assert result is False


class TestCheckCliUnix:
    """Tests for _check_cli_unix method."""

    def test_check_cli_unix_available(self, validator: ProviderValidator) -> None:
        """Unix CLI detection succeeds when CLI in PATH."""
        with patch("shutil.which", return_value="/usr/bin/opencode"):
            result = validator._check_cli_unix("opencode")

        assert result is True

    def test_check_cli_unix_unavailable(self, validator: ProviderValidator) -> None:
        """Unix CLI detection fails when CLI not in PATH."""
        with patch("shutil.which", return_value=None):
            result = validator._check_cli_unix("opencode")

        assert result is False


class TestCheckCliWindows:
    """Tests for _check_cli_windows method."""

    @pytest.mark.asyncio
    async def test_check_cli_windows_available(self, validator: ProviderValidator) -> None:
        """Windows CLI detection succeeds when CLI found."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock(return_value=None)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await validator._check_cli_windows("opencode")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_cli_windows_unavailable(self, validator: ProviderValidator) -> None:
        """Windows CLI detection fails when CLI not found."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.wait = AsyncMock(return_value=None)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await validator._check_cli_windows("opencode")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_cli_windows_timeout(self, validator: ProviderValidator) -> None:
        """Windows CLI detection handles timeout."""
        mock_proc = AsyncMock()
        mock_proc.wait = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
                result = await validator._check_cli_windows("opencode")

        assert result is False


class TestCheckOllamaModels:
    """Tests for check_ollama_models method."""

    @pytest.mark.asyncio
    async def test_check_ollama_models_available(self, validator: ProviderValidator) -> None:
        """Ollama model detection parses output correctly."""
        mock_output = b"""NAME                    ID              SIZE      MODIFIED
deepseek-r1:latest      abc123          3.8 GB    2 days ago
llama2:latest           def456          3.8 GB    1 week ago
codellama:13b           ghi789          6.7 GB    2 weeks ago
"""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(mock_output, b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            models = await validator.check_ollama_models()

        assert "deepseek-r1" in models
        assert "llama2" in models
        assert "codellama:13b" in models
        assert len(models) == 3

    @pytest.mark.asyncio
    async def test_check_ollama_not_available(self, validator: ProviderValidator) -> None:
        """Ollama unavailable returns empty list."""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            models = await validator.check_ollama_models()

        assert models == []

    @pytest.mark.asyncio
    async def test_parse_ollama_output_empty(self, validator: ProviderValidator) -> None:
        """Parsing empty Ollama output returns empty list."""
        models = validator._parse_ollama_output("")
        assert models == []

    @pytest.mark.asyncio
    async def test_parse_ollama_output_header_only(self, validator: ProviderValidator) -> None:
        """Parsing header-only output returns empty list."""
        output = "NAME                    ID              SIZE      MODIFIED"
        models = validator._parse_ollama_output(output)
        assert models == []

    @pytest.mark.asyncio
    async def test_parse_ollama_output_with_tags(self, validator: ProviderValidator) -> None:
        """Parsing output correctly removes :latest suffix."""
        output = """NAME                    ID              SIZE      MODIFIED
deepseek-r1:latest      abc123          3.8 GB    2 days ago
llama2:7b               def456          3.8 GB    1 week ago
"""
        models = validator._parse_ollama_output(output)
        assert "deepseek-r1" in models
        assert "llama2:7b" in models


class TestSuggestFixes:
    """Tests for suggest_fixes method."""

    def test_suggest_fixes_claude_code(self, validator: ProviderValidator) -> None:
        """Suggestions provided for Claude Code installation."""
        suggestions = validator.suggest_fixes("claude-code")

        assert len(suggestions) > 0
        assert any("npm install" in sug for sug in suggestions)

    def test_suggest_fixes_opencode(self, validator: ProviderValidator) -> None:
        """Suggestions provided for OpenCode installation."""
        suggestions = validator.suggest_fixes("opencode")

        assert len(suggestions) > 0
        assert any("install" in sug.lower() for sug in suggestions)

    def test_suggest_fixes_ollama(self, validator: ProviderValidator) -> None:
        """Suggestions provided for Ollama installation."""
        suggestions = validator.suggest_fixes("ollama")

        assert len(suggestions) > 0
        assert any("ollama" in sug.lower() for sug in suggestions)

    def test_suggest_fixes_direct_api_anthropic(self, validator: ProviderValidator) -> None:
        """Suggestions provided for missing API key."""
        suggestions = validator.suggest_fixes("direct-api-anthropic")

        assert len(suggestions) > 0
        assert any("ANTHROPIC_API_KEY" in sug for sug in suggestions)

    def test_suggest_fixes_direct_api_openai(self, validator: ProviderValidator) -> None:
        """Suggestions provided for OpenAI API key."""
        suggestions = validator.suggest_fixes("direct-api-openai")

        assert len(suggestions) > 0
        assert any("OPENAI_API_KEY" in sug for sug in suggestions)

    def test_suggest_fixes_unknown_provider(self, validator: ProviderValidator) -> None:
        """Suggestions provided for unknown provider."""
        suggestions = validator.suggest_fixes("unknown-provider")

        assert len(suggestions) > 0
        assert any("available providers" in sug.lower() for sug in suggestions)


class TestIntegration:
    """Integration tests for full validation flow."""

    @pytest.mark.asyncio
    async def test_full_validation_claude_code_success(
        self, validator: ProviderValidator
    ) -> None:
        """Full validation succeeds for properly configured Claude Code."""
        async def mock_cli_check(cli_name: str) -> bool:
            return True

        with patch.object(validator, "check_cli_available", side_effect=mock_cli_check):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                result = await validator.validate_configuration("claude-code", {})

        assert result.success is True
        assert len(result.messages) > 0
        assert len(result.warnings) == 0
        assert result.validation_time_ms > 0

    @pytest.mark.asyncio
    async def test_full_validation_opencode_ollama_success(
        self, validator: ProviderValidator
    ) -> None:
        """Full validation succeeds for OpenCode with Ollama."""
        async def mock_cli_check(cli_name: str) -> bool:
            return True

        async def mock_ollama_models() -> list[str]:
            return ["deepseek-r1"]

        with patch.object(validator, "check_cli_available", side_effect=mock_cli_check):
            with patch.object(validator, "check_ollama_models", side_effect=mock_ollama_models):
                result = await validator.validate_configuration(
                    "opencode", {"ai_provider": "ollama", "use_local": True}
                )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_full_validation_multiple_failures(
        self, validator: ProviderValidator
    ) -> None:
        """Full validation captures multiple failures."""
        async def mock_cli_check(cli_name: str) -> bool:
            return False

        with patch.object(validator, "check_cli_available", side_effect=mock_cli_check):
            with patch.dict(os.environ, {}, clear=True):
                result = await validator.validate_configuration("claude-code", {})

        assert result.success is False
        assert len(result.warnings) >= 1  # CLI missing
        assert len(result.suggestions) >= 2  # Install CLI + Set API key


class TestCrossPlatform:
    """Cross-platform behavior tests."""

    @pytest.mark.asyncio
    async def test_windows_platform_detection(self, validator: ProviderValidator) -> None:
        """Validator correctly detects Windows platform."""
        async def mock_windows_check(cli_name: str) -> bool:
            return True

        with patch("platform.system", return_value="Windows"):
            with patch.object(validator, "_check_cli_windows", side_effect=mock_windows_check):
                result = await validator.check_cli_available("opencode")
                assert result is True

    @pytest.mark.asyncio
    async def test_linux_platform_detection(self, validator: ProviderValidator) -> None:
        """Validator correctly detects Linux platform."""
        with patch("platform.system", return_value="Linux"):
            with patch("shutil.which", return_value="/usr/bin/opencode") as mock_which:
                result = await validator.check_cli_available("opencode")
                assert result is True
                mock_which.assert_called_once_with("opencode")

    @pytest.mark.asyncio
    async def test_macos_platform_detection(self, validator: ProviderValidator) -> None:
        """Validator correctly detects macOS platform."""
        with patch("platform.system", return_value="Darwin"):
            with patch("shutil.which", return_value="/usr/local/bin/opencode") as mock_which:
                result = await validator.check_cli_available("opencode")
                assert result is True
                mock_which.assert_called_once_with("opencode")
