# System Architecture
## Todo Application - Reference Benchmark

**Version:** 1.0.0
**Date:** 2025-10-27
**Status:** Final
**Author:** Winston (Architect) via GAO-Dev
**Purpose:** Technical architecture for GAO-Dev benchmark todo application

---

## 1. Overview

### 1.1 System Context

The Todo Application is a modern, full-stack web application designed to serve as a reference benchmark for GAO-Dev's autonomous development capabilities. It demonstrates production-quality code generation, proper architectural patterns, and comprehensive testing.

**System Boundary:**
- Users interact via web browser
- Application handles all business logic
- PostgreSQL stores all persistent data
- No external API dependencies (for simplicity and determinism)

### 1.2 Architectural Principles

**Clean Architecture:**
- Separation of concerns across layers
- Business logic independent of frameworks
- Dependency inversion (abstractions don't depend on details)
- Testable components with clear boundaries

**API-First Design:**
- Well-defined API contracts
- RESTful conventions
- OpenAPI/Swagger documentation
- Versioning strategy (future-proof)

**Security by Design:**
- Defense in depth
- Least privilege access
- Secure defaults
- OWASP Top 10 protections

**Performance First:**
- Fast initial page load (<2s FCP)
- Optimized database queries
- Efficient data structures
- Progressive enhancement

**Accessibility Built-In:**
- Semantic HTML
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support

### 1.3 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Monorepo vs Multi-repo** | Monorepo | Simpler deployment, shared types, single build |
| **Backend Framework** | Next.js API Routes (primary) | Simpler stack, single language, excellent TypeScript support |
| **Database** | PostgreSQL | ACID compliance, rich features, production-ready |
| **ORM** | Prisma | Type-safe, great DX, automatic migrations |
| **Authentication** | NextAuth.js | Battle-tested, CSRF protection, flexible |
| **State Management** | React Context + hooks | Sufficient for scope, less boilerplate |
| **Styling** | Tailwind CSS | Rapid development, consistent design, small bundle |
| **Testing** | Jest + Playwright + Vitest | Comprehensive coverage, industry standard |
| **Deployment** | Docker + Docker Compose | Deterministic, production-like, portable |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
+------------------------------------------------------------------+
|                          Web Browser                              |
|  (React Components, Client-Side State, UI Interactions)          |
+------------------------------------------------------------------+
                               |
                               | HTTPS
                               v
+------------------------------------------------------------------+
|                      Next.js Application                          |
|                                                                   |
|  +----------------------------+  +---------------------------+   |
|  |   Presentation Layer       |  |    API Layer              |   |
|  |  (React Server Components, |  |  (Next.js API Routes)     |   |
|  |   Client Components,       |  |                           |   |
|  |   Pages, Layouts)          |  |  - Authentication         |   |
|  |                            |  |  - Todos CRUD             |   |
|  |  - Todo List View          |  |  - Categories CRUD        |   |
|  |  - Todo Form               |  |  - Tags CRUD              |   |
|  |  - Category Manager        |  |                           |   |
|  |  - Login/Register          |  |  Business Logic:          |   |
|  +----------------------------+  |  - Validation             |   |
|                                  |  - Authorization          |   |
|                                  |  - Data transformation    |   |
|                                  +---------------------------+   |
|                                               |                  |
+-----------------------------------------------|------------------+
                                                |
                                                v
                                  +---------------------------+
                                  |   Data Access Layer       |
                                  |   (Prisma ORM)            |
                                  |                           |
                                  |  - User Repository        |
                                  |  - Todo Repository        |
                                  |  - Category Repository    |
                                  |  - Tag Repository         |
                                  +---------------------------+
                                                |
                                                v
                                  +---------------------------+
                                  |   PostgreSQL Database     |
                                  |                           |
                                  |  Tables:                  |
                                  |  - users                  |
                                  |  - todos                  |
                                  |  - categories             |
                                  |  - tags                   |
                                  |  - todo_tags              |
                                  +---------------------------+
```

### 2.2 Component Breakdown

**Presentation Layer (Frontend)**:
- Responsibilities: UI rendering, user interactions, client-side validation
- Technologies: React 18+, Next.js 14 App Router, Tailwind CSS
- Communication: Calls API layer via fetch

**API Layer (Backend)**:
- Responsibilities: Business logic, validation, authorization, data transformation
- Technologies: Next.js API Routes, TypeScript
- Communication: Uses Prisma ORM to access data

**Data Access Layer**:
- Responsibilities: Database queries, data mapping, transaction management
- Technologies: Prisma ORM
- Communication: SQL queries to PostgreSQL

**Database Layer**:
- Responsibilities: Data persistence, integrity, querying
- Technologies: PostgreSQL 14+
- Communication: SQL protocol

---

## 3. Frontend Architecture

### 3.1 Next.js App Router Structure

```
app/
├── (auth)/                          # Auth route group
│   ├── login/
│   │   └── page.tsx                 # Login page
│   └── register/
│       └── page.tsx                 # Register page
│
├── (dashboard)/                     # Protected route group
│   ├── todos/
│   │   ├── page.tsx                 # Todo list page
│   │   └── [id]/
│   │       └── page.tsx             # Todo detail/edit page
│   ├── categories/
│   │   └── page.tsx                 # Category management page
│   └── layout.tsx                   # Dashboard layout (with auth check)
│
├── api/                             # API routes
│   ├── auth/
│   │   └── [...nextauth]/
│   │       └── route.ts             # NextAuth.js handler
│   ├── todos/
│   │   ├── route.ts                 # GET /api/todos, POST /api/todos
│   │   └── [id]/
│   │       ├── route.ts             # GET, PUT, DELETE /api/todos/:id
│   │       └── complete/
│   │           └── route.ts         # PATCH /api/todos/:id/complete
│   ├── categories/
│   │   ├── route.ts                 # GET, POST /api/categories
│   │   └── [id]/
│   │       └── route.ts             # PUT, DELETE /api/categories/:id
│   └── tags/
│       ├── route.ts                 # GET, POST /api/tags
│       └── [id]/
│           └── route.ts             # DELETE /api/tags/:id
│
├── layout.tsx                       # Root layout
└── page.tsx                         # Home page (redirect to /todos)
```

### 3.2 Component Hierarchy

```
RootLayout
├── AuthLayout (for login/register)
│   ├── LoginPage
│   │   └── LoginForm
│   └── RegisterPage
│       └── RegisterForm
│
└── DashboardLayout (protected, with nav)
    ├── TodosPage
    │   ├── TodoFilters
    │   │   ├── CategoryFilter
    │   │   ├── TagFilter
    │   │   └── StatusFilter
    │   ├── TodoList
    │   │   └── TodoItem
    │   │       ├── TodoCheckbox
    │   │       ├── TodoTitle
    │   │       ├── TodoMeta (due date, priority, category, tags)
    │   │       └── TodoActions (edit, delete)
    │   └── CreateTodoButton
    │       └── TodoForm (modal)
    │
    └── CategoriesPage
        ├── CategoryList
        │   └── CategoryItem
        └── CreateCategoryButton
            └── CategoryForm (modal)
```

### 3.3 State Management

**Global State (React Context):**
- Auth state (user session)
- Theme preferences (future)

**Server State (React Query or SWR):**
- Todos data
- Categories data
- Tags data
- Optimistic updates
- Cache invalidation

**Local State (useState):**
- Form inputs
- Modal visibility
- Filter selections
- UI interactions

**URL State:**
- Active filters
- Sort order
- Search query

### 3.4 Data Flow

```
User Action
    |
    v
Event Handler (onClick, onSubmit)
    |
    v
API Call (fetch /api/todos)
    |
    v
Optimistic Update (update UI immediately)
    |
    v
API Response
    |
    +---> Success: Confirm optimistic update, revalidate cache
    |
    +---> Error: Rollback optimistic update, show error message
```

---

## 4. Backend Architecture

### 4.1 API Design

**RESTful Endpoints:**

```
Authentication:
POST   /api/auth/register      - Register new user
POST   /api/auth/login         - Login (handled by NextAuth)
POST   /api/auth/logout        - Logout
GET    /api/auth/session       - Get current session

Todos:
GET    /api/todos              - List todos (with query params for filtering)
POST   /api/todos              - Create todo
GET    /api/todos/:id          - Get single todo
PUT    /api/todos/:id          - Update todo
DELETE /api/todos/:id          - Delete todo (soft delete)
PATCH  /api/todos/:id/complete - Toggle completion status

Categories:
GET    /api/categories         - List categories
POST   /api/categories         - Create category
PUT    /api/categories/:id     - Update category
DELETE /api/categories/:id     - Delete category

Tags:
GET    /api/tags               - List user's tags
POST   /api/tags               - Create tag
DELETE /api/tags/:id           - Delete tag
```

**Query Parameters:**

```
GET /api/todos?status=active&category=work&tag=urgent&sort=due_date&order=asc
```

**Request/Response Format:**

```typescript
// Create Todo Request
POST /api/todos
{
  "title": "Team meeting",
  "description": "Discuss Q4 goals",
  "dueDate": "2025-11-01",
  "priority": "high",
  "categoryId": "uuid",
  "tagIds": ["uuid1", "uuid2"]
}

// Response
{
  "data": {
    "id": "uuid",
    "title": "Team meeting",
    "description": "Discuss Q4 goals",
    "dueDate": "2025-11-01",
    "priority": "high",
    "categoryId": "uuid",
    "category": {
      "id": "uuid",
      "name": "Work",
      "color": "#3b82f6"
    },
    "tags": [
      { "id": "uuid1", "name": "urgent" },
      { "id": "uuid2", "name": "meeting" }
    ],
    "isCompleted": false,
    "createdAt": "2025-10-27T12:00:00Z",
    "updatedAt": "2025-10-27T12:00:00Z"
  }
}

// Error Response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required",
    "details": {
      "field": "title",
      "constraint": "required"
    }
  }
}
```

### 4.2 Business Logic Layer

**Service Pattern:**

```typescript
// services/todo.service.ts

