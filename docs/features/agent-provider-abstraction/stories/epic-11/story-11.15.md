# Story 11.15: Migration Tooling & Commands

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer) + Bob (Scrum Master)
**Created**: 2025-11-04
**Dependencies**: Story 11.14 (Comprehensive Testing)

---

## User Story

**As a** GAO-Dev user
**I want** automated tools to migrate to the new provider system
**So that** I can easily adopt multi-provider support without manual configuration changes

---

## Acceptance Criteria

### AC1: Provider Validation Command
- ✅ `gao-dev providers validate` command created
- ✅ Checks all registered providers
- ✅ Validates CLI installation (claude-code, opencode)
- ✅ Validates API keys (direct-api)
- ✅ Reports health status
- ✅ Color-coded output (green/yellow/red)

### AC2: Provider List Command
- ✅ `gao-dev providers list` command created
- ✅ Shows all registered providers
- ✅ Indicates availability status
- ✅ Shows supported models
- ✅ Shows configuration source
- ✅ Table format output

### AC3: Provider Info Command
- ✅ `gao-dev providers info <name>` command created
- ✅ Detailed provider information
- ✅ Configuration options
- ✅ Model list with descriptions
- ✅ Tool support matrix
- ✅ Example usage

### AC4: Provider Test Command
- ✅ `gao-dev providers test <name>` command created
- ✅ Executes test task on provider
- ✅ Verifies provider functionality
- ✅ Reports success/failure
- ✅ Shows performance metrics
- ✅ Diagnostic output on failure

### AC5: Migration Check Command
- ✅ `gao-dev providers migrate-check` command created
- ✅ Scans project for provider usage
- ✅ Identifies needed changes
- ✅ Reports compatibility status
- ✅ Suggests migration actions
- ✅ JSON output option

### AC6: Configuration Migration Tool
- ✅ `gao-dev providers migrate-config` command created
- ✅ Updates agent YAML files
- ✅ Adds provider fields if missing
- ✅ Preserves existing configuration
- ✅ Creates backup before changes
- ✅ Dry-run mode

### AC7: Provider Setup Wizard
- ✅ `gao-dev providers setup` interactive wizard
- ✅ Guides user through provider selection
- ✅ Prompts for API keys
- ✅ Validates configuration
- ✅ Updates defaults.yaml
- ✅ Tests provider after setup

### AC8: Provider Compare Command
- ✅ `gao-dev providers compare` command created
- ✅ Compares available providers
- ✅ Shows performance comparison
- ✅ Shows cost comparison
- ✅ Shows feature comparison
- ✅ Recommendation based on user needs

### AC9: Provider Switch Command
- ✅ `gao-dev providers switch <name>` command created
- ✅ Changes default provider
- ✅ Updates defaults.yaml
- ✅ Validates new provider
- ✅ Confirms before changing
- ✅ Rollback on failure

### AC10: Health Check Integration
- ✅ `gao-dev health` includes provider checks
- ✅ Reports provider status
- ✅ Warns about missing providers
- ✅ Suggests fixes for issues

### AC11: Help & Documentation
- ✅ All commands have --help text
- ✅ Examples included in help
- ✅ Clear error messages
- ✅ Links to documentation
- ✅ Troubleshooting hints

### AC12: Configuration Rollback Command (R3 - Winston's Recommendation)
- ✅ `gao-dev providers rollback` command created
- ✅ Lists available backups with timestamps
- ✅ Allows selection of specific backup to restore
- ✅ Validates backup before restoration
- ✅ Confirms with user before restoring
- ✅ Restores agent YAML files from backup
- ✅ Restores defaults.yaml from backup
- ✅ Logs rollback operation
- ✅ Verifies configuration after rollback
- ✅ Can rollback last migration automatically (--last flag)

---

## Technical Details

### File Structure
```
gao_dev/cli/
├── commands.py                      # MODIFIED: Add provider commands group
└── provider_commands.py             # NEW: Provider CLI commands

gao_dev/core/providers/
├── validation.py                    # NEW: Provider validation
├── migration.py                     # NEW: Migration helpers
└── setup_wizard.py                  # NEW: Interactive setup

docs/
└── provider-migration-guide.md      # MODIFIED: Add CLI commands section
```

