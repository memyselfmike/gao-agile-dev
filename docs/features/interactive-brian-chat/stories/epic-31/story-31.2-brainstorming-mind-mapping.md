# Story 31.2: Brainstorming & Mind Mapping

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.2
**Priority**: P0 (Critical - Brainstorming Core Capability)
**Estimate**: 8 story points
**Duration**: 3-4 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1 (Vision Elicitation)

---

## Story Description

Implement brainstorming facilitation engine that helps users explore solutions creatively using 10+ techniques from BMAD library. Includes text-based mind map generation (mermaid diagrams), SCAMPER technique, "How Might We" framing, and affinity mapping.

Mary becomes a brainstorming facilitator who guides users through creative exploration, captures ideas, and synthesizes insights.

---

## User Story

**As a** user exploring solutions
**I want** Mary to facilitate brainstorming sessions with multiple techniques
**So that** we explore creative approaches and find the best solution

---

## Acceptance Criteria

- [ ] BrainstormingEngine class implemented
- [ ] 10+ brainstorming techniques loaded from BMAD library (`bmad/core/workflows/brainstorming/brain-methods.csv`)
- [ ] Technique recommendation algorithm based on goal and context
- [ ] SCAMPER technique fully implemented (Substitute, Combine, Adapt, Modify, Put, Eliminate, Reverse)
- [ ] "How Might We" framing implemented
- [ ] Affinity mapping and idea grouping implemented
- [ ] Mind map generation in mermaid syntax
- [ ] BrainstormingSummary data model implemented
- [ ] Ideas captured and organized by theme
- [ ] Insights synthesis (key themes, quick wins, long-term opportunities)
- [ ] Mary facilitates brainstorming conversationally (LLM-powered, not scripted)
- [ ] Brainstorming outputs saved to `.gao-dev/mary/brainstorming-sessions/`
- [ ] 12+ unit tests passing
- [ ] Performance: Technique recommendation <500ms, Mind map generation <5 sec

---

## Files to Create/Modify

### New Files

- `gao_dev/orchestrator/brainstorming_engine.py` (~350 LOC)
  - BrainstormingEngine class
  - Load 36 techniques from BMAD CSV
  - Technique recommendation algorithm
  - Facilitation prompt generation
  - Mind map generation (mermaid syntax)
  - Insights synthesis

- `gao_dev/core/models/brainstorming_summary.py` (~150 LOC)
  - BrainstormingTechnique dataclass
  - Idea dataclass
  - BrainstormingSummary dataclass
  - to_markdown() method

- `gao_dev/workflows/1-analysis/brainstorming/brainstorming-session.yaml` (~80 LOC)
  - Brainstorming session workflow
  - Technique selection prompts
  - Facilitation guidelines

- `tests/orchestrator/test_brainstorming_engine.py` (~250 LOC)
  - Tests for technique loading
  - Tests for recommendation algorithm
  - Tests for SCAMPER technique
  - Tests for mind map generation
  - Tests for insights synthesis

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~80 LOC added)
  - Add `facilitate_brainstorming()` method
  - Integrate BrainstormingEngine
  - Session management for brainstorming

---

## Technical Design

### BrainstormingEngine Architecture

**Location**: `gao_dev/orchestrator/brainstorming_engine.py`

