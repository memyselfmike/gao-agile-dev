# Epic 7.2: Workflow-Driven Core Architecture

**Status**: Ready
**Total Story Points**: 22 (enhanced from initial 15)
**Stories**: 6 (added Story 7.2.6)
**Priority**: Critical - Fundamental architectural refactor

**Enhancement Summary**: This epic was enhanced after deep analysis of BMAD workflows to include:
- Scale-adaptive workflow selection (Level 0-4)
- Brian agent as Workflow Orchestrator
- Multi-workflow sequence execution
- Complete workflow registry (55+ workflows)
- Terminology updates (bmm workflows → GAO-Dev workflows)

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

### Story 7.2.1: Create Brian Agent & Scale-Adaptive Workflow Selection (5 pts, was 3)
Create Brian (Workflow Orchestrator agent) with scale-adaptive workflow selection.

**Key Deliverables:**
- Brian agent definition file (`gao_dev/agents/brian.md`)
- `BrianOrchestrator` class with scale-adaptive logic
- Scale level assessment (Level 0-4) using AI
- Workflow sequence building based on scale
- Integration with workflow registry
- Clarifying questions for ambiguous prompts

**Enhancement**: +2 pts for Brian agent creation and scale-adaptive complexity assessment

### Story 7.2.2: Add Multi-Workflow Sequence Executor to Core (7 pts, was 5)
Implement multi-workflow sequence execution across phases.

**Key Deliverables:**
- `execute_workflow_sequence()` method in GAODevOrchestrator
- Multi-workflow execution (not just single workflows)
- Phase transition handling (Phase 1 → 2 → 3 → 4)
- JIT tech-spec generation during implementation
- State persistence across workflows
- Returns comprehensive multi-workflow results

**Enhancement**: +2 pts for multi-workflow sequencing and phase transitions

### Story 7.2.3: Refactor Benchmark for Scale-Adaptive Testing (4 pts, was 3)
Change benchmark system to support scale-adaptive testing.

**Key Deliverables:**
- BenchmarkRunner calls `gao_dev.execute_workflow_sequence(prompt)`
- Support scale level in benchmark config
- Test workflow sequences (not just single workflows)
- Metrics for multi-workflow execution
- Simplified benchmark config with optional scale_level

**Enhancement**: +1 pt for scale level support and workflow sequence testing

### Story 7.2.4: Add Clarification Dialog (2 pts, unchanged)
Allow GAO-Dev to ask clarifying questions when needed.

**Key Deliverables:**
- `ask_clarification()` method in GAODevOrchestrator
- Different behavior in CLI vs benchmark mode
- Benchmark mode uses sensible defaults
- CLI mode prompts user interactively

### Story 7.2.5: Integration Testing (2 pts, unchanged)
Test end-to-end workflow execution with scale-adaptive approach.

**Key Deliverables:**
- Integration tests for scale-adaptive workflow selection
- Test each scale level (0-4)
- End-to-end tests with workflow sequences
- Benchmark tests using new architecture
- Documentation of test results

### Story 7.2.6: Load Complete Workflow Registry (2 pts, NEW)
Load all 55+ workflows from GAO-Dev for Brian's selection.

**Key Deliverables:**
- Enhanced WorkflowRegistry with recursive loading
- Load all 55+ workflows across all phases
- Phase 1 (Analysis), Phase 2 (Planning), Phase 3 (Solutioning), Phase 4 (Implementation), Test Architecture, Helpers
- Workflow discovery APIs (list, get, search)
- Terminology updates (bmm workflows → GAO-Dev workflows)

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
