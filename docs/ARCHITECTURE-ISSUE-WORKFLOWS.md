# Critical Architecture Issue: Workflow Location & Responsibility

**Date**: 2025-10-28
**Severity**: Critical - Fundamental design flaw
**Status**: Identified, needs Epic 7.2 to fix

---

## The Problem

**Current (Wrong) Implementation:**
Workflows are defined and orchestrated by the **sandbox/benchmark system**, treating GAO-Dev as just a collection of agent-spawning methods.

```
sandbox/benchmark/
├── runner.py              # Defines workflow execution
├── orchestrator.py        # Orchestrates phases
└── config.py              # Workflow configuration

gao_dev/orchestrator/
└── orchestrator.py        # Just spawns agents (create_prd, implement_story)
```

**What's Wrong:**
1. Benchmark system is defining HOW to work (phases, workflows)
2. GAO-Dev is passive - just called by benchmark
3. BMAD workflows exist in `bmad/bmm/workflows/` but aren't used by core
4. No intelligence in workflow selection
5. Violates separation of concerns

---

## The Correct Architecture (BMAD Method)

**Core Principle**: GAO-Dev should be **workflow-driven** with **intelligent workflow selection**.

### How It Should Work

```
User → GAO-Dev Core
         ↓
    1. Analyze Initial Prompt
         ↓
    2. Select Appropriate Workflow
       (or ask clarifying questions)
         ↓
    3. Execute Workflow
       ├─→ Call agents (Mary, John, Winston, etc.)
       ├─→ Manage state/progress
       └─→ Create artifacts
         ↓
    4. Return Results

Benchmark System (Passive Observer)
├─→ Provides initial prompt
├─→ Measures GAO-Dev performance
└─→ Collects metrics
```

### Correct Component Responsibilities

**GAO-Dev Core** (`gao_dev/core/`)
- ✅ Workflow Registry - Load workflows from `bmad/bmm/workflows/`
- ✅ Workflow Selector - AI-powered workflow selection
- ✅ Workflow Executor - Execute workflow steps
- ✅ State Manager - Track workflow progress
- ✅ Agent Orchestrator - Coordinate agents

**GAO-Dev Orchestrator** (`gao_dev/orchestrator/`)
- ✅ High-level workflow execution
- ✅ Agent delegation based on workflow steps
- ✅ Artifact management
- ✅ Progress tracking

**Benchmark System** (`gao_dev/sandbox/`)
- ✅ Test harness ONLY
- ✅ Provide initial prompt
- ✅ Measure performance (time, cost, quality)
- ✅ Collect metrics
- ❌ Does NOT define workflows
- ❌ Does NOT orchestrate execution

---

## What Exists vs What's Missing

### Already Built (But Not Used Correctly)

1. **BMAD Workflows** (`bmad/bmm/workflows/`)
   - `1-analysis/` - Research workflows
   - `2-plan-workflows/prd/` - PRD creation workflow
   - `3-solutioning/` - Architecture workflows
   - `4-implementation/create-story/` - Story creation workflow
   - `4-implementation/dev-story/` - Development workflow

2. **Workflow Registry** (`gao_dev/core/workflow_registry.py`)
   - Can load workflows from disk
   - Parses workflow YAML/MD files

3. **Agents** (`gao_dev/agents/`)
   - Mary (Business Analyst)
   - John (Product Manager)
   - Winston (Architect)
   - Sally (UX Designer)
   - Bob (Scrum Master)
   - Amelia (Developer)
   - Murat (Test Architect)

### Missing Components

1. **Workflow Selector** - AI analyzes prompt, selects workflow
2. **Workflow Executor** - Executes workflow steps, calls agents
3. **Intelligent Orchestration** - GAO-Dev decides HOW to work
4. **Clarification Dialog** - Asks user for missing context
5. **State Management** - Tracks progress through workflow

---

## Proposed Solution: Epic 7.2

### Epic 7.2: Workflow-Driven Core Architecture

**Goal**: Make GAO-Dev truly workflow-driven with intelligent workflow selection.

#### Story 7.2.1: Create Workflow Selector (3 pts)
Add AI-powered workflow selection to GAODevOrchestrator.

**Implementation:**
```python
# gao_dev/orchestrator/workflow_selector.py

class WorkflowSelector:
    """Select appropriate workflow based on initial prompt."""

    async def select_workflow(
        self,
        initial_prompt: str,
        available_workflows: List[Workflow]
    ) -> Workflow:
        """
        Analyze prompt and select best workflow.

        Uses AI to:
        1. Understand user intent
        2. Identify project type (greenfield, enhancement, bug fix)
        3. Determine required workflow
        4. Ask clarifying questions if needed
        """
        # Use Task tool to analyze prompt
        analysis_task = f'''
        Analyze this user request and determine the appropriate workflow:

        User Request: {initial_prompt}

        Available Workflows:
        {self._format_workflows(available_workflows)}

        Determine:
        1. Project type (greenfield, enhancement, maintenance)
        2. Required phases (analysis, planning, architecture, implementation)
        3. Appropriate workflow
        4. Any clarifying questions needed
        '''

        # Get AI analysis
        # Return selected workflow or ask questions
```