### Implementation Approach

#### Step 1: Create Provider Commands Module

**File**: `gao_dev/cli/provider_commands.py`

```python
"""CLI commands for provider management."""

import click
from pathlib import Path
from typing import Optional
import structlog

from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.validation import ProviderValidator
from gao_dev.core.providers.migration import ConfigMigrator
from gao_dev.core.providers.setup_wizard import ProviderSetupWizard

logger = structlog.get_logger(__name__)


@click.group("providers")
def providers_cli():
    """
    Manage AI providers.

    Commands for validating, testing, and migrating between providers.
    """
    pass


@providers_cli.command("list")
@click.option(
    "--format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def list_providers(format: str):
    """
    List all registered providers.

    Shows provider name, availability status, and supported models.

    Examples:
        gao-dev providers list
        gao-dev providers list --format json
    """
    factory = ProviderFactory()
    provider_names = factory.list_providers()

    if format == "table":
        # Table format
        click.echo("\nRegistered Providers:\n")
        click.echo(f"{'Provider':<20} {'Status':<12} {'Models':<30}")
        click.echo("-" * 65)

        for name in provider_names:
            try:
                # Try to create provider to check availability
                provider = factory.create_provider(name)
                status = click.style("Available", fg="green")
                models = ", ".join(provider.get_supported_models()[:3])
                if len(provider.get_supported_models()) > 3:
                    models += "..."
            except Exception as e:
                status = click.style("Unavailable", fg="red")
                models = click.style(f"({str(e)[:25]})", fg="yellow")

            click.echo(f"{name:<20} {status:<20} {models:<30}")

        click.echo()

    elif format == "json":
        import json
        # JSON format
        providers_data = []
        for name in provider_names:
            try:
                provider = factory.create_provider(name)
                providers_data.append({
                    "name": name,
                    "available": True,
                    "models": provider.get_supported_models(),
                })
            except Exception as e:
                providers_data.append({
                    "name": name,
                    "available": False,
                    "error": str(e),
                })

        click.echo(json.dumps(providers_data, indent=2))


@providers_cli.command("validate")
@click.option("--provider", "-p", help="Validate specific provider only")
def validate_providers(provider: Optional[str]):
    """
    Validate provider configurations.

    Checks:
    - CLI installation (for claude-code, opencode)
    - API key presence (for direct-api)
    - Provider functionality

    Examples:
        gao-dev providers validate
        gao-dev providers validate --provider claude-code
    """
    validator = ProviderValidator()

    if provider:
        # Validate single provider
        result = validator.validate_provider(provider)
        _display_validation_result(provider, result)
    else:
        # Validate all providers
        click.echo("\nValidating all providers...\n")
        results = validator.validate_all_providers()

        all_valid = True
        for name, result in results.items():
            _display_validation_result(name, result)
            if not result.valid:
                all_valid = False

        click.echo()
        if all_valid:
            click.echo(click.style("✓ All providers valid", fg="green"))
        else:
            click.echo(click.style("✗ Some providers invalid", fg="red"))
            click.echo("\nRun 'gao-dev providers info <name>' for details")


def _display_validation_result(name: str, result):
    """Display validation result."""
    if result.valid:
        status = click.style("✓", fg="green")
    else:
        status = click.style("✗", fg="red")

    click.echo(f"{status} {name:<20} {result.message}")

    if result.warnings:
        for warning in result.warnings:
            click.echo(f"  ⚠ {click.style(warning, fg='yellow')}")


@providers_cli.command("test")
@click.argument("provider_name")
@click.option("--model", "-m", default="sonnet-4.5", help="Model to test")
@click.option("--task", "-t", default="What is 2+2?", help="Test task")
def test_provider(provider_name: str, model: str, task: str):
    """
    Test a provider with a simple task.

    Executes a test task and verifies the provider works correctly.

    Examples:
        gao-dev providers test claude-code
        gao-dev providers test direct-api --model gpt-4
    """
    import asyncio
    from gao_dev.core.providers.models import AgentContext

    click.echo(f"\nTesting provider: {provider_name}")
    click.echo(f"Model: {model}")
    click.echo(f"Task: {task}\n")

    factory = ProviderFactory()

    try:
        # Create provider
        provider = factory.create_provider(provider_name)

        # Execute task
        context = AgentContext(project_root=Path.cwd())

        click.echo("Executing task...")
        start_time = time.time()

        results = []
        async def run_task():
            async for chunk in provider.execute_task(
                task=task,
                context=context,
                model=model,
                timeout=60,
            ):
                results.append(chunk)

        asyncio.run(run_task())

        elapsed = time.time() - start_time

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("Response:")
        click.echo("=" * 60)
        click.echo("".join(results))
        click.echo("=" * 60)

        click.echo(f"\n{click.style('✓', fg='green')} Test passed")
        click.echo(f"Execution time: {elapsed:.2f}s")

    except Exception as e:
        click.echo(f"\n{click.style('✗', fg='red')} Test failed: {e}")
        logger.error("provider_test_failed", provider=provider_name, error=str(e))
        raise click.Abort()


@providers_cli.command("migrate-check")
@click.option("--project-root", type=click.Path(), default=".", help="Project root")
def migrate_check(project_root: str):
    """
    Check if project needs migration.

    Scans project configuration and identifies any needed changes
    for provider abstraction.

    Examples:
        gao-dev providers migrate-check
        gao-dev providers migrate-check --project-root /path/to/project
    """
    migrator = ConfigMigrator(Path(project_root))

    click.echo("\nScanning project configuration...\n")

    report = migrator.analyze_project()

    # Display findings
    click.echo(f"Agent configurations found: {report.num_agents}")
    click.echo(f"Need migration: {report.num_need_migration}")
    click.echo()

    if report.num_need_migration == 0:
        click.echo(click.style("✓ No migration needed", fg="green"))
        return

    click.echo(click.style("Migration needed:", fg="yellow"))
    for item in report.migration_items:
        click.echo(f"  - {item.file}: {item.description}")

    click.echo(f"\nRun 'gao-dev providers migrate-config' to apply changes")


@providers_cli.command("migrate-config")
@click.option("--project-root", type=click.Path(), default=".", help="Project root")
@click.option("--dry-run", is_flag=True, help="Show changes without applying")
@click.option("--backup/--no-backup", default=True, help="Create backup")
def migrate_config(project_root: str, dry_run: bool, backup: bool):
    """
    Migrate agent configurations for provider abstraction.

    Updates agent YAML files to include provider fields.
    Creates backup before making changes.

    Examples:
        gao-dev providers migrate-config --dry-run
        gao-dev providers migrate-config
        gao-dev providers migrate-config --no-backup
    """
    migrator = ConfigMigrator(Path(project_root))

    if dry_run:
        click.echo("\nDry run mode - no changes will be made\n")

    click.echo("Analyzing configurations...")
    report = migrator.analyze_project()

    if report.num_need_migration == 0:
        click.echo(click.style("✓ No migration needed", fg="green"))
        return

    # Confirm
    if not dry_run:
        click.confirm(
            f"\nMigrate {report.num_need_migration} configuration(s)?",
            abort=True,
        )

    # Create backup
    if backup and not dry_run:
        backup_path = migrator.create_backup()
        click.echo(f"\nBackup created: {backup_path}")

    # Migrate
    click.echo("\nMigrating configurations...")

    for item in report.migration_items:
        if dry_run:
            click.echo(f"Would migrate: {item.file}")
            click.echo(f"  {item.description}")
        else:
            try:
                migrator.migrate_file(item.file)
                click.echo(f"{click.style('✓', fg='green')} {item.file}")
            except Exception as e:
                click.echo(f"{click.style('✗', fg='red')} {item.file}: {e}")

    if not dry_run:
        click.echo(f"\n{click.style('✓', fg='green')} Migration complete")


@providers_cli.command("rollback")
@click.option("--project-root", type=click.Path(), default=".", help="Project root")
@click.option("--backup-id", help="Specific backup ID to restore")
@click.option("--last", is_flag=True, help="Rollback to last backup automatically")
@click.option("--list", "list_backups", is_flag=True, help="List available backups")
def rollback_config(project_root: str, backup_id: Optional[str], last: bool, list_backups: bool):
    """
    Rollback configuration to previous backup.

    Restores agent YAML files and defaults.yaml from a backup
    created during migration.

    Examples:
        gao-dev providers rollback --list
        gao-dev providers rollback --last
        gao-dev providers rollback --backup-id 20251104_143022
    """
    migrator = ConfigMigrator(Path(project_root))

    # List backups
    if list_backups:
        backups = migrator.list_backups()

        if not backups:
            click.echo("No backups found")
            return

        click.echo("\nAvailable backups:\n")
        click.echo(f"{'Backup ID':<25} {'Created':<25} {'Files':<10}")
        click.echo("-" * 65)

        for backup in backups:
            click.echo(
                f"{backup['id']:<25} {backup['created']:<25} {backup['num_files']:<10}"
            )

        click.echo(f"\nTotal: {len(backups)} backup(s)")
        click.echo("\nTo restore a backup:")
        click.echo("  gao-dev providers rollback --backup-id <id>")
        click.echo("  gao-dev providers rollback --last")
        return

    # Determine which backup to restore
    if last:
        backup_to_restore = migrator.get_last_backup()
        if not backup_to_restore:
            click.echo(f"{click.style('✗', fg='red')} No backups found")
            return
        click.echo(f"Restoring last backup: {backup_to_restore['id']}")

    elif backup_id:
        backup_to_restore = migrator.get_backup(backup_id)
        if not backup_to_restore:
            click.echo(f"{click.style('✗', fg='red')} Backup '{backup_id}' not found")
            click.echo("\nRun 'gao-dev providers rollback --list' to see available backups")
            return
        click.echo(f"Restoring backup: {backup_id}")

    else:
        click.echo(f"{click.style('!', fg='yellow')} Please specify a backup:")
        click.echo("  --last                 Restore last backup")
        click.echo("  --backup-id <id>       Restore specific backup")
        click.echo("  --list                 List available backups")
        return

    # Validate backup
    if not migrator.validate_backup(backup_to_restore):
        click.echo(f"{click.style('✗', fg='red')} Backup validation failed")
        click.echo("Backup may be corrupted or incomplete")
        return

    # Show backup details
    click.echo(f"\nBackup details:")
    click.echo(f"  Created: {backup_to_restore['created']}")
    click.echo(f"  Files: {backup_to_restore['num_files']}")
    click.echo(f"  Size: {backup_to_restore['size_mb']:.2f} MB")

    # Confirm
    click.confirm(
        f"\n{click.style('WARNING:', fg='yellow')} This will overwrite current configuration. Continue?",
        abort=True,
    )

    # Perform rollback
    try:
        click.echo("\nRestoring configuration...")

        restored_files = migrator.restore_backup(backup_to_restore['id'])

        for file in restored_files:
            click.echo(f"{click.style('✓', fg='green')} Restored: {file}")

        # Verify configuration after rollback
        click.echo("\nVerifying configuration...")
        if migrator.verify_configuration():
            click.echo(f"\n{click.style('✓', fg='green')} Rollback complete!")
            click.echo(f"Configuration restored from backup: {backup_to_restore['id']}")
        else:
            click.echo(f"\n{click.style('⚠', fg='yellow')} Rollback complete but configuration validation failed")
            click.echo("Run 'gao-dev providers validate' for details")

    except Exception as e:
        click.echo(f"\n{click.style('✗', fg='red')} Rollback failed: {e}")
        logger.error("rollback_failed", error=str(e))
        raise click.Abort()


@providers_cli.command("setup")
def setup_wizard():
    """
    Interactive provider setup wizard.

    Guides you through provider selection and configuration.

    Example:
        gao-dev providers setup
    """
    wizard = ProviderSetupWizard()

    click.echo("\n" + "=" * 60)
    click.echo(" Provider Setup Wizard")
    click.echo("=" * 60 + "\n")

    try:
        wizard.run()
        click.echo(f"\n{click.style('✓', fg='green')} Setup complete!")
    except KeyboardInterrupt:
        click.echo("\n\nSetup cancelled")
        raise click.Abort()


@providers_cli.command("switch")
@click.argument("provider_name")
@click.option("--confirm/--no-confirm", default=True, help="Confirm before switching")
def switch_provider(provider_name: str, confirm: bool):
    """
    Switch default provider.

    Changes the default provider in defaults.yaml.

    Examples:
        gao-dev providers switch opencode
        gao-dev providers switch direct-api --no-confirm
    """
    from gao_dev.core.config_loader import ConfigLoader

    # Validate provider exists
    factory = ProviderFactory()
    if provider_name not in factory.list_providers():
        click.echo(f"{click.style('✗', fg='red')} Provider '{provider_name}' not found")
        click.echo(f"\nAvailable providers:")
        for name in factory.list_providers():
            click.echo(f"  - {name}")
        raise click.Abort()

    # Load current config
    config_loader = ConfigLoader()
    current_provider = config_loader.get_default_provider()

    if current_provider == provider_name:
        click.echo(f"Already using '{provider_name}' as default provider")
        return

    # Confirm
    if confirm:
        click.confirm(
            f"\nSwitch default provider from '{current_provider}' to '{provider_name}'?",
            abort=True,
        )

    # Switch
    try:
        config_loader.set_default_provider(provider_name)
        click.echo(f"\n{click.style('✓', fg='green')} Default provider changed to '{provider_name}'")

    except Exception as e:
        click.echo(f"\n{click.style('✗', fg='red')} Failed to switch provider: {e}")
        raise click.Abort()


@providers_cli.command("info")
@click.argument("provider_name")
def provider_info(provider_name: str):
    """
    Show detailed provider information.

    Displays configuration options, supported models, and examples.

    Examples:
        gao-dev providers info claude-code
        gao-dev providers info opencode
    """
    factory = ProviderFactory()

    try:
        info = factory.get_provider_info(provider_name)

        click.echo(f"\n{'='*60}")
        click.echo(f" {info['name']}")
        click.echo(f"{'='*60}\n")

        click.echo(f"Description: {info['description']}")
        click.echo(f"Requires CLI: {'Yes' if info['requires_cli'] else 'No'}")
        click.echo(f"Requires API Key: {'Yes' if info['requires_api_key'] else 'No'}")

        click.echo("\nSupported Models:")
        for model in info['models']:
            click.echo(f"  - {model}")

        click.echo("\nConfiguration Options:")
        for option, description in info['config_options'].items():
            click.echo(f"  {option}: {description}")

        click.echo("\nExample Usage:")
        click.echo(info['example'])
        click.echo()

    except Exception as e:
        click.echo(f"{click.style('✗', fg='red')} Provider '{provider_name}' not found")
        raise click.Abort()
```

