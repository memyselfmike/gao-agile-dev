---
document:
  type: "prd"
  state: "draft"
  created: "2025-11-07"
  last_modified: "2025-11-07"
  author: "John"
  feature: "ai-analysis-service"
  epic: null
  story: null
  related_documents:
    - "../../analysis/brian-architecture-analysis.md"
  replaces: null
  replaced_by: null
---

# Product Requirements Document
## GAO-Dev AI Analysis Service & Brian Provider Abstraction

**Version:** 1.0.0
**Date:** 2025-11-07
**Status:** Draft
**Author:** Product Strategy (via architecture analysis)

---

## Executive Summary

### Vision
Enable GAO-Dev's orchestration components to use any AI provider (Claude, OpenCode, local models) for analysis tasks by introducing a reusable AI Analysis Service. This will allow Brian and future analysis components to work with local models like deepseek-r1, reducing costs and enabling offline development.

### Goals
1. **Provider Independence**: Remove Brian's direct dependency on Anthropic client
2. **Local Model Support**: Enable use of Ollama + deepseek-r1 and other local models
3. **Reusable Service**: Create service usable by any component needing AI analysis
4. **Cost Reduction**: Enable use of free local models for development and testing
5. **Preserve Functionality**: Maintain all existing Brian capabilities

---

## Problem Statement

### Current State

**Pain Points:**

**Brian's Hardcoded Provider Dependency:**
- Brian uses `self.anthropic.messages.create()` directly (line 206-210 in `brian_orchestrator.py`)
- Bypasses GAO-Dev's provider abstraction layer entirely
- Cannot use:
  - Local models (Ollama + deepseek-r1)
  - OpenCode provider
  - Alternative AI providers
  - Testing mocks
- Blocks cost-saving opportunities (local model usage)

**Code Evidence:**
```python
# gao_dev/orchestrator/brian_orchestrator.py:206-210
response = self.anthropic.messages.create(
    model=self.model,  # Goes to Anthropic API only
    max_tokens=2048,
    messages=[{"role": "user", "content": analysis_prompt}]
)
```

**Architectural Inconsistency:**
- All agents (John, Winston, Bob, Amelia, etc.) use ProcessExecutor with provider abstraction
- Brian (orchestrator) uses Anthropic client directly
- Violates Dependency Inversion Principle
- Impossible to test Brian without Anthropic API calls

**Impact:**
- Cannot benchmark with local models (original user request)
- Development requires paid API calls
- Testing requires live API access
- Inconsistent architecture across codebase
- Future analysis components will have same problem

### Target State

**Desired End State:**

**Provider-Abstracted Analysis:**
- Brian uses AIAnalysisService (new service layer)
- AIAnalysisService uses ProcessExecutor internally
- Works with any provider: Claude Code, OpenCode, Anthropic, local Ollama
- Testable with mocks
- Reusable for future analysis needs

**Architecture:**
```
BrianOrchestrator
    |
    v uses
AIAnalysisService (NEW)
    |
    v uses
ProcessExecutor
    |
    v uses
Provider Abstraction (OpenCode, Claude Code, etc.)
    |
    v
Local Models (Ollama + deepseek-r1) OR Cloud APIs (Anthropic)
```

**Benefits:**
- Brian works with any AI provider
- Can use free local models for development
- Consistent architecture (all components use provider abstraction)
- Easy to test (mock AIAnalysisService)
- Reusable for future analysis needs (cost estimation, code review summaries, etc.)

---

## Features

### Core Features

