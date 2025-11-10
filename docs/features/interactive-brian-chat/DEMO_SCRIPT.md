# Mary Demo Script - Interactive Walkthrough

**Epic**: 31 - Full Mary Integration
**Version**: 1.0
**Duration**: 15-20 minutes
**Last Updated**: 2025-11-10

This script walks through a live demo of Mary (Business Analyst) capabilities, showcasing all workflows integrated with Epic 10 prompt system.

---

## Demo Setup

### Prerequisites

```bash
# Ensure GAO-Dev is installed
gao-dev --version

# Ensure all Mary prompts are present
ls gao_dev/config/prompts/agents/mary_*.yaml | wc -l
# Should show 24 prompts

# Optional: Have a test project ready
cd /path/to/demo-project
```

### Demo Environment

- **Terminal**: Full screen, readable font size
- **Screen Share**: Ensure terminal is visible
- **Timing**: Allow 15-20 minutes for full demo
- **Audience**: Technical or non-technical (adapt language accordingly)

---

## Demo Script

### Act 1: Introduction (2 minutes)

**Talking Points**:
- Mary is GAO-Dev's Business Analyst agent
- Helps clarify vague ideas into clear product visions
- Uses proven business analysis techniques (Vision Canvas, SCAMPER, MoSCoW)
- All prompts powered by Epic 10 system (customizable YAML)

**Show**:
```bash
# Show Mary's prompts
ls -l gao_dev/config/prompts/agents/mary_*.yaml

# Count: 24 prompts total
# - 4 vision elicitation
# - 10 brainstorming
# - 5 requirements analysis
# - 5 domain-specific
```

**Key Message**: "Mary brings professional business analysis to every project, helping you build the RIGHT thing before you build it."

---

### Act 2: Vision Elicitation Demo (6-8 minutes)

**Scenario**: "Let's say I have a vague idea for a productivity tool."

#### Step 1: Start Interactive Chat

```bash
gao-dev start
```

**Expected Output**:
```
Brian: Hello! I'm Brian, your GAO-Dev coordinator.
Brian: Checking project status...
Brian: [Shows current project info or "No project detected"]
Brian: What would you like to work on today?
```

#### Step 2: Submit Vague Request

```
You: I want to build a productivity tool for developers
```

**Expected Output**:
```
Brian: Analyzing your request...
Brian: Vagueness score: 0.85 (quite vague)
Brian: I recommend starting with Mary (Business Analyst) to clarify your vision.
Brian: This will take about 20-30 minutes. Would you like to proceed?
```

**Talking Point**: "Notice Brian detected high vagueness. Instead of building the wrong thing, he brings in Mary."

#### Step 3: Accept Mary's Help

```
You: yes
```

**Expected Output**:
```
Mary: Hello! I'm Mary, your Business Analyst.
Mary: Let's clarify your vision using a structured approach.
Mary: I'll use the Vision Canvas technique.

=== TARGET USERS ===
Mary: Who would use this productivity tool?
```

#### Step 4: Complete Vision Canvas (Abbreviated for demo)

```
You: Software developers working remotely

Mary: What specific problems are they experiencing?

You: Context switching between tools, lost focus, hard to track deep work

Mary: If this tool existed perfectly, what would it enable?

You: Uninterrupted deep work sessions with automatic distractions blocking

Mary: What are the 3-5 most important features?

You: 1. Focus timer with Pomodoro
     2. Automatic notification blocking
     3. Session analytics
     4. Integration with calendar
```

**Expected Output**:
```
Mary: Excellent! Here's your vision summary:

**Target Users**: Remote software developers
**Core Problem**: Context switching and distraction management
**Product Vision**: Enable uninterrupted deep work sessions
**Key Features**: Focus timer, notification blocking, analytics, calendar sync
**Differentiator**: Automatic distraction management vs manual toggling

Mary: I've saved this to: .gao-dev/mary/vision-documents/vision-[timestamp].md

Mary: This vision is ready for John (Product Manager) to create a PRD.
Mary: Would you like me to hand this off to Brian?
```

