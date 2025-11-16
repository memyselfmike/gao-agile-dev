# GAO-Dev Web Interface - Frontend

Modern React frontend for the GAO-Dev autonomous AI development system.

## Tech Stack

- **React 19.2** - Latest React with concurrent features
- **Vite 7.2** - Next-generation frontend tooling
- **TypeScript 5.9** - Strict mode enabled, no `any` types
- **Zustand 5.0** - Lightweight state management
- **Tailwind CSS 4.1** - Utility-first CSS framework
- **React Router 7.9** - Client-side routing

## Features

- Fast dev server startup (<2 seconds with HMR)
- Production build optimization (<30 seconds, <500KB bundle)
- WebSocket client with auto-reconnect
- Global state management (chat, activity, files, session)
- TypeScript strict mode (no `any` types allowed)
- ESLint + Prettier configured
- Path aliases (@/ for src/)

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development

```bash
npm run dev
```

Dev server starts at `http://localhost:5173`

### Build

```bash
npm run build
```

Output in `dist/` directory, served by FastAPI backend.

### Lint

```bash
npm run lint
```

### Format

```bash
npm run format
```

## Project Structure

```
src/
├── stores/           # Zustand stores
│   ├── chatStore.ts       # Chat messages, active agent
│   ├── activityStore.ts   # Activity stream events
│   ├── filesStore.ts      # File tree, open files
│   └── sessionStore.ts    # Session lock, read-only mode
├── lib/              # Utilities
│   └── websocket.ts       # WebSocket client
├── types/            # TypeScript types
│   └── index.ts           # Shared type definitions
├── App.tsx           # Main application
├── main.tsx          # Entry point
└── index.css         # Global styles (Tailwind)
```

## State Management

### Zustand Stores

1. **chatStore** - Chat messages and active agent
2. **activityStore** - Activity stream events (max 100)
3. **filesStore** - File tree and open files
4. **sessionStore** - Session lock state and read-only mode

Usage:

```tsx
import { useChatStore } from '@/stores';

const messages = useChatStore((state) => state.messages);
const addMessage = useChatStore((state) => state.addMessage);
```

## WebSocket Client

Connect to GAO-Dev backend WebSocket:

```tsx
import { createWebSocketClient } from '@/lib/websocket';

const client = await createWebSocketClient(
  (message) => console.log('Received:', message),
  () => console.log('Connected'),
  () => console.log('Disconnected'),
  (error) => console.error('Error:', error)
);

client.send({ type: 'ping', payload: {} });
client.disconnect();
```

## Environment Variables

Create `.env.local`:

```env
VITE_API_URL=http://127.0.0.1:3000
VITE_WS_URL=ws://127.0.0.1:3000/ws
```

## Bundle Size

Production build (gzipped):
- Initial bundle: ~196KB JS + ~8.5KB CSS = **~205KB** ✅
- Vendor chunk: React, React DOM, React Router
- Zustand chunk: State management
- Build time: **<30 seconds** ✅

## Code Quality

- TypeScript strict mode enabled
- No `any` types allowed
- ESLint configured with React + TypeScript rules
- Prettier with Tailwind plugin for class sorting
- 100 character line length
- Single quotes, 2-space indent

## Performance

- Dev server starts in <2 seconds ✅
- Hot Module Replacement (HMR) enabled
- Production build <30 seconds ✅
- Lazy loading for routes (future)
- Code splitting (vendor, zustand)

## Future Enhancements (Story 39.5+)

- shadcn/ui components
- Chat interface
- Activity stream panel
- File explorer
- Kanban board
- Real-time collaboration

## License

Part of GAO-Dev - Autonomous AI Development System
