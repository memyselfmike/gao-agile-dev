# Product Requirements Document
## Todo Application - Reference Benchmark

**Version:** 1.0.0
**Date:** 2025-10-27
**Status:** Final
**Author:** John (Product Manager) via GAO-Dev
**Purpose:** Reference application for GAO-Dev autonomous benchmarking

---

## Executive Summary

### Vision

Create a production-quality todo application that serves as the reference benchmark for validating GAO-Dev's autonomous development capabilities. This application must be realistic enough to represent real-world projects while scoped appropriately for deterministic benchmarking.

### Goals

1. **Validate Autonomy**: Prove GAO-Dev can build production-ready applications autonomously
2. **Measure Performance**: Generate meaningful metrics across all categories (performance, autonomy, quality, workflow)
3. **Establish Baseline**: Create a repeatable benchmark for tracking improvements
4. **Demonstrate Quality**: Showcase GAO-Dev's ability to produce clean, tested, documented code

### Success Metrics

**Development Metrics:**
- Build time: 30-60 minutes (autonomous)
- Token usage: <500k tokens
- API cost: <$5 per run

**Quality Metrics:**
- Test coverage: >80%
- Zero TypeScript errors
- Zero linting errors
- API documented (OpenAPI/Swagger)
- Accessibility score: WCAG 2.1 AA

**Autonomy Metrics:**
- Manual interventions: 0
- One-shot success rate: >90%
- Error recovery rate: >80%

---

## Problem Statement

### User Needs

**Target User**: Individual professionals and students who need to organize personal tasks

**Pain Points:**
- Scattered tasks across multiple apps and sticky notes
- Difficulty prioritizing work
- Missing deadlines due to poor organization
- No single source of truth for personal tasks
- Lack of context/categorization for tasks

### Current Solutions

**Existing Apps:**
- Todoist: Feature-rich but complex
- Microsoft To Do: Good integration but limited customization
- Any.do: Simple but lacks power features
- Apple Reminders: iOS-only, limited functionality

**Gaps:**
- Most are either too simple or too complex
- Many lack proper categorization
- Few offer good keyboard navigation
- Limited accessibility features

### Our Approach

Build a **balanced todo application** that:
- Provides essential features without bloat
- Offers flexible organization (categories + tags)
- Ensures accessibility and keyboard navigation
- Demonstrates production-quality development
- Can be built autonomously by GAO-Dev

---

## Features

### Core Features (P0 - Must Have)

#### Feature 1: User Authentication

**Description**: Secure user registration and login system

**User Stories:**

**US-1.1**: As a new user, I want to register an account so I can save my todos securely
- Email + password registration
- Email validation
- Password strength requirements (8+ chars, 1 uppercase, 1 number, 1 special)
- Duplicate email detection

**US-1.2**: As a returning user, I want to log in to access my todos
- Email + password login
- Remember me option (30-day session)
- Clear error messages for invalid credentials

**US-1.3**: As a logged-in user, I want to log out to secure my account
- Logout button in header
- Session invalidation
- Redirect to login page

**Acceptance Criteria:**
- [ ] Registration form validates all fields
- [ ] Passwords are hashed (bcrypt or argon2)
- [ ] Sessions persist across browser restarts (with "remember me")
- [ ] Invalid login shows "Invalid email or password" (not specific)
- [ ] Logout clears session and redirects

**Technical Requirements:**
- Use NextAuth.js for authentication
- Session storage: JWT or database sessions
- Password hashing: bcrypt (10 rounds minimum)
- CSRF protection enabled

---

#### Feature 2: Todo CRUD Operations

**Description**: Create, read, update, and delete todo items

**User Stories:**

**US-2.1**: As a user, I want to create a new todo so I can track tasks
- Title field (required, 1-200 chars)
- Description field (optional, max 1000 chars)
- Due date picker (optional)
- Priority selector (Low, Medium, High)
- Category dropdown (optional)
- Tag multi-select (optional)

**US-2.2**: As a user, I want to view all my todos so I can see what needs to be done
- List view with todos sorted by due date (nearest first)
- Show: title, due date, priority, category, tags
- Visual indicators for overdue items (red text)
- Completed items shown at bottom with strikethrough

