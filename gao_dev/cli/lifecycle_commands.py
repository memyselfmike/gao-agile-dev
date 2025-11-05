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
from gao_dev.lifecycle.template_manager import DocumentTemplateManager
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.search import DocumentSearch
from gao_dev.lifecycle.models import DocumentState


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


def _get_template_manager() -> DocumentTemplateManager:
    """
    Initialize and return template manager.

    Returns:
        DocumentTemplateManager instance

    Raises:
        click.ClickException: If initialization fails
    """
    try:
        # Get lifecycle manager
        doc_manager, _, governance_manager = _get_lifecycle_manager()

        # Initialize template manager
        templates_dir = Path(__file__).parent.parent / "config" / "templates"
        naming_convention = DocumentNamingConvention()
        template_manager = DocumentTemplateManager(
            templates_dir=templates_dir,
            doc_manager=doc_manager,
            naming_convention=naming_convention,
            governance=governance_manager,
        )

        return template_manager

    except Exception as e:
        raise click.ClickException(f"Failed to initialize template manager: {e}")


def _get_search_manager() -> DocumentSearch:
    """
    Initialize and return search manager.

    Returns:
        DocumentSearch instance

    Raises:
        click.ClickException: If initialization fails
    """
    try:
        # Use default paths relative to project root
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize registry and search
        registry = DocumentRegistry(db_path)
        search_manager = DocumentSearch(registry)

        return search_manager

    except Exception as e:
        raise click.ClickException(f"Failed to initialize search manager: {e}")


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


@lifecycle.command()
@click.argument("template")
@click.option("--subject", required=True, help="Document subject (e.g., 'user-authentication')")
@click.option("--author", required=True, help="Document author")
@click.option("--feature", help="Feature name (optional)")
@click.option("--epic", type=int, help="Epic number (required for stories)")
@click.option("--version", default="1.0", help="Document version (default: 1.0)")
@click.option("--output-dir", type=click.Path(), help="Output directory (default: current dir)")
@click.option("--related-docs", multiple=True, help="Related document paths (can be specified multiple times)")
@click.option("--tags", multiple=True, help="Document tags (can be specified multiple times)")
@click.option("--adr-number", type=int, help="ADR number (for ADR templates)")
@click.option("--decision", help="Decision text (for ADR templates)")
@click.option("--status", default="Proposed", help="Status (for ADR templates, default: Proposed)")
def create(
    template: str,
    subject: str,
    author: str,
    feature: str,
    epic: int,
    version: str,
    output_dir: str,
    related_docs: tuple,
    tags: tuple,
    adr_number: int,
    decision: str,
    status: str,
):
    """
    Create document from template.

    Creates a new document from a template with automatic frontmatter,
    naming convention, and lifecycle registration.

    Examples:
        gao-dev lifecycle create prd --subject "user-auth" --author "John"
        gao-dev lifecycle create story --subject "login-flow" --author "Bob" --epic 5
        gao-dev lifecycle create adr --subject "database-choice" --author "Winston" --adr-number 1 --decision "Use PostgreSQL"
    """
    try:
        template_manager = _get_template_manager()

        # Build variables dictionary
        variables = {
            "subject": subject,
            "author": author,
            "version": version,
        }

        # Add optional variables
        if feature:
            variables["feature"] = feature
        if epic:
            variables["epic"] = epic
        if related_docs:
            variables["related_docs"] = list(related_docs)
        if tags:
            variables["tags"] = list(tags)
        if adr_number:
            variables["adr_number"] = adr_number
        if decision:
            variables["decision"] = decision
        if status:
            variables["status"] = status

        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path.cwd()

        click.echo(f">> Creating {template} document: {subject}")

        # Create document from template
        file_path = template_manager.create_from_template(
            template_name=template, variables=variables, output_dir=output_path
        )

        # Display success message
        click.echo(f"\n[OK] Document created successfully!")
        click.echo(f"  File: {file_path}")
        click.echo(f"  Path: {file_path.absolute()}")

        # Show governance info
        doc_type = template_manager._get_doc_type(template)
        governance_config = template_manager.governance.config["document_governance"]
        ownership = governance_config["ownership"].get(doc_type.lower(), {})

        if ownership:
            owner = ownership.get("approved_by")
            reviewer = ownership.get("reviewed_by")
            if owner:
                click.echo(f"  Owner: {owner}")
            if reviewer:
                click.echo(f"  Reviewer: {reviewer}")

        click.echo()

    except ValueError as e:
        raise click.ClickException(str(e))
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to create document: {e}")


@lifecycle.command()
def list_templates():
    """
    List available document templates.

    Shows all available templates with their descriptions.

    Example:
        gao-dev lifecycle list-templates
    """
    try:
        template_manager = _get_template_manager()

        templates = template_manager.list_templates()

        if not templates:
            click.echo("[WARNING] No templates found.")
            return

        click.echo(f"\n>> Available Document Templates ({len(templates)})\n")

        for template_name in templates:
            info = template_manager.get_template_variables(template_name)
            click.echo(f"{template_name.upper():20} - {info['description']}")

            # Show required variables
            required = info.get("required", [])
            if required:
                click.echo(f"{'':22}Required: {', '.join(required)}")

            # Show optional variables
            optional = info.get("optional", [])
            if optional:
                click.echo(f"{'':22}Optional: {', '.join(optional)}")

            click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to list templates: {e}")


