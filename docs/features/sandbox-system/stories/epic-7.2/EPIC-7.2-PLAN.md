# Epic 7.2: Workflow-Driven Core Architecture

**Status**: Ready
**Total Story Points**: 15
**Stories**: 5
**Priority**: Critical - Fundamental architectural refactor

---

## Epic Goal

Transform GAO-Dev from a passive system (orchestrated by benchmark) to an **autonomous workflow-driven system** that intelligently selects and executes BMAD workflows based on user prompts.

---

## The Problem

**Current (Wrong) Architecture:**
```
User/Benchmark → Defines Workflow → GAO-Dev Executes → Results
```

The benchmark system currently:
- Defines HOW GAO-Dev should work (phases, agent sequence)
- Orchestrates workflow execution
- Treats GAO-Dev as a collection of agent-spawning methods

**What's Wrong:**
1. GAO-Dev is passive, not autonomous
2. Workflow intelligence lives in benchmark, not core
3. BMAD workflows exist in `bmad/bmm/workflows/` but aren't used
4. No intelligent workflow selection
5. Violates separation of concerns

---

## The Solution

**Correct (New) Architecture:**
```
User Prompt → GAO-Dev Analyzes → Selects Workflow → Executes → Benchmark Observes
```

GAO-Dev should:
- **Analyze** initial prompt to understand user intent
- **Select** appropriate workflow from BMAD registry
- **Execute** workflow autonomously, calling agents as needed
- **Ask** clarifying questions if context is missing
- **Create** artifacts and manage git commits
- **Return** results to caller

Benchmark should:
- **Provide** initial prompt only
- **Observe** GAO-Dev execution
- **Collect** metrics (time, cost, quality)
- **NOT** define workflows or orchestrate execution

---

## Correct Component Responsibilities

### GAO-Dev Core (`gao_dev/core/`)
- ✅ Workflow Registry - Load workflows from `bmad/bmm/workflows/`
- ✅ Workflow Selector - AI-powered workflow selection
- ✅ Workflow Executor - Execute workflow steps
- ✅ State Manager - Track workflow progress
- ✅ Agent Orchestrator - Coordinate agents

### GAO-Dev Orchestrator (`gao_dev/orchestrator/`)
- ✅ High-level workflow execution
- ✅ Agent delegation based on workflow steps
- ✅ Artifact management
- ✅ Progress tracking

### Benchmark System (`gao_dev/sandbox/`)
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
   - Mary, John, Winston, Sally, Bob, Amelia, Murat
   - All defined and ready

### Missing Components

1. **Workflow Selector** - AI analyzes prompt, selects workflow
2. **Workflow Executor** - Executes workflow steps, calls agents
3. **Intelligent Orchestration** - GAO-Dev decides HOW to work
4. **Clarification Dialog** - Asks user for missing context
5. **State Management** - Tracks progress through workflow

---

## Epic Stories

### Story 7.2.1: Create Workflow Selector (3 pts)
Add AI-powered workflow selection to GAODevOrchestrator.

**Key Deliverables:**
- `WorkflowSelector` class with AI-powered analysis
- Analyzes initial prompt to determine project type and required workflow
- Returns selected workflow or list of clarifying questions
- Integration with workflow registry

### Story 7.2.2: Add Workflow Executor to Core (5 pts)
Implement workflow execution in GAODevOrchestrator.

**Key Deliverables:**
- `execute_workflow(initial_prompt)` method in GAODevOrchestrator
- Executes workflow steps sequentially
- Calls appropriate agents based on workflow definition
- Manages state, creates artifacts, commits to git
- Returns WorkflowResult with metrics

### Story 7.2.3: Refactor Benchmark to Use Core Workflows (3 pts)
Change benchmark system to be a passive test harness.

**Key Deliverables:**
- BenchmarkRunner calls `gao_dev.execute_workflow(prompt)`
- Remove workflow orchestration from benchmark
- Keep only metrics collection and performance measurement
- Simplified benchmark config (just initial_prompt and success_criteria)