#### Step 2: Create Validation Module

**File**: `gao_dev/core/providers/validation.py`

```python
"""Provider validation utilities."""

from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

from gao_dev.core.providers.factory import ProviderFactory

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of provider validation."""

    valid: bool
    message: str
    warnings: List[str]


class ProviderValidator:
    """Validates provider configurations and availability."""

    def __init__(self):
        """Initialize validator."""
        self.factory = ProviderFactory()

    def validate_provider(self, provider_name: str) -> ValidationResult:
        """
        Validate a specific provider.

        Args:
            provider_name: Name of provider

        Returns:
            Validation result
        """
        warnings = []

        try:
            # Try to create provider
            provider = self.factory.create_provider(provider_name)

            # Validate provider
            if not provider.validate():
                return ValidationResult(
                    valid=False,
                    message="Provider validation failed",
                    warnings=warnings,
                )

            return ValidationResult(
                valid=True,
                message="Provider configured correctly",
                warnings=warnings,
            )

        except Exception as e:
            return ValidationResult(
                valid=False,
                message=str(e),
                warnings=warnings,
            )

    def validate_all_providers(self) -> Dict[str, ValidationResult]:
        """
        Validate all registered providers.

        Returns:
            Dict of provider name -> validation result
        """
        results = {}
        provider_names = self.factory.list_providers()

        for name in provider_names:
            results[name] = self.validate_provider(name)

        return results
```