export class TodoService {
  constructor(private prisma: PrismaClient) {}

  async createTodo(userId: string, data: CreateTodoDto): Promise<Todo> {
    // Validate input
    this.validateTodoData(data);

    // Check category belongs to user
    if (data.categoryId) {
      await this.verifyCategoryOwnership(userId, data.categoryId);
    }

    // Create todo with tags
    const todo = await this.prisma.todo.create({
      data: {
        ...data,
        userId,
        tags: {
          connect: data.tagIds?.map(id => ({ id }))
        }
      },
      include: {
        category: true,
        tags: true
      }
    });

    return todo;
  }

  async listTodos(userId: string, filters: TodoFilters): Promise<Todo[]> {
    const where = this.buildWhereClause(userId, filters);
    const orderBy = this.buildOrderByClause(filters.sort, filters.order);

    return this.prisma.todo.findMany({
      where,
      orderBy,
      include: {
        category: true,
        tags: true
      }
    });
  }

  // ... more methods
}
```

**Validation:**

```typescript
// lib/validation.ts
import { z } from 'zod';

export const CreateTodoSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(1000).optional(),
  dueDate: z.string().datetime().optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  categoryId: z.string().uuid().optional(),
  tagIds: z.array(z.string().uuid()).optional()
});

export type CreateTodoDto = z.infer<typeof CreateTodoSchema>;
```

**Authorization:**

```typescript
// lib/authorization.ts

