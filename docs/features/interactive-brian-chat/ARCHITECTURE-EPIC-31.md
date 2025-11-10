# Architecture Document: Epic 31 - Full Mary Integration

**Epic ID**: Epic 31
**Feature**: Interactive Brian Chat - Full Mary (Business Analyst) Integration
**Version**: 1.0
**Created**: 2025-11-10
**Owner**: Winston (Technical Architect)
**Status**: Planning

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Context](#system-context)
3. [Component Architecture](#component-architecture)
4. [Data Architecture](#data-architecture)
5. [Integration Points](#integration-points)
6. [Workflow Architecture](#workflow-architecture)
7. [Brainstorming Engine Design](#brainstorming-engine-design)
8. [Requirements Analysis Engine](#requirements-analysis-engine)
9. [Domain Intelligence System](#domain-intelligence-system)
10. [Performance & Scalability](#performance--scalability)
11. [Security & Privacy](#security--privacy)
12. [Technology Stack](#technology-stack)

---

## Architecture Overview

### Design Principles

1. **LLM-Powered Conversational Discovery**: All Mary interactions use LLM for intelligent, adaptive dialogue (not hardcoded scripts)
2. **Strategy Pattern**: Mary intelligently selects clarification strategies based on context and vagueness
3. **Modular Workflows**: Each workflow (vision elicitation, brainstorming, requirements analysis) is independent and composable
4. **BMAD Methodology Integration**: Leverages 36 brainstorming techniques and 39 advanced elicitation methods from BMAD framework
5. **Stateful Sessions**: Conversation state persisted for long-running sessions with checkpoint/resume capability
6. **Domain Awareness**: Context-sensitive question generation based on detected project domain

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Interactive Brian Chat                      │
│                     (ConversationalBrian)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Delegates vague requests
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BrianOrchestrator                            │
│  ┌────────────────────────────────────────────────────┐         │
│  │ Vagueness Assessment (0.0-1.0 score)               │         │
│  │ - Missing who/what/why/how?                        │         │
│  │ - Ambiguous terms?                                 │         │
│  │ - Unclear scope?                                   │         │
│  └────────────────────┬───────────────────────────────┘         │
│                       │                                          │
│                       │ If vagueness > 0.6                       │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────┐         │
│  │ Delegate to Mary                                   │         │
│  └────────────────────┬───────────────────────────────┘         │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MaryOrchestrator                             │
│                   (Business Analyst Agent)                       │
│  ┌────────────────────────────────────────────────────┐         │
│  │ Strategy Selection Engine                          │         │
│  │ - assess_clarification_needs()                     │         │
│  │ - select_strategy() → vision|brainstorm|advanced   │         │
│  └────────────────────┬───────────────────────────────┘         │
│                       │                                          │
│       ┌───────────────┼───────────────┬──────────────┐          │
│       │               │               │              │          │
│       ▼               ▼               ▼              ▼          │
│  ┌─────────┐   ┌──────────────┐ ┌─────────────┐ ┌─────────┐   │
│  │ Vision  │   │ Brainstorming│ │ Advanced    │ │ Domain  │   │
│  │ Elicit  │   │ Engine       │ │ Requirements│ │ Library │   │
│  │         │   │              │ │ Analyzer    │ │         │   │
│  └─────────┘   └──────────────┘ └─────────────┘ └─────────┘   │
│       │               │               │              │          │
└───────┼───────────────┼───────────────┼──────────────┼──────────┘
        │               │               │              │
        └───────────────┴───────────────┴──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AIAnalysisService (Epic 21)                      │
│  - LLM API calls (Claude Haiku/Sonnet)                          │
│  - Streaming support for real-time responses                    │
│  - Token optimization and caching                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Context

### External Systems

1. **AIAnalysisService (Epic 21)**
   - Purpose: LLM API integration for conversational AI
   - Used for: All Mary dialogue, synthesis, and analysis
   - Models: Haiku (fast/cheap) for most interactions, Sonnet (smart) for complex synthesis

2. **ConversationManager (Epic 26)**
   - Purpose: Multi-turn dialogue state management
   - Used for: Session persistence, conversation history, checkpoint/resume

3. **FastContextLoader (Epic 25)**
   - Purpose: Project context awareness
   - Used for: Load existing project state for context-aware questions

4. **GitIntegratedStateManager (Epic 25)**
   - Purpose: Atomic file+DB+git operations
   - Used for: Persist Mary's outputs (requirements summaries, brainstorming reports)

### Internal Systems

1. **BrianOrchestrator**
   - Delegates vague requests to Mary
   - Receives clarified requirements back
   - Proceeds with workflow selection

2. **WorkflowRegistry & WorkflowExecutor**
   - Manages Mary's workflows (vision elicitation, brainstorming, requirements analysis)
   - Executes workflow instructions with variable resolution

---

## Component Architecture

### 1. MaryOrchestrator (Enhanced from Epic 30)

**Location**: `gao_dev/orchestrator/mary_orchestrator.py`

**Responsibilities**:
- Strategy selection (vision elicitation, brainstorming, advanced requirements, basic clarification)
- Orchestrate multi-turn conversations
- Generate requirements summaries
- Persist outputs to `.gao-dev/mary/`

**Key Methods**:

```python
class MaryOrchestrator:
    """Mary - Business Analyst Orchestrator."""

    async def select_clarification_strategy(
        self,
        user_request: str,
        vagueness_score: float,
        project_context: Optional[Dict[str, Any]] = None
    ) -> ClarificationStrategy:
        """
        Select best clarification strategy based on request analysis.

        Strategies:
        - vision_elicitation: Very vague, need to build vision from scratch
        - brainstorming: Multiple approaches possible, explore creatively
        - advanced_requirements: Clear direction, need deep analysis
        - basic_clarification: Just need a few details

        Args:
            user_request: Original request
            vagueness_score: 0.0-1.0 from BrianOrchestrator
            project_context: Optional project context

        Returns:
            Selected ClarificationStrategy
        """

    async def elicit_vision(
        self,
        user_request: str
    ) -> VisionSummary:
        """
        Elicit product vision through guided discovery.

        Workflows:
        - Vision canvas
        - Problem-solution fit
        - Outcome mapping
        - 5W1H analysis

        Returns:
            VisionSummary with clarified vision
        """

    async def facilitate_brainstorming(
        self,
        user_request: str,
        technique: Optional[str] = None
    ) -> BrainstormingSummary:
        """
        Facilitate brainstorming session with selected technique(s).

        Uses BrainstormingEngine for technique selection and facilitation.

        Args:
            user_request: Topic to brainstorm
            technique: Optional specific technique (otherwise Mary recommends)

        Returns:
            BrainstormingSummary with ideas, mind maps, insights
        """

    async def analyze_requirements(
        self,
        user_request: str,
        initial_requirements: List[str]
    ) -> RequirementsAnalysis:
        """
        Perform advanced requirements analysis.

        Analyses:
        - MoSCoW prioritization
        - Kano model categorization
        - Dependency mapping
        - Risk identification
        - Constraint analysis

        Returns:
            RequirementsAnalysis with prioritized requirements
        """
```

**State Management**:

```python
@dataclass
class MarySession:
    """Mary's conversation session state."""
    session_id: str
    user_request: str
    strategy: ClarificationStrategy
    conversation_history: List[Message]
    artifacts: Dict[str, Any]  # Mind maps, summaries, etc.
    checkpoint_data: Optional[Dict[str, Any]]
    started_at: datetime
    last_activity: datetime
```

---

### 2. BrainstormingEngine (New)

**Location**: `gao_dev/orchestrator/brainstorming_engine.py`

**Responsibilities**:
- Load brainstorming techniques from BMAD library (36 techniques)
- Recommend techniques based on context
- Generate facilitation prompts
- Capture and organize ideas
- Generate mind maps (mermaid syntax)
- Synthesize insights

**Architecture**:

```python
class BrainstormingEngine:
    """
    Facilitate brainstorming sessions with BMAD techniques.

    Loads techniques from: bmad/core/workflows/brainstorming/brain-methods.csv
    """

    def __init__(
        self,
        analysis_service: AIAnalysisService,
        conversation_manager: ConversationManager
    ):
        """Initialize with technique library."""
        self.techniques = self._load_techniques()
        self.analysis_service = analysis_service
        self.conversation_manager = conversation_manager

    def _load_techniques(self) -> List[BrainstormingTechnique]:
        """
        Load techniques from BMAD CSV.

        Returns:
            List of 36 brainstorming techniques across 7 categories:
            - Structured (SCAMPER, Six Thinking Hats, Mind Mapping, etc.)
            - Creative (What If, Analogical Thinking, Reversal Inversion, etc.)
            - Collaborative (Yes And, Brain Writing, Role Playing, etc.)
            - Deep (Five Whys, Provocation, Assumption Reversal, etc.)
            - Theatrical (Time Travel, Alien Anthropologist, Dream Fusion, etc.)
            - Wild (Chaos Engineering, Pirate Code, Zombie Apocalypse, etc.)
            - Introspective (Inner Child, Shadow Work, Values Archaeology, etc.)
        """

    async def recommend_techniques(
        self,
        topic: str,
        goal: BrainstormingGoal,
        context: Dict[str, Any]
    ) -> List[BrainstormingTechnique]:
        """
        Recommend 2-4 techniques based on goal and context.

        Analysis:
        - Innovation/new ideas → creative, wild
        - Problem solving → deep, structured
        - Team building → collaborative
        - Personal insight → introspective_delight
        - Strategic planning → structured, deep
        """

    async def facilitate_technique(
        self,
        technique: BrainstormingTechnique,
        topic: str
    ) -> AsyncIterator[FacilitationPrompt]:
        """
        Facilitate brainstorming technique through guided prompts.

        Yields facilitation prompts one at a time.
        User responses captured by ConversationManager.
        """

    async def generate_mind_map(
        self,
        ideas: List[Idea],
        central_topic: str
    ) -> str:
        """
        Generate text-based mind map in mermaid syntax.

        Returns:
            Mermaid diagram code for rendering
        """

    async def synthesize_insights(
        self,
        session: BrainstormingSession
    ) -> BrainstormingSummary:
        """
        Synthesize session into structured summary.

        Returns:
            - Key themes
            - Insights and learnings
            - Quick wins vs long-term ideas
            - Recommended follow-up techniques
        """
```

**Technique Data Model**:

```python
@dataclass
class BrainstormingTechnique:
    """Brainstorming technique from BMAD library."""
    category: str  # structured, creative, collaborative, deep, theatrical, wild, introspective_delight
    name: str
    description: str
    facilitation_prompts: List[str]  # Parsed from CSV (pipe-separated)
    best_for: str
    energy_level: str  # high, moderate, low
    typical_duration: str  # e.g., "15-20" minutes
```

---

### 3. RequirementsAnalyzer (New)

**Location**: `gao_dev/orchestrator/requirements_analyzer.py`

**Responsibilities**:
- MoSCoW prioritization (Must, Should, Could, Won't)
- Kano model analysis (Basic, Performance, Excitement features)
- Dependency mapping between requirements
- Risk identification and assessment
- Constraint analysis (time, budget, technical, compliance)

**Architecture**:

```python
class RequirementsAnalyzer:
    """
    Advanced requirements analysis using BMAD methods.
    """

    async def moscow_prioritize(
        self,
        requirements: List[str],
        context: Dict[str, Any]
    ) -> MoSCoWAnalysis:
        """
        Prioritize requirements using MoSCoW method.

        Categories:
        - Must: Non-negotiable, MVP critical
        - Should: Important but not critical
        - Could: Nice to have if time permits
        - Won't: Out of scope for now

        Uses LLM to analyze each requirement and categorize.
        """

    async def kano_categorize(
        self,
        requirements: List[str]
    ) -> KanoAnalysis:
        """
        Categorize requirements using Kano model.

        Categories:
        - Basic: Expected features (dissatisfaction if missing)
        - Performance: Satisfaction proportional to implementation quality
        - Excitement: Delighters (unexpected value)
        - Indifferent: Users don't care
        - Reverse: Users don't want this

        Uses LLM to understand user expectations and categorize.
        """

    async def map_dependencies(
        self,
        requirements: List[str]
    ) -> DependencyGraph:
        """
        Identify dependencies between requirements.

        Returns:
            Graph structure: requirement → [dependencies]
            Includes circular dependency detection
        """

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

    async def analyze_constraints(
        self,
        requirements: List[str],
        context: Dict[str, Any]
    ) -> ConstraintAnalysis:
        """
        Analyze constraints affecting requirements.

        Constraint types:
        - Time constraints
        - Budget constraints
        - Technical constraints
        - Compliance requirements
        - Resource availability
        """
```

---

### 4. DomainQuestionLibrary (New)

**Location**: `gao_dev/orchestrator/domain_question_library.py`

**Responsibilities**:
- Detect domain from user input (web app, mobile, API, CLI, data pipeline)
- Provide domain-specific question libraries
- Context-aware question selection

**Architecture**:

```python
class DomainQuestionLibrary:
    """
    Domain-specific question libraries for requirements clarification.
    """

    def __init__(self):
        """Initialize with 5 domain libraries."""
        self.domains = {
            "web_app": self._load_web_app_questions(),
            "mobile_app": self._load_mobile_app_questions(),
            "api_service": self._load_api_questions(),
            "cli_tool": self._load_cli_questions(),
            "data_pipeline": self._load_data_pipeline_questions()
        }

    async def detect_domain(
        self,
        user_request: str,
        project_context: Optional[Dict[str, Any]] = None
    ) -> DomainType:
        """
        Detect domain from user request and context.

        Uses hybrid approach:
        1. Keyword matching (fast, 90% accuracy)
        2. LLM classification (slower, higher accuracy)

        Returns:
            Detected domain or "generic" if uncertain
        """

    def get_questions(
        self,
        domain: DomainType,
        focus_area: Optional[str] = None
    ) -> List[str]:
        """
        Get domain-specific questions.

        Args:
            domain: Detected domain
            focus_area: Optional focus (e.g., "authentication", "data_model")

        Returns:
            10-15 contextually relevant questions
        """
```

**Domain Question Sets**:

```python
# Web Application Questions
web_app_questions = {
    "general": [
        "Who are your target users?",
        "Will this be a public or internal app?",
        "Do you need user authentication?",
        "What's the expected user volume (concurrent users)?",
        "Mobile-responsive required?",
    ],
    "authentication": [
        "Email/password or social login?",
        "Multi-factor authentication required?",
        "Session timeout requirements?",
        "Password reset flow needed?",
    ],
    "data_model": [
        "What entities will the app manage?",
        "Relationships between entities?",
        "Data volume expectations?",
        "Real-time updates needed?",
    ],
    # ... more focus areas
}

# Mobile App Questions
mobile_app_questions = {
    "general": [
        "iOS, Android, or both?",
        "Native or cross-platform (React Native, Flutter)?",
        "Offline functionality required?",
        "Push notifications needed?",
        "Device sensors usage (camera, GPS, etc.)?",
    ],
    # ... more focus areas
}

# Similar structures for API, CLI, Data Pipeline
```

---

## Data Architecture

### Storage Strategy

Mary's outputs are stored as markdown files in `.gao-dev/mary/`:

```
.gao-dev/
├── mary/
│   ├── requirements-summaries/
│   │   └── summary-2025-11-10-14-30.md
│   ├── brainstorming-sessions/
│   │   ├── session-2025-11-10-15-00.md
│   │   └── mind-maps/
│   │       └── mindmap-2025-11-10-15-30.mmd
│   ├── vision-documents/
│   │   └── vision-2025-11-10-16-00.md
│   └── requirements-analysis/
│       └── analysis-2025-11-10-16-30.md
└── documents.db  # Metadata indexed in DB
```

### Data Models

**VisionSummary**:

```python
@dataclass
class VisionSummary:
    """Vision elicitation output."""
    original_request: str
    vision_canvas: VisionCanvas
    problem_solution_fit: ProblemSolutionFit
    outcome_map: OutcomeMap
    five_w_one_h: FiveWOneH
    created_at: datetime
    file_path: Path

@dataclass
class VisionCanvas:
    """Vision canvas template."""
    target_users: List[str]
    user_needs: List[str]
    product_vision: str
    key_features: List[str]
    success_metrics: List[str]
    differentiators: List[str]
```

**BrainstormingSummary**:

```python
@dataclass
class BrainstormingSummary:
    """Brainstorming session output."""
    topic: str
    techniques_used: List[str]
    ideas_generated: List[Idea]
    mind_maps: List[str]  # Mermaid syntax
    key_themes: List[str]
    insights_learnings: List[str]
    quick_wins: List[Idea]
    long_term_opportunities: List[Idea]
    recommended_followup: List[str]
    session_duration: timedelta
    created_at: datetime
    file_path: Path
```

**RequirementsAnalysis**:

```python
@dataclass
class RequirementsAnalysis:
    """Advanced requirements analysis output."""
    original_requirements: List[str]
    moscow: MoSCoWAnalysis
    kano: KanoAnalysis
    dependencies: DependencyGraph
    risks: List[Risk]
    constraints: ConstraintAnalysis
    prioritized_requirements: List[PrioritizedRequirement]
    created_at: datetime
    file_path: Path
```

---

## Integration Points

### 1. Brian → Mary Delegation

**Flow**:

```python
# BrianOrchestrator
async def assess_and_select_workflows(self, initial_prompt: str):
    # Step 1: Assess vagueness
    vagueness = await self._assess_vagueness(initial_prompt)

    if vagueness > 0.6:
        # Step 2: Delegate to Mary
        self.logger.info("delegating_to_mary", vagueness=vagueness)

        # Step 3: Mary selects strategy
        strategy = await self.mary.select_clarification_strategy(
            initial_prompt,
            vagueness,
            self.project_context
        )

        # Step 4: Mary executes selected strategy
        if strategy == ClarificationStrategy.VISION_ELICITATION:
            result = await self.mary.elicit_vision(initial_prompt)
        elif strategy == ClarificationStrategy.BRAINSTORMING:
            result = await self.mary.facilitate_brainstorming(initial_prompt)
        elif strategy == ClarificationStrategy.ADVANCED_REQUIREMENTS:
            result = await self.mary.analyze_requirements(
                initial_prompt,
                await self._extract_initial_requirements(initial_prompt)
            )
        else:  # BASIC_CLARIFICATION
            result = await self.mary.clarify_requirements(initial_prompt)

        # Step 5: Re-analyze with clarified requirements
        clarified_prompt = result.to_prompt()
        return await self._analyze_with_clear_requirements(clarified_prompt)

    # Request is clear - proceed normally
    return await self._analyze_prompt(initial_prompt)
```

### 2. Mary → AIAnalysisService

**All Mary dialogue uses AIAnalysisService**:

```python
# MaryOrchestrator
async def _generate_facilitation_prompt(
    self,
    technique: BrainstormingTechnique,
    topic: str,
    conversation_history: List[Message]
) -> str:
    """Generate next facilitation prompt using LLM."""

    prompt = f"""
You are Mary, a Business Analyst facilitating a brainstorming session.

Technique: {technique.name}
Description: {technique.description}
Topic: {topic}

Conversation so far:
{self._format_conversation(conversation_history)}

Generate the next facilitation prompt to guide the user.
Use the technique's prompts as inspiration: {technique.facilitation_prompts}

Be conversational, encouraging, and curious.
Ask open-ended questions to draw out ideas.
"""

    return await self.analysis_service.analyze(
        prompt,
        model="haiku",  # Fast and cheap for most facilitation
        temperature=0.7
    )
```

### 3. Mary → ConversationManager

**Session state management**:

```python
# MaryOrchestrator
async def elicit_vision(self, user_request: str) -> VisionSummary:
    # Create conversation session
    session = await self.conversation_manager.create_session(
        agent="Mary",
        workflow="vision-elicitation",
        context={"user_request": user_request}
    )

    # Multi-turn dialogue
    async for prompt in self._vision_elicitation_dialogue(session):
        # Yield prompt to user (via ChatSession)
        yield prompt

        # Wait for user response
        response = await session.get_user_response()

        # Save to conversation history
        await session.add_message("user", response)

        # Generate next prompt
        next_prompt = await self._generate_next_prompt(session)
        await session.add_message("mary", next_prompt)

    # Generate summary
    summary = await self._synthesize_vision(session)

    # Persist session
    await self.conversation_manager.save_session(session)

    return summary
```

---

## Workflow Architecture

### Vision Elicitation Workflows

**Location**: `gao_dev/workflows/1-analysis/vision-elicitation/`

**Workflows**:

1. **vision-canvas.yaml**
   - Target users
   - User needs
   - Product vision
   - Key features
   - Success metrics
   - Differentiators

2. **problem-solution-fit.yaml**
   - Problem statement
   - Current solutions (competitors)
   - Gaps in current solutions
   - Proposed solution
   - Value proposition

3. **outcome-mapping.yaml**
   - Desired outcomes (what success looks like)
   - Leading indicators
   - Lagging indicators
   - Boundary partners (stakeholders)

4. **5w1h-analysis.yaml**
   - Who: Target users, stakeholders
   - What: Features, capabilities
   - When: Timeline, milestones
   - Where: Deployment, usage context
   - Why: Business value, user value
   - How: Technical approach, resources

### Brainstorming Workflows

**Location**: `gao_dev/workflows/1-analysis/brainstorming/`

**Techniques Loaded from**: `bmad/core/workflows/brainstorming/brain-methods.csv`

**Workflow Structure**:

```yaml
name: brainstorming-session
agent: mary
phase: 1-analysis
description: Facilitate brainstorming with BMAD techniques

inputs:
  - topic: "{{brainstorming_topic}}"
  - technique: "{{selected_technique}}"
  - duration: "{{session_duration}}"

instructions: |
  You are facilitating a brainstorming session on: {{topic}}

  Technique: {{technique}}

  Follow the technique's facilitation prompts.
  Be conversational and encouraging.
  Ask open-ended questions.
  Build on user's ideas with "Yes, and..."
  Capture all ideas without judgment.

output_file: ".gao-dev/mary/brainstorming-sessions/session-{{timestamp}}.md"
```

### Requirements Analysis Workflows

**Location**: `gao_dev/workflows/1-analysis/requirements-analysis/`

**Workflows**:

1. **moscow-prioritization.yaml**
2. **kano-model.yaml**
3. **dependency-mapping.yaml**
4. **risk-identification.yaml**
5. **constraint-analysis.yaml**

---

## Brainstorming Engine Design

### Technique Recommendation Algorithm

```python
def recommend_techniques(
    self,
    goal: BrainstormingGoal,
    complexity: str,
    energy: str
) -> List[BrainstormingTechnique]:
    """
    Recommend techniques based on goal, complexity, and energy.

    Algorithm:
    1. Filter techniques by goal category
       - Innovation → creative, wild
       - Problem solving → deep, structured
       - Team building → collaborative
       - Strategic planning → structured, deep

    2. Match complexity
       - Complex topic → deep, structured
       - Simple topic → creative, wild

    3. Match energy level
       - High energy → creative, theatrical, wild
       - Low energy → structured, deep, introspective

    4. Select 2-4 complementary techniques
       - Progressive flow: divergent → focused → convergent

    5. Return with rationale
    """
```

### Mind Map Generation

**Mermaid Syntax**:

```python
async def generate_mind_map(
    self,
    ideas: List[Idea],
    central_topic: str
) -> str:
    """
    Generate mermaid mind map from ideas.

    Algorithm:
    1. Use LLM to cluster ideas into themes
    2. Build hierarchical structure: topic → themes → ideas
    3. Generate mermaid syntax

    Example output:
    ```mermaid
    graph TD
        A[Authentication System]
        A --> B[User Management]
        A --> C[Security]
        A --> D[UX]
        B --> B1[Registration]
        B --> B2[Profile]
        C --> C1[2FA]
        C --> C2[OAuth]
        D --> D1[Passwordless]
        D --> D2[Social Login]
    ```
    """
```

---

## Requirements Analysis Engine

### MoSCoW Prioritization

**Algorithm**:

```python
async def moscow_prioritize(
    self,
    requirements: List[str],
    context: Dict[str, Any]
) -> MoSCoWAnalysis:
    """
    Prioritize using MoSCoW method.

    For each requirement:
    1. LLM analyzes:
       - Is this critical for MVP? (Must)
       - Important but MVP can work without? (Should)
       - Nice to have if time? (Could)
       - Out of scope? (Won't)

    2. Consider context:
       - Timeline constraints
       - Resource availability
       - Technical dependencies
       - Business priorities

    3. Return categorized requirements
    """
```

### Kano Model Categorization

**Algorithm**:

```python
async def kano_categorize(
    self,
    requirements: List[str]
) -> KanoAnalysis:
    """
    Categorize using Kano model.

    For each requirement:
    1. LLM asks:
       - Do users expect this? (Basic)
       - Does quality matter? (Performance)
       - Will this delight users? (Excitement)
       - Do users care? (Indifferent/Reverse)

    2. Categorize based on user expectations

    3. Return with recommendations:
       - Basic: Must implement well
       - Performance: Invest in quality
       - Excitement: Differentiate here
    """
```

---

## Domain Intelligence System

### Domain Detection

**Hybrid Approach**:

```python
async def detect_domain(
    self,
    user_request: str,
    project_context: Optional[Dict[str, Any]] = None
) -> DomainType:
    """
    Detect domain using hybrid approach.

    Phase 1: Keyword Matching (fast, 90% accuracy)
    - "web app", "website", "frontend" → web_app
    - "mobile", "iOS", "Android" → mobile_app
    - "API", "REST", "GraphQL" → api_service
    - "CLI", "command line" → cli_tool
    - "ETL", "pipeline", "data processing" → data_pipeline

    Phase 2: LLM Classification (if uncertain)
    - Use LLM to analyze request
    - Consider project context
    - Return best match or "generic"

    Confidence threshold: 0.7
    If confidence < 0.7, fall back to generic questions
    """
```

### Question Selection

**Context-Aware Algorithm**:

```python
def get_questions(
    self,
    domain: DomainType,
    focus_area: Optional[str] = None
) -> List[str]:
    """
    Select questions based on domain and focus area.

    1. Load domain question library
    2. If focus_area specified:
       - Return focused questions (10-15)
    3. Else:
       - Return general questions (5-7)
       - Add focus area discovery questions (3-5)

    4. Order by importance:
       - Who (users/stakeholders)
       - What (features/capabilities)
       - Why (value/business case)
       - How (technical approach)
       - Constraints (time/budget/technical)
    """
```

---

## Performance & Scalability

### Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Strategy selection | <500ms | Time from request to strategy selected |
| Vision elicitation | <3 min | Full vision canvas completion |
| Brainstorming technique | 15-20 min | Per technique (user-paced) |
| Mind map generation | <5 sec | Mermaid syntax generation |
| Requirements analysis | <2 min | Full MoSCoW + Kano + dependencies |
| Domain detection | <200ms | Keyword + LLM classification |

### Optimization Strategies

1. **Model Selection**:
   - Haiku for most interactions (fast, cheap)
   - Sonnet only for complex synthesis (mind maps, insights)

2. **Caching**:
   - Technique library cached in memory
   - Domain question libraries cached
   - Conversation history cached in ConversationManager

3. **Streaming**:
   - Stream LLM responses for real-time feedback
   - Yield facilitation prompts incrementally

4. **Parallel Processing**:
   - Domain detection + question selection in parallel
   - MoSCoW + Kano analysis can run concurrently

### Scalability Considerations

- **Stateless Core**: MaryOrchestrator is stateless (state in ConversationManager)
- **Session Limits**: Max 1 hour per session, checkpoint/resume for longer
- **Token Management**: Conversation history summarized after 50 messages
- **Concurrent Sessions**: Support 10+ simultaneous users (Epic 30 infrastructure)

---

## Security & Privacy

### Data Privacy

1. **User Input Protection**:
   - All user input encrypted in transit (HTTPS)
   - Session data encrypted at rest
   - No PII logged (use session IDs only)

2. **LLM API Security**:
   - API keys in environment variables (not code)
   - Rate limiting on AIAnalysisService
   - Request/response logging (without content)

3. **Output Storage**:
   - Mary's outputs stored locally (`.gao-dev/mary/`)
   - No cloud storage of user requirements
   - Files owned by project (not shared)

### Error Handling

```python
class MaryOrchestrator:
    async def elicit_vision(self, user_request: str) -> VisionSummary:
        try:
            # Vision elicitation workflow
            ...
        except LLMAPIError as e:
            # LLM API failure
            self.logger.error("llm_api_error", error=str(e))
            raise MaryOrchestrationError(
                "I'm having trouble connecting to my knowledge base. "
                "Please try again in a moment."
            )
        except ConversationTimeoutError as e:
            # User inactive for too long
            self.logger.warning("conversation_timeout", session_id=e.session_id)
            # Save checkpoint for resume
            await self._save_checkpoint(e.session_id)
            raise MaryOrchestrationError(
                "Our session timed out. I've saved our progress. "
                "Type 'resume' to continue where we left off."
            )
        except Exception as e:
            # Unknown error
            self.logger.exception("unexpected_error", error=str(e))
            raise MaryOrchestrationError(
                "I encountered an unexpected error. "
                "Let's start fresh or try a different approach."
            )
```

---

## Technology Stack

### Languages & Frameworks

- **Python 3.11+**: Core language
- **asyncio**: Asynchronous I/O for streaming
- **structlog**: Structured logging
- **pydantic**: Data validation
- **pathlib**: Path handling

### External Services

- **Claude API (Anthropic)**: LLM via AIAnalysisService
  - Haiku: Fast, cheap (most Mary interactions)
  - Sonnet: Smart, expensive (complex synthesis only)

### Data Storage

- **SQLite**: Metadata indexing (documents.db)
- **Markdown Files**: Human-readable outputs (.gao-dev/mary/)
- **In-Memory**: Technique library, question libraries, session cache

### Visualization

- **Mermaid**: Text-based mind maps and diagrams
- **Rich (Python)**: Terminal formatting for CLI output

### Testing

- **pytest**: Unit and integration tests
- **pytest-asyncio**: Async test support
- **unittest.mock**: Mocking AIAnalysisService for tests

---

## Deployment Architecture

### File Structure (After Epic 31)

```
gao_dev/
├── orchestrator/
│   ├── mary_orchestrator.py          # Enhanced from Epic 30
│   ├── brainstorming_engine.py       # New
│   ├── requirements_analyzer.py      # New
│   └── domain_question_library.py    # New
│
├── workflows/
│   └── 1-analysis/
│       ├── vision-elicitation/
│       │   ├── vision-canvas.yaml
│       │   ├── problem-solution-fit.yaml
│       │   ├── outcome-mapping.yaml
│       │   └── 5w1h-analysis.yaml
│       ├── brainstorming/
│       │   └── brainstorming-session.yaml
│       └── requirements-analysis/
│           ├── moscow-prioritization.yaml
│           ├── kano-model.yaml
│           ├── dependency-mapping.yaml
│           ├── risk-identification.yaml
│           └── constraint-analysis.yaml
│
├── config/
│   └── domains/
│       ├── web_app_questions.yaml
│       ├── mobile_app_questions.yaml
│       ├── api_service_questions.yaml
│       ├── cli_tool_questions.yaml
│       └── data_pipeline_questions.yaml
│
└── data/
    └── bmad/
        ├── brain-methods.csv          # 36 techniques
        └── adv-elicit-methods.csv     # 39 methods
```

---

## Migration & Rollout

### Phase 1: Foundation (Story 31.1)

- Enhance MaryOrchestrator with strategy selection
- Implement vision elicitation workflows
- Test Brian → Mary delegation with vision elicitation

### Phase 2: Brainstorming (Story 31.2)

- Build BrainstormingEngine
- Load BMAD techniques
- Implement mind map generation
- Test brainstorming facilitation

### Phase 3: Advanced Analysis (Story 31.3)

- Build RequirementsAnalyzer
- Implement MoSCoW, Kano, dependencies, risks
- Test advanced analysis workflows

### Phase 4: Domain Intelligence (Story 31.4)

- Build DomainQuestionLibrary
- Create 5 domain question sets
- Implement domain detection
- Test context-aware questions

### Phase 5: Integration (Story 31.5)

- 15+ integration tests
- User guide and examples
- Performance validation
- Final end-to-end testing

---

## Appendix: API Reference

### MaryOrchestrator

```python
class MaryOrchestrator:
    # Strategy Selection
    async def select_clarification_strategy(
        user_request: str,
        vagueness_score: float,
        project_context: Optional[Dict]
    ) -> ClarificationStrategy

    # Vision Elicitation
    async def elicit_vision(user_request: str) -> VisionSummary

    # Brainstorming
    async def facilitate_brainstorming(
        user_request: str,
        technique: Optional[str]
    ) -> BrainstormingSummary

    # Requirements Analysis
    async def analyze_requirements(
        user_request: str,
        initial_requirements: List[str]
    ) -> RequirementsAnalysis

    # Basic Clarification (from Epic 30)
    async def clarify_requirements(
        user_request: str,
        project_context: Optional[Dict]
    ) -> RequirementsSummary
```

### BrainstormingEngine

```python
class BrainstormingEngine:
    # Technique Management
    def _load_techniques() -> List[BrainstormingTechnique]
    async def recommend_techniques(
        topic: str,
        goal: BrainstormingGoal,
        context: Dict
    ) -> List[BrainstormingTechnique]

    # Facilitation
    async def facilitate_technique(
        technique: BrainstormingTechnique,
        topic: str
    ) -> AsyncIterator[FacilitationPrompt]

    # Synthesis
    async def generate_mind_map(
        ideas: List[Idea],
        central_topic: str
    ) -> str
    async def synthesize_insights(
        session: BrainstormingSession
    ) -> BrainstormingSummary
```

### RequirementsAnalyzer

```python
class RequirementsAnalyzer:
    async def moscow_prioritize(
        requirements: List[str],
        context: Dict
    ) -> MoSCoWAnalysis

    async def kano_categorize(
        requirements: List[str]
    ) -> KanoAnalysis

    async def map_dependencies(
        requirements: List[str]
    ) -> DependencyGraph

    async def identify_risks(
        requirements: List[str],
        context: Dict
    ) -> List[Risk]

    async def analyze_constraints(
        requirements: List[str],
        context: Dict
    ) -> ConstraintAnalysis
```

### DomainQuestionLibrary

```python
class DomainQuestionLibrary:
    async def detect_domain(
        user_request: str,
        project_context: Optional[Dict]
    ) -> DomainType

    def get_questions(
        domain: DomainType,
        focus_area: Optional[str]
    ) -> List[str]
```

---

**Document Status**: Complete
**Next Steps**: Review architecture, approve, proceed with story implementation
**Author**: Winston (Technical Architect)
**Reviewers**: Brian (Workflow Coordinator), Mary (Business Analyst), Amelia (Developer)

**Version History**:
- v1.0 (2025-11-10): Initial architecture document created
