"""
CLI commands for Document Lifecycle Management.

This module provides CLI commands for managing document lifecycle operations,
including archival, cleanup, and retention policy reporting.
"""

import click
from pathlib import Path
import sys

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.archival import ArchivalManager
from gao_dev.lifecycle.governance import DocumentGovernance


def _get_lifecycle_manager() -> tuple[DocumentLifecycleManager, ArchivalManager, DocumentGovernance]:
    """
    Initialize and return lifecycle, archival, and governance managers.

    Returns:
        Tuple of (DocumentLifecycleManager, ArchivalManager, DocumentGovernance)

    Raises:
        click.ClickException: If initialization fails
    """
    try:
        # Use default paths relative to project root
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"
        archive_dir = project_root / ".archive"
        policies_path = Path(__file__).parent.parent / "config" / "retention_policies.yaml"
        governance_path = Path(__file__).parent.parent / "config" / "governance.yaml"

        # Ensure directories exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Initialize registry and managers
        registry = DocumentRegistry(db_path)
        doc_manager = DocumentLifecycleManager(registry, archive_dir)
        archival_manager = ArchivalManager(doc_manager, policies_path)
        governance_manager = DocumentGovernance(doc_manager, governance_path)

        return doc_manager, archival_manager, governance_manager

    except Exception as e:
        raise click.ClickException(f"Failed to initialize lifecycle manager: {e}")


@click.group()
def lifecycle():
    """
    Document lifecycle management commands.

    Manage document archival, cleanup, and retention policies.
    """
    pass


@lifecycle.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview what would be archived without making changes",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information about each action",
)
def archive(dry_run: bool, verbose: bool):
    """
    Archive obsolete documents based on retention policies.

    This command evaluates all OBSOLETE documents and archives those that
    meet the retention policy criteria. Archived documents are moved to
    the .archive/ directory and their state is updated to ARCHIVED.

    Use --dry-run to preview what would be archived without making changes.

    Example:
        gao-dev lifecycle archive --dry-run
        gao-dev lifecycle archive
    """
    try:
        doc_manager, archival_manager, _ = _get_lifecycle_manager()

        if dry_run:
            click.echo(">> DRY RUN: Previewing archival actions...")
        else:
            click.echo(">> Archiving obsolete documents...")

        # Perform archival
        actions = archival_manager.archive_obsolete_documents(dry_run=dry_run)

        if not actions:
            click.echo("  [OK] No documents eligible for archival.")
            return

        # Display results
        click.echo(f"\n  {len(actions)} document(s) {'would be' if dry_run else ''} archived:\n")

        for action in actions:
            if verbose:
                click.echo(f"  - {action.document.path}")
                click.echo(f"    Type: {action.document.type.value}")
                click.echo(f"    State: {action.document.state.value}")
                click.echo(f"    Reason: {action.reason}")
                if action.document.metadata.get("tags"):
                    click.echo(f"    Tags: {', '.join(action.document.metadata['tags'])}")
                click.echo()
            else:
                click.echo(f"  - {action.document.path}: {action.reason}")

        if dry_run:
            click.echo("\n[INFO] This was a dry run. No changes were made.")
            click.echo("       Run without --dry-run to actually archive documents.")
        else:
            click.echo(f"\n[OK] Successfully archived {len(actions)} document(s).")

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Archive operation failed: {e}")


@lifecycle.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview what would be deleted without making changes",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information about each action",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt (use with caution)",
)
def cleanup(dry_run: bool, verbose: bool, confirm: bool):
    """
    Delete archived documents past retention period.

    This command evaluates all ARCHIVED documents and permanently deletes
    those that:
    1. Have exceeded their retention period
    2. Are marked as delete_after_archive=true in policy
    3. Do NOT have compliance tags (compliance docs are NEVER deleted)

    WARNING: This is a destructive operation. Deleted documents cannot be
    recovered. Use --dry-run first to preview what would be deleted.

    Example:
        gao-dev lifecycle cleanup --dry-run
        gao-dev lifecycle cleanup --confirm
    """
    try:
        doc_manager, archival_manager, _ = _get_lifecycle_manager()

        if dry_run:
            click.echo(">> DRY RUN: Previewing cleanup actions...")
        else:
            click.echo(">> Cleaning up expired archived documents...")

        # Perform cleanup evaluation
        actions = archival_manager.cleanup_expired_documents(dry_run=True)

        if not actions:
            click.echo("  [OK] No documents eligible for deletion.")
            return

        # Display what would be deleted
        click.echo(f"\n  {len(actions)} document(s) {'would be' if dry_run else ''} deleted:\n")

        for action in actions:
            if verbose:
                click.echo(f"  - {action.document.path}")
                click.echo(f"    Type: {action.document.type.value}")
                click.echo(f"    State: {action.document.state.value}")
                click.echo(f"    Reason: {action.reason}")
                if action.document.metadata.get("tags"):
                    click.echo(f"    Tags: {', '.join(action.document.metadata['tags'])}")
                click.echo()
            else:
                click.echo(f"  - {action.document.path}: {action.reason}")

        if dry_run:
            click.echo("\n[INFO] This was a dry run. No changes were made.")
            click.echo("       Run without --dry-run to actually delete documents.")
            return

        # Confirmation prompt (unless --confirm flag is used)
        if not confirm:
            click.echo("\n[WARNING] This will PERMANENTLY delete the documents listed above.")
            click.echo("          This action CANNOT be undone.")
            if not click.confirm("\nAre you sure you want to proceed?"):
                click.echo("[CANCELLED] No documents were deleted.")
                return

        # Actually perform deletion
        actions = archival_manager.cleanup_expired_documents(dry_run=False)
        click.echo(f"\n[OK] Successfully deleted {len(actions)} document(s).")

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Cleanup operation failed: {e}")


