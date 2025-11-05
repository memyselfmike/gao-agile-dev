# Story 11.6: OpenCode Research & CLI Mapping

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: None (can run in parallel with Phase 1)

---

## User Story

**As a** GAO-Dev developer
**I want** comprehensive research and documentation on OpenCode CLI
**So that** I can make an informed decision on implementing OpenCodeProvider and understand integration requirements

---

## Acceptance Criteria

### AC1: OpenCode Installation & Setup
- ✅ OpenCode installed locally
- ✅ Bun runtime installed and verified
- ✅ OpenCode CLI tested and working
- ✅ Installation documented with commands
- ✅ Prerequisites documented

### AC2: CLI Interface Documented
- ✅ All CLI flags documented with examples
- ✅ Command structure understood
- ✅ Input format documented
- ✅ Output format analyzed and documented
- ✅ Error handling patterns identified
- ✅ Comparison with Claude Code CLI

### AC3: Provider Support Tested
- ✅ Anthropic provider tested
- ✅ OpenAI provider tested (if API key available)
- ✅ Google provider tested (if API key available)
- ✅ Provider switching documented
- ✅ Provider-specific quirks noted

### AC4: Tool Mapping Created
- ✅ GAO-Dev tools mapped to OpenCode tools
- ✅ Tool compatibility matrix created
- ✅ Unsupported tools identified
- ✅ Tool behavior differences documented

### AC5: Output Format Analysis
- ✅ Streaming output analyzed
- ✅ Progress indicators documented
- ✅ Error message format understood
- ✅ Result parsing strategy defined
- ✅ Comparison with Claude Code output

### AC6: Performance Testing
- ✅ Basic task execution time measured
- ✅ Compared to Claude Code performance
- ✅ Memory usage observed
- ✅ Subprocess overhead measured

### AC7: Known Issues Documented
- ✅ Bugs or limitations identified
- ✅ Workarounds documented
- ✅ Version compatibility noted
- ✅ Platform-specific issues (Windows, Mac, Linux)

### AC8: Go/No-Go Decision
- ✅ Clear recommendation on proceeding with OpenCodeProvider
- ✅ Implementation complexity assessed
- ✅ Alternative approaches considered if needed
- ✅ Risk assessment completed

### AC9: Documentation Deliverables
- ✅ Research report created: `docs/opencode-research.md`
- ✅ Setup guide created: `docs/opencode-setup-guide.md`
- ✅ CLI reference created: `docs/opencode-cli-reference.md`
- ✅ Tool compatibility matrix: `docs/opencode-tool-mapping.md`

---

## Technical Details

### Deliverable Files
```
docs/
├── opencode-research.md           # Comprehensive research report
├── opencode-setup-guide.md        # Installation and setup
├── opencode-cli-reference.md      # CLI flags and usage
└── opencode-tool-mapping.md       # Tool compatibility matrix
```

### Research Areas

#### 1. Installation & Setup

**Questions to Answer:**
- What are the prerequisites? (Node.js, Bun, etc.)
- How do you install OpenCode?
- How do you configure it?
- What environment variables are needed?

**Commands to Test:**
```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash

# Install OpenCode
npm install -g @sst/opencode
# OR
bun install -g @sst/opencode

# Verify installation
opencode --version

# Test basic execution
echo "Write a hello world Python script" | opencode
```

#### 2. CLI Interface

**Questions to Answer:**
- What CLI flags are available?
- How do you specify the AI provider?
- How do you specify the model?
- How do you pass tasks/prompts?
- How do you set working directory?
- How do you specify tools/permissions?

**Example Commands to Test:**
```bash
# Basic execution
opencode --provider anthropic --model claude-sonnet-4.5 "Write hello world"

# With working directory
opencode --cwd /path/to/project --provider openai --model gpt-4 "Add tests"

# Interactive mode
opencode

# Non-interactive mode
echo "Create a file" | opencode --provider anthropic
```

#### 3. Provider Support

**Questions to Answer:**
- How do you switch providers?
- What models are supported per provider?
- How are API keys specified?
- Are there provider-specific flags?

**Commands to Test:**
```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
opencode --provider anthropic --model claude-sonnet-4.5 "Test task"

# OpenAI
export OPENAI_API_KEY=sk-...
opencode --provider openai --model gpt-4 "Test task"

# Google
export GOOGLE_API_KEY=...
opencode --provider google --model gemini-pro "Test task"
```

#### 4. Tool/Capability Mapping

**GAO-Dev Tools to Map:**
- Read
- Write
- Edit
- MultiEdit
- Bash
- Grep
- Glob
- Task
- WebFetch
- WebSearch
- TodoWrite
- AskUserQuestion

**Questions to Answer:**
- Does OpenCode have equivalent tools?
- Are they named differently?
- Do they work the same way?
- Are there tools OpenCode has that GAO-Dev doesn't?

#### 5. Output Format

**Questions to Answer:**
- Is output streamed?
- What format is the output?
- How are errors reported?
- How do you parse results?
- Are there progress indicators?

**Test Scenario:**
```bash
# Capture output for analysis
opencode "Create a Python hello world script" > output.txt 2>&1

# Analyze output format
cat output.txt
```

