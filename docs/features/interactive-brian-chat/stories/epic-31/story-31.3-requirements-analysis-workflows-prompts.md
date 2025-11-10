# Story 31.3: Requirements Analysis Workflows & Prompts

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.3
**Priority**: P0 (Critical - Advanced BA Capabilities)
**Estimate**: 5 story points
**Duration**: 2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1 (Vision Elicitation Workflows)

---

## Story Description

Implement advanced requirements analysis workflows and prompts using professional business analyst techniques: MoSCoW prioritization, Kano model categorization, dependency mapping, risk identification, and constraint analysis. These techniques ensure requirements are well-prioritized, dependencies understood, and risks identified early.

**Epic 10 Integration**: Following GAO-Dev's established pattern, we separate:
- **Workflow** (metadata only) → `gao_dev/workflows/1-analysis/requirements-analysis/workflow.yaml`
- **Prompts** (LLM instructions) → `gao_dev/prompts/agents/mary_requirements_*.yaml` (5 files)

Product teams will receive comprehensive requirements analysis that identifies priorities, dependencies, risks, and constraints before development begins.

---

## User Story

**As a** product team
**I want** Mary to perform deep requirements analysis with proven BA techniques
**So that** we capture all priorities, dependencies, and risks before building

---

## Acceptance Criteria

### Workflows & Prompts
- [ ] Workflow file created: `gao_dev/workflows/1-analysis/requirements-analysis/workflow.yaml` (metadata only)
- [ ] 5 prompt files created in `gao_dev/prompts/agents/`:
  - [ ] `mary_requirements_moscow.yaml` (MoSCoW prioritization)
  - [ ] `mary_requirements_kano.yaml` (Kano model categorization)
  - [ ] `mary_requirements_dependency.yaml` (Dependency mapping)
  - [ ] `mary_requirements_risk.yaml` (Risk identification)
  - [ ] `mary_requirements_constraint.yaml` (Constraint analysis)
- [ ] All prompts follow Epic 10 format (system_prompt, user_prompt, variables, response, metadata)
- [ ] All prompts use `@file:gao_dev/agents/mary.md` for persona injection
- [ ] All prompts use `{{variable}}` syntax for substitution

### Code Implementation
- [ ] MaryOrchestrator enhanced with `analyze_requirements()` method
- [ ] MaryOrchestrator uses PromptLoader (Epic 10) to load prompts
- [ ] RequirementsAnalysis data model implemented
- [ ] Analysis outputs saved to `.gao-dev/mary/requirements-analysis/`
- [ ] Analysis summary indexed in documents.db

### Integration
- [ ] Brian successfully delegates to Mary for requirements analysis
- [ ] Mary performs all 5 analysis methods
- [ ] Analysis summary handed back to Brian for workflow selection

### Testing
- [ ] 13+ unit tests passing (5 prompts × 2 tests + 3 orchestrator tests)
- [ ] Integration test: requirements list → analysis → comprehensive report
- [ ] Performance: Full analysis completes in <2 minutes

---

## Files to Create/Modify

### New Files

**Workflow (Metadata)**:
- `gao_dev/workflows/1-analysis/requirements-analysis/workflow.yaml` (~70 LOC)
  - Metadata for all 5 analysis methods
  - Variable definitions
  - Prompt references (not embedded instructions!)

**Prompts (LLM Instructions)**:
- `gao_dev/prompts/agents/mary_requirements_moscow.yaml` (~110 LOC)
  - System prompt with Mary's persona and MoSCoW framework
  - User prompt for categorizing Must/Should/Could/Won't
  - Variables: `mary_persona`, `requirements_list`, `project_context`
  - Response config: max_tokens, temperature

- `gao_dev/prompts/agents/mary_requirements_kano.yaml` (~110 LOC)
  - System prompt with Kano model framework
  - User prompt for categorizing Basic/Performance/Excitement features

