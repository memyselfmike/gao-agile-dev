# Documentation Skill

**Skill Name**: documentation
**Purpose**: Create, review, and maintain agent-optimized documentation
**Agent**: document-keeper
**Tools Available**: Read, Write, Edit, Grep, Glob, Bash

---

## When to Use This Skill

Invoke this skill when you need to:
- ✅ Create quick-start guides for integration patterns
- ✅ Add TL;DR sections to existing documentation
- ✅ Generate API reference documentation
- ✅ Review documentation for token efficiency and actionability
- ✅ Extract code examples from codebase
- ✅ Validate documentation links and cross-references
- ✅ Create agent-specific integration guides
- ✅ Optimize documentation structure for AI agents

**Do NOT use this skill for**:
- ❌ Writing code (use developer skill)
- ❌ Architecture design (use architect skill)
- ❌ Testing (use ui-testing or bug-verification skills)

---

## Documentation Quality Standards

### Token Efficiency Requirements

| Document Type | Max Tokens | Required Sections |
|---------------|------------|-------------------|
| TL;DR Section | 100 | What, Why, Key Points |
| Quick-Start Guide | 2,000 | TL;DR, Steps, Examples, Testing, Issues |
| Agent Integration Guide | 3,000 | Role, Integration Points, Patterns, Tasks |
| API Reference | N/A | Tables (scannable lookup) |

### Actionability Requirements

**Every guide MUST include**:
1. ✅ Copy-paste ready code examples
2. ✅ Complete workflows (not fragments)
3. ✅ Error handling examples
4. ✅ Testing patterns
5. ✅ Common issues table

**Code Example Format**:
```markdown
### Example: [Descriptive Name]

**Use case**: [When you'd use this]

**File**: `path/to/file.py`

\```python
# Complete, working example with comments
from module import Class

def function():
    # Step 1: Setup
    instance = Class()

    # Step 2: Execute
    result = instance.method()

    # Step 3: Handle errors
    if not result:
        raise ValueError("Description")

    return result
\```

**Testing**:
\```python
def test_function():
    result = function()
    assert result is not None
\```

**Common issues**:
| Issue | Cause | Fix |
|-------|-------|-----|
| Error X | Missing Y | Install Y: `pip install Y` |
```

---

## Documentation Workflow

### Phase 1: Analysis

**Goal**: Understand what needs to be documented and for whom

**Steps**:
1. **Identify audience**
   ```bash
   # Ask: Who will use this documentation?
   - Which agents? (Brian, Amelia, Winston, etc.)
   - Which users? (Developers, DevOps, etc.)
   - What task are they trying to accomplish?
   ```

2. **Assess existing documentation**
   ```bash
   # Use Grep to find related docs
   grep -r "topic name" docs/

   # Check for gaps
   - Is there a quick-start guide?
   - Are there code examples?
   - Is there an API reference?
   ```

3. **Determine document type needed**
   ```bash
   # Decision tree:
   - Need quick answer? → TL;DR section
   - Need to implement feature? → Quick-Start Guide
   - Need API details? → API Reference
   - Need role-specific guidance? → Agent Integration Guide
   ```

### Phase 2: Structure Design

**Goal**: Plan information architecture before writing

**Quick-Start Guide Structure**:
```markdown
# Quick Start: [Topic]

## 🚀 TL;DR
[50-100 tokens: What, when, key steps]

## Prerequisites
- [Required knowledge/tools]

## Step-by-Step Guide

### Step 1: [Action Verb]
[Code example]
[Brief explanation]

### Step 2: [Action Verb]
[Code example]
[Brief explanation]

## Testing Your Implementation
[Test code example]

## Common Issues
[Table of problems and solutions]

## See Also
[Links with purpose statements]

**Estimated tokens**: ~1,500
```

**API Reference Structure**:
```markdown
# API Reference: [Component]

## REST Endpoints

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| POST | /api/x | Do Y | `{...}` | `{...}` |

### Examples

#### POST /api/x
[Request/response examples]

## WebSocket Events

| Event | Direction | When | Data |
|-------|-----------|------|------|
| x.y | S→C | ... | `{...}` |

**Estimated tokens**: ~2,000 (lookup)
```

**Agent Integration Guide Structure**:
```markdown
# [Agent]'s Integration Guide

## Your Role
[1-2 sentences]

## Key Integration Points

### [Integration Point 1]
**When**: [Scenario]
**Code**: [Example]
**Test**: [Test pattern]

## Code Patterns Library

### Pattern: [Name]
**Use when**: [Scenario]
**Example**: [Complete code]

## Common Tasks
[Task list with examples]

**Estimated tokens**: ~2,500
```