```python
"""Brainstorming facilitation engine using BMAD techniques."""

from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import csv
from pathlib import Path
import structlog

from ..core.services.ai_analysis_service import AIAnalysisService
from ..core.conversation_manager import ConversationManager

logger = structlog.get_logger()


class BrainstormingGoal(Enum):
    """Brainstorming session goals."""
    INNOVATION = "innovation"  # Generate new ideas
    PROBLEM_SOLVING = "problem_solving"  # Solve specific problem
    STRATEGIC_PLANNING = "strategic_planning"  # Plan strategy
    EXPLORATION = "exploration"  # Open-ended exploration


@dataclass
class BrainstormingTechnique:
    """Brainstorming technique from BMAD library."""
    category: str  # structured, creative, collaborative, deep, theatrical, wild, introspective_delight
    name: str
    description: str
    facilitation_prompts: List[str]
    best_for: str
    energy_level: str  # high, moderate, low
    typical_duration: str  # e.g., "15-20" minutes


@dataclass
class Idea:
    """Captured idea from brainstorming."""
    content: str
    technique: str
    theme: Optional[str] = None
    priority: Optional[str] = None  # quick_win, long_term, moonshot


class BrainstormingEngine:
    """
    Facilitate brainstorming sessions with BMAD techniques.

    Loads 36 techniques from: bmad/core/workflows/brainstorming/brain-methods.csv
    """

    def __init__(
        self,
        analysis_service: AIAnalysisService,
        conversation_manager: ConversationManager
    ):
        """Initialize with technique library."""
        self.analysis_service = analysis_service
        self.conversation_manager = conversation_manager
        self.techniques = self._load_techniques()
        self.logger = logger.bind(component="brainstorming_engine")

    def _load_techniques(self) -> Dict[str, BrainstormingTechnique]:
        """
        Load techniques from BMAD CSV.

        CSV columns: category, technique_name, description, facilitation_prompts,
                     best_for, energy_level, typical_duration

        Returns:
            Dict mapping technique_name → BrainstormingTechnique (36 techniques)
        """
        csv_path = Path(__file__).parent.parent.parent / "bmad" / "core" / "workflows" / "brainstorming" / "brain-methods.csv"

        techniques = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                technique = BrainstormingTechnique(
                    category=row['category'],
                    name=row['technique_name'],
                    description=row['description'],
                    facilitation_prompts=row['facilitation_prompts'].split('|'),
                    best_for=row['best_for'],
                    energy_level=row['energy_level'],
                    typical_duration=row['typical_duration']
                )
                techniques[technique.name] = technique

        self.logger.info("techniques_loaded", count=len(techniques))
        return techniques

    async def recommend_techniques(
        self,
        topic: str,
        goal: BrainstormingGoal,
        context: Dict[str, Any]
    ) -> List[BrainstormingTechnique]:
        """
        Recommend 2-4 techniques based on goal and context.

        Recommendation algorithm:
        1. Filter by goal:
           - INNOVATION → creative, wild categories
           - PROBLEM_SOLVING → deep, structured categories
           - STRATEGIC_PLANNING → structured, deep categories
           - EXPLORATION → all categories

        2. Consider energy level from context
        3. Select complementary techniques (diverse approaches)
        4. Return 2-4 techniques with rationale
        """
        self.logger.info("recommending_techniques", goal=goal.value, topic=topic[:50])

        # Filter by goal
        if goal == BrainstormingGoal.INNOVATION:
            categories = ["creative", "wild"]
        elif goal == BrainstormingGoal.PROBLEM_SOLVING:
            categories = ["deep", "structured"]
        elif goal == BrainstormingGoal.STRATEGIC_PLANNING:
            categories = ["structured", "deep"]
        else:  # EXPLORATION
            categories = ["creative", "collaborative", "structured"]

        candidates = [
            t for t in self.techniques.values()
            if t.category in categories
        ]

        # Select 2-4 diverse techniques
        recommendations = self._select_diverse_techniques(candidates, count=3)

        self.logger.info(
            "techniques_recommended",
            count=len(recommendations),
            techniques=[t.name for t in recommendations]
        )
        return recommendations

    def _select_diverse_techniques(
        self,
        candidates: List[BrainstormingTechnique],
        count: int = 3
    ) -> List[BrainstormingTechnique]:
        """Select diverse techniques from candidates."""
        # Ensure diversity by selecting from different categories
        selected = []
        used_categories = set()

        for technique in candidates:
            if technique.category not in used_categories:
                selected.append(technique)
                used_categories.add(technique.category)
                if len(selected) >= count:
                    break

        return selected[:count]

    async def facilitate_technique(
        self,
        technique: BrainstormingTechnique,
        topic: str,
        session: Any
    ) -> AsyncIterator[str]:
        """
        Facilitate brainstorming technique through guided prompts.

        Yields facilitation prompts one at a time.
        User responses captured by ConversationManager.

        Example for SCAMPER:
        - Yield: "S - SUBSTITUTE: What could you substitute?"
        - User responds
        - Yield: "C - COMBINE: What could you combine?"
        - etc.
        """
        self.logger.info("facilitating_technique", technique=technique.name)

        # Introduction
        intro = f"""
Let's explore {topic} using the {technique.name} technique!

{technique.description}

Ready to begin?
"""
        yield intro

        # Iterate through facilitation prompts
        for i, prompt_template in enumerate(technique.facilitation_prompts):
            # Adapt prompt to topic
            prompt = self._adapt_prompt_to_topic(prompt_template, topic)

            yield f"Mary: {prompt}"

            # Wait for user response (handled by session)
            response = await session.get_user_response()

            # Build on response with "Yes, and..."
            if i < len(technique.facilitation_prompts) - 1:
                buildup = await self._generate_buildup(response, topic)
                if buildup:
                    yield f"Mary: {buildup}"

    def _adapt_prompt_to_topic(self, prompt_template: str, topic: str) -> str:
        """Adapt generic prompt to specific topic."""
        # Simple replacement for now
        return prompt_template.replace("this", topic)

    async def _generate_buildup(self, user_response: str, topic: str) -> Optional[str]:
        """
        Generate "Yes, and..." buildup using LLM.

        Example:
        User: "We could use biometrics"
        Mary: "Yes! Biometrics could add security. What if we combined that with..."
        """
        prompt = f"""
You are Mary, facilitating a brainstorming session on {topic}.

The user just said: "{user_response}"

Generate a brief encouraging response that:
1. Acknowledges their idea ("Yes!", "Great!", "Interesting!")
2. Builds on it with "and..." or "what if..."
3. Keep it under 2 sentences

Be enthusiastic but concise.
"""

        return await self.analysis_service.analyze(
            prompt,
            model="haiku",
            temperature=0.8,
            max_tokens=100
        )

    async def generate_mind_map(
        self,
        ideas: List[Idea],
        central_topic: str
    ) -> str:
        """
        Generate text-based mind map in mermaid syntax.

        Uses LLM to cluster ideas into themes and create hierarchy.

        Returns:
            Mermaid diagram code

        Example output:
        ```mermaid
        graph TD
            A[Authentication System]
            A --> B[User Management]
            A --> C[Security]
            B --> B1[Registration]
            B --> B2[Profile]
            C --> C1[2FA]
            C --> C2[Biometrics]
        ```
        """
        self.logger.info("generating_mind_map", idea_count=len(ideas))

        # Use LLM to cluster ideas into themes
        clustering_prompt = f"""
You have {len(ideas)} ideas from brainstorming on "{central_topic}".

Ideas:
{chr(10).join(f"- {idea.content}" for idea in ideas)}

Cluster these ideas into 3-5 themes.
For each theme, list the relevant ideas.

Return as JSON:
{{
  "themes": [
    {{
      "name": "Theme Name",
      "ideas": ["idea1", "idea2"]
    }}
  ]
}}
"""

        response = await self.analysis_service.analyze(
            clustering_prompt,
            model="haiku",
            response_format="json"
        )

        themes = json.loads(response)["themes"]

        # Generate mermaid syntax
        mermaid = ["graph TD"]
        mermaid.append(f"    A[{central_topic}]")

        for i, theme in enumerate(themes):
            theme_id = chr(66 + i)  # B, C, D, ...
            mermaid.append(f"    A --> {theme_id}[{theme['name']}]")

            for j, idea in enumerate(theme['ideas'][:5]):  # Limit 5 ideas per theme
                idea_id = f"{theme_id}{j+1}"
                # Truncate long ideas
                idea_text = idea[:30] + "..." if len(idea) > 30 else idea
                mermaid.append(f"    {theme_id} --> {idea_id}[{idea_text}]")

        return "\n".join(mermaid)

    async def synthesize_insights(
        self,
        session: Any,
        ideas: List[Idea],
        techniques_used: List[str]
    ) -> Dict[str, Any]:
        """
        Synthesize session into insights.

        Returns:
            - key_themes: Recurring themes across techniques
            - insights_learnings: Key realizations
            - quick_wins: Ideas that can be implemented quickly
            - long_term_opportunities: Ideas needing more development
            - recommended_followup: Suggested next techniques
        """
        self.logger.info("synthesizing_insights", idea_count=len(ideas))

        synthesis_prompt = f"""
Analyze this brainstorming session and extract insights.

Techniques used: {', '.join(techniques_used)}
Ideas generated: {len(ideas)}

Ideas:
{chr(10).join(f"- {idea.content}" for idea in ideas)}

Extract:
1. Key themes (recurring concepts)
2. Insights and learnings (realizations)
3. Quick wins (ideas implementable in <1 month)
4. Long-term opportunities (ideas needing >3 months)
5. Recommended follow-up techniques

Return as JSON:
{{
  "key_themes": ["theme1", "theme2"],
  "insights_learnings": ["insight1", "insight2"],
  "quick_wins": ["idea1", "idea2"],
  "long_term_opportunities": ["idea3", "idea4"],
  "recommended_followup": ["technique1", "technique2"]
}}
"""

        response = await self.analysis_service.analyze(
            synthesis_prompt,
            model="sonnet",  # Use smarter model for synthesis
            response_format="json"
        )

        return json.loads(response)
```