- `gao_dev/prompts/agents/mary_requirements_dependency.yaml` (~100 LOC)
  - System prompt with dependency mapping framework
  - User prompt for identifying requirement relationships

- `gao_dev/prompts/agents/mary_requirements_risk.yaml` (~110 LOC)
  - System prompt with risk identification framework
  - User prompt for identifying technical/resource/timeline/scope risks

- `gao_dev/prompts/agents/mary_requirements_constraint.yaml` (~100 LOC)
  - System prompt with constraint analysis framework
  - User prompt for identifying time/budget/technical/compliance constraints

**Data Models**:
- `gao_dev/core/models/requirements_analysis.py` (~180 LOC)
  - RequirementsAnalysis dataclass
  - MoSCoWCategory dataclass
  - KanoCategory dataclass
  - Risk dataclass
  - to_markdown() method for file output
  - to_prompt() method for handing to Brian

**Tests**:
- `tests/orchestrator/test_mary_requirements_analysis.py` (~200 LOC)
  - Test each of 5 prompts (prompt rendering, variable resolution)
  - Test RequirementsAnalysis generation
  - Test complete analysis flow
  - Integration test: end-to-end requirements analysis

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~80 LOC modified/added)
  - Add `analyze_requirements()` method
  - Use PromptLoader to load requirements analysis prompts
  - Generate RequirementsAnalysis from LLM responses
  - Save to `.gao-dev/mary/requirements-analysis/`

- `gao_dev/orchestrator/brian_orchestrator.py` (~20 LOC modified)
  - Update delegation logic to handle requirements analysis strategy
  - Pass RequirementsAnalysis back to workflow selection

---

## Technical Design

### Architecture Overview

```
User: "Analyze these requirements: [login, dashboard, dark mode, export]"
  ↓
BrianOrchestrator.assess_vagueness() → 0.65 (needs analysis)
  ↓
BrianOrchestrator delegates to Mary
  ↓
MaryOrchestrator.select_clarification_strategy() → ADVANCED_REQUIREMENTS
  ↓
MaryOrchestrator.analyze_requirements()
  ├─ Load workflow: "requirements-analysis/workflow.yaml"
  ├─ Load prompt: "mary_requirements_moscow" (via PromptLoader)
  ├─ Render and execute → MoSCoW categories
  ├─ Load prompt: "mary_requirements_kano"
  ├─ Render and execute → Kano categories
  ├─ Load prompt: "mary_requirements_dependency"
  ├─ Render and execute → Dependency map
  ├─ Load prompt: "mary_requirements_risk"
  ├─ Render and execute → Risk list
  ├─ Load prompt: "mary_requirements_constraint"
  ├─ Render and execute → Constraint list
  └─ Save to .gao-dev/mary/requirements-analysis/analysis-{timestamp}.md
  ↓
Return RequirementsAnalysis to Brian
  ↓
Brian uses analysis for workflow selection
```

### Workflow File (Metadata Only)

**File**: `gao_dev/workflows/1-analysis/requirements-analysis/workflow.yaml`

```yaml
name: requirements-analysis
description: Advanced requirements analysis with professional BA techniques
phase: 1
author: Mary (Business Analyst)
non_interactive: true
autonomous: true
iterative: false

variables:
  requirements_list:
    description: List of requirements to analyze
    type: array
    required: true

  project_context:
    description: Project context for analysis
    type: string
    default: ""

  timeline:
    description: Project timeline
    type: string
    default: ""

  team_size:
    description: Team size
    type: integer
    default: 0

required_tools:
  - analysis_service

output_file: ".gao-dev/mary/requirements-analysis/analysis-{{timestamp}}.md"

# Reference prompts by name (Epic 10 pattern)
prompts:
  moscow: "mary_requirements_moscow"
  kano: "mary_requirements_kano"
  dependency: "mary_requirements_dependency"
  risk: "mary_requirements_risk"
  constraint: "mary_requirements_constraint"

metadata:
  category: requirements_analysis
  domain: business_analysis
  methods_available: 5
  typical_duration: 1-2  # minutes
```

