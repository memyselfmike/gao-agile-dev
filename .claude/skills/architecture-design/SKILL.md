---
name: architecture-design
description: Design system architectures with focus on scalability, maintainability, and user value. Create comprehensive architectural documentation including technology decisions, API design, data architecture, and security. Use when designing new systems, making technology choices, or planning system migrations.
allowed-tools: Read, Write, Edit, Grep, Glob, WebFetch
---

# Architecture Design Skill

This skill guides you through creating pragmatic, well-documented system architectures that balance business needs with technical excellence.

## When to Use

Use this skill when you need to:
- Design a new system or major component
- Evaluate and select technologies
- Plan system migrations or refactoring
- Document architectural decisions
- Review and validate existing architectures

## Core Architecture Principles

### 1. User Journeys First
Start with how users interact with the system. Let user needs drive technical decisions.

### 2. Boring Technology
Prefer proven, stable technologies. Reserve innovation for genuine competitive advantages.

### 3. Design for Evolution
Systems must adapt to changing requirements. Build for continuous evolution.

### 4. Security by Design
Build security in from the start, not bolt it on later.

### 5. Developer Productivity
Good architecture enables developers to be productive and deliver value quickly.

### 6. Simplicity Over Cleverness
Simple solutions that can scale beat clever solutions that can't be maintained.

## Architecture Document Structure

### 1. Executive Summary
**Purpose**: High-level overview for stakeholders
**Include**:
- System purpose and key capabilities
- Critical architectural decisions (1-2 paragraphs)
- Technology stack overview
- Major trade-offs made

### 2. User Journeys & Data Flow
**Purpose**: Connect architecture to user needs
**Include**:
- Primary user scenarios (3-5 key journeys)
- Data flow through the system for each journey
- Integration touchpoints
- User-facing vs. backend components

**Diagram**: User journey flowchart showing system interactions

### 3. System Architecture
**Purpose**: High-level component view
**Include**:
- Component diagram showing major parts
- Component responsibilities (what each does)
- Communication patterns (sync/async, protocols)
- Deployment topology

**Diagram**: C4 Context or Container diagram

### 4. Technology Stack
**Purpose**: Document technology choices with rationale
**Include**:
- Language/framework with justification
- Database(s) with use case explanation
- Infrastructure decisions (cloud, containers, etc.)
- Third-party services and why

**Format**:
```markdown
### Backend: Python/FastAPI
**Rationale**: Team expertise, strong async support, excellent data science libraries for planned ML features.

**Alternatives Considered**:
- Go: Better performance but team lacks expertise
- Node.js: Good for real-time but weaker for data processing

### Database: PostgreSQL
**Rationale**: ACID guarantees needed for financial transactions, excellent JSON support for flexible schema, proven at scale.

**Alternatives Considered**:
- MongoDB: More flexible but lacks ACID guarantees
- DynamoDB: Serverless appeal but vendor lock-in concerns
```

### 5. API Design
**Purpose**: Define how components communicate
**Include**:
- API architecture (REST, GraphQL, gRPC, etc.) with rationale
- Authentication/Authorization approach
- Endpoint design principles
- Versioning strategy
- Error handling patterns

**Example**:
```markdown
### REST API Design

**Principles**:
- Resource-oriented URLs (/api/users, /api/orders)
- HTTP verbs for operations (GET, POST, PUT, DELETE)
- JSON for request/response bodies
- Consistent error responses

**Authentication**: JWT tokens with 1-hour expiry, refresh tokens for renewal

**Versioning**: URL-based versioning (/api/v1/, /api/v2/)

**Endpoints**:
- GET /api/v1/users - List users (paginated)
- POST /api/v1/users - Create user
- GET /api/v1/users/{id} - Get user details
```

### 6. Data Architecture
**Purpose**: Define how data is stored and accessed
**Include**:
- Database schema approach
- Data modeling decisions
- Caching strategy
- Data consistency guarantees
- Backup and recovery

**Diagram**: Entity-relationship diagram or data flow diagram

### 7. Security Architecture
**Purpose**: Document security measures
**Include**:
- Authentication mechanism (OAuth, JWT, etc.)
- Authorization model (RBAC, ABAC)
- Data protection (encryption at rest/in transit)
- Security boundaries and trust zones
- Threat mitigation strategies

**Security Checklist**:
- [ ] Authentication implemented
- [ ] Authorization enforced
- [ ] Data encrypted in transit (TLS)
- [ ] Sensitive data encrypted at rest
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Security logging

### 8. Scalability & Performance
**Purpose**: Define how system will scale
**Include**:
- Scaling strategy (horizontal/vertical)
- Performance targets (latency, throughput)
- Bottleneck identification
- Load balancing approach
- Caching strategy

**Performance Targets Example**:
```markdown
- API Response Time: p95 < 200ms, p99 < 500ms
- Page Load Time: < 2 seconds
- Concurrent Users: Support 10,000 concurrent users
- Database Queries: < 50ms for read queries
- Throughput: 1,000 requests/second
```

### 9. Deployment Architecture
**Purpose**: Define how system is deployed
**Include**:
- Deployment topology (regions, availability zones)
- Environment strategy (dev/staging/prod)
- CI/CD approach
- Infrastructure as Code (Terraform, CloudFormation)
- Monitoring and observability

**Diagram**: Deployment diagram showing infrastructure

### 10. Non-Functional Requirements
**Purpose**: Define quality attributes
**Include**:
- Availability targets (99.9%, 99.99%)
- Disaster recovery plan (RTO, RPO)
- Monitoring and alerting
- Logging strategy
- Backup and recovery