#### 1. **AI Analysis Service**
   - **Description**: Reusable service providing provider-abstracted AI calls for analysis tasks
   - **Priority**: High (Foundation for all other work)
   - **Current State**:
     - No abstraction for analysis-only AI calls
     - Components must choose between:
       - Using Anthropic client directly (breaks abstraction)
       - Implementing IAgent interface (overengineering for analysis-only tasks)
   - **Target State**:
     ```python
     # gao_dev/core/services/ai_analysis_service.py
     class AIAnalysisService:
         """
         Provider-abstracted AI analysis service.

         Provides simple interface for components that need AI analysis
         without full agent capabilities (tools, artifacts, etc.).
         """

         def __init__(self, executor: ProcessExecutor):
             self.executor = executor

         async def analyze(
             self,
             prompt: str,
             model: str,
             system_prompt: Optional[str] = None,
             response_format: str = "json",
             max_tokens: int = 2048,
             temperature: float = 0.7
         ) -> str:
             """
             Send analysis prompt to AI provider, get response.

             Args:
                 prompt: User prompt for analysis
                 model: Model to use (e.g., "deepseek-r1", "claude-sonnet-4-5")
                 system_prompt: Optional system instructions
                 response_format: Expected format ("json", "text")
                 max_tokens: Maximum response length
                 temperature: Sampling temperature

             Returns:
                 str: AI response (text or JSON string)

             Raises:
                 AnalysisError: If analysis fails
             """
     ```
   - **Benefits**:
     - Simple interface for analysis-only AI calls
     - Provider-agnostic (works with any ProcessExecutor provider)
     - Easy to test (mock service or executor)
     - Reusable across codebase
   - **Success Criteria**:
     - Service implemented with comprehensive tests
     - Works with all providers (Claude Code, OpenCode, Anthropic)
     - Handles errors gracefully
     - Performance <5% overhead vs. direct API calls
     - Clear documentation

#### 2. **Brian Provider Abstraction**
   - **Description**: Refactor Brian to use AIAnalysisService instead of Anthropic client
   - **Priority**: High (Immediate user need)
   - **Changes Required**:

     **Remove Anthropic Client:**
     ```python
     # BEFORE (brian_orchestrator.py:185-187)
     self.anthropic = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

     # AFTER
     self.analysis_service = AIAnalysisService(executor)
     ```

     **Replace API Calls:**
     ```python
     # BEFORE (brian_orchestrator.py:206-210)
     response = self.anthropic.messages.create(
         model=self.model,
         max_tokens=2048,
         messages=[{"role": "user", "content": analysis_prompt}]
     )

     # AFTER
     response_text = await self.analysis_service.analyze(
         prompt=analysis_prompt,
         model=self.model,
         response_format="json",
         max_tokens=2048
     )
     ```

     **Update Initialization:**
     ```python
     # gao_dev/orchestrator/brian_orchestrator.py
     def __init__(
         self,
         workflow_registry: WorkflowRegistry,
         analysis_service: AIAnalysisService,  # NEW: Inject service
         brian_persona_path: Optional[Path] = None,
         project_root: Optional[Path] = None,
         model: Optional[str] = None
     ):
     ```

   - **Benefits**:
     - Brian can use any AI provider
     - Works with local models (deepseek-r1)
     - Testable without live API
     - Consistent with agent architecture
   - **Success Criteria**:
     - Zero direct Anthropic API calls in Brian
     - All existing tests pass
     - New tests with mocked service
     - Works with deepseek-r1 in benchmark
     - Same functionality as before

#### 3. **ProcessExecutor Integration**
   - **Description**: AIAnalysisService leverages existing ProcessExecutor for provider abstraction
   - **Priority**: High (Enables provider flexibility)
   - **Implementation Strategy**:
     - Use ProcessExecutor's existing provider abstraction
     - Create minimal agent-like interface for analysis tasks
     - Leverage existing provider implementations (OpenCode, Claude Code, etc.)
     - No changes to ProcessExecutor or providers needed
   - **Approach**:
     ```python
     class AIAnalysisService:
         async def analyze(self, prompt: str, model: str, **kwargs) -> str:
             # Create minimal execution context
             context = AnalysisContext(
                 prompt=prompt,
                 model=model,
                 **kwargs
             )

             # Execute via ProcessExecutor
             result = await self.executor.execute(context)

             # Extract and return response
             return result.response
     ```
   - **Benefits**:
     - Reuses battle-tested provider abstraction
     - No duplication of provider logic
     - Automatically works with new providers
     - Consistent error handling
   - **Success Criteria**:
     - Works with all existing providers
     - No changes to provider implementations
     - Clean interface between service and executor

