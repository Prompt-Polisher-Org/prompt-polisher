# Frontend Documentation

## Overview

The Prompt Polisher frontend is a **Next.js 14** application using the App Router, SCSS Modules, Framer Motion, GSAP, and Zustand for state management. It provides a modern, dark-themed AI interface with glassmorphism effects, smooth animations, and responsive design across mobile, tablet, and desktop.

---

## Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | 14.x | React framework with App Router |
| **TypeScript** | 5.x | Type safety |
| **SCSS Modules** | — | Component-scoped styling |
| **Framer Motion** | 11.x | Page transitions and declarative animations |
| **GSAP** | 3.x | Landing page and complex timeline animations |
| **Zustand** | 4.x | Lightweight state management (auth store) |
| **Axios** | 1.x | HTTP client with interceptors |
| **Chart.js / Recharts** | — | Analytics dashboard charts |
| **Google Fonts** | — | Inter (body) + JetBrains Mono (code) |

---

## Design System

### Color Palette

The design uses an **Obsidian/AI Dark Theme** by default with light mode support via CSS variable switching.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg-base` | `#0f111a` | Page background (deep navy) |
| `--color-bg-surface` | `#1a1d2d` | Card/panel backgrounds |
| `--color-bg-surface-elevated` | `#24283b` | Elevated surfaces (modals, dropdowns) |
| `--color-primary` | `#6366f1` | Primary actions, links (Indigo) |
| `--color-primary-hover` | `#818cf8` | Hover state for primary |
| `--color-success` | `#10b981` | Success states (Emerald) |
| `--color-accent` | `#f59e0b` | Warnings, highlights (Amber) |
| `--color-danger` | `#ef4444` | Errors, destructive actions (Red) |
| `--color-text-primary` | `#f8fafc` | Body text |
| `--color-text-secondary` | `#94a3b8` | Secondary text |
| `--color-text-muted` | `#64748b` | Muted/disabled text |

### Typography

| Token | Value |
|-------|-------|
| `--font-sans` | `Inter, sans-serif` |
| `--font-mono` | `JetBrains Mono, monospace` |

### Spacing (4px Grid)

`--space-1` (4px) through `--space-16` (64px) with a consistent 4px base unit.

### Border Radius

| Token | Value |
|-------|-------|
| `--radius-sm` | 4px |
| `--radius-md` | 8px |
| `--radius-lg` | 12px |
| `--radius-xl` | 16px |
| `--radius-full` | 9999px (pill) |

### Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--z-base` | 0 | Default stacking |
| `--z-elevated` | 10 | Cards, buttons |
| `--z-dropdown` | 50 | Menus |
| `--z-sticky` | 100 | Sticky headers |
| `--z-modal` | 1000 | Modals, overlays |
| `--z-toast` | 2000 | Toast notifications |

### SCSS Resources

| File | Purpose |
|------|---------|
| `src/styles/_variables.scss` | All CSS custom properties (design tokens) |
| `src/styles/_mixins.scss` | Responsive breakpoints, glassmorphism, gradients |
| `src/styles/_animations.scss` | Keyframe animations (fadeIn, slideUp, scale, shimmer) |

---

## Component Library

### UI Components (`src/components/ui/`)

| Component | File | Description |
|-----------|------|-------------|
| **Button** | `Button/` | Primary, secondary, ghost, and danger variants with hover effects and loading state |
| **Input** | `Input/` | Text, password, and textarea variants with validation states |
| **Card** | `Card/` | Standard and glassmorphism card with backdrop blur |
| **Spinner** | `Spinner/` | CSS-based loading spinner |
| **Skeleton** | `Skeleton.tsx` | Shimmer loading placeholders for content (not just spinners) |
| **ErrorBoundary** | `ErrorBoundary.tsx` | React error boundary with fallback UI |
| **PageTransition** | `PageTransition.tsx` | Framer Motion wrapper for page-level animations |
| **ThemeProvider** | `ThemeProvider.tsx` | Context provider for dark/light mode with CSS variable switching |
| **ThemeToggle** | `ThemeToggle.tsx` | Toggle button with smooth transition animation |
| **OfflineBanner** | `OfflineBanner.tsx` | Detects offline state and shows a banner, queues requests |
| **KeyboardShortcuts** | `KeyboardShortcuts.tsx` | Global keyboard shortcut system for navigation and actions |

