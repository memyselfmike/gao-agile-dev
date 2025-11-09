# Story 29.3: Brian Context Augmentation

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 8 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: Story 29.2 (LearningApplicationService)

---

## User Story

**As a** Brian (workflow selector)
**I want** my analysis context enriched with top 5 relevant learnings
**So that** I make better workflow decisions based on past experience

---

## Acceptance Criteria

### AC1: BrianOrchestrator Enhancement

- [ ] Modify `gao_dev/orchestrator/brian_orchestrator.py` (~100 lines added)
- [ ] Add method: `_build_context_with_learnings(scale_level, project_type, user_prompt) -> str`
- [ ] Integrate `LearningApplicationService` into BrianOrchestrator
- [ ] Performance: <500ms for context building (C5 fix - realistic target)
- [ ] Breakdown:
  - Learning retrieval: ~50ms
  - Template rendering: ~100ms
  - Brian context building: ~200ms
  - Network RTT for 19K tokens: ~150ms
- [ ] Previous <100ms target was unrealistic given network latency

### AC2: Learning Context Template

- [ ] Create prompt template enhancement in `gao_dev/config/prompts/brian/`
- [ ] Template includes:
  ```markdown
  ## Relevant Past Learnings

  Based on analysis of past projects, here are key learnings relevant to this context:

  {{#learnings}}
  ### Learning {{rank}}: {{category}} (Confidence: {{confidence}}, Success Rate: {{success_rate}})

  **Content**: {{content}}

  **Context**: {{context}}

  **Applications**: Applied {{application_count}} times with {{success_rate}}% success

  **Recommendation**: {{recommendation}}

  ---
  {{/learnings}}

  Please consider these learnings when selecting workflows. If learnings suggest:
  - Quality issues ’ Add extra testing workflows
  - Process improvements ’ Adjust ceremony frequency
  - Architectural patterns ’ Include review steps
  - Technical pitfalls ’ Add validation checkpoints
  ```
- [ ] Template supports 0-5 learnings (graceful when none found)
- [ ] Template renders in <100ms

### AC3: Context Building Logic

- [ ] Method signature:
  ```python
  def _build_context_with_learnings(
      self,
      scale_level: ScaleLevel,
      project_type: str,
      user_prompt: str
  ) -> str:
      """
      Build Brian's analysis context enriched with learnings.

      Args:
          scale_level: Detected scale level
          project_type: Project type (greenfield, feature, bugfix)
          user_prompt: Original user request

      Returns:
          Enriched context string for Brian's analysis
      """
  ```
- [ ] Extract context tags from user prompt (keywords, requirements)
- [ ] Call `LearningApplicationService.get_relevant_learnings()` with context
- [ ] Format learnings using template
- [ ] Append to base Brian context
- [ ] Return final enriched context

### AC4: Learning Extraction from User Prompt

- [ ] Implement `_extract_context_from_prompt(user_prompt) -> Dict[str, Any]`
- [ ] Extract:
  - Tags: Keywords like "authentication", "api", "testing"
  - Requirements: Security, performance, scalability mentions
  - Technologies: Python, React, PostgreSQL, etc.
  - Project phase: Greenfield, enhancement, refactor
- [ ] Use simple keyword matching (no ML required)
- [ ] Examples:
  ```python
  "Build a todo app with authentication"
  ’ {"tags": ["todo", "authentication"], "requirements": [], "technologies": []}

  "Add JWT authentication to API with Redis caching"
  ’ {"tags": ["authentication", "api", "caching"],
     "requirements": ["security"],
     "technologies": ["jwt", "redis"]}
  ```

### AC5: Integration with Existing Brian Flow

- [ ] Modify `select_workflows_with_learning()` to use new context builder
- [ ] Flow:
  ```python
  def select_workflows_with_learning(self, user_prompt: str):
      # 1. Complexity analysis (existing)
      analysis = self._analyze_complexity(user_prompt)

      # 2. Build enriched context with learnings (NEW)
      context = self._build_context_with_learnings(
          scale_level=analysis.scale_level,
          project_type=analysis.project_type,
          user_prompt=user_prompt
      )

      # 3. Select workflows with enriched context (existing)
      workflows = self.workflow_selector.select_workflows(
          scale_level=analysis.scale_level,
          context=context  # Now includes learnings
      )

      # 4. Record learning applications (NEW - moved to Story 29.4)
      # Done in workflow adjustment logic

      return workflows
  ```
- [ ] Backward compatible (works when no learnings found)
- [ ] Structured logging for learning application

### AC6: Learning Context Caching