#### 4. **Model Configuration Enhancement**
   - **Description**: Ensure model selection works correctly for analysis service
   - **Priority**: Medium (Quality of life)
   - **Configuration Priority**:
     1. Explicit `model` parameter to `analyze()` method
     2. `GAO_DEV_MODEL` environment variable (global override)
     3. Agent/component YAML config (brian.agent.yaml)
     4. System default
   - **Changes**:
     ```python
     # Support explicit model override per call
     await analysis_service.analyze(
         prompt=prompt,
         model="deepseek-r1"  # Overrides config
     )

     # Or use configured model
     await analysis_service.analyze(
         prompt=prompt,
         model=self.model  # From Brian's config
     )
     ```
   - **Benefits**:
     - Flexible model selection
     - Easy testing with different models
     - Supports per-analysis model choice
   - **Success Criteria**:
     - Model priority order works correctly
     - Environment variable overrides work
     - Logging shows model selection source
     - Tests verify all selection paths

#### 5. **Testing & Validation Infrastructure**
   - **Description**: Comprehensive tests for new service and Brian refactoring
   - **Priority**: High (Quality assurance)
   - **Test Categories**:

     **Unit Tests:**
     - `tests/unit/core/services/test_ai_analysis_service.py`
       - Service initialization
       - Analysis method variations
       - Error handling
       - Response parsing

     **Integration Tests:**
     - `tests/integration/test_brian_provider_abstraction.py`
       - Brian with mocked analysis service
       - Brian with real providers (Claude, OpenCode)
       - Model selection logic
       - Error scenarios

     **Benchmark Tests:**
     - Run existing simple-todo benchmark with deepseek-r1
       - Verify Brian uses correct provider
       - Validate workflow selection works
       - Check performance metrics

   - **Mock Strategy**:
     ```python
     @pytest.fixture
     def mock_analysis_service():
         service = Mock(spec=AIAnalysisService)
         service.analyze.return_value = '{"scale_level": 2, "needs_clarification": false}'
         return service

     def test_brian_with_mocked_service(mock_analysis_service):
         brian = BrianOrchestrator(
             workflow_registry=registry,
             analysis_service=mock_analysis_service
         )
         result = await brian.analyze_prompt("Build todo app")
         assert result.scale_level == 2
     ```

   - **Success Criteria**:
     - 90%+ code coverage for new code
     - All existing tests pass
     - Integration tests with all providers
     - Benchmark runs successfully with deepseek-r1
     - Performance tests show <5% overhead

#### 6. **Documentation & Migration Guide**
   - **Description**: Document the new service and migration process
   - **Priority**: Medium (Developer experience)
   - **Documentation Needs**:

     **AIAnalysisService API Docs:**
     - Usage examples
     - Configuration options
     - Error handling
     - Best practices

     **Migration Guide for Components:**
     - When to use AIAnalysisService vs. IAgent
     - How to migrate from direct API calls
     - Testing strategies
     - Examples

     **Architecture Decision Record:**
     - Why AIAnalysisService vs. making Brian an IAgent
     - Trade-offs considered
     - Future extensibility

   - **Key Documentation Files**:
     - `docs/features/ai-analysis-service/ARCHITECTURE.md`
     - `docs/features/ai-analysis-service/MIGRATION_GUIDE.md`
     - `docs/api/ai-analysis-service.md`
     - `README.md` updates (mention local model support)

   - **Success Criteria**:
     - Complete API documentation
     - Migration guide with examples
     - Architecture rationale documented
     - Updated README with local model instructions

---

## Technical Requirements

### New Components

```
gao_dev/
├── core/
│   └── services/
│       ├── ai_analysis_service.py      # NEW: Main service
│       └── analysis_context.py         # NEW: Context model
│
├── orchestrator/
│   └── brian_orchestrator.py           # MODIFIED: Use service
│
└── exceptions/
    └── analysis_exceptions.py          # NEW: Service exceptions

tests/
├── unit/
│   └── core/
│       └── services/
│           └── test_ai_analysis_service.py
│
└── integration/
    └── test_brian_provider_abstraction.py
```

### Interface Definitions

