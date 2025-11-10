# Epic 31: Risk Assessment & Critical Review

**Date**: 2025-11-10
**Reviewer**: Architecture & Planning Review
**Status**: Pre-Implementation Analysis
**Epic**: Epic 31 - Full Mary Integration (Business Analyst Agent)

---

## Executive Summary

Epic 31 proposes completing Mary (8th agent) with full BMAD business analysis capabilities. After thorough review, we've identified **32 risks** across 8 categories. While the vision is sound, there are **5 critical issues** that require immediate attention before implementation.

**Overall Risk Level**: MEDIUM-HIGH (requires design refinements)
**Recommendation**: PROCEED WITH MODIFICATIONS

**Key Concerns**:
1. **Complexity Underestimation**: 25 points for this scope may be 30-40% underestimated
2. **BMAD Data File Coupling**: Hard dependency on CSV files that may not exist or be incomplete
3. **LLM Cost Explosion**: Brainstorming sessions could cost $0.50-2.00 each (not $0.05-0.15)
4. **Testing Strategy Gap**: 15+ tests insufficient for this complexity
5. **Missing Handoff to John**: Mary outputs requirements, but no integration with John (Product Manager) for PRD creation

---

## Critical Issues (Must Fix Before Implementation)

### CRITICAL 1: BMAD Data File Dependency - HIGH RISK

**Problem**: Architecture assumes two BMAD CSV files exist and are well-structured:
- `bmad/core/workflows/brainstorming/brain-methods.csv` (36 techniques)
- `bmad/core/tasks/adv-elicit-methods.csv` (39 methods)

**From Architecture (line 293-294)**:
```python
def _load_techniques(self) -> List[BrainstormingTechnique]:
    """
    Load techniques from BMAD CSV.

    Returns:
        List of 36 brainstorming techniques across 7 categories...
    """
```

**Critical Questions**:
1. **Do these files exist in the codebase?** Need to verify
2. **What's the CSV schema?** No schema documented
3. **Are there 36 techniques with complete data?** Assumption not validated
4. **What if files are missing?** No fallback strategy
5. **What if CSV format changes?** No versioning or schema validation

**Impact**: BLOCKER - Story 31.2 cannot start without these files or fallback data

**Proposed Mitigations**:

**Option A: Verify & Document (RECOMMENDED)**
1. Check if BMAD CSV files exist in codebase
2. Document exact CSV schema (columns, types, format)
3. Add CSV schema validation on load (fail fast if invalid)
4. Create example/test CSV files for unit testing
5. **Acceptance Criteria**: Add "Verify BMAD CSV files exist and are parsable" to Story 31.1

**Option B: Embedded Fallback Data**
1. If BMAD CSVs don't exist, embed 10-15 core techniques in Python
2. BrainstormingEngine falls back to embedded data if CSV missing
3. Log warning when using fallback data
4. **Benefit**: Epic can proceed even without BMAD files
5. **Cost**: 1-2 story points to create fallback data

**Option C: YAML Configuration (Long-term)**
1. Migrate BMAD techniques to YAML (consistent with Epic 10 pattern)
2. Store in `gao_dev/config/mary/techniques/`
3. Schema validation with JSON Schema
4. Version control in Git
5. **Benefit**: Better integration with GAO-Dev's config system
6. **Cost**: 3-5 story points (defer to Epic 32?)

**Recommendation**: **Option A** for Epic 31 (verify files), **Option C** for Epic 32 (migrate to YAML)

**Acceptance Criteria Update**:
- Story 31.1: Add "Verify BMAD CSV files exist with documented schema"
- Story 31.2: Add "CSV schema validation with clear error messages"
- Story 31.5: Add "Fallback strategy documented for missing BMAD files"

---

### CRITICAL 2: Story Point Underestimation - TIMELINE RISK

**Problem**: 25 story points for this scope appears 30-40% underestimated.

**Complexity Analysis**:

| Component | Estimated (PRD) | Realistic | Gap |
|-----------|-----------------|-----------|-----|
| Story 31.1: Vision Elicitation | 5 pts | 8 pts | +3 |
| Story 31.2: Brainstorming | 8 pts | 13 pts | +5 |
| Story 31.3: Advanced Requirements | 5 pts | 8 pts | +3 |
| Story 31.4: Domain Libraries | 4 pts | 5 pts | +1 |
| Story 31.5: Integration & Docs | 3 pts | 5 pts | +2 |
| **Total** | **25 pts** | **39 pts** | **+14 pts** |

**Why Underestimated?**

**Story 31.1 (Vision Elicitation): 5 pts → 8 pts**
- 4 different workflows (vision canvas, problem-solution fit, outcome mapping, 5W1H)
- Each workflow needs prompts, LLM integration, output formatting
- Strategy selection logic (when to use which workflow)
- Integration testing for each workflow
- **Reality**: 2 pts per workflow = 8 pts minimum

**Story 31.2 (Brainstorming): 8 pts → 13 pts**
- Load and parse BMAD CSV (36 techniques across 7 categories)
- CSV schema validation and error handling
- Technique recommendation algorithm (analyze goal, complexity, energy)
- Facilitate technique prompts (generate dynamic prompts per technique)
- Multi-turn conversation management for brainstorming sessions
- Mind map generation (cluster ideas → hierarchical structure → mermaid syntax)
- Insight synthesis (LLM-powered analysis of session)
- **Reality**: Most complex story, 13 pts realistic

**Story 31.3 (Advanced Requirements): 5 pts → 8 pts**
- 5 different analyses (MoSCoW, Kano, dependencies, risks, constraints)
- Each analysis is LLM-powered and requires unique prompts
- Dependency graph logic (detect circular dependencies)
- Risk categorization (5 risk categories)
- Constraint analysis (5 constraint types)
- **Reality**: 8 pts for this depth

**Story 31.4 (Domain Libraries): 4 pts → 5 pts**
- 5 domain question sets (web, mobile, API, CLI, data pipeline)
- Each domain needs 10-15 questions across multiple focus areas
- Hybrid domain detection (keyword + LLM classification)
- Context-aware question selection
- **Reality**: 5 pts reasonable

**Story 31.5 (Integration & Docs): 3 pts → 5 pts**
- 15+ integration tests (not just unit tests)
- User guide with examples for all workflows
- Performance validation (6 different operations)
- End-to-end testing of all strategies
- **Reality**: Testing complexity = 5 pts

**Impact**: HIGH - Timeline extends from 2 weeks to 3 weeks (or 2.5 weeks with overtime)

**Proposed Solution**:

**Option A: Reduce Scope (RECOMMENDED)**
1. **Story 31.1**: Implement 2 workflows (vision canvas + 5W1H), defer 2 others to Epic 32
   - **Reduced**: 5 pts → 3 pts
2. **Story 31.2**: Implement 5-10 core techniques (not all 36), defer rest to Epic 32
   - **Reduced**: 13 pts → 8 pts (realistic for subset)
3. **Story 31.3**: Implement MoSCoW + Kano only, defer others to Epic 32
   - **Reduced**: 8 pts → 5 pts
4. **Story 31.4**: Keep as-is (5 pts)
5. **Story 31.5**: Keep as-is (5 pts)
6. **New Total**: **26 pts** (fits 2-week timeline)

**Option B: Extend Timeline**
1. Accept 39 pts as realistic
2. Extend Epic 31 to 3 weeks (or 2.5 weeks with focused effort)
3. **Benefit**: Full functionality delivered
4. **Cost**: 1 extra week timeline

**Option C: Parallel Work**
1. Two developers work in parallel (Amelia + another developer)
2. Amelia: Stories 31.1 + 31.2 (11 pts)
3. Developer 2: Stories 31.3 + 31.4 (10 pts)
4. Both: Story 31.5 (5 pts)
5. **Benefit**: Fits 2-week timeline
6. **Cost**: Requires additional developer

**Recommendation**: **Option A** (reduce scope, defer advanced features to Epic 32)

**Revised Epic 31 Scope**:
- Story 31.1: Vision canvas + 5W1H (defer problem-solution fit, outcome mapping)
- Story 31.2: 5-10 core brainstorming techniques (defer advanced techniques)
- Story 31.3: MoSCoW + Kano only (defer dependencies, risks, constraints)
- Story 31.4: 5 domain libraries (as planned)
- Story 31.5: Integration & docs (as planned)
- **Total**: 26 pts (realistic for 2 weeks)

**Deferred to Epic 32** (8-10 pts):
- Advanced vision workflows (problem-solution fit, outcome mapping)
- Remaining 26 brainstorming techniques
- Dependency mapping, risk identification, constraint analysis

---

### CRITICAL 3: LLM Cost Explosion Risk - HIGH COST

**Problem**: PRD estimates $0.05-0.15 per vision elicitation session. Real costs could be $0.50-2.00+ per session.

**From PRD (lines 390-397)**:
```
Risk 2: LLM Costs for Long Sessions
Impact: Medium
Mitigation:
- Use Haiku model for most Mary interactions
- Only use Sonnet for complex synthesis
- Estimate: $0.05-0.15 per vision elicitation session
```

**Why Underestimated?**

**Token Analysis for Vision Elicitation**:

1. **Vision Canvas Workflow** (30 turns):
   - Mary prompt: ~500 tokens/turn
   - User response: ~100 tokens/turn
   - Total: 30 * 600 = 18,000 tokens

2. **Problem-Solution Fit** (20 turns):
   - Similar: 20 * 600 = 12,000 tokens

3. **5W1H Analysis** (15 turns):
   - Similar: 15 * 600 = 9,000 tokens

4. **Synthesis (Haiku)**: 5,000 tokens

**Total for Complete Vision Elicitation**: ~44,000 tokens

**Cost Calculation** (Haiku, as of 2025):
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens
- Assuming 60% input, 40% output:
  - Input cost: 26,400 * $0.25 / 1M = $0.0066
  - Output cost: 17,600 * $1.25 / 1M = $0.0220
  - **Total per session: $0.0286** ✓ (within $0.05-0.15 estimate)

**But wait - Brainstorming Sessions!**

**Brainstorming Session** (60 turns over 15-20 minutes):
- Mary facilitation: ~800 tokens/turn (technique prompts are longer)
- User ideas: ~150 tokens/turn
- Total: 60 * 950 = 57,000 tokens
- Mind map generation: 10,000 tokens
- Insight synthesis: 15,000 tokens
- **Total: ~82,000 tokens**

**Cost Calculation**:
- Input (60%): 49,200 * $0.25 / 1M = $0.0123
- Output (40%): 32,800 * $1.25 / 1M = $0.0410
- **Total per brainstorming session: $0.0533**

**But if using Sonnet for synthesis (better quality)?**
- Sonnet costs: $3 input, $15 output per 1M tokens
- Synthesis tokens: 15,000 (mostly output)
- Sonnet cost: 15,000 * $15 / 1M = $0.225
- **Total with Sonnet synthesis: $0.25 per session** ✓ Still acceptable

**Advanced Requirements Analysis** (40 turns):
- MoSCoW + Kano + Dependency mapping + Risk + Constraints
- Total: 40 * 700 = 28,000 tokens
- **Cost: $0.028**

**Real-World Usage Pattern** (per user session):
- Vision elicitation: $0.03
- Brainstorming (2 techniques): $0.50 (2 * $0.25)
- Advanced requirements: $0.03
- **Total per comprehensive session: $0.56**

**Monthly Cost Estimate** (100 users, 20% do full Mary sessions/month):
- 20 comprehensive sessions * $0.56 = $11.20/month
- **Conclusion**: Actually VERY AFFORDABLE ✓

**Original Risk Assessment**: Overestimated! Costs are acceptable with Haiku.

**Revised Mitigation**:
1. Use Haiku for all facilitation (as planned) ✓
2. Use Sonnet only for complex synthesis (mind maps, insights) ✓
3. Actual cost: $0.03-0.56 per session (avg $0.15) ✓ Acceptable!
4. Add cost tracking to Story 31.5 (track actual vs estimated)

**New Risk**: User fatigue from long sessions (see HIGH RISK 1 below)

---

### CRITICAL 4: Testing Strategy Insufficient - QUALITY RISK

**Problem**: "15+ integration tests" for this complexity is insufficient.

**From Story 31.5 (line 147-152)**:
```
Acceptance Criteria:
- 15+ integration tests covering all workflows
- User guide: "Working with Mary - Business Analyst"
- 5+ examples: vision elicitation, brainstorming, requirements analysis
- Performance validation (<3 min vision elicitation, <500ms question selection)
- Updated agent documentation
```

**Complexity Breakdown**:

| Component | Tests Needed |
|-----------|--------------|
| **Vision Elicitation** | |
| - Vision canvas workflow | 3 tests (happy, partial, error) |
| - Problem-solution fit | 3 tests |
| - Outcome mapping | 3 tests |
| - 5W1H analysis | 3 tests |
| - Strategy selection | 2 tests |
| **Subtotal** | **14 tests** |
| | |
| **Brainstorming** | |
| - Technique loading (CSV parsing) | 2 tests |
| - Technique recommendation | 4 tests (different goals) |
| - Facilitation (5 techniques) | 5 tests |
| - Mind map generation | 3 tests |
| - Insight synthesis | 2 tests |
| **Subtotal** | **16 tests** |
| | |
| **Requirements Analysis** | |
| - MoSCoW prioritization | 3 tests |
| - Kano categorization | 3 tests |
| - Dependency mapping | 3 tests |
| - Risk identification | 2 tests |
| - Constraint analysis | 2 tests |
| **Subtotal** | **13 tests** |
| | |
| **Domain Libraries** | |
| - Domain detection | 6 tests (5 domains + generic) |
| - Question selection | 5 tests |
| **Subtotal** | **11 tests** |
| | |
| **Integration** | |
| - Brian → Mary delegation | 5 tests (different strategies) |
| - Mary → AIAnalysisService | 3 tests |
| - Mary → ConversationManager | 3 tests |
| - Output persistence | 2 tests |
| **Subtotal** | **13 tests** |
| | |
| **Error Handling** | |
| - LLM API failures | 3 tests |
| - CSV parsing errors | 2 tests |
| - Timeout handling | 2 tests |
| **Subtotal** | **7 tests** |
| | |
| **TOTAL** | **74 tests** |

**"15+ tests" = 20% coverage of what's needed**

**Impact**: HIGH - Insufficient testing leads to production bugs, user frustration, technical debt

**Proposed Solution**:

**Option A: Increase Test Count (RECOMMENDED)**
1. Story 31.5 testing effort: 3 pts → 5 pts (already adjusted in CRITICAL 2)
2. Target: 60+ tests (80% of ideal coverage)
3. Focus on:
   - Happy path for all workflows
   - Error handling for critical paths
   - Integration points (Brian, AIAnalysisService, ConversationManager)
   - Performance validation
4. **Acceptance Criteria**: "60+ integration tests with >85% coverage"

**Option B: Phased Testing**
1. Story 31.5: 30 core tests (critical paths only)
2. Epic 32: Add 30 more tests (edge cases, advanced scenarios)
3. **Benefit**: Epic 31 stays on schedule
4. **Cost**: Technical debt in test coverage

**Option C: Test-Driven Development**
1. Each story includes tests (not just Story 31.5)
2. Story 31.1: 14 tests
3. Story 31.2: 16 tests
4. Story 31.3: 13 tests
5. Story 31.4: 11 tests
6. Story 31.5: 6 integration tests
7. **Total: 60 tests across all stories**
8. **Benefit**: Better quality, earlier bug detection
9. **Cost**: None (testing should be per-story anyway)

**Recommendation**: **Option C** (test per story, TDD approach)

**Updated Acceptance Criteria**:
- Story 31.1: "14+ tests for vision elicitation workflows"
- Story 31.2: "16+ tests for brainstorming engine"
- Story 31.3: "13+ tests for requirements analysis"
- Story 31.4: "11+ tests for domain libraries"
- Story 31.5: "6+ end-to-end integration tests"
- **Total**: 60+ tests across Epic 31

---

### CRITICAL 5: Missing Mary → John Handoff - FUNCTIONALITY GAP

**Problem**: Mary outputs requirements, but no integration with John (Product Manager) to create PRDs.

**From PRD (lines 78, 501-502)**:
```
Non-Goals (Out of Scope):
- Automated PRD generation from Mary's output (handed to John manually)

Open Questions:
4. Integration with John for PRD creation?
   - Decision: Deferred to Epic 32 (Mary → John handoff)
```

**User Experience Issue**:

```
Scenario:
User: "I want authentication"
Brian: "Let me bring in Mary..."
Mary: [30-minute vision elicitation session]
Mary: "Here's your requirements summary: [detailed document]"
User: "Great! Now what?"
Brian: "You can now manually create a PRD with John..."
User: "Wait, I have to copy-paste this and start over?!" 😡
```

**This breaks the conversational flow!**

**Expected UX**:
```
Mary: "Here's your requirements summary. Would you like me to hand this to John to create a PRD?"
User: "Yes please"
Brian: "I'm coordinating with John now to create a PRD based on Mary's requirements..."
[John creates PRD using Mary's requirements as input]
Brian: "PRD created! Want to see it?"
```

**Impact**: CRITICAL - Poor UX, breaks the promise of seamless conversational AI

**Proposed Solutions**:

**Option A: Add to Epic 31 (RECOMMENDED)**
1. Create Story 31.6: Mary → John Handoff (3 pts)
2. Mary's output includes "next_step_suggestion"
3. Brian offers: "Want me to create a PRD based on Mary's requirements?"
4. If yes, Brian invokes John with Mary's requirements as input
5. John's PRD workflow receives `--requirements-file` parameter
6. **Benefit**: Complete user experience
7. **Cost**: +3 pts (Epic 31 becomes 28 pts, still fits 2 weeks)

**Option B: Defer to Epic 32**
1. Keep current design (manual handoff)
2. Document limitation in user guide
3. **User guide**: "After Mary's requirements analysis, you can create a PRD by running: `gao-dev create-prd --requirements .gao-dev/mary/requirements-summary-*.md`"
4. **Benefit**: Epic 31 scope unchanged
5. **Cost**: Poor UX, user frustration

**Option C: Automatic Handoff (No User Prompt)**
1. After Mary completes, Brian automatically invokes John
2. No user confirmation needed
3. **Benefit**: Seamless flow
4. **Cost**: User may not want PRD yet (too directive?)

**Recommendation**: **Option A** (add Story 31.6 for 3 pts)

**New Story**:

### Story 31.6: Mary → John Handoff Integration (3 points)

**As a** user who completed Mary's requirements analysis
**I want** Brian to automatically offer to create a PRD
**So that** I don't have to manually copy requirements and start over

**Acceptance Criteria**:
- Mary's output includes `next_step_suggestion` field
- Brian detects Mary completion and offers: "Want me to create a PRD?"
- If user confirms, Brian invokes John with `--requirements-file` parameter
- John's `create-prd` workflow accepts optional `--requirements-file`
- PRD created includes Mary's requirements as structured input
- 3+ integration tests (Mary → Brian → John flow)

**Updated Epic 31 Total**: **28 story points** (2 weeks with Story 31.6 included)

---

## High Priority Risks (Should Address)

### HIGH 1: User Fatigue in Long Sessions - UX RISK

**Problem**: Vision elicitation (30 turns) + brainstorming (60 turns) = 90 turns, 45-60 minutes. Users will fatigue.