**Talking Point**: "In 5 minutes, we went from 'productivity tool' (vague) to a clear vision with target users, problems, and features."

#### Step 5: Show Generated Files

```bash
# Exit chat (Ctrl+C)

# Show vision document
cat .gao-dev/mary/vision-documents/vision-*.md
```

**Key Message**: "All Mary's outputs are saved. This vision document can be shared with stakeholders, refined, or fed directly into PRD creation."

---

### Act 3: Brainstorming Demo (4-5 minutes)

**Scenario**: "Now let's brainstorm creative alternatives for authentication."

#### Step 1: Request Brainstorming

```bash
gao-dev start
```

```
You: Mary, help me brainstorm better authentication methods
```

**Expected Output**:
```
Mary: I can help facilitate brainstorming!
Mary: I recommend SCAMPER technique for generating creative ideas.
Mary: SCAMPER: Substitute, Combine, Adapt, Modify, Put, Eliminate, Reverse

Ready to explore?
```

#### Step 2: Run Through SCAMPER (Abbreviated)

```
You: yes

Mary: === S - SUBSTITUTE ===
Mary: What could you SUBSTITUTE passwords with?

You: Biometric, magic links, OAuth

Mary: === C - COMBINE ===
Mary: What if you COMBINED two authentication methods?

You: Password + fingerprint, email + trusted device

[Continue through remaining letters...]
```

**Expected Output**:
```
Mary: Fantastic! You generated 15 ideas across 7 categories.

=== KEY THEMES ===
1. Passwordless options (magic links, OAuth, biometrics)
2. Multi-factor security
3. Trust-based authentication

=== MIND MAP ===
[Shows Mermaid diagram]

=== QUICK WINS ===
1. Magic links (easy to implement)
2. OAuth integration (leverage existing accounts)

Mary: I've saved this to: .gao-dev/mary/brainstorming-sessions/brainstorm-[timestamp].md
```

**Talking Point**: "SCAMPER forced us to think creatively. We generated 15 ideas in 3 minutes that we wouldn't have thought of otherwise."

---

### Act 4: Requirements Analysis Demo (3-4 minutes)

**Scenario**: "Let's prioritize features for an MVP."

#### Step 1: Request Analysis

```
You: Mary, analyze these requirements:
     - User login
     - Dashboard
     - Export to PDF
     - Dark mode
     - AI insights

     Timeline: 3 months, team of 3
```

**Expected Output**:
```
Mary: Let me analyze these requirements using:
      - MoSCoW prioritization
      - Risk identification
      - Dependency mapping

Analyzing...

=== MoSCoW PRIORITIZATION ===

**MUST HAVE**:
- User login (security requirement)
- Dashboard (core value)

**SHOULD HAVE**:
- Export to PDF (customer request)
- Dark mode (UX expectation)

**COULD HAVE**:
- AI insights (differentiator but complex)

=== RISKS ===

1. AI insights (HIGH RISK):
   - Technical complexity
   - Unpredictable timeline
   - Recommend: Defer to Phase 2

2. 3-month timeline (MEDIUM RISK):
   - Tight for 5 features
   - Recommend: Cut AI from MVP

=== RECOMMENDATION ===

**Phase 1 MVP** (3 months):
- User login
- Dashboard
- Export to PDF
- Dark mode

**Phase 2** (Months 4-6):
- AI insights (requires ML expertise)

Mary: I've saved this analysis to: .gao-dev/mary/requirements-analysis/analysis-[timestamp].md
```

**Talking Point**: "Mary identified that AI insights is high risk. Better to cut it from MVP than miss deadline or ship buggy AI."

---

### Act 5: Epic 10 Integration Demo (2-3 minutes)

**Scenario**: "Show how Mary's prompts are customizable."

#### Step 1: Show Prompt Structure