```python
# gao_dev/core/services/ai_analysis_service.py

@dataclass
class AnalysisResult:
    """Result from AI analysis."""
    response: str
    model_used: str
    tokens_used: int
    duration_ms: float

class AIAnalysisService:
    """
    Provider-abstracted AI analysis service.

    Provides simple interface for components that need AI analysis
    without full agent capabilities.
    """

    def __init__(
        self,
        executor: ProcessExecutor,
        default_model: Optional[str] = None
    ):
        """Initialize service with executor."""
        self.executor = executor
        self.default_model = default_model or "claude-sonnet-4-5-20250929"
        self.logger = structlog.get_logger()

    async def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        response_format: str = "json",
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> AnalysisResult:
        """
        Send analysis prompt to AI provider.

        Args:
            prompt: User prompt for analysis
            model: Model to use (defaults to configured model)
            system_prompt: Optional system instructions
            response_format: Expected format ("json" or "text")
            max_tokens: Maximum response length
            temperature: Sampling temperature

        Returns:
            AnalysisResult with response and metadata

        Raises:
            AnalysisError: If analysis fails
        """
```

### Performance Requirements
- Analysis call overhead: <5% vs. direct API calls
- Service initialization: <50ms
- Response parsing: <10ms
- Memory overhead: <10MB per service instance

### Quality Requirements
- 90%+ code coverage for new code
- All existing tests must pass
- Integration tests with all providers
- Performance benchmarks
- Type hints throughout (mypy strict mode)

### Compatibility Requirements
- Works with Python 3.11+
- Compatible with all existing providers
- No breaking changes to existing APIs
- Backwards compatible with current Brian usage

---

## User Stories & Acceptance Criteria

### Epic 21: AI Analysis Service & Brian Provider Abstraction

#### Story 21.1: Create AI Analysis Service (8 points)
**As a** developer
**I want** a reusable AI analysis service
**So that** components can use AI without full agent overhead

**Acceptance Criteria:**
- [ ] AIAnalysisService class implemented
- [ ] Works with ProcessExecutor
- [ ] Supports all providers (Claude Code, OpenCode, Anthropic)
- [ ] Error handling and logging
- [ ] Unit tests with 90%+ coverage
- [ ] API documentation complete

**Technical Tasks:**
- Create `ai_analysis_service.py`
- Implement `analyze()` method
- Add `AnalysisResult` dataclass
- Create `AnalysisError` exception
- Write unit tests
- Document API

#### Story 21.2: Refactor Brian to Use Analysis Service (5 points)
**As a** developer
**I want** Brian to use AIAnalysisService
**So that** Brian works with any AI provider

**Acceptance Criteria:**
- [ ] Brian no longer uses Anthropic client directly
- [ ] Brian receives AIAnalysisService via dependency injection
- [ ] `_analyze_prompt()` uses `analysis_service.analyze()`
- [ ] All existing Brian tests pass
- [ ] Same functionality as before
- [ ] Logging shows provider being used

**Technical Tasks:**
- Remove `anthropic` import from brian_orchestrator.py
- Add `analysis_service` parameter to `__init__`
- Replace `self.anthropic.messages.create()` with `self.analysis_service.analyze()`
- Update response parsing if needed
- Update tests

#### Story 21.3: Update Brian Initialization Points (3 points)
**As a** developer
**I want** Brian initialized with AIAnalysisService
**So that** all Brian usages work correctly

**Acceptance Criteria:**
- [ ] GAODevOrchestrator creates AIAnalysisService
- [ ] AIAnalysisService passed to Brian constructor
- [ ] ProcessExecutor shared between agents and analysis service
- [ ] Configuration loaded correctly
- [ ] All orchestrator tests pass

**Technical Tasks:**
- Update `orchestrator.py` to create AIAnalysisService
- Pass service to Brian constructor
- Update `BrianFactory` if exists
- Update integration tests
- Verify configuration flow

#### Story 21.4: Integration Testing with Multiple Providers (5 points)
**As a** developer
**I want** comprehensive tests with all providers
**So that** I know the abstraction works correctly