### SCAMPER Technique Implementation

```python
async def facilitate_scamper(
    self,
    topic: str,
    session: Any
) -> List[Idea]:
    """
    Facilitate SCAMPER technique.

    SCAMPER: Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse
    """
    scamper_prompts = [
        ("Substitute", f"What elements of {topic} could you SUBSTITUTE? (Replace with something else)"),
        ("Combine", f"What could you COMBINE with {topic}? (Merge with other features/ideas)"),
        ("Adapt", f"How could you ADAPT {topic}? (Adjust to serve another purpose)"),
        ("Modify", f"What could you MODIFY in {topic}? (Change size, shape, attributes)"),
        ("Put to other uses", f"How else could {topic} be used? (New contexts or users)"),
        ("Eliminate", f"What could you ELIMINATE from {topic}? (Remove complexity)"),
        ("Reverse", f"What if you REVERSED {topic}? (Do opposite, flip assumptions)")
    ]

    ideas = []
    for lens, prompt in scamper_prompts:
        yield f"\nMary: {prompt}"
        response = await session.get_user_response()

        # Capture ideas
        idea = Idea(
            content=f"{lens}: {response}",
            technique="SCAMPER"
        )
        ideas.append(idea)

        # Build on response
        buildup = await self._generate_buildup(response, topic)
        if buildup:
            yield f"Mary: {buildup}"

    return ideas
```

