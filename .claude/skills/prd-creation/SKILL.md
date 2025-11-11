---
name: prd-creation
description: Create comprehensive Product Requirements Documents (PRDs) that clearly define product vision, requirements, success criteria, and user needs. Use when planning new features, products, or major initiatives.
allowed-tools: Read, Write, Edit, Grep, Glob, WebFetch, WebSearch
---

# PRD Creation Skill

This skill guides you through creating comprehensive, well-structured Product Requirements Documents that align stakeholders and guide development.

## When to Use

Use this skill when you need to:
- Define a new product or major feature
- Document product requirements comprehensively
- Align stakeholders on product vision and scope
- Create a blueprint for development teams
- Plan product launches or significant updates

## PRD Core Sections

Every PRD should include these sections (adapt as needed):

### 1. Executive Summary
**Purpose**: Quick overview for busy stakeholders
**Contents**:
- What we're building (1 paragraph)
- Why we're building it (problem and value)
- Expected impact (key metrics)
- Timeline overview

**Quality check**: Can someone read just this and understand the project?

### 2. Problem Statement
**Purpose**: Clearly articulate the problem being solved
**Contents**:
- The Problem: What specific problem exists?
- Current Situation: How do users handle this today?
- The Solution: High-level description of our approach
- Why Now: Why is this the right time?

**Quality check**: Is the problem clear and compelling?

### 3. Goals & Success Criteria
**Purpose**: Define what success looks like
**Contents**:
- Primary Goal: Main objective
- Secondary Goals: Supporting objectives
- Stretch Goals: Aspirational targets
- Success Criteria: Measurable indicators of success
- KPIs: Specific metrics with targets

**Quality check**: Are success criteria measurable and time-bound?

### 4. User Personas & Use Cases
**Purpose**: Define who we're building for
**Contents**:
- Primary Persona: Detailed profile with goals/pain points
- Secondary Personas: Other user types
- Use Cases: Step-by-step scenarios of how users will use the product

**Quality check**: Are personas specific and realistic (not generic)?

### 5. Functional Requirements
**Purpose**: Specify what the product must do
**Contents**:
- Organized by feature category
- Each requirement with description, value, priority (MoSCoW), and acceptance criteria
- Clear, testable requirements

**Quality check**: Can developers estimate and implement these requirements?

### 6. Non-Functional Requirements
**Purpose**: Define quality attributes and constraints
**Contents**:
- Performance: Speed, throughput, scalability targets
- Security: Authentication, authorization, data protection
- Usability: UX standards, accessibility requirements
- Reliability: Uptime, disaster recovery, data integrity

**Quality check**: Are requirements specific with measurable targets?

### 7. User Experience & Design
**Purpose**: Outline UX approach
**Contents**:
- Key user flows (entry → actions → outcomes)
- UI/UX considerations and principles
- Interaction patterns
- Accessibility requirements

**Quality check**: Are user flows clear and complete?

### 8. Technical Considerations
**Purpose**: Highlight technical requirements and constraints
**Contents**:
- Integration points (external systems)
- Data requirements (sources, models, migration)
- Technical constraints (platform, browser support)
- Performance requirements

**Quality check**: Have you consulted with architects/tech leads?

### 9. Competitive Analysis
**Purpose**: Position product in market context
**Contents**:
- Direct competitors (comparison table)
- Indirect competitors
- Market positioning
- Differentiation strategy

**Quality check**: Is competitive advantage clear?

### 10. Scope & Prioritization
**Purpose**: Define what's in and out of scope
**Contents**:
- In Scope: What we're building
- Out of Scope: What we explicitly won't build (and why)
- MVP vs. Future Phases
- MoSCoW prioritization of features

**Quality check**: Is MVP realistic and valuable?

### 11. Dependencies & Risks
**Purpose**: Identify blockers and risks
**Contents**:
- Internal dependencies (teams, systems)
- External dependencies (vendors, partners)
- Risks with probability, impact, and mitigation

**Quality check**: Are high-impact risks mitigated?

### 12. Timeline & Milestones
**Purpose**: Provide project timeline
**Contents**:
- High-level timeline with milestones
- Release strategy (alpha/beta/GA)
- Key dates and dependencies

**Quality check**: Is timeline realistic given dependencies?

### 13. Metrics & Analytics
**Purpose**: Define how we'll measure success
**Contents**:
- Analytics requirements (events to track)
- Conversion funnels
- User behavior metrics
- Success metrics post-launch

**Quality check**: Can we actually measure these metrics?

## PRD Quality Checklist

Before considering a PRD complete:

**Clarity & Completeness**
- [ ] Problem is clearly articulated
- [ ] User personas are specific and realistic
- [ ] Success criteria are measurable
- [ ] Requirements are clear and testable
- [ ] Priorities are explicit (MoSCoW)
- [ ] Scope is well-defined (in/out)
- [ ] Open questions are captured

