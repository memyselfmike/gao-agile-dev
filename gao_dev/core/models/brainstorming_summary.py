"""Brainstorming session data models.

This module defines data structures for capturing brainstorming results
including ideas, techniques, and comprehensive session summaries.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.2 - Brainstorming & Mind Mapping
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path


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
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BrainstormingSummary:
    """Brainstorming session output."""

    topic: str
    techniques_used: List[str]
    ideas_generated: List[Idea]
    mind_maps: List[str] = field(default_factory=list)  # Mermaid syntax
    key_themes: List[str] = field(default_factory=list)
    insights_learnings: List[str] = field(default_factory=list)
    quick_wins: List[Idea] = field(default_factory=list)
    long_term_opportunities: List[Idea] = field(default_factory=list)
    recommended_followup: List[str] = field(default_factory=list)
    session_duration: Optional[timedelta] = None
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[Path] = None

    def to_markdown(self) -> str:
        """
        Generate complete markdown report.

        Returns:
            Formatted markdown string with all session details
        """
        sections = []

        # Header
        sections.append(f"# Brainstorming Session: {self.topic}\n")
        sections.append(f"**Date**: {self.created_at.strftime('%Y-%m-%d %H:%M')}")

        if self.session_duration:
            total_seconds = self.session_duration.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            sections.append(f"**Duration**: {minutes} minutes {seconds} seconds")
        else:
            sections.append("**Duration**: N/A")

        sections.append(f"**Techniques Used**: {', '.join(self.techniques_used)}")
        sections.append(f"**Ideas Generated**: {len(self.ideas_generated)}\n")
        sections.append("---\n")

        # Key Themes
        sections.append("## Key Themes\n")
        if self.key_themes:
            for theme in self.key_themes:
                sections.append(f"- {theme}")
        else:
            sections.append("*No themes identified*")
        sections.append("")

        # All Ideas
        sections.append("## Ideas Generated\n")
        if self.ideas_generated:
            # Group by technique
            techniques_dict = {}
            for idea in self.ideas_generated:
                if idea.technique not in techniques_dict:
                    techniques_dict[idea.technique] = []
                techniques_dict[idea.technique].append(idea)

            for technique, ideas in techniques_dict.items():
                sections.append(f"### {technique}\n")
                for idea in ideas:
                    sections.append(f"- {idea.content}")
                sections.append("")
        else:
            sections.append("*No ideas generated*\n")

        # Quick Wins
        sections.append("## Quick Wins (Implement in <1 month)\n")
        if self.quick_wins:
            for idea in self.quick_wins:
                sections.append(f"- {idea.content}")
        else:
            sections.append("*No quick wins identified*")
        sections.append("")

        # Long-term
        sections.append("## Long-term Opportunities (>3 months)\n")
        if self.long_term_opportunities:
            for idea in self.long_term_opportunities:
                sections.append(f"- {idea.content}")
        else:
            sections.append("*No long-term opportunities identified*")
        sections.append("")

        # Insights
        sections.append("## Insights & Learnings\n")
        if self.insights_learnings:
            for insight in self.insights_learnings:
                sections.append(f"- {insight}")
        else:
            sections.append("*No insights identified*")
        sections.append("")

        # Mind Maps
        if self.mind_maps:
            sections.append("## Mind Maps\n")
            for i, mindmap in enumerate(self.mind_maps, 1):
                sections.append(f"### Map {i}\n")
                sections.append("```mermaid")
                sections.append(mindmap)
                sections.append("```\n")

        # Recommended Follow-up
        sections.append("## Recommended Follow-up Techniques\n")
        if self.recommended_followup:
            for technique in self.recommended_followup:
                sections.append(f"- {technique}")
        else:
            sections.append("*No follow-up techniques recommended*")

        sections.append("\n---")
        sections.append("\n**Generated by**: Mary (Business Analyst)")
        if self.file_path:
            sections.append(f"**File**: {self.file_path.name}")

        return "\n".join(sections)
