# Epic 30: Risk Assessment & Critical Review

**Date**: 2025-11-10
**Reviewer**: Architecture & Planning Review
**Status**: Pre-Implementation Analysis

---

## Executive Summary

Epic 30 is well-designed overall, but we've identified **25 risks** across 7 categories that need attention before implementation. Most are **medium severity** and addressable with specific mitigations. **4 critical issues** require immediate design changes.

**Overall Risk Level**: MEDIUM (manageable with mitigations)
**Recommendation**: PROCEED with modifications

---

## Critical Issues (Must Fix Before Implementation)

### ✅ CRITICAL 1: User Confirmation Flow Not Fully Designed - RESOLVED

**Original Problem**: Story 30.3 said "asks for user confirmation before executing workflows" but the mechanism was unclear.

**Root Cause Discovered**: This revealed a **fundamental architecture issue** - GAO-Dev was missing the 8th BMAD agent (Mary - Business Analyst). Without Mary, Brian would create PRDs from vague requests without proper requirements clarification.

---

### **IMPLEMENTED SOLUTION** ✅

**Paradigm Shift**: Changed from "permission-seeking Brian" to "**directive Brian with Mary for clarification**"

#### 1. **Added Mary (Business Analyst)** - The Missing 8th Agent

**Story 30.8: Minimal Mary Integration** (5 pts)
- Basic requirements clarification (4-5 questions)
- Vagueness detection via LLM
- Brian delegates vague requests to Mary automatically
- Mary generates requirements summary
- Brian proceeds with clear requirements

**Epic 31: Full Mary Integration** (25 pts, 2 weeks)
- Complete BMAD business analyst workflows
- Vision elicitation (canvas, problem-solution fit, 5W1H)
- Brainstorming & mind mapping (36 techniques)
- Advanced requirements analysis (MoSCoW, Kano, dependencies)
- Domain-specific question libraries (web, mobile, API, CLI, data)

#### 2. **Directive Brian Architecture**

Brian is now **directive, not permission-seeking**:

```python
# OLD (Permission-Based) ❌
Brian: "I recommend creating a PRD. Shall I proceed?"
[Waits for yes/no]

# NEW (Directive) ✅
Brian: "To build authentication, we need a PRD first."
Brian: "I'm coordinating with John (Product Manager) now..."
[2-second interruption window]
[Proceeds automatically if no interruption]
```

User can interrupt:
```python
User: "wait"  # Brian stops
User: "skip the PRD"  # Brian adjusts plan
User: "why do we need a PRD?"  # Brian explains, then continues
```

#### 3. **LLM-Powered Intent Detection**

Replaced keyword matching with AIAnalysisService (from Epic 21):

```python
class IntentAnalyzer:
    """Uses LLM to understand user intent in context."""

    async def analyze_intent(self, user_input: str, context: ConversationContext):
        # Analyzes:
        # - new_request, interruption, refinement, question, confirmation
        # - Confidence score (0.0-1.0)
        # - Extracted parameters
        # Returns IntentAnalysis with reasoning
```

#### 4. **Session State Simplified**

Instead of complex confirmation state machine, track active operations:

```python
class ChatSession:
    def __init__(self, ...):
        self.active_operation: Optional[ActiveOperation] = None  # Simplified!

    async def handle_input(self, user_input: str):
        if self.active_operation:
            # Treat as potential interruption
            intent = await self.intent_analyzer.analyze_intent(user_input, context)
            if intent.is_interruption:
                await self._handle_interruption(intent)
        else:
            # Normal new request
            await self._handle_normal_input(user_input)
```

#### 5. **Requirements Clarity Flow**

```
User: "I want authentication"  (vague)
    ↓
Brian detects vagueness_score > 0.6
    ↓
Brian: "Bringing in Mary (Business Analyst)..."
    ↓
Mary: "Who needs to authenticate?"
Mary: "What about password requirements?"
[4-5 clarifying questions via LLM]
    ↓
Mary generates requirements summary
    ↓
Brian: "Thanks! Here's the clarified plan..."
Brian: "I'm creating the PRD now..."
[2-second interruption window]
    ↓
PRD created with accurate requirements ✅
```

---

### **Changes Made**

**Epic 30 Updates**:
- Added Story 30.8: Minimal Mary Integration (+5 pts)
- Updated Story 30.3: LLM-powered intent detection (not keyword matching)
- Updated Story 30.5: Active operation tracking (not pending confirmation)
- New Total: **47 story points** (3 weeks)

