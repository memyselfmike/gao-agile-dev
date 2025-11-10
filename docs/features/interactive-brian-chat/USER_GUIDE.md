# Interactive Brian Chat - User Guide

**Version**: 1.0
**Last Updated**: 2025-11-10
**Status**: Production Ready

---

## Overview

The Interactive Brian Chat interface transforms GAO-Dev from a command-line tool into a conversational development partner. Simply run `gao-dev start` and have natural dialogue with Brian, your AI Engineering Manager.

**Key Benefits**:
- No memorizing CLI commands
- Natural language interaction
- Multi-turn conversations with context
- Project auto-detection
- Guided initialization for new projects
- Session history preservation

---

## Getting Started

### Prerequisites

- GAO-Dev installed (Epics 22-30 complete)
- Python 3.11+
- Dependency: `prompt-toolkit` (installed automatically)

### Installation

If you installed GAO-Dev from source:

```bash
# Install/update GAO-Dev
pip install -e .

# Verify installation
gao-dev --version
```

### Quick Start

Navigate to your project directory and start the chat interface:

```bash
cd /path/to/your/project
gao-dev start
```

Brian will greet you with your project status:

```
Welcome to GAO-Dev!

I'm Brian, your AI Engineering Manager.

Project: my-awesome-app
Epics: 5 | Stories: 32
Current Epic: Epic 5: User Authentication

Recent Activity:
  - feat(epic-5): Story 5.3 - Login UI Component
  - feat(epic-5): Story 5.2 - JWT Token Service
  - feat(epic-5): Story 5.1 - User Model & Database

Type your requests in natural language, or type 'help' for available commands.
Type 'exit', 'quit', or 'bye' to end the session.

You: _
```

---

## Basic Usage

### Making Your First Request

Just type what you want to build in natural language:

```
You: I want to add a password reset feature

Brian: Let me analyze that for you...

Brian: I've analyzed your request. Here's what I found:

Scale Level: Level 2 - Small feature (1-2 weeks, light planning)
Project Type: feature

Reasoning: This is an enhancement to your existing authentication system

Recommended Workflows:
  1. create_prd
  2. create_stories
  3. implement_stories

Estimated Duration: 1-2 days

Shall I proceed with this plan? (yes/no)

You: yes

Brian: Great! I'll coordinate with the team...
Brian: [1/3] create_prd...
Brian: ✓ create_prd complete!
Brian: [2/3] create_stories...
Brian: ✓ create_stories complete!
Brian: [3/3] implement_stories...
Brian: ✓ implement_stories complete!
Brian: All workflows completed successfully!
```

### Understanding Scale Levels

Brian analyzes your request and selects the appropriate scale level:

| Level | Type | Duration | Planning | Example |
|-------|------|----------|----------|---------|
| **0** | Quick Chore | < 1 hour | None | "Fix typo in README" |
| **1** | Bug Fix | 1-4 hours | Minimal | "Fix login validation bug" |
| **2** | Small Feature | 1-2 weeks | Light | "Add password reset" |
| **3** | Medium Feature | 1-2 months | Full | "Build notification system" |
| **4** | Greenfield App | 2-6 months | Comprehensive | "Build complete e-commerce platform" |

The scale level determines which workflows are executed and how much planning is done.

---

## Common Workflows

### Building a New Feature

```
You: I want to add email notifications

Brian: [Analyzes...]
Brian: This is a Level 2 feature requiring:
  1. create_prd
  2. create_architecture
  3. create_stories
  4. implement_stories

Shall I proceed with this plan? (yes/no)

You: yes

Brian: Great! I'll coordinate with the team...
[Workflows execute with progress updates]
Brian: All workflows completed successfully!
```

### Fixing a Bug

```
You: Fix the bug where login fails on mobile

Brian: [Analyzes...]
Brian: This is a Level 1 bug fix requiring:
  1. create_story
  2. implement_fix
  3. add_tests

Shall I proceed? (yes/no)

You: yes

[Workflows execute]
```

### Multi-Turn Refinement

Build on previous requests to refine your plan:

```
You: I want to build a blog

Brian: [Analyzes blog feature...]

You: And add comments

Brian: Building on your previous request...
[Analyzes blog + comments together]

You: Also add user profiles

Brian: Now analyzing all three features together...
[Provides comprehensive plan for blog + comments + profiles]
```

Brian remembers the conversation context and combines related requests intelligently.

---

## Initialization Commands

### Starting a New Project (Greenfield)

If you're in an empty directory:

```
You: init

Brian: Welcome! Let's set up your new GAO-Dev project.

Creating project structure for 'my-project'...
✓ Project directories created
✓ Git repository initialized
✓ README.md created
✓ .gitignore created
✓ Initial commit created

Project 'my-project' initialized successfully!

You're all set! What would you like to build first?
```