@lifecycle.command()
@click.option(
    "--format",
    type=click.Choice(["markdown", "csv"], case_sensitive=False),
    default="markdown",
    help="Output format (markdown or csv)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save report to file instead of printing to console",
)
def retention_report(format: str, output: str):
    """
    Generate retention policy compliance report.

    This command analyzes all documents and reports their retention status,
    grouped by document type. The report shows:
    - Documents eligible for archival
    - Documents eligible for deletion
    - Days until next action
    - Compliance tags protecting documents

    Use --format csv to generate a CSV report suitable for compliance audits.

    Example:
        gao-dev lifecycle retention-report
        gao-dev lifecycle retention-report --format csv -o report.csv
    """
    try:
        doc_manager, archival_manager, _ = _get_lifecycle_manager()

        click.echo(">> Generating retention policy report...")

        # Generate report
        report = archival_manager.generate_retention_report(format=format.lower())

        # Output to file or console
        if output:
            output_path = Path(output)
            output_path.write_text(report, encoding="utf-8")
            click.echo(f"\n[OK] Report saved to: {output_path}")
        else:
            click.echo("\n" + report)

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Report generation failed: {e}")


@lifecycle.command()
@click.argument("doc_type")
def show_policy(doc_type: str):
    """
    Show retention policy for a document type.

    Display the configured retention policy for the specified document type,
    including archival thresholds, retention periods, and compliance settings.

    Example:
        gao-dev lifecycle show-policy prd
        gao-dev lifecycle show-policy story
    """
    try:
        doc_manager, archival_manager, _ = _get_lifecycle_manager()

        policy = archival_manager.get_policy(doc_type)

        if not policy:
            click.echo(f"[ERROR] No retention policy configured for document type: {doc_type}")
            click.echo("\nAvailable document types:")
            for pol in archival_manager.list_policies():
                click.echo(f"  - {pol.doc_type}")
            sys.exit(1)

        # Display policy details
        click.echo(f"\n>> Retention Policy: {doc_type.upper()}\n")
        click.echo(f"Archive to Obsolete:   {policy.archive_to_obsolete} days" +
                   (" (never)" if policy.archive_to_obsolete == -1 else ""))
        click.echo(f"Obsolete to Archive:   {policy.obsolete_to_archive} days" +
                   (" (never)" if policy.obsolete_to_archive == -1 else ""))
        click.echo(f"Archive Retention:     {policy.archive_retention} days" +
                   (" (forever)" if policy.archive_retention == -1 else ""))
        click.echo(f"Delete After Archive:  {'Yes' if policy.delete_after_archive else 'No'}")

        if policy.compliance_tags:
            click.echo(f"\nCompliance Tags (prevent deletion):")
            for tag in policy.compliance_tags:
                click.echo(f"  - {tag}")
        else:
            click.echo(f"\nCompliance Tags:       None")

        click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to show policy: {e}")


@lifecycle.command()
def list_policies():
    """
    List all configured retention policies.

    Display a summary of all document types with configured retention policies.

    Example:
        gao-dev lifecycle list-policies
    """
    try:
        doc_manager, archival_manager, _ = _get_lifecycle_manager()

        policies = archival_manager.list_policies()

        if not policies:
            click.echo("[WARNING] No retention policies configured.")
            return

        click.echo(f"\n>> Configured Retention Policies ({len(policies)})\n")

        for policy in sorted(policies, key=lambda p: p.doc_type):
            click.echo(f"{policy.doc_type.upper():20} | " +
                       f"Obs->Arc: {str(policy.obsolete_to_archive):4} days | " +
                       f"Retention: {str(policy.archive_retention):4} days | " +
                       f"Delete: {'Yes' if policy.delete_after_archive else 'No':3} | " +
                       f"Compliance: {len(policy.compliance_tags)} tags")

        click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to list policies: {e}")


