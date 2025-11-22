"""Brainstorming facilitation engine using BMAD techniques.

This module implements brainstorming facilitation with 36 techniques from BMAD library,
including technique recommendation, session facilitation, mind map generation,
and insights synthesis.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.2 - Brainstorming & Mind Mapping
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import csv
import json
from pathlib import Path
import structlog

from ..core.services.ai_analysis_service import AIAnalysisService
from .conversation_manager import ConversationManager
from ..core.models.brainstorming_summary import (
    BrainstormingTechnique,
    Idea,
)


logger = structlog.get_logger()


class BrainstormingGoal(str, Enum):
    """Brainstorming session goals."""

    INNOVATION = "innovation"  # Generate new ideas
    PROBLEM_SOLVING = "problem_solving"  # Solve specific problem
    STRATEGIC_PLANNING = "strategic_planning"  # Plan strategy
    EXPLORATION = "exploration"  # Open-ended exploration


class BrainstormingEngine:
    """
    Facilitate brainstorming sessions with BMAD techniques.

    Loads 36 techniques from: bmad/core/workflows/brainstorming/brain-methods.csv
    Provides technique recommendation, facilitation, mind map generation, and synthesis.
    """

    def __init__(
        self,
        analysis_service: AIAnalysisService,
        conversation_manager: Optional[ConversationManager] = None,
    ):
        """
        Initialize brainstorming engine.

        Args:
            analysis_service: AI analysis service for LLM-powered facilitation
            conversation_manager: Optional conversation manager for multi-turn dialogue
        """
        self.analysis_service = analysis_service
        self.conversation_manager = conversation_manager
        self.logger = logger.bind(component="brainstorming_engine")
        self.techniques = self._load_techniques()

    def _load_techniques(self) -> Dict[str, BrainstormingTechnique]:
        """
        Load techniques from BMAD CSV.

        CSV columns: category, technique_name, description, facilitation_prompts,
                     best_for, energy_level, typical_duration

        Returns:
            Dict mapping technique_name -> BrainstormingTechnique (36 techniques)

        Raises:
            FileNotFoundError: If CSV file not found
            ValueError: If CSV format is invalid
        """
        csv_path = (
            Path(__file__).parent.parent.parent
            / "bmad"
            / "core"
            / "workflows"
            / "brainstorming"
            / "brain-methods.csv"
        )

        if not csv_path.exists():
            self.logger.error("techniques_csv_not_found", path=str(csv_path))
            raise FileNotFoundError(f"Techniques CSV not found: {csv_path}")

        techniques = {}
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    technique = BrainstormingTechnique(
                        category=row["category"],
                        name=row["technique_name"],
                        description=row["description"],
                        facilitation_prompts=row["facilitation_prompts"].split("|"),
                        best_for=row["best_for"],
                        energy_level=row["energy_level"],
                        typical_duration=row["typical_duration"],
                    )
                    techniques[technique.name] = technique
        except Exception as e:
            self.logger.error("techniques_load_failed", error=str(e))
            raise ValueError(f"Failed to load techniques from CSV: {e}")

        self.logger.info("techniques_loaded", count=len(techniques))
        return techniques

    async def recommend_techniques(
        self, topic: str, goal: BrainstormingGoal, context: Optional[Dict[str, Any]] = None
    ) -> List[BrainstormingTechnique]:
        """
        Recommend 2-4 techniques based on goal and context.

        Recommendation algorithm:
        1. Filter by goal:
           - INNOVATION -> creative, wild categories
           - PROBLEM_SOLVING -> deep, structured categories
           - STRATEGIC_PLANNING -> structured, deep categories
           - EXPLORATION -> all categories

        2. Consider energy level from context (if provided)
        3. Select complementary techniques (diverse approaches)
        4. Return 2-4 techniques with rationale

        Args:
            topic: Brainstorming topic
            goal: Brainstorming goal
            context: Optional context with preferences (energy_level, etc.)

        Returns:
            List of 2-4 recommended BrainstormingTechnique objects
        """
        self.logger.info("recommending_techniques", goal=goal.value, topic=topic[:50])

        if context is None:
            context = {}

        # Filter by goal
        if goal == BrainstormingGoal.INNOVATION:
            categories = ["creative", "wild", "theatrical"]
        elif goal == BrainstormingGoal.PROBLEM_SOLVING:
            categories = ["deep", "structured"]
        elif goal == BrainstormingGoal.STRATEGIC_PLANNING:
            categories = ["structured", "deep", "collaborative"]
        else:  # EXPLORATION
            categories = ["creative", "collaborative", "structured"]

        candidates = [t for t in self.techniques.values() if t.category in categories]

        # Filter by energy level if specified
        preferred_energy = context.get("energy_level")
        if preferred_energy:
            energy_filtered = [t for t in candidates if t.energy_level == preferred_energy]
            if energy_filtered:
                candidates = energy_filtered

        # Select 3 diverse techniques
        recommendations = self._select_diverse_techniques(candidates, count=3)

        self.logger.info(
            "techniques_recommended",
            count=len(recommendations),
            techniques=[t.name for t in recommendations],
        )
        return recommendations

    def _select_diverse_techniques(
        self, candidates: List[BrainstormingTechnique], count: int = 3
    ) -> List[BrainstormingTechnique]:
        """
        Select diverse techniques from candidates.

        Ensures diversity by selecting from different categories when possible.

        Args:
            candidates: List of candidate techniques
            count: Number of techniques to select

        Returns:
            List of selected techniques
        """
        selected = []
        used_categories = set()

        # First pass: one from each category
        for technique in candidates:
            if technique.category not in used_categories:
                selected.append(technique)
                used_categories.add(technique.category)
                if len(selected) >= count:
                    break

        # Second pass: fill remaining if needed
        if len(selected) < count:
            for technique in candidates:
                if technique not in selected:
                    selected.append(technique)
                    if len(selected) >= count:
                        break

        return selected[:count]

    async def facilitate_scamper(
        self, topic: str, user_responses: Optional[List[str]] = None
    ) -> List[Idea]:
        """
        Facilitate SCAMPER technique.

        SCAMPER: Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse

        Args:
            topic: Topic to brainstorm about
            user_responses: Optional list of 7 user responses (for testing)

        Returns:
            List of 7 ideas (one per SCAMPER lens)
        """
        scamper_prompts = [
            ("Substitute", f"What elements of {topic} could you SUBSTITUTE? (Replace with something else)"),
            ("Combine", f"What could you COMBINE with {topic}? (Merge with other features/ideas)"),
            ("Adapt", f"How could you ADAPT {topic}? (Adjust to serve another purpose)"),
            ("Modify", f"What could you MODIFY in {topic}? (Change size, shape, attributes)"),
            ("Put to other uses", f"How else could {topic} be used? (New contexts or users)"),
            ("Eliminate", f"What could you ELIMINATE from {topic}? (Remove complexity)"),
            ("Reverse", f"What if you REVERSED {topic}? (Do opposite, flip assumptions)"),
        ]

        ideas = []
        for i, (lens, prompt) in enumerate(scamper_prompts):
            # For testing or batch mode, use provided responses
            if user_responses and i < len(user_responses):
                response = user_responses[i]
            else:
                # In real session, would get response from conversation manager
                response = f"[User response to: {prompt}]"

            # Capture idea
            idea = Idea(content=f"{lens}: {response}", technique="SCAMPER Method")
            ideas.append(idea)

        self.logger.info("scamper_facilitation_complete", idea_count=len(ideas))
        return ideas

    async def facilitate_how_might_we(
        self, problem_statement: str, user_responses: Optional[List[str]] = None
    ) -> List[Idea]:
        """
        Facilitate "How Might We" framing.

        Reframes problems as opportunities using "How might we..." questions.

        Args:
            problem_statement: Problem to reframe
            user_responses: Optional list of user responses (for testing)

        Returns:
            List of HMW ideas
        """
        # Generate HMW framings using AI
        hmw_prompt = f"""