### Adding GAO-Dev to Existing Project (Brownfield)

If you have an existing codebase without GAO-Dev tracking:

```
You: init

Brian: I see you have an existing project. Let me add GAO-Dev tracking...

Analyzing existing structure...
✓ Detected Python project with Flask
✓ Created .gao-dev/ directory
✓ Initialized document tracking
✓ Created initial README (preserved existing content)

GAO-Dev tracking initialized! Your existing code is safe.

What would you like to work on?
```

---

## Help System

### Getting Help

```
You: help

Brian: I'm here to help you build software! Here's what I can do:

Feature Requests: Just describe what you want to build
  - "I want to add authentication"
  - "Build a todo app with a REST API"
  - "Fix the bug in the login flow"

Project Information:
  - "What's the status?" - Current project state
  - "What should I work on next?" - Suggestions

Commands:
  - 'help' - Show this message
  - 'exit', 'quit', 'bye' - End session

Just type naturally and I'll figure out what you need!
```

### Context-Specific Help

You can also ask specific questions:

```
You: How do I create a PRD?

Brian: I can create a PRD for you! Just describe your feature:
  "I want to build [feature description]"

I'll analyze it and create a comprehensive PRD using John (Product Manager).

You: What workflows are available?

Brian: I have access to 55+ workflows across 4 phases:
  - Analysis: Project assessment, requirements gathering
  - Planning: PRD creation, story breakdown
  - Solutioning: Architecture, technical design
  - Implementation: Coding, testing, deployment

Just describe what you want and I'll select the right workflows!
```

---

## Session Management

### Session History

Brian automatically saves your conversation history when you exit:

```
You: exit

Brian: Goodbye! Great work today. See you next time!

Session Stats:
- Conversation turns: 12
- Memory usage: 2.3 MB
- Session saved to: last_session_history.json
```

### Restoring Previous Session

When you restart, Brian can optionally restore your previous session:

```
$ gao-dev start

[Brian detects previous session]
Brian: Found previous session history from 2025-11-10.
Brian: (Auto-loading for reference - you can start fresh anytime)
```

Note: In current version (1.0), session history is preserved but not automatically restored. Future versions may add interactive restoration prompts.

---

## Advanced Features

### Cancelling Operations

Press **Ctrl+C** during any long-running operation to cancel:

```
You: Build a complete e-commerce platform

Brian: [Starts executing workflows...]
Brian: [1/15] create_prd...
[User presses Ctrl+C]

Operation cancelled by user

You: [REPL continues - you can try a different approach]
```

The REPL won't exit - you can immediately start a different request.

### Input History

Use **arrow keys** to recall previous inputs:

- **Up Arrow**: Previous input
- **Down Arrow**: Next input

This works just like your terminal shell!

### Confirmation Workflow

For every analysis, Brian asks for confirmation before executing:

```
Brian: Shall I proceed with this plan? (yes/no)

You: yes       → Executes workflows
You: no        → Cancels, asks for alternative
You: not sure  → Brian provides more details
```

You're always in control.

---

## Tips & Tricks

### Be Natural

Brian understands natural language. Don't overthink it:

**Good Examples**:
- "I want to build a todo app"
- "Add authentication to the project"
- "Fix the bug where users can't login"
- "Help me create tests for the API"

**Also Works**:
- "Build todo app"
- "Add auth"
- "Fix login bug"
- "Create tests"

### Use Context

Brian remembers your conversation. Build on previous requests:

```
You: I want to build a blog

Brian: [Analyzes...]

You: And add comments
     ^^^ Refers to the blog from previous message

Brian: Building on your blog request, I'll add commenting functionality...
```

### Ask Questions

Don't know what to do? Just ask:

```
You: What should I work on next?

Brian: Based on your current epic (Epic 5: User Authentication),
       I recommend completing Story 5.4: Password Reset Flow.

       Would you like me to create a plan for that?
```

### Check Progress

Ask for status updates:

```
You: What's the status?

Brian: [Displays current project status]

You: How many stories are left in Epic 5?

Brian: Epic 5 has 2 remaining stories:
  - Story 5.4: Password Reset Flow
  - Story 5.5: Integration Tests
```

---

## Exiting the REPL

Multiple ways to exit gracefully:

```
You: exit
You: quit
You: bye
You: goodbye

[Or press Ctrl+D]
```

Brian will save your session and show stats:

```
Brian: Goodbye! Great work today. See you next time!

Session Stats:
- Conversation turns: 8
- Memory usage: 1.5 MB
- Session saved to: last_session_history.json
```

---

## Troubleshooting

### "No GAO-Dev project detected"

**Problem**: You're in a directory without `.gao-dev/`

**Solution**:
```
You: init
```

