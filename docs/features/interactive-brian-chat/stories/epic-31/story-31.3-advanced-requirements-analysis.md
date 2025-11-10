# Story 31.3: Advanced Requirements Analysis

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.3
**Priority**: P0 (Critical - Advanced BA Capabilities)
**Estimate**: 5 story points
**Duration**: 2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1 (Vision Elicitation)

---

## Story Description

Implement advanced requirements analysis capabilities: MoSCoW prioritization (Must, Should, Could, Won't), Kano model categorization (Basic, Performance, Excitement), dependency mapping, risk identification, and constraint analysis. These are professional business analyst techniques that ensure requirements are well-prioritized and risks are identified early.

---

## User Story

**As a** product team
**I want** Mary to perform deep requirements analysis with proven BA techniques
**So that** we capture all edge cases, priorities, dependencies, and risks

---

## Acceptance Criteria

- [ ] RequirementsAnalyzer class implemented
- [ ] MoSCoW prioritization method (Must, Should, Could, Won't)
- [ ] Kano model categorization (Basic, Performance, Excitement, Indifferent, Reverse)
- [ ] Dependency mapping between requirements (graph structure)
- [ ] Risk identification (technical, resource, timeline, scope)
- [ ] Constraint analysis (time, budget, technical, compliance)
- [ ] RequirementsAnalysis data model implemented
- [ ] Analysis outputs saved to `.gao-dev/mary/requirements-analysis/`
- [ ] Mary integrates analyzer in workflow
- [ ] 8+ unit tests passing
- [ ] Performance: Full analysis <2 minutes

---

## Files to Create/Modify

### New Files

- `gao_dev/orchestrator/requirements_analyzer.py` (~300 LOC)
- `gao_dev/core/models/requirements_analysis.py` (~180 LOC)
- `gao_dev/workflows/1-analysis/requirements-analysis/*.yaml` (5 workflows, ~60 LOC each)
- `tests/orchestrator/test_requirements_analyzer.py` (~200 LOC)

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~60 LOC added)

---

## Technical Design

### RequirementsAnalyzer

**Location**: `gao_dev/orchestrator/requirements_analyzer.py`

```python
"""Advanced requirements analysis engine."""

from typing import List, Dict, Any
from dataclasses import dataclass
import structlog

from ..core.services.ai_analysis_service import AIAnalysisService

logger = structlog.get_logger()


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


class RequirementsAnalyzer:
    """Advanced requirements analysis using BMAD methods."""

    def __init__(self, analysis_service: AIAnalysisService):
        self.analysis_service = analysis_service
        self.logger = logger.bind(component="requirements_analyzer")

    async def moscow_prioritize(
        self,
        requirements: List[str],
        context: Dict[str, Any]
    ) -> List[MoSCoWCategory]:
        """
        Prioritize requirements using MoSCoW method.

        Categories:
        - Must: Non-negotiable, MVP critical
        - Should: Important but not critical
        - Could: Nice to have if time permits
        - Won't: Out of scope for now

        Uses LLM to analyze each requirement and categorize.
        """
        self.logger.info("moscow_prioritizing", count=len(requirements))

        prompt = f"""
Prioritize these requirements using MoSCoW method.

Context: {context.get('product_vision', 'N/A')}
Timeline: {context.get('timeline', 'N/A')}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

For each requirement, categorize as:
- MUST: Critical for MVP, non-negotiable
- SHOULD: Important but MVP can work without
- COULD: Nice to have if time permits
- WON'T: Out of scope for this release

Return as JSON array:
[
  {{"requirement": "...", "category": "must", "rationale": "..."}},
  ...
]
"""

        response = await self.analysis_service.analyze(
            prompt,
            model="haiku",
            response_format="json"
        )

        categories = [MoSCoWCategory(**item) for item in json.loads(response)]
        self.logger.info("moscow_complete", must_count=len([c for c in categories if c.category == "must"]))
        return categories

    async def kano_categorize(
        self,
        requirements: List[str]
    ) -> List[KanoCategory]:
        """
        Categorize requirements using Kano model.

        Categories:
        - Basic: Expected features (dissatisfaction if missing)
        - Performance: Satisfaction proportional to quality
        - Excitement: Delighters (unexpected value)
        - Indifferent: Users don't care
        - Reverse: Users don't want this
        """
        self.logger.info("kano_categorizing", count=len(requirements))

        prompt = f"""
Categorize these requirements using Kano model.

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

For each requirement:
- BASIC: Users expect this (angry if missing, neutral if present)
- PERFORMANCE: More is better (satisfaction proportional to quality)
- EXCITEMENT: Delighters (neutral if missing, happy if present)
- INDIFFERENT: Users don't care either way
- REVERSE: Users actually don't want this

Return as JSON array:
[
  {{"requirement": "...", "category": "basic", "rationale": "..."}},
  ...
]
"""

        response = await self.analysis_service.analyze(
            prompt,
            model="haiku",
            response_format="json"
        )

        categories = [KanoCategory(**item) for item in json.loads(response)]
        self.logger.info("kano_complete", excitement_count=len([c for c in categories if c.category == "excitement"]))
        return categories

    async def map_dependencies(
        self,
        requirements: List[str]
    ) -> Dict[str, List[str]]:
        """
        Identify dependencies between requirements.

        Returns:
            Graph structure: requirement → [dependencies]
            Example: {"User login": ["User registration", "Password reset"]}
        """
        self.logger.info("mapping_dependencies", count=len(requirements))

        prompt = f"""
Identify dependencies between these requirements.

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

For each requirement, list what other requirements it depends on.
A requirement depends on another if it needs that feature to exist first.

Return as JSON object mapping requirement → list of dependencies:
{{
  "Requirement A": ["Requirement B", "Requirement C"],
  "Requirement D": []
}}
"""

        response = await self.analysis_service.analyze(
            prompt,
            model="haiku",
            response_format="json"
        )

        dependencies = json.loads(response)
        self.logger.info("dependencies_mapped", total_deps=sum(len(deps) for deps in dependencies.values()))
        return dependencies

    async def identify_risks(
        self,
        requirements: List[str],
        context: Dict[str, Any]
    ) -> List[Risk]:
        """
        Identify risks in requirements.

        Risk categories:
        - Technical feasibility
        - Resource constraints
        - Timeline risks
        - Scope creep potential
        - External dependencies
        """
        self.logger.info("identifying_risks", count=len(requirements))

        prompt = f"""
Identify risks in these requirements.

Context: {context}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

For each significant risk:
- Description: What could go wrong?
- Category: technical, resource, timeline, scope, external
- Severity: high, medium, low
- Likelihood: high, medium, low
- Mitigation: How to address this risk?

Return as JSON array:
[
  {{
    "description": "...",
    "category": "technical",
    "severity": "high",
    "likelihood": "medium",
    "mitigation": "..."
  }},
  ...
]
"""

        response = await self.analysis_service.analyze(
            prompt,
            model="sonnet",  # Use smarter model for risk analysis
            response_format="json"
        )

        risks = [Risk(**item) for item in json.loads(response)]
        high_risks = [r for r in risks if r.severity == "high"]
        self.logger.info("risks_identified", total=len(risks), high_risks=len(high_risks))
        return risks

    async def analyze_constraints(
        self,
        requirements: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Analyze constraints affecting requirements.

        Constraint types:
        - Time constraints
        - Budget constraints
        - Technical constraints
        - Compliance requirements
        - Resource availability
        """
        self.logger.info("analyzing_constraints", count=len(requirements))

        prompt = f"""
Identify constraints affecting these requirements.

Context: {context}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

Identify constraints in these categories:
- time: Deadline or timeline constraints
- budget: Cost or funding constraints
- technical: Technology or platform constraints
- compliance: Regulatory or legal requirements
- resource: Team size or skill constraints

Return as JSON object:
{{
  "time": ["Must launch by Q2", ...],
  "budget": ["Limited to $50K", ...],
  "technical": ["Must use Python", ...],
  "compliance": ["GDPR compliance required", ...],
  "resource": ["Only 2 developers", ...]
}}
"""

        response = await self.analysis_service.analyze(
            prompt,
            model="haiku",
            response_format="json"
        )

        constraints = json.loads(response)
        self.logger.info("constraints_analyzed", categories=len([k for k, v in constraints.items() if v]))
        return constraints
```

### Data Models

**Location**: `gao_dev/core/models/requirements_analysis.py`

```python
"""Requirements analysis data models."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class RequirementsAnalysis:
    """Complete requirements analysis output."""
    original_requirements: List[str]
    moscow: List[MoSCoWCategory]
    kano: List[KanoCategory]
    dependencies: Dict[str, List[str]]
    risks: List[Risk]
    constraints: Dict[str, List[str]]
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[Path] = None

    def to_markdown(self) -> str:
        """Generate complete analysis report."""
        sections = []

        sections.append("# Requirements Analysis\n")
        sections.append(f"**Date**: {self.created_at.strftime('%Y-%m-%d')}\n")
        sections.append("---\n")

        # MoSCoW
        sections.append("## MoSCoW Prioritization\n")
        for category_name in ["must", "should", "could", "wont"]:
            items = [m for m in self.moscow if m.category == category_name]
            if items:
                sections.append(f"### {category_name.upper()}\n")
                for item in items:
                    sections.append(f"- **{item.requirement}**")
                    sections.append(f"  - Rationale: {item.rationale}\n")

        # Kano
        sections.append("## Kano Model Analysis\n")
        for category_name in ["basic", "performance", "excitement"]:
            items = [k for k in self.kano if k.category == category_name]
            if items:
                sections.append(f"### {category_name.title()} Features\n")
                for item in items:
                    sections.append(f"- {item.requirement}")
                    sections.append(f"  - {item.rationale}\n")

        # Dependencies
        sections.append("## Dependency Map\n")
        for req, deps in self.dependencies.items():
            if deps:
                sections.append(f"- **{req}** depends on:")
                for dep in deps:
                    sections.append(f"  - {dep}")
                sections.append("")

        # Risks
        sections.append("## Risks\n")
        for risk in sorted(self.risks, key=lambda r: (r.severity, r.likelihood), reverse=True):
            sections.append(f"### {risk.description}")
            sections.append(f"- **Category**: {risk.category}")
            sections.append(f"- **Severity**: {risk.severity} | **Likelihood**: {risk.likelihood}")
            sections.append(f"- **Mitigation**: {risk.mitigation}\n")

        # Constraints
        sections.append("## Constraints\n")
        for category, items in self.constraints.items():
            if items:
                sections.append(f"### {category.title()}\n")
                for item in items:
                    sections.append(f"- {item}")
                sections.append("")

        return "\n".join(sections)
```

---

## Testing Strategy

### Unit Tests (8+ tests)

1. **test_moscow_prioritization** - Categorizes into must/should/could/wont
2. **test_kano_categorization** - Categorizes into basic/performance/excitement
3. **test_dependency_mapping** - Identifies dependencies correctly
4. **test_circular_dependency_detection** - Warns about circular deps
5. **test_risk_identification** - Identifies risks with severity/likelihood
6. **test_constraint_analysis** - Identifies all constraint types
7. **test_requirements_analysis_to_markdown** - Complete report generated
8. **test_mary_analyze_requirements** - Mary orchestrates full analysis

---

## Definition of Done

- [ ] RequirementsAnalyzer implemented
- [ ] MoSCoW, Kano, dependencies, risks, constraints working
- [ ] RequirementsAnalysis data model complete
- [ ] 5 analysis workflows created
- [ ] Mary integrates analyzer
- [ ] Outputs saved to `.gao-dev/mary/requirements-analysis/`
- [ ] 8+ tests passing
- [ ] Performance: <2 minutes for full analysis
- [ ] Manual testing complete
- [ ] Code review complete
- [ ] Git commit: `feat(epic-31): Story 31.3 - Advanced Requirements Analysis (5 pts)`

---

**Created**: 2025-11-10
**Status**: Ready to Implement