### Prompt File Example: MoSCoW Prioritization

**File**: `gao_dev/prompts/agents/mary_requirements_moscow.yaml`

```yaml
name: mary_requirements_moscow
description: "Mary performs MoSCoW prioritization analysis"
version: 1.0.0

system_prompt: |
  You are Mary, a Business Analyst performing MoSCoW prioritization on requirements.

  {{mary_persona}}

  **MoSCoW Prioritization Framework**:
  MoSCoW is a prioritization technique that categorizes requirements into 4 buckets:

  1. **MUST** (Non-negotiable, MVP Critical):
     - Without this, the product cannot launch
     - Critical for core value proposition
     - Legal/regulatory requirement
     - Fundamental to business case
     - Example: User authentication for a secure app

  2. **SHOULD** (Important but not Critical):
     - Important for user experience
     - Strong business case but MVP can work without it
     - Can be added in v1.1 if needed
     - Example: Password reset flow (workaround: admin reset)

  3. **COULD** (Nice to Have):
     - Desirable but optional
     - Implement if time/budget permits
     - Low impact if omitted
     - Example: Dark mode, export to PDF

  4. **WON'T** (Out of Scope):
     - Not in this release/version
     - Explicitly deferred or rejected
     - May be revisited later
     - Example: AI-powered recommendations (future)

  **Analysis Approach**:
  - Consider business value, user impact, technical feasibility, urgency
  - Be realistic about "Must" - only truly critical items
  - Provide clear rationale for each categorization
  - Consider MVP vs future releases
  - Factor in timeline and resources

user_prompt: |
  Prioritize these requirements using MoSCoW method.

  **Project Context**: {{project_context}}
  **Timeline**: {{timeline}}

  **Requirements**:
  {{requirements_list}}

  For each requirement, analyze:
  1. Business value and user impact
  2. Criticality to MVP/launch
  3. Dependencies on other requirements
  4. Technical complexity

  Then categorize as:
  - **MUST**: Critical for MVP, non-negotiable
  - **SHOULD**: Important but MVP can work without
  - **COULD**: Nice to have if time permits
  - **WON'T**: Out of scope for this release

  Return JSON array:
  [
    {
      "requirement": "User login with email/password",
      "category": "must",
      "rationale": "Fundamental security requirement - app cannot function without user accounts"
    },
    {
      "requirement": "Dark mode toggle",
      "category": "could",
      "rationale": "Desirable UX feature but not critical to core functionality"
    }
  ]

  **Important**:
  - Be conservative with "MUST" - only truly critical items
  - Provide clear, specific rationale
  - Consider the stated timeline and context
  - Think about MVP vs future releases

variables:
  mary_persona: "@file:gao_dev/agents/mary.md"  # Epic 10 reference resolution
  requirements_list: ""
  project_context: ""
  timeline: "Not specified"

response:
  max_tokens: 2048
  temperature: 0.5  # Balanced for analysis
  format: json

metadata:
  category: requirements_analysis
  agent: mary
  phase: 1
  method: moscow
  method_type: prioritization
  typical_duration: 1-2
  best_for: "Prioritizing features for MVP and release planning"
  original_source: "Professional BA technique (adapted for GAO-Dev)"
```

### MaryOrchestrator Implementation

**File**: `gao_dev/orchestrator/mary_orchestrator.py`