- [ ] Cache learning context for same scale_level + project_type
- [ ] Cache TTL: 1 hour (learnings don't change frequently)
- [ ] Cache key: `f"learning_context_{scale_level}_{project_type}_{context_hash}"`
- [ ] Cache invalidation: On new learnings indexed
- [ ] Improves performance from ~50ms to ~5ms (cache hit)

### AC7: Fallback Handling

- [ ] Gracefully handle no learnings found (relevance score < threshold)
- [ ] Gracefully handle LearningApplicationService errors
- [ ] Fallback: Continue with base Brian context (no learnings)
- [ ] Log warning but don't fail workflow selection
- [ ] Example:
  ```python
  try:
      learnings = self.learning_app.get_relevant_learnings(...)
  except Exception as e:
      logger.warning(f"Failed to load learnings: {e}", exc_info=True)
      learnings = []  # Fallback to empty
  ```

### AC8: Unit Tests

- [ ] Create `tests/orchestrator/test_brian_context_augmentation.py` (~250 lines)
- [ ] Tests:
  - Context building with 0-5 learnings
  - Template rendering correctness
  - Performance target met (<500ms, C5 fix)
  - Cache hit/miss scenarios
  - Fallback on errors
  - Context extraction from various prompts
  - Integration with workflow selection
- [ ] Test coverage >95%
- [ ] Mock LearningApplicationService for isolation

---

## Technical Details

### Files to Modify

**1. BrianOrchestrator Enhancement**:
- `gao_dev/orchestrator/brian_orchestrator.py` (+100 lines)
  - Add `_build_context_with_learnings()`
  - Add `_extract_context_from_prompt()`
  - Modify `select_workflows_with_learning()`
  - Add caching logic

**2. Prompt Template**:
- `gao_dev/config/prompts/brian/context_with_learnings.yaml` (new, ~80 lines)
  - Mustache template for learnings
  - Conditional rendering (0-5 learnings)
  - Clear recommendations section

**3. Unit Tests**:
- `tests/orchestrator/test_brian_context_augmentation.py` (new, ~250 lines)

### Context Extraction Algorithm

```python
def _extract_context_from_prompt(self, user_prompt: str) -> Dict[str, Any]:
    """
    Extract context clues from user prompt.

    Uses simple keyword matching for:
    - Tags: Common feature keywords
    - Requirements: Security, performance, scalability
    - Technologies: Named technologies/frameworks
    - Phase: Greenfield vs enhancement indicators
    """
    context = {
        "tags": [],
        "requirements": [],
        "technologies": [],
        "phase": "unknown"
    }

    prompt_lower = user_prompt.lower()

    # Extract tags (features)
    feature_keywords = [
        "authentication", "auth", "login", "api", "rest", "graphql",
        "database", "db", "storage", "cache", "search", "testing",
        "ui", "frontend", "backend", "admin", "user", "payment"
    ]
    context["tags"] = [kw for kw in feature_keywords if kw in prompt_lower]

    # Extract requirements
    requirement_keywords = {
        "security": ["security", "secure", "auth", "encryption", "ssl"],
        "performance": ["performance", "fast", "optimize", "cache"],
        "scalability": ["scalability", "scale", "distributed", "cluster"]
    }
    for req, keywords in requirement_keywords.items():
        if any(kw in prompt_lower for kw in keywords):
            context["requirements"].append(req)

    # Extract technologies
    tech_keywords = [
        "python", "javascript", "react", "vue", "django", "flask",
        "postgres", "mysql", "redis", "mongodb", "jwt", "oauth"
    ]
    context["technologies"] = [tech for tech in tech_keywords if tech in prompt_lower]

    # Detect phase
    if any(word in prompt_lower for word in ["build", "create", "new"]):
        context["phase"] = "greenfield"
    elif any(word in prompt_lower for word in ["add", "enhance", "extend"]):
        context["phase"] = "enhancement"
    elif any(word in prompt_lower for word in ["fix", "bug", "issue"]):
        context["phase"] = "bugfix"

    return context
```

### Performance Optimization (C5 Fix)

**Target**: <500ms (revised from unrealistic <100ms)

**Breakdown**:
1. **Learning Query**: ~50ms
   - Database indexed query
   - Limit to 50 candidates, filter to top 5
   - Caching reduces to ~5ms on cache hit

2. **Template Rendering**: ~100ms
   - Mustache template with 5 learnings
   - String concatenation and formatting

3. **Context Building**: ~200ms
   - Append to base Brian context (19K tokens)
   - Format final prompt string

4. **Network RTT**: ~150ms
   - 19K tokens to Claude API
   - Network latency (unavoidable)

**Total**: ~500ms (realistic with network latency included)

**Optimizations**:
- Cache learning context (1-hour TTL)
- Limit learnings to top 5
- Pre-render common templates
- Async loading where possible

---

## Testing Strategy

### Unit Tests

**Test 1: Context Building with 5 Learnings**
```python
def test_build_context_with_learnings_full():
    """Test context building with 5 relevant learnings."""
    learnings = [create_mock_learning(i) for i in range(5)]

    context = brian._build_context_with_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="greenfield",
        user_prompt="Build API with authentication"
    )

    assert "## Relevant Past Learnings" in context
    assert "Learning 1:" in context
    assert "Learning 5:" in context
```

**Test 2: Performance Target Met**
```python
def test_context_building_performance():
    """Test context building meets <500ms target (C5 fix)."""
    import time

    start = time.time()
    context = brian._build_context_with_learnings(...)
    duration_ms = (time.time() - start) * 1000

    assert duration_ms < 500, f"Context building took {duration_ms}ms"
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] BrianOrchestrator enhanced with learning context
- [ ] Context template created and validated
- [ ] Performance target met (<500ms, C5 fix)
- [ ] Caching implemented and tested
- [ ] Fallback handling tested
- [ ] Unit tests passing (>95% coverage)
- [ ] No linting errors (ruff)
- [ ] Type hints complete, mypy passes
- [ ] Code reviewed and approved
- [ ] Changes committed with clear message
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Story 29.2 (LearningApplicationService)
- Epic 24 (LearningIndexService)

**Downstream**:
- Story 29.4 (Workflow Adjustment Logic)

---

## Notes

- **C5 Fix Applied**: Performance target revised from <100ms to <500ms (realistic)
- Context caching critical for performance
- Simple keyword extraction sufficient (no ML needed)
- Graceful degradation when no learnings found

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `ARCHITECTURE.md` (Component 2)
- Critical Fixes: `CRITICAL_FIXES.md` (C5)
- Epic 29: `epics/epic-29-self-learning-feedback-loop.md`