export async function requireAuth(request: Request): Promise<User> {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    throw new UnauthorizedError('Authentication required');
  }

  return session.user;
}

export async function requireTodoOwnership(
  todoId: string,
  userId: string
): Promise<void> {
  const todo = await prisma.todo.findUnique({
    where: { id: todoId },
    select: { userId: true }
  });

  if (!todo || todo.userId !== userId) {
    throw new ForbiddenError('Access denied');
  }
}
```

### 4.3 Error Handling

**Error Hierarchy:**

```typescript
// lib/errors.ts

export class AppError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: any) {
    super('VALIDATION_ERROR', message, 400, details);
  }
}

export class UnauthorizedError extends AppError {
  constructor(message: string = 'Authentication required') {
    super('UNAUTHORIZED', message, 401);
  }
}

export class ForbiddenError extends AppError {
  constructor(message: string = 'Access denied') {
    super('FORBIDDEN', message, 403);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super('NOT_FOUND', `${resource} not found`, 404);
  }
}
```

**Global Error Handler:**

```typescript
// lib/error-handler.ts

export function handleApiError(error: unknown): Response {
  // Log error
  logger.error('API Error:', error);

  // Known app error
  if (error instanceof AppError) {
    return NextResponse.json(
      {
        error: {
          code: error.code,
          message: error.message,
          details: error.details
        }
      },
      { status: error.statusCode }
    );
  }

  // Prisma errors
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    return handlePrismaError(error);
  }

  // Unknown error
  return NextResponse.json(
    {
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An unexpected error occurred'
      }
    },
    { status: 500 }
  );
}
```

---

## 5. Database Architecture

### 5.1 Schema Design

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Categories table
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL,
  is_custom BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE UNIQUE INDEX idx_categories_user_name ON categories(user_id, name);

-- Tags table
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE UNIQUE INDEX idx_tags_user_name ON tags(user_id, name);

-- Todos table
CREATE TABLE todos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  due_date DATE,
  priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
  category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  is_completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  is_deleted BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_todos_user_id ON todos(user_id);
CREATE INDEX idx_todos_category_id ON todos(category_id);
CREATE INDEX idx_todos_due_date ON todos(due_date);
CREATE INDEX idx_todos_is_completed ON todos(is_completed);
CREATE INDEX idx_todos_is_deleted ON todos(is_deleted);

-- TodoTags junction table
CREATE TABLE todo_tags (
  todo_id UUID NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (todo_id, tag_id)
);

CREATE INDEX idx_todo_tags_todo_id ON todo_tags(todo_id);
CREATE INDEX idx_todo_tags_tag_id ON todo_tags(tag_id);
```