### Phase 3: Content Creation

**Goal**: Write actionable documentation with examples

**Best Practices**:

1. **Start with examples, not theory**
   ```markdown
   ❌ Wrong:
   "The API endpoint accepts a JSON payload with the following
   schema which must be validated..."

   ✅ Right:
   ### Example: Call the API

   \```python
   response = await client.post("/api/endpoint", json={
       "field": "value"
   })
   \```

   The endpoint accepts JSON payloads...
   ```

2. **Show complete workflows**
   ```markdown
   ❌ Wrong (fragment):
   \```python
   result = thing.process()
   \```

   ✅ Right (complete):
   \```python
   from gao_dev.module import Thing

   async def complete_workflow():
       # Setup
       thing = Thing(config)

       # Execute
       result = await thing.process()

       # Error handling
       if not result:
           raise ValueError("Processing failed")

       return result
   \```
   ```

3. **Include testing**
   ```markdown
   ### Testing

   \```python
   import pytest

   async def test_workflow():
       result = await complete_workflow()
       assert result is not None
       assert result.status == "success"
   \```
   ```

4. **Document common issues**
   ```markdown
   ## Common Issues

   | Issue | Cause | Fix |
   |-------|-------|-----|
   | `ModuleNotFoundError` | Missing dependency | `pip install module-name` |
   | `TimeoutError` | Service not running | Start service: `gao-dev start` |
   ```

### Phase 4: Optimization

**Goal**: Minimize tokens while maximizing value

**Techniques**:

1. **Use tables over prose**
   ```markdown
   ❌ Wrong (500 tokens):
   "The first endpoint is POST /api/x which is used to create new
   resources. It requires authentication via session token. The
   request should include a JSON payload with fields x and y..."

   ✅ Right (150 tokens):
   | Method | Endpoint | Purpose | Auth | Request |
   |--------|----------|---------|------|---------|
   | POST | /api/x | Create resource | Token | `{x, y}` |
   ```

2. **Use bullet lists**
   ```markdown
   ❌ Wrong:
   "You should first install the dependencies, then configure
   the settings, and finally run the initialization script."

   ✅ Right:
   **Steps**:
   1. Install dependencies: `pip install -r requirements.txt`
   2. Configure: `cp .env.example .env`
   3. Initialize: `gao-dev init`
   ```

3. **Eliminate redundancy**
   ```markdown
   ❌ Wrong:
   "This function does X. When you call this function, it will
   perform X by doing Y. The function is useful when you need X."

   ✅ Right:
   "Performs X by doing Y."
   ```

### Phase 5: Validation

**Goal**: Ensure documentation meets quality standards

**Checklist**:

```markdown
## Documentation Quality Checklist

### Token Efficiency ✓
- [ ] TL;DR present (if >500 lines)
- [ ] TL;DR <100 tokens
- [ ] Quick-start <2,000 tokens
- [ ] Agent guide <3,000 tokens
- [ ] Tables used for data
- [ ] No redundant information

### Actionability ✓
- [ ] Code examples included
- [ ] Examples are complete (not fragments)
- [ ] Error handling shown
- [ ] Testing patterns included
- [ ] Common issues documented

### Agent-Friendliness ✓
- [ ] Inverted pyramid (key facts first)
- [ ] Clear navigation (headers, TOC)
- [ ] Purpose stated for links
- [ ] Decision trees (if complex)

### Accuracy ✓
- [ ] Code examples tested
- [ ] Links validated (no 404s)
- [ ] Synchronized with codebase
- [ ] Terminology consistent
- [ ] Version noted (if applicable)

### Discoverability ✓
- [ ] Linked from parent docs
- [ ] Cross-referenced in related docs
- [ ] Added to documentation index
- [ ] Keywords in title/headers
```

**Testing Examples**:
```bash
# Always test code examples
1. Copy example code to temp file
2. Run the code
3. Verify it works as documented
4. If it fails, fix example or add common issue
```

**Measuring Tokens**:
```bash
# Rough estimate: 1 token ≈ 4 characters
wc -c file.md  # Character count
# Divide by 4 for token estimate

# For precise count, use Claude Code's token counter
# or copy to Claude and check token usage
```

---

## Common Patterns

