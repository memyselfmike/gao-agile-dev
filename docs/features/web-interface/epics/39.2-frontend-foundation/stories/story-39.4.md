# Story 39.4: React + Vite + Zustand Setup

**Story Number**: 39.4
**Epic**: 39.2 - Frontend Foundation
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: S (Small - 2 points)
**Dependencies**: Story 39.1 (FastAPI server to serve frontend)

## User Story
As a **developer**, I want **modern React development environment with Vite and Zustand** so that **I can build fast, maintainable frontend components with efficient state management**.

## Acceptance Criteria
- [ ] AC1: Vite 5+ configured with React 18+ template
- [ ] AC2: TypeScript strict mode enabled (no `Any` types)
- [ ] AC3: Vite dev server starts in <2 seconds with HMR
- [ ] AC4: Production build completes in <30 seconds
- [ ] AC5: Build output optimized (<500KB initial bundle)
- [ ] AC6: Zustand store created for global state (chat, activity, files)
- [ ] AC7: Environment variables configured (.env.local for dev)
- [ ] AC8: ESLint + Prettier configured with GAO-Dev standards
- [ ] AC9: Path aliases configured (@/ for src/)
- [ ] AC10: WebSocket client utility created for /ws connection

## Technical Context
**Tech Stack**: React 18, Vite 5, Zustand, TypeScript 5, Tailwind CSS
**Integration**: FastAPI serves built frontend from /dist
**Store Structure**: Separate stores for chat, activity, kanban, files