### 5.2 Prisma Schema

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id           String      @id @default(uuid())
  email        String      @unique
  passwordHash String      @map("password_hash")
  createdAt    DateTime    @default(now()) @map("created_at")
  updatedAt    DateTime    @updatedAt @map("updated_at")

  todos        Todo[]
  categories   Category[]
  tags         Tag[]

  @@map("users")
}

model Category {
  id        String   @id @default(uuid())
  userId    String   @map("user_id")
  name      String
  color     String
  isCustom  Boolean  @default(true) @map("is_custom")
  createdAt DateTime @default(now()) @map("created_at")

  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  todos     Todo[]

  @@unique([userId, name])
  @@index([userId])
  @@map("categories")
}

model Tag {
  id        String   @id @default(uuid())
  userId    String   @map("user_id")
  name      String
  createdAt DateTime @default(now()) @map("created_at")

  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  todos     Todo[]   @relation("TodoTags")

  @@unique([userId, name])
  @@index([userId])
  @@map("tags")
}

model Todo {
  id          String    @id @default(uuid())
  userId      String    @map("user_id")
  title       String
  description String?
  dueDate     DateTime? @map("due_date") @db.Date
  priority    Priority  @default(MEDIUM)
  categoryId  String?   @map("category_id")
  isCompleted Boolean   @default(false) @map("is_completed")
  completedAt DateTime? @map("completed_at")
  isDeleted   Boolean   @default(false) @map("is_deleted")
  createdAt   DateTime  @default(now()) @map("created_at")
  updatedAt   DateTime  @updatedAt @map("updated_at")

  user        User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  category    Category? @relation(fields: [categoryId], references: [id], onDelete: SetNull)
  tags        Tag[]     @relation("TodoTags")

  @@index([userId])
  @@index([categoryId])
  @@index([dueDate])
  @@index([isCompleted])
  @@index([isDeleted])
  @@map("todos")
}

enum Priority {
  LOW
  MEDIUM
  HIGH