Generate 5 "How Might We..." questions to reframe this problem as opportunities:

Problem: {problem_statement}

Return only the questions, one per line, starting with "How might we...?"
"""

        try:
            result = await self.analysis_service.analyze(
                prompt=hmw_prompt, model="haiku", temperature=0.7, max_tokens=300
            )
            hmw_questions = [
                line.strip() for line in result.response.split("\n") if line.strip()
            ]
        except Exception as e:
            self.logger.error("hmw_generation_failed", error=str(e))
            # Fallback
            hmw_questions = [
                f"How might we solve {problem_statement}?",
                f"How might we approach {problem_statement} differently?",
                f"How might we eliminate {problem_statement}?",
            ]

        ideas = []
        for i, question in enumerate(hmw_questions[:5]):
            if user_responses and i < len(user_responses):
                response = user_responses[i]
            else:
                response = f"[User response to: {question}]"

            idea = Idea(content=f"{question} - {response}", technique="How Might We")
            ideas.append(idea)

        self.logger.info("hmw_facilitation_complete", idea_count=len(ideas))
        return ideas

    async def perform_affinity_mapping(
        self, ideas: List[Idea], num_themes: int = 5
    ) -> Dict[str, List[Idea]]:
        """
        Group ideas by theme using affinity mapping.

        Uses AI to cluster ideas into themes.

        Args:
            ideas: List of ideas to cluster
            num_themes: Target number of themes (3-7 typical)

        Returns:
            Dict mapping theme name -> list of ideas
        """
        if not ideas:
            return {}

        self.logger.info("affinity_mapping_started", idea_count=len(ideas), num_themes=num_themes)

        # Use AI to cluster ideas
        clustering_prompt = f"""
