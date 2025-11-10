# User Guide: Working with Mary (Business Analyst)

**Version**: 1.0 (Epic 31 with Epic 10 Integration)
**Last Updated**: 2025-11-10

---

## Introduction

Mary is GAO-Dev's Business Analyst agent. She helps you clarify vague ideas, facilitate brainstorming sessions, analyze requirements, and ensure you build the right thing before writing code.

Mary uses conversational AI (not hardcoded scripts) to adapt to your needs, ask relevant questions, and guide you through proven business analysis techniques.

**Epic 10 Integration**: All Mary workflows use GAO-Dev's prompt system with `@file:` reference resolution and `{{variable}}` substitution. This means:
- Prompts are externalized to YAML files
- Easy to customize without code changes
- Plugin-friendly for domain-specific extensions

---

## When Mary Gets Involved

Mary automatically joins the conversation when Brian detects your request needs exploration:

- **Vagueness > 0.8**: Vision elicitation (20-30 min)
- **Vagueness 0.6-0.8**: Simple clarification questions (5-10 min)

You can also explicitly request Mary:
```
> "Mary, can you help me brainstorm authentication ideas?"
> "I need help clarifying my vision"
> "Can we do a requirements analysis?"
```

---

## Mary's Capabilities

### 1. Vision Elicitation (Story 31.1)

**When to use**: You have a vague idea and need to articulate your vision.

**Techniques** (4 prompts):
- **Vision Canvas**: Target users, needs, vision, features, metrics, differentiators
- **Problem-Solution Fit**: Problem statement, current solutions, gaps, value prop
- **Outcome Mapping**: Desired outcomes, leading/lagging indicators, stakeholders
- **5W1H Analysis**: Who, What, When, Where, Why, How

**Example**:
```
You: "I want to build something for teams"
Brian: "This is quite vague. Let me bring in Mary..."
Mary: "Let's clarify your vision! First, who would use this?"
You: "Small development teams, 5-10 people"
Mary: "What problems are they experiencing?"
[... continues through vision canvas ...]
Mary: "Here's your vision summary: [summary]"
```

**Output**: Vision document saved to `.gao-dev/mary/vision-documents/`

**Prompts Used (Epic 10)**:
- `mary_vision_canvas` - Comprehensive vision canvas framework
- `mary_vision_problem_solution_fit` - Problem-solution fit analysis
- `mary_vision_outcome_mapping` - Outcome-based planning
- `mary_vision_5w1h` - Structured discovery questions

### 2. Brainstorming Facilitation (Story 31.2)

**When to use**: You want to explore creative solutions and generate ideas.

**Techniques** (10 prompts):
- **SCAMPER**: Substitute, Combine, Adapt, Modify, Put, Eliminate, Reverse
- **Mind Mapping**: Visual organization and connections
- **What If Scenarios**: Explore radical possibilities
- **First Principles**: Strip assumptions, rebuild from truths
- **Five Whys**: Drill to root causes
- **Yes And Building**: Momentum through positive additions
- **Resource Constraints**: Force prioritization through limitations
- **Assumption Reversal**: Challenge and flip beliefs
- **Stakeholder Round Table**: Multiple perspectives
- **Reverse Engineering**: Work backwards from desired outcome

**Example**:
```
You: "I need ideas for better authentication"
Mary: "Let's brainstorm! I recommend SCAMPER technique. Ready?"
Mary: "S - SUBSTITUTE: What could you substitute passwords with?"
You: "Biometrics? Hardware keys?"
Mary: "Great! C - COMBINE: What if we combined biometrics with..."
[... continues through SCAMPER ...]
Mary: "You generated 12 ideas! Here's your mind map: [diagram]"
```

**Output**: Brainstorming summary with ideas, mind maps, insights saved to `.gao-dev/mary/brainstorming-sessions/`