  @@map("priority")
}
```

### 5.3 Indexes Strategy

**Primary Indexes:**
- All `id` columns (automatic via PRIMARY KEY)
- `users.email` (UNIQUE for login lookups)

**Foreign Key Indexes:**
- `categories.user_id` - Common filter: "user's categories"
- `tags.user_id` - Common filter: "user's tags"
- `todos.user_id` - Common filter: "user's todos"
- `todos.category_id` - Common join: todos with categories

**Query Optimization Indexes:**
- `todos.due_date` - Sorting by due date (common)
- `todos.is_completed` - Filtering active vs completed
- `todos.is_deleted` - Filtering soft-deleted items
- `todo_tags.todo_id` - Join performance
- `todo_tags.tag_id` - Reverse join performance

**Composite Indexes (if needed):**
- `(user_id, is_deleted, is_completed, due_date)` - Optimal for main query

### 5.4 Migration Strategy

**Development:**
```bash
# Create migration
npx prisma migrate dev --name add_categories_table

# Apply migrations
npx prisma migrate dev

# Reset database (dev only)
npx prisma migrate reset
```

**Production:**
```bash
# Deploy migrations
npx prisma migrate deploy

# Generate Prisma Client
npx prisma generate
```

---

## 6. Security Architecture

### 6.1 Authentication Flow

```
User Register:
1. User submits email + password
2. Server validates input (email format, password strength)
3. Check email not already registered
4. Hash password (bcrypt, cost 10)
5. Create user in database
6. Create session (NextAuth)
7. Return session token

User Login:
1. User submits email + password
2. Server finds user by email
3. Compare password hash (bcrypt.compare)
4. If valid, create session (NextAuth)
5. Return session token
6. Set HTTP-only cookie

Authenticated Request:
1. Client sends request with session cookie
2. Server validates session (NextAuth middleware)
3. Extract user from session
4. Attach user to request context
5. Process request
```

### 6.2 Authorization Model

**Role-Based Access Control (RBAC):**
- Currently single role: "user"
- Future: "admin" for user management

**Resource-Based Authorization:**
```typescript
// Every resource check
async function requireTodoAccess(todoId: string, userId: string) {
  const todo = await prisma.todo.findUnique({
    where: { id: todoId },
    select: { userId: true }
  });

  if (!todo) {
    throw new NotFoundError('Todo');
  }

  if (todo.userId !== userId) {
    throw new ForbiddenError('You do not own this todo');
  }
}
```

**Authorization Rules:**
- Users can only access their own resources
- No cross-user data leakage
- API routes always check session
- Database queries always filter by user_id

### 6.3 Data Protection

**Passwords:**
- Hashed with bcrypt (cost 10 minimum)
- Never logged or returned in responses
- Reset requires email verification (future P2)

**Sessions:**
- HTTP-only cookies (no JavaScript access)
- Secure flag in production (HTTPS only)
- SameSite=Lax (CSRF protection)
- 24-hour expiry (or 30 days with "remember me")

**API Tokens (Future):**
- JWT for API access
- Short-lived (1 hour)
- Refresh token rotation

**Database:**
- Connection string in environment variables
- SSL/TLS for production connections
- Prepared statements (Prisma prevents SQL injection)

### 6.4 OWASP Top 10 Protections

**A01: Broken Access Control**
- All API routes check authentication
- Resource ownership verified before access
- No direct object references without authorization

**A02: Cryptographic Failures**
- Passwords hashed with bcrypt
- HTTPS in production
- Sensitive data not logged

**A03: Injection**
- Prisma ORM (parameterized queries)
- Input validation with Zod
- No raw SQL queries

**A04: Insecure Design**
- Security requirements defined upfront
- Threat modeling performed
- Principle of least privilege

**A05: Security Misconfiguration**
- Environment-based configuration
- No default credentials
- Security headers set

**A06: Vulnerable Components**
- Dependencies audited (npm audit)
- Regular updates
- Minimal dependencies

**A07: Authentication Failures**
- Strong password requirements
- Account lockout (future)
- Secure session management

**A08: Software and Data Integrity**
- Code review required
- Automated tests
- No untrusted code execution

**A09: Logging Failures**
- All errors logged
- Security events tracked
- No sensitive data in logs

**A10: Server-Side Request Forgery**
- No external URL fetching (currently)
- URL validation if added (future)

### 6.5 Security Headers

```typescript
// middleware.ts

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=()'
  );

  // CSP (Content Security Policy)
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
  );

  return response;
}
```

---

## 7. Deployment Architecture

### 7.1 Development Environment

**Local Setup:**
```bash
# Clone repository
git clone <repo-url>
cd todo-app

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env.local
# Edit .env.local with local database URL