**Epic 31 Created**:
- Full Mary with BMAD workflows
- 5 stories, **25 story points** (2 weeks)
- Completes the 8th agent

**Architecture Changes**:
- Brian is directive (proceeds with 2s interruption window)
- Mary handles all requirements clarification
- LLM-powered intent detection everywhere (Haiku for speed)
- Interruption > Confirmation (better UX)

---

### **Design Decisions**

1. **Interruption Window**: 2 seconds (user can type "wait")
2. **Brian's Tone**: Directive after Mary clarifies (not permission-seeking)
3. **LLM Usage**: All the time (local models like Haiku for cost)
4. **Timeout**: 5 minutes → "Are you still there?" → auto-cancel
5. **Ambiguous Responses**: LLM probes for clarification

---

### **Impact**:
- **Positive**: Better UX (directive flow), proper requirements analysis (Mary), LLM intelligence
- **Story Points**: +10 pts total (+5 for Story 30.8, +5 for complexity in 30.3/30.5)
- **Timeline**: +1 week (Epic 30 now 3 weeks)
- **Completeness**: GAO-Dev now has all 8 BMAD agents ✅

**Status**: ✅ **RESOLVED** - Architecture redesigned, stories updated
**Effort**: 10 story points added to Epic 30, Epic 31 created (25 pts)

---

### ✅ CRITICAL 2: Streaming Workflow Output Integration - RESOLVED

**Original Problem**: Workflows yield progress messages. How do these integrate with Brian's conversational responses?

---

### **IMPLEMENTED SOLUTION** ✅

**Design Decision**: BrianResponse type system with Rich CLI formatting, error recovery, and state persistence

#### 1. **Response Type System with Rich CLI**

Implemented 11 response types with agent-specific colors:

```python
class ResponseType(Enum):
    BRIAN_INTRO = "brian_intro"           # Brian's initial analysis
    BRIAN_COMMENTARY = "brian_commentary"  # Brian explaining what's happening
    BRIAN_CONCLUSION = "brian_conclusion"  # Brian wrapping up
    BRIAN_QUESTION = "brian_question"      # Brian asking for input
    AGENT_START = "agent_start"            # Agent beginning work
    AGENT_PROGRESS = "agent_progress"      # Agent providing status update
    AGENT_OUTPUT = "agent_output"          # Agent's actual work output
    AGENT_COMPLETE = "agent_complete"      # Agent finished successfully
    ERROR = "error"                        # Error occurred
    WARNING = "warning"                    # Warning/caution
    SUCCESS = "success"                    # Success confirmation

@dataclass
class BrianResponse:
    type: ResponseType
    content: str
    metadata: Dict[str, Any] = None
    agent: Optional[str] = None
    timestamp: Optional[float] = None
```

**Agent Color Scheme**:
- Brian (Workflow Coordinator): Green
- John (Product Manager): Blue
- Winston (Architect): Magenta
- Sally (UX Designer): Cyan
- Bob (Scrum Master): Yellow
- Amelia (Developer): Bright Cyan
- Murat (Test Architect): Bright Yellow
- Mary (Business Analyst): Bright Magenta

**Visual Hierarchy**: Brian's commentary at left margin, agent work indented

#### 2. **Intelligent Error Recovery**

- Automatic retry once on first failure
- AI-powered failure analysis after second failure (using AIAnalysisService from Epic 21)
- Alternative approaches suggested based on error type
- User prompted to choose next action

#### 3. **Progress Tracking for Long Operations**

- Operations >30 seconds show spinner with elapsed time
- Real-time progress updates stream to console
- Current agent and activity visible during execution

#### 4. **State Persistence for Crash Recovery** (CRITICAL)

- Active operations persisted to database immediately on start
- Operation progress updates saved to StateTracker (Epic 15)
- Artifacts tracked as they're created
- Failed/cancelled operations marked with details
- Recovery mode on startup: offers to resume interrupted operations

#### 5. **Integration with Existing Systems**

- StateTracker (Epic 15): Active operation persistence
- DocumentLifecycle (Epic 12): Artifact tracking
- AIAnalysisService (Epic 21): Failure analysis
- GAODevOrchestrator (Epic 27): Command execution

---

### **Changes Made**