**Prompts Used (Epic 10)**:
- `mary_brainstorming_scamper` - SCAMPER creative thinking
- `mary_brainstorming_mindmap` - Mind map generation
- `mary_brainstorming_whatif` - What-if scenario exploration
- `mary_brainstorming_first_principles` - First principles thinking
- `mary_brainstorming_five_whys` - Root cause analysis
- `mary_brainstorming_yes_and` - "Yes, and..." building
- `mary_brainstorming_constraints` - Constraint-based creativity
- `mary_brainstorming_reversal` - Assumption reversal
- `mary_brainstorming_stakeholders` - Stakeholder perspectives
- `mary_brainstorming_reverse` - Reverse engineering

### 3. Advanced Requirements Analysis (Story 31.3)

**When to use**: You have requirements but need prioritization and risk analysis.

**Analyses** (5 prompts):
- **MoSCoW Prioritization**: Must, Should, Could, Won't
- **Kano Model**: Basic, Performance, Excitement features
- **Dependency Mapping**: What depends on what
- **Risk Identification**: Technical, resource, timeline risks
- **Constraint Analysis**: Time, budget, technical, compliance

**Example**:
```
You: "Analyze these requirements: [list]"
Mary: "Let's prioritize using MoSCoW method..."
Mary: "MUST: User login, Dashboard"
Mary: "SHOULD: Dark mode, Export"
Mary: "COULD: AI suggestions"
[... continues with Kano, dependencies, risks ...]
```

**Output**: Requirements analysis report saved to `.gao-dev/mary/requirements-analysis/`

**Prompts Used (Epic 10)**:
- `mary_requirements_moscow` - MoSCoW prioritization
- `mary_requirements_kano` - Kano model categorization
- `mary_requirements_dependency` - Dependency mapping
- `mary_requirements_risk` - Risk identification
- `mary_requirements_constraint` - Constraint analysis

### 4. Domain-Specific Questions (Story 31.4)

**When to use**: Automatic - Mary asks domain-relevant questions.

**Domains** (5 prompts):
- **Web App**: Responsive design, SEO, hosting, authentication (20 questions)
- **Mobile App**: iOS/Android, offline mode, push notifications (18 questions)
- **API Service**: REST/GraphQL, authentication, rate limiting (17 questions)
- **CLI Tool**: Commands, configuration, output formats (15 questions)
- **Data Pipeline**: ETL, scheduling, error handling, monitoring (19 questions)

**Example**:
```
You: "Build a mobile fitness app"
Mary: [Detects mobile_app domain]
Mary: "iOS, Android, or both?"
Mary: "Will users need offline access to workouts?"
Mary: "Push notifications for workout reminders?"
[... domain-specific questions embedded in prompt ...]
```

**Prompts Used (Epic 10)**:
- `mary_domain_web_app` - Web application questions
- `mary_domain_mobile_app` - Mobile app questions
- `mary_domain_api_service` - API service questions
- `mary_domain_cli_tool` - CLI tool questions
- `mary_domain_data_pipeline` - Data pipeline questions

---

## Epic 10 Prompt System

All Mary workflows use GAO-Dev's Epic 10 prompt system:

**Workflow Files** (metadata only):
- `workflows/1-analysis/vision-elicitation/workflow.yaml`
- `workflows/1-analysis/brainstorming/workflow.yaml`
- `workflows/1-analysis/requirements-analysis/workflow.yaml`
- `workflows/1-analysis/domain-requirements/workflow.yaml`

**Prompt Files** (LLM instructions):
- 24 total prompts in `gao_dev/config/prompts/agents/mary_*.yaml`
- All use `@file:gao_dev/agents/mary.md` for persona injection
- All use `{{variable}}` syntax for variable substitution
- All follow Epic 10 format: system_prompt, user_prompt, variables, response, metadata

**Benefits**:
- Prompts externalized (no code changes needed)
- Easy to customize per project
- Plugin-friendly for domain-specific extensions

**Example Prompt Structure**:
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

---

## Tips for Working with Mary