**Stakeholder Alignment**
- [ ] Business stakeholders reviewed and approved
- [ ] Engineering reviewed for feasibility
- [ ] Design reviewed for UX considerations
- [ ] QA reviewed for testability
- [ ] All major concerns are addressed

**Technical Readiness**
- [ ] Technical feasibility validated
- [ ] Integration points identified
- [ ] Performance requirements specified
- [ ] Security requirements defined
- [ ] Dependencies documented

**Strategic Fit**
- [ ] Aligns with company/product strategy
- [ ] Competitive positioning is clear
- [ ] Business case is compelling
- [ ] ROI is justified

## Writing Best Practices

### Use Clear, Precise Language
- Avoid ambiguity ("fast" → "page load time < 2 seconds")
- Use active voice
- Define acronyms on first use
- Be specific, not vague

### Ground in Data
- Support statements with evidence
- Include user research findings
- Reference market data
- Cite competitive analysis

### Make It Scannable
- Use headings and subheadings
- Include tables for comparisons
- Use bullet points for lists
- Add executive summary for quick reading

### Document Decisions
- Explain why decisions were made
- Capture trade-offs considered
- Note alternatives that were rejected
- Include rationale for priorities

### Keep It Living
- Update as requirements evolve
- Track changes in version history
- Communicate updates to stakeholders
- Archive old versions

## Common Pitfalls to Avoid

1. **Solution Jumping**: Defining solution before understanding problem
2. **Feature Laundry List**: Including every possible feature without prioritization
3. **Vague Requirements**: "User-friendly interface" is not a requirement
4. **Missing User Value**: Technical features without clear user benefit
5. **Ignoring Constraints**: Not accounting for technical, time, or resource limits
6. **No Success Metrics**: Can't measure if product is successful
7. **Skipping Research**: Making assumptions instead of validating with data
8. **Over-Specifying**: Too much implementation detail (that's for tech specs)

## Research & Discovery Process

Before writing the PRD:

1. **User Research**
   - Conduct user interviews (5-10 users)
   - Review support tickets and feedback
   - Analyze user behavior data
   - Create user personas

2. **Market Research**
   - Analyze competitive products
   - Review industry trends
   - Assess market size and opportunity
   - Identify differentiation opportunities

3. **Technical Discovery**
   - Consult with architects on feasibility
   - Identify technical constraints
   - Assess integration requirements
   - Estimate complexity

4. **Stakeholder Input**
   - Interview business stakeholders
   - Align on strategic priorities
   - Validate business case
   - Get buy-in on approach

## Collaboration & Review

### Getting Feedback

**Early Draft Review** (Day 1-2):
- Share problem statement and goals
- Validate user personas
- Confirm strategic fit
- Gather initial reactions

**Detailed Review** (Week 1):
- Engineering: Feasibility and technical requirements
- Design: UX considerations and user flows
- QA: Testability of requirements
- Business: Strategic alignment and priorities

**Final Review** (Week 2):
- All stakeholders review complete draft
- Address open questions
- Finalize priorities
- Get formal approval

### Handling Conflicts

When stakeholders disagree:
1. **Document the disagreement**: Capture all perspectives
2. **Present trade-offs**: Show pros/cons of each option
3. **Escalate if needed**: Bring to decision-maker
4. **Document decision**: Record what was decided and why
5. **Move forward**: Commit to the decision

## Success Indicators

Your PRD is ready when:
- Problem and solution are crystal clear
- All stakeholders are aligned
- Engineers can estimate work
- Designers can create mockups
- QA can plan test strategy
- Success metrics are defined
- No major open questions remain

## Template Quick Reference

```markdown
# PRD: [Product Name]

**Author**: [Name] | **Date**: [Date] | **Status**: [Draft/Review/Approved]

## Executive Summary
[2-3 paragraphs: what, why, impact]

## Problem Statement
### The Problem | Current Situation | The Solution | Why Now

## Goals & Success Criteria
### Goals | Success Criteria | KPIs

## User Personas & Use Cases
### Primary Persona | Secondary Personas | Use Cases

## Functional Requirements
[Organized by feature category with priorities]

## Non-Functional Requirements
### Performance | Security | Usability | Reliability

## User Experience & Design
### Key User Flows | UI/UX Considerations

## Technical Considerations
### Integration Points | Data Requirements | Constraints

## Competitive Analysis
### Competitors | Positioning | Differentiation

## Scope & Prioritization
### In Scope | Out of Scope | MVP vs. Future

## Dependencies & Risks
### Dependencies | Risks & Mitigation

## Timeline & Milestones
### High-Level Timeline | Release Strategy

## Metrics & Analytics
### Analytics Requirements | Success Metrics

## Open Questions
[TBD items]

## Appendix
### References | Change Log
```