```bash
# Show a Mary prompt file
cat gao_dev/config/prompts/agents/mary_vision_canvas.yaml
```

**Expected Output**:
```yaml
name: mary_vision_canvas
system_prompt: |
  {{mary_persona}}

  You are facilitating a Vision Canvas session...
user_prompt: |
  User request: {{user_request}}

  Walk through these elements:
  1. Target Users
  2. User Needs
  3. Product Vision
  4. Key Features
  5. Success Metrics
  6. Differentiators
variables:
  mary_persona: "@file:gao_dev/agents/mary.md"
  user_request: "{{user_request}}"
response:
  format: json
  temperature: 0.7
metadata:
  category: vision_elicitation
  story: "31.1"
```

**Talking Point**: "Notice the `@file:` reference. Mary's persona is loaded from a separate file. You can customize her personality, add domain expertise, or create specialized variants."

#### Step 2: Show Mary's Persona

```bash
cat gao_dev/agents/mary.md
```

**Expected Output**:
```markdown
# Mary - Business Analyst

## Role
Business Analyst and Requirements Facilitator

## Personality
- Curious and inquisitive
- Patient and empathetic
- Structured yet flexible
- Focuses on "why" before "what"

## Approach
- Ask clarifying questions
- Use proven frameworks
- Visual thinking (diagrams)
- Collaborative discovery

[...]
```

**Talking Point**: "You can edit this file to change Mary's behavior. Want her more technical? Add technical expertise. Want domain-specific questions? Add domain knowledge."

#### Step 3: Show Customization Example

```bash
# Create custom domain prompt (conceptual - don't actually create)
```

**Example Custom Prompt**:
```yaml
name: mary_domain_healthcare
system_prompt: |
  {{mary_persona}}

  You specialize in healthcare applications and are familiar with:
  - HIPAA compliance requirements
  - HL7/FHIR standards
  - Clinical workflows
  - Patient privacy regulations

  When gathering requirements for healthcare apps, always ask about:
  - PHI (Protected Health Information) handling
  - Audit logging requirements
  - Access controls (RBAC)
  - Data retention policies
```

**Talking Point**: "This is the power of Epic 10. You can create domain-specific Mary variants (mary-healthcare, mary-fintech, mary-ecommerce) without touching code."

---

### Act 6: Full Flow Demo (2-3 minutes)

**Scenario**: "Show how Mary fits into the complete GAO-Dev workflow."

#### Visual Flow Diagram

```
User Vague Request
    ↓
Brian detects vagueness (score > 0.8)
    ↓
Mary: Vision Elicitation (20-30 min)
    ↓
Mary generates Vision Summary
    ↓
Brian receives clarified vision
    ↓
Brian selects workflow: PRD → Architecture → Stories
    ↓
John (PM) creates PRD
    ↓
Winston (Architect) creates Architecture
    ↓
Bob (Scrum Master) breaks into stories
    ↓
Amelia (Developer) implements
    ↓
Production-ready application
```

**Talking Point**: "Mary is the FIRST step in GAO-Dev's autonomous development pipeline. She ensures we build the RIGHT thing before we build it right."

---

## Demo Wrap-Up (2 minutes)

### Key Messages

1. **Mary eliminates guesswork**: Vague ideas → Clear visions
2. **Proven techniques**: Vision Canvas, SCAMPER, MoSCoW, Kano
3. **Seamless integration**: Mary → Brian → John → Implementation
4. **Epic 10 powered**: All prompts customizable via YAML
5. **Production-ready**: 24 prompts, 4 workflows, comprehensive testing

### Statistics to Highlight

- **60+ tests** across Epic 31 (14 + 16 + 13 + 11 + 20+)
- **24 prompts** covering vision, brainstorming, requirements, domains
- **4 workflows** fully integrated
- **<10ms** prompt loading (Epic 10 caching)
- **<5 minutes** to clarify vague requests

### Call to Action