# Start database
docker-compose up -d postgres

# Run migrations
npx prisma migrate dev

# Seed default categories (optional)
npx prisma db seed

# Start development server
npm run dev

# Open browser
# http://localhost:3000
```

**Environment Variables (.env.local):**
```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/todo_app"
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-key-change-in-production"
```

### 7.2 Production Environment

**Docker Deployment:**

```yaml
# docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: todo_app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/todo_app
      NEXTAUTH_URL: ${NEXTAUTH_URL}
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}
      NODE_ENV: production
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app_network

volumes:
  postgres_data:

networks:
  app_network:
```

**Dockerfile:**
```dockerfile
FROM node:18-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate Prisma Client
RUN npx prisma generate

# Build Next.js
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma

USER nextjs

EXPOSE 3000

ENV PORT 3000

# Run migrations on startup, then start app
CMD npx prisma migrate deploy && node server.js
```

### 7.3 CI/CD Pipeline

**GitHub Actions (.github/workflows/deploy.yml):**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test
      - run: npm run test:e2e

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t todo-app .
      - run: docker push todo-app:latest
      # Deploy to your hosting platform
```

### 7.4 Infrastructure

**Option 1: Vercel (Recommended for simplicity)**
- Deploy Next.js app to Vercel
- Use Vercel Postgres or external PostgreSQL
- Automatic HTTPS, CDN, deployments

**Option 2: Docker on VPS**
- Deploy Docker Compose to DigitalOcean, AWS, etc.
- Setup reverse proxy (Nginx)
- Configure SSL with Let's Encrypt

**Option 3: Kubernetes (Overkill for benchmark)**
- Not recommended for this scope

---

## 8. Performance & Scalability

### 8.1 Performance Optimization

**Frontend Optimizations:**
- Code splitting (route-based, automatic with Next.js)
- Image optimization (next/image)
- Font optimization (next/font)
- Lazy loading (React.lazy for heavy components)
- Debounced search (300ms)
- Virtualized lists (if >100 todos)

**Backend Optimizations:**
- Database query optimization
  - Proper indexes on common queries
  - Only select needed fields
  - Use include/select strategically
- Prisma query optimization
  - Batch queries where possible
  - Avoid N+1 queries
- API response compression (gzip)

**Database Optimizations:**
- Connection pooling (Prisma default)
- Prepared statements (Prisma default)
- Indexes on foreign keys and common filters
- EXPLAIN ANALYZE for slow queries

**Caching Strategy:**
- Server-side: Cache user's categories/tags (rarely change)
- Client-side: React Query/SWR for data caching
- Static: Pre-render landing page (ISR)

### 8.2 Performance Targets

**Page Load:**
- First Contentful Paint (FCP): <1.5s
- Largest Contentful Paint (LCP): <2.5s
- Time to Interactive (TTI): <3s
- Lighthouse Performance Score: >90

**API Response Times:**
- p50: <100ms
- p95: <200ms
- p99: <500ms

**Database Queries:**
- Simple queries: <10ms
- Complex joins: <50ms
- Full-text search: <100ms

### 8.3 Scalability Considerations

**Current Scale (Benchmark):**
- 100 concurrent users
- 10,000 todos per user
- 1000 total users

**Scaling Strategies:**

**Horizontal Scaling:**
- Stateless app servers (can add more containers)
- Session in database or Redis (not in-memory)
- Load balancer in front of app servers

**Database Scaling:**
- Read replicas for read-heavy queries
- Connection pooling (PgBouncer)
- Partitioning by user_id (if needed)

**Caching:**
- Redis for session storage
- Redis for frequently accessed data
- CDN for static assets

**Monitoring:**
- Application metrics (response times, error rates)
- Database metrics (query times, connection pool)
- Infrastructure metrics (CPU, memory, disk)
- Logging (structured logs with context)

---

## 9. Code Organization

### 9.1 Directory Structure

