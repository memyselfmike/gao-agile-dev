"""Agent recommender for Adaptive Agile Methodology.

Recommends agents based on task type and workflow phase.

Story 5.2: Extracted from brian_orchestrator.py
"""

from typing import Dict, List, Optional, Any


class AgentRecommender:
    """Recommends Adaptive Agile agents for tasks.

    Maps tasks and phases to appropriate agent recommendations.
    Supports 7 specialized agents for different development phases.

    Agents:
        - Mary: Business Analyst (analysis, research)
        - John: Product Manager (planning, PRDs)
        - Winston: Technical Architect (architecture, design)
        - Sally: UX Designer (user experience, interfaces)
        - Bob: Scrum Master (story management, coordination)
        - Amelia: Software Developer (implementation, code)
        - Murat: Test Architect (testing, quality)

    Example:
        ```python
        from gao_dev.methodologies.adaptive_agile import AgentRecommender

        recommender = AgentRecommender()
        agents = recommender.recommend("create architecture", {"phase": "solutioning"})
        # Returns: ["Winston", "Sally"]
        ```
    """

    # Phase-based agent mapping
    PHASE_AGENTS = {
        "analysis": ["Mary"],
        "planning": ["John", "Bob"],
        "solutioning": ["Winston", "Sally"],
        "implementation": ["Bob", "Amelia", "Murat"],
        "testing": ["Murat", "Amelia"]
    }

    # Task keyword-based agent mapping
    TASK_KEYWORDS = {
        "research": ["Mary"],
        "analysis": ["Mary"],
        "analyze": ["Mary"],
        "brief": ["Mary", "John"],
        "prd": ["John", "Bob"],
        "plan": ["John", "Bob"],
        "planning": ["John", "Bob"],
        "epic": ["John", "Bob"],
        "story": ["Bob"],
        "stories": ["Bob"],
        "architecture": ["Winston"],
        "design": ["Winston", "Sally"],
        "database": ["Winston"],
        "api": ["Winston"],
        "tech": ["Winston"],
        "technical": ["Winston"],
        "ux": ["Sally"],
        "interface": ["Sally"],
        "ui": ["Sally"],
        "implement": ["Bob", "Amelia"],
        "code": ["Amelia"],
        "develop": ["Amelia"],
        "review": ["Bob", "Amelia"],
        "test": ["Murat"],
        "testing": ["Murat"],
        "qa": ["Murat"],
        "quality": ["Murat"],
    }

    def recommend(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents for a task.

        Args:
            task: Task description or workflow name
            context: Optional context dictionary containing:
                - phase: Current workflow phase
                - workflow: Current workflow name
                - scale_level: Scale level (0-4)

        Returns:
            List of recommended agent names

        Example:
            ```python
            # Phase-based recommendation
            agents = recommender.recommend(
                "any task",
                context={"phase": "planning"}
            )
            # Returns: ["John", "Bob"]

            # Keyword-based recommendation
            agents = recommender.recommend("implement feature")
            # Returns: ["Bob", "Amelia"]
            ```
        """
        context = context or {}

        # Strategy 1: Check if phase specified in context
        phase = context.get("phase", "").lower()
        if phase and phase in self.PHASE_AGENTS:
            return self.PHASE_AGENTS[phase].copy()

        # Strategy 2: Check task keywords
        task_lower = task.lower()
        for keyword, agents in self.TASK_KEYWORDS.items():
            if keyword in task_lower:
                return agents.copy()

        # Strategy 3: Default to developer for unknown tasks
        return ["Amelia"]

    def get_all_agents(self) -> List[str]:
        """Get list of all available agents.

        Returns:
            List of all agent names in methodology
        """
        return ["Mary", "John", "Winston", "Sally", "Bob", "Amelia", "Murat"]

    def get_agents_for_phase(self, phase: str) -> List[str]:
        """Get recommended agents for a specific phase.

        Args:
            phase: Workflow phase name

        Returns:
            List of agent names for phase

        Raises:
            KeyError: If phase not recognized
        """
        phase_lower = phase.lower()
        if phase_lower not in self.PHASE_AGENTS:
            raise KeyError(
                f"Unknown phase '{phase}'. "
                f"Valid phases: {list(self.PHASE_AGENTS.keys())}"
            )
        return self.PHASE_AGENTS[phase_lower].copy()

    def get_primary_agent_for_workflow(self, workflow_name: str) -> str:
        """Get primary agent for a workflow.

        Determines the lead agent responsible for a workflow based on
        its name and typical responsibilities.

        Args:
            workflow_name: Name of workflow

        Returns:
            Primary agent name

        Example:
            ```python
            agent = recommender.get_primary_agent_for_workflow("create-prd")
            # Returns: "John"
            ```
        """
        workflow_lower = workflow_name.lower()

        # Match workflow patterns to primary agents
        if "research" in workflow_lower or "brief" in workflow_lower:
            return "Mary"
        elif "prd" in workflow_lower or "epic" in workflow_lower:
            return "John"
        elif "story" in workflow_lower or "stories" in workflow_lower:
            return "Bob"
        elif "architecture" in workflow_lower or "design" in workflow_lower:
            return "Winston"
        elif "implement" in workflow_lower or "code" in workflow_lower:
            return "Amelia"
        elif "test" in workflow_lower or "qa" in workflow_lower:
            return "Murat"
        else:
            # Default to Bob (Scrum Master) for coordination
            return "Bob"