**US-2.3**: As a user, I want to edit a todo to update details
- Click todo to open edit modal
- All fields editable
- Save/Cancel buttons
- Auto-save on blur (optional enhancement)

**US-2.4**: As a user, I want to delete a todo to remove completed or unwanted tasks
- Delete button (trash icon) on each todo
- Confirmation dialog: "Are you sure? This cannot be undone"
- Soft delete (mark as deleted, don't remove from DB immediately)

**US-2.5**: As a user, I want to mark todos as complete to track progress
- Checkbox next to each todo
- Toggle complete/incomplete
- Completed todos move to bottom of list
- Visual differentiation (strikethrough, lighter color)

**Acceptance Criteria:**
- [ ] Can create todo with just title (minimal input)
- [ ] Todos persist across sessions
- [ ] Edit updates reflect immediately
- [ ] Delete requires confirmation
- [ ] Completed todos visually distinct
- [ ] Form validation shows clear error messages

**Technical Requirements:**
- RESTful API endpoints:
  - POST /api/todos - Create
  - GET /api/todos - List (with filtering)
  - GET /api/todos/:id - Get single
  - PUT /api/todos/:id - Update
  - DELETE /api/todos/:id - Delete
  - PATCH /api/todos/:id/complete - Toggle completion
- Optimistic UI updates
- Error handling with rollback on failure

---

#### Feature 3: Categories & Tags

**Description**: Organize todos using categories and tags

**User Stories:**

**US-3.1**: As a user, I want to assign categories to todos so I can group related tasks
- Predefined categories: Work, Personal, Shopping, Health, Other
- Each todo can have 0-1 category
- Categories shown as colored badges

**US-3.2**: As a user, I want to create custom categories so I can personalize organization
- "Manage Categories" page
- Create new category (name + color)
- Edit/delete existing categories
- Max 20 categories per user

**US-3.3**: As a user, I want to add tags to todos for flexible organization
- Tags are free-form text
- Auto-complete from existing tags
- Multiple tags per todo
- Tags shown as small pills

**US-3.4**: As a user, I want to filter todos by category/tag so I can focus
- Filter dropdown: All, Category X, Tag Y
- Filters combine (AND logic)
- Clear filters button
- Filter state persists in URL

**Acceptance Criteria:**
- [ ] Default categories available immediately
- [ ] Custom categories can be created
- [ ] Tags auto-complete from user's existing tags
- [ ] Filters work correctly (show only matching todos)
- [ ] Category colors are visually distinct

**Technical Requirements:**
- Categories table: id, user_id, name, color, is_custom
- Tags table: id, user_id, name
- TodoTags junction table: todo_id, tag_id
- Color palette: 10 predefined colors (hex codes)

---

### Enhanced Features (P1 - Should Have)

#### Feature 4: Filtering & Sorting

**Description**: Advanced filtering and sorting options

**User Stories:**

**US-4.1**: As a user, I want to sort todos by different criteria to organize my view
- Sort options: Due date, Priority, Created date, Alphabetical
- Ascending/descending toggle
- Sort preference saved per user

**US-4.2**: As a user, I want to filter by completion status to focus on active tasks
- Show: All, Active, Completed
- Default: Active only
- Badge showing count in each filter

**US-4.3**: As a user, I want to filter by due date to see urgent items
- Overdue, Today, This week, This month, No due date
- Combined with other filters

**Acceptance Criteria:**
- [ ] Sort persists across page reloads
- [ ] Filters can combine (category + status + due date)
- [ ] Counts update as filters change
- [ ] Fast filtering (<100ms client-side)

---

#### Feature 5: Search

**Description**: Full-text search across todos

**User Stories:**

**US-5.1**: As a user, I want to search todos by title/description to find specific tasks
- Search bar in header
- Searches title and description
- Real-time results (debounced 300ms)
- Highlight matching text

**Acceptance Criteria:**
- [ ] Search is case-insensitive
- [ ] Partial matches work ("meet" finds "meeting")
- [ ] Empty search shows all todos
- [ ] Search combined with filters

**Technical Requirements:**
- Client-side search for <100 todos
- Server-side search for 100+ todos (SQL ILIKE)
- Debounced search to avoid excessive queries

---

#### Feature 6: Bulk Operations

**Description**: Perform actions on multiple todos at once

**User Stories:**

**US-6.1**: As a user, I want to select multiple todos to perform batch operations
- Checkbox selection mode
- Select all / Select none
- Actions: Complete, Delete, Change category

**Acceptance Criteria:**
- [ ] Can select/deselect individual todos
- [ ] Can select all visible todos
- [ ] Bulk actions show confirmation
- [ ] Changes apply atomically (all or none)

---

### Future Features (P2 - Nice to Have)

#### Feature 7: Collaboration
- Share todos with other users
- Assign todos to others
- Comments on todos

#### Feature 8: Attachments
- Upload files to todos
- Image previews
- Max 5MB per file

#### Feature 9: Reminders
- Email reminders for due dates
- Browser notifications
- Recurring reminders

---

## Technical Requirements

### Tech Stack

**Frontend:**
- Framework: Next.js 14+ (App Router)
- Language: TypeScript 5+
- Styling: Tailwind CSS 3+
- UI Components: shadcn/ui or Radix UI
- Forms: React Hook Form + Zod validation
- State: React Context + hooks (or Zustand if needed)
- HTTP Client: fetch with custom wrapper

**Backend:**
- Option A: FastAPI (Python 3.11+)
- Option B: Next.js API Routes (TypeScript)
- Database: PostgreSQL 14+
- ORM: Prisma (Node) or SQLAlchemy (Python)
- Auth: NextAuth.js or FastAPI JWT

**Testing:**
- Frontend: Jest + React Testing Library
- E2E: Playwright
- Backend: Pytest (Python) or Vitest (Node)
- Coverage: >80% required

**DevOps:**
- Containerization: Docker + Docker Compose
- CI/CD: GitHub Actions
- Deployment: Vercel (frontend) or Docker (full-stack)

### System Requirements

**Development Environment:**
- Node.js 18+
- Python 3.11+ (if using FastAPI)
- PostgreSQL 14+
- Docker & Docker Compose
- Git

**Production Environment:**
- CPU: 1 vCPU minimum
- RAM: 512MB minimum
- Storage: 1GB minimum
- Database: PostgreSQL (managed service recommended)

### Architecture Constraints

**Principles:**
- Clean Architecture (separation of concerns)
- API-first design
- Mobile-responsive from day 1
- Accessibility built-in (not retrofitted)

**Patterns:**
- Repository pattern for data access
- Service layer for business logic
- Controller/Route handlers thin
- Dependency injection where applicable

### Integration Points

**Authentication:**
- NextAuth.js providers (credentials, OAuth optional)
- Session management
- CSRF protection

**Database:**
- PostgreSQL via Prisma ORM
- Connection pooling
- Migration management

**External Services (Optional P2):**
- Email service (SendGrid, Resend)
- File storage (S3, Cloudinary)

---

## Non-Functional Requirements

### Performance

**Response Times:**
- Page load: <2 seconds (First Contentful Paint)
- API responses: <200ms (p95)
- Search: <100ms (client-side)
- Database queries: <50ms (p95)

**Scalability:**
- Support 100 concurrent users
- 10,000 todos per user without performance degradation

**Optimization:**
- Code splitting (route-based)
- Image optimization (Next.js Image)
- Database indexes on common queries
- Lazy loading for todo lists

### Security

**OWASP Top 10 Protections:**
- SQL Injection: Use parameterized queries (ORM)
- XSS: React escapes by default, validate input
- CSRF: Token-based protection
- Authentication: Secure password hashing
- Authorization: User can only access own data
- Sensitive Data: No secrets in client code
- Rate Limiting: 100 req/min per IP

**Data Protection:**
- Passwords hashed with bcrypt (cost 10+)
- Sessions use HTTP-only cookies
- HTTPS only in production
- No sensitive data in logs

### Accessibility

**WCAG 2.1 AA Compliance:**
- Semantic HTML (headings, landmarks, lists)
- Keyboard navigation (tab order, focus management)
- Screen reader support (ARIA labels, live regions)
- Color contrast ratio: 4.5:1 minimum
- Focus indicators visible
- No keyboard traps

**Testing:**
- Automated: axe-core via Playwright
- Manual: Keyboard-only navigation test
- Screen reader: Test with NVDA/JAWS

### Usability

**Design Principles:**
- Mobile-first responsive design
- Consistent UI patterns
- Clear error messages
- Confirmation for destructive actions
- Loading states for async operations

**Browser Support:**
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

**Device Support:**
- Desktop: 1024px+ (optimal experience)
- Tablet: 768px-1023px
- Mobile: 375px-767px

---

## User Stories & Acceptance Criteria

### Epic: User Management

**Story 1: User Registration**

As a new user, I want to create an account so I can start using the app.

**Acceptance Criteria:**
- [ ] Registration form has email, password, confirm password fields
- [ ] Email validation: valid format, unique
- [ ] Password validation: 8+ chars, 1 uppercase, 1 number, 1 special
- [ ] Confirm password must match
- [ ] Success: User created, logged in, redirected to todos page
- [ ] Error: Clear message shown, form not cleared

**Test Scenarios:**
```
1. Valid registration -> Account created, user logged in
2. Duplicate email -> Error: "Email already registered"
3. Weak password -> Error: "Password must contain..."
4. Mismatched passwords -> Error: "Passwords do not match"
```

---

**Story 2: User Login**

As a returning user, I want to log in to access my todos.

**Acceptance Criteria:**
- [ ] Login form has email, password, remember me checkbox
- [ ] Valid credentials -> User logged in, redirect to todos
- [ ] Invalid credentials -> Generic error (don't reveal which field)
- [ ] Remember me -> Session lasts 30 days
- [ ] No remember me -> Session lasts 24 hours
- [ ] Logout -> Session cleared, redirect to login

**Test Scenarios:**
```
1. Valid credentials -> Logged in successfully
2. Invalid email -> Error: "Invalid credentials"
3. Invalid password -> Error: "Invalid credentials"
4. Remember me checked -> Session persists after browser close
5. Logout -> Session cleared, redirected to login
```

---

### Epic: Todo Management

**Story 3: Create Todo**

As a user, I want to create a new todo to track a task.

**Acceptance Criteria:**
- [ ] Create form has: title, description, due date, priority, category, tags
- [ ] Only title is required
- [ ] Due date: date picker, optional
- [ ] Priority: dropdown (Low, Medium, High), defaults to Medium
- [ ] Category: dropdown from user's categories, optional
- [ ] Tags: multi-select with autocomplete, optional
- [ ] Success: Todo created, appears in list, form cleared
- [ ] Error: Validation messages shown inline

**Test Scenarios:**
```
1. Minimal (title only) -> Todo created with defaults
2. All fields -> Todo created with all data
3. Empty title -> Error: "Title is required"
4. Title too long (>200) -> Error: "Title max 200 characters"
5. Past due date -> Accepted (user might be logging old task)
```

---

**Story 4: View Todos**

As a user, I want to see all my todos in an organized list.

**Acceptance Criteria:**
- [ ] Todos displayed as cards/rows
- [ ] Show: checkbox, title, due date, priority badge, category badge, tags
- [ ] Sorted by due date (nearest first), then priority
- [ ] Overdue items highlighted (red text or border)
- [ ] Completed items at bottom with strikethrough
- [ ] Empty state: "No todos yet. Create your first one!"

**Test Scenarios:**
```
1. No todos -> Empty state shown
2. Multiple todos -> Sorted correctly
3. Overdue todo -> Highlighted in red
4. Completed todo -> At bottom, strikethrough
```

---

**Story 5: Edit Todo**

As a user, I want to edit a todo to update its details.

**Acceptance Criteria:**
- [ ] Click todo -> Opens edit modal/form
- [ ] All fields populated with current values
- [ ] Changes save on "Save" click
- [ ] Modal closes on save or cancel
- [ ] Optimistic update: Changes show immediately
- [ ] Error: Rollback on failure, show error message

**Test Scenarios:**
```
1. Edit title -> Saved and displayed
2. Change due date -> Updated correctly
3. Add tags -> Tags appear on todo
4. Cancel edit -> No changes applied
5. Save with invalid data -> Error shown, modal stays open
```

---

**Story 6: Delete Todo**

As a user, I want to delete a todo to remove it from my list.

**Acceptance Criteria:**
- [ ] Delete button (trash icon) visible on hover or always
- [ ] Click delete -> Confirmation dialog appears
- [ ] Dialog: "Are you sure? This cannot be undone." + Cancel/Delete buttons
- [ ] Delete confirmed -> Todo removed from list immediately
- [ ] Delete cancelled -> No action taken
- [ ] Soft delete: Mark as deleted, don't remove from DB

**Test Scenarios:**
```
1. Delete + confirm -> Todo removed from list
2. Delete + cancel -> Todo remains
3. Deleted todo -> No longer appears in any filter
4. Deleted todo -> Can be recovered from admin panel (future)
```

---

**Story 7: Complete Todo**

As a user, I want to mark todos as complete to track my progress.

**Acceptance Criteria:**
- [ ] Checkbox next to each todo
- [ ] Click checkbox -> Todo marked complete, moves to bottom
- [ ] Click again -> Todo marked incomplete, moves back to position
- [ ] Completed todos: Strikethrough text, lighter color
- [ ] State persists across page reloads

**Test Scenarios:**
```
1. Mark complete -> Moves to bottom, strikethrough applied
2. Mark incomplete -> Moves back to sorted position
3. Reload page -> Completion state persists
```

---

### Epic: Organization

**Story 8: Manage Categories**

As a user, I want to create and manage custom categories.

**Acceptance Criteria:**
- [ ] "Manage Categories" page accessible from settings
- [ ] List of all categories (default + custom)
- [ ] Create: Name + color picker
- [ ] Edit: Change name or color
- [ ] Delete: Only if no todos use it (or reassign prompt)
- [ ] Max 20 categories per user

**Test Scenarios:**
```
1. Create category -> Appears in list and dropdowns
2. Edit category -> Changes reflected on todos
3. Delete unused category -> Removed successfully
4. Delete used category -> Error or reassign prompt
5. Create 21st category -> Error: "Max 20 categories"
```

---

**Story 9: Filter by Category/Tag**

As a user, I want to filter todos by category or tag.

**Acceptance Criteria:**
- [ ] Filter controls above todo list
- [ ] Category dropdown: All, [each category]
- [ ] Tag multi-select: [all user's tags]
- [ ] Filters apply immediately (client-side)
- [ ] Filter state in URL (shareable, bookmarkable)
- [ ] Clear filters button

**Test Scenarios:**
```
1. Filter by category -> Only matching todos shown
2. Filter by tag -> Only matching todos shown
3. Filter by both -> AND logic (must match both)
4. Clear filters -> All todos shown
5. Copy URL -> Same filter state on paste
```

---

### Epic: Advanced Features

**Story 10: Search Todos**

As a user, I want to search my todos by title or description.

**Acceptance Criteria:**
- [ ] Search input in header or above todo list
- [ ] Searches title and description fields
- [ ] Debounced: 300ms after typing stops
- [ ] Case-insensitive, partial matching
- [ ] Highlights matching text in results (optional)
- [ ] Empty search -> Shows all todos

**Test Scenarios:**
```
1. Search "meeting" -> Finds "Team Meeting", "Meeting notes"
2. Search "MEETING" -> Same results (case-insensitive)
3. Search "xyz123" -> No results message
4. Clear search -> All todos shown
```

---

## Success Metrics

### Quality KPIs

**Code Quality:**
- Test coverage: >80% (target 90%)
- Type coverage: 100% (no `any` types)
- Linting: 0 errors, 0 warnings
- Complexity: Cyclomatic complexity <10 per function

**Functional Quality:**
- All user stories: Acceptance criteria met 100%
- Regression bugs: 0 after final review
- Accessibility: 0 violations (automated scan)

### Performance KPIs

**Speed:**
- Page load (FCP): <2s
- API response time (p95): <200ms
- Search response: <100ms

**Efficiency:**
- Bundle size: <500KB (gzipped)
- Lighthouse score: >90 (Performance, Accessibility, Best Practices, SEO)

### User Experience KPIs

**Usability:**
- Keyboard navigable: 100% of functionality
- Mobile-friendly: Responsive on all screen sizes
- Error recovery: Clear messages for all error states

**Completeness:**
- All P0 features: 100% implemented
- All P1 features: 100% implemented
- API documentation: 100% coverage

### Autonomy KPIs (for GAO-Dev Benchmark)

**Autonomous Completion:**
- Manual interventions: 0
- One-shot success: >90%
- Error recovery: >80%

**Development Metrics:**
- Build time: 30-60 minutes
- Token usage: <500k
- Cost: <$5

---

## Timeline & Milestones

### Phase 1: Foundation (Week 1)
**Deliverables:**
- Project setup (Next.js, Tailwind, PostgreSQL)
- Authentication system
- Database schema & migrations

**Success Criteria:**
- [ ] Users can register and log in
- [ ] Database tables created
- [ ] Tests passing for auth

---

### Phase 2: Core Features (Week 2)
**Deliverables:**
- Todo CRUD operations
- Categories & tags
- Basic filtering

**Success Criteria:**
- [ ] Can create, read, update, delete todos
- [ ] Categories work
- [ ] Tags work
- [ ] >80% test coverage

---

### Phase 3: Enhanced Features (Week 3)
**Deliverables:**
- Search functionality
- Advanced filtering
- Bulk operations
- UI polish

**Success Criteria:**
- [ ] Search works correctly
- [ ] All filters functional
- [ ] Bulk operations tested
- [ ] Responsive design complete

---

### Phase 4: Quality & Deployment (Week 4)
**Deliverables:**
- Full test suite
- API documentation
- Docker deployment
- Accessibility audit

**Success Criteria:**
- [ ] >80% code coverage
- [ ] 0 TypeScript errors
- [ ] 0 accessibility violations
- [ ] Deployable with `docker-compose up`

---

## Risks & Mitigations

### Risk 1: Scope Creep
**Impact**: High
**Probability**: Medium
**Mitigation**: Strict adherence to P0/P1 priorities; P2 features deferred

### Risk 2: Authentication Complexity
**Impact**: Medium
**Probability**: Medium
**Mitigation**: Use NextAuth.js (battle-tested); start with simple credentials provider

### Risk 3: Database Performance
**Impact**: Medium
**Probability**: Low
**Mitigation**: Proper indexes; query optimization; pagination for large lists

### Risk 4: Accessibility Gaps
**Impact**: High (for production use)
**Probability**: Medium
**Mitigation**: Automated testing with axe-core; manual keyboard testing; use semantic HTML

### Risk 5: Autonomous Build Complexity
**Impact**: High (for benchmark)
**Probability**: Medium
**Mitigation**: Clear specifications; comprehensive tests; iterative improvement via Epic 7

---

## Open Questions

1. **Backend Choice**: FastAPI (Python) or Next.js API routes (TypeScript)?
   - **Recommendation**: Next.js API routes (simpler deployment, single language)

2. **State Management**: React Context or Zustand/Redux?
   - **Recommendation**: React Context (sufficient for this scope)

3. **UI Component Library**: shadcn/ui, Radix, or custom?
   - **Recommendation**: shadcn/ui (modern, accessible, customizable)

4. **Deployment Target**: Vercel, Docker, or both?
   - **Recommendation**: Docker (more realistic for benchmarking full-stack deployment)

5. **Email Integration**: Required for P0?
   - **Decision**: No, defer to P2 (adds complexity without benchmark value)

---

## Appendix

### A. Database Schema (ERD)

```
Users
- id: UUID (PK)
- email: VARCHAR(255) UNIQUE NOT NULL
- password_hash: VARCHAR(255) NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()

Categories
- id: UUID (PK)
- user_id: UUID (FK -> Users.id)
- name: VARCHAR(50) NOT NULL
- color: VARCHAR(7) NOT NULL (hex color)
- is_custom: BOOLEAN DEFAULT TRUE
- created_at: TIMESTAMP DEFAULT NOW()

Tags
- id: UUID (PK)
- user_id: UUID (FK -> Users.id)
- name: VARCHAR(50) NOT NULL
- created_at: TIMESTAMP DEFAULT NOW()
UNIQUE(user_id, name)

Todos
- id: UUID (PK)
- user_id: UUID (FK -> Users.id)
- title: VARCHAR(200) NOT NULL
- description: TEXT NULL
- due_date: DATE NULL
- priority: ENUM('low', 'medium', 'high') DEFAULT 'medium'
- category_id: UUID NULL (FK -> Categories.id)
- is_completed: BOOLEAN DEFAULT FALSE
- completed_at: TIMESTAMP NULL
- is_deleted: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT NOW()
- updated_at: TIMESTAMP DEFAULT NOW()

TodoTags (junction table)
- todo_id: UUID (FK -> Todos.id)
- tag_id: UUID (FK -> Tags.id)
PRIMARY KEY(todo_id, tag_id)
```

### B. API Endpoints

**Authentication:**
```
POST   /api/auth/register      - Register new user
POST   /api/auth/login         - Login
POST   /api/auth/logout        - Logout
GET    /api/auth/session       - Get current session
```

**Todos:**
```
GET    /api/todos              - List todos (with filters)
POST   /api/todos              - Create todo
GET    /api/todos/:id          - Get single todo
PUT    /api/todos/:id          - Update todo
DELETE /api/todos/:id          - Delete todo
PATCH  /api/todos/:id/complete - Toggle completion
POST   /api/todos/bulk/complete - Bulk complete
POST   /api/todos/bulk/delete  - Bulk delete
```

**Categories:**
```
GET    /api/categories         - List categories
POST   /api/categories         - Create category
PUT    /api/categories/:id     - Update category
DELETE /api/categories/:id     - Delete category
```

**Tags:**
```
GET    /api/tags               - List user's tags
POST   /api/tags               - Create tag
DELETE /api/tags/:id           - Delete tag
```

### C. UI Wireframes

**Login Page:**
```
+----------------------------------+
|           Todo App               |
+----------------------------------+
|                                  |
|   Email:    [____________]       |
|   Password: [____________]       |
|   [ ] Remember me                |
|                                  |
|   [      Login      ]            |
|                                  |
|   Don't have account? Register   |
+----------------------------------+
```

**Todos List Page:**
```
+----------------------------------+
| Todo App          [Search]  User |
+----------------------------------+
| Filters: [All v] [Tags v] [x]    |
| Sort: [Due Date v] [^]           |
+----------------------------------+
| [ ] Team Meeting                 |
|     Due: Tomorrow | High | Work  |
|     #planning #urgent            |
+----------------------------------+
| [ ] Buy groceries                |
|     Due: Today | Medium | Personal|
|     #errands                     |
+----------------------------------+
| [+] Add Todo                     |
+----------------------------------+
```

### D. Testing Strategy

**Unit Tests (>80% coverage):**
- All service functions
- All utility functions
- React components (user interactions)

**Integration Tests:**
- API endpoints (request/response)
- Database operations
- Authentication flow

**E2E Tests (Critical Paths):**
- User registration -> login -> create todo -> logout
- Create todo -> edit -> complete -> delete
- Filter by category -> search -> clear filters

**Accessibility Tests:**
- Automated: axe-core scan on all pages
- Manual: Keyboard navigation test
- Screen reader: Test with NVDA

---

## Approval & Sign-off

**Product Review (John - PM)**:
- [ ] Product vision approved
- [ ] Features aligned with goals
- [ ] Success metrics appropriate

**Technical Review (Winston - Architect)**:
- [ ] Tech stack approved
- [ ] Architecture sound
- [ ] Performance targets achievable

**Development Review (Amelia - Developer)**:
- [ ] Requirements clear
- [ ] Acceptance criteria testable
- [ ] Implementable autonomously

**QA Review (Murat - QA)**:
- [ ] Test strategy comprehensive
- [ ] Quality gates appropriate
- [ ] Success criteria measurable

**Final Approval**:
- [ ] Ready for Story 6.2 (Architecture)
- [ ] Ready for autonomous implementation

---

*This PRD serves as the definitive specification for the reference todo application used in GAO-Dev benchmarking. It is designed to be clear, complete, and implementable by autonomous agents.*