```
todo-app/
├── app/                                    # Next.js app directory
│   ├── (auth)/                             # Auth pages
│   ├── (dashboard)/                        # Protected pages
│   ├── api/                                # API routes
│   ├── layout.tsx                          # Root layout
│   └── page.tsx                            # Home page
│
├── components/                             # React components
│   ├── ui/                                 # UI primitives (Button, Input, etc.)
│   ├── todos/                              # Todo-specific components
│   │   ├── TodoList.tsx
│   │   ├── TodoItem.tsx
│   │   ├── TodoForm.tsx
│   │   └── TodoFilters.tsx
│   ├── categories/                         # Category components
│   └── shared/                             # Shared components (Header, Footer)
│
├── lib/                                    # Shared utilities
│   ├── prisma.ts                           # Prisma client singleton
│   ├── auth.ts                             # NextAuth configuration
│   ├── validation.ts                       # Zod schemas
│   ├── errors.ts                           # Error classes
│   └── utils.ts                            # General utilities
│
├── services/                               # Business logic
│   ├── todo.service.ts
│   ├── category.service.ts
│   ├── tag.service.ts
│   └── user.service.ts
│
├── types/                                  # TypeScript types
│   ├── api.ts                              # API types
│   ├── models.ts                           # Data model types
│   └── index.ts                            # Barrel exports
│
├── prisma/                                 # Database
│   ├── schema.prisma                       # Prisma schema
│   ├── migrations/                         # Migration history
│   └── seed.ts                             # Seed data
│
├── public/                                 # Static assets
│   ├── images/
│   └── favicon.ico
│
├── tests/                                  # Tests
│   ├── unit/                               # Unit tests
│   ├── integration/                        # Integration tests
│   └── e2e/                                # End-to-end tests
│
├── .env.example                            # Environment variables template
├── .eslintrc.json                          # ESLint config
├── .prettierrc                             # Prettier config
├── docker-compose.yml                      # Docker Compose config
├── Dockerfile                              # Docker image
├── next.config.js                          # Next.js config
├── package.json                            # Dependencies
├── tailwind.config.ts                      # Tailwind config
├── tsconfig.json                           # TypeScript config
└── README.md                               # Project README
```

### 9.2 Naming Conventions

**Files:**
- React components: PascalCase (TodoList.tsx)
- Utilities: kebab-case (auth-utils.ts)
- API routes: route.ts (Next.js convention)
- Types: kebab-case (api-types.ts)

**Code:**
- Components: PascalCase (TodoList)
- Functions: camelCase (createTodo)
- Constants: UPPER_SNAKE_CASE (MAX_TITLE_LENGTH)
- Interfaces: PascalCase with I prefix (ITodoService) or without (TodoService)
- Types: PascalCase (CreateTodoDto)

**Database:**
- Tables: snake_case plural (todos, categories)
- Columns: snake_case (user_id, created_at)
- Indexes: idx_table_column (idx_todos_user_id)

### 9.3 Module Boundaries

**Presentation Layer (components/):**
- No direct database access
- No business logic
- Calls API via fetch
- Displays data, handles user input

**API Layer (app/api/):**
- Validates input
- Checks authorization
- Calls service layer
- Returns JSON responses

**Service Layer (services/):**
- Contains business logic
- Uses repositories for data access
- Throws domain-specific errors
- Independent of HTTP/API concerns

**Data Layer (Prisma):**
- Database queries
- Data mapping
- Transaction management
- No business logic

---

## 10. Quality Attributes

### 10.1 Testability

**Unit Tests:**
- All services fully testable
- Pure functions easy to test
- Dependency injection for mocks

**Integration Tests:**
- API routes with test database
- Prisma with in-memory or test DB
- Isolated test data per test

**E2E Tests:**
- Full user flows
- Real browser (Playwright)
- Test database per run

**Test Structure:**
```
tests/
├── unit/
│   ├── services/
│   │   └── todo.service.test.ts
│   └── lib/
│       └── validation.test.ts
├── integration/
│   └── api/
│       ├── todos.test.ts
│       └── auth.test.ts
└── e2e/
    ├── auth.spec.ts
    ├── todos.spec.ts
    └── categories.spec.ts
```

### 10.2 Maintainability

