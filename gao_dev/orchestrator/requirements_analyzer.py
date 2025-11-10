"""Advanced requirements analysis engine.

This module implements comprehensive requirements analysis using proven BA techniques:
- MoSCoW prioritization (Must, Should, Could, Won't)
- Kano model categorization (Basic, Performance, Excitement)
- Dependency mapping (graph structure)
- Risk identification (technical, resource, timeline, scope, external)
- Constraint analysis (time, budget, technical, compliance)

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.3 - Advanced Requirements Analysis
"""

from typing import List, Dict, Any
import json
import structlog

from ..core.services.ai_analysis_service import AIAnalysisService
from ..core.models.requirements_analysis import (
    MoSCoWCategory,
    KanoCategory,
    Risk,
    Constraint,
    RequirementsAnalysis,
)

logger = structlog.get_logger()


class RequirementsAnalyzer:
    """
    Advanced requirements analysis using BMAD methods.

    Provides comprehensive analysis of requirements using professional
    business analyst techniques to ensure proper prioritization and risk
    identification.
    """

    def __init__(self, analysis_service: AIAnalysisService):
        """
        Initialize requirements analyzer.

        Args:
            analysis_service: AI analysis service for LLM-powered analysis
        """
        self.analysis_service = analysis_service
        self.logger = logger.bind(component="requirements_analyzer")

    async def moscow_prioritize(
        self, requirements: List[str], context: Dict[str, Any]
    ) -> List[MoSCoWCategory]:
        """
        Prioritize requirements using MoSCoW method.

        Categories:
        - Must: Non-negotiable, MVP critical
        - Should: Important but not critical
        - Could: Nice to have if time permits
        - Won't: Out of scope for now

        Uses LLM to analyze each requirement and categorize.

        Args:
            requirements: List of requirement strings to prioritize
            context: Context dict with product_vision, timeline, etc.

        Returns:
            List of MoSCoWCategory objects

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        self.logger.info("moscow_prioritizing", count=len(requirements))

        prompt = f"""Prioritize these requirements using MoSCoW method.

Context:
- Product Vision: {context.get('product_vision', 'N/A')}
- Timeline: {context.get('timeline', 'N/A')}
- Constraints: {context.get('constraints', 'N/A')}

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

For each requirement, categorize as:
- MUST: Critical for MVP, non-negotiable
- SHOULD: Important but MVP can work without
- COULD: Nice to have if time permits
- WONT: Out of scope for this release

Return as JSON array:
[
  {{"requirement": "...", "category": "must", "rationale": "..."}},
  ...
]
"""

        try:
            response = await self.analysis_service.analyze(
                prompt, model="haiku", response_format="json", max_tokens=2048
            )

            categories_data = json.loads(response.response)
            categories = [MoSCoWCategory(**item) for item in categories_data]

            must_count = len([c for c in categories if c.category.lower() == "must"])
            self.logger.info("moscow_complete", must_count=must_count, total=len(categories))

            return categories

        except json.JSONDecodeError as e:
            self.logger.error("moscow_json_parse_failed", error=str(e))
            # Fallback: create default categories
            return [
                MoSCoWCategory(
                    requirement=req,
                    category="should",
                    rationale="Unable to analyze automatically",
                )
                for req in requirements
            ]

    async def kano_categorize(self, requirements: List[str]) -> List[KanoCategory]:
        """
        Categorize requirements using Kano model.

        Categories:
        - Basic: Expected features (dissatisfaction if missing)
        - Performance: Satisfaction proportional to quality
        - Excitement: Delighters (unexpected value)
        - Indifferent: Users don't care
        - Reverse: Users don't want this

        Args:
            requirements: List of requirement strings to categorize

        Returns:
            List of KanoCategory objects

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        self.logger.info("kano_categorizing", count=len(requirements))

        prompt = f"""Categorize these requirements using Kano model.

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

        try:
            response = await self.analysis_service.analyze(
                prompt, model="haiku", response_format="json", max_tokens=2048
            )

            categories_data = json.loads(response.response)
            categories = [KanoCategory(**item) for item in categories_data]

            excitement_count = len([c for c in categories if c.category.lower() == "excitement"])
            self.logger.info(
                "kano_complete", excitement_count=excitement_count, total=len(categories)
            )

            return categories

        except json.JSONDecodeError as e:
            self.logger.error("kano_json_parse_failed", error=str(e))
            # Fallback: create default categories
            return [
                KanoCategory(
                    requirement=req,
                    category="performance",
                    rationale="Unable to analyze automatically",
                )
                for req in requirements
            ]

    async def map_dependencies(self, requirements: List[str]) -> Dict[str, List[str]]:
        """
        Identify dependencies between requirements.

        Returns:
            Graph structure: requirement -> [dependencies]
            Example: {"User login": ["User registration", "Password reset"]}

        Args:
            requirements: List of requirement strings to analyze

        Returns:
            Dictionary mapping requirements to their dependencies

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        self.logger.info("mapping_dependencies", count=len(requirements))

        prompt = f"""Identify dependencies between these requirements.

Requirements:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(requirements))}

For each requirement, list what other requirements it depends on.
A requirement depends on another if it needs that feature to exist first.

Return as JSON object mapping requirement -> list of dependencies:
{{
  "Requirement A": ["Requirement B", "Requirement C"],
  "Requirement D": []
}}
"""

        try:
            response = await self.analysis_service.analyze(
                prompt, model="haiku", response_format="json", max_tokens=2048
            )

            dependencies = json.loads(response.response)
            total_deps = sum(len(deps) for deps in dependencies.values())
            self.logger.info("dependencies_mapped", total_deps=total_deps)

            return dependencies

        except json.JSONDecodeError as e:
            self.logger.error("dependency_json_parse_failed", error=str(e))
            # Fallback: return empty dependencies
            return {req: [] for req in requirements}

    async def identify_risks(
        self, requirements: List[str], context: Dict[str, Any]
    ) -> List[Risk]:
        """
        Identify risks in requirements.

        Risk categories:
        - Technical feasibility
        - Resource constraints
        - Timeline risks
        - Scope creep potential
        - External dependencies

        Args:
            requirements: List of requirement strings to analyze
            context: Context dict with team_size, timeline, technical_stack, etc.

        Returns:
            List of Risk objects

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        self.logger.info("identifying_risks", count=len(requirements))

        prompt = f"""Identify risks in these requirements.

