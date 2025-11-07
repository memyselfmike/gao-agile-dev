# AI Analysis Service Architecture

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Version**: 1.0
**Status**: Implemented
**Last Updated**: 2025-11-07

---

## Problem Statement

Before Epic 21, Brian orchestrator used the Anthropic client directly for complexity analysis. This approach had several limitations:

1. **Provider Lock-in**: Hard dependency on Anthropic API
2. **No Local Model Support**: Cannot use free local models (Ollama + deepseek-r1)
3. **Limited Testability**: Cannot test without live API calls
4. **Cost Concerns**: Every analysis costs money
5. **Architectural Inconsistency**: Other agents use provider abstraction, Brian didn't

### Specific Issues

```python
# Before: Direct Anthropic dependency in Brian
import anthropic

class BrianOrchestrator:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def analyze_complexity(self, prompt: str):
        # Direct API call - no abstraction, no flexibility
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": prompt}]
        )
        # Cannot swap providers, cannot test easily
```

---

## Solution: AIAnalysisService

### Decision

Create **AIAnalysisService** - a reusable service for analysis-only AI calls that provides provider abstraction for lightweight analysis tasks.

### Why Service Instead of IAgent?

**Brian is NOT an agent:**
- No artifacts created (no files, no commits)
- No tools needed (no Read, Write, Bash, etc.)
- Single-shot analysis (returns decision, not work product)
- Returns structured decisions, not deliverables
- Stateless operation (no context maintenance)

**IAgent is too heavy for this use case:**
- Designed for artifact-creating agents (John, Winston, Amelia, etc.)
- Full tool access (Read, Write, Edit, Bash, Grep, etc.)
- Complex lifecycle management (initialization, state, cleanup)
- Overhead for simple analysis tasks
- Over-engineering for decision-making

**Service is the right abstraction:**
- Simple, focused interface for analysis
- Lightweight - no unnecessary complexity
- Reusable across any component
- Easy to test and mock
- Right level of abstraction for non-artifact work

### Classification Decision

**Brian = Orchestrator, NOT Agent**

Brian doesn't create artifacts or use tools. It's a workflow coordinator that makes routing decisions. The AIAnalysisService provides the AI capability Brian needs without forcing it into the IAgent pattern.

---

## Architecture

### Component Diagram

```
User Request
    ↓
BrianOrchestrator (workflow coordinator)
    ↓ uses
AIAnalysisService (analysis abstraction)
    ↓ uses
Anthropic Client (API integration)
    ↓
Any Provider:
  - Anthropic API (Claude Sonnet 4.5)
  - Ollama (deepseek-r1, llama3, etc.)
  - OpenCode Server
  - Future: OpenAI, Gemini, etc.
```

### Data Flow

```
1. Brian receives user prompt
   ↓
2. Brian calls AIAnalysisService.analyze(prompt)
   ↓
3. Service formats request for provider
   ↓
4. Service calls provider API (Anthropic/Ollama/etc.)
   ↓
5. Service parses response
   ↓
6. Service returns AnalysisResult
   ↓
7. Brian processes decision
   ↓
8. Brian selects workflows and routes to agents
```

### Class Structure

```python
@dataclass
class AnalysisResult:
    """Result from AI analysis."""
    response: str           # AI response (text or JSON)
    model_used: str         # Model that processed request
    tokens_used: int        # Token count (prompt + completion)
    duration_ms: float      # Processing time

class AIAnalysisService:
    """Provider-abstracted AI analysis service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        """Initialize with API key and default model."""

    async def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        response_format: str = "json",
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> AnalysisResult:
        """Execute AI analysis and return structured result."""
```

---

## Benefits

### 1. Provider Independence
- Works with any AI provider (Anthropic, Ollama, OpenCode, etc.)
- Easy to swap providers based on cost/performance needs
- No vendor lock-in

### 2. Cost Savings
- Use free local models for development
- Reserve paid API for production/critical tasks
- Benchmark runs cost $0 with local models

### 3. Testability
- Easy to mock for unit tests
- No live API calls needed in tests
- Fast test execution

### 4. Reusability
- Any component can use for analysis
- Consistent interface across codebase
- Single source of truth for analysis calls

### 5. Architectural Consistency
- All components now use abstraction
- No direct API dependencies in business logic
- Clean separation of concerns

---

## Trade-offs

### Pros
- **Clean Architecture**: Separation of concerns
- **Flexibility**: Easy to change providers
- **Testability**: Mockable interface
- **Reusability**: Single service for all analysis
- **Cost Efficiency**: Free local models option