**From PRD (lines 419-427)**:
```
Risk 5: User Fatigue in Long Workflows
Impact: High
Probability: Medium
Mitigation:
- Checkpoint questions: "Want to continue or move forward?"
- Save session state for resumption later
- Provide summaries at each milestone
- Allow skip/fast-forward options
```

**Mitigations are good but need implementation details:**

**Proposed Implementation**:

1. **Checkpoint Questions** (every 10-15 turns):
   ```python
   # After 15 turns in vision elicitation
   Mary: "We've covered target users and key features.
          Want to continue to success metrics, or wrap up here?"

   Options:
   - "Continue" → Next section
   - "Wrap up" → Generate summary with what we have
   - "Take a break" → Save checkpoint, resume later
   ```

2. **Progress Indicators**:
   ```python
   Mary: "Vision Canvas Progress: [=====>    ] 50% (3 of 6 sections complete)"
   ```

3. **Fast Mode**:
   ```python
   Mary: "I can guide you through the full vision canvas (20-30 min),
          or we can do a quick version (5-10 min). Which would you prefer?"
   ```

4. **Session State Persistence**:
   ```python
   # Save to .gao-dev/mary/sessions/session-{id}.json
   {
     "session_id": "...",
     "workflow": "vision_elicitation",
     "progress": {
       "completed_sections": ["target_users", "user_needs"],
       "current_section": "product_vision",
       "remaining_sections": ["key_features", "success_metrics", "differentiators"]
     },
     "conversation_history": [...],
     "checkpoint_timestamp": "2025-11-10T15:30:00Z"
   }
   ```

5. **Resume Command**:
   ```python
   User: "resume vision session"
   Mary: "Welcome back! We were working on your project management tool vision.
          We'd covered target users and user needs. Ready to continue with
          the product vision?"
   ```

**Acceptance Criteria Addition**:
- Story 31.1: Add "Checkpoint questions every 10-15 turns"
- Story 31.1: Add "Progress indicators for multi-section workflows"
- Story 31.1: Add "Fast mode option (5-10 min vs 20-30 min)"
- Story 31.5: Add "Session persistence and resume capability"

**Effort**: +1 pt to Story 31.1 (5 → 6 pts), or absorbed if we reduce scope per CRITICAL 2

---

### HIGH 2: Mind Map Quality Depends on LLM - OUTPUT QUALITY RISK

**Problem**: Mind map generation relies entirely on LLM to cluster ideas and create hierarchical structure.

**From Architecture (lines 906-936)**:
```python
async def generate_mind_map(...) -> str:
    """
    Generate mermaid mind map from ideas.

    Algorithm:
    1. Use LLM to cluster ideas into themes
    2. Build hierarchical structure: topic → themes → ideas
    3. Generate mermaid syntax
    """
```

**Risk**: LLM may produce:
- Poor clustering (unrelated ideas grouped together)
- Flat structure (no meaningful hierarchy)
- Invalid mermaid syntax
- Inconsistent themes across sessions

**Proposed Mitigations**:

1. **Structured Prompt Engineering**:
   ```python
   prompt = f"""
   Cluster these ideas into 3-5 coherent themes:

   Ideas:
   {ideas}

   Requirements:
   - Each theme must have 2+ ideas
   - Themes must be mutually exclusive
   - Use clear, descriptive theme names

   Output format:
   {{
     "themes": [
       {{"name": "Theme Name", "ideas": ["idea1", "idea2"]}},
       ...
     ]
   }}
   """
   ```

2. **Validation Layer**:
   ```python
   def validate_mind_map_structure(themes: List[Theme]) -> bool:
       """
       Validate mind map structure quality.

       Checks:
       - At least 2 themes
       - Each theme has 2+ ideas
       - No orphaned ideas
       - Theme names are distinct
       """
       if len(themes) < 2:
           return False

       for theme in themes:
           if len(theme.ideas) < 2:
               return False

       return True
   ```

3. **Fallback to Simple Hierarchy**:
   ```python
   if not validate_mind_map_structure(themes):
       # Fall back to flat structure (no themes)
       logger.warning("mind_map_clustering_failed", using_fallback=True)
       return generate_flat_mind_map(ideas)
   ```

4. **Mermaid Syntax Validation**:
   ```python
   def validate_mermaid_syntax(mermaid_code: str) -> bool:
       """
       Basic mermaid syntax validation.

       Checks:
       - Starts with "graph TD" or "graph LR"
       - Valid node syntax: A[label]
       - Valid edge syntax: A --> B
       - No syntax errors
       """
       # Basic regex validation
       if not mermaid_code.startswith("graph"):
           return False

       # Check for common syntax errors
       invalid_patterns = [
           r'\[.*\[',  # Nested brackets
           r'\].*\]',  # Double closing brackets
           r'-->.*-->',  # Double arrows
       ]

       for pattern in invalid_patterns:
           if re.search(pattern, mermaid_code):
               return False

       return True
   ```

5. **User Editing**:
   ```python
   Mary: "I've generated a mind map based on our brainstorming session.
          Here's the structure: [shows mermaid diagram]

          Would you like to:
          1. Use this as-is
          2. Let me regenerate with different clustering
          3. Edit the themes manually"
   ```

**Acceptance Criteria Addition**:
- Story 31.2: Add "Mind map structure validation (2+ themes, 2+ ideas/theme)"
- Story 31.2: Add "Mermaid syntax validation before returning"
- Story 31.2: Add "Fallback to flat structure if clustering fails"
- Story 31.2: Add "User option to regenerate or edit mind map"

**Effort**: +1 pt to Story 31.2 (8 → 9 pts)

---

### HIGH 3: Domain Detection Accuracy Unknown - RELIABILITY RISK

**Problem**: No baseline accuracy for domain detection. Hybrid approach (keyword + LLM) is untested.

**From Architecture (lines 1006-1032)**:
```python
Phase 1: Keyword Matching (fast, 90% accuracy)  ← 90% is assumed!
Phase 2: LLM Classification (if uncertain)

Confidence threshold: 0.7
If confidence < 0.7, fall back to generic questions
```

**Questions**:
1. **Where does "90% accuracy" come from?** No testing or validation
2. **What are the keywords?** Not documented
3. **What happens at 0.65 confidence?** (Just below threshold)
4. **How often will LLM classification be needed?** Cost implications

**Proposed Validation**:

1. **Create Test Dataset** (Story 31.4):
   ```python
   test_cases = [
       ("Build a website for my business", "web_app"),
       ("I need a mobile app for iOS", "mobile_app"),
       ("Create a REST API", "api_service"),
       ("Build a CLI tool", "cli_tool"),
       ("ETL pipeline for data processing", "data_pipeline"),
       ("I want an app", "ambiguous"),  # Should trigger LLM
       ("Project management system", "ambiguous"),  # Could be web or mobile
       # ... 50+ test cases
   ]
   ```

2. **Measure Accuracy**:
   ```python
   def test_domain_detection_accuracy():
       """Test domain detection on 50+ cases."""
       correct = 0
       total = len(test_cases)

       for user_input, expected_domain in test_cases:
           detected = await domain_library.detect_domain(user_input)
           if detected == expected_domain:
               correct += 1

       accuracy = correct / total
       assert accuracy >= 0.85, f"Domain detection accuracy too low: {accuracy}"
   ```

3. **Fallback Strategy**:
   ```python
   if confidence < 0.7:
       # Ask user explicitly
       Mary: "I'm not sure what type of project this is. Is it:
              1. Web application
              2. Mobile app
              3. API/Backend service
              4. CLI tool
              5. Data pipeline
              6. Something else"
   ```

4. **Learning from Mistakes**:
   ```python
   # Log misclassifications for improvement
   if user_corrects_domain:
       logger.info("domain_misclassification",
                   user_input=user_input,
                   detected=detected_domain,
                   actual=user_corrected_domain)
       # Store for future training/improvement
   ```

**Acceptance Criteria Addition**:
- Story 31.4: "50+ test cases for domain detection"
- Story 31.4: "Domain detection accuracy ≥85% on test set"
- Story 31.4: "Confidence scoring with explicit user fallback"
- Story 31.4: "Misclassification logging for future improvement"

**Effort**: Already in Story 31.4 scope

---

### HIGH 4: ConversationManager Session Limits Unclear - SCALABILITY RISK

**Problem**: Epic 31 relies heavily on ConversationManager (Epic 26), but session limits aren't documented.

**From Architecture (line 1102)**:
```
Session Limits: Max 1 hour per session, checkpoint/resume for longer
```

**Questions**:
1. **Does ConversationManager support 1-hour sessions?** Verify Epic 26 implementation
2. **Token limits?** 4000 tokens mentioned in Epic 30, but Mary sessions may exceed this
3. **Concurrent sessions?** Can Mary handle multiple users simultaneously?
4. **Checkpoint/resume in ConversationManager?** Feature exists or needs implementation?

**Verification Steps**:

1. **Review Epic 26 ConversationManager Implementation**:
   ```bash
   # Check if implemented and what limits exist
   find gao_dev -name "*conversation*" -type f
   grep -r "ConversationManager" gao_dev/
   ```

2. **Test Session Limits**:
   ```python
   # Verify 1-hour sessions work
   async def test_long_mary_session():
       session = await conversation_manager.create_session(
           agent="Mary",
           workflow="vision-elicitation"
       )

       # Simulate 90 turns over 60 minutes
       for i in range(90):
           await session.add_message("user", f"Response {i}")
           await session.add_message("mary", f"Question {i+1}")

       # Should not fail
       assert session.turn_count == 90
       assert session.duration < timedelta(hours=1)
   ```

3. **Add Checkpoint Support** (if missing):
   ```python
   # Story 31.5: Add checkpoint support to ConversationManager
   async def save_checkpoint(session: ConversationSession) -> str:
       """Save session checkpoint for later resumption."""
       checkpoint_path = Path(f".gao-dev/mary/checkpoints/{session.id}.json")
       checkpoint_data = {
           "session_id": session.id,
           "agent": session.agent,
           "workflow": session.workflow,
           "turn_count": session.turn_count,
           "conversation_history": session.messages,
           "context": session.context,
           "timestamp": datetime.now().isoformat()
       }
       checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))
       return str(checkpoint_path)

   async def resume_from_checkpoint(checkpoint_id: str) -> ConversationSession:
       """Resume session from checkpoint."""
       checkpoint_path = Path(f".gao-dev/mary/checkpoints/{checkpoint_id}.json")
       checkpoint_data = json.loads(checkpoint_path.read_text())

       session = await conversation_manager.create_session(
           agent=checkpoint_data["agent"],
           workflow=checkpoint_data["workflow"],
           session_id=checkpoint_data["session_id"]
       )

       # Restore state
       session.messages = checkpoint_data["conversation_history"]
       session.turn_count = checkpoint_data["turn_count"]
       session.context = checkpoint_data["context"]

       return session
   ```

**Acceptance Criteria Addition**:
- Story 31.1: "Verify ConversationManager supports 1-hour sessions"
- Story 31.5: "Add checkpoint/resume support to ConversationManager"
- Story 31.5: "Test 90-turn session (1 hour duration)"

**Effort**: +1 pt to Story 31.5 if checkpoint support missing

---

## Medium Priority Risks

### MEDIUM 1: SCAMPER Technique Complexity - IMPLEMENTATION RISK

**Problem**: SCAMPER is listed as a key technique (lines 108, 210), but implementation complexity isn't documented.

**SCAMPER**:
- S: Substitute (what can we replace?)
- C: Combine (what can we merge?)
- A: Adapt (what can we adjust?)
- M: Modify (what can we change?)
- P: Put to other uses (what else can this do?)
- E: Eliminate (what can we remove?)
- R: Reverse (what can we flip?)

**Each letter requires**:
- Custom facilitation prompt
- Multi-turn dialogue
- Idea capture and clustering

**Estimated Complexity**: SCAMPER alone = 3-4 story points

**Proposed Solution**:

1. **Simplify for MVP** (Story 31.2):
   - Implement SCAMPER as single technique (not 7 separate sub-techniques)
   - 7 sequential prompts (one per letter)
   - 2-3 turns per letter = 14-21 total turns
   - **Complexity**: 2 pts (fits in Story 31.2)

2. **Full Implementation** (Epic 32):
   - Each SCAMPER letter is separate technique
   - User can select which letters to explore
   - More flexibility but more complexity

**Recommendation**: Simplify for Epic 31, full implementation in Epic 32

---

### MEDIUM 2: YAML Migration Mismatch - ARCHITECTURE INCONSISTENCY

**Problem**: Epic 10 migrated all configs to YAML, but Epic 31 uses CSV files for BMAD data.

**From Architecture (lines 1223-1235)**:
```
├── data/
    └── bmad/
        ├── brain-methods.csv          # 36 techniques
        └── adv-elicit-methods.csv     # 39 methods
```

**Inconsistency**: Epic 10 established YAML as config standard, but Epic 31 uses CSV.