**Story 30.4 Updated**: Command Routing & Execution
- Original: 5 story points
- Updated: **11 story points** (+6 points)
- Now includes: Response types, Rich CLI, error recovery, state persistence, help system, subcommand routing

---

**Impact**: HIGH - Comprehensive solution ensures great UX and system reliability
**Effort**: 6 additional story points added to Story 30.4
**Status**: ✅ **DESIGN COMPLETE** - Ready for implementation

---

### ✅ CRITICAL 3: Help System - RESOLVED

**Original Problem**: User types "help" - what happens? There's no help command specified.

---

### **IMPLEMENTED SOLUTION** ✅

**Design Decision**: AI-powered contextual help with intent understanding (NOT generic lists)

#### Core Principle

**Intent-based help** - Don't overwhelm users with lists. Understand what they need and provide targeted guidance.

#### User Experience

User types "help" or "help [with something]" → AI analyzes intent → Checks project context → Provides targeted, actionable guidance

**Examples**:

1. **"help" in active project**:
   - AI checks: Has 3 epics, 2 pending stories
   - Response: "You have 2 pending stories ready. Want me to implement story 3.1? Or run a retrospective?"

2. **"help with ceremonies"**:
   - AI detects: Asking about ceremonies
   - Response: "Last retro was 2 weeks ago. Want me to run a retrospective?"

3. **"help I'm stuck"**:
   - AI detects: User is lost
   - Response: "You're on Epic 3 with 8 stories. Story 3.4 is ready. Want me to implement it?"

4. **"help" in greenfield**:
   - AI detects: No project found
   - Response: "Let's get started! Tell me what you want to build."

#### Implementation

- **Command Detection**: Recognize "help" command
- **AI Analysis**: Use AIAnalysisService (Epic 21) to understand user intent
- **Context Gathering**: Check project state via StateTracker (Epic 15)
- **Targeted Response**: Generate specific, actionable guidance
- **Next Steps**: Always suggest concrete actions

#### What This Is NOT:
- ❌ Not a static help menu
- ❌ Not a list of all commands
- ❌ Not generic documentation

#### What This IS:
- ✅ AI-powered intent understanding
- ✅ Context-aware guidance
- ✅ Actionable next steps
- ✅ Conversation, not documentation

---

### **Changes Made**

**Story 30.4 Updated**: Help system added to Command Routing
- +1 story point (included in the +6 total)
- Fully integrated with AI-powered command routing

---

**Impact**: HIGH - Dramatically improves discoverability and new user experience
**Effort**: 1 story point (included in Story 30.4 total)
**Status**: ✅ **DESIGN COMPLETE** - Ready for implementation

---

### ✅ CRITICAL 4: Exit During Long-Running Operations - RESOLVED

**Original Problem**: User types "exit" while a story is being implemented. What happens?

---

### **IMPLEMENTED SOLUTION** ✅

**Design Decision**: Graceful cancellation with state preservation and recovery

#### User Experience

**Scenario 1: Exit command during operation**
- User types "exit"
- System confirms: "Operation in progress. Cancel and exit?"
- User confirms
- Operation cancelled gracefully
- State saved to database
- Farewell message with session summary

**Scenario 2: Ctrl+C during operation**
- User presses Ctrl+C
- Operation cancelled immediately
- User asked: "Exit or continue?"
- State preserved regardless of choice

**Scenario 3: Exit when idle**
- User types "exit"
- Immediate farewell message
- No confirmation needed

#### Implementation Details

**Exit Handling (Story 30.1)**:
- Exit commands: "exit", "quit", "bye", "goodbye"
- Signal handlers for Ctrl+C (SIGINT)
- Confirmation if operation in progress
- Immediate exit when idle

**Cancellation Support (Story 30.5)**:
- asyncio.Event for cancellation signaling
- 5-second grace period for cleanup
- Force cancellation after timeout
- Cancellation propagates through all layers (REPL → Session → Router → Orchestrator)

**State Preservation (Story 30.5 + Epic 15)**:
- Cancelled operations saved to database with status=cancelled
- Partial artifacts tracked
- Recovery mode on next startup offers to resume

**Session Summary on Exit**:
- Duration
- Operations completed
- Artifacts created
- API cost (if applicable)

**Bottom Toolbar**:
- Shows current operation status
- Hints: "Ctrl+C to cancel, 'exit' to quit"

