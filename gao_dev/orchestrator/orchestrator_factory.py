"""Factory for creating GAODevOrchestrator with default services.

Extracted from orchestrator.py to keep the facade lean (<300 LOC).
This factory handles all service initialization and dependency wiring.
"""

from pathlib import Path
from typing import Optional, AsyncGenerator
import os
import structlog

from .orchestrator import GAODevOrchestrator
from .workflow_execution_engine import WorkflowExecutionEngine
from .artifact_manager import ArtifactManager
from .agent_coordinator import AgentCoordinator
from .ceremony_orchestrator import CeremonyOrchestrator
from .brian_orchestrator import BrianOrchestrator
from ..core.config_loader import ConfigLoader
from ..core.workflow_registry import WorkflowRegistry
from ..core.workflow_executor import WorkflowExecutor
from ..core.prompt_loader import PromptLoader
from ..core.events.event_bus import EventBus
from ..core.services.workflow_coordinator import WorkflowCoordinator
from ..core.services.story_lifecycle import StoryLifecycleManager
from ..core.services.process_executor import ProcessExecutor
from ..core.services.quality_gate import QualityGateManager
from ..core.services.ai_analysis_service import AIAnalysisService
from ..core.services.git_integrated_state_manager import GitIntegratedStateManager
from ..lifecycle.project_lifecycle import ProjectDocumentLifecycle

logger = structlog.get_logger()