### Story 7.2.4: Add Clarification Dialog (2 pts)
Allow GAO-Dev to ask clarifying questions when needed.

**Key Deliverables:**
- `ask_clarification()` method in GAODevOrchestrator
- Different behavior in CLI vs benchmark mode
- Benchmark mode uses sensible defaults
- CLI mode prompts user interactively

### Story 7.2.5: Integration Testing (2 pts)
Test end-to-end workflow execution.

**Key Deliverables:**
- Integration tests for workflow selection
- End-to-end tests with multiple workflow types
- Benchmark tests using new architecture
- Documentation of test results

---

## Migration Path

### Phase 1: Core Workflow System (Stories 7.2.1-7.2.2)
1. Add WorkflowSelector to GAODevOrchestrator
2. Implement execute_workflow() method
3. Test with existing workflows

### Phase 2: Refactor Benchmark (Story 7.2.3)
1. Simplify benchmark to call GAO-Dev core
2. Remove workflow orchestration from benchmark
3. Keep metrics collection

### Phase 3: Add Intelligence (Stories 7.2.4-7.2.5)
1. Add clarification dialog
2. Test end-to-end
3. Document new architecture

---

## Benefits of This Architecture

1. **True Autonomy**: GAO-Dev decides HOW to work, not told by benchmark
2. **Reusability**: CLI can use same workflow system as benchmarks
3. **Intelligence**: AI-powered workflow selection based on prompt analysis
4. **Extensibility**: Easy to add new workflows to `bmad/bmm/workflows/`
5. **BMAD Compliance**: Uses workflows from BMAD Method
6. **Separation of Concerns**: Benchmark tests, GAO-Dev orchestrates

---

## Success Criteria

Epic 7.2 is complete when:

- ✅ GAO-Dev can take an initial prompt and autonomously select a workflow
- ✅ GAO-Dev executes BMAD workflows from `bmad/bmm/workflows/`
- ✅ Benchmark is a passive test harness (no workflow orchestration)
- ✅ Workflow selection is intelligent (AI-powered)
- ✅ GAO-Dev can ask clarifying questions when needed
- ✅ End-to-end tests pass for multiple workflow types
- ✅ Documentation updated to reflect new architecture

---

## Technical Debt Addressed

This epic fixes the fundamental architectural flaw identified in `docs/ARCHITECTURE-ISSUE-WORKFLOWS.md`:
- Workflows now defined in GAO-Dev core, not benchmark
- GAO-Dev is truly autonomous and workflow-driven
- Benchmark is passive observer, not orchestrator
- BMAD workflows are used as intended

---

## Dependencies

- **Epic 7**: Autonomous Artifact Creation (COMPLETE)
- **Epic 7.1**: Integration & Architecture Fix (COMPLETE)
- **BMAD Workflows**: Must exist in `bmad/bmm/workflows/` (EXIST)
- **Workflow Registry**: Must be functional (EXISTS)

---

## Risks and Mitigation

**Risk 1**: Breaking existing benchmarks during refactor
**Mitigation**: Keep backward compatibility layer during transition

**Risk 2**: Workflow selection may not always choose correctly
**Mitigation**: Allow manual workflow override, log selection reasoning

**Risk 3**: Complex workflows may timeout
**Mitigation**: Add workflow timeout configuration, progress checkpoints

---

## Related Documentation

- `docs/ARCHITECTURE-ISSUE-WORKFLOWS.md` - Problem analysis and proposed solution
- `docs/EPIC-7-INTEGRATION-ISSUES.md` - Integration bugs that led to this discovery
- `bmad/bmm/workflows/README.md` - BMAD workflow documentation
- `gao_dev/core/workflow_registry.py` - Existing workflow registry
- `gao_dev/orchestrator/orchestrator.py` - Core orchestrator to be enhanced