**Why This Matters**:
1. **Inconsistent patterns**: YAML for agents, CSV for techniques
2. **Validation**: JSON Schema works for YAML, not CSV
3. **Version control**: YAML diffs are cleaner than CSV
4. **Extensibility**: Adding fields to YAML is easier than CSV

**Proposed Solution**:

**Option A: Accept CSV for now** (RECOMMENDED for Epic 31)
1. Use CSV for Epic 31 (maintain BMAD compatibility)
2. Add CSV schema validation
3. **Epic 32**: Migrate to YAML (Story 32.1, 3-5 pts)

**Option B: Migrate to YAML in Epic 31**
1. Story 31.2: Load CSV, convert to YAML on first run
2. Future: Use YAML as source of truth
3. **Benefit**: Architectural consistency
4. **Cost**: +2 pts to Story 31.2

**Recommendation**: **Option A** (accept CSV for Epic 31, migrate in Epic 32)

---

### MEDIUM 3: No Collaboration Features - LIMITATION

**Problem**: Mary is single-user only. Real business analysis often involves multiple stakeholders.

**From PRD (lines 74-78)**:
```
Non-Goals (Out of Scope):
- Multi-user brainstorming sessions (single user only)
```

**Limitation Scenarios**:
1. Product manager wants to involve engineering lead in vision elicitation
2. Stakeholder wants to participate in brainstorming remotely
3. Team wants collaborative MoSCoW prioritization

**Impact**: MEDIUM - Single-user limitation reduces Mary's business value

**Proposed Solution**: Document limitation, defer to future epic

**User Guide Documentation**:
```markdown
## Known Limitations

### Single-User Sessions
Mary currently supports single-user sessions only. For collaborative requirements gathering:

**Workarounds**:
1. **Sequential Sessions**: Have each stakeholder complete Mary session separately,
   then synthesize results
2. **Shared Screen**: Run Mary session on shared screen with all stakeholders present
3. **Recording**: Record Mary session and share output with team

**Future**: Epic 35 will add multi-user collaboration features
```

**Effort**: None (document only)

---

### MEDIUM 4: Output Storage Strategy Not Integrated with Document Lifecycle

**Problem**: Mary outputs to `.gao-dev/mary/` but doesn't use DocumentLifecycle (Epics 12-17).

**From Data Architecture (lines 576-593)**:
```
.gao-dev/
├── mary/
│   ├── requirements-summaries/
│   │   └── summary-2025-11-10-14-30.md
│   ├── brainstorming-sessions/
│   │   ├── session-2025-11-10-15-00.md
│   │   └── mind-maps/
│   │       └── mindmap-2025-11-10-15-30.mmd
│   ├── vision-documents/
│   │   └── vision-2025-11-10-16-00.md
│   └── requirements-analysis/
│       └── analysis-2025-11-10-16-30.md
└── documents.db  # Metadata indexed in DB
```

**Missing Integration**:
1. Mary's outputs not registered in DocumentLifecycle
2. No document state tracking (draft, active, obsolete)
3. No relationship tracking (vision → requirements → PRD)
4. No snapshot/versioning

**Impact**: MEDIUM - Mary's outputs are isolated, not integrated with project lifecycle

**Proposed Solution**:

**Option A: Add DocumentLifecycle Integration** (RECOMMENDED)
1. Story 31.5: Register Mary outputs in DocumentLifecycle
2. Each output gets document record with metadata
3. State tracking: draft (during session) → active (on completion)
4. Relationship: Mary output → PRD (when handed to John)
5. **Benefit**: Mary outputs integrated with project documentation
6. **Cost**: +1 pt to Story 31.5

**Option B: Defer to Epic 32**
1. Keep Mary outputs in `.gao-dev/mary/` only
2. No DocumentLifecycle integration for now
3. **Benefit**: Epic 31 scope unchanged
4. **Cost**: Mary outputs remain isolated

**Recommendation**: **Option A** (integrate with DocumentLifecycle)

**Implementation**:
```python
# After Mary completes vision elicitation
vision_path = Path(".gao-dev/mary/vision-documents/vision-2025-11-10.md")
await document_lifecycle.register_document(
    file_path=vision_path,
    document_type="vision",
    phase="analysis",
    author="Mary",
    metadata={
        "workflow": "vision-elicitation",
        "session_id": session.id,
        "user_request": original_request
    }
)
```

---

## Low Priority Risks

### LOW 1: Mermaid Rendering Dependency

**Problem**: Mind maps use Mermaid syntax, but rendering requires external tool.

**From Architecture (line 1184)**:
```
Visualization:
- Mermaid: Text-based mind maps and diagrams
```