### 11. Migration Strategy (if applicable)
**Purpose**: Plan migration from existing system
**Include**:
- Current state assessment
- Target state definition
- Migration approach (big bang vs. incremental)
- Risk assessment and mitigation
- Rollback plan
- Data migration strategy

### 12. Technical Debt & Future Considerations
**Purpose**: Acknowledge limitations and future work
**Include**:
- Known limitations and trade-offs
- Technical debt being accepted
- Future enhancement areas
- When to revisit key decisions

## Technology Evaluation Framework

When selecting technologies, evaluate:

### 1. Requirements Fit
- Does it meet our functional requirements?
- Does it meet our non-functional requirements (performance, scale)?

### 2. Team Expertise
- Do we have the skills?
- Can we acquire the skills quickly?
- Is training available?

### 3. Community & Ecosystem
- Is it actively maintained?
- Is documentation good?
- Are there good libraries and tools?
- Is community support available?

### 4. Performance
- Does it meet performance requirements?
- Are there benchmarks available?
- What's the scalability story?

### 5. Cost
- Licensing costs
- Infrastructure costs
- Development costs
- Maintenance costs

### 6. Risk
- What if it's abandoned?
- What if it doesn't scale?
- What's the migration path out?
- Vendor lock-in concerns?

## Architectural Patterns

### Common Patterns to Consider

**Monolith vs. Microservices**:
- Start with well-structured monolith
- Split only when clear bounded contexts emerge
- Consider operational complexity

**Layered Architecture**:
- Presentation → Business Logic → Data Access
- Clear separation of concerns
- Easy to understand and maintain

**Event-Driven Architecture**:
- Components communicate via events
- Good for complex workflows
- Enables loose coupling

**CQRS (Command Query Responsibility Segregation)**:
- Separate read and write models
- Optimize each for its purpose
- Use when read/write patterns differ significantly

**API Gateway Pattern**:
- Single entry point for clients
- Handles authentication, rate limiting, routing
- Simplifies client interactions

## Architecture Review Checklist

Before finalizing architecture:

**Functional Completeness**
- [ ] All PRD requirements addressed
- [ ] User journeys supported
- [ ] Integration points defined
- [ ] Data flows complete

**Technical Excellence**
- [ ] Technology choices justified
- [ ] Security comprehensively addressed
- [ ] Scalability approach clear
- [ ] Performance targets defined
- [ ] Monitoring planned

**Pragmatism**
- [ ] Avoids over-engineering
- [ ] Matches team capabilities
- [ ] Fits timeline and budget
- [ ] Enables iterative delivery

**Documentation Quality**
- [ ] Diagrams are clear
- [ ] Decisions are explained
- [ ] Trade-offs are documented
- [ ] Future considerations noted

## Common Anti-Patterns to Avoid

1. **Resume-Driven Development**: Choosing tech for your resume
2. **Golden Hammer**: Using same solution for every problem
3. **Big Ball of Mud**: No clear architecture or boundaries
4. **Premature Optimization**: Optimizing before measuring
5. **Not Invented Here**: Rebuilding everything from scratch
6. **Shiny Object Syndrome**: Chasing latest trends without justification
7. **Analysis Paralysis**: Over-analyzing without deciding
8. **Ivory Tower Architecture**: Ignoring implementation realities

## Step-by-Step Process

1. **Understand Requirements**
   - Review PRD thoroughly
   - Identify key user journeys
   - Note non-functional requirements
   - Understand constraints

2. **Map User Journeys**
   - Document 3-5 critical journeys
   - Follow data flow through system
   - Identify touchpoints and integrations

3. **Identify Components**
   - Break system into logical components
   - Define component responsibilities
   - Identify interfaces

4. **Select Technologies**
   - Evaluate options for each component
   - Apply evaluation framework
   - Document decisions and rationale

5. **Design Data Architecture**
   - Model key entities
   - Choose database(s)
   - Plan caching strategy

6. **Design APIs**
   - Define communication protocols
   - Design endpoint structure
   - Plan authentication/authorization

7. **Address Security**
   - Apply security checklist
   - Design authentication/authorization
   - Plan data protection

8. **Plan for Scale**
   - Define performance targets
   - Design scaling strategy
   - Identify bottlenecks

9. **Plan Deployment**
   - Design deployment topology
   - Plan CI/CD pipeline
   - Define monitoring strategy

10. **Document Everything**
    - Create diagrams
    - Write rationale for decisions
    - Document trade-offs
    - Note future considerations

11. **Review & Iterate**
    - Get feedback from team
    - Address concerns
    - Refine based on input

## Success Indicators

Your architecture is ready when:
- User needs are clearly supported
- Technology choices are justified
- Security is designed in
- System can scale to meet needs
- Team can implement it
- Stakeholders understand key decisions
- Trade-offs are explicit
- Documentation is clear and complete

## Quick Template

```markdown
# Architecture: [Project Name]

## Executive Summary
[What we're building, key decisions, tech stack, major trade-offs]

## User Journeys & Data Flow
[3-5 key journeys with data flow]

## System Architecture
[Component diagram and descriptions]

## Technology Stack
[Choices with rationale for each]

## API Design
[Architecture, authentication, endpoints]

## Data Architecture
[Schema, caching, consistency]

## Security Architecture
[Authentication, authorization, data protection, threats]

## Scalability & Performance
[Targets, scaling strategy, bottlenecks]

## Deployment Architecture
[Topology, environments, CI/CD, monitoring]

## Non-Functional Requirements
[Availability, DR, monitoring, logging]

## Technical Debt & Future
[Limitations, future enhancements, decision revisit triggers]
```