You have {len(ideas)} ideas to cluster into {num_themes} themes.

Ideas:
{chr(10).join(f"{i+1}. {idea.content}" for i, idea in enumerate(ideas))}

Cluster these ideas into {num_themes} coherent themes.
For each theme, provide:
- Theme name (2-4 words)
- Idea numbers that belong to that theme

Return as JSON:
{{
  "themes": [
    {{
      "name": "Theme Name",
      "idea_indices": [1, 3, 5]
    }}
  ]
}}
"""

        try:
            result = await self.analysis_service.analyze(
                prompt=clustering_prompt,
                model="sonnet",
                response_format="json",
                temperature=0.5,
                max_tokens=1000,
            )
            themes_data = json.loads(result.response)
        except Exception as e:
            self.logger.error("affinity_mapping_failed", error=str(e))
            # Fallback: single theme
            return {"General Ideas": ideas}

        # Build theme -> ideas mapping
        theme_groups: Dict[str, List[Idea]] = {}
        for theme in themes_data.get("themes", []):
            theme_name = theme["name"]
            theme_groups[theme_name] = []
            for idx in theme.get("idea_indices", []):
                if 0 <= idx - 1 < len(ideas):
                    idea = ideas[idx - 1]
                    idea.theme = theme_name
                    theme_groups[theme_name].append(idea)

        self.logger.info("affinity_mapping_complete", theme_count=len(theme_groups))
        return theme_groups

    async def generate_mind_map(self, ideas: List[Idea], central_topic: str) -> str:
        """
        Generate text-based mind map in mermaid syntax.

        Uses LLM to cluster ideas into themes and create hierarchy.

        Args:
            ideas: List of ideas to map
            central_topic: Central topic for the mind map

        Returns:
            Mermaid diagram code

        Raises:
            ValueError: If no ideas provided
        """
        if not ideas:
            raise ValueError("Cannot generate mind map with no ideas")

        self.logger.info("generating_mind_map", idea_count=len(ideas))

        # Use LLM to cluster ideas into themes
        clustering_prompt = f"""
You have {len(ideas)} ideas from brainstorming on "{central_topic}".

Ideas:
{chr(10).join(f"- {idea.content[:100]}" for idea in ideas)}