```python
class MaryOrchestrator:
    async def analyze_requirements(
        self,
        requirements: List[str],
        project_context: str = "",
        timeline: str = "",
        team_size: int = 0
    ) -> RequirementsAnalysis:
        """
        Perform comprehensive requirements analysis using Epic 10 prompt system.

        Runs all 5 analysis methods:
        - MoSCoW prioritization
        - Kano model categorization
        - Dependency mapping
        - Risk identification
        - Constraint analysis

        Args:
            requirements: List of requirement strings
            project_context: Optional project context
            timeline: Optional project timeline
            team_size: Optional team size

        Returns:
            RequirementsAnalysis with all analysis results
        """

        # Load workflow metadata
        workflow = self.workflow_registry.load_workflow(
            "1-analysis/requirements-analysis/workflow.yaml"
        )

        # Prepare common variables
        variables = {
            "requirements_list": "\n".join(f"{i+1}. {req}" for i, req in enumerate(requirements)),
            "mary_persona": "@file:gao_dev/agents/mary.md",  # Auto-resolved
            "project_context": project_context,
            "timeline": timeline,
            "team_size": team_size
        }

        # 1. MoSCoW Prioritization
        moscow_template = self.prompt_loader.load_prompt(workflow.prompts["moscow"])
        moscow_rendered = self.prompt_loader.render_prompt(moscow_template, variables)
        moscow_response = await self.analysis_service.analyze(
            moscow_rendered,
            model="sonnet",
            response_format="json",
            max_tokens=moscow_template.response.max_tokens,
            temperature=moscow_template.response.temperature
        )
        moscow_categories = [MoSCoWCategory(**item) for item in json.loads(moscow_response)]

        # 2. Kano Model Categorization
        kano_template = self.prompt_loader.load_prompt(workflow.prompts["kano"])
        kano_rendered = self.prompt_loader.render_prompt(kano_template, variables)
        kano_response = await self.analysis_service.analyze(
            kano_rendered,
            model="sonnet",
            response_format="json",
            max_tokens=kano_template.response.max_tokens,
            temperature=kano_template.response.temperature
        )
        kano_categories = [KanoCategory(**item) for item in json.loads(kano_response)]

        # 3. Dependency Mapping
        dependency_template = self.prompt_loader.load_prompt(workflow.prompts["dependency"])
        dependency_rendered = self.prompt_loader.render_prompt(dependency_template, variables)
        dependency_response = await self.analysis_service.analyze(
            dependency_rendered,
            model="sonnet",
            response_format="json",
            max_tokens=dependency_template.response.max_tokens,
            temperature=dependency_template.response.temperature
        )
        dependencies = json.loads(dependency_response)

        # 4. Risk Identification
        risk_template = self.prompt_loader.load_prompt(workflow.prompts["risk"])
        risk_rendered = self.prompt_loader.render_prompt(risk_template, variables)
        risk_response = await self.analysis_service.analyze(
            risk_rendered,
            model="sonnet",
            response_format="json",
            max_tokens=risk_template.response.max_tokens,
            temperature=risk_template.response.temperature
        )
        risks = [Risk(**item) for item in json.loads(risk_response)]

        # 5. Constraint Analysis
        constraint_template = self.prompt_loader.load_prompt(workflow.prompts["constraint"])
        constraint_rendered = self.prompt_loader.render_prompt(constraint_template, variables)
        constraint_response = await self.analysis_service.analyze(
            constraint_rendered,
            model="sonnet",
            response_format="json",
            max_tokens=constraint_template.response.max_tokens,
            temperature=constraint_template.response.temperature
        )
        constraints = json.loads(constraint_response)

        # Create comprehensive analysis
        analysis = RequirementsAnalysis(
            original_requirements=requirements,
            moscow=moscow_categories,
            kano=kano_categories,
            dependencies=dependencies,
            risks=risks,
            constraints=constraints,
            created_at=datetime.now()
        )

        # Save to .gao-dev/mary/requirements-analysis/
        output_path = workflow.output_file.format(
            timestamp=datetime.now().isoformat()
        )
        await self._save_analysis(analysis, output_path)

        self.logger.info(
            "requirements_analysis_complete",
            must_count=len([m for m in moscow_categories if m.category == "must"]),
            risk_count=len(risks),
            high_risk_count=len([r for r in risks if r.severity == "high"])
        )

        return analysis
```