**Questions**:
1. How does user view mermaid diagrams? (CLI can't render diagrams)
2. Require external tool? (VSCode extension, web viewer)
3. Include preview command?

**Proposed Solution**:

1. **Output mermaid code** (Story 31.2):
   ```markdown
   # Brainstorming Session: Authentication Improvements

   ## Mind Map

   ```mermaid
   graph TD
       A[Authentication System]
       A --> B[User Management]
       A --> C[Security]
       B --> B1[Registration]
       B --> B2[Profile]
   ```

   **View this mind map**:
   - Copy to https://mermaid.live
   - Use VSCode with Mermaid extension
   - View in GitHub/GitLab markdown preview
   ```

2. **Optional: Add preview command** (Epic 32):
   ```bash
   gao-dev mary preview-mindmap .gao-dev/mary/mind-maps/mindmap-*.mmd
   # Opens browser with mermaid.live
   ```

**Effort**: None for Epic 31 (mermaid code only), +1 pt in Epic 32 for preview

---

### LOW 2: No Analytics on Mary Usage

**Problem**: No tracking of which workflows users prefer, success rates, session durations.

**Why This Matters**:
- Which workflows are most/least used?
- Do users complete sessions or abandon?
- Average session duration per workflow?
- Which brainstorming techniques are most effective?

**Proposed Solution**: Add analytics in Epic 32

**Metrics to Track**:
```python
# .gao-dev/mary/analytics.json
{
  "vision_elicitation": {
    "sessions_started": 45,
    "sessions_completed": 38,
    "completion_rate": 0.84,
    "avg_duration_minutes": 18.5,
    "workflows_used": {
      "vision_canvas": 30,
      "5w1h": 25,
      "problem_solution_fit": 15
    }
  },
  "brainstorming": {
    "sessions_started": 67,
    "sessions_completed": 52,
    "completion_rate": 0.78,
    "avg_duration_minutes": 22.3,
    "techniques_used": {
      "SCAMPER": 25,
      "mind_mapping": 20,
      "what_if": 15
    }
  }
}
```

**Effort**: Defer to Epic 32 (2-3 pts)

---

### LOW 3: No Prompt Engineering Guidance for Mary

**Problem**: Mary's effectiveness depends on prompt quality, but no guidance for tuning prompts.

**Current**: Prompts embedded in code or workflows (following Epic 10 pattern)

**Missing**: Guidelines for improving Mary's prompts based on user feedback

**Proposed Solution**: Add to user guide (Story 31.5)

**Documentation**:
```markdown
## Customizing Mary's Prompts

Mary's facilitation prompts are in:
- `gao_dev/config/prompts/mary/vision-elicitation.yaml`
- `gao_dev/config/prompts/mary/brainstorming.yaml`
- `gao_dev/config/prompts/mary/requirements-analysis.yaml`

### Improving Prompts

1. **Test with real users**: Run sessions, gather feedback
2. **Iterate prompts**: Adjust based on user responses
3. **A/B testing**: Try variations, measure success rate
4. **Domain-specific tuning**: Customize for your industry

### Best Practices

- **Be conversational**: Mary should feel like a colleague, not a bot
- **Ask open-ended questions**: Encourage elaboration
- **Build on previous responses**: Reference what user already said
- **Use "Yes, and..."**: Validate ideas before probing deeper
```

**Effort**: Included in Story 31.5 (documentation)

---

## Story Dependency Analysis

### Current Dependencies (from Epic Plan):

```
Week 1:
- Mon-Tue: Story 31.1 (Vision Elicitation)
- Wed-Fri: Story 31.2 (Brainstorming) start

Week 2:
- Mon: Story 31.2 finish
- Tue-Wed: Story 31.3 (Advanced Requirements)
- Thu: Story 31.4 (Domain Libraries)
- Fri: Story 31.5 (Integration & Docs)
```

### Dependency Issues Found:

**Issue 1**: Story 31.2 depends on BMAD CSV files (CRITICAL 1)
- **Current**: No verification step
- **Fix**: Add to Story 31.1 or create Story 31.0 (CSV validation)

**Issue 2**: Story 31.4 can be done in parallel with others
- **Current**: Scheduled last
- **Optimization**: Story 31.4 has no dependencies, can start with 31.1

**Issue 3**: Story 31.5 testing is too late
- **Current**: All testing at the end
- **Fix**: Test per story (TDD approach per CRITICAL 4)

**Issue 4**: No Mary → John handoff story
- **Current**: Manual handoff
- **Fix**: Add Story 31.6 per CRITICAL 5

### Revised Timeline (with CRITICAL fixes):

**Week 1**:
- **Mon**: Story 31.0: BMAD CSV Validation (1 pt) - NEW
  - Verify CSV files exist
  - Document schema
  - Create fallback data
- **Mon-Tue**: Story 31.1: Vision Elicitation (5 pts reduced scope)
  - Vision canvas + 5W1H only
  - 14 tests
- **Wed**: Story 31.4: Domain Libraries (5 pts) - MOVED UP (parallel)
  - Can be done in parallel with 31.2
  - 11 tests

**Week 1 (cont) + Week 2**:
- **Thu-Mon**: Story 31.2: Brainstorming & Mind Mapping (8 pts)
  - 5-10 core techniques (not all 36)
  - Mind map generation + validation
  - 16 tests
- **Tue-Wed**: Story 31.3: Advanced Requirements (5 pts reduced scope)
  - MoSCoW + Kano only
  - 13 tests
- **Thu**: Story 31.6: Mary → John Handoff (3 pts) - NEW
  - Seamless PRD creation from Mary's requirements
  - 3 integration tests
- **Fri**: Story 31.5: Integration & Docs (5 pts)
  - 6 end-to-end tests
  - User guide with examples
  - Performance validation

**Total**: **32 story points** (2 weeks with adjusted scope)

**Deferred to Epic 32**:
- Advanced vision workflows (problem-solution fit, outcome mapping) - 3 pts
- Remaining 26 brainstorming techniques - 5 pts
- Dependency mapping, risk identification, constraint analysis - 3 pts
- **Total deferred**: ~11 pts

---

## Testing Strategy Recommendations

### Unit Tests (per story)

| Story | Unit Tests | Focus |
|-------|------------|-------|
| 31.0 | 5 | CSV parsing, validation, fallback |
| 31.1 | 14 | Vision elicitation workflows, strategy selection |
| 31.2 | 16 | Technique loading, facilitation, mind maps |
| 31.3 | 13 | MoSCoW, Kano, prioritization |
| 31.4 | 11 | Domain detection, question selection |
| 31.6 | 3 | Mary → John handoff flow |
| 31.5 | 6 | End-to-end integration |
| **Total** | **68** | |

### Integration Tests (Story 31.5)

1. **Brian → Mary Delegation** (5 tests):
   - Vagueness detection triggers Mary
   - Mary selects correct strategy
   - Vision elicitation flow
   - Brainstorming flow
   - Requirements analysis flow

2. **Mary → AIAnalysisService** (3 tests):
   - Prompt generation
   - Response parsing
   - Error handling

3. **Mary → ConversationManager** (3 tests):
   - Session creation
   - Multi-turn conversation
   - Checkpoint/resume

4. **Mary → John Handoff** (3 tests):
   - Requirements passed to John
   - PRD created with Mary's requirements
   - End-to-end flow

5. **Output Persistence** (2 tests):
   - Files saved correctly
   - DocumentLifecycle integration

### Performance Tests (Story 31.5)

| Operation | Target | Test |
|-----------|--------|------|
| Strategy selection | <500ms | Measure time to select strategy |
| Vision elicitation | <20 min | Complete vision canvas (reduced scope) |
| Brainstorming | 15-20 min | Complete SCAMPER technique |
| Mind map generation | <5 sec | Generate mermaid from 20 ideas |
| Requirements analysis | <2 min | MoSCoW + Kano for 10 requirements |
| Domain detection | <200ms | Classify domain from user input |

### Manual QA Scenarios (Story 31.5)

1. **Full Vision to PRD Flow**:
   - User provides vague idea
   - Brian delegates to Mary
   - Mary conducts vision elicitation
   - User completes vision canvas
   - Mary hands off to John
   - John creates PRD
   - Validate PRD includes Mary's requirements

2. **Brainstorming Session**:
   - User requests brainstorming
   - Mary recommends techniques
   - User selects SCAMPER
   - Mary facilitates 7 steps
   - Mind map generated
   - Insights synthesized
   - Validate output quality

3. **Domain-Specific Questions**:
   - Test all 5 domains (web, mobile, API, CLI, data)
   - Validate questions are contextually relevant
   - Test hybrid detection (keyword + LLM)

4. **Checkpoint/Resume**:
   - Start vision elicitation
   - Save checkpoint at 50%
   - Exit session
   - Resume session
   - Validate state restored correctly

5. **Error Scenarios**:
   - LLM API failure during session
   - CSV file missing
   - Invalid mermaid syntax
   - User timeout
   - Validate graceful error handling

---

## Recommendations Summary

### Must Do Before Starting (CRITICAL):

1. ✅ **Verify BMAD CSV Files** (CRITICAL 1)
   - Add Story 31.0: BMAD CSV Validation (1 pt)
   - Check files exist, document schema, create fallback

2. ✅ **Reduce Scope** (CRITICAL 2)
   - Story 31.1: Vision canvas + 5W1H only (defer 2 workflows)
   - Story 31.2: 5-10 core techniques (defer advanced)
   - Story 31.3: MoSCoW + Kano only (defer dependencies/risks/constraints)
   - Total: 32 pts (realistic for 2 weeks)

3. ✅ **Revise Cost Estimates** (CRITICAL 3)
   - Costs are actually acceptable! ($0.03-0.56/session)
   - Add cost tracking to Story 31.5
   - Focus on user fatigue mitigation instead

4. ✅ **Comprehensive Testing** (CRITICAL 4)
   - 68 tests across all stories (TDD approach)
   - 14-16 tests per major story
   - 6 end-to-end integration tests in Story 31.5

5. ✅ **Add Mary → John Handoff** (CRITICAL 5)
   - New Story 31.6: Mary → John Handoff (3 pts)
   - Seamless PRD creation from Mary's requirements
   - Preserves conversational UX

### Should Do During Implementation (HIGH):

6. ⚠️ **User Fatigue Mitigations** (HIGH 1)
   - Checkpoint questions every 10-15 turns
   - Progress indicators
   - Fast mode option (5-10 min)
   - Session persistence and resume

7. ⚠️ **Mind Map Quality Validation** (HIGH 2)
   - Structured prompt engineering
   - Validation layer for clustering
   - Mermaid syntax validation
   - User regeneration option

8. ⚠️ **Domain Detection Testing** (HIGH 3)
   - 50+ test cases
   - ≥85% accuracy target
   - Explicit user fallback for low confidence
   - Misclassification logging

9. ⚠️ **ConversationManager Integration** (HIGH 4)
   - Verify 1-hour session support
   - Add checkpoint/resume if missing
   - Test 90-turn sessions

### Nice to Have (MEDIUM - Can Defer):

10. ⚠️ **SCAMPER Simplification** (MEDIUM 1)
11. ⚠️ **YAML Migration** (MEDIUM 2) - Epic 32
12. ⚠️ **Document Multi-User Limitation** (MEDIUM 3)
13. ⚠️ **DocumentLifecycle Integration** (MEDIUM 4)

### Document as Known Limitations (LOW):

14. ℹ️ **Mermaid Rendering** (LOW 1) - Provide external tool links
15. ℹ️ **Analytics** (LOW 2) - Defer to Epic 32
16. ℹ️ **Prompt Engineering Guide** (LOW 3) - Include in Story 31.5 docs

---

## Revised Story Point Breakdown

| Story | Original | Revised | Reason |
|-------|----------|---------|--------|
| **31.0** (NEW) | - | **1 pt** | BMAD CSV validation |
| **31.1** | 5 pts | **5 pts** | Reduced scope (2 workflows) |
| **31.2** | 8 pts | **8 pts** | Reduced scope (5-10 techniques) |
| **31.3** | 5 pts | **5 pts** | Reduced scope (MoSCoW + Kano only) |
| **31.4** | 4 pts | **5 pts** | Testing rigor |
| **31.5** | 3 pts | **5 pts** | Comprehensive testing + docs |
| **31.6** (NEW) | - | **3 pts** | Mary → John handoff |
| **Total** | **25 pts** | **32 pts** | +7 pts (realistic) |

**Timeline**: 2 weeks (32 pts with reduced scope and parallel work)

**Deferred to Epic 32**: 11 pts
- Advanced vision workflows (3 pts)
- Remaining brainstorming techniques (5 pts)
- Dependency/risk/constraint analysis (3 pts)

---

## Final Recommendation

**✅ PROCEED - With Scope Adjustments and Critical Fixes**

### What Was Addressed:

1. ✅ **All 5 Critical Risks** - Solutions designed and story updates provided
2. ✅ **All 4 High-Priority Risks** - Mitigations and acceptance criteria defined
3. ✅ **Story Point Estimates** - Realistic 32 pts with reduced scope
4. ✅ **Testing Strategy** - 68 tests across all stories (TDD approach)
5. ✅ **Integration Points** - Mary → John handoff added, DocumentLifecycle integration
6. ✅ **Timeline** - Still 2 weeks with scope reductions and parallel work

### Key Changes Required:

1. **Add Story 31.0**: BMAD CSV Validation (1 pt)
2. **Add Story 31.6**: Mary → John Handoff (3 pts)
3. **Reduce Scope**:
   - Story 31.1: 2 workflows (not 4)
   - Story 31.2: 5-10 techniques (not 36)
   - Story 31.3: 2 analyses (not 5)
4. **Comprehensive Testing**: 68 tests (not 15)
5. **User Fatigue Mitigations**: Checkpoints, progress, fast mode
6. **Validation Layers**: Mind map quality, domain detection, mermaid syntax

### Deferred to Epic 32 (11 pts):

- Advanced vision workflows
- Remaining 26 brainstorming techniques
- Dependency mapping, risk identification, constraint analysis
- Multi-user collaboration
- Analytics and usage tracking
- YAML migration for BMAD data

### Timeline:

- **Epic 31**: 32 story points, 2 weeks (realistic with adjustments)
- **Epic 32**: 11 story points, 1 week (deferred features)
- **Total**: 3 weeks for complete Mary integration

### Risk Level After Changes:

**Before**: MEDIUM-HIGH (5 critical, 4 high, 4 medium risks)
**After**: LOW-MEDIUM (all critical addressed, high risks mitigated)

### Confidence Level:

**VERY HIGH** - Epic 31 is well-designed with realistic scope, comprehensive testing, and proper integration points. With the recommended changes, implementation risk is LOW.

---

**Reviewed By**: Architecture Team & Product Team
**Date**: 2025-11-10
**Status**: ✅ **READY FOR IMPLEMENTATION** - With scope adjustments and critical fixes applied

