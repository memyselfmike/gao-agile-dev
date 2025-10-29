# How to Run GAO-Dev - Greenfield Todo App Benchmark

This guide shows you how to run GAO-Dev to autonomously build a production-ready todo application from a simple prompt.

---

## What Will Happen

When you run this benchmark, GAO-Dev will:

1. **Analyze** your prompt ("Build a todo application...")
2. **Select** appropriate workflows via Brian agent
3. **Create** comprehensive documentation (PRD, architecture)
4. **Design** the system and UX
5. **Break down** into implementable stories
6. **Implement** all code (backend + frontend)
7. **Write** comprehensive tests
8. **Make** atomic git commits throughout
9. **Validate** quality and success criteria

**Result**: Complete, production-ready todo application! 🎉

**Time**: 2-3 hours (depending on API speed)

---

## Prerequisites

### 1. Anthropic API Key

You need a Claude API key from Anthropic.

**Get one**:
1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create a new key
5. Copy it (you won't see it again!)

### 2. Set the API Key

**On Linux/Mac**:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**On Windows (PowerShell)**:
```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
```

**On Windows (Command Prompt)**:
```cmd
set ANTHROPIC_API_KEY=your-key-here
```

**Verify it's set**:
```bash
# Linux/Mac
echo $ANTHROPIC_API_KEY

# Windows PowerShell
echo $env:ANTHROPIC_API_KEY

# Windows CMD
echo %ANTHROPIC_API_KEY%
```

---

## Run the Benchmark

### Method 1: Using gao-dev Command (If Installed)

```bash
gao-dev sandbox run sandbox/benchmarks/workflow-driven-todo.yaml
```

### Method 2: Using Python Module

```bash
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml
```

### Method 3: From Project Root

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml
```

---

## What You'll See

The benchmark will output progress in real-time:

```
[Benchmark] Starting: workflow-driven-todo
[Benchmark] Loading config...
[OK] Config validated

[Brian] Analyzing prompt...
[Brian] Detected: GREENFIELD full-stack application
[Brian] Scale Level: 2 (Small feature, 3-8 stories)
[Brian] Selected workflows: prd, architecture, story-creation, implementation

[John - PM] Creating PRD...
[File] Created: docs/PRD.md
[Git] Commit: docs: add comprehensive PRD

[Winston - Architect] Creating architecture...
[File] Created: docs/ARCHITECTURE.md
[Git] Commit: docs: add system architecture

[Sally - UX] Creating designs...
[File] Created: docs/UX-DESIGN.md
[Git] Commit: docs: add UX designs and wireframes

[Bob - Scrum Master] Creating stories...
[Created] Story 1: Setup project structure
[Created] Story 2: User authentication system
[Created] Story 3: Task CRUD operations
[Created] Story 4: Task categories and tags
[Created] Story 5: Due dates and reminders
[Created] Story 6: Responsive UI
[Created] Story 7: Integration and deployment

[Amelia - Developer] Implementing Story 1...
[Files] backend/main.py, backend/models.py, backend/config.py
[Tests] tests/test_setup.py
[Git] Commit: feat: implement Story 1 - Setup project structure

[Murat - QA] Validating Story 1...
[Tests] Running pytest...
[OK] All tests passing
[OK] Coverage: 92%

... (continues for all stories)

[Benchmark] Validating success criteria...
[OK] All required artifacts exist
[OK] Tests passing (coverage: 85%)
[OK] Quality checks passed (ruff, mypy, black)
[OK] Git history clean (8 commits)

[Benchmark] SUCCESS!
[Duration] 2h 15m 32s
[Cost] $X.XX (X tokens)

Results saved to: sandbox/projects/workflow-driven-todo-20251029-103045/
```

---

## View the Results

### Check the Created Application

```bash
cd sandbox/projects/workflow-driven-todo-<timestamp>/

# View documentation
cat docs/PRD.md
cat docs/ARCHITECTURE.md

# View code
ls backend/
ls frontend/
ls tests/

# View git history
git log --oneline
```

### View the Benchmark Report

```bash
gao-dev sandbox report run workflow-driven-todo-<timestamp>
```

This opens an HTML report with:
- Timeline of execution
- Metrics (duration, tokens, cost)
- Success criteria results
- Code quality scores
- Charts and visualizations

---

## Success Criteria

The benchmark passes if:

✅ **All Artifacts Created**:
- docs/PRD.md
- docs/ARCHITECTURE.md
- docs/API.md
- backend/**/*.py
- frontend/**/*.tsx
- tests/**/*.py
- docker-compose.yml
- README.md

✅ **Tests Pass**: All tests must pass

✅ **Code Coverage**: ≥80%

✅ **Quality Checks**:
- Linting (ruff) passes
- Type checking (mypy) passes
- Formatting (black) passes

✅ **Git Commits**: ≥5 atomic commits in conventional format

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
# Set the key first
export ANTHROPIC_API_KEY="your-key"

# Then run again
```

### "gao-dev command not found"
```bash
# Use Python module instead
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml
```

### "Module gao_dev not found"
```bash
# Install in development mode
cd "D:\GAO Agile Dev"
pip install -e .

# Then run
```

### Benchmark Takes Too Long
This is normal! Building a production app takes time:
- PRD creation: ~10-15 minutes
- Architecture: ~10-15 minutes
- Each story: ~15-20 minutes
- Total: 2-3 hours

You can monitor progress in real-time.

### Benchmark Fails Partway
Check the error message:
- API rate limit? Wait and retry
- Token limit? Adjust prompt complexity
- Quality check failed? Review the code

The benchmark will save partial results even if it fails.

---

## What You Get

After successful completion:

### Documentation
- **PRD.md**: Comprehensive product requirements
- **ARCHITECTURE.md**: System architecture and design decisions
- **API.md**: API documentation (OpenAPI/Swagger)
- **UX-DESIGN.md**: User flows and wireframes
- **README.md**: Setup and deployment instructions

### Code
- **backend/**: Python/FastAPI application
  - Models, routes, auth, database
  - Business logic
  - API endpoints
- **frontend/**: React/TypeScript application
  - Components, pages, hooks
  - State management
  - Responsive UI
- **tests/**: Comprehensive test suite
  - Unit tests
  - Integration tests
  - E2E tests (if applicable)
  - >80% coverage

### Infrastructure
- **docker-compose.yml**: Local development setup
- **requirements.txt** / **package.json**: Dependencies
- **Database migrations**: Schema and seed data
- **.gitignore**, **.env.example**, etc.

### Git History
Clean, atomic commits following conventional format:
```
docs: add comprehensive PRD
docs: add system architecture
docs: add UX designs
feat: implement Story 1 - Setup project structure
feat: implement Story 2 - User authentication
feat: implement Story 3 - Task CRUD operations
...
```

---

## Next Steps After Success

### 1. Explore the Created Application

```bash
cd sandbox/projects/workflow-driven-todo-<timestamp>/

# Read the docs
cat README.md

# Set up the environment
docker-compose up -d

# Run tests
pytest

# Start the backend
cd backend && python main.py

# Start the frontend
cd frontend && npm start
```

### 2. Analyze the Metrics

```bash
gao-dev sandbox report run workflow-driven-todo-<timestamp>
```

Look at:
- How long did each phase take?
- How many tokens were used?
- What was the cost?
- Which quality metrics passed?

### 3. Try Different Prompts

Edit `sandbox/benchmarks/workflow-driven-todo.yaml` and change the prompt:

```yaml
initial_prompt: |
  Build a blog platform with:
  - User authentication
  - Post creation/editing
  - Comments system
  - Tag-based organization
  - RSS feed
  - Python/Django backend
  - Vue.js frontend
```

Then run again!

### 4. Test at Different Scale Levels

Change the `scale_level`:
- `0`: Chore (1 story) - "Fix typo in README"
- `1`: Bug fix (1-2 stories) - "Fix login error"
- `2`: Small feature (3-8 stories) - Todo app ← **Current**
- `3`: Medium feature (12-20 stories) - Full blog platform
- `4`: Greenfield app (40+ stories) - Complete SaaS platform

---

## Cost Estimate

Based on typical Claude Sonnet 3.5 pricing:

**Todo App Benchmark** (Scale Level 2):
- Tokens: ~500K-1M
- Cost: $5-15 USD
- Time: 2-3 hours

This validates that GAO-Dev can autonomously build a production app!

---

## Questions?

**Q: Do I need to watch it run?**
A: No! You can start it and come back. Progress is logged.

**Q: Can I stop and resume?**
A: Not yet (Story 4.8 - Standalone Mode is deferred). Run to completion.

**Q: What if it fails?**
A: Check logs, fix the issue, run again. Partial results are saved.

**Q: Can I customize the prompt?**
A: Yes! Edit `workflow-driven-todo.yaml` and change `initial_prompt`.

**Q: Will it really work?**
A: Architecture is validated (41 tests passing). Needs API key to execute agents.

**Q: How do I know it's production-ready?**
A: Check the generated code, tests, documentation. It should be deployable!

---

## The Bottom Line

```bash
# 1. Set API key
export ANTHROPIC_API_KEY="your-key"

# 2. Run GAO-Dev
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml

# 3. Wait 2-3 hours

# 4. Get production-ready todo app!
cd sandbox/projects/workflow-driven-todo-<timestamp>/
```

**That's it!** GAO-Dev does the rest autonomously.

---

**Last Updated**: 2025-10-29
**Status**: Ready to run
**Requirement**: ANTHROPIC_API_KEY
**Expected Duration**: 2-3 hours
**Expected Cost**: $5-15 USD
