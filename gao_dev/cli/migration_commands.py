"""Migration CLI commands for git-integrated hybrid architecture.

This module provides CLI commands for migrating existing projects to the
git-integrated hybrid architecture and checking/repairing consistency.

Epic: 27 - Integration & Migration
Story: 27.3 - Create Migration Tools

Commands:
    - gao-dev migrate: Migrate project to hybrid architecture
    - gao-dev migrate --dry-run: Preview migration without changes
    - gao-dev consistency-check: Check file-DB consistency
    - gao-dev consistency-repair: Repair consistency issues
"""

import sys
from pathlib import Path
from datetime import datetime

import click
import structlog

from gao_dev.core.services.git_migration_manager import (
    GitMigrationManager,
    MigrationResult,
    GitMigrationManagerError
)
from gao_dev.core.services.git_consistency_checker import (
    GitAwareConsistencyChecker,
    ConsistencyReport,
    ConsistencyIssue,
    GitAwareConsistencyCheckerError
)
from gao_dev.core.state.migrations.add_features_table import AddFeaturesTableMigration

logger = structlog.get_logger()


@click.group()
def migrate_group():
    """Migration and consistency management commands."""
    pass


@migrate_group.command(name="migrate")
@click.option(
    "--project",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Project root path (default: current directory)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be migrated without making changes"
)
@click.option(
    "--no-branch",
    is_flag=True,
    default=False,
    help="Skip creating migration branch"
)
@click.option(
    "--auto-merge",
    is_flag=True,
    default=False,
    help="Automatically merge migration branch after success"
)
@click.option(
    "--db-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Database path (default: .gao-dev/documents.db)"
)
def migrate_project(
    project: Path | None,
    dry_run: bool,
    no_branch: bool,
    auto_merge: bool,
    db_path: Path | None
):
    """
    Migrate existing project to git-integrated hybrid architecture.

    This command orchestrates a safe migration from file-based state management
    to the hybrid (file + database) architecture with git transaction safety.

    Migration phases:
      1. Create state tables in database
      2. Backfill epics from filesystem
      3. Backfill stories from filesystem (git-inferred state)
      4. Validate migration completeness

    Each phase creates a git commit checkpoint for rollback safety.

    Examples:
        # Preview migration
        gao-dev migrate --dry-run

        # Migrate current project
        gao-dev migrate

        # Migrate specific project
        gao-dev migrate --project /path/to/project

        # Migrate without branch isolation
        gao-dev migrate --no-branch

        # Migrate and auto-merge
        gao-dev migrate --auto-merge
    """
    try:
        # Determine project path
        project_path = project or Path.cwd()

        # Determine database path
        if db_path is None:
            db_path = project_path / ".gao-dev" / "documents.db"

        click.echo(f"\n{'='*70}")
        click.echo(f"GAO-Dev Migration to Hybrid Architecture")
        click.echo(f"{'='*70}\n")

        click.echo(f"Project Path: {project_path}")
        click.echo(f"Database Path: {db_path}")
        click.echo(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
        click.echo()

        # Dry run mode
        if dry_run:
            _perform_dry_run(project_path, db_path)
            return

        # Confirm before proceeding
        if not click.confirm("Proceed with migration?", default=True):
            click.echo("Migration cancelled.")
            return

        # Initialize migration manager
        click.echo("Initializing migration manager...")
        manager = GitMigrationManager(
            db_path=db_path,
            project_path=project_path
        )

        # Run migration
        click.echo("\nStarting migration...")
        click.echo("-" * 70)

        result: MigrationResult = manager.migrate_to_hybrid_architecture(
            create_branch=not no_branch,
            auto_merge=auto_merge
        )

        # Display results
        click.echo()
        _display_migration_result(result)

        # Exit code
        sys.exit(0 if result.success else 1)

    except GitMigrationManagerError as e:
        click.echo(f"\n[ERROR] Migration failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        logger.exception("migration_command_error", error=str(e))
        sys.exit(1)


@migrate_group.command(name="consistency-check")
@click.option(
    "--project",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Project root path (default: current directory)"
)
@click.option(
    "--db-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Database path (default: .gao-dev/documents.db)"
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show detailed issue information"
)
def check_consistency(
    project: Path | None,
    db_path: Path | None,
    verbose: bool
):
    """
    Check file-database consistency using git awareness.

    This command detects inconsistencies between filesystem and database state
    by analyzing git status and comparing with database records.

    Checks performed:
      1. Uncommitted changes (working tree dirty)
      2. Orphaned DB records (file deleted but still in DB)
      3. Unregistered files (file exists but not in DB)
      4. State mismatches (DB state != git-inferred state)

    Examples:
        # Check current project
        gao-dev consistency-check

        # Check specific project
        gao-dev consistency-check --project /path/to/project

        # Verbose output with details
        gao-dev consistency-check --verbose
    """
    try:
        # Determine project path
        project_path = project or Path.cwd()

        # Determine database path
        if db_path is None:
            db_path = project_path / ".gao-dev" / "documents.db"

        click.echo(f"\n{'='*70}")
        click.echo(f"GAO-Dev Consistency Check")
        click.echo(f"{'='*70}\n")

        click.echo(f"Project Path: {project_path}")
        click.echo(f"Database Path: {db_path}")
        click.echo()

        # Check database exists
        if not db_path.exists():
            click.echo("[WARNING] Database does not exist. Project may not be migrated.")
            click.echo(f"  Run 'gao-dev migrate' to migrate project to hybrid architecture.")
            sys.exit(0)

        # Initialize checker
        click.echo("Initializing consistency checker...")
        checker = GitAwareConsistencyChecker(
            db_path=db_path,
            project_path=project_path
        )

        # Run check
        click.echo("Checking consistency...")
        click.echo("-" * 70)

        report: ConsistencyReport = checker.check_consistency()

        # Display results
        click.echo()
        _display_consistency_report(report, verbose=verbose)

        # Exit code
        sys.exit(0 if not report.has_issues else 1)

    except GitAwareConsistencyCheckerError as e:
        click.echo(f"\n[ERROR] Consistency check failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        logger.exception("consistency_check_command_error", error=str(e))
        sys.exit(1)


@migrate_group.command(name="consistency-repair")
@click.option(
    "--project",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Project root path (default: current directory)"
)
@click.option(
    "--db-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Database path (default: .gao-dev/documents.db)"
)
@click.option(
    "--no-commit",
    is_flag=True,
    default=False,
    help="Skip creating git commit after repair"
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be repaired without making changes"
)
def repair_consistency(
    project: Path | None,
    db_path: Path | None,
    no_commit: bool,
    dry_run: bool
):
    """
    Repair file-database consistency issues.

    This command repairs detected inconsistencies by treating files as the
    source of truth. It will:
      - Register untracked files in database
      - Remove orphaned database records
      - Update stale database records
      - Create atomic git commit after repair

    Examples:
        # Preview repairs
        gao-dev consistency-repair --dry-run

        # Repair current project
        gao-dev consistency-repair

        # Repair specific project
        gao-dev consistency-repair --project /path/to/project

        # Repair without git commit
        gao-dev consistency-repair --no-commit
    """
    try:
        # Determine project path
        project_path = project or Path.cwd()

        # Determine database path
        if db_path is None:
            db_path = project_path / ".gao-dev" / "documents.db"

        click.echo(f"\n{'='*70}")
        click.echo(f"GAO-Dev Consistency Repair")
        click.echo(f"{'='*70}\n")

        click.echo(f"Project Path: {project_path}")
        click.echo(f"Database Path: {db_path}")
        click.echo(f"Mode: {'DRY RUN' if dry_run else 'LIVE REPAIR'}")
        click.echo()

        # Check database exists
        if not db_path.exists():
            click.echo("[ERROR] Database does not exist. Nothing to repair.")
            click.echo(f"  Run 'gao-dev migrate' to migrate project to hybrid architecture.")
            sys.exit(1)

        # Initialize checker
        click.echo("Initializing consistency checker...")
        checker = GitAwareConsistencyChecker(
            db_path=db_path,
            project_path=project_path
        )

        # Run check first
        click.echo("Checking consistency...")
        report: ConsistencyReport = checker.check_consistency()

        if not report.has_issues:
            click.echo("\n[OK] No consistency issues found. Nothing to repair.")
            sys.exit(0)

        # Display issues
        click.echo()
        _display_consistency_report(report, verbose=True)

        # Dry run mode
        if dry_run:
            click.echo("\n[DRY RUN] Would repair the above issues.")
            sys.exit(0)

        # Confirm before proceeding
        click.echo()
        if not click.confirm("Proceed with repair?", default=True):
            click.echo("Repair cancelled.")
            return

        # Perform repair
        click.echo("\nRepairing consistency issues...")
        click.echo("-" * 70)

        checker.repair(
            report=report,
            create_commit=not no_commit
        )

        click.echo("\n[OK] Consistency issues repaired successfully!")

        if not no_commit:
            click.echo("  Git commit created: 'chore: repair file-database consistency'")

        sys.exit(0)

    except GitAwareConsistencyCheckerError as e:
        click.echo(f"\n[ERROR] Consistency repair failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        logger.exception("consistency_repair_command_error", error=str(e))
        sys.exit(1)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _perform_dry_run(project_path: Path, db_path: Path) -> None:
    """Perform dry run analysis of migration."""
    click.echo("Analyzing project for migration...")
    click.echo("-" * 70)

    # Check for epics
    epics_dir = project_path / "docs" / "epics"
    epic_count = 0
    if epics_dir.exists():
        epic_files = list(epics_dir.glob("epic-*.md"))
        epic_count = len(epic_files)
        click.echo(f"\nEpics found: {epic_count}")
        for epic_file in sorted(epic_files)[:5]:  # Show first 5
            click.echo(f"  - {epic_file.name}")
        if epic_count > 5:
            click.echo(f"  ... and {epic_count - 5} more")
    else:
        click.echo("\nEpics found: 0")
        click.echo("  (No docs/epics directory)")

    # Check for stories
    stories_dir = project_path / "docs" / "stories"
    story_count = 0
    if stories_dir.exists():
        story_files = list(stories_dir.glob("**/story-*.md"))
        story_count = len(story_files)
        click.echo(f"\nStories found: {story_count}")
        for story_file in sorted(story_files)[:5]:  # Show first 5
            click.echo(f"  - {story_file.relative_to(stories_dir)}")
        if story_count > 5:
            click.echo(f"  ... and {story_count - 5} more")
    else:
        click.echo("\nStories found: 0")
        click.echo("  (No docs/stories directory)")

    # Check database
    click.echo(f"\nDatabase: {db_path}")
    if db_path.exists():
        click.echo("  [WARNING] Database already exists. Migration may fail.")
        click.echo("  Backup existing database before migrating.")
    else:
        click.echo("  [OK] Database does not exist. Ready for migration.")

    # Summary
    click.echo("\n" + "=" * 70)
    click.echo("Migration Summary (Dry Run)")
    click.echo("=" * 70)
    click.echo(f"  Epics to migrate: {epic_count}")
    click.echo(f"  Stories to migrate: {story_count}")
    click.echo(f"  Database path: {db_path}")
    click.echo()
    click.echo("To perform actual migration, run:")
    click.echo("  gao-dev migrate")


def _display_migration_result(result: MigrationResult) -> None:
    """Display migration result in formatted output."""
    click.echo("=" * 70)

    if result.success:
        click.echo("Migration Status: SUCCESS")
        click.echo("=" * 70)
        click.echo(f"  Phase Completed: {result.phase_completed}/4")
        click.echo(f"  Epics Migrated: {result.epics_count}")
        click.echo(f"  Stories Migrated: {result.stories_count}")
        click.echo()
        click.echo(f"Summary: {result.summary}")

        if result.checkpoints:
            click.echo("\nGit Checkpoints:")
            for phase, sha in result.checkpoints.items():
                click.echo(f"  {phase}: {sha[:8]}")

        click.echo("\n[OK] Migration completed successfully!")

    else:
        click.echo("Migration Status: FAILED")
        click.echo("=" * 70)
        click.echo(f"  Phase Failed: {result.phase_completed}")
        click.echo(f"  Error: {result.error}")

        if result.rollback_performed:
            click.echo("\n[WARNING] Automatic rollback performed.")
            click.echo("  Project state restored to pre-migration.")

        if result.checkpoints:
            click.echo("\nGit Checkpoints (before rollback):")
            for phase, sha in result.checkpoints.items():
                click.echo(f"  {phase}: {sha[:8]}")

        click.echo("\n[ERROR] Migration failed. Check logs for details.")


def _display_consistency_report(report: ConsistencyReport, verbose: bool = False) -> None:
    """Display consistency report in formatted output."""
    click.echo("=" * 70)
    click.echo(f"Consistency Check Report - {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo("=" * 70)

    if not report.has_issues:
        click.echo("\n[OK] No consistency issues found!")
        click.echo("  File and database state are in sync.")
        return

    click.echo(f"\n[WARNING] Found {report.total_issues} consistency issues:")

    # Uncommitted changes
    if report.uncommitted_changes:
        click.echo(f"\n  Uncommitted Changes: {len(report.uncommitted_changes)}")
        if verbose:
            for file_path in report.uncommitted_changes[:10]:
                click.echo(f"    - {file_path}")
            if len(report.uncommitted_changes) > 10:
                click.echo(f"    ... and {len(report.uncommitted_changes) - 10} more")

    # Orphaned records
    if report.orphaned_records:
        click.echo(f"\n  Orphaned DB Records: {len(report.orphaned_records)}")
        if verbose:
            for issue in report.orphaned_records[:10]:
                click.echo(f"    - {issue.description}")
            if len(report.orphaned_records) > 10:
                click.echo(f"    ... and {len(report.orphaned_records) - 10} more")

    # Unregistered files
    if report.unregistered_files:
        click.echo(f"\n  Unregistered Files: {len(report.unregistered_files)}")
        if verbose:
            for issue in report.unregistered_files[:10]:
                click.echo(f"    - {issue.description}")
            if len(report.unregistered_files) > 10:
                click.echo(f"    ... and {len(report.unregistered_files) - 10} more")

    # State mismatches
    if report.state_mismatches:
        click.echo(f"\n  State Mismatches: {len(report.state_mismatches)}")
        if verbose:
            for issue in report.state_mismatches[:10]:
                click.echo(f"    - {issue.description}")
                click.echo(f"      DB: {issue.db_state} | Git: {issue.git_state}")
            if len(report.state_mismatches) > 10:
                click.echo(f"    ... and {len(report.state_mismatches) - 10} more")

    click.echo()
    click.echo("To repair these issues, run:")
    click.echo("  gao-dev consistency-repair")


@migrate_group.command(name="migrate-features")
@click.option(
    "--project",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Project root path (default: current directory)"
)
@click.option(
    "--db-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Database path (default: .gao-dev/documents.db)"
)
@click.option(
    "--rollback",
    is_flag=True,
    default=False,
    help="Rollback features table migration"
)
def migrate_features(
    project: Path | None,
    db_path: Path | None,
    rollback: bool
):
    """
    Migrate database to add features table.

    This command adds the features table, indexes, triggers, and audit trail
    to an existing database. It is idempotent and safe to run multiple times.

    Features added:
      - features table with constraints
      - Indexes for performance (scope, status, scale_level)
      - Auto-timestamp triggers (created_at, completed_at)
      - Audit trail (features_audit table)

    Examples:
        # Apply migration
        gao-dev migrate-features

        # Apply migration to specific project
        gao-dev migrate-features --project /path/to/project

        # Rollback migration
        gao-dev migrate-features --rollback
    """
    try:
        # Determine project path
        project_path = project or Path.cwd()

        # Determine database path
        if db_path is None:
            db_path = project_path / ".gao-dev" / "documents.db"

        click.echo(f"\n{'='*70}")
        click.echo(f"GAO-Dev Features Table Migration")
        click.echo(f"{'='*70}\n")

        click.echo(f"Project Path: {project_path}")
        click.echo(f"Database Path: {db_path}")
        click.echo(f"Mode: {'ROLLBACK' if rollback else 'APPLY'}")
        click.echo()

        # Check database exists
        if not db_path.exists():
            click.echo("[ERROR] Database does not exist.")
            click.echo(f"  Run 'gao-dev migrate' to create database first.")
            sys.exit(1)

        # Initialize migration
        click.echo("Initializing features table migration...")
        migration = AddFeaturesTableMigration(db_path)

        if rollback:
            # Rollback migration
            click.echo("Rolling back migration...")
            success = migration.rollback()

            if success:
                click.echo("\n[OK] Features table migration rolled back successfully!")
            else:
                click.echo("\n[INFO] Migration was not applied, nothing to rollback.")
        else:
            # Apply migration
            click.echo("Applying migration...")
            success = migration.apply()

            if success:
                click.echo("\n[OK] Features table migration applied successfully!")
                click.echo("\nCreated:")
                click.echo("  - features table")
                click.echo("  - features_audit table")
                click.echo("  - Indexes (scope, status, scale_level)")
                click.echo("  - Triggers (auto-timestamps, audit trail)")
            else:
                click.echo("\n[INFO] Migration already applied, no changes made.")

        sys.exit(0)

    except RuntimeError as e:
        click.echo(f"\n[ERROR] Migration failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        logger.exception("migrate_features_command_error", error=str(e))
        sys.exit(1)
