"""Requirements analysis data models.

This module defines data structures for capturing advanced requirements analysis results
including MoSCoW prioritization, Kano model categorization, dependencies, risks, and constraints.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.3 - Advanced Requirements Analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class MoSCoWCategory:
    """MoSCoW categorized requirement."""

    requirement: str
    category: str  # must, should, could, wont
    rationale: str


@dataclass
class KanoCategory:
    """Kano model categorized requirement."""

    requirement: str
    category: str  # basic, performance, excitement, indifferent, reverse
    rationale: str


@dataclass
class Risk:
    """Identified risk."""

    description: str
    category: str  # technical, resource, timeline, scope, external
    severity: str  # high, medium, low
    likelihood: str  # high, medium, low
    mitigation: str


@dataclass
class Constraint:
    """Project constraint."""

    description: str
    category: str  # time, budget, technical, compliance, resource
    impact: Optional[str] = None


@dataclass
class RequirementsAnalysis:
    """
    Complete requirements analysis output.

    Contains results from all analysis techniques:
    - MoSCoW prioritization
    - Kano model categorization
    - Dependency mapping
    - Risk identification
    - Constraint analysis
    """

    original_requirements: List[str]
    moscow: List[MoSCoWCategory] = field(default_factory=list)
    kano: List[KanoCategory] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    risks: List[Risk] = field(default_factory=list)
    constraints: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[Path] = None

    def to_markdown(self) -> str:
        """
        Generate complete analysis report.

        Returns:
            Formatted markdown string with all analysis results
        """
        sections = []

        # Header
        sections.append("# Requirements Analysis Report\n")
        sections.append(f"**Date**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"**Total Requirements**: {len(self.original_requirements)}\n")
        sections.append("---\n")

        # Original Requirements
        sections.append("## Original Requirements\n")
        for i, req in enumerate(self.original_requirements, 1):
            sections.append(f"{i}. {req}")
        sections.append("\n---\n")

        # MoSCoW Prioritization
        sections.append("## MoSCoW Prioritization\n")
        sections.append(
            "Categorizes requirements by priority:\n"
            "- **MUST**: Critical for MVP, non-negotiable\n"
            "- **SHOULD**: Important but MVP can work without\n"
            "- **COULD**: Nice to have if time permits\n"
            "- **WON'T**: Out of scope for this release\n"
        )

        for category_name in ["must", "should", "could", "wont"]:
            items = [m for m in self.moscow if m.category.lower() == category_name]
            if items:
                sections.append(f"### {category_name.upper()}\n")
                for item in items:
                    sections.append(f"**{item.requirement}**")
                    sections.append(f"  - *Rationale*: {item.rationale}\n")

        sections.append("---\n")

        # Kano Model Analysis
        sections.append("## Kano Model Analysis\n")
        sections.append(
            "Categorizes requirements by user satisfaction impact:\n"
            "- **Basic**: Expected features (dissatisfaction if missing)\n"
            "- **Performance**: Satisfaction proportional to quality\n"
            "- **Excitement**: Delighters (unexpected value)\n"
            "- **Indifferent**: Users don't care either way\n"
            "- **Reverse**: Users don't want this\n"
        )

        for category_name in ["basic", "performance", "excitement", "indifferent", "reverse"]:
            items = [k for k in self.kano if k.category.lower() == category_name]
            if items:
                sections.append(f"### {category_name.title()} Features\n")
                for item in items:
                    sections.append(f"- **{item.requirement}**")
                    sections.append(f"  - *Rationale*: {item.rationale}\n")

        sections.append("---\n")

        # Dependency Mapping
        sections.append("## Dependency Map\n")
        sections.append(
            "Shows which requirements depend on others (must be built first).\n"
        )

        has_dependencies = False
        for req, deps in self.dependencies.items():
            if deps:
                has_dependencies = True
                sections.append(f"**{req}** depends on:")
                for dep in deps:
                    sections.append(f"  - {dep}")
                sections.append("")

        if not has_dependencies:
            sections.append("*No dependencies identified*\n")

        sections.append("---\n")

        # Risk Analysis
        sections.append("## Risk Analysis\n")
        sections.append(
            "Identified risks with severity, likelihood, and mitigation strategies.\n"
        )

        if self.risks:
            # Sort by severity and likelihood (high priority first)
            severity_order = {"high": 3, "medium": 2, "low": 1}
            likelihood_order = {"high": 3, "medium": 2, "low": 1}
            sorted_risks = sorted(
                self.risks,
                key=lambda r: (
                    severity_order.get(r.severity.lower(), 0),
                    likelihood_order.get(r.likelihood.lower(), 0),
                ),
                reverse=True,
            )

            for risk in sorted_risks:
                sections.append(f"### {risk.description}\n")
                sections.append(f"- **Category**: {risk.category.title()}")
                sections.append(
                    f"- **Severity**: {risk.severity.title()} | "
                    f"**Likelihood**: {risk.likelihood.title()}"
                )
                sections.append(f"- **Mitigation**: {risk.mitigation}\n")
        else:
            sections.append("*No risks identified*\n")

        sections.append("---\n")

        # Constraint Analysis
        sections.append("## Constraint Analysis\n")
        sections.append("Project constraints that affect requirements implementation.\n")

        constraint_categories = {
            "time": "Time Constraints",
            "budget": "Budget Constraints",
            "technical": "Technical Constraints",
            "compliance": "Compliance Requirements",
            "resource": "Resource Constraints",
        }

        has_constraints = False
        for category_key, category_title in constraint_categories.items():
            items = self.constraints.get(category_key, [])
            if items:
                has_constraints = True
                sections.append(f"### {category_title}\n")
                for item in items:
                    sections.append(f"- {item}")
                sections.append("")

        if not has_constraints:
            sections.append("*No constraints identified*\n")

        # Footer
        sections.append("---\n")
        sections.append("**Generated by**: Mary (Business Analyst)")
        if self.file_path:
            sections.append(f"**File**: {self.file_path.name}")

        return "\n".join(sections)

    def get_must_have_requirements(self) -> List[str]:
        """
        Get list of MUST requirements for MVP planning.

        Returns:
            List of requirement strings categorized as MUST
        """
        return [m.requirement for m in self.moscow if m.category.lower() == "must"]

    def get_high_priority_risks(self) -> List[Risk]:
        """
        Get high priority risks (high severity or high likelihood).

        Returns:
            List of Risk objects with high severity or high likelihood
        """
        return [
            r
            for r in self.risks
            if r.severity.lower() == "high" or r.likelihood.lower() == "high"
        ]

    def get_dependency_order(self) -> List[str]:
        """
        Get requirements in dependency order (topological sort).

        Returns:
            List of requirement strings in order they should be implemented
        """
        # Simple implementation: return requirements with no dependencies first
        no_deps = []
        with_deps = []

        for req in self.original_requirements:
            if not self.dependencies.get(req, []):
                no_deps.append(req)
            else:
                with_deps.append(req)

        return no_deps + with_deps