Brian will initialize a new project or add tracking to existing code.

### "I'm not sure what you mean"

**Problem**: Brian couldn't understand your request

**Solution**: Rephrase more clearly:
- ❌ "Do the thing"
- ✅ "I want to build a todo app"

Or try:
```
You: help
```

### Slow First Response

**Problem**: First analysis takes 2-3 seconds

**Explanation**: This is normal - Brian is analyzing your request with AI. Subsequent responses are faster (< 1 second) due to caching.

**Tip**: Be patient on first request. Once Brian understands your project context, responses speed up significantly.

### Errors During Execution

**Problem**: Workflow execution fails with error

**What Happens**:
```
Brian: Execution failed: [error message]
Brian: Would you like to try a different approach?

You: [REPL continues - you can retry or try something else]
```

**Solution**:
- Read the error message
- Try rephrasing your request
- Ask Brian for help: `help me fix this`
- Check project setup: `What's the status?`

The REPL never crashes - you can always continue working.

### Session Not Saving

**Problem**: Session history not persisting

**Check**:
1. Does `.gao-dev/` directory exist?
   - If not: `You: init`
2. Do you have write permissions?
   - Check directory permissions
3. Is disk full?
   - Free up space

**Workaround**: Session state is also kept in memory during the session, so you can continue working. Just may not persist across restarts.

---

## Performance Expectations

### Startup Time

- **Target**: < 2 seconds from command to greeting
- **Typical**: 0.5 - 1.5 seconds

### Response Times

- **First analysis**: 2-3 seconds (AI processing)
- **Subsequent analyses**: < 1 second (caching)
- **Help commands**: Instant
- **Status queries**: < 100ms

### Memory Usage

- **Typical session**: 10-50 MB
- **Long session (100+ turns)**: 50-100 MB
- **Warning threshold**: 200 MB (session will recommend restart)

---

## Command Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show help information | `You: help` |
| `init` | Initialize project (greenfield or brownfield) | `You: init` |
| `exit` | Exit REPL (saves session) | `You: exit` |
| `quit` | Alias for exit | `You: quit` |
| `bye` | Alias for exit | `You: bye` |

### Natural Language Patterns

| Pattern | Brian's Action | Example |
|---------|----------------|---------|
| "I want to build [X]" | Analyze and propose workflows | "I want to build a blog" |
| "Add [feature]" | Analyze feature addition | "Add authentication" |
| "Fix [bug]" | Analyze bug fix | "Fix login bug" |
| "What's the status?" | Show project status | "What's the status?" |
| "Help me [action]" | Provide guidance | "Help me create tests" |

### Confirmation Responses

| Response | Action |
|----------|--------|
| `yes` | Execute proposed workflows |
| `no` | Cancel, ask for alternative |
| `not sure` | Show more details |
| `tell me more` | Explain workflows |

---

## Best Practices

### 1. Start with Clear Requests

**Good**:
```
You: I want to add user authentication with JWT tokens
```

**Better**:
```
You: I want to add user authentication with JWT tokens, including login, logout, and password reset
```

The more specific you are, the better Brian can analyze and plan.

### 2. Review Before Confirming

Always read Brian's analysis before saying "yes":

```
Brian: Shall I proceed with this plan? (yes/no)

[REVIEW]:
- Scale level makes sense?
- Workflows look appropriate?
- Estimated duration reasonable?

You: yes  [Only if everything looks good]
```

### 3. Use Multi-Turn Conversations

Don't try to describe everything in one message. Build iteratively:

```
You: I want to build a blog

Brian: [Analyzes basic blog...]

You: With Markdown support

Brian: [Updates analysis with Markdown...]

You: And syntax highlighting for code

Brian: [Final comprehensive analysis with all features...]
```

### 4. Ask Questions Freely

If you're unsure about anything:

```
You: What does Level 2 mean?

Brian: Level 2 is a small feature requiring 1-2 weeks with light planning...

You: What workflows will run?

Brian: For this request, I'll run:
  1. create_prd - John will create Product Requirements Document
  2. create_stories - Bob will break into implementable stories
  3. implement_stories - Amelia will code the solution
```

### 5. Save Long Sessions

For long coding sessions (> 100 turns), consider periodic exits to save:

```
You: [After 50+ turns]
You: exit

[Restart]
$ gao-dev start

You: [Continue working - fresh memory, saved history]
```

This prevents memory buildup and ensures progress is saved.

---

## Integration with Existing Workflows

### Works Alongside CLI

The chat interface doesn't replace the CLI - it complements it:

```bash
# Traditional CLI (still works)
gao-dev create-prd --name "My Feature"
gao-dev list-workflows
gao-dev health

# Interactive chat (new)
gao-dev start
> I want to create a PRD for my feature
```