---

### **Changes Made**

**Story 30.1 Updated**: REPL Foundation
- No additional story points (core functionality)
- Includes: Exit commands, Ctrl+C handling, signal handlers, farewell message

**Story 30.5 Updated**: Session State Management
- No additional story points (expected functionality)
- Includes: Cancellation support, state preservation, cleanup

---

**Impact**: HIGH - Ensures data integrity and professional UX
**Effort**: Included in existing stories (no additional points)
**Status**: ✅ **DESIGN COMPLETE** - Ready for implementation

---

## High Priority Risks (Should Address)

### ⚠️ HIGH 1: Intent Parsing Too Simplistic

**Problem**: "Simple keyword matching" may not handle ambiguous inputs.

**Examples of Ambiguity**:
- "show me the PRD" → Command or question?
- "create story" → Missing parameters, needs clarification
- "why did that fail?" → Requires context from previous operation
- "fix the bug in story 1.1" → Complex intent (find bug + fix + update story)

**Current Approach**: Story 30.3 uses keyword matching:
```python
if any(keyword in input.lower() for keyword in ["build", "create", "add"]):
    return IntentType.FEATURE_REQUEST
```

**Risk**: Brittle, fails on edge cases, frustrates users.

**Proposed Improvement**:
Add intent confidence scoring:

```python
@dataclass
class Intent:
    type: IntentType
    confidence: float  # 0.0-1.0
    entities: Dict[str, Any]  # Extracted entities (epic nums, etc.)
    clarification_needed: bool

class IntentParser:
    def parse(self, user_input: str, context: Dict) -> Intent:
        # Try multiple detection strategies
        keyword_intent = self._keyword_matching(user_input)
        pattern_intent = self._pattern_matching(user_input)
        context_intent = self._context_based(user_input, context)

        # Combine with confidence
        intent = self._combine_intents([keyword_intent, pattern_intent, context_intent])

        # Check if clarification needed
        if intent.confidence < 0.6:
            intent.clarification_needed = True

        return intent
```

**If High Confidence** (>0.8): Execute
**If Medium Confidence** (0.6-0.8): Confirm with user
**If Low Confidence** (<0.6): Ask for clarification

**Impact**: MEDIUM - MVP works with simple matching, but frustrating for complex requests
**Effort**: 2-3 days to add confidence scoring and clarification flows
**Recommendation**: Start with simple matching (MVP), iterate in future story

---

### ✅ HIGH 2: History Memory Limits - RESOLVED

**Original Problem**: Story 30.5 mentions "limit to 100 turns" but `InMemoryHistory` from prompt-toolkit doesn't have this built-in.

---

### **IMPLEMENTED SOLUTION** ✅

**Design Decision**: Bounded history for both UI and conversation context

#### Two Types of History

**1. UI History (prompt-toolkit)**: BoundedHistory
- Arrow-up/down command history
- 100 command limit
- Oldest automatically removed when limit exceeded

```python
class BoundedHistory(InMemoryHistory):
    """History with maximum size limit."""
    def __init__(self, max_size: int = 100):
        super().__init__()
        self.max_size = max_size
        self._history_deque = deque(maxlen=max_size)
```

**2. Conversation History (AI context)**: BoundedConversationHistory
- Full conversation turns for AI
- 100 turn limit
- System messages preserved even when pruning
- Token-aware context limiting (4000 tokens for AI)

#### Memory Monitoring

- get_memory_usage() provides statistics
- Warning at 80% capacity (80 turns)
- Warning when memory exceeds 10MB
- Memory stats in session summary on exit

#### Persistence

- Conversation history saved to `.gao-dev/last_session_history.json` on exit
- Can be loaded on next session (optional)
- Memory usage statistics saved

---

### **Changes Made**

**Story 30.5 Updated**: Session State Management
- No additional story points (expected functionality)
- Includes: BoundedHistory, BoundedConversationHistory, memory monitoring, persistence

**Configuration** (config/defaults.yaml):
```yaml
chat:
  max_ui_history: 100
  max_conversation_turns: 100
  max_context_tokens: 4000
  warn_at_turn_count: 80
```

---

**Impact**: MEDIUM - Prevents memory issues in very long sessions
**Effort**: Included in Story 30.5 (no additional points)
**Status**: ✅ **DESIGN COMPLETE** - Ready for implementation

---

