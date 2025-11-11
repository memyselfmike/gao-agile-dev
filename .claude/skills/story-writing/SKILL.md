---
name: story-writing
description: Create well-structured user stories from requirements with clear acceptance criteria, technical context, and test scenarios. Use when creating user stories, refining backlog items, or breaking down epics.
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Story Writing Skill

This skill helps you create well-structured, developer-ready user stories that follow agile best practices.

## When to Use

Use this skill when you need to:
- Create new user stories from requirements
- Refine existing stories
- Break down epics into stories
- Add acceptance criteria to stories
- Define story test scenarios

## Story Template

Every story should follow this structure:

```markdown
# Story [Epic.Story]: [Title]

**Status**: Draft | Ready | In Progress | Done
**Priority**: Must Have | Should Have | Could Have
**Estimate**: [Story points or time]

## User Story

As a [user type]
I want [goal/desire]
So that [benefit/value]

## Context & Background

[Brief explanation of why this story exists, relevant background information, links to related PRD/Architecture sections]

## Acceptance Criteria

- [ ] AC1: [Specific, testable criterion - GIVEN/WHEN/THEN format preferred]
- [ ] AC2: [Each AC should be independently verifiable]
- [ ] AC3: [Focus on WHAT needs to be achieved, not HOW]

## Technical Context

### Dependencies
- [List any dependent stories, services, or systems]

### Architecture References
- [Link to relevant architecture decisions or sections]

### APIs/Interfaces
- [Relevant endpoints, interfaces, or data contracts]

### Technical Notes
- [Any technical constraints, considerations, or implementation guidance]

## Test Scenarios

### Happy Path
1. [Primary success scenario]

### Edge Cases
1. [Boundary conditions or unusual scenarios]

### Error Cases
1. [How system should handle errors]

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Deployed to staging/production

## Notes

[Any additional notes, open questions, or discussion points]
```

## Quality Checklist

Before completing a story, verify:

- [ ] **User Value is Clear**: The "so that" clause explains real value
- [ ] **Acceptance Criteria are Testable**: Each AC can be verified objectively
- [ ] **Scope is Reasonable**: Story can be completed in one sprint
- [ ] **Dependencies are Identified**: Any blockers are documented
- [ ] **Technical Context is Sufficient**: Developers have what they need
- [ ] **Test Scenarios are Comprehensive**: Happy path, edge cases, errors covered
- [ ] **Priority is Clear**: MoSCoW priority is assigned
- [ ] **Definition of Done is Complete**: All DoD items are listed

## INVEST Criteria

Good stories follow INVEST:

- **Independent**: Story can be developed separately
- **Negotiable**: Details can be discussed and refined
- **Valuable**: Delivers value to users or business
- **Estimable**: Team can estimate effort
- **Small**: Can be completed in a sprint
- **Testable**: Can verify when done

## Common Mistakes to Avoid

1. **Technical tasks masquerading as stories**: "Refactor database" is not a user story
2. **Too large**: Story should fit in a sprint
3. **Vague ACs**: "System should be fast" is not testable
4. **Missing "so that"**: Must explain the value/benefit
5. **Implementation details**: Focus on what, not how
6. **No test scenarios**: Tests validate the ACs

## Examples

### Good Story Example

```markdown
# Story 1.3: User Can Reset Password

**Status**: Ready
**Priority**: Must Have
**Estimate**: 3 points

## User Story

As a registered user
I want to reset my password via email
So that I can regain access to my account if I forget my password

## Context & Background

Users frequently forget passwords and get locked out. This is a top support request (40% of tickets). See PRD section 3.2 for security requirements.

## Acceptance Criteria

- [ ] AC1: GIVEN user clicks "Forgot Password", WHEN they enter their email, THEN they receive a password reset link within 2 minutes
- [ ] AC2: GIVEN user clicks reset link, WHEN link is less than 24 hours old, THEN they see password reset form
- [ ] AC3: GIVEN user submits new password, WHEN password meets requirements (8+ chars, 1 uppercase, 1 number), THEN password is updated and user can log in
- [ ] AC4: GIVEN user tries to use reset link twice, WHEN link already used, THEN they see error message

## Technical Context

### Dependencies
- Email service (SendGrid configured)
- User authentication service

### APIs/Interfaces
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- Token generation/validation service

### Technical Notes
- Token should be cryptographically secure (32+ bytes)
- Rate limiting: Max 3 requests per email per hour
- Tokens stored in Redis with 24h TTL

## Test Scenarios

### Happy Path
1. User receives reset email within 2 minutes
2. User clicks link and sees form
3. User enters valid password
4. User can log in with new password

### Edge Cases
1. User requests reset for non-existent email (send generic message, don't reveal)
2. User clicks expired link (show message, offer to resend)
3. User submits password not meeting requirements (show validation errors)

### Error Cases
1. Email service down (queue request, retry)
2. Invalid/tampered token (reject with security log)
3. Rate limit exceeded (show wait time)

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests for token generation/validation
- [ ] Integration tests for email sending
- [ ] E2E test for complete flow
- [ ] Security review completed
- [ ] Documentation updated (user help docs)
- [ ] Deployed to production

## Notes

- Consider adding 2FA in Story 1.4
- Monitor reset request patterns for abuse
```

## Step-by-Step Process

1. **Start with User Value**: Identify who needs what and why
2. **Extract from Requirements**: Pull relevant requirements from PRD/Architecture
3. **Write User Story**: Use "As a... I want... So that..." format
4. **Define Acceptance Criteria**: Make them specific, testable, and complete
5. **Add Technical Context**: Include architecture references, dependencies, APIs
6. **Define Test Scenarios**: Cover happy path, edge cases, and errors
7. **Specify Definition of Done**: List all completion requirements
8. **Review Against INVEST**: Ensure story meets quality criteria
9. **Get Feedback**: Share with team for refinement

## Success Indicators

Your story is ready when:
- A developer can implement it without asking clarification questions
- A tester can create test cases directly from the ACs
- The story can be completed in one sprint
- User value is clear and compelling
- All technical context is provided