**Acceptance Criteria:**
- [ ] Integration test with Claude Code provider
- [ ] Integration test with OpenCode provider
- [ ] Integration test with mocked provider
- [ ] Test with deepseek-r1 local model
- [ ] Test error scenarios (API failures, timeouts)
- [ ] Performance benchmarks

**Technical Tasks:**
- Create `test_brian_provider_abstraction.py`
- Test Brian + AIAnalysisService + each provider
- Test model selection (env var, config, explicit)
- Test error handling
- Add performance tests
- Document test setup

#### Story 21.5: Benchmark Validation with DeepSeek-R1 (3 points)
**As a** user
**I want** to run benchmarks with local deepseek-r1 model
**So that** I can validate GAO-Dev with free local models

**Acceptance Criteria:**
- [ ] `simple-todo-deepseek.yaml` benchmark runs successfully
- [ ] Brian uses deepseek-r1 via OpenCode + Ollama
- [ ] Workflow selection works correctly
- [ ] Metrics captured correctly
- [ ] Report generated successfully
- [ ] Performance acceptable vs. Claude

**Technical Tasks:**
- Run benchmark with `AGENT_PROVIDER=opencode-sdk`
- Verify Brian logs show deepseek-r1 model
- Check workflow sequence correctness
- Review generated report
- Document performance comparison
- Create troubleshooting guide

#### Story 21.6: Documentation & Examples (3 points)
**As a** developer
**I want** comprehensive documentation
**So that** I can use and extend the analysis service

**Acceptance Criteria:**
- [ ] AIAnalysisService API documentation
- [ ] Architecture decision record
- [ ] Usage examples
- [ ] Migration guide for components
- [ ] When to use service vs. agent guidance
- [ ] README updated with local model info

**Technical Tasks:**
- Write `ARCHITECTURE.md`
- Write `MIGRATION_GUIDE.md`
- Create usage examples
- Document testing strategies
- Update README.md
- Add troubleshooting section

---

## Success Metrics

### Before (Current State)
- Brian provider: Anthropic only (hardcoded)
- Local model support: None
- Testing: Requires live API access
- Architecture: Inconsistent (Brian bypasses abstraction)
- Cost: All development requires paid API calls

### After (Target State)
- Brian provider: Any (Claude, OpenCode, local)
- Local model support: Full (deepseek-r1, etc.)
- Testing: Mockable, no API required
- Architecture: Consistent (all use provider abstraction)
- Cost: Free local models for development

### KPIs
- **Provider abstraction**: 100% (Brian fully abstracted)
- **Local model benchmarks**: Working (deepseek-r1 benchmark runs)
- **Test coverage**: 90%+ for new code
- **Performance overhead**: <5% vs. direct API
- **Developer velocity**: 50% faster iteration with local models

---

## Risks & Mitigations

### Technical Risks

**Risk 1: Performance overhead from abstraction layer**
- **Impact**: Medium
- **Probability**: Low
- **Mitigation**:
  - Keep service thin (minimal processing)
  - Benchmark before/after
  - Optimize hot paths if needed
  - Target <5% overhead

**Risk 2: ProcessExecutor not suitable for analysis tasks**
- **Impact**: High
- **Probability**: Low
- **Mitigation**:
  - ProcessExecutor already handles simple prompts
  - Analysis is simpler than full agent workflows
  - Fallback: Direct provider calls with abstraction
  - Prototype first to validate approach

**Risk 3: Local model quality insufficient**
- **Impact**: Low (Feature still valuable)
- **Probability**: Medium
- **Mitigation**:
  - Use for development/testing only initially
  - Benchmark quality metrics
  - Document known limitations
  - Keep Claude as default for production

**Risk 4: Breaking existing Brian functionality**
- **Impact**: High
- **Probability**: Low
- **Mitigation**:
  - Comprehensive test suite
  - Feature flag for rollback
  - Parallel testing (old vs. new)
  - Gradual rollout

### Organizational Risks

**Risk 1: Increased complexity**
- **Impact**: Low
- **Probability**: Low
- **Mitigation**:
  - Clear abstraction boundaries
  - Good documentation
  - Simple, focused service
  - Examples and guides