1. **Be open and exploratory**: Mary thrives in open-ended conversations
2. **Build on ideas**: Mary uses "Yes, and..." - you can too
3. **Ask for technique changes**: "Can we try a different brainstorming technique?"
4. **Save checkpoints**: Long sessions auto-save, you can resume later
5. **Review outputs**: Mary saves everything to `.gao-dev/mary/` - review and refine

---

## Performance & Limits

- **Vision Elicitation**: 20-30 minutes (user-paced)
- **Brainstorming Session**: 15-25 minutes (user-paced)
- **Requirements Analysis**: 1-2 minutes (automated)
- **Domain Detection**: <200ms (keyword + LLM)
- **Prompt Loading**: <10ms per prompt (Epic 10 caching)
- **Session Timeout**: 1 hour (auto-checkpoint)

---

## Troubleshooting

### Issue: Mary asks questions I already answered

**Solution**: Mary builds on conversation history - review and clarify if needed. The session state may have been reset.

### Issue: Wrong domain detected

**Solution**: Explicitly state domain: "This is a CLI tool..."

### Issue: Too many questions

**Solution**: "Mary, I have enough clarity now" or "Skip to summary"

### Issue: Want to customize prompts

**Solution**: Edit YAML files in `gao_dev/config/prompts/agents/mary_*.yaml`

**Example Customization**:
```yaml
# Customize mary_vision_canvas.yaml
name: mary_vision_canvas
system_prompt: |
  {{mary_persona}}

  [ADD YOUR CUSTOM INSTRUCTIONS HERE]

  You are facilitating a Vision Canvas session...
```

### Issue: Mary not responding

**Possible Causes**:
1. AI service timeout - Check network connection
2. Invalid prompt format - Check logs for errors
3. Missing prompt file - Verify all 24 Mary prompts exist

**Debug Steps**:
```bash
# Check logs
gao-dev logs --level debug

# Verify prompts exist
ls gao_dev/config/prompts/agents/mary_*.yaml

# Test prompt loading
python -c "from gao_dev.core.prompt_loader import PromptLoader; p = PromptLoader(); print(p.load_prompt('mary_vision_canvas'))"
```

---

## Next Steps After Mary

After Mary completes clarification:
1. **Vision Summary** → John creates PRD
2. **Brainstorming Output** → Inform feature prioritization
3. **Requirements Analysis** → Winston creates architecture
4. **All outputs** → Stored in `.gao-dev/mary/` for reference

**Typical Flow**:
```
User Vague Request
    ↓
Brian detects vagueness (score > 0.8)
    ↓
Mary: Vision Elicitation (20-30 min)
    ↓
Mary generates Vision Summary
    ↓
Vision Summary → Brian
    ↓
Brian: "Great! Now let me bring in John to create a PRD..."
    ↓
John creates PRD from Vision Summary
    ↓
[Continue with Architecture, Stories, Implementation...]
```

---

## Command Reference

### Starting a Mary Session

```bash
# Via interactive chat
gao-dev start

You: "I have a vague idea for a project"
Brian: "Let me bring in Mary to help clarify..."

# Or explicitly
You: "Mary, help me brainstorm authentication"
You: "Mary, can we do a vision canvas?"
```

### Viewing Mary's Outputs

```bash
# All Mary outputs stored in project's .gao-dev/mary/
ls .gao-dev/mary/

# Structure:
.gao-dev/mary/
├── vision-documents/
│   ├── vision-2025-11-10-143022.md
│   └── vision-2025-11-10-150133.md
├── brainstorming-sessions/
│   ├── brainstorm-scamper-2025-11-10-143545.md
│   └── brainstorm-whatif-2025-11-10-151203.md
└── requirements-analysis/
    └── analysis-2025-11-10-152410.md
```

---

## Integration with Other Agents

### Mary → John (Product Manager)

Mary's vision summaries are formatted for John:
- Vision Summary includes all key information
- Converts to Brian-compatible prompt via `to_prompt()`
- John creates PRD from vision

### Mary → Brian (Workflow Coordinator)

