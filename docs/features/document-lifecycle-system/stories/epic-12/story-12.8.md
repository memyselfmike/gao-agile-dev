# Story 12.8 (NEW): Document Templates System

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 3
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** 1

---

## Story Description

Create document template system that generates documents from Jinja2 templates with proper frontmatter, naming convention, and governance metadata. Reduces document creation time by 80% and ensures consistency (5S: Standardize - templates for common documents).

---

## Business Value

The templates system provides:
- **Efficiency**: 80% reduction in document creation time
- **Consistency**: All documents follow standard format with proper frontmatter
- **Quality**: Auto-populated governance fields (owner, reviewer, review_due_date)
- **Compliance**: Standard naming convention enforced automatically
- **Integration**: Auto-registers documents in lifecycle system

---

## Acceptance Criteria

### Template Management
- [ ] `DocumentTemplateManager` class for template operations
- [ ] `create_from_template(template_name, variables, output_dir)` generates document
- [ ] Templates stored in `gao_dev/config/templates/`
- [ ] Jinja2 for variable substitution
- [ ] Templates support all document types

### Automatic Features
- [ ] Auto-generates filename using `DocumentNamingConvention`
- [ ] Auto-populates YAML frontmatter with governance fields:
  - owner, reviewer (from governance config)
  - review_due_date (from review cadence)
  - created_date, last_updated (current date)
  - version (default: 1.0)
  - related_docs (from variables)
  - tags (from variables)
  - retention_policy (from document type)
- [ ] Auto-registers document in lifecycle system
- [ ] All in one operation (atomic)

### Templates to Create
- [ ] `prd.md.j2` - Product Requirements Document
- [ ] `architecture.md.j2` - System Architecture
- [ ] `epic.md.j2` - Epic Definition
- [ ] `story.md.j2` - User Story
- [ ] `adr.md.j2` - Architecture Decision Record
- [ ] `postmortem.md.j2` - Incident Postmortem
- [ ] `runbook.md.j2` - Operational Runbook

### Template Variables
- [ ] Common variables: subject, author, feature, epic, related_docs, tags
- [ ] Template-specific variables supported
- [ ] Variable validation before rendering
- [ ] Clear error messages for missing required variables

### CLI Commands
- [ ] `gao-dev lifecycle create <template> --subject "..." --author "..."`
- [ ] `gao-dev lifecycle create prd --subject "user-auth" --author "John" --feature "auth-system"`
- [ ] `gao-dev lifecycle create story --subject "login-flow" --epic 5 --author "Bob"`
- [ ] `gao-dev lifecycle list-templates` - Show available templates
- [ ] Output shows: filename created, path, owner assigned

### Template Features
- [ ] Templates include @doc: references for context injection (prepares for Epic 13)
- [ ] Frontmatter matches schema from Story 12.1
- [ ] Sections for each document type (e.g., PRD has Goals, Features, Success Criteria)
- [ ] Comments in templates guide users on what to fill in

**Test Coverage:** >80%

---

## Technical Notes

### Implementation

```python
# gao_dev/lifecycle/template_manager.py
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import yaml

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.governance import DocumentGovernance

class DocumentTemplateManager:
    """
    Manage document templates with proper frontmatter.

    Implements 5S Standardize principle.
    """

    def __init__(
        self,
        templates_dir: Path,
        doc_manager: DocumentLifecycleManager,
        naming_convention: DocumentNamingConvention,
        governance: DocumentGovernance
    ):
        """
        Initialize template manager.

        Args:
            templates_dir: Directory containing templates
            doc_manager: Document lifecycle manager
            naming_convention: Naming convention helper
            governance: Governance manager
        """
        self.templates_dir = templates_dir
        self.doc_mgr = doc_manager
        self.naming = naming_convention
        self.governance = governance
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))

    def create_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """
        Create new document from template.

        Args:
            template_name: Template name (e.g., "prd", "architecture")
            variables: Template variables (subject, author, feature, epic, etc.)
            output_dir: Where to create the document

        Returns:
            Path to created document

        Example:
            create_from_template(
                "prd",
                {
                    "subject": "user-authentication",
                    "author": "John",
                    "feature": "auth-system",
                    "related_docs": ["docs/ARCHITECTURE.md"]
                },
                Path("docs/features/auth-system")
            )
            # Creates: docs/features/auth-system/PRD_user-authentication_2024-11-05_v1.0.md
        """
        # Validate required variables
        self._validate_variables(template_name, variables)

        # Load template
        try:
            template = self.jinja_env.get_template(f"{template_name}.md.j2")
        except TemplateNotFound:
            raise ValueError(f"Template not found: {template_name}")

        # Generate filename using naming convention
        doc_type = variables.get('doc_type', template_name.upper())
        filename = self.naming.generate_filename(
            doc_type=doc_type,
            subject=variables['subject'],
            version=variables.get('version', '1.0')
        )

        # Generate frontmatter with governance fields
        frontmatter = self._generate_frontmatter(template_name, variables)

        # Merge frontmatter into template variables
        template_vars = {
            **variables,
            'frontmatter_yaml': yaml.dump(frontmatter, default_flow_style=False)
        }

        # Render template
        rendered = template.render(**template_vars)

        # Write file
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / filename
        file_path.write_text(rendered, encoding='utf-8')

        # Auto-register in lifecycle system
        document = self.doc_mgr.register_document(
            path=file_path,
            doc_type=variables.get('doc_type', template_name),
            author=variables['author'],
            metadata=frontmatter
        )

        # Auto-assign ownership from governance
        self.governance.auto_assign_ownership(document)

        return file_path

    def _generate_frontmatter(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate YAML frontmatter with governance fields.

        Auto-populates based on governance config and template type.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Get governance config for document type
        doc_type = variables.get('doc_type', template_name)
        governance_config = self.governance.config['document_governance']
        ownership = governance_config['ownership'].get(doc_type, {})
        review_cadence = governance_config['review_cadence'].get(doc_type, 90)

        # Calculate review due date
        if review_cadence != -1:
            review_due = (datetime.now() + timedelta(days=review_cadence)).strftime("%Y-%m-%d")
        else:
            review_due = None

        # Build frontmatter
        frontmatter = {
            "title": variables['subject'],
            "doc_type": doc_type.upper(),
            "status": "draft",
            "author": variables['author'],
            "owner": ownership.get('approved_by'),
            "reviewer": ownership.get('reviewed_by'),
            "created_date": today,
            "last_updated": today,
            "version": variables.get('version', '1.0'),
            "review_due_date": review_due,
            "related_docs": variables.get('related_docs', []),
            "tags": variables.get('tags', []),
            "retention_policy": self._get_retention_policy(doc_type),
            "feature": variables.get('feature'),
            "epic": variables.get('epic'),
        }

        # Remove None values
        return {k: v for k, v in frontmatter.items() if v is not None}

    def _get_retention_policy(self, doc_type: str) -> str:
        """Get retention policy name for document type."""
        # Map to policy names from retention_policies.yaml
        policy_map = {
            'prd': 'permanent_product_decisions',
            'architecture': 'permanent_architecture',
            'story': 'archive_after_1_year',
            'qa_report': 'compliance_5_years',
            'postmortem': 'permanent_learning',
        }
        return policy_map.get(doc_type.lower(), 'default_archive_90_days')

    def _validate_variables(self, template_name: str, variables: Dict[str, Any]) -> None:
        """Validate required variables for template."""
        required = ['subject', 'author']

        if template_name == 'story':
            required.append('epic')

        missing = [v for v in required if v not in variables]

        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

    def list_templates(self) -> list:
        """List available templates."""
        return [
            f.stem for f in self.templates_dir.glob('*.md.j2')
        ]
```