### ✅ HIGH 3: Progress Indicators - RESOLVED

**Original Problem**: If Brian's analysis takes 5 seconds, REPL feels frozen.

---

### **IMPLEMENTED SOLUTION** ✅

**Design Decision**: Spinner with elapsed time for operations >30 seconds (included in Critical 2 solution)

#### Implementation

- Operations >30 seconds show spinner with elapsed time
- Rich Progress library with SpinnerColumn and TimeElapsedColumn
- Real-time progress updates stream to console
- Current agent and activity visible during execution
- Spinner stops on completion/error

**Example**:
```
[Spinner] Creating Product Requirements Document... (0:45 elapsed)
  • Analyzing requirements
  • Writing PRD sections
```

---

### **Changes Made**

**Story 30.4**: Progress indicators included in Command Routing
- Part of the response type system (Critical 2)
- No additional story points (included in +6)

---

**Impact**: MEDIUM - Improves perceived performance
**Effort**: Included in Story 30.4
**Status**: ✅ **DESIGN COMPLETE** - Included in Critical 2 solution

---

### ✅ HIGH 4: Subcommand Routing - RESOLVED

**Original Problem**: Commands like `ceremony`, `learning`, `state` have subcommands. How does routing work?

---

### **IMPLEMENTED SOLUTION** ✅

**Design Decision**: AI-powered subcommand parsing (consistent with AI-first approach)

#### Natural Language Subcommand Handling

User inputs are parsed by AI to extract command structure:

**Examples**:
- "list ceremonies for epic 1" → command=ceremony, subcommand=list, args={epic: 1}
- "show learning 5" → command=learning, subcommand=show, args={id: 5}
- "what's the state of story 1.1" → command=state, subcommand=show, args={epic: 1, story: 1}
- "run retrospective ceremony" → command=ceremony, subcommand=run, args={type: "retrospective"}

#### Supported Commands with Subcommands

- **ceremony**: list, show, run (with type: planning/standup/review/retrospective)
- **learning**: list, show, apply
- **state**: show (with epic/story identifiers)
- **story**: list, show, status
- **epic**: list, show, status

#### Natural Language Flexibility

AI handles variations:
- "list ceremonies" / "show ceremonies" / "ceremonies list"
- "show learning 5" / "learning 5" / "get learning 5"
- "state of story 1.1" / "show story 1.1 state" / "story 1.1 status"

#### Argument Extraction

AI extracts from natural language:
- Epic numbers: "epic 1", "for epic 3"
- Story identifiers: "story 1.1", "story 2.3"
- Learning IDs: "learning 5", "#5"
- Ceremony types: "retrospective", "planning", "standup"

#### Fallback Strategy

- If parsing fails, AI asks user to clarify
- Provides suggestions based on partial parse

---

### **Changes Made**

**Story 30.4 Updated**: Subcommand routing added to Command Routing
- +1 story point (included in the +6 total)
- Uses AIAnalysisService (Epic 21) for parsing

---

**Impact**: MEDIUM - Enables full command accessibility
**Effort**: 1 story point (included in Story 30.4 total)
**Status**: ✅ **DESIGN COMPLETE** - Ready for implementation

---

## Medium Priority Risks

### ⚠️ MEDIUM 1: Greenfield Detection Edge Cases

**Problem**: What if user is in:
- Random directory (not a project)
- Git repo but not GAO-Dev project
- Parent directory of multiple projects

**Current Design** (Story 30.2): Searches up to 5 parent dirs for `.gao-dev/`.

**Edge Cases Not Handled**:
1. **Multiple projects found**: Which one to use?
2. **Empty directory**: Assume greenfield?
3. **Git repo without `.gao-dev/`**: Offer to add GAO-Dev?

**Proposed Solution**:
Add explicit handling:

```python
class ProjectStatusReporter:
    def auto_detect(self) -> DetectionResult:
        result = self._search_for_gao_dev()

        if result.multiple_found:
            # Ambiguous - ask user
            return DetectionResult(
                status="ambiguous",
                message="Multiple projects found. Which one?",
                options=result.projects
            )
        elif result.found:
            return DetectionResult(status="found", project_root=result.path)
        elif self._is_git_repo():
            return DetectionResult(
                status="git_without_gao_dev",
                message="Git repo detected. Add GAO-Dev tracking?"
            )
        else:
            return DetectionResult(
                status="greenfield",
                message="No project detected. Initialize new project?"
            )
```

