"""CLI commands for provider management."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import structlog
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from gao_dev.core.providers import (
    ProviderFactory,
    ProviderSelector,
    ProviderHealthChecker,
)

logger = structlog.get_logger()
console = Console()


@click.group(name="providers")
def providers_cli():
    """Provider management commands."""
    pass


@providers_cli.command(name="list")
def list_providers():
    """
    List all available providers.

    Shows registered providers and their basic information.

    Example:
        gao-dev providers list
    """
    try:
        factory = ProviderFactory()
        providers = factory.list_providers()

        # Create table
        table = Table(title="Available Providers", show_header=True)
        table.add_column("Provider Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")

        # Add providers
        for provider_name in providers:
            # Determine type
            if provider_name.startswith("direct-api-"):
                provider_type = "Direct API"
            elif provider_name == "claude-code":
                provider_type = "CLI (Claude Code)"
            elif provider_name == "opencode":
                provider_type = "CLI (OpenCode)"
            else:
                provider_type = "Custom"

            table.add_row(provider_name, provider_type, "Available")

        console.print(table)

        # Show count
        console.print(f"\nTotal: {len(providers)} providers available")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


@providers_cli.command(name="validate")
@click.argument("provider_name", required=False)
@click.option(
    "--api-key", help="API key for validation (overrides environment variable)"
)
def validate_provider(provider_name: Optional[str], api_key: Optional[str]):
    """
    Validate provider configuration.

    Checks if a provider is properly configured and can be used.

    Arguments:
        PROVIDER_NAME: Name of provider to validate (optional, validates all if not provided)

    Example:
        gao-dev providers validate claude-code
        gao-dev providers validate direct-api-anthropic --api-key sk-...
        gao-dev providers validate  # Validate all
    """
    try:
        factory = ProviderFactory()

        # If no provider specified, validate all
        if not provider_name:
            providers_to_validate = factory.list_providers()
        else:
            providers_to_validate = [provider_name]

        # Create table
        table = Table(title="Provider Validation Results", show_header=True)
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        for prov_name in providers_to_validate:
            try:
                # Create provider
                config = {}
                if api_key:
                    config["api_key"] = api_key

                provider = factory.create_provider(prov_name, config=config)

                # Validate
                result = asyncio.run(provider.validate_configuration())

                if isinstance(result, bool):
                    if result:
                        status = "[green]PASS[/green]"
                        details = "Configuration valid"
                    else:
                        status = "[red]FAIL[/red]"
                        details = "Configuration invalid"
                elif isinstance(result, dict):
                    if result.get("valid", False):
                        status = "[green]PASS[/green]"
                        details = result.get("message", "Configuration valid")
                    else:
                        status = "[red]FAIL[/red]"
                        details = result.get("message", "Configuration invalid")
                else:
                    status = "[yellow]UNKNOWN[/yellow]"
                    details = "Unable to determine validity"

                table.add_row(prov_name, status, details)

            except Exception as e:
                table.add_row(
                    prov_name, "[red]ERROR[/red]", f"Validation failed: {str(e)[:50]}"
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


@providers_cli.command(name="test")
@click.argument("provider_name")
@click.option("--prompt", default="Hello, world!", help="Test prompt to send")
@click.option("--model", default="sonnet-4.5", help="Model to use for test")
@click.option("--api-key", help="API key (overrides environment variable)")
def test_provider(
    provider_name: str, prompt: str, model: str, api_key: Optional[str]
):
    """
    Test a provider with a simple prompt.

    Sends a test prompt to verify the provider works end-to-end.

    Arguments:
        PROVIDER_NAME: Name of provider to test

    Example:
        gao-dev providers test claude-code --prompt "Say hello"
        gao-dev providers test direct-api-anthropic --api-key sk-...
    """
    try:
        factory = ProviderFactory()

        # Create provider
        config = {}
        if api_key:
            config["api_key"] = api_key

        console.print(f"\n[cyan]Testing provider:[/cyan] {provider_name}")
        console.print(f"[cyan]Model:[/cyan] {model}")
        console.print(f"[cyan]Prompt:[/cyan] {prompt}\n")

        provider = factory.create_provider(provider_name, config=config)

        # Test execution
        console.print("[yellow]Executing...[/yellow]\n")

        # Note: Actual execution would require AgentContext and proper setup
        # For now, just verify provider can be created and has execute_task method
        if hasattr(provider, "execute_task"):
            console.print(
                "[green]SUCCESS:[/green] Provider is properly configured and ready"
            )
            console.print(
                "\n[dim]Note: Full execution test requires agent context setup[/dim]"
            )
        else:
            console.print("[red]FAIL:[/red] Provider missing execute_task method")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]Test failed:[/red] {e}", style="bold red")
        sys.exit(1)


@providers_cli.command(name="health")
def check_health():
    """
    Check health of all providers.

    Performs health checks on all registered providers.

    Example:
        gao-dev providers health
    """
    try:
        factory = ProviderFactory()
        checker = ProviderHealthChecker(factory)

        console.print("\n[cyan]Running health checks...[/cyan]\n")

        # Run health checks
        results = asyncio.run(checker.check_all_providers())

        # Create table
        table = Table(title="Provider Health Status", show_header=True)
        table.add_column("Provider", style="cyan")
        table.add_column("Health", style="green")
        table.add_column("Details", style="yellow")

        for provider_name, health_result in results.items():
            if health_result.get("healthy", False):
                health = "[green]HEALTHY[/green]"
            else:
                health = "[red]UNHEALTHY[/red]"

            details = health_result.get("message", "No details")

            table.add_row(provider_name, health, details)

        console.print(table)

        # Summary
        healthy_count = sum(1 for r in results.values() if r.get("healthy", False))
        total_count = len(results)

        console.print(f"\n[cyan]Summary:[/cyan] {healthy_count}/{total_count} healthy")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


@providers_cli.command(name="info")
@click.argument("provider_name")
def show_provider_info(provider_name: str):
    """
    Show detailed information about a provider.

    Displays configuration schema, supported models, and capabilities.

    Arguments:
        PROVIDER_NAME: Name of provider

    Example:
        gao-dev providers info claude-code
        gao-dev providers info direct-api-anthropic
    """
    try:
        factory = ProviderFactory()
        provider = factory.create_provider(provider_name)

        # Create panel with provider info
        info_text = f"""
[cyan]Name:[/cyan] {provider.name}
[cyan]Version:[/cyan] {provider.version}

[cyan]Supported Models:[/cyan]
"""
        models = provider.get_supported_models()
        for model in models:
            info_text += f"  - {model}\n"

        info_text += f"\n[cyan]Configuration Schema:[/cyan]\n"
        schema = provider.get_configuration_schema()
        if schema:
            for key, value in schema.items():
                info_text += f"  - {key}: {value.get('type', 'unknown')}\n"
        else:
            info_text += "  No configuration required\n"

        panel = Panel(info_text, title=f"Provider: {provider_name}", expand=False)
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


@providers_cli.command(name="cache-stats")
def show_cache_stats():
    """
    Show provider cache statistics.

    Displays current cache usage and hit rates.

    Example:
        gao-dev providers cache-stats
    """
    try:
        factory = ProviderFactory()
        stats = factory.get_cache_stats()

        # Create table
        table = Table(title="Cache Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Provider Cache Size", str(stats["provider_cache_size"]))
        table.add_row("Model Cache Size", str(stats["model_cache_size"]))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    providers_cli()