**Code Quality:**
- Linting (ESLint)
- Formatting (Prettier)
- Type checking (TypeScript strict mode)
- Code review (PR required)

**Documentation:**
- README with setup instructions
- API documentation (Swagger)
- Inline comments for complex logic
- Architecture decision records (ADRs)

**Modularity:**
- Clear separation of concerns
- Small, focused functions
- Reusable components
- DRY principle

### 10.3 Accessibility

**Standards:**
- WCAG 2.1 AA compliance
- Semantic HTML
- ARIA attributes where needed
- Keyboard navigation

**Implementation:**
- Focus management (modals, forms)
- Screen reader announcements (live regions)
- Color contrast (4.5:1 minimum)
- Skip links for navigation

**Testing:**
- Automated: axe-core via Playwright
- Manual: Keyboard-only testing
- Screen reader: NVDA/JAWS testing

### 10.4 Reliability

**Error Handling:**
- All errors caught and logged
- User-friendly error messages
- Graceful degradation
- Retry logic for transient failures

**Data Integrity:**
- Database constraints (foreign keys, NOT NULL)
- Application-level validation
- Transaction management
- Soft deletes (no data loss)

**Monitoring:**
- Error tracking (Sentry or similar)
- Performance monitoring (Vercel Analytics)
- Uptime monitoring
- Database health checks

---

## 11. Technology Alternatives

### 11.1 Backend: FastAPI Alternative

**If using FastAPI instead of Next.js API routes:**

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, get_db

app = FastAPI()

@app.post("/api/todos", response_model=schemas.Todo)
def create_todo(
    todo: schemas.TodoCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_todo(db=db, todo=todo, user_id=current_user.id)

@app.get("/api/todos", response_model=list[schemas.Todo])
def list_todos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_todos(db=db, user_id=current_user.id, skip=skip, limit=limit)
```

**Trade-offs:**
- (+) FastAPI is very fast
- (+) Great OpenAPI docs auto-generation
- (+) Python may be more familiar
- (-) Two languages (Python + TypeScript)
- (-) Separate deployment needed
- (-) More complex architecture

**Recommendation:** Use Next.js API routes for simplicity and single language.

### 11.2 State Management: Zustand/Redux

**If app state becomes complex:**

```typescript
// store/todos.ts
import create from 'zustand';

interface TodoStore {
  todos: Todo[];
  filters: TodoFilters;
  setTodos: (todos: Todo[]) => void;
  addTodo: (todo: Todo) => void;
  updateTodo: (id: string, updates: Partial<Todo>) => void;
  deleteTodo: (id: string) => void;
  setFilters: (filters: TodoFilters) => void;
}

export const useTodoStore = create<TodoStore>((set) => ({
  todos: [],
  filters: {},
  setTodos: (todos) => set({ todos }),
  addTodo: (todo) => set((state) => ({ todos: [...state.todos, todo] })),
  updateTodo: (id, updates) =>
    set((state) => ({
      todos: state.todos.map((t) => (t.id === id ? { ...t, ...updates } : t))
    })),
  deleteTodo: (id) =>
    set((state) => ({ todos: state.todos.filter((t) => t.id !== id) })),
  setFilters: (filters) => set({ filters })
}));
```

**Recommendation:** Start with React Context, upgrade to Zustand only if needed.

---

## 12. Conclusion

This architecture provides a solid foundation for building a production-quality todo application that serves as a benchmark for GAO-Dev's autonomous capabilities. It balances:

- **Simplicity**: Straightforward patterns, minimal dependencies
- **Quality**: Clean code, comprehensive tests, accessibility
- **Performance**: Fast page loads, optimized queries
- **Security**: OWASP compliance, defense in depth
- **Maintainability**: Clear structure, good documentation
- **Scalability**: Can handle growth if needed

The architecture is designed to be implementable by autonomous agents following the specifications in this document and the PRD.

---

**Reviewed by:**
- [ ] Winston (Architect) - Architecture approved
- [ ] Amelia (Developer) - Implementable
- [ ] Murat (QA) - Testable
- [ ] John (PM) - Aligns with PRD

**Status**: Ready for implementation

---

*This architecture document serves as the technical blueprint for the reference todo application used in GAO-Dev benchmarking.*