**Impact**: MEDIUM - Affects first-time experience
**Effort**: 1 day
**Story Update**: Add edge case handling to Story 30.2

---

### ⚠️ MEDIUM 2: No Multi-Project Support

**Problem**: FastContextLoader is project-scoped. Can't switch projects mid-session.

**User Scenario**:
```
You: I'm working on project A now
Brian: OK, switched to project A
You: Now I want to work on project B
Brian: Switched to project B
```

**Current Gap**: REPL is tied to one project for entire session.

**Proposed Solution (Future Enhancement)**:
Don't implement now, but document limitation:

```markdown
## Known Limitations

- **Single Project Per Session**: REPL works with one project at a time.
  To switch projects, exit and restart in different directory.

  **Workaround**: Open multiple terminals for multiple projects.
```

**Impact**: LOW - Edge case, workaround exists
**Effort**: Would be 2-3 days to implement
**Recommendation**: Document limitation, defer to future epic

---

### ⚠️ MEDIUM 3: No Cost Tracking in Interactive Mode

**Problem**: Brian's analysis uses LLMs. Long sessions could accumulate costs.

**Current State**: Epic 21 added local model support (deepseek-r1), mitigating costs. But for users using Claude API, costs could add up.

**Proposed Solution**:
Add session cost tracking:

```python
class ChatSession:
    def __init__(self, ...):
        self.session_cost = 0.0  # USD

    async def handle_input(self, user_input: str):
        # Track cost of Brian's analysis
        analysis = await self.brian.assess_and_select_workflows(user_input)
        self.session_cost += analysis.cost  # Add cost from analysis

        yield response

# On exit
async def _show_farewell(self):
    if self.session.session_cost > 0:
        console.print(f"\n[dim]Session cost: ${self.session.session_cost:.4f}[/dim]")
    console.print(Panel("Goodbye!..."))
```

**Impact**: LOW - Most users will use local models
**Effort**: 4 hours
**Recommendation**: Add in Story 30.5 if time permits

---

### ⚠️ MEDIUM 4: Windows Compatibility Not Explicitly Tested

**Problem**: Codebase is on Windows. prompt-toolkit works cross-platform, but edge cases exist.

**Known Windows Issues**:
- Ctrl+C handling can be different
- ANSI color support varies (old cmd.exe vs PowerShell vs Windows Terminal)
- File path handling (backslashes)

**Current Mitigation**: CLI already has Windows fixes (see `commands.py` lines 10-17):
```python
if sys.platform == "win32":
    import io
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Reconfigure stdout/stderr
```

**Proposed Solution**:
Add explicit Windows testing to Story 30.7:

```markdown
### Manual QA Scenarios (Windows-Specific)
- [ ] Test in cmd.exe
- [ ] Test in PowerShell
- [ ] Test in Windows Terminal
- [ ] Ctrl+C exits gracefully
- [ ] Colors render correctly
- [ ] File paths display correctly (no double backslashes)
```

**Impact**: LOW - Likely works, but needs validation
**Effort**: 2 hours of testing
**Story Update**: Add Windows testing to Story 30.7

---

## Low Priority Risks

### ℹ️ LOW 1: No Accessibility (Colorblind) Consideration

**Problem**: Rich formatting uses colors (green for Brian, red for errors). Colorblind users may struggle.

**Mitigation**: Use shape/symbols too:
- Brian: `[✓]` prefix + green
- Errors: `[✗]` prefix + red
- Progress: `[⋯]` prefix + dim

**Impact**: LOW - Nice to have
**Effort**: 2 hours
**Recommendation**: Add if time permits in Story 30.1

---

### ℹ️ LOW 2: No Session Persistence Across Restarts

**Problem**: When user exits and restarts, session context is lost.

**User Scenario**:
```
Session 1:
You: Create PRD for auth feature
Brian: Done!
[exit]

Session 2:
You: What was the PRD about?
Brian: I don't have context from previous session.
```

**Proposed Solution (Future)**:
Save session summary to `.gao-dev/last_session.json` on exit.

**Impact**: LOW - Users understand sessions are isolated
**Recommendation**: Defer to future enhancement

---

### ℹ️ LOW 3: Concurrent Operations Not Supported

**Problem**: User can't run multiple workflows simultaneously.