### BrainstormingSummary Data Model

**Location**: `gao_dev/core/models/brainstorming_summary.py`

```python
"""Brainstorming session data models."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class Idea:
    """Captured idea from brainstorming."""
    content: str
    technique: str
    theme: Optional[str] = None
    priority: Optional[str] = None  # quick_win, long_term, moonshot
    created_at: datetime = field(default_factory=datetime.now)


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
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[Path] = None

    def to_markdown(self) -> str:
        """Generate complete markdown report."""
        sections = []

        sections.append(f"# Brainstorming Session: {self.topic}\n")
        sections.append(f"**Date**: {self.created_at.strftime('%Y-%m-%d %H:%M')}")
        sections.append(f"**Duration**: {self.session_duration}")
        sections.append(f"**Techniques Used**: {', '.join(self.techniques_used)}")
        sections.append(f"**Ideas Generated**: {len(self.ideas_generated)}\n")
        sections.append("---\n")

        # Key Themes
        sections.append("## Key Themes\n")
        for theme in self.key_themes:
            sections.append(f"- {theme}")
        sections.append("")

        # All Ideas
        sections.append("## Ideas Generated\n")
        for idea in self.ideas_generated:
            sections.append(f"### {idea.technique}")
            sections.append(f"{idea.content}\n")

        # Quick Wins
        sections.append("## Quick Wins (Implement in <1 month)\n")
        for idea in self.quick_wins:
            sections.append(f"- {idea.content}")
        sections.append("")

        # Long-term
        sections.append("## Long-term Opportunities (>3 months)\n")
        for idea in self.long_term_opportunities:
            sections.append(f"- {idea.content}")
        sections.append("")

        # Insights
        sections.append("## Insights & Learnings\n")
        for insight in self.insights_learnings:
            sections.append(f"- {insight}")
        sections.append("")

        # Mind Maps
        if self.mind_maps:
            sections.append("## Mind Maps\n")
            for i, mindmap in enumerate(self.mind_maps):
                sections.append(f"### Map {i+1}\n")
                sections.append("```mermaid")
                sections.append(mindmap)
                sections.append("```\n")

        # Recommended Follow-up
        sections.append("## Recommended Follow-up Techniques\n")
        for technique in self.recommended_followup:
            sections.append(f"- {technique}")

        return "\n".join(sections)