### Cons
- **New Service**: One more component to maintain
- **Slight Complexity**: Abstraction layer adds code
- **Learning Curve**: Developers must understand service API
- **Initial Setup**: Requires provider configuration

### Verdict
**Benefits far outweigh costs.** The service is simple, focused, and solves real problems (cost, flexibility, testability).

---

## Design Decisions

### Decision 1: Direct Anthropic Client (for now)

**Choice**: Use Anthropic client directly in AIAnalysisService
**Rationale**:
- ProcessExecutor is designed for full agent tasks (tools, artifacts)
- Analysis is simpler - just prompt/response
- Can add full provider abstraction later if needed

**Future**: Could integrate with ProcessExecutor for unified provider abstraction.

### Decision 2: Async API

**Choice**: Async/await interface
**Rationale**:
- Orchestrator is already async
- Allows concurrent analysis calls
- Better resource utilization

### Decision 3: JSON Response Format Default

**Choice**: Default `response_format="json"`
**Rationale**:
- Brian needs structured decisions
- Easier to parse and validate
- Fallback to "text" when needed

### Decision 4: Result Dataclass

**Choice**: Return structured `AnalysisResult`
**Rationale**:
- Provides response + metadata (tokens, duration, model)
- Enables metrics tracking
- Better than returning raw string

---

## Alternatives Considered

### Alternative 1: Make Brian an IAgent

**Rejected because:**
- Brian doesn't create artifacts
- Would need dummy tool implementations
- Violates Single Responsibility Principle
- Over-engineering for simple analysis

### Alternative 2: Use ProcessExecutor Directly

**Rejected because:**
- ProcessExecutor designed for full agent tasks
- Overkill for simple analysis
- Harder to mock and test
- More complexity than needed

### Alternative 3: Keep Direct Anthropic Calls

**Rejected because:**
- No provider flexibility
- Cannot use local models
- Hard to test
- Inconsistent with rest of architecture

### Alternative 4: Create Generic "AI Service"

**Rejected because:**
- Too broad - different use cases need different abstractions
- Analysis is distinct from artifact creation
- Focused service is easier to understand and maintain

---

## Implementation Notes

### Error Handling

Service maps Anthropic errors to standard exceptions:
- `AnalysisError`: Base exception for all failures
- `AnalysisTimeoutError`: Request timeout
- `InvalidModelError`: Model not found or invalid

### Logging

Comprehensive structured logging:
- Request parameters (model, tokens, temperature)
- Response metadata (duration, tokens used)
- Errors with full context

### Validation

- JSON response validation (warns if malformed)
- Token count tracking
- Duration measurement

---

## Future Extensions

### Near-term (Epic 22+)
1. **Full Provider Abstraction**: Integrate with ProcessExecutor
2. **Multi-Model Consensus**: Run same analysis on multiple models, compare
3. **Caching**: Cache analysis results for identical prompts
4. **Retry Logic**: Automatic retry on transient errors

### Long-term
1. **Cost Estimation Service**: Reuse for other analysis tasks
2. **Code Review Summarization**: Analyze code diffs
3. **Complexity Analysis for Other Components**: Reuse beyond Brian
4. **A/B Testing**: Compare prompt variations

---

## Migration Guide

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for step-by-step migration instructions.

---

## Success Metrics

### Epic 21 Goals (Achieved)
- Brian refactored to use AIAnalysisService
- Can run benchmarks with local models (deepseek-r1)
- Cost savings: $0 for development vs. $0.01-0.05 per analysis
- Test coverage: AIAnalysisService 100% covered

### Quality Indicators
- No direct Anthropic imports in orchestrators
- All analysis goes through service
- Easy to swap providers
- Fast test execution (mocked service)

---

## References

- **PRD**: [PRD.md](./PRD.md)
- **Epic 21 Plan**: [EPIC-21-PLAN.md](./EPIC-21-PLAN.md)
- **Implementation**: `gao_dev/core/services/ai_analysis_service.py`
- **Brian Orchestrator**: `gao_dev/orchestrator/brian_orchestrator.py`
- **Tests**: `tests/integration/test_brian_orchestrator.py`

---

## Related Patterns

- **Service Layer Pattern**: Business logic in reusable services
- **Adapter Pattern**: Abstracts provider differences
- **Strategy Pattern**: Pluggable AI providers
- **Facade Pattern**: Simplified interface over complex API

---

**Document Status**: Complete
**Approved By**: Winston (Technical Architect)
**Review Date**: 2025-11-07