#### Story 7.2.2: Add Workflow Executor to Core (5 pts)
Implement workflow execution in GAODevOrchestrator.

**Implementation:**
```python
# gao_dev/orchestrator/orchestrator.py

class GAODevOrchestrator:

    async def execute_workflow(
        self,
        initial_prompt: str,
        workflow: Optional[Workflow] = None
    ) -> WorkflowResult:
        """
        Execute complete workflow from initial prompt.

        Flow:
        1. Select workflow (if not provided)
        2. For each workflow step:
           a. Call appropriate agent
           b. Collect artifacts
           c. Update state
           d. Commit to git
        3. Return results
        """
        # Select workflow if not provided
        if not workflow:
            workflow = await self.selector.select_workflow(
                initial_prompt,
                self.workflow_registry.list_workflows()
            )

        # Execute workflow steps
        result = WorkflowResult(workflow_name=workflow.name)

        for step in workflow.steps:
            step_result = await self._execute_step(step)
            result.steps.append(step_result)

            if step_result.failed:
                break

        return result
```

#### Story 7.2.3: Refactor Benchmark to Use Core Workflows (3 pts)
Change benchmark system to be a passive test harness.

**Changes:**
```python
# gao_dev/sandbox/benchmark/runner.py

class BenchmarkRunner:

    def run_benchmark(self, config: BenchmarkConfig):
        """Run benchmark by calling GAO-Dev core, not orchestrating directly."""

        # Initialize GAO-Dev
        gao_dev = GAODevOrchestrator(project_root=self.project_path)

        # Start timer
        start_time = time.time()

        # Let GAO-Dev decide and execute workflow
        result = asyncio.run(
            gao_dev.execute_workflow(initial_prompt=config.initial_prompt)
        )

        # Collect metrics
        duration = time.time() - start_time
        metrics = self._collect_metrics(result, duration)

        return BenchmarkResult(
            success=result.success,
            duration=duration,
            metrics=metrics
        )
```

#### Story 7.2.4: Add Clarification Dialog (2 pts)
Allow GAO-Dev to ask clarifying questions.

**Implementation:**
```python
class GAODevOrchestrator:

    async def ask_clarification(
        self,
        questions: List[str]
    ) -> Dict[str, str]:
        """
        Ask user for clarification.

        In benchmark mode: Use defaults or fail
        In CLI mode: Prompt user interactively
        """
        if self.mode == "benchmark":
            # Use sensible defaults
            return self._get_default_answers(questions)
        else:
            # Ask user
            return await self._prompt_user(questions)
```

#### Story 7.2.5: Integration Testing (2 pts)
Test end-to-end workflow execution.

---

## Migration Path

### Phase 1: Core Workflow System (Epic 7.2 Stories 1-2)
1. Add WorkflowSelector to GAODevOrchestrator
2. Implement execute_workflow() method
3. Test with existing workflows

### Phase 2: Refactor Benchmark (Story 7.2.3)
1. Simplify benchmark to call GAO-Dev core
2. Remove workflow orchestration from benchmark
3. Keep metrics collection

### Phase 3: Add Intelligence (Stories 7.2.4-5)
1. Add clarification dialog
2. Test end-to-end
3. Document new architecture

---

## Benefits of This Architecture

1. **True Autonomy**: GAO-Dev decides HOW to work, not told by benchmark
2. **Reusability**: CLI can use same workflow system
3. **Intelligence**: AI-powered workflow selection
4. **Extensibility**: Easy to add new workflows
5. **BMAD Compliance**: Uses workflows from `bmad/bmm/workflows/`
6. **Separation of Concerns**: Benchmark just tests, doesn't orchestrate

---

## Current State Summary

**What Works:**
- ✅ BMAD workflows defined in `bmad/bmm/workflows/`
- ✅ Workflow registry can load workflows
- ✅ Agents defined and ready
- ✅ Epic 7.1 fixes applied (integration working)

**What's Wrong:**
- ❌ Workflows orchestrated by benchmark, not core
- ❌ No intelligent workflow selection
- ❌ GAO-Dev is passive, not autonomous
- ❌ Benchmark defines HOW to work (wrong!)

**What We Need:**
- Epic 7.2: Workflow-Driven Core Architecture (15 pts, 5 stories)
- Refactor to make GAO-Dev truly autonomous and workflow-driven

---

## Next Steps

1. Create Epic 7.2 stories in `docs/features/sandbox-system/stories/epic-7.2/`
2. Update sprint-status.yaml
3. Implement Epic 7.2 to fix architecture
4. Then benchmarks will work as intended

**Priority**: High - This is fundamental to GAO-Dev's design