```

---

## Testing Strategy

### Unit Tests (12+ tests)

1. **test_load_techniques_from_csv** - Verify 36 techniques loaded
2. **test_technique_recommendation_innovation** - Innovation goal → creative/wild
3. **test_technique_recommendation_problem_solving** - Problem solving → deep/structured
4. **test_scamper_facilitation** - SCAMPER generates 7 prompts
5. **test_how_might_we_framing** - HMW reframes problems as opportunities
6. **test_affinity_mapping** - Ideas grouped by theme
7. **test_mind_map_generation** - Mermaid syntax generated correctly
8. **test_insights_synthesis** - Themes and quick wins identified
9. **test_mary_facilitate_brainstorming** - Mary orchestrates session
10. **test_brainstorming_summary_to_markdown** - Complete report generated
11. **test_ideas_captured_with_technique** - Each idea tagged with technique
12. **test_session_saved_to_file** - Output saved to `.gao-dev/mary/brainstorming-sessions/`

---

## Definition of Done

- [ ] BrainstormingEngine implemented with 36 techniques
- [ ] SCAMPER, HMW, affinity mapping implemented
- [ ] Mind map generation (mermaid syntax)
- [ ] Insights synthesis (themes, quick wins, long-term)
- [ ] Mary facilitates brainstorming conversationally (LLM-powered)
- [ ] BrainstormingSummary data model complete
- [ ] Outputs saved to `.gao-dev/mary/brainstorming-sessions/`
- [ ] 12+ tests passing
- [ ] Performance validated (<500ms recommendation, <5s mind map)
- [ ] Manual testing: Full brainstorming session
- [ ] Code review complete
- [ ] Git commit: `feat(epic-31): Story 31.2 - Brainstorming & Mind Mapping (8 pts)`

---

## Manual Testing Checklist

- [ ] Start `gao-dev start`
- [ ] Type: "I need ideas for improving authentication"
- [ ] Verify: Mary suggests brainstorming
- [ ] Choose technique: SCAMPER
- [ ] Answer all 7 SCAMPER prompts
- [ ] Verify: Mary builds on answers with "Yes, and..."
- [ ] Complete session (10-20 minutes)
- [ ] Verify: Mind map generated
- [ ] Verify: Insights synthesized (themes, quick wins)
- [ ] Verify: Summary saved to file
- [ ] Check summary includes all ideas and insights

---

**Created**: 2025-11-10
**Status**: Ready to Implement