Context:
{json.dumps(context, indent=2)}

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

        try:
            response = await self.analysis_service.analyze(
                prompt, model="sonnet", response_format="json", max_tokens=3072
            )

            risks_data = json.loads(response.response)
            risks = [Risk(**item) for item in risks_data]

            high_risks = [r for r in risks if r.severity.lower() == "high"]
            self.logger.info("risks_identified", total=len(risks), high_risks=len(high_risks))

            return risks

        except json.JSONDecodeError as e:
            self.logger.error("risk_json_parse_failed", error=str(e))
            # Fallback: return generic risk
            return [
                Risk(
                    description="Requirements analysis could not identify specific risks",
                    category="scope",
                    severity="medium",
                    likelihood="low",
                    mitigation="Manual review recommended",
                )
            ]

    async def analyze_constraints(
        self, requirements: List[str], context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Analyze constraints affecting requirements.

        Constraint types:
        - Time constraints
        - Budget constraints
        - Technical constraints
        - Compliance requirements
        - Resource availability

        Args:
            requirements: List of requirement strings to analyze
            context: Context dict with timeline, budget, team_size, etc.

        Returns:
            Dictionary of constraint categories to constraint lists

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        self.logger.info("analyzing_constraints", count=len(requirements))

        prompt = f"""Identify constraints affecting these requirements.

Context:
{json.dumps(context, indent=2)}

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

        try:
            response = await self.analysis_service.analyze(
                prompt, model="haiku", response_format="json", max_tokens=2048
            )

            constraints = json.loads(response.response)
            active_categories = len([k for k, v in constraints.items() if v])
            self.logger.info("constraints_analyzed", categories=active_categories)

            return constraints

        except json.JSONDecodeError as e:
            self.logger.error("constraint_json_parse_failed", error=str(e))
            # Fallback: return empty constraints
            return {"time": [], "budget": [], "technical": [], "compliance": [], "resource": []}

    async def analyze_all(
        self, requirements: List[str], context: Dict[str, Any]
    ) -> RequirementsAnalysis:
        """
        Perform complete requirements analysis.

        Runs all analysis techniques:
        - MoSCoW prioritization
        - Kano model categorization
        - Dependency mapping
        - Risk identification
        - Constraint analysis

        Args:
            requirements: List of requirement strings to analyze
            context: Context dict with all relevant information

        Returns:
            RequirementsAnalysis object with all results

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        self.logger.info("full_analysis_started", req_count=len(requirements))

        # Run all analyses in parallel where possible
        moscow = await self.moscow_prioritize(requirements, context)
        kano = await self.kano_categorize(requirements)
        dependencies = await self.map_dependencies(requirements)
        risks = await self.identify_risks(requirements, context)
        constraints = await self.analyze_constraints(requirements, context)

        analysis = RequirementsAnalysis(
            original_requirements=requirements,
            moscow=moscow,
            kano=kano,
            dependencies=dependencies,
            risks=risks,
            constraints=constraints,
        )

        self.logger.info(
            "full_analysis_complete",
            must_count=len([m for m in moscow if m.category.lower() == "must"]),
            risk_count=len(risks),
            high_risks=len([r for r in risks if r.severity.lower() == "high"]),
        )

        return analysis