### Example Template: PRD

```jinja2
{# gao_dev/config/templates/prd.md.j2 #}
---
{{ frontmatter_yaml }}
---

# Product Requirements Document
## {{ subject }}

**Author:** {{ author }}
**Date:** {{ created_date }}
**Status:** Draft
**Version:** {{ version }}

---

## Executive Summary

<!-- Provide a brief overview of the product/feature -->

### Vision

<!-- What is the vision for this product/feature? -->

### The Problem

<!-- What problem does this solve? -->

### The Solution

<!-- High-level solution description -->

---

## Goals & Success Criteria

### Goals

1. Goal 1
2. Goal 2
3. Goal 3

### Success Criteria

- [ ] Success criterion 1
- [ ] Success criterion 2
- [ ] Success criterion 3

---

## User Stories

### Primary User Stories

**US-1: As a [user type], I want [goal] so that [benefit]**

<!-- Add more user stories -->

---

## Features & Requirements

### Feature 1: [Name]

**Requirements:**
- REQ-1.1: Requirement description
- REQ-1.2: Requirement description

### Feature 2: [Name]

**Requirements:**
- REQ-2.1: Requirement description

---

## Non-Functional Requirements

### Performance
- Requirement 1
- Requirement 2

### Security
- Requirement 1
- Requirement 2

### Usability
- Requirement 1

---

## Dependencies

### Internal Dependencies
- Dependency 1
- Dependency 2

### External Dependencies
- Dependency 1

---

## Risks & Mitigations

### Risk 1: [Description]
**Severity**: High/Medium/Low
**Mitigation**: Mitigation strategy

---

## Timeline & Milestones

| Milestone | Target Date | Status |
|-----------|------------|--------|
| Milestone 1 | YYYY-MM-DD | Planned |
| Milestone 2 | YYYY-MM-DD | Planned |

---

## Related Documents

{% if related_docs %}
{% for doc in related_docs %}
- [{{ doc }}]({{ doc }})
{% endfor %}
{% endif %}

---

*Generated from template on {{ created_date }}*
```

**Files to Create:**
- `gao_dev/lifecycle/template_manager.py`
- `gao_dev/config/templates/prd.md.j2`
- `gao_dev/config/templates/architecture.md.j2`
- `gao_dev/config/templates/epic.md.j2`
- `gao_dev/config/templates/story.md.j2`
- `gao_dev/config/templates/adr.md.j2`
- `gao_dev/config/templates/postmortem.md.j2`
- `gao_dev/config/templates/runbook.md.j2`
- `gao_dev/cli/lifecycle_commands.py` (enhanced with create command)
- `tests/lifecycle/test_template_manager.py`

**Dependencies:**
- Story 12.1 (DocumentNamingConvention, frontmatter schema)
- Story 12.2 (DocumentRegistry)
- Story 12.7 (DocumentGovernance)

---

## Testing Requirements

### Unit Tests
- [ ] Test create_from_template() generates file
- [ ] Test frontmatter populated correctly
- [ ] Test naming convention applied
- [ ] Test governance fields auto-assigned
- [ ] Test template variable validation
- [ ] Test list_templates()

### Integration Tests
- [ ] Create PRD from template, verify all fields
- [ ] Create Story from template, verify epic link
- [ ] Verify document auto-registered in lifecycle

### Performance Tests
- [ ] Template rendering <1 second

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Template creation guide
- [ ] Variable reference for each template
- [ ] CLI command examples
- [ ] Custom template development guide

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All 7 templates created
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] CLI commands working
- [ ] Templates validated with real usage
- [ ] Committed with atomic commit message