**Risk 2: Local model setup friction**
- **Impact**: Low (Optional feature)
- **Probability**: Medium
- **Mitigation**:
  - Clear setup instructions
  - Automated setup script
  - Troubleshooting guide
  - Default to Claude (zero setup)

---

## Dependencies

### Internal Dependencies
- **ProcessExecutor** (exists): Core provider abstraction
- **Provider implementations** (exist): Claude Code, OpenCode, Anthropic
- **Brian orchestrator** (exists): Will be refactored
- **Workflow registry** (exists): Used by Brian
- **AgentConfigLoader** (exists): For model configuration

### External Dependencies
- **anthropic** (installed): Can remain for Anthropic provider
- **openai** (installed): Used by OpenCode SDK provider
- **ollama** (external): Must be installed and running for local models
- **deepseek-r1** (external): Must be pulled in Ollama

### Environment Setup for Local Models
```bash
# Install Ollama
# https://ollama.ai/download

# Pull deepseek-r1 model
ollama pull deepseek-r1:8b

# Configure OpenCode server (opencode.json already created)
# Start OpenCode server
opencode start

# Set environment variable
export AGENT_PROVIDER=opencode-sdk
export GAO_DEV_MODEL=deepseek-r1

# Run benchmark
python run_deepseek_benchmark.py
```

---

## Timeline & Milestones

### Phase 1: Service Foundation (Stories 21.1)
**Duration**: 1 sprint (2 weeks)
- Create AIAnalysisService
- Core functionality working
- Unit tests complete
- **Milestone**: Service can execute analysis via ProcessExecutor

### Phase 2: Brian Refactoring (Stories 21.2, 21.3)
**Duration**: 1 sprint (2 weeks)
- Refactor Brian to use service
- Update initialization points
- All existing tests pass
- **Milestone**: Brian fully provider-abstracted

### Phase 3: Testing & Validation (Stories 21.4, 21.5)
**Duration**: 1 sprint (2 weeks)
- Integration tests with all providers
- Benchmark with deepseek-r1
- Performance validation
- **Milestone**: Benchmark runs successfully with local model

### Phase 4: Documentation (Story 21.6)
**Duration**: 0.5 sprint (1 week)
- Complete documentation
- Examples and guides
- README updates
- **Milestone**: Feature fully documented and production-ready

**Total Estimated Duration**: 3.5 sprints (~7 weeks)

---

## Appendix

### References
- **Architecture Analysis**: `docs/analysis/brian-architecture-analysis.md`
- **Brian Implementation**: `gao_dev/orchestrator/brian_orchestrator.py`
- **ProcessExecutor**: `gao_dev/core/process_executor.py`
- **OpenCode Provider**: `gao_dev/core/providers/opencode_sdk.py`
- **Existing Benchmark**: `sandbox/benchmarks/simple-todo-deepseek.yaml`
- **Benchmark Runner**: `run_deepseek_benchmark.py`

### Glossary
- **AI Analysis Service**: Reusable service providing provider-abstracted AI calls for analysis tasks
- **Provider Abstraction**: Pattern enabling use of multiple AI providers through common interface
- **ProcessExecutor**: Core service managing agent execution across providers
- **Analysis Component**: Component that needs AI for decision-making but doesn't create artifacts
- **Local Model**: LLM running locally via Ollama (e.g., deepseek-r1)

### Architecture Decision: Why AIAnalysisService vs. IAgent?

**Decision**: Create AIAnalysisService instead of making Brian implement IAgent

**Rationale**:
1. **Brian is not an agent**: Doesn't create artifacts, doesn't use tools, single-shot analysis
2. **IAgent is too heavy**: Designed for artifact-creating agents with full tool access
3. **Reusability**: Analysis service useful for future analysis needs (cost estimation, code review summaries)
4. **Separation of concerns**: Brian focuses on workflow logic, service handles AI calls
5. **Right abstraction**: Match abstraction to use case

**Trade-offs**:
- **Pro**: Simpler, more focused, reusable, right level of abstraction
- **Con**: New service to maintain, slightly more complexity
- **Verdict**: Benefits outweigh costs, this is the right architectural choice

### Version History
- **1.0.0** (2025-11-07): Initial PRD creation based on architecture analysis
