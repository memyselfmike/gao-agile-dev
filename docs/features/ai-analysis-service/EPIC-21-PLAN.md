# Epic 21: AI Analysis Service & Brian Provider Abstraction

**Status**: Ready
**Total Story Points**: 27
**Stories**: 6
**Priority**: High - Enables local model usage and architecture consistency

---

## Epic Goal

Enable GAO-Dev's orchestration components (starting with Brian) to use any AI provider through a reusable AI Analysis Service, eliminating hardcoded provider dependencies and enabling local model usage (Ollama + deepseek-r1) for cost savings and offline development.

---

## The Problem

**Current (Wrong) Architecture:**
```
BrianOrchestrator
    |
    v uses directly
Anthropic API Client (hardcoded)
    |
    v
Anthropic Cloud Only
```

Brian's provider dependency:
- Uses `self.anthropic.messages.create()` directly (line 206-210)
- Bypasses GAO-Dev's provider abstraction entirely
- Cannot use local models (Ollama + deepseek-r1)
- Cannot use OpenCode provider
- Cannot be tested without live API
- Violates Dependency Inversion Principle

**Impact:**
1. **Cost**: All development requires paid Anthropic API calls
2. **Inconsistency**: Agents use provider abstraction, Brian doesn't
3. **Testing**: Cannot test Brian without live API access
4. **Flexibility**: Cannot benchmark with local models (user's original request)
5. **Architecture**: Violates core design principles

**Evidence**: Benchmark attempts with deepseek-r1 failed with "404 - model: deepseek-r1" because Brian sends the model name to Anthropic's cloud API, which doesn't recognize local models.

---

## The Solution

**Correct (New) Architecture:**
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
Provider Abstraction
    |
    v
Any Provider: Claude Code, OpenCode, Anthropic, Local Ollama
```

Create **AIAnalysisService** - a reusable service for analysis-only AI calls:
1. Provides simple interface for components needing AI analysis
2. Uses ProcessExecutor internally for provider abstraction
3. Works with any provider (Claude, OpenCode, local models)
4. Easy to test (mock service or executor)
5. Reusable for future analysis needs

Refactor **Brian** to use the service:
1. Remove direct Anthropic client dependency
2. Receive AIAnalysisService via dependency injection
3. Use service for all AI analysis calls
4. Maintain existing functionality

---

## Why AIAnalysisService vs Making Brian an IAgent?

**Decision**: Create AIAnalysisService instead of making Brian implement IAgent

**Rationale**:
- **Brian is not an agent**: Doesn't create artifacts, doesn't use tools, single-shot analysis
- **IAgent is too heavy**: Designed for artifact-creating agents with full tool access
- **Reusability**: Service can be used by any component needing AI analysis
- **Right abstraction**: Match abstraction level to use case

**From Architecture Analysis** (docs/analysis/brian-architecture-analysis.md):
- Brian is an "AI-powered orchestration component"
- Makes strategic decisions about workflows
- Returns structured decisions, not artifacts
- No iteration, no tools, no file interaction

---

## Epic Stories

### Story 21.1: Create AI Analysis Service (8 points)
Create reusable AIAnalysisService providing provider-abstracted AI calls.

**Key Deliverables:**
- `gao_dev/core/services/ai_analysis_service.py` - Main service class
- `analyze()` method with flexible parameters
- Integration with ProcessExecutor
- Error handling and logging
- Unit tests with 90%+ coverage
- API documentation

### Story 21.2: Refactor Brian to Use Analysis Service (5 points)
Remove Brian's direct Anthropic dependency and use AIAnalysisService.

**Key Deliverables:**
- Remove `anthropic` import from brian_orchestrator.py
- Add `analysis_service` parameter to `__init__`
- Replace `self.anthropic.messages.create()` with `self.analysis_service.analyze()`
- All existing Brian tests pass
- Same functionality as before

### Story 21.3: Update Brian Initialization Points (3 points)
Update all locations that create Brian to inject AIAnalysisService.

**Key Deliverables:**
- GAODevOrchestrator creates AIAnalysisService
- AIAnalysisService passed to Brian constructor
- ProcessExecutor shared between agents and service
- Configuration loaded correctly
- All orchestrator tests pass

### Story 21.4: Integration Testing with Multiple Providers (5 points)
Comprehensive tests validating service works with all providers.

**Key Deliverables:**
- Integration tests with Claude Code provider
- Integration tests with OpenCode provider
- Integration tests with mocked provider
- Test with deepseek-r1 local model
- Error scenario tests
- Performance benchmarks

### Story 21.5: Benchmark Validation with DeepSeek-R1 (3 points)
Validate that benchmarks work with local deepseek-r1 model.

**Key Deliverables:**
- Run `simple-todo-deepseek.yaml` benchmark successfully
- Brian uses deepseek-r1 via OpenCode + Ollama
- Workflow selection works correctly
- Metrics captured correctly
- Report generated successfully
- Performance comparison documented

### Story 21.6: Documentation & Examples (3 points)
Complete documentation for service and migration guidance.

**Key Deliverables:**
- AIAnalysisService API documentation
- Architecture decision record
- Usage examples
- Migration guide for components
- When to use service vs. agent guidance
- README updated with local model info

---

## What Exists vs What's Missing

### Already Built
1. **ProcessExecutor** (`gao_dev/core/process_executor.py`) - Provider abstraction
2. **Provider Implementations** - Claude Code, OpenCode, Anthropic providers
3. **OpenCode Configuration** (`opencode.json`) - Ollama + deepseek-r1 setup
4. **Brian Orchestrator** (`gao_dev/orchestrator/brian_orchestrator.py`) - Needs refactoring
5. **Benchmark Infrastructure** - Ready to test with local models

### Missing Components
1. **AIAnalysisService** - Reusable analysis service (Story 21.1)
2. **Brian Integration** - Refactor to use service (Stories 21.2, 21.3)
3. **Comprehensive Tests** - Integration and benchmark tests (Stories 21.4, 21.5)
4. **Documentation** - API docs and migration guide (Story 21.6)

---

## Migration Path

### Phase 1: Service Foundation (Story 21.1)
**Duration**: 1 sprint (2 weeks)
1. Design AIAnalysisService interface
2. Implement using ProcessExecutor
3. Add comprehensive unit tests
4. Document API

**Milestone**: Service can execute analysis via any provider

### Phase 2: Brian Refactoring (Stories 21.2, 21.3)
**Duration**: 1 sprint (2 weeks)
1. Refactor Brian to use service
2. Update all initialization points
3. Validate existing tests pass
4. Test with multiple providers

**Milestone**: Brian fully provider-abstracted

### Phase 3: Testing & Validation (Stories 21.4, 21.5)
**Duration**: 1 sprint (2 weeks)
1. Integration tests with all providers
2. Benchmark with deepseek-r1
3. Performance validation
4. Error handling verification

**Milestone**: Benchmark runs successfully with local model

### Phase 4: Documentation (Story 21.6)
**Duration**: 0.5 sprint (1 week)
1. Complete API documentation
2. Write migration guide
3. Create examples
4. Update README

**Milestone**: Feature fully documented and production-ready

---

## Benefits of This Architecture

1. **Cost Savings**: Free local models for development and testing
2. **Provider Independence**: Works with any AI provider
3. **Architecture Consistency**: All components use provider abstraction
4. **Testability**: Easy to mock for testing
5. **Reusability**: Service can be used by future analysis components
6. **Offline Development**: Can work without internet (with local models)

---

## Success Criteria

Epic 21 is complete when:

- [x] AIAnalysisService implemented and tested
- [x] Brian uses AIAnalysisService (no direct Anthropic calls)
- [x] Works with all providers (Claude, OpenCode, local models)
- [x] Benchmark runs successfully with deepseek-r1
- [x] 90%+ test coverage for new code
- [x] Performance overhead <5% vs. direct API calls
- [x] Complete documentation and examples
- [x] All existing tests pass

---

## Technical Debt Addressed

This epic fixes the architectural inconsistency identified during local model testing:
- Brian now uses provider abstraction like all agents
- No hardcoded provider dependencies in orchestration layer
- Consistent architecture across entire codebase
- Enables testing without live API access

---

## Dependencies

### Internal Dependencies
- **ProcessExecutor** (exists) - Core provider abstraction
- **Provider Implementations** (exist) - Claude Code, OpenCode, Anthropic
- **Brian Orchestrator** (exists) - Will be refactored
- **Workflow Registry** (exists) - Used by Brian
- **AgentConfigLoader** (exists) - For model configuration

### External Dependencies
- **Ollama** (external) - Must be installed for local models
- **deepseek-r1** (external) - Must be pulled in Ollama
- **OpenCode Server** (optional) - For OpenCode provider

### Environment Setup
```bash
# Install Ollama (https://ollama.ai/download)
# Pull deepseek-r1 model
ollama pull deepseek-r1:8b

# Configure OpenCode server (opencode.json already exists)
# Start OpenCode server
opencode start

# Set environment variables
export AGENT_PROVIDER=opencode-sdk
export GAO_DEV_MODEL=deepseek-r1

# Run benchmark
python run_deepseek_benchmark.py
```

---

## Risks and Mitigation

**Risk 1**: Performance overhead from abstraction layer
- **Impact**: Medium
- **Probability**: Low
- **Mitigation**: Keep service thin, benchmark before/after, target <5% overhead

**Risk 2**: ProcessExecutor not suitable for analysis tasks
- **Impact**: High
- **Probability**: Low
- **Mitigation**: ProcessExecutor already handles simple prompts, analysis is simpler than full agent workflows

**Risk 3**: Local model quality insufficient
- **Impact**: Low (feature still valuable)
- **Probability**: Medium
- **Mitigation**: Use for development/testing only initially, document limitations, keep Claude as default

**Risk 4**: Breaking existing Brian functionality
- **Impact**: High
- **Probability**: Low
- **Mitigation**: Comprehensive tests, feature flag for rollback, parallel testing, gradual rollout

---

## Related Documentation

- **Architecture Analysis**: `docs/analysis/brian-architecture-analysis.md`
- **Feature PRD**: `docs/features/ai-analysis-service/PRD.md`
- **Brian Implementation**: `gao_dev/orchestrator/brian_orchestrator.py`
- **ProcessExecutor**: `gao_dev/core/process_executor.py`
- **OpenCode Provider**: `gao_dev/core/providers/opencode_sdk.py`
- **Benchmark Config**: `sandbox/benchmarks/simple-todo-deepseek.yaml`
- **Benchmark Runner**: `run_deepseek_benchmark.py`

---

## Estimated Timeline

**Total Duration**: 3.5 sprints (~7 weeks)

| Phase | Duration | Stories | Milestone |
|-------|----------|---------|-----------|
| Phase 1: Service Foundation | 2 weeks | 21.1 | Service working |
| Phase 2: Brian Refactoring | 2 weeks | 21.2, 21.3 | Brian abstracted |
| Phase 3: Testing & Validation | 2 weeks | 21.4, 21.5 | Benchmark passing |
| Phase 4: Documentation | 1 week | 21.6 | Production ready |

---

## Sprint Planning Recommendation

**Sprint 1**: Stories 21.1 (8 points)
- Focus: Create AIAnalysisService
- Goal: Service infrastructure complete

**Sprint 2**: Stories 21.2, 21.3 (8 points)
- Focus: Refactor Brian
- Goal: Brian uses service

**Sprint 3**: Stories 21.4, 21.5 (8 points)
- Focus: Integration testing
- Goal: Benchmark with local models works

**Sprint 4**: Story 21.6 (3 points)
- Focus: Documentation
- Goal: Production-ready with docs
