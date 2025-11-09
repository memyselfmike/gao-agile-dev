# Brian Architecture Analysis
**Date**: 2025-11-07
**Purpose**: Determine if Brian is an agent or orchestration, and plan provider abstraction

---

## Current State Analysis

### Brian's Role & Responsibilities

**What Brian Does:**
1. **Prompt Analysis** (`_analyze_prompt` method)
   - Analyzes user requests using AI
   - Determines scale level (0-4)
   - Assesses project type (greenfield, brownfield, game)
   - Evaluates technical and domain complexity
   - Identifies if clarification is needed

2. **Workflow Selection** (`_build_workflow_sequence` method)
   - Selects appropriate workflow sequences based on scale
   - Routes based on project type and context
   - Builds structured workflow plans
   - Returns WorkflowSequence with rationale

3. **Strategic Coordination**
   - Acts as "Engineering Manager" deciding HOW to build
   - Coordinates other agents (John, Winston, Bob, Amelia)
   - Makes meta-level decisions about process

### How Brian Uses AI

**Current Implementation** (line 206-210):
```python
response = self.anthropic.messages.create(
    model=self.model,
    max_tokens=2048,
    messages=[{"role": "user", "content": analysis_prompt}]
)
```

**AI Usage Pattern:**
- Single AI call per prompt analysis
- Sends prompt → Receives JSON response
- Parses into `PromptAnalysis` dataclass
- No iteration, no tools, no artifact creation

### Key Statistics

- **File Size**: 524 lines
- **AI Calls**: 1 per analysis
- **Dependencies**: `anthropic` package (direct)
- **Artifacts Created**: None (returns data structures)
- **Tools Used**: None (no Read, Write, Bash, etc.)

---

## Classification: Agent vs Orchestration?

### Agent Traits (❌ Missing)
- ❌ Creates artifacts (files, code, documents)
- ❌ Uses tools (Read, Write, Edit, Bash, etc.)
- ❌ Interacts with project files
- ❌ Produces work products
- ❌ Iterates on tasks

### Agent Traits (✅ Present)
- ✅ Uses AI for decision-making
- ✅ Has persona
- ✅ Configurable model
- ✅ Uses prompt templates

### Orchestration Traits (✅ Present)
- ✅ Coordinates other agents
- ✅ Makes strategic decisions
- ✅ Returns metadata/instructions
- ✅ No artifact creation
- ✅ Single-shot analysis (no iteration)

### Conclusion: **Analysis Orchestrator**

Brian is **NOT a traditional agent**. Brian is an **AI-powered orchestration component** that:
- Uses AI for intelligent analysis
- Makes strategic decisions about workflows
- Coordinates actual agents (John, Winston, Bob, Amelia)
- Returns structured decisions, not artifacts

**Analogy**: Brian is like a project manager who uses AI to assess projects and assign teams, but doesn't write code themselves.

---

## Problem Statement

**Current Architecture Issue:**
- Brian uses `Anthropic` client directly
- Hardcoded dependency bypasses provider abstraction
- Cannot use:
  - Local models (Ollama + deepseek-r1)
  - OpenCode provider
  - Alternative AI providers
  - Testing mocks

**Impact:**
- Inconsistent with other agents (which use ProcessExecutor)
- Limits model flexibility and testing
- Blocks local model usage for cost savings
- Violates dependency inversion principle

---

## Solution Options

### Option A: Make Brian a True IAgent
**Approach**: Refactor Brian to implement IAgent interface, use ProcessExecutor

**Pros:**
- Consistent architecture with other agents
- Automatic provider abstraction
- Can use all providers

**Cons:**
- Brian doesn't need agent tools (Read, Write, etc.)
- Overengineering - IAgent interface designed for artifact-creating agents
- Awkward fit for analysis-only use case

**Verdict**: ❌ **Not Recommended** - Wrong abstraction

---

### Option B: Create AI Analysis Service
**Approach**: Build reusable `AIAnalysisService` that provides provider-abstracted AI calls

**Architecture:**
```
BrianOrchestrator
    ↓ uses
AIAnalysisService (new)
    ↓ uses
ProcessExecutor
    ↓ uses
Provider Abstraction (OpenCode, Claude Code, etc.)
```

**Pros:**
- Proper abstraction for analysis-only AI calls
- Reusable for future analysis needs (cost estimation, code review summaries, etc.)
- Brian stays as orchestration (not forced into IAgent)
- Provider-agnostic
- Easy to test

**Cons:**
- New service to maintain
- Slightly more complex architecture

**Verdict**: ✅ **RECOMMENDED** - Best long-term solution

---

### Option C: Inject ProcessExecutor into Brian
**Approach**: Give Brian access to ProcessExecutor, use it only for AI calls

**Pros:**
- Minimal code changes
- Provider abstraction achieved
- Quick implementation

**Cons:**
- ProcessExecutor designed for full agent workflows (with tools)
- Misuse of abstraction (using executor without tools)
- Less reusable

**Verdict**: ⚠️ **Acceptable Short-term** - Quick fix but not ideal

---

## Recommended Solution: Option B

### Create AIAnalysisService

**Purpose**: Provide provider-abstracted AI calls for analysis tasks

**Interface:**
```python
class AIAnalysisService:
    async def analyze(
        self,
        prompt: str,
        model: str,
        response_format: str = "json",
        max_tokens: int = 2048
    ) -> str:
        """
        Send prompt to AI provider, get response.

        Provider-agnostic - uses ProcessExecutor internally.
        """
```

**Benefits:**
1. **Reusability**: Can be used by Brian, cost estimators, code reviewers, etc.
2. **Provider Flexibility**: Works with any provider (Claude, OpenCode, local models)
3. **Testing**: Easy to mock for tests
4. **Separation of Concerns**: Brian focuses on workflow logic, service handles AI calls

---

## Migration Plan

### Phase 1: Create AIAnalysisService
- Design interface
- Implement using ProcessExecutor
- Add tests

### Phase 2: Refactor Brian
- Replace `self.anthropic.messages.create()` with `analysis_service.analyze()`
- Remove `anthropic` dependency from BrianOrchestrator
- Update initialization to inject AIAnalysisService

### Phase 3: Test & Validate
- Unit tests with mocked service
- Integration tests with real providers
- Benchmark with local models (deepseek-r1)

---

## Next Steps

1. Create PRD for "AI Analysis Service & Brian Provider Abstraction"
2. Define Epic and Stories
3. Implement using proven BMAD workflow
4. Validate with deepseek-r1 benchmark

---

## Success Criteria

✅ Brian can use any AI provider (not just Anthropic)
✅ Works with local models (Ollama + deepseek-r1)
✅ No direct dependency on `anthropic` package
✅ Reusable service for future analysis needs
✅ Maintains existing Brian functionality
✅ All tests passing