### Chat Components (`src/components/chat/`)

| Component | File | Description |
|-----------|------|-------------|
| **ChatInterface** | `ChatInterface.tsx` | Main chat container — message list with auto-scroll, WebSocket integration, typing indicator |
| **ChatInput** | `ChatInput.tsx` | Auto-resizing textarea with send button, Ctrl+Enter shortcut, character count |
| **MessageBubble** | `MessageBubble.tsx` | Styled message bubble (user = right/primary, AI = left/secondary) with timestamps and typewriter effect |
| **FeedbackWidget** | `FeedbackWidget.tsx` | Thumbs up/down + optional comment, animated submit, "Thank you" confirmation |
| **PromptComparisonView** | `PromptComparisonView.tsx` | Side-by-side or inline diff view comparing raw vs optimized prompts, with syntax highlighting |
| **PromptTemplates** | `PromptTemplates.tsx` | Template cards for common use cases (coding, writing, marketing, etc.) — click to pre-fill input |
| **SessionSidebar** | `SessionSidebar.tsx` | List of past chat sessions with "New Chat" button |

---

## Pages / Routes

| Route | File | Description |
|-------|------|-------------|
| `/` | `app/page.tsx` | Landing page — hero section, feature grid, testimonials, CTA, footer |
| `/login` | `app/login/` | Login form (email/password + Google/GitHub OAuth) with glassmorphism card |
| `/register` | `app/register/` | Registration form with password strength indicator |
| `/onboarding` | `app/onboarding/` | 5-step preference wizard (tone, verbosity, model, domain, instructions) with animated stepper |
| `/dashboard` | `app/dashboard/page.tsx` | Main chat interface with session sidebar |
| `/dashboard/history` | `app/dashboard/history/` | Chat history — searchable, filterable session list |
| `/dashboard/preferences` | `app/dashboard/preferences/` | Preference editor with inline editing and preview |
| `/dashboard/analytics` | `app/dashboard/analytics/` | Usage analytics — line charts, pie charts, quality metrics |

### Dashboard Layout (`app/dashboard/layout.tsx`)

The dashboard uses a shared layout with:
- **Collapsible sidebar** — navigation links, collapses to hamburger on mobile
- **Top header** — user avatar + dropdown menu
- **Main content** — routed outlet area
- **Responsive breakpoints** — mobile (<768px), tablet (768–1024px), desktop (>1024px)

---

## State Management

### Auth Store (`src/store/authStore.ts`)

Uses **Zustand** with the following shape:

```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (tokens: TokenPair) => void;
  logout: () => void;
  setUser: (user: User) => void;
}
```

Tokens are stored in memory (Zustand store) and automatically attached to requests via the Axios interceptor.

---

## API Client (`src/lib/api.ts`)

Configured Axios instance with:

1. **Base URL** — `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
2. **Request interceptor** — attaches `Authorization: Bearer <token>` header
3. **Response interceptor** — on 401, attempts token refresh via `/api/v1/auth/refresh`; on failure, logs out
4. **Error handler** — triggers toast notifications for API errors

---

## Animations

| Animation | Technology | Location |
|-----------|-----------|----------|
| Page transitions | Framer Motion | `PageTransition.tsx` wraps each page |
| Landing page hero | GSAP timeline | `app/page.tsx` |
| Chat typewriter effect | CSS + JS | `MessageBubble.tsx` |
| Skeleton shimmer | CSS keyframes | `Skeleton.tsx` |
| Theme toggle | CSS transition | `ThemeToggle.tsx` |
| Onboarding stepper | Framer Motion | `app/onboarding/` |
| Form submission | Framer Motion | Login/Register pages |
| Chart rendering | Chart.js built-in | Analytics page |

---

## Dark / Light Mode

Implemented via CSS variable switching:
1. `ThemeProvider.tsx` reads from `localStorage` (key: `theme`)
2. Sets `data-theme="dark"` or `data-theme="light"` on `<html>`
3. `_variables.scss` defines `:root` (dark) and `[data-theme="light"]` overrides
4. Smooth 300ms CSS transition on `background-color` and `color`

---

## Development

### Setup

```bash
cd frontend
npm install
npm run dev    # → http://localhost:3000
```

### Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Build

```bash
npm run build   # Production build
npm start       # Serve production build
```

### Linting

```bash
npx eslint .    # ESLint check
```
