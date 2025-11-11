---
name: code-review
description: Perform comprehensive code reviews focusing on correctness, security, performance, maintainability, and best practices. Use after code changes to ensure quality standards before merging.
allowed-tools: Read, Grep, Glob, Bash
---

# Code Review Skill

This skill guides you through performing thorough, constructive code reviews that improve code quality while respecting the developer's effort.

## When to Use

Use this skill when you need to:
- Review code changes before merging
- Perform quality checks on implementations
- Identify potential bugs or security issues
- Ensure coding standards are followed
- Provide constructive feedback to developers

## Code Review Philosophy

### Goals of Code Review
1. **Catch Bugs**: Find defects before they reach production
2. **Ensure Quality**: Maintain code standards and best practices
3. **Share Knowledge**: Team learning and knowledge transfer
4. **Improve Design**: Identify better approaches
5. **Maintain Consistency**: Keep codebase cohesive

### Review Mindset
- **Be Kind**: Assume positive intent, respect the developer's effort
- **Be Specific**: Point to exact lines, suggest concrete improvements
- **Be Constructive**: Explain why, not just what's wrong
- **Be Pragmatic**: Balance perfection with shipping
- **Be Curious**: Ask questions to understand intent

## Review Checklist

### 1. Correctness
**Does the code do what it's supposed to do?**

- [ ] Implements all acceptance criteria
- [ ] Logic is sound and correct
- [ ] Edge cases are handled
- [ ] Error conditions are handled
- [ ] No obvious bugs
- [ ] Tests pass and are meaningful

**Red Flags**:
- Off-by-one errors
- Incorrect conditions (using `&&` instead of `||`)
- Missing null/undefined checks
- Incorrect algorithm logic

### 2. Security
**Is the code secure?**

- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (proper escaping)
- [ ] Authentication/authorization checks
- [ ] No secrets in code (API keys, passwords)
- [ ] Secure dependencies (no known vulnerabilities)
- [ ] CSRF protection where needed
- [ ] Proper error handling (no stack traces to users)

**Red Flags**:
- String concatenation in SQL queries
- Unescaped user input in HTML
- Hardcoded secrets or credentials
- Missing authorization checks
- Overly permissive access controls

### 3. Performance
**Will the code perform well?**

- [ ] No obvious performance issues
- [ ] Efficient algorithms and data structures
- [ ] Database queries are optimized
- [ ] No N+1 query problems
- [ ] Proper indexing used
- [ ] Caching used where appropriate
- [ ] Unnecessary work avoided

**Red Flags**:
- Loops inside loops with large datasets
- Database queries inside loops
- Loading entire datasets when pagination possible
- Inefficient algorithms (O(n²) when O(n) possible)
- Missing database indexes

### 4. Readability & Maintainability
**Can other developers understand and maintain this code?**

- [ ] Clear, descriptive variable/function names
- [ ] Logical code organization
- [ ] Appropriate comments for complex logic
- [ ] No overly long functions (< 50 lines ideal)
- [ ] No overly complex conditions (extract to named functions)
- [ ] Consistent with project style
- [ ] No "clever" code (simple is better)

**Red Flags**:
- Single-letter variable names (except i, j for loops)
- Unclear function names (doStuff, processData)
- Functions longer than a screen (50+ lines)
- Deeply nested conditions (> 3 levels)
- Magic numbers without constants

### 5. Design & Architecture
**Does the code follow good design principles?**

- [ ] Follows existing patterns in codebase
- [ ] Appropriate abstraction level
- [ ] Single Responsibility Principle
- [ ] DRY (Don't Repeat Yourself)
- [ ] Loose coupling
- [ ] Follows project architecture

**Red Flags**:
- Duplicated code (same logic in multiple places)
- God objects/functions (do too much)
- Tight coupling (hard to test/change)
- Mixing concerns (business logic in UI)
- Over-engineering (unnecessary abstraction)

### 6. Testing
**Is the code properly tested?**

- [ ] Tests exist for new/changed code
- [ ] Tests are meaningful (not just for coverage)
- [ ] Tests cover happy paths
- [ ] Tests cover edge cases
- [ ] Tests cover error conditions
- [ ] Tests are readable and maintainable
- [ ] All tests pass

**Red Flags**:
- No tests for complex logic
- Tests that don't actually test anything
- Tests that test implementation details
- Flaky tests (random failures)
- Tests that don't reflect acceptance criteria

### 7. Error Handling
**Are errors handled gracefully?**

- [ ] Expected errors are handled
- [ ] Error messages are helpful
- [ ] Errors are logged appropriately
- [ ] No swallowed exceptions
- [ ] Proper cleanup in error paths
- [ ] User-facing error messages are clear

**Red Flags**:
- Empty catch blocks
- Generic error messages ("An error occurred")
- Stack traces shown to users
- No error logging
- Resource leaks in error paths

### 8. Documentation
**Is the code properly documented?**

- [ ] Public APIs are documented
- [ ] Complex logic has explanatory comments
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] No outdated comments

