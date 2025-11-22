# Documentation Review Command

Review documentation for quality, token efficiency, actionability, and agent-friendliness.

## Task

You are the **document-keeper** agent reviewing documentation.

Analyze the specified documentation for:

1. **Token Efficiency**
   - Does it have TL;DR if >500 lines?
   - Are quick-starts <2,000 tokens?
   - Are agent guides <3,000 tokens?
   - Are tables used instead of prose?
   - Is there redundant information?

2. **Actionability**
   - Are there copy-paste code examples?
   - Do examples show complete workflows?
   - Is error handling demonstrated?
   - Are testing patterns provided?
   - Is there a "Common Issues" section?

3. **Agent-Friendliness**
   - Inverted pyramid structure (key facts first)?
   - Clear navigation (headers, TOC)?
   - Role-based views for different agents?
   - Purpose stated for cross-references?
   - Decision trees for discovery?

4. **Accuracy**
   - Are code examples tested?
   - Is it synchronized with codebase?
   - Are links validated (no broken links)?
   - Is terminology consistent?
   - Is version noted (if applicable)?

5. **Discoverability**
   - Linked from parent documentation?
   - Cross-referenced in related docs?
   - Added to documentation index?
   - Keywords in title and headers?

## Output

Provide a comprehensive critique with:

### Issues Found
- **Critical** (blocks agent efficiency)
- **High** (significantly impacts usability)
- **Medium** (improvements needed)
- **Low** (nice to have)

### Specific Fixes
For each issue, provide:
- What's wrong
- How to fix it
- Estimated effort
- Example of fix

### Action Plan
Prioritized list of fixes in phases:
- Phase 1: Critical (immediate)
- Phase 2: High priority (this sprint)
- Phase 3: Medium (next sprint)

### Success Metrics
How to measure improvement:
- Token reduction
- Time to find answer
- Agent success rate

## Example Usage

```
/doc-review docs/ARCHITECTURE_OVERVIEW.md
```

This will review the architecture overview and provide a detailed critique with actionable fixes.