```bash
# Try it yourself!
gao-dev start

# Or explore examples
cat docs/features/interactive-brian-chat/examples/mary-examples.md

# Or read the user guide
cat docs/features/interactive-brian-chat/USER_GUIDE_MARY.md
```

---

## Demo Troubleshooting

### Issue: Mary not responding

**Debug**:
```bash
# Check prompts exist
ls gao_dev/config/prompts/agents/mary_*.yaml | wc -l

# Check logs
gao-dev logs --level debug
```

### Issue: Vision canvas not saving

**Debug**:
```bash
# Check .gao-dev directory exists
ls -la .gao-dev/

# Create if missing
mkdir -p .gao-dev/mary/vision-documents
```

### Issue: Brian doesn't delegate to Mary

**Cause**: Request may not be vague enough (score < 0.8)

**Solution**: Make request more vague:
- ❌ "Build a React todo app with auth and dark mode"
- ✅ "I want to build something for productivity"

---

## Demo Variations

### For Technical Audience

- Emphasize Epic 10 integration
- Show prompt YAML structure
- Discuss architecture (MaryOrchestrator, BrainstormingEngine, etc.)
- Mention test coverage (60+ tests)

### For Business Audience

- Focus on outcomes (vague → clear)
- Show business value (build right thing, reduce waste)
- Demonstrate techniques (Vision Canvas, SCAMPER)
- Skip technical implementation details

### For Sales/Marketing

- Emphasize "AI business analyst" positioning
- Show before/after (vague request → clear vision)
- Highlight time savings (30 min vs. days of meetings)
- Demonstrate production-readiness

---

## Post-Demo Resources

### For Developers

- [Epic 31 Architecture](./ARCHITECTURE.md)
- [Story Files](./stories/epic-31/)
- [Integration Tests](../../tests/integration/test_mary_integration.py)

### For Users

- [User Guide](./USER_GUIDE_MARY.md)
- [Examples](./examples/mary-examples.md)
- [QA Checklist](./QA_CHECKLIST.md)

### For Contributors

- [Epic 31 PRD](./PRD.md)
- [Epic Breakdown](./epics/epic-31-full-mary-integration.md)
- [CLAUDE.md](../../../CLAUDE.md) - Project guide

---

## Demo Recording Checklist

**Before Recording**:
- [ ] GAO-Dev installed and working
- [ ] All 24 Mary prompts present
- [ ] Test project initialized
- [ ] Terminal font readable
- [ ] Screen recording software ready

**During Recording**:
- [ ] Introduce Mary's role
- [ ] Show vague request → clear vision
- [ ] Demonstrate brainstorming technique
- [ ] Show requirements analysis
- [ ] Highlight Epic 10 integration
- [ ] Show generated files

**After Recording**:
- [ ] Edit for clarity (trim pauses)
- [ ] Add captions/annotations
- [ ] Include timestamps in description
- [ ] Link to documentation
- [ ] Post to YouTube/Vimeo

---

## Frequently Asked Questions

**Q: How long does a typical Mary session take?**

A: 20-30 minutes for vision elicitation, 15-25 for brainstorming, 1-2 for requirements analysis.

**Q: Can I customize Mary's questions?**

A: Yes! Edit the YAML prompt files in `gao_dev/config/prompts/agents/mary_*.yaml`

**Q: Does Mary work offline?**

A: No, Mary requires AI service connection (Claude, OpenAI, etc.) for facilitation.

**Q: Can Mary handle multiple projects?**

A: Yes, each project has its own `.gao-dev/mary/` directory for isolated outputs.

**Q: What if I disagree with Mary's recommendations?**

A: Mary is a facilitator, not a dictator. You make the final decisions. Her outputs are starting points for refinement.

---

**Version**: 1.0
**Last Updated**: 2025-11-10 (Epic 31 Complete)
**Demo Duration**: 15-20 minutes
**Difficulty**: Beginner-friendly