**Red Flags**:
- Public functions without documentation
- Commented-out code
- Misleading or outdated comments
- No explanation of non-obvious logic

## Review Process

### 1. Pre-Review
Before diving into code:
- Read the story/issue being addressed
- Understand acceptance criteria
- Review architectural context
- Check CI status (all tests passing?)

### 2. High-Level Review
Start with the big picture:
- Does the approach make sense?
- Is it consistent with architecture?
- Are there better alternatives?
- Is scope appropriate (not too much)?

### 3. Detailed Review
Review the code line by line:
- Follow the checklist above
- Flag issues by severity
- Suggest specific improvements
- Ask questions about intent

### 4. Test Review
Review tests carefully:
- Do tests match acceptance criteria?
- Are tests meaningful?
- Are edge cases covered?
- Can tests be improved?

### 5. Provide Feedback
Give clear, actionable feedback:
- Point to specific lines
- Explain why it's an issue
- Suggest concrete fixes
- Distinguish must-fix from nice-to-have

## Feedback Categories

Use clear categories for feedback:

### Critical Issues (Must Fix)
- Security vulnerabilities
- Data corruption risks
- Breaking changes
- Logic bugs
- Performance problems

**Label**: `🔴 Critical` or `Must Fix`

### Important Issues (Should Fix)
- Code quality issues
- Maintainability concerns
- Missing tests
- Design problems
- Unclear code

**Label**: `🟡 Important` or `Should Fix`

### Suggestions (Nice to Have)
- Style preferences
- Minor optimizations
- Alternative approaches
- Learning opportunities

**Label**: `🟢 Suggestion` or `Nice to Have`

### Questions
- Clarify intent
- Understand decisions
- Learn from the author

**Label**: `❓ Question`

## Example Feedback

### Good Feedback Examples

**Critical - Security Issue**:
```
🔴 Critical: SQL Injection Vulnerability

Line 42: User input is directly concatenated into SQL query.

Current code:
query = f"SELECT * FROM users WHERE id = {user_id}"

Recommended fix:
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

Why: Direct string concatenation allows SQL injection attacks.
```

**Important - Missing Error Handling**:
```
🟡 Important: Missing Error Handling

Lines 56-60: API call has no error handling. If the external service is down, this will crash.

Suggestion:
try:
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()
except requests.RequestException as e:
    logger.error(f"API call failed: {e}")
    return None  # or raise custom exception
```

**Suggestion - Code Clarity**:
```
🟢 Suggestion: Variable Naming

Line 23: Variable name 'd' is unclear.

Current: d = calculate_discount(price, rate)
Better: discount_amount = calculate_discount(price, rate)

Why: Clear names make code self-documenting.
```

**Question**:
```
❓ Question

Line 78: I see you're using a cache with 1-hour TTL. What's the rationale for this duration? Is it based on how often the data changes?

Just curious to understand the trade-offs here.
```

### Poor Feedback Examples

**Too Vague**:
```
❌ This doesn't look right.
✅ Line 42: SQL injection vulnerability - use parameterized queries.
```

**Not Constructive**:
```
❌ This is terrible code.
✅ Line 56: This function is doing too much. Consider splitting into smaller functions for better maintainability.
```

**No Context**:
```
❌ Fix this.
✅ Line 23: Variable name 'd' is unclear. Consider 'discount_amount' for better readability.
```

## Common Review Scenarios

### Reviewing a Bug Fix
Focus on:
- Does it actually fix the bug?
- Are there tests to prevent regression?
- Are there similar bugs elsewhere?
- Is the fix minimal (least change needed)?

### Reviewing a New Feature
Focus on:
- Does it meet acceptance criteria?
- Is it consistent with architecture?
- Are all edge cases handled?
- Is it properly tested?

### Reviewing a Refactoring
Focus on:
- Does behavior remain unchanged?
- Is it actually better (not just different)?
- Are tests still passing?
- Is change scope reasonable?

## When to Approve

Approve when:
- All critical issues are resolved
- Important issues are addressed or acknowledged
- Tests pass
- Code meets quality standards
- You'd be comfortable maintaining this code

## When to Request Changes

Request changes when:
- Critical security or correctness issues exist
- Important quality issues aren't addressed
- Tests are missing or inadequate
- Code violates project standards
- Acceptance criteria aren't met

## After Review

### If Changes Requested
- Be available for questions
- Review updated code promptly
- Verify changes address concerns
- Approve when satisfied

### If Approved
- Thank the reviewer
- Merge the code
- Monitor for issues post-merge

## Success Indicators

You're doing code review well when:
- Bugs are caught before production
- Code quality is consistently high
- Developers learn and improve
- Reviews are respectful and constructive
- Feedback is specific and actionable
- Review turnaround is fast (< 24 hours)
- Team knowledge is shared

## Remember

- **Be kind**: Respect the developer's effort
- **Be specific**: Point to exact issues with fixes
- **Be timely**: Review promptly to avoid blocking
- **Be consistent**: Apply standards uniformly
- **Be learning-focused**: Reviews teach everyone
- **Be pragmatic**: Perfect is the enemy of good enough