### Pattern 1: Adding TL;DR to Existing Doc

**When**: Document >500 lines lacks TL;DR

**Steps**:
1. Read entire document
2. Extract key facts:
   - What is this?
   - Why does it exist?
   - Key points (3-5 bullets)
   - Quick links to common tasks

3. Write TL;DR (target: 50-100 tokens):
   ```markdown
   ## 🚀 TL;DR

   **What**: [One sentence describing system/feature]
   **Why**: [One sentence on purpose/value]
   **Key Points**:
   - [Point 1 in <10 words]
   - [Point 2 in <10 words]
   - [Point 3 in <10 words]

   **Quick Start**: [Link to actionable guide]
   **Deep Dive**: [Continue reading below]
   ```

4. Insert at top (after title, before first section)
5. Verify token count
6. Commit with message: `docs: Add TL;DR to [filename]`

### Pattern 2: Creating Quick-Start Guide

**When**: Agents need actionable integration pattern

**Steps**:
1. **Identify pattern**
   ```bash
   # Search codebase for implementations
   grep -r "pattern_name" gao_dev/

   # Find common usage
   # Identify best practice example
   ```

2. **Extract example**
   ```bash
   # Read implementation file
   # Copy representative code
   # Simplify to minimal working example
   ```

3. **Write guide** (use template above)
   - TL;DR (<100 tokens)
   - Prerequisites (tools, knowledge)
   - Step-by-step with code
   - Testing section
   - Common issues table

4. **Test example**
   ```bash
   # Create temp file with example
   # Run the code
   # Verify it works
   # Add error handling if needed
   ```

5. **Optimize tokens**
   - Remove redundancy
   - Use tables where possible
   - Employ bullets over prose
   - Measure token count

6. **Save and link**
   ```bash
   # Save to docs/quick-start/TOPIC.md
   # Link from CLAUDE.md Quick Reference
   # Link from related architecture docs
   # Commit
   ```

### Pattern 3: Generating API Reference

**When**: Need lookup table for endpoints/events

**Steps**:
1. **Collect endpoint information**
   ```bash
   # Search for FastAPI routes
   grep -r "@router\." gao_dev/web/api/

   # For each endpoint, extract:
   # - Method (POST, GET, etc.)
   # - Path (/api/x)
   # - Purpose (docstring or function name)
   # - Request schema (Pydantic model)
   # - Response schema
   ```

2. **Create table**
   ```markdown
   ## REST Endpoints

   | Method | Endpoint | Purpose | Request | Response |
   |--------|----------|---------|---------|----------|
   | POST | /api/chat | Send message | `{message: str}` | `{status, id}` |
   | GET | /api/chat/history | Get history | `?max=50` | `{messages: [...]}` |
   ```

3. **Add examples**
   ```markdown
   ### Example: POST /api/chat

   **Request**:
   \```bash
   curl -X POST http://localhost:3000/api/chat \
     -H "X-Session-Token: abc123" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello"}'
   \```

   **Response**:
   \```json
   {
     "status": "success",
     "message_id": "msg_123"
   }
   \```
   ```

4. **Document WebSocket events** (same pattern)

5. **Save and link**
   ```bash
   # Save to docs/API_REFERENCE.md
   # Link from CLAUDE.md
   # Link from ARCHITECTURE_OVERVIEW.md
   ```

### Pattern 4: Creating Agent Integration Guide

**When**: Agent needs role-specific documentation

**Steps**:
1. **Understand agent role**
   ```bash
   # Read agent config: gao_dev/config/agents/[agent].yaml
   # Read persona: gao_dev/config/agents/personas/[agent].md
   # Identify key responsibilities
   ```

2. **Identify integration points**
   ```bash
   # What services does this agent use?
   # What workflows does this agent execute?
   # What patterns should this agent follow?
   ```

3. **Extract code patterns**
   ```bash
   # Search for agent implementations
   grep -r "agent_name" gao_dev/

   # Find representative examples
   # Extract working patterns
   ```

4. **Write guide** (use agent guide template)
   - Your Role (1-2 sentences)
   - Key Integration Points (3-5 points with examples)
   - Code Patterns Library (common patterns)
   - Common Tasks (task list)
   - Examples Repository (links)

5. **Validate with agent** (simulate agent task)
   - Can agent find what they need?
   - Are examples actionable?
   - Is token count reasonable (<3,000)?