Cluster these ideas into 3-5 themes.
For each theme, list the relevant ideas (use exact idea text, truncated to 30 chars).

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

        try:
            result = await self.analysis_service.analyze(
                prompt=clustering_prompt,
                model="sonnet",
                response_format="json",
                temperature=0.5,
                max_tokens=1500,
            )
            themes = json.loads(result.response)["themes"]
        except Exception as e:
            self.logger.error("mind_map_clustering_failed", error=str(e))
            # Fallback: create single theme with all ideas
            themes = [{"name": "All Ideas", "ideas": [idea.content[:30] for idea in ideas[:10]]}]

        # Generate mermaid syntax
        mermaid = ["graph TD"]
        # Sanitize central topic for mermaid (remove special chars)
        central_safe = central_topic.replace('"', "'").replace("[", "(").replace("]", ")")
        mermaid.append(f'    A["{central_safe}"]')

        for i, theme in enumerate(themes[:5]):  # Limit to 5 themes
            theme_id = chr(66 + i)  # B, C, D, E, F
            theme_name = theme["name"].replace('"', "'").replace("[", "(").replace("]", ")")
            mermaid.append(f'    A --> {theme_id}["{theme_name}"]')

            for j, idea in enumerate(theme.get("ideas", [])[:5]):  # Limit 5 ideas per theme
                idea_id = f"{theme_id}{j+1}"
                # Truncate and sanitize
                idea_text = idea[:30] + ("..." if len(idea) > 30 else "")
                idea_text = idea_text.replace('"', "'").replace("[", "(").replace("]", ")")
                mermaid.append(f'    {theme_id} --> {idea_id}["{idea_text}"]')

        result = "\n".join(mermaid)
        self.logger.info("mind_map_generated", line_count=len(mermaid))
        return result

    async def synthesize_insights(
        self, ideas: List[Idea], techniques_used: List[str], topic: str
    ) -> Dict[str, Any]:
        """
        Synthesize session into insights.

        Returns:
            Dictionary with:
            - key_themes: Recurring themes across techniques
            - insights_learnings: Key realizations
            - quick_wins: Ideas that can be implemented quickly
            - long_term_opportunities: Ideas needing more development
            - recommended_followup: Suggested next techniques
        """
        if not ideas:
            return {
                "key_themes": [],
                "insights_learnings": [],
                "quick_wins": [],
                "long_term_opportunities": [],
                "recommended_followup": [],
            }

        self.logger.info("synthesizing_insights", idea_count=len(ideas))

        synthesis_prompt = f"""
Analyze this brainstorming session on "{topic}" and extract insights.

Techniques used: {', '.join(techniques_used)}
Ideas generated: {len(ideas)}

Ideas:
{chr(10).join(f"- {idea.content}" for idea in ideas[:50])}

Extract:
1. Key themes (2-5 recurring concepts)
2. Insights and learnings (2-4 key realizations)
3. Quick wins (2-5 ideas implementable in <1 month)
4. Long-term opportunities (2-5 ideas needing >3 months)
5. Recommended follow-up techniques (2-3 from BMAD library)

Return as JSON:
{{
  "key_themes": ["theme1", "theme2"],
  "insights_learnings": ["insight1", "insight2"],
  "quick_wins": ["idea1", "idea2"],
  "long_term_opportunities": ["idea3", "idea4"],
  "recommended_followup": ["technique1", "technique2"]
}}
"""

        try:
            result = await self.analysis_service.analyze(
                prompt=synthesis_prompt,
                model="sonnet",
                response_format="json",
                temperature=0.5,
                max_tokens=1500,
            )
            insights = json.loads(result.response)
            self.logger.info("insights_synthesized", theme_count=len(insights.get("key_themes", [])))
            return insights
        except Exception as e:
            self.logger.error("insights_synthesis_failed", error=str(e))
            # Fallback: minimal insights
            return {
                "key_themes": ["Innovation", "Problem Solving"],
                "insights_learnings": ["Multiple perspectives yield better solutions"],
                "quick_wins": [ideas[0].content if ideas else "No ideas"],
                "long_term_opportunities": [ideas[-1].content if len(ideas) > 1 else "No ideas"],
                "recommended_followup": ["Mind Mapping", "Five Whys"],
            }

    def get_technique(self, name: str) -> Optional[BrainstormingTechnique]:
        """
        Get technique by name.

        Args:
            name: Technique name (case-sensitive)

        Returns:
            BrainstormingTechnique or None if not found
        """
        return self.techniques.get(name)

    def list_techniques(self, category: Optional[str] = None) -> List[BrainstormingTechnique]:
        """
        List all techniques, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of techniques
        """
        if category:
            return [t for t in self.techniques.values() if t.category == category]
        return list(self.techniques.values())