**Example**:
```
You: Create PRD
[While PRD is being created]
You: Also create story 1.1
Brian: Please wait for current operation to complete
```

**Current Design**: Single-threaded execution (good for MVP).

**Impact**: LOW - Rare use case
**Recommendation**: Defer to future enhancement

---

## Story Dependency Analysis

### Current Order (From Epic):
1. Story 30.1 (REPL)
2. Story 30.2 (Status) + 30.5 (Session) in parallel
3. Story 30.3 (Brian)
4. Story 30.4 (Routing)
5. Story 30.6 (Greenfield)
6. Story 30.7 (Testing)

### Issues Found:

**Issue 1**: Story 30.3 depends on Story 30.5 (needs pending action state)
- **Current**: 30.5 in parallel with 30.2, both before 30.3 ✓ Correct
- **Fix**: Explicitly document this dependency in 30.3

**Issue 2**: Story 30.4 needs response types from CRITICAL 2
- **Current**: No dependency on design work
- **Fix**: Add 1-day design task before 30.4

**Issue 3**: Story 30.6 could be done anytime after 30.2
- **Current**: Scheduled after 30.4, 30.5
- **Optimization**: Could be done in parallel with 30.4 to save time

### Revised Timeline:

**Week 1**:
- **Mon-Tue**: Story 30.1 (5 pts) + CRITICAL 4 fixes (cancellation)
- **Wed**: Story 30.2 (3 pts) + CRITICAL 3 (help system)
- **Thu**: Story 30.5 (3 pts) + CRITICAL 1 (confirmation flow)
- **Fri**: Design response types (CRITICAL 2)
- **Mon**: Story 30.3 (8 pts) start

**Week 2**:
- **Tue**: Story 30.3 (8 pts) finish
- **Wed**: Story 30.4 (5 pts)
- **Thu**: Story 30.6 (5 pts) - Can do in parallel with 30.4
- **Fri**: Story 30.7 (3 pts) integration tests
- **Mon**: Story 30.7 finish + manual QA

**Revised Total**: Still 2 weeks, but with critical fixes included

---

## Testing Strategy Gaps

### Gap 1: No End-to-End Scenario Tests

**Problem**: Story 30.7 has "integration tests" but scenarios aren't defined.

**Proposed E2E Scenarios**:
1. **New User Flow**:
   - Start REPL in empty dir
   - Initialize greenfield project
   - Create first PRD
   - Break into stories
   - Exit

2. **Feature Request Flow**:
   - Start REPL in existing project
   - Request feature ("I want auth")
   - Brian analyzes
   - User confirms
   - Workflows execute
   - Exit

3. **Multi-Turn Refinement**:
   - User: "I want a feature"
   - Brian: "What kind?"
   - User: "Authentication"
   - Brian: "Email or OAuth?"
   - User: "Email"
   - Brian: "Here's my recommendation..."

4. **Error Recovery**:
   - Request feature
   - Workflow fails
   - Brian suggests remediation
   - User tries again
   - Success

5. **Help Discovery**:
   - User: "help"
   - Shows commands
   - User: "how do I create PRD?"
   - Shows specific help
   - User: "create a PRD"
   - Executes

**Story Update**: Add these specific scenarios to Story 30.7

---

### Gap 2: No Performance Tests

**Problem**: No tests for startup time, response time, memory usage.

**Proposed Performance Tests**:
```python
def test_repl_startup_time():
    """REPL should start in <2 seconds."""
    start = time.time()
    repl = ChatREPL(project_root)
    # Simulate startup
    elapsed = time.time() - start
    assert elapsed < 2.0

def test_brian_analysis_time():
    """Brian analysis should complete in <5 seconds."""
    start = time.time()
    analysis = await brian.assess_and_select_workflows("build auth feature")
    elapsed = time.time() - start
    assert elapsed < 5.0

def test_session_memory_usage():
    """Session should use <100MB."""
    session = ChatSession(...)
    # Simulate 50 turns
    for i in range(50):
        await session.handle_input(f"test input {i}")
    memory = get_memory_usage(session)
    assert memory < 100 * 1024 * 1024  # 100MB
```

**Story Update**: Add performance tests to Story 30.7

---

## Recommendations

### Must Do (Before Starting Implementation):

1. ✅ **Design confirmation flow state machine** (CRITICAL 1)
   - Add to Story 30.5
   - 1 day effort