Mary hands off clarified requests:
- Brian receives `VisionSummary` object
- Brian selects appropriate workflows
- Brian coordinates remaining agents

### Mary → Winston (Architect)

Requirements feed architecture:
- MoSCoW prioritization informs MVP scope
- Dependency mapping guides architecture layers
- Risk analysis influences technology choices

---

## Advanced Usage

### Custom Brainstorming Techniques

Create your own technique by adding a prompt:

```yaml
# gao_dev/config/prompts/agents/mary_brainstorming_custom.yaml
name: mary_brainstorming_custom
system_prompt: |
  {{mary_persona}}

  You are facilitating a custom brainstorming technique called "Future Backwards".

  [YOUR TECHNIQUE DESCRIPTION]
user_prompt: |
  Topic: {{topic}}

  [YOUR FACILITATION STEPS]
variables:
  mary_persona: "@file:gao_dev/agents/mary.md"
  topic: "{{topic}}"
response:
  format: json
  temperature: 0.8
metadata:
  category: brainstorming
  technique: custom
```

Then use it:
```python
result = await mary.facilitate_brainstorming(
    user_request="AI ethics",
    technique="custom"
)
```

### Domain-Specific Customization

Add your own domain:

```yaml
# gao_dev/config/prompts/agents/mary_domain_iot_device.yaml
name: mary_domain_iot_device
system_prompt: |
  {{mary_persona}}

  You are gathering requirements for an IoT device project.

  Ask about:
  - Hardware specifications
  - Communication protocols
  - Power management
  - Security considerations
  [...]
```

---

## Examples

See [mary-examples.md](./examples/mary-examples.md) for 5+ complete examples demonstrating Mary's capabilities.

---

## FAQ

**Q: How is Mary different from Brian?**

A: Brian is the workflow coordinator who selects what work to do. Mary is the business analyst who helps clarify WHAT to build before Brian decides HOW to build it.

**Q: Can I skip Mary and go straight to implementation?**

A: Yes! If your request is clear (vagueness < 0.6), Brian won't invoke Mary. But if your idea is vague, Mary's clarification saves time downstream.

**Q: Are Mary's sessions saved?**

A: Yes, all vision documents, brainstorming summaries, and requirements analyses are saved to `.gao-dev/mary/` in your project.

**Q: Can Mary work with existing projects?**

A: Absolutely! Mary can help clarify new features for existing projects or facilitate retrospectives and planning sessions.

**Q: How do I customize Mary's behavior?**

A: Edit the YAML prompt files in `gao_dev/config/prompts/agents/mary_*.yaml`. You can change questions, techniques, and facilitation styles without touching code.

**Q: What languages does Mary support?**

A: Mary's prompts are in English, but she can facilitate in any language the underlying LLM supports.

**Q: Does Mary replace user research?**

A: No, Mary accelerates initial discovery but doesn't replace talking to real users. Use Mary to clarify YOUR vision, then validate with users.

---

## Resources

### Documentation

- [Epic 31 PRD](../PRD.md) - Product requirements for Mary integration
- [Epic 31 Architecture](../ARCHITECTURE.md) - Technical design
- [Mary Examples](./examples/mary-examples.md) - 5+ complete examples
- [Demo Script](./DEMO_SCRIPT.md) - Interactive demo

### Prompt Files

All 24 Mary prompts: `gao_dev/config/prompts/agents/mary_*.yaml`

### Source Code

- `gao_dev/orchestrator/mary_orchestrator.py` - Mary's main orchestrator
- `gao_dev/orchestrator/brainstorming_engine.py` - Brainstorming facilitation
- `gao_dev/orchestrator/requirements_analyzer.py` - Requirements analysis
- `gao_dev/orchestrator/domain_question_library.py` - Domain questions

---

**Questions?** Type `help mary` in the chat or see examples in `examples/mary-examples.md`

**Version**: 1.0
**Last Updated**: 2025-11-10 (Epic 31 Complete)
