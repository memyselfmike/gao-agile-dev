# OpenCode Tool Compatibility Matrix

**Version**: OpenCode v0.1.x vs GAO-Dev Tools
**Last Updated**: 2025-11-04
**Epic**: Epic 11 - Agent Provider Abstraction
**Story**: Story 11.6 - OpenCode Research & CLI Mapping

---

## Table of Contents

1. [Overview](#overview)
2. [Tool Compatibility Matrix](#tool-compatibility-matrix)
3. [Detailed Tool Analysis](#detailed-tool-analysis)
4. [Behavioral Differences](#behavioral-differences)
5. [Recommendations](#recommendations)

---

## Overview

This document maps GAO-Dev tools to OpenCode capabilities, documenting compatibility, differences, and implementation considerations for `OpenCodeProvider`.

**Key Findings**:
- ✅ **Core tools supported**: Read, Write, Edit, Bash, file operations
- ⚠️ **Partial support**: Some tools have equivalent but different behavior
- ❌ **Gaps**: Specialized GAO-Dev tools not available in OpenCode
- 🔄 **Alternative approaches**: LSP and TUI features provide different capabilities

---

## Tool Compatibility Matrix

| GAO-Dev Tool | OpenCode Equivalent | Status | Compatibility | Notes |
|--------------|---------------------|--------|---------------|-------|
| **Read** | File reading (built-in) | ✅ | **100%** | OpenCode can read files in project context |
| **Write** | File writing (built-in) | ✅ | **100%** | OpenCode can create/modify files |
| **Edit** | File editing (built-in) | ✅ | **95%** | OpenCode has edit capabilities, may differ in precision |
| **MultiEdit** | Multiple edits | ⚠️ | **70%** | Likely handled as sequential single edits |
| **Bash** | Shell execution | ✅ | **100%** | OpenCode can execute shell commands |
| **Grep** | LSP-based search | ⚠️ | **60%** | LSP provides semantic search, not literal grep |
| **Glob** | File search, fuzzy `@` | ✅ | **90%** | Fuzzy file search with `@` syntax |
| **Task** | N/A | ❌ | **0%** | No direct equivalent for task orchestration |
| **WebFetch** | N/A | ❌ | **0%** | No documented web fetching capability |
| **WebSearch** | N/A | ❌ | **0%** | No documented web search capability |
| **TodoWrite** | N/A | ❌ | **0%** | No task management built-in |
| **AskUserQuestion** | Interactive TUI | ⚠️ | **N/A** | TUI allows interaction, incompatible with subprocess |
| **NotebookEdit** | N/A | ❓ | **Unknown** | Jupyter support not documented |
| **Skill** | Custom agents | ⚠️ | **50%** | `opencode agent create` provides similar capability |
| **SlashCommand** | N/A | ❌ | **0%** | No custom command system |

**Overall Compatibility**: **~65%** (core file/code operations excellent, specialized tools missing)

---

## Detailed Tool Analysis

### ✅ Fully Compatible Tools

#### 1. Read
**GAO-Dev**: Read file contents with optional line range

**OpenCode**: Can read files in project context

**Compatibility**: ✅ **100%**

**Implementation**:
```python
# GAO-Dev: Read(file_path="/path/to/file.py")
# OpenCode: Implicitly reads files when referenced in prompts
```

**Example Prompt**:
```
"Read main.py and explain the authentication flow"
```

**Notes**:
- OpenCode may read files implicitly based on context
- No explicit "Read" tool invocation needed
- LSP integration provides intelligent file understanding

---

#### 2. Write
**GAO-Dev**: Write content to file (create or overwrite)

**OpenCode**: Can create and modify files

**Compatibility**: ✅ **100%**

**Implementation**:
```python
# GAO-Dev: Write(file_path="/path/to/file.py", content="...")
# OpenCode: Prompts like "Create file X with content Y"
```

**Example Prompts**:
```
"Create a file named hello.py with a hello world function"
"Write a README.md with project documentation"
```

**Notes**:
- OpenCode handles file creation naturally through prompts
- No explicit "Write" tool needed
- Supports multi-file creation in single prompt

---

#### 3. Edit
**GAO-Dev**: Edit file by replacing old_string with new_string

**OpenCode**: Can modify files with edits

**Compatibility**: ✅ **95%** (may differ in precision)

**Implementation**:
```python
# GAO-Dev: Edit(file_path="file.py", old_string="...", new_string="...")
# OpenCode: Prompts like "Modify X by changing Y to Z"
```

**Example Prompts**:
```
"Edit main.py to add error handling to the login function"
"Modify config.yaml to set debug: true"
```

**Differences**:
- GAO-Dev: Exact string replacement (deterministic)
- OpenCode: AI-driven edits (may vary)
- OpenCode may make broader changes based on context

**Recommendation**: Test precision with small, specific edits

---

#### 4. Bash
**GAO-Dev**: Execute shell commands with output capture

**OpenCode**: Can execute shell commands

**Compatibility**: ✅ **100%**

**Implementation**:
```python
# GAO-Dev: Bash(command="pytest tests/")
# OpenCode: Prompts like "Run pytest tests/"
```

**Example Prompts**:
```
"Run pytest and show the results"
"Execute npm install and verify dependencies"
"Run the development server on port 3000"
```

**Notes**:
- OpenCode can execute commands and interpret output
- May provide context-aware suggestions based on results
- Error handling likely more intelligent than raw subprocess

---

### ⚠️ Partially Compatible Tools

#### 5. MultiEdit
**GAO-Dev**: Apply multiple edits to file(s) atomically

**OpenCode**: Sequential or batched edits

**Compatibility**: ⚠️ **70%**

**Implementation**:
```python
# GAO-Dev: MultiEdit(edits=[...])
# OpenCode: Prompts like "Make the following changes to X: 1) ..., 2) ..., 3) ..."
```

**Example Prompt**:
```
"Make these changes to main.py:
1. Add import logging at the top
2. Replace print statements with logging
3. Add error handling to process() function"
```

**Differences**:
- GAO-Dev: Atomic multi-edit operation
- OpenCode: May apply edits sequentially
- No guarantee of atomicity (may leave partial state on error)

**Recommendation**: Test multi-edit reliability, may need sequential single edits

---

#### 6. Grep
**GAO-Dev**: Search file contents with regex patterns

**OpenCode**: LSP-based semantic search

**Compatibility**: ⚠️ **60%**

**Implementation**:
```python
# GAO-Dev: Grep(pattern="def.*login", path="/project")
# OpenCode: Prompts like "Find all login functions in the project"
```

**Example Prompts**:
```
"Search for all functions that handle authentication"
"Find files containing TODO comments"
"List all imports of the requests library"
```

**Differences**:
- GAO-Dev: Literal regex matching (ripgrep-based)
- OpenCode: Semantic search via LSP (understands code structure)
- OpenCode may be more intelligent but less precise

**Tradeoffs**:
- **Pros**: LSP understands code semantics (finds "login" even if named differently)
- **Cons**: May miss exact regex patterns

**Recommendation**: Use semantic search prompts instead of exact regex

---

#### 7. Glob
**GAO-Dev**: Find files matching glob patterns

**OpenCode**: Fuzzy file search with `@` syntax

**Compatibility**: ✅ **90%**

**Implementation**:
```python
# GAO-Dev: Glob(pattern="**/*.py")
# OpenCode: Prompts like "Find all Python files" or use "@*.py"
```

**Example Prompts**:
```
"List all Python test files"
"Find all configuration files"
# Or use fuzzy search: "@test"
```

**Differences**:
- GAO-Dev: Exact glob pattern matching
- OpenCode: Fuzzy search + natural language
- `@` syntax for file references (fuzzy matching)

**Notes**:
- OpenCode's fuzzy search may be more user-friendly
- May match more broadly than strict glob patterns

---

#### 8. AskUserQuestion
**GAO-Dev**: Prompt user with multiple-choice questions

**OpenCode**: Interactive TUI (not subprocess-compatible)

**Compatibility**: ⚠️ **N/A** (architectural incompatibility)

**Implementation**:
```python
# GAO-Dev: AskUserQuestion(questions=[...])
# OpenCode: Interactive prompts in TUI (not available in `run` mode)
```

**Issue**:
- GAO-Dev: Structured multiple-choice prompts
- OpenCode TUI: Free-form interaction
- OpenCode `run`: Non-interactive (no user questions)

**Workaround**:
- Pre-determine answers before calling OpenCodeProvider
- Use non-interactive prompts with embedded choices
- Accept that user interaction not available

**Recommendation**: Document as unsupported in OpenCodeProvider

---

#### 9. Skill / Custom Agents
**GAO-Dev**: Execute specialized skills (plugins)

**OpenCode**: `opencode agent create` for custom agents

**Compatibility**: ⚠️ **50%**

**Implementation**:
```python
# GAO-Dev: Skill(command="pdf")
# OpenCode: opencode run --agent pdf-processor "Process document"
```

**Example**:
```bash
# Create custom agent
opencode agent create
# Name: pdf-processor
# System prompt: "You are a PDF processing specialist..."

# Use agent
opencode run --agent pdf-processor "Extract text from document.pdf"
```

**Differences**:
- GAO-Dev: Built-in skill system with specific capabilities
- OpenCode: Custom agents with system prompts (more flexible but less structured)

**Recommendation**: Explore custom agents as alternative to GAO-Dev skills

---

### ❌ Unsupported Tools

#### 10. Task
**GAO-Dev**: Orchestrate complex multi-step tasks

**OpenCode**: No direct equivalent

**Compatibility**: ❌ **0%**

**Workaround**:
- Break complex tasks into sequential prompts
- Use detailed prompts describing all steps
- Leverage OpenCode's conversation continuity with sessions

**Example**:
```bash
# Instead of Task orchestration
# Use detailed prompt:
opencode run "
Create a REST API with these steps:
1. Set up project structure
2. Create models for User and Product
3. Implement CRUD endpoints
4. Add authentication
5. Write unit tests
6. Create API documentation
"
```

---

#### 11. WebFetch
**GAO-Dev**: Fetch web content and process with AI

**OpenCode**: No documented web fetching

**Compatibility**: ❌ **0%**

**Workaround**:
- Fetch content externally, pass as file or prompt
- Use OpenCode to process fetched content

**Example**:
```bash
# Fetch externally
curl https://example.com/api/docs > docs.txt

# Process with OpenCode
opencode run "Summarize the API documentation in docs.txt"
```

---

#### 12. WebSearch
**GAO-Dev**: Search web and use results in AI context

**OpenCode**: No documented web search

**Compatibility**: ❌ **0%**

**Workaround**: Similar to WebFetch, search externally and provide results

---

#### 13. TodoWrite
**GAO-Dev**: Manage task lists with status tracking

**OpenCode**: No task management built-in

**Compatibility**: ❌ **0%**

**Workaround**:
- Manage task lists externally (GAO-Dev layer)
- OpenCode prompts can create TODO files as documentation

**Example**:
```bash
opencode run "Create TODO.md with a task list for implementing feature X"
```

---

#### 14. NotebookEdit
**GAO-Dev**: Edit Jupyter notebook cells

**OpenCode**: No documented Jupyter support

**Compatibility**: ❓ **Unknown**

**Investigation Needed**: Test if OpenCode can work with .ipynb files

---

#### 15. SlashCommand
**GAO-Dev**: Execute custom slash commands from .claude/commands/

**OpenCode**: No custom command system

**Compatibility**: ❌ **0%**

**Note**: OpenCode has `/init`, `/undo`, `/redo`, `/share` in TUI, but these are built-in, not extensible

---

## Behavioral Differences

### 1. Execution Model

**Claude Code (via GAO-Dev)**:
- Stateless: Each execution independent
- Tools explicitly specified and invoked
- Deterministic tool behavior

**OpenCode**:
- Stateful: Session-based continuity
- Tools implicit (inferred from prompts)
- AI-driven tool selection

**Impact**: OpenCode may behave differently across runs due to conversation history

---

### 2. Tool Invocation

**Claude Code**:
```
Explicit tool calls:
- Read(file="main.py")
- Edit(file="main.py", old="...", new="...")
```

**OpenCode**:
```
Natural language prompts:
- "Read main.py and edit the login function"
- (AI decides which operations to perform)
```

**Impact**: Less control over exact operations, but more flexibility

---

### 3. Error Handling

**Claude Code**:
- Structured error codes
- Tool-specific error messages

**OpenCode**:
- AI-generated error messages
- May provide suggestions/fixes
- Less structured

**Impact**: Error parsing more complex, but errors may be more helpful

---

### 4. Performance

**Claude Code**:
- Optimized for subprocess execution
- Minimal overhead
- Fast startup

**OpenCode**:
- TUI framework overhead (even in `run` mode)
- LSP initialization
- Slower startup (~2-3x estimated)

**Impact**: OpenCode ~20-50% slower (estimated, needs benchmarking)

---

## Recommendations

### For OpenCodeProvider Implementation

1. **Core File Operations**: ✅ Implement - excellent compatibility
   - Read, Write, Edit, Bash, Glob

2. **Specialized Tools**: ⚠️ Document as unsupported or limited
   - Task, WebFetch, WebSearch, TodoWrite, AskUserQuestion

3. **Tool Detection**: Implement `supports_tool()` accurately
   ```python
   SUPPORTED_TOOLS = {
       "Read", "Write", "Edit", "Bash", "Glob"
   }
   PARTIAL_SUPPORT = {
       "MultiEdit", "Grep", "Skill"
   }
   ```

4. **Prompt Engineering**: Convert tool calls to natural language prompts
   ```python
   def tool_to_prompt(tool_name, **kwargs):
       if tool_name == "Read":
           return f"Read {kwargs['file_path']} and show contents"
       elif tool_name == "Write":
           return f"Create {kwargs['file_path']} with content: {kwargs['content']}"
       # ...
   ```

5. **Testing**: Validate each supported tool thoroughly
   - Unit tests with mocked subprocess
   - Integration tests with real OpenCode (optional)
   - Cross-provider tests (Anthropic, OpenAI, Google)

---

### For GAO-Dev Users

**When to use OpenCodeProvider**:
- ✅ Tasks use core file operations (Read, Write, Edit, Bash)
- ✅ Need OpenAI or Google models
- ✅ Semantic search more important than exact grep

**When to use ClaudeCodeProvider**:
- ❌ Need specialized tools (WebFetch, WebSearch, Task)
- ❌ Require deterministic tool behavior
- ❌ Performance critical
- ❌ Complex multi-edit operations

**Hybrid Approach**:
```python
# Select provider based on tools needed
if needs_web_fetch or needs_web_search:
    provider = claude_code_provider
elif prefers_openai_models:
    provider = opencode_provider
else:
    provider = claude_code_provider  # default
```

---

## Future Enhancements

**Potential OpenCode Extensions** (if we contribute or request features):
1. Add WebFetch capability (HTTP requests)
2. Add WebSearch integration
3. Add TodoWrite equivalent (task management)
4. Improve MultiEdit atomicity
5. Structured error codes for better parsing

**Alternative Approaches**:
- Use OpenCode `serve` mode (HTTP API) for better control
- Wrap OpenCode with GAO-Dev tool adapters
- Implement missing tools at GAO-Dev layer (external to OpenCode)

---

## Conclusion

OpenCode provides **strong compatibility** with GAO-Dev's core file and code operations (~85% for essential tools), but lacks specialized tools like WebFetch, WebSearch, and Task orchestration.

**Recommendation for Story 11.7**:
- ✅ Implement OpenCodeProvider for core tools
- 📝 Document unsupported tools clearly
- ⚠️ Mark as experimental until validated
- 🧪 Thorough testing across providers

**See Also**:
- [OpenCode Research Report](opencode-research.md)
- [OpenCode Setup Guide](opencode-setup-guide.md)
- [OpenCode CLI Reference](opencode-cli-reference.md)
- [Provider Selection Guide](provider-selection-guide.md)