2. ✅ **Design response type system** (CRITICAL 2)
   - Add to Story 30.4
   - 1 day effort

3. ✅ **Add help system** (CRITICAL 3)
   - Add mini-story 30.4.5 (1 pt) or extend 30.4
   - 1 day effort

4. ✅ **Add cancellation support** (CRITICAL 4)
   - Add to Story 30.1 and 30.5
   - 1 day effort

5. ✅ **Define E2E test scenarios** (Testing Gap 1)
   - Add to Story 30.7
   - 0.5 day effort

### Should Do (During Implementation):

6. ⚠️ **Add progress indicators** (HIGH 3)
   - Story 30.1 or 30.3
   - 0.5 day effort

7. ⚠️ **Implement bounded history** (HIGH 2)
   - Story 30.5
   - 0.25 day effort

8. ⚠️ **Add subcommand routing** (HIGH 4)
   - Story 30.4
   - 1 day effort

9. ⚠️ **Handle greenfield edge cases** (MEDIUM 1)
   - Story 30.2
   - 1 day effort

### Nice to Have (If Time Permits):

10. ℹ️ **Add session cost tracking** (MEDIUM 3)
11. ℹ️ **Add accessibility symbols** (LOW 1)
12. ℹ️ **Add performance tests** (Gap 2)

### Document as Limitations:

13. ℹ️ **Multi-project support** (MEDIUM 2) - Future enhancement
14. ℹ️ **Session persistence** (LOW 2) - Future enhancement
15. ℹ️ **Concurrent operations** (LOW 3) - Future enhancement

---

## Revised Story Point Estimate

**Original Estimate**: 32 story points (2 weeks)

**With All Resolutions**:
- Original stories: 32 pts
- CRITICAL 1 (Mary integration): +5 pts (Story 30.8)
- CRITICAL 2 (Response types, state persistence, error recovery): +6 pts (Story 30.4)
- CRITICAL 3 (AI-powered help system): Included in Story 30.4
- CRITICAL 4 (Exit handling, cancellation): Included in Stories 30.1 and 30.5
- HIGH 2 (Bounded history): Included in Story 30.5
- HIGH 3 (Progress indicators): Included in Story 30.4
- HIGH 4 (Subcommand routing): Included in Story 30.4

**Epic 30 Total**: **47 story points** (3 weeks)

**Epic 31 Created**: **25 story points** (2 weeks) - Full Mary Integration

**Combined Total**: **72 story points** (5 weeks total)

**Note**: All critical and high-priority risks have been addressed with comprehensive solutions

---

## Final Recommendation

**✅ PROCEED - All Critical and High-Priority Risks Resolved**

### What Was Addressed:

1. ✅ **All 4 Critical Risks** - Comprehensive solutions designed
2. ✅ **All 4 High-Priority Risks** - Comprehensive solutions designed
3. ✅ **Story Point Estimates** - Updated to reflect true scope (47 pts Epic 30 + 25 pts Epic 31)
4. ✅ **System Integration** - All solutions leverage existing infrastructure (Epic 15, 21, 27)
5. ✅ **Architecture Consistency** - AI-powered throughout (help, intent, subcommands, failure analysis)

### Key Design Decisions:

1. **AI-First Approach**: Intent detection, help system, subcommand routing all use AIAnalysisService
2. **State Persistence**: Active operations saved to database for crash recovery
3. **Rich CLI**: Agent-specific colors, 11 response types, beautiful formatting
4. **Error Recovery**: Retry once → AI analysis → suggest alternatives
5. **Contextual Help**: Always context-aware and actionable, never generic lists
6. **Directive Brian**: Brian proceeds with confidence, Mary handles clarification

### Updated Timeline:

- **Epic 30**: 47 story points (3 weeks)
- **Epic 31**: 25 story points (2 weeks)
- **Total**: 72 story points (5 weeks)

### Next Steps:

1. Update story files with detailed acceptance criteria
2. Begin implementation starting with Story 30.1 (REPL Foundation)
3. Test comprehensively throughout (Story 30.7)

**Risk Level After Resolutions**: LOW

**Confidence**: VERY HIGH - Epic has comprehensive, well-integrated solutions

---

**Reviewed By**: Architecture Team & Product Team
**Date**: 2025-11-10
**Status**: ✅ **DESIGNS COMPLETE** - Ready for Implementation
