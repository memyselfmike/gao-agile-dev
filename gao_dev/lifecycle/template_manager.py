"""
Document Template Manager.

This module provides document template management with automatic frontmatter,
naming convention, and governance metadata integration.

Implements 5S Standardize principle by providing consistent document templates.
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import yaml

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.governance import DocumentGovernance


class DocumentTemplateManager:
    """
    Manage document templates with proper frontmatter.

    This class provides template-based document creation with:
    - Automatic filename generation using naming convention
    - Auto-populated YAML frontmatter with governance fields
    - Auto-registration in document lifecycle system
    - Variable validation and substitution

    Implements 5S Standardize principle.
    """

    def __init__(
        self,
        templates_dir: Path,
        doc_manager: DocumentLifecycleManager,
        naming_convention: DocumentNamingConvention,
        governance: DocumentGovernance,
    ):
        """
        Initialize template manager.

        Args:
            templates_dir: Directory containing templates
            doc_manager: Document lifecycle manager
            naming_convention: Naming convention helper
            governance: Governance manager
        """
        self.templates_dir = Path(templates_dir)
        self.doc_mgr = doc_manager
        self.naming = naming_convention
        self.governance = governance

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def create_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        output_dir: Path,
    ) -> Path:
        """
        Create new document from template.

        This method:
        1. Validates required variables
        2. Generates filename using naming convention
        3. Auto-populates frontmatter with governance fields
        4. Renders template
        5. Writes file
        6. Auto-registers in lifecycle system
        7. Auto-assigns ownership

        Args:
            template_name: Template name (e.g., "prd", "architecture")
            variables: Template variables (subject, author, feature, epic, etc.)
            output_dir: Where to create the document

        Returns:
            Path to created document

        Raises:
            ValueError: If template not found or variables invalid

        Example:
            >>> manager.create_from_template(
            ...     "prd",
            ...     {
            ...         "subject": "user-authentication",
            ...         "author": "John",
            ...         "feature": "auth-system",
            ...         "related_docs": ["docs/ARCHITECTURE.md"]
            ...     },
            ...     Path("docs/features/auth-system")
            ... )
            # Creates: docs/features/auth-system/PRD_user-authentication_2024-11-05_v1.0.md
        """
        # Validate required variables
        self._validate_variables(template_name, variables)

        # Load template
        try:
            template = self.jinja_env.get_template(f"{template_name}.md.j2")
        except TemplateNotFound:
            raise ValueError(
                f"Template not found: {template_name}\n"
                f"Available templates: {', '.join(self.list_templates())}"
            )

        # Generate filename using naming convention
        doc_type = self._get_doc_type(template_name)
        filename = self.naming.generate_filename(
            doc_type=doc_type,
            subject=variables["subject"],
            version=variables.get("version", "1.0"),
            adr_number=variables.get("adr_number") if template_name == "adr" else None,
        )

        # Generate frontmatter with governance fields
        frontmatter = self._generate_frontmatter(template_name, variables)

        # Add current date if not in variables
        if "created_date" not in variables:
            variables["created_date"] = datetime.now().strftime("%Y-%m-%d")

        # Merge frontmatter into template variables
        template_vars = {
            **variables,
            "frontmatter_yaml": yaml.dump(frontmatter, default_flow_style=False),
        }

        # Render template
        rendered = template.render(**template_vars)

        # Write file
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / filename
        file_path.write_text(rendered, encoding="utf-8")

        # Auto-register in lifecycle system
        document = self.doc_mgr.register_document(
            path=file_path,
            doc_type=doc_type.lower(),
            author=variables["author"],
            metadata=frontmatter,
        )

        # Auto-assign ownership from governance
        self.governance.auto_assign_ownership(document)

        return file_path

    def _generate_frontmatter(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate YAML frontmatter with governance fields.

        Auto-populates based on governance config and template type.

        Args:
            template_name: Template name
            variables: Template variables

        Returns:
            Dictionary with frontmatter fields
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Get governance config for document type
        doc_type = self._get_doc_type(template_name)
        governance_config = self.governance.config["document_governance"]
        ownership = governance_config["ownership"].get(doc_type.lower(), {})
        review_cadence = governance_config["review_cadence"].get(doc_type.lower(), 90)

        # Calculate review due date
        if review_cadence != -1:
            review_due = (datetime.now() + timedelta(days=review_cadence)).strftime(
                "%Y-%m-%d"
            )
        else:
            review_due = None

        # Build frontmatter
        frontmatter = {
            "title": variables["subject"],
            "doc_type": doc_type,
            "status": variables.get("status", "draft"),  # Allow overriding status
            "author": variables["author"],
            "owner": ownership.get("approved_by"),
            "reviewer": ownership.get("reviewed_by"),
            "created_date": today,
            "last_updated": today,
            "version": variables.get("version", "1.0"),
            "review_due_date": review_due,
            "related_docs": variables.get("related_docs", []),
            "tags": variables.get("tags", []),
            "retention_policy": self._get_retention_policy(doc_type.lower()),
        }

        # Add feature/epic if provided
        if "feature" in variables:
            frontmatter["feature"] = variables["feature"]
        if "epic" in variables:
            frontmatter["epic"] = variables["epic"]

        # Remove None values
        return {k: v for k, v in frontmatter.items() if v is not None}

    def _get_retention_policy(self, doc_type: str) -> str:
        """
        Get retention policy name for document type.

        Args:
            doc_type: Document type

        Returns:
            Retention policy name
        """
        # Map to policy names from retention_policies.yaml
        policy_map = {
            "prd": "permanent_product_decisions",
            "architecture": "permanent_architecture",
            "story": "archive_after_1_year",
            "epic": "archive_after_1_year",
            "qa_report": "compliance_5_years",
            "test_report": "archive_after_1_year",
            "postmortem": "permanent_learning",
            "adr": "permanent_architecture",
            "runbook": "archive_after_1_year",
        }
        return policy_map.get(doc_type.lower(), "default_archive_90_days")

    def _validate_variables(
        self, template_name: str, variables: Dict[str, Any]
    ) -> None:
        """
        Validate required variables for template.

        Args:
            template_name: Template name
            variables: Variables to validate

        Raises:
            ValueError: If required variables are missing
        """
        required = ["subject", "author"]

        # Template-specific requirements
        if template_name == "story":
            required.append("epic")
        elif template_name == "adr":
            required.extend(["decision", "status"])

        missing = [v for v in required if v not in variables]

        if missing:
            raise ValueError(
                f"Missing required variables for template '{template_name}': "
                f"{', '.join(missing)}"
            )

    def _get_doc_type(self, template_name: str) -> str:
        """
        Get document type from template name.

        Args:
            template_name: Template name

        Returns:
            Document type in uppercase
        """
        # Map template names to doc types
        type_map = {
            "prd": "PRD",
            "architecture": "ARCHITECTURE",
            "epic": "EPIC",
            "story": "STORY",
            "adr": "ADR",
            "postmortem": "POSTMORTEM",
            "runbook": "RUNBOOK",
        }
        return type_map.get(template_name.lower(), template_name.upper())

    def list_templates(self) -> List[str]:
        """
        List available templates.

        Returns:
            List of template names (without .md.j2 extension)
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for f in self.templates_dir.glob("*.md.j2"):
            # Remove .md.j2 extension (f.stem gives us "name.md", need just "name")
            name = f.stem  # e.g., "prd.md"
            if name.endswith(".md"):
                name = name[:-3]  # Remove ".md"
            templates.append(name)

        return sorted(templates)

    def get_template_variables(self, template_name: str) -> Dict[str, Any]:
        """
        Get variable information for a template.

        Args:
            template_name: Template name

        Returns:
            Dictionary with variable information

        Example:
            >>> manager.get_template_variables("prd")
            {
                "required": ["subject", "author"],
                "optional": ["feature", "related_docs", "tags", "version"],
                "description": "Product Requirements Document"
            }
        """
        # Define template metadata
        template_info = {
            "prd": {
                "description": "Product Requirements Document",
                "required": ["subject", "author"],
                "optional": ["feature", "related_docs", "tags", "version"],
            },
            "architecture": {
                "description": "System Architecture",
                "required": ["subject", "author"],
                "optional": ["feature", "related_docs", "tags", "version"],
            },
            "epic": {
                "description": "Epic Definition",
                "required": ["subject", "author"],
                "optional": ["feature", "related_docs", "tags", "version"],
            },
            "story": {
                "description": "User Story",
                "required": ["subject", "author", "epic"],
                "optional": ["feature", "related_docs", "tags", "version"],
            },
            "adr": {
                "description": "Architecture Decision Record",
                "required": ["subject", "author", "decision", "status"],
                "optional": ["adr_number", "related_docs", "tags"],
            },
            "postmortem": {
                "description": "Incident Postmortem",
                "required": ["subject", "author"],
                "optional": ["incident_date", "related_docs", "tags"],
            },
            "runbook": {
                "description": "Operational Runbook",
                "required": ["subject", "author"],
                "optional": ["related_docs", "tags", "version"],
            },
        }

        return template_info.get(
            template_name,
            {
                "description": "Unknown template",
                "required": ["subject", "author"],
                "optional": [],
            },
        )