@lifecycle.command()
@click.argument("query")
@click.option("--type", "doc_type", help="Filter by document type (prd, architecture, etc.)")
@click.option(
    "--state",
    type=click.Choice(["draft", "active", "obsolete", "archived"], case_sensitive=False),
    help="Filter by document state",
)
@click.option("--tags", multiple=True, help="Filter by tags (can be specified multiple times)")
@click.option("--limit", type=int, default=50, help="Max results to return (default: 50)")
@click.option("--with-content", is_flag=True, help="Search file content (slower but more accurate)")
def search(query: str, doc_type: str, state: str, tags: tuple, limit: int, with_content: bool):
    """
    Full-text search for documents.

    Search across document paths, content, and metadata using FTS5.
    Results are ranked by relevance.

    Examples:
        gao-dev lifecycle search "authentication security"
        gao-dev lifecycle search "api design" --type architecture --state active
        gao-dev lifecycle search "testing" --tags epic-3 --tags unit-tests
        gao-dev lifecycle search "user authentication" --with-content
    """
    try:
        search_manager = _get_search_manager()

        click.echo(f">> Searching for: {query}")

        # Convert state string to enum if provided
        state_enum = DocumentState(state) if state else None

        # Perform search
        if with_content:
            results = search_manager.search_with_content(
                query=query,
                doc_type=doc_type,
                state=state_enum,
                tags=list(tags) if tags else None,
                limit=limit,
            )
        else:
            results = search_manager.search(
                query=query,
                doc_type=doc_type,
                state=state_enum,
                tags=list(tags) if tags else None,
                limit=limit,
            )

        if not results:
            click.echo("\n  [INFO] No documents found matching your query.")
            return

        # Display results as table
        click.echo(f"\n  Found {len(results)} document(s):\n")
        click.echo(f"  {'Path':<60} {'Type':<15} {'State':<10} {'Score':<10}")
        click.echo(f"  {'-' * 60} {'-' * 15} {'-' * 10} {'-' * 10}")

        for doc, score in results:
            # Truncate path if too long
            path_display = doc.path if len(doc.path) <= 60 else "..." + doc.path[-57:]
            click.echo(
                f"  {path_display:<60} {doc.type.value:<15} {doc.state.value:<10} {score:<10.4f}"
            )

        click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Search failed: {e}")


@lifecycle.command()
@click.argument("doc_id", type=int)
@click.option("--limit", type=int, default=10, help="Max related documents to return (default: 10)")
def related(doc_id: int, limit: int):
    """
    Find related documents by content similarity.

    Uses FTS5 to find documents with similar content to the specified document.
    Results are ranked by similarity score.

    Examples:
        gao-dev lifecycle related 123
        gao-dev lifecycle related 456 --limit 5
    """
    try:
        search_manager = _get_search_manager()

        click.echo(f">> Finding documents related to document ID: {doc_id}")

        # Get source document info
        registry = search_manager.registry
        source_doc = registry.get_document(doc_id)

        click.echo(f"  Source: {source_doc.path}")
        click.echo(f"  Type: {source_doc.type.value}")
        click.echo(f"  State: {source_doc.state.value}\n")

        # Find related documents
        results = search_manager.get_related_documents(doc_id, limit=limit)

        if not results:
            click.echo("  [INFO] No related documents found.")
            return

        # Display results as table
        click.echo(f"  Found {len(results)} related document(s):\n")
        click.echo(f"  {'Path':<60} {'Type':<15} {'State':<10} {'Score':<10}")
        click.echo(f"  {'-' * 60} {'-' * 15} {'-' * 10} {'-' * 10}")

        for doc, score in results:
            # Truncate path if too long
            path_display = doc.path if len(doc.path) <= 60 else "..." + doc.path[-57:]
            click.echo(
                f"  {path_display:<60} {doc.type.value:<15} {doc.state.value:<10} {score:<10.4f}"
            )

        click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to find related documents: {e}")


@lifecycle.command()
@click.option("--tags", multiple=True, required=True, help="Tags to search (can be specified multiple times)")
@click.option("--match-all", is_flag=True, help="Require all tags (default: match any tag)")
@click.option("--limit", type=int, default=50, help="Max results to return (default: 50)")
def search_tags(tags: tuple, match_all: bool, limit: int):
    """
    Search documents by tags.

    By default, matches documents with ANY of the specified tags.
    Use --match-all to require documents to have ALL tags.

    Examples:
        gao-dev lifecycle search-tags --tags epic-3 --tags security
        gao-dev lifecycle search-tags --tags prd --tags active --match-all
    """
    try:
        search_manager = _get_search_manager()

        mode = "ALL" if match_all else "ANY"
        click.echo(f">> Searching for documents with {mode} tags: {', '.join(tags)}")

        # Perform tag search
        results = search_manager.search_by_tags(
            tags=list(tags), match_all=match_all, limit=limit
        )

        if not results:
            click.echo("\n  [INFO] No documents found matching the specified tags.")
            return

        # Display results as table
        click.echo(f"\n  Found {len(results)} document(s):\n")
        click.echo(f"  {'Path':<60} {'Type':<15} {'State':<10} {'Tags':<30}")
        click.echo(f"  {'-' * 60} {'-' * 15} {'-' * 10} {'-' * 30}")

        for doc in results:
            # Truncate path if too long
            path_display = doc.path if len(doc.path) <= 60 else "..." + doc.path[-57:]
            tags_display = ", ".join(doc.get_tags()[:3])  # Show first 3 tags
            if len(doc.get_tags()) > 3:
                tags_display += "..."
            click.echo(
                f"  {path_display:<60} {doc.type.value:<15} {doc.state.value:<10} {tags_display:<30}"
            )

        click.echo()

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Tag search failed: {e}")


# Register the lifecycle group as a subcommand
def register_lifecycle_commands(cli_group):
    """
    Register lifecycle commands with the main CLI group.

    Args:
        cli_group: Click group to register commands with
    """
    cli_group.add_command(lifecycle)