Use whichever feels more natural for the task.

### Session Context Awareness

Brian is aware of work done outside the REPL:

```
[You create Epic 5 via CLI]
$ gao-dev state create-epic 5 "User Auth"

[Later, in REPL]
$ gao-dev start

Brian: [Shows Epic 5 in status]
Brian: I see you're working on Epic 5: User Auth

You: Create stories for Epic 5

Brian: [Creates stories for Epic 5]
```

All GAO-Dev tools share the same state database (`.gao-dev/documents.db`).

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+C** | Cancel current operation (REPL continues) |
| **Ctrl+D** | Exit REPL gracefully |
| **Up Arrow** | Previous input (history) |
| **Down Arrow** | Next input (history) |
| **Ctrl+U** | Clear current line |
| **Ctrl+K** | Delete from cursor to end of line |
| **Ctrl+A** | Move cursor to beginning of line |
| **Ctrl+E** | Move cursor to end of line |

These are standard `prompt-toolkit` shortcuts and work like your terminal.

---

## Examples Gallery

### Example 1: New Feature Request

```
You: I want to add a search feature to the blog

Brian: Let me analyze that for you...

Brian: I've analyzed your request. Here's what I found:

Scale Level: Level 2 - Small feature (1-2 weeks, light planning)
Project Type: feature

Reasoning: Search functionality for existing blog system

Recommended Workflows:
  1. create_prd
  2. create_stories
  3. implement_stories

Estimated Duration: 1 week

Shall I proceed with this plan? (yes/no)

You: yes

Brian: Great! I'll coordinate with the team...
[Workflows execute]
Brian: All workflows completed successfully!
```

### Example 2: Bug Fix

```
You: The login form doesn't validate email format

Brian: Let me analyze that for you...

Brian: I've analyzed your request. Here's what I found:

Scale Level: Level 1 - Bug fix (1-4 hours, minimal planning)
Project Type: bug

Reasoning: Input validation issue in existing feature

Recommended Workflows:
  1. create_bugfix_story
  2. implement_fix
  3. add_test

Estimated Duration: 2-3 hours

Shall I proceed with this plan? (yes/no)

You: yes

[Workflows execute]
```

### Example 3: Greenfield Project

```
$ cd empty-directory
$ gao-dev start

Brian: Welcome to GAO-Dev!

I'm Brian, your AI Engineering Manager.

No GAO-Dev project detected in current directory.
Would you like to initialize a new project? Type 'init' to get started.

You: init

Brian: Welcome! Let's set up your new GAO-Dev project.

What would you like to name this project? (or press Enter for 'empty-directory')

You: awesome-saas-app

Brian: Creating project structure for 'awesome-saas-app'...
✓ Project directories created
✓ Git repository initialized
✓ README.md created
✓ .gitignore created
✓ Initial commit created

Project 'awesome-saas-app' initialized successfully!

You're all set! What would you like to build first?

You: I want to build a SaaS application with user management, subscription billing, and admin dashboard

Brian: [Analyzes greenfield app...]

Brian: This is a Level 4 greenfield application requiring comprehensive planning.

[Proposes full BMAD workflow]
```

---

## Further Reading

### Documentation

- **[Architecture Guide](./ARCHITECTURE.md)** - Technical design and component details
- **[PRD](./PRD.md)** - Product requirements and user stories
- **[Epic Breakdown](./epics/epic-30-interactive-chat.md)** - Story-by-story implementation details

### Related Features

- **[Workflow System](../workflow-driven-core/)** - How Brian selects workflows
- **[Document Lifecycle](../document-lifecycle-system/)** - How documents are tracked
- **[Self-Learning System](../self-learning-feedback-loop/)** - How Brian learns from experience

### Plugin Development

Want to extend the chat interface?

- **[Plugin Development Guide](../../../docs/plugin-development-guide.md)** - Create custom agents and workflows

---

## Support & Feedback

### Getting Help

1. **In the REPL**: Type `help`
2. **Documentation**: Check this guide and related docs
3. **CLI Health Check**: `gao-dev health`
4. **GitHub Issues**: Report bugs or request features

### Reporting Issues

When reporting issues, include:

1. What you typed
2. What Brian responded
3. What you expected
4. Session logs (if available)

Example:
```
I typed: "Build a todo app"
Brian said: "I'm not sure what you mean"
Expected: Brian should analyze as Level 2 feature
Logs: [attach .gao-dev/logs/]
```

### Feature Requests

We'd love to hear your ideas! Consider:

- What workflows would you like to see?
- What makes conversations feel unnatural?
- What features would save you time?

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-10 | Initial release with Epic 30 completion |

---

**Happy Building with Brian!** 🚀

Start your next conversation:
```bash
$ gao-dev start
```