@lifecycle.command()
@click.option(
    "--owner",
    "-o",
    help="Filter by document owner",
)
@click.option(
    "--overdue-only",
    is_flag=True,
    help="Show only overdue reviews",
)
def review_due(owner: str, overdue_only: bool):
    """
    Show documents needing review.

    Lists documents that are due for review based on their review cadence.
    By default, shows documents due within 7 days. Use --overdue-only to
    see only documents past their review date.

    Example:
        gao-dev lifecycle review-due
        gao-dev lifecycle review-due --owner John
        gao-dev lifecycle review-due --overdue-only
    """
    try:
        _, _, governance_manager = _get_lifecycle_manager()

        click.echo(">> Checking documents needing review...")

        documents = governance_manager.check_review_due(
            owner=owner, include_overdue_only=overdue_only
        )

        if not documents:
            if overdue_only:
                click.echo("  [OK] No overdue reviews found.")
            else:
                click.echo("  [OK] No reviews due within 7 days.")
            return

        # Display results
        status = "overdue" if overdue_only else "due within 7 days"
        click.echo(f"\n  {len(documents)} document(s) {status}:\n")

        for doc in documents:
            days_overdue = governance_manager._days_overdue(doc)
            status_marker = "[OVERDUE]" if days_overdue > 0 else "[DUE SOON]"

            click.echo(f"  {status_marker} {doc.path}")
            click.echo(f"    Type: {doc.type.value}")
            click.echo(f"    Owner: {doc.owner or 'N/A'}")
            click.echo(f"    Reviewer: {doc.reviewer or 'N/A'}")
            click.echo(f"    Due Date: {doc.review_due_date or 'N/A'}")

            if days_overdue > 0:
                click.echo(f"    Days Overdue: {days_overdue}")

            priority = doc.metadata.get("priority", "N/A")
            if priority != "N/A":
                click.echo(f"    Priority: {priority}")

            click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to check reviews due: {e}")


@lifecycle.command()
@click.argument("doc_id", type=int)
@click.option(
    "--notes",
    "-n",
    help="Review notes",
)
def mark_reviewed(doc_id: int, notes: str):
    """
    Mark a document as reviewed.

    Records the review in the document's history and calculates the next
    review due date based on the document's review cadence.

    Example:
        gao-dev lifecycle mark-reviewed 123
        gao-dev lifecycle mark-reviewed 123 --notes "All good"
    """
    try:
        _, _, governance_manager = _get_lifecycle_manager()

        click.echo(f">> Marking document {doc_id} as reviewed...")

        # Get current user (in real implementation, would get from auth)
        # For now, use a placeholder
        reviewer = "CLI User"

        review = governance_manager.mark_reviewed(doc_id, reviewer, notes)

        click.echo(f"\n  [OK] Document marked as reviewed.")
        click.echo(f"    Document ID: {review.document_id}")
        click.echo(f"    Reviewer: {review.reviewer}")
        click.echo(f"    Reviewed At: {review.reviewed_at}")

        if review.next_review_due:
            click.echo(f"    Next Review Due: {review.next_review_due}")
        else:
            click.echo(f"    Next Review Due: Never (immutable document)")

        if review.notes:
            click.echo(f"    Notes: {review.notes}")

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to mark document as reviewed: {e}")


@lifecycle.command()
@click.option(
    "--format",
    type=click.Choice(["markdown", "csv"], case_sensitive=False),
    default="markdown",
    help="Output format (markdown or csv)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save report to file instead of printing to console",
)
def governance_report(format: str, output: str):
    """
    Generate governance compliance report.

    The report includes:
    - Documents needing review (overdue and upcoming)
    - Documents without owners
    - Review statistics by document type

    Use --format csv to generate a CSV report suitable for compliance audits.

    Example:
        gao-dev lifecycle governance-report
        gao-dev lifecycle governance-report --format csv -o governance.csv
    """
    try:
        _, _, governance_manager = _get_lifecycle_manager()

        click.echo(">> Generating governance compliance report...")

        # Generate report
        report = governance_manager.generate_governance_report(format=format.lower())

        # Output to file or console
        if output:
            output_path = Path(output)
            output_path.write_text(report, encoding="utf-8")
            click.echo(f"\n[OK] Report saved to: {output_path}")
        else:
            click.echo("\n" + report)

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Governance report generation failed: {e}")


# Register the lifecycle group as a subcommand
def register_lifecycle_commands(cli_group):
    """
    Register lifecycle commands with the main CLI group.

    Args:
        cli_group: Click group to register commands with
    """
    cli_group.add_command(lifecycle)