---

## Testing Strategy

### Unit Tests (13+ tests)

**Test Prompt Rendering** (5 tests):
```python
def test_moscow_prompt_rendering():
    """Test MoSCoW prompt loads and renders correctly."""
    loader = PromptLoader(prompts_dir=Path("gao_dev/prompts"))
    template = loader.load_prompt("mary_requirements_moscow")

    assert template.name == "mary_requirements_moscow"
    assert "MoSCoW" in template.system_prompt

    rendered = loader.render_prompt(template, {
        "requirements_list": "1. Login\n2. Dashboard",
        "mary_persona": "You are Mary",
        "project_context": "Web app",
        "timeline": "3 months"
    })

    assert "Login" in rendered
    assert "Dashboard" in rendered
```

(Similar tests for: kano, dependency, risk, constraint)

**Test Analysis Methods** (5 tests):
```python
async def test_moscow_prioritization():
    """Test MoSCoW prioritization analysis."""
    requirements = ["User login", "Dashboard", "Dark mode"]

    analysis = await orchestrator.analyze_requirements(requirements)

    assert len(analysis.moscow) == 3
    assert any(m.category == "must" for m in analysis.moscow)
```

**Test Complete Analysis** (3 tests):
```python
async def test_analyze_requirements_full_flow():
    """Test complete requirements analysis."""
    requirements = [
        "User authentication",
        "Dashboard with metrics",
        "Export to PDF",
        "Dark mode"
    ]

    analysis = await orchestrator.analyze_requirements(
        requirements=requirements,
        project_context="SaaS web app",
        timeline="3 months",
        team_size=3
    )

    assert isinstance(analysis, RequirementsAnalysis)
    assert len(analysis.moscow) == 4
    assert len(analysis.kano) == 4
    assert analysis.dependencies
    assert len(analysis.risks) > 0
    assert analysis.constraints
```

### Integration Tests (2 tests)

```python
async def test_brian_delegates_to_mary_for_requirements_analysis():
    """Test Brian delegates requirements analysis to Mary."""
    brian = BrianOrchestrator(...)

    result = await brian.assess_and_select_workflows(
        "Analyze requirements: login, dashboard, export"
    )

    assert result.delegated_to == "Mary"
    assert result.mary_strategy == "advanced_requirements"
```

---

## Implementation Checklist

- [ ] Create workflow file: `workflows/1-analysis/requirements-analysis/workflow.yaml`
- [ ] Create prompt: `prompts/agents/mary_requirements_moscow.yaml`
- [ ] Create prompt: `prompts/agents/mary_requirements_kano.yaml`
- [ ] Create prompt: `prompts/agents/mary_requirements_dependency.yaml`
- [ ] Create prompt: `prompts/agents/mary_requirements_risk.yaml`
- [ ] Create prompt: `prompts/agents/mary_requirements_constraint.yaml`
- [ ] Create data model: `core/models/requirements_analysis.py`
- [ ] Enhance MaryOrchestrator with `analyze_requirements()` method
- [ ] Update BrianOrchestrator delegation logic
- [ ] Create tests: `tests/orchestrator/test_mary_requirements_analysis.py`
- [ ] Run tests (13+ tests passing)
- [ ] Integration test: End-to-end requirements analysis
- [ ] Performance validation: <2 minutes for complete analysis

---

## Definition of Done

- [ ] All 6 files created (1 workflow + 5 prompts)
- [ ] All prompts follow Epic 10 format
- [ ] MaryOrchestrator uses PromptLoader
- [ ] 13+ tests passing (>90% coverage)
- [ ] Integration test passes
- [ ] All 5 analysis methods working (MoSCoW, Kano, dependencies, risks, constraints)
- [ ] Analysis report generated in markdown
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No regressions in existing tests

---

**Status**: Todo
**Next Story**: Story 31.4 (Domain-Specific Requirements Workflows & Prompts)
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Epic 10 integration)