6. **Save and link**
   ```bash
   # Save to docs/agent-guides/[AGENT]_INTEGRATION.md
   # Link from CLAUDE.md Quick Reference
   # Link from agent config
   ```

---

## Tools Usage Patterns

### Using Read Tool
```bash
# Read existing documentation
Read(file_path="docs/ARCHITECTURE_OVERVIEW.md")

# Read code for examples
Read(file_path="gao_dev/web/api/chat.py")

# Read in sections if large (>2000 lines)
Read(file_path="large_file.md", offset=0, limit=500)
```

### Using Grep Tool
```bash
# Find all documentation on topic
Grep(pattern="API endpoint", path="docs/", output_mode="files_with_matches")

# Find code patterns
Grep(pattern="@router.post", path="gao_dev/web/api/", output_mode="content")

# Find broken links
Grep(pattern="\[.*\]\(.*404.*\)", path="docs/", output_mode="content")
```

### Using Glob Tool
```bash
# Find all markdown files
Glob(pattern="**/*.md", path="docs/")

# Find all API route files
Glob(pattern="gao_dev/web/api/*.py")
```

### Using Edit Tool
```bash
# Add TL;DR to existing doc
Edit(
    file_path="docs/ARCHITECTURE_OVERVIEW.md",
    old_string="## Executive Summary",
    new_string="## 🚀 TL;DR\n\n[content]\n\n---\n\n## Executive Summary"
)

# Fix broken link
Edit(
    file_path="docs/guide.md",
    old_string="[Link](broken/path.md)",
    new_string="[Link](correct/path.md)"
)
```

### Using Write Tool
```bash
# Create new quick-start guide
Write(
    file_path="docs/quick-start/ADDING_API_ENDPOINT.md",
    content="[complete guide content]"
)
```

---

## Success Metrics

Track these metrics for documentation quality:

### Efficiency Metrics
- **Time to Answer**: <1 minute for agents to find information
- **Token Consumption**: <1,000 tokens for common tasks
- **First-Attempt Success**: 90%+ agents complete task without additional help

### Quality Metrics
- **Broken Links**: 0 (always)
- **Example Accuracy**: 100% (all examples tested and working)
- **Coverage**: 90%+ of system documented
- **Token Efficiency**: TL;DR <100, Quick-Start <2,000, Agent Guide <3,000

### Impact Metrics
- **Reduced Questions**: Fewer "how do I...?" questions from agents
- **Faster Development**: Agents implement features 2x faster with good docs
- **Higher Code Quality**: Better code from better examples
- **System Evolution**: Documentation enables confident architectural changes

---

## Example: Complete Documentation Task

**Task**: Create quick-start guide for adding WebSocket events

**Execution**:

```markdown
1. Analyze Pattern
   - Grep for existing WebSocket event implementations
   - Identify common pattern
   - Extract best example

2. Structure Guide
   - TL;DR: What, when, key steps
   - Prerequisites: Python knowledge, FastAPI
   - Steps: 1) Define event, 2) Emit, 3) Handle frontend, 4) Test
   - Testing: Complete test example
   - Common Issues: Table of problems

3. Write Content
   # Quick Start: Adding WebSocket Events

   ## 🚀 TL;DR
   **What**: Add real-time events to GAO-Dev web UI
   **When**: Need to notify frontend of backend changes
   **Key Steps**:
   - Define event type in `events.py`
   - Emit via `event_bus.publish()`
   - Handle in `App.tsx`
   - Test with subscriber

   **Time**: 10 minutes

   [Continue with full guide...]

4. Test Examples
   - Create temp files with examples
   - Run backend example
   - Run frontend example
   - Verify WebSocket connection works

5. Optimize
   - Measure tokens: ~1,800 (within <2,000 limit ✓)
   - Check for redundancy
   - Convert prose to bullets where possible

6. Save and Link
   - Save to docs/quick-start/ADDING_WEBSOCKET_EVENT.md
   - Link from CLAUDE.md Quick Reference
   - Link from Web Interface ARCHITECTURE.md
   - Commit: "docs: Add quick-start guide for WebSocket events"
```

---

## Remember

- **Agent-first**: Design for AI consumption, not just humans
- **Examples over theory**: Show working code, explain after
- **Test everything**: All examples must be verified working
- **Token efficiency**: Respect agents' context limits
- **Living docs**: Update as code evolves

**Your goal**: Enable agents to find answers in <1,000 tokens

---

**Skill Status**: Active
**Last Updated**: 2025-11-22
**Maintainer**: document-keeper agent
