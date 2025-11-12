---
description: Review planning documents using CRAAP framework
---

# CRAAP Framework Review for Feature Planning

You are now conducting a systematic review of planning documents using the **CRAAP framework** to identify potential issues and generate a comprehensive report.

## Step 1: Gather Information

Ask the user for the following information:
1. **Feature Name**: What feature are you reviewing?
2. **Folder Path**: Where are the planning documents located? (e.g., `docs/features/user-auth/`)

## Step 2: Document Discovery

Once you have the Feature Name and Folder Path:
- Search the specified folder for relevant planning documents
- Prioritize documents like:
  - Product Requirements Document (PRD.md)
  - Architecture Document (ARCHITECTURE.md)
  - Technical Specification
  - README.md
  - Any other files containing detailed planning

If multiple relevant documents are found, process them collectively.
If no relevant documents are found, inform the user and ask for clarification.

## Step 3: Apply CRAAP Framework

For each identified planning document, systematically apply the **CRAAP framework**:

### C - Critique and Refine
- Identify **weaknesses** in the current plan
- Find **vague areas** that lack sufficient detail
- Spot **redundancies** or unnecessary complexity
- Discover **opportunities for improvement**
- Question assumptions and validate they are sound

**Key Questions:**
- Are requirements clearly defined and measurable?
- Is the scope well-bounded?
- Are success criteria explicit?
- Are there any contradictions or inconsistencies?

### R - Risk Potential and Unforeseen Issues
- Analyze **potential flaws** in the approach
- Identify **blind spots** the team may have missed
- Consider **negative consequences** of proposed solutions
- Evaluate **edge cases** and error scenarios
- Assess **technical risks** and dependencies

**Key Questions:**
- What could go wrong with this approach?
- What are we not seeing?
- What assumptions could prove false?
- What external dependencies could fail?
- What security/performance/scalability risks exist?

### A - Analyse Flow / Dependencies
- Examine **logical structure** and organization
- Review **sequencing** of implementation steps
- Map **interdependencies** between components
- Check **data flow** and integration points
- Validate **timing and ordering** of deliverables

**Key Questions:**
- Does the implementation sequence make sense?
- Are dependencies clearly identified?
- Are there circular dependencies?
- Is the phasing/milestoning logical?
- Are integration points well-defined?

### A - Alignment with Goal
- Verify every component **supports the core objective**
- Check that requirements **trace to business goals**
- Ensure **no scope creep** or unnecessary features
- Validate **priorities** align with value delivery
- Confirm **success metrics** measure what matters

**Key Questions:**
- Does each requirement serve the core goal?
- Are we solving the right problem?
- Is anything missing that's critical to success?
- Are priorities aligned with business value?
- Will success criteria prove we've achieved the goal?

### P - Perspective
- Challenge assumptions from a **critical outsider's viewpoint**
- Consider **alternative approaches** not explored
- Question **"obvious" decisions** that may not be optimal
- Think like a **user, developer, tester, operator**
- Apply **devil's advocate** reasoning

**Key Questions:**
- What would an outsider question about this plan?
- Are we making assumptions we shouldn't?
- What alternatives did we not consider?
- Would this make sense to someone unfamiliar with the context?
- What would each stakeholder (user, dev, ops) critique?

## Step 4: Compile Findings

Create a comprehensive list of:
- **Critical Issues**: Must be addressed before proceeding
- **Moderate Concerns**: Should be addressed soon
- **Minor Improvements**: Nice-to-have enhancements
- **Recommendations**: Specific actions to mitigate issues

## Step 5: Generate Report

Create a new file in the **specified Folder Path** named:
`CRAAP_Review_[Feature Name].md`

The report should include:

```markdown
# CRAAP Review: [Feature Name]

**Review Date**: [Current Date]
**Documents Reviewed**:
- [List all documents reviewed]

---

## Executive Summary

[Brief overview of the review findings]

---

## CRAAP Analysis

### Critique and Refine

**Identified Issues:**
- [Issue 1]
- [Issue 2]
...

**Recommendations:**
- [Recommendation 1]
- [Recommendation 2]
...

### Risk Potential and Unforeseen Issues

**Identified Risks:**
- [Risk 1]
- [Risk 2]
...

**Mitigation Strategies:**
- [Strategy 1]
- [Strategy 2]
...

### Analyse Flow / Dependencies

**Dependency Issues:**
- [Issue 1]
- [Issue 2]
...

**Flow Improvements:**
- [Improvement 1]
- [Improvement 2]
...

### Alignment with Goal

**Alignment Concerns:**
- [Concern 1]
- [Concern 2]
...

**Recommendations:**
- [Recommendation 1]
- [Recommendation 2]
...

### Perspective (Critical Outsider View)

**Challenging Assumptions:**
- [Assumption 1]
- [Assumption 2]
...

**Alternative Approaches:**
- [Alternative 1]
- [Alternative 2]
...

---

## Priority Issues

### Critical (Must Fix)
1. [Issue]
2. [Issue]

### Moderate (Should Fix)
1. [Issue]
2. [Issue]

### Minor (Nice to Have)
1. [Issue]
2. [Issue]

---

## Action Items

1. [ ] [Action item with owner]
2. [ ] [Action item with owner]
...

---

## Conclusion

[Summary of overall health of the planning documents and next steps]
```

## Example Interaction Flow

**Agent:** "I'll help you review your feature planning documents using the CRAAP framework. What is the name of the feature you'd like to review?"

**User:** "User Authentication"

**Agent:** "Great. In which folder are the planning documents located?"

**User:** "docs/features/user-auth/"

**Agent:** "Thank you. I will now:
1. Search for planning documents in 'docs/features/user-auth/'
2. Apply the CRAAP framework to systematically review them
3. Generate a comprehensive report in 'docs/features/user-auth/CRAAP_Review_User_Authentication.md'"

[Agent performs the review]

**Agent:** "The review is complete. I've created 'CRAAP_Review_User_Authentication.md' with:
- X critical issues found
- Y moderate concerns identified
- Z recommendations provided

Would you like me to walk you through the key findings?"

---

## Important Notes

- **Be thorough**: The goal is to stress-test the planning documents
- **Be specific**: Vague findings like "could be better" aren't helpful
- **Be constructive**: Always provide actionable recommendations
- **Be objective**: Apply the same rigor regardless of who created the documents
- **Be systematic**: Work through each CRAAP element methodically

Now, let's begin. What feature would you like to review?