#### 6. Performance

**Benchmark Tests:**
```bash
# Simple task timing
time opencode "Write hello world Python script"
time claude "Write hello world Python script"

# Compare execution time
# Compare memory usage (use ps, top, or Windows Task Manager)
```

### Research Report Template

**File**: `docs/opencode-research.md`

```markdown
# OpenCode Research Report

**Date**: 2025-11-04
**Researcher**: [Name]
**Version Tested**: OpenCode vX.X.X

---

## Executive Summary

[Brief overview of findings]

**Go/No-Go Recommendation**: [GO | NO-GO]

**Reasoning**: [1-2 paragraphs]

---

## Installation & Setup

### Prerequisites
- Bun vX.X.X or higher
- Node.js vX.X.X or higher (if using npm)
- [Other requirements]

### Installation Steps
```bash
[Commands]
```

### Configuration
[Environment variables, config files, etc.]

---

## CLI Interface

### Command Structure
```bash
opencode [options] [prompt]
```

### Available Flags
| Flag | Description | Example |
|------|-------------|---------|
| `--provider` | AI provider | `--provider anthropic` |
| `--model` | Model ID | `--model gpt-4` |
| `--cwd` | Working directory | `--cwd /path` |
| ... | ... | ... |

### Comparison with Claude Code
| Feature | Claude Code | OpenCode |
|---------|-------------|----------|
| Provider | Anthropic only | Multi-provider |
| Flags | `--print`, `--model` | `--provider`, `--model` |
| ... | ... | ... |

---

## Provider Support

### Anthropic
- Models: claude-sonnet-4.5, claude-opus-3, ...
- API Key: ANTHROPIC_API_KEY
- Notes: [Any quirks]

### OpenAI
- Models: gpt-4, gpt-4-turbo, ...
- API Key: OPENAI_API_KEY
- Notes: [Any quirks]

### Google
- Models: gemini-pro, ...
- API Key: GOOGLE_API_KEY
- Notes: [Any quirks]

---

## Tool Mapping

| GAO-Dev Tool | OpenCode Equivalent | Compatible? | Notes |
|--------------|---------------------|-------------|-------|
| Read | [equivalent] | ✅ | [notes] |
| Write | [equivalent] | ✅ | [notes] |
| Bash | [equivalent] | ✅ | [notes] |
| ... | ... | ... | ... |

---

## Output Format

### Streaming Output
[Description of how OpenCode streams output]

### Error Handling
[How errors are reported]

### Parsing Strategy
[How to parse OpenCode output for GAO-Dev]

---

## Performance

### Benchmarks
| Task | Claude Code | OpenCode | Difference |
|------|-------------|----------|------------|
| Hello World | 5.2s | 6.1s | +17% |
| Simple Task | 12.3s | 13.8s | +12% |

### Memory Usage
- Claude Code: ~150MB
- OpenCode: ~180MB

---

## Known Issues

### Critical Issues
1. [Issue description]
2. [Issue description]

### Minor Issues
1. [Issue description]
2. [Issue description]

### Workarounds
- [Issue]: [Workaround]

---

## Implementation Recommendations

### Recommended Approach
[How to implement OpenCodeProvider]

### Alternative Approaches
[If primary approach has issues]

### Estimated Complexity
- Implementation: [X days]
- Testing: [X days]
- Documentation: [X days]

---

## Decision: GO / NO-GO

**Decision**: [GO | NO-GO]

**Justification**:
- [Reason 1]
- [Reason 2]
- [Reason 3]

**Next Steps**:
1. [Step 1]
2. [Step 2]
```

---

## Testing Strategy

### Installation Testing
- Install on Windows, Mac, Linux
- Test with different Node/Bun versions
- Document any installation issues

### Functional Testing
- Execute basic tasks
- Test all provider types
- Test error scenarios
- Test timeout scenarios

### Performance Testing
- Benchmark against Claude Code
- Measure memory usage
- Measure startup time

### Compatibility Testing
- Test tool equivalence
- Test output parsing
- Test error handling

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] OpenCode installed and tested locally
- [ ] CLI interface fully documented
- [ ] All providers tested
- [ ] Tool mapping complete
- [ ] Output format analyzed
- [ ] Performance benchmarks completed
- [ ] Known issues documented
- [ ] Go/No-Go decision made
- [ ] Research report reviewed
- [ ] Setup guide reviewed
- [ ] CLI reference complete
- [ ] Tool mapping reviewed

---

## Dependencies

**Upstream**: None (can start immediately)

**Downstream**:
- Story 11.7 (OpenCodeProvider) - BLOCKS if NO-GO
- Story 11.7 - Uses findings for implementation

---

## Notes

- **CRITICAL**: This is a research story - objective is information gathering
- Go/No-Go decision is binding for Story 11.7
- If NO-GO, we skip OpenCodeProvider and focus on DirectAPIProvider
- Installation may require admin privileges
- Test with multiple AI providers if API keys available
- Windows testing important (Bun support on Windows)
- Document version numbers for reproducibility

---

## Related Documents

- OpenCode GitHub: https://github.com/sst/opencode
- OpenCode Docs: https://opencode.dev (if available)
- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
