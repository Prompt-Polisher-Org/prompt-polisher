# 🎨 Frontend — Prompt Polisher UI

> **Tech Stack**: Next.js 14 (App Router) · SCSS Modules · Framer Motion · GSAP · Zustand · Socket.IO Client

## Setup

```bash
npm install
npm run dev        # → http://localhost:3000
```

## Directory Structure

```
frontend/
├── src/
│   ├── app/                 # App Router pages
│   │   ├── (auth)/          # Login, Register, Onboarding
│   │   ├── (dashboard)/     # Main app pages
│   │   └── layout.tsx       # Root layout
│   ├── components/
│   │   ├── ui/              # Design system components
│   │   ├── chat/            # Chat interface
│   │   ├── preferences/     # Preference management
│   │   └── animations/      # Animation wrappers
│   ├── styles/
│   │   ├── _variables.scss  # Design tokens
│   │   ├── _mixins.scss     # SCSS mixins
│   │   ├── _animations.scss # Keyframes
│   │   └── globals.scss     # Global styles
│   ├── lib/
│   │   ├── api.ts           # API client
│   │   ├── ws.ts            # WebSocket client
│   │   └── store.ts         # Zustand stores
│   └── hooks/               # Custom React hooks
├── public/                  # Static assets
└── package.json
```

## Owner
🎨 **Frontend / UI Lead** (Member A)
