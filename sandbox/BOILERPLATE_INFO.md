# Boilerplate Repository Information

## Frontend: Simple Next.js Starter

**Repository**: https://github.com/webventurer/simple-nextjs-starter
**Branch**: main (assumed)
**Type**: Frontend only (Next.js 15)

---

## Technology Stack

### Core
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript (strict mode)
- **Package Manager**: pnpm
- **Dev Server**: Turbopack

### Styling
- **CSS Framework**: SCSS with CSS Modules
- **Theming**: CSS Custom Properties
- **Font Loading**: next/font optimization

### Content
- **MDX Support**: Markdown with React components
- **GitHub Flavored Markdown**: Task lists, tables, strikethrough

### Code Quality
- **Linter/Formatter**: Biome (replaces ESLint + Prettier)
- **Type Checking**: TypeScript strict mode
- **Pre-commit Hooks**: Automatic TypeScript validation

---

## Directory Structure

```
simple-nextjs-starter/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── page.module.scss
│   ├── components/           # Reusable semantic components
│   ├── lib/
│   │   └── utils.ts
│   └── styles/
│       ├── layout.css
│       └── typography.css
├── content/                  # Markdown/MDX content
├── docs/                     # Documentation
├── public/                   # Static assets
├── tools/remark/             # Custom Remark plugins
├── package.json
├── tsconfig.json
├── biome.json                # Biome config
└── README.md
```

---

## Setup & Installation

### Clone & Install
```bash
git clone https://github.com/webventurer/simple-nextjs-starter <project-name>
cd <project-name>
pnpm install
pnpm dev
```

### Available Scripts
- `pnpm dev` - Development server (Turbopack)
- `pnpm build` - Production build
- `pnpm lint` - Run Biome linter
- `pnpm format` - Format code with Biome
- `pnpm type:check` - TypeScript validation
- `pre-commit install` - Setup git hooks

---

## Template Variables

### Identified Placeholders
- `<repository-url>` - Git repository URL
- `your-username` - GitHub username
- Project name (in package.json)

### Substitution Map
```yaml
substitutions:
  repository_url: "{{GIT_REPO_URL}}"
  username: "{{GITHUB_USERNAME}}"
  project_name: "{{PROJECT_NAME}}"
  project_description: "{{PROJECT_DESCRIPTION}}"
  author: "{{AUTHOR}}"
```

### Files Requiring Substitution
- `package.json` - name, description, author, repository
- `README.md` - clone URLs, usernames
- `src/app/layout.tsx` - metadata (title, description)

---

## Integration Notes

### What's Included
✅ Frontend framework (Next.js 15)
✅ TypeScript configuration
✅ Styling system (SCSS)
✅ Content system (MDX)
✅ Code quality tools (Biome)
✅ Development tooling

### What's Missing (Need to Add for Todo App)
❌ Backend API (need FastAPI or Express)
❌ Database integration
❌ Authentication system
❌ API client/fetching layer
❌ State management (if needed)
❌ Testing framework
❌ Docker configuration
❌ Environment variable management

---

## Backend Options

Since the boilerplate only provides frontend, we need to add backend separately.

### Option 1: FastAPI (Python)
**Pros:**
- Aligns with GAO-Dev being Python
- Excellent API documentation (auto-generated OpenAPI)
- Fast, modern, async support
- Great for ML/AI integration later

**Cons:**
- Different language from frontend
- Need CORS configuration
- Deployment more complex (two runtimes)

**Structure:**
```
project/
├── frontend/          # Next.js starter
└── backend/           # FastAPI
    ├── app/
    │   ├── main.py
    │   ├── routers/
    │   ├── models/
    │   └── db/
    ├── requirements.txt
    └── Dockerfile
```

### Option 2: Next.js API Routes (Node.js)
**Pros:**
- Single language (TypeScript)
- Integrated with Next.js (same deployment)
- Simpler setup
- Better for serverless

**Cons:**
- Less structured than FastAPI
- Not as robust for complex APIs
- No auto-generated docs

**Structure:**
```
project/
└── frontend/          # Next.js starter + API routes
    ├── src/app/api/   # API routes
    │   ├── auth/
    │   └── todos/
    └── lib/db/        # Database layer
```

### Option 3: Express (Node.js)
**Pros:**
- Mature ecosystem
- Same language as frontend
- Flexible, well-documented

**Cons:**
- More boilerplate than FastAPI
- Not as modern as FastAPI
- Manual API documentation

**Structure:**
```
project/
├── frontend/          # Next.js starter
└── backend/           # Express
    ├── src/
    │   ├── index.ts
    │   ├── routes/
    │   ├── models/
    │   └── db/
    ├── package.json
    └── Dockerfile
```

---

## Recommended Approach

### Phase 1: Use Next.js API Routes
**Why:**
- Fastest to implement
- Single codebase
- Good for MVP/prototype
- Easy deployment (Vercel)

**Implementation:**
```
project/
└── frontend/                    # Clone of simple-nextjs-starter
    ├── src/
    │   ├── app/
    │   │   ├── api/             # API routes (NEW)
    │   │   │   ├── auth/
    │   │   │   │   ├── register/route.ts
    │   │   │   │   └── login/route.ts
    │   │   │   └── todos/
    │   │   │       ├── route.ts
    │   │   │       └── [id]/route.ts
    │   │   └── ...
    │   ├── components/
    │   └── lib/
    │       ├── db/              # Database client (NEW)
    │       ├── auth/            # Auth utilities (NEW)
    │       └── utils.ts
    ├── prisma/                  # Database schema (NEW)
    │   └── schema.prisma
    └── ...
```

### Phase 2: Migrate to FastAPI (If Needed)
Once we validate the full workflow, we can migrate to separate backend for:
- Better API documentation
- More robust architecture
- Scalability

---

## Database Options

### SQLite (Development)
- ✅ No setup required
- ✅ File-based, easy to reset
- ✅ Good for prototyping
- ❌ Not for production

### PostgreSQL (Production)
- ✅ Production-ready
- ✅ Full SQL features
- ✅ Docker-friendly
- ❌ Requires setup

### Recommendation: Prisma ORM
- Works with both SQLite and PostgreSQL
- Type-safe database client
- Auto-generated types
- Migration system
- Good DX

---

## Next Steps

1. **Clone Boilerplate**: Clone simple-nextjs-starter into sandbox
2. **Add Backend Layer**: Add Next.js API routes for todo app
3. **Add Database**: Integrate Prisma with PostgreSQL
4. **Add Authentication**: Implement JWT-based auth
5. **Add Testing**: Add Jest + React Testing Library
6. **Add Docker**: Create docker-compose.yml

---

*This document will be used by the boilerplate integration system to properly configure new projects.*
