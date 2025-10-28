# Simple Artifacts Benchmark Example

**Epic 7 Feature Demonstration**

This benchmark demonstrates GAO-Dev's artifact creation capabilities introduced in Epic 7.

## What This Benchmark Does

Creates a minimal "Hello World" Python application with:
- Product Requirements Document (PRD)
- System Architecture document
- Proper project structure
- Git commits after each phase

## Expected Output

### Artifacts Created

```
sandbox/projects/hello-world-001/
├── .git/                          # Git repository
├── .gitignore                     # Ignore patterns
├── docs/
│   ├── PRD.md                     # Product requirements
│   └── ARCHITECTURE.md            # System architecture
├── README.md                      # Project documentation
└── [Additional files from agents]
```

### Git History

```bash
$ git log --oneline
abc1234 feat(architecture): Create system architecture design
def5678 feat(prd): Create Product Requirements Document
ghi9012 chore: Initialize project structure
```

Each commit includes:
- Conventional commit format
- Benchmark run ID
- Phase name
- Agent name
- Artifact count

## How to Run

### Prerequisites

1. GAO-Dev installed
2. Anthropic API key set (not needed for dry-run)
3. Git configured

### Run the Benchmark

```bash
# From GAO-Dev root directory
cd "D:\GAO Agile Dev"

# Dry-run mode (no API calls)
gao-dev sandbox run --config sandbox/benchmarks/simple-with-artifacts.yaml --mode dry-run

# Agent mode (requires API key)
gao-dev sandbox run --config sandbox/benchmarks/simple-with-artifacts.yaml --mode agent
```

### Check the Output

```bash
# View created artifacts
ls -R sandbox/projects/hello-world-001/

# View git history
cd sandbox/projects/hello-world-001/
git log --oneline --stat

# View a specific file
cat docs/PRD.md
```

## Expected Metrics

- **Duration**: ~15-20 minutes (agent mode)
- **Phases**: 2 (PRD, Architecture)
- **Artifacts**: 2-3 files
- **Git Commits**: 2-3 commits
- **Cost**: ~$0.10-0.50 (depending on agent output)

## Success Criteria

✅ PRD document created at `docs/PRD.md`
✅ Architecture document created at `docs/ARCHITECTURE.md`
✅ Git repository initialized
✅ Atomic commits after each phase
✅ No errors or warnings

## Troubleshooting

### "No artifacts created"

- Check that agent mode is enabled (not dry-run)
- Verify agents are producing markdown output with file indicators
- Check logs for parser warnings

### "Git commit failed"

- Ensure git is installed and in PATH
- Check project directory permissions
- Verify `.git` directory exists

### "Parser not finding files"

- Agents need to use format: `**Save as**: docs/PRD.md`
- Or code blocks with file comments: ` ```markdown # docs/PRD.md `

## What Epic 7 Features Are Demonstrated

1. **Story 7.1**: GAODevOrchestrator integration (replaces AgentSpawner)
2. **Story 7.2**: Artifact parser extracts files from agent markdown
3. **Story 7.3**: Atomic git commits after each phase
4. **Story 7.4**: Metrics collection (duration, tokens, artifacts)
5. **Story 7.5**: Artifact verification (existence, syntax, validity)

## Next Steps

After this works, try:
- More complex benchmarks (full app development)
- Multiple epics and stories
- Different tech stacks
- Custom success criteria

## Notes

This benchmark is intentionally minimal to validate Epic 7 functionality.
Real benchmarks would include:
- Story creation phase
- Implementation phase
- Multiple stories
- Comprehensive testing
- Quality gates