def create_orchestrator(
    project_root: Path,
    api_key: Optional[str] = None,
    mode: str = "cli",
) -> GAODevOrchestrator:
    """
    Create orchestrator with default service configuration.

    Factory function that sets up all services with standard dependencies.
    This is the recommended way to create an orchestrator instance.

    Args:
        project_root: Root directory of the project
        api_key: Optional Anthropic API key
        mode: Execution mode - "cli", "benchmark", or "api"

    Returns:
        Fully initialized GAODevOrchestrator instance with all services

    Example:
        >>> orchestrator = create_orchestrator(
        ...     project_root=Path("my-project"),
        ...     mode="benchmark"
        ... )
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    # Step 1: Initialize configuration infrastructure
    config_loader = ConfigLoader(project_root)
    workflow_registry = WorkflowRegistry(config_loader)
    workflow_registry.index_workflows()
    workflow_executor = WorkflowExecutor(config_loader)
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_loader = PromptLoader(
        prompts_dir=prompts_dir, config_loader=config_loader, cache_enabled=True
    )
    event_bus = EventBus()

    # Step 2: Initialize ProcessExecutor
    # Priority: 1) Environment variable, 2) Config file, 3) Default
    provider_name_from_env = os.getenv("AGENT_PROVIDER")
    if provider_name_from_env:
        provider_name = provider_name_from_env.lower()
        logger.info("using_provider_from_env", provider=provider_name)
    else:
        # Read from config file (gao-dev.yaml)
        provider_config_from_file = config_loader.get("providers", {})
        provider_name = provider_config_from_file.get("default", "claude-code").lower()
        logger.info("using_provider_from_config", provider=provider_name)

    # Get provider-specific config from config file
    provider_specific_config = {}
    if provider_name in config_loader.get("providers", {}):
        provider_specific_config = config_loader.get("providers", {}).get(provider_name, {})

    # Merge with API key if provided
    if api_key and "api_key" not in provider_specific_config:
        provider_specific_config["api_key"] = api_key

    process_executor = ProcessExecutor(
        project_root=project_root,
        provider_name=provider_name,
        provider_config=provider_specific_config if provider_specific_config else None,
    )

    # Step 3: Initialize document lifecycle
    doc_lifecycle = None
    try:
        doc_lifecycle = ProjectDocumentLifecycle.initialize(project_root)
    except Exception as e:
        logger.warning("document_lifecycle_init_failed", error=str(e))

    # Step 4: Initialize Epic 22 services (Stories 22.1-22.4)
    artifact_manager = ArtifactManager(
        project_root=project_root,
        document_lifecycle=doc_lifecycle,
        tracked_dirs=["docs", "src", "gao_dev"],
    )

    agent_coordinator = AgentCoordinator(
        process_executor=process_executor,
        project_root=project_root,
    )

    # Initialize database path for state management
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir(parents=True, exist_ok=True)
    db_path = gao_dev_dir / "documents.db"

    # Initialize GitIntegratedStateManager (Epic 27.1)
    git_state_manager = GitIntegratedStateManager(
        db_path=db_path,
        project_path=project_root,
        auto_commit=True
    )

    # Epic 28.4: Initialize ceremony components
    from ..core.services.ceremony_trigger_engine import CeremonyTriggerEngine
    from ..core.services.ceremony_failure_handler import CeremonyFailureHandler

    ceremony_trigger_engine = CeremonyTriggerEngine(db_path=db_path)
    ceremony_failure_handler = CeremonyFailureHandler()

    # Initialize CeremonyOrchestrator with git_state_manager (Epic 28.4: C3 fix)
    ceremony_orchestrator = CeremonyOrchestrator(
        config=config_loader,
        db_path=db_path,
        project_root=project_root,
        git_state_manager=git_state_manager  # Epic 28.4: For atomic transactions
    )

    # Create agent executor closure for workflow execution
    async def agent_executor(
        workflow_info, epic: int = 1, story: int = 1, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Execute workflow via ProcessExecutor with variable resolution.

        Accepts arbitrary keyword arguments which are merged into params
        for variable resolution (e.g., story_title, project_name, etc.).
        """
        params = {
            "epic": epic,
            "story": story,
            "epic_num": epic,
            "story_num": story,
            **kwargs  # Merge any additional parameters
        }
        variables = workflow_executor.resolve_variables(workflow_info, params)

        instructions_file = workflow_info.installed_path / "instructions.md"
        task = (
            instructions_file.read_text()
            if instructions_file.exists()
            else workflow_info.description
        )
        task = workflow_executor.render_template(task, variables)

        async for output in process_executor.execute_agent_task(
            task=task,
            tools=["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob", "TodoWrite"],
        ):
            yield output

    workflow_execution_engine = WorkflowExecutionEngine(
        workflow_registry=workflow_registry,
        workflow_executor=workflow_executor,
        prompt_loader=prompt_loader,
        agent_executor=agent_executor,
    )

    # Step 5: Initialize remaining services
    workflow_coordinator = WorkflowCoordinator(
        workflow_registry=workflow_registry,
        agent_factory=None,
        event_bus=event_bus,
        agent_executor=agent_executor,
        project_root=project_root,
        doc_manager=doc_lifecycle,
        workflow_executor=workflow_executor,
        max_retries=3,
        # Epic 28.4: Ceremony integration
        ceremony_trigger_engine=ceremony_trigger_engine,
        ceremony_orchestrator=ceremony_orchestrator,
        ceremony_failure_handler=ceremony_failure_handler,
        git_state_manager=git_state_manager,
        db_path=db_path,
    )

    story_lifecycle = StoryLifecycleManager(
        story_repository=None,
        event_bus=event_bus,
    )

    quality_gate_manager = QualityGateManager(
        project_root=project_root,
        event_bus=event_bus,
    )

    # Step 6: Initialize Brian orchestrator
    brian_model = os.getenv("GAO_DEV_MODEL")
    if not brian_model:
        brian_config_path = config_loader.get_agents_path() / "brian.agent.yaml"
        if brian_config_path.exists():
            import yaml

            try:
                with open(brian_config_path, encoding="utf-8") as f:
                    brian_config = yaml.safe_load(f)
                    brian_model = (
                        brian_config.get("agent", {}).get("configuration", {}).get("model")
                    )
            except Exception:
                pass

    try:
        analysis_service = AIAnalysisService(executor=process_executor, default_model=brian_model)
    except Exception as e:
        logger.warning("analysis_service_unavailable", error=str(e))
        analysis_service = None  # type: ignore

    brian_persona_path = config_loader.get_agents_path() / "brian.md"
    brian_orchestrator = BrianOrchestrator(
        workflow_registry=workflow_registry,
        analysis_service=analysis_service,
        brian_persona_path=brian_persona_path if brian_persona_path.exists() else None,
    )

    # Step 7: Create orchestrator with all services (including GitIntegratedStateManager)
    return GAODevOrchestrator(
        project_root=project_root,
        workflow_execution_engine=workflow_execution_engine,
        artifact_manager=artifact_manager,
        agent_coordinator=agent_coordinator,
        ceremony_orchestrator=ceremony_orchestrator,
        workflow_coordinator=workflow_coordinator,
        story_lifecycle=story_lifecycle,
        process_executor=process_executor,
        quality_gate_manager=quality_gate_manager,
        brian_orchestrator=brian_orchestrator,
        git_state_manager=git_state_manager,  # Epic 27.1
        api_key=api_key,
        mode=mode,
    )