#### Step 3: Create Migration Module

**File**: `gao_dev/core/providers/migration.py`

```python
"""Configuration migration utilities."""

from pathlib import Path
from typing import List
from dataclasses import dataclass
import shutil
import yaml
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MigrationItem:
    """Item needing migration."""

    file: Path
    description: str


@dataclass
class MigrationReport:
    """Report of migration analysis."""

    num_agents: int
    num_need_migration: int
    migration_items: List[MigrationItem]


class ConfigMigrator:
    """Migrates agent configurations for provider abstraction."""

    def __init__(self, project_root: Path):
        """Initialize migrator."""
        self.project_root = project_root
        self.agents_dir = project_root / "gao_dev" / "config" / "agents"

    def analyze_project(self) -> MigrationReport:
        """
        Analyze project configuration.

        Returns:
            Migration report
        """
        if not self.agents_dir.exists():
            return MigrationReport(0, 0, [])

        agent_files = list(self.agents_dir.glob("*.yaml"))
        migration_items = []

        for agent_file in agent_files:
            # Load agent config
            with open(agent_file) as f:
                config = yaml.safe_load(f)

            # Check if needs migration
            agent_config = config.get("agent", {}).get("configuration", {})

            if "provider" not in agent_config:
                migration_items.append(
                    MigrationItem(
                        file=agent_file,
                        description="Add provider field",
                    )
                )

        return MigrationReport(
            num_agents=len(agent_files),
            num_need_migration=len(migration_items),
            migration_items=migration_items,
        )

    def create_backup(self) -> Path:
        """
        Create backup of agent configurations.

        Returns:
            Path to backup directory
        """
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / f".gao-backup-{timestamp}"

        shutil.copytree(self.agents_dir, backup_dir / "agents")

        logger.info("backup_created", backup_dir=backup_dir)
        return backup_dir

    def migrate_file(self, agent_file: Path) -> None:
        """
        Migrate a single agent configuration file.

        Args:
            agent_file: Path to agent config file
        """
        # Load config
        with open(agent_file) as f:
            config = yaml.safe_load(f)

        # Add provider field if missing
        agent_config = config.get("agent", {}).get("configuration", {})

        if "provider" not in agent_config:
            agent_config["provider"] = "claude-code"  # Default

        # Write back
        with open(agent_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info("config_migrated", file=agent_file)

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.

        Returns:
            List of backup metadata dictionaries
        """
        backups = []

        for backup_dir in self.project_root.glob(".gao-backup-*"):
            if not backup_dir.is_dir():
                continue

            # Extract timestamp from directory name
            backup_id = backup_dir.name.replace(".gao-backup-", "")

            # Get backup metadata
            num_files = len(list((backup_dir / "agents").glob("*.yaml")))
            size_bytes = sum(f.stat().st_size for f in (backup_dir / "agents").rglob("*") if f.is_file())

            backups.append({
                "id": backup_id,
                "path": backup_dir,
                "created": backup_id,  # Timestamp is in format YYYYMMDD_HHMMSS
                "num_files": num_files,
                "size_mb": size_bytes / (1024 * 1024),
            })

        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b["created"], reverse=True)
        return backups

    def get_last_backup(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent backup.

        Returns:
            Backup metadata dict, or None if no backups exist
        """
        backups = self.list_backups()
        return backups[0] if backups else None

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific backup by ID.

        Args:
            backup_id: Backup timestamp ID (e.g., "20251104_143022")

        Returns:
            Backup metadata dict, or None if not found
        """
        backups = self.list_backups()
        for backup in backups:
            if backup["id"] == backup_id:
                return backup
        return None

    def validate_backup(self, backup: Dict[str, Any]) -> bool:
        """
        Validate backup integrity.

        Args:
            backup: Backup metadata dict

        Returns:
            True if backup is valid and complete
        """
        backup_path = backup["path"]

        # Check backup directory exists
        if not backup_path.exists():
            logger.error("backup_validation_failed", reason="directory_not_found")
            return False

        # Check agents subdirectory exists
        agents_backup = backup_path / "agents"
        if not agents_backup.exists():
            logger.error("backup_validation_failed", reason="agents_dir_not_found")
            return False

        # Check at least one YAML file exists
        yaml_files = list(agents_backup.glob("*.yaml"))
        if not yaml_files:
            logger.error("backup_validation_failed", reason="no_yaml_files")
            return False

        # Validate each YAML file can be loaded
        for yaml_file in yaml_files:
            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                logger.error(
                    "backup_validation_failed",
                    reason="corrupted_yaml",
                    file=str(yaml_file),
                    error=str(e)
                )
                return False

        return True

    def restore_backup(self, backup_id: str) -> List[Path]:
        """
        Restore configuration from backup.

        Args:
            backup_id: Backup timestamp ID

        Returns:
            List of restored file paths

        Raises:
            ValueError: If backup not found or invalid
        """
        backup = self.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Backup '{backup_id}' not found")

        if not self.validate_backup(backup):
            raise ValueError(f"Backup '{backup_id}' validation failed")

        backup_path = backup["path"]
        agents_backup = backup_path / "agents"

        restored_files = []

        # Restore each agent configuration file
        for backup_file in agents_backup.glob("*.yaml"):
            target_file = self.agents_dir / backup_file.name

            # Copy backup file to target location
            shutil.copy2(backup_file, target_file)
            restored_files.append(target_file)

            logger.info(
                "file_restored",
                source=str(backup_file),
                target=str(target_file)
            )

        logger.info(
            "backup_restored",
            backup_id=backup_id,
            num_files=len(restored_files)
        )

        return restored_files

    def verify_configuration(self) -> bool:
        """
        Verify configuration after migration or rollback.

        Returns:
            True if configuration is valid
        """
        try:
            # Check agents directory exists
            if not self.agents_dir.exists():
                return False

            # Load and validate each agent config
            for agent_file in self.agents_dir.glob("*.yaml"):
                with open(agent_file) as f:
                    config = yaml.safe_load(f)

                # Basic validation
                if "agent" not in config:
                    return False
                if "configuration" not in config["agent"]:
                    return False

            return True

        except Exception as e:
            logger.error("configuration_verification_failed", error=str(e))
            return False
```

---

## Testing Strategy

### CLI Command Tests
- Each command has unit tests
- Integration tests with real configurations
- Error scenario tests

### Migration Tests
- Dry-run testing
- Backup creation
- Rollback testing

### Validation Tests
- Provider availability checks
- Configuration validation
- Health checks

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Provider validation command working
- [ ] Provider list command working
- [ ] Provider info command working
- [ ] Provider test command working
- [ ] Migration check command working
- [ ] Configuration migration tool working
- [ ] Provider setup wizard working
- [ ] Provider compare command working
- [ ] Provider switch command working
- [ ] Health check integration complete
- [ ] Help text complete
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- Story 11.14 (Comprehensive Testing) - MUST be complete

**Downstream**:
- Story 11.16 (Production Documentation) - documents migration commands

---

## Notes

- **User-Friendly**: Clear, helpful error messages
- **Safety**: Backup before migration
- **Validation**: Test providers before migration
- **Guidance**: Interactive wizard for beginners
- **Automation**: One-command migration where possible
- **Documentation**: Examples in help text

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Migration Guide: `docs/provider-migration-guide.md`
- Story 11.14: `story-11.14.md` (Comprehensive Testing)
