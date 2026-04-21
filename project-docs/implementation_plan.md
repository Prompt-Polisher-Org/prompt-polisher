# 🚀 Prompt Polisher — Master Context Document

> **Purpose**: This document is the single source of truth for all 4 team members. Each member should load this into their AI assistant's context at the start of every working session to maintain perfect alignment.

> **Last Updated**: 2026-04-21 | **Target Completion**: Week 14 (~July 2026)

---

## Table of Contents

1. [Part 1: The Tech Stack](#part-1-the-tech-stack)
2. [Part 2: The Architecture](#part-2-the-architecture)
3. [Part 3: The 14-Week Roadmap](#part-3-the-14-week-roadmap)
4. [Part 4: Division of Labor](#part-4-division-of-labor)
5. [Appendix: Conventions & Standards](#appendix-conventions--standards)

---

# Part 1: The Tech Stack

## Stack Overview Table

| Layer | Technology | Why This Choice |
|---|---|---|
| **Frontend Framework** | **Next.js 14+ (App Router)** | Server components, streaming, API routes, SEO — ideal for SaaS |
| **UI Animation** | **Framer Motion + GSAP** | Bespoke, non-standard animations for premium feel |
| **Styling** | **Custom SCSS Modules + CSS Variables** | Full design control; no Bootstrap/Tailwind — meets "bespoke UI" requirement |
| **State Management** | **Zustand** | Lightweight, minimal boilerplate, excellent for chat state |
| **Backend API** | **FastAPI (Python 3.11+)** | Async-native, WebSocket support, native Python AI ecosystem integration |
| **WebSockets** | **FastAPI WebSockets + Socket.IO** | Real-time streaming of model inference token-by-token |
| **AI Training** | **PyTorch 2.x + HuggingFace Transformers** | Industry standard; `Trainer` API for fine-tuning, PEFT/LoRA for efficient training |
| **Tokenizer** | **SentencePiece (BPE)** | Train a custom tokenizer from scratch on prompt-engineering corpora |
| **Model Architecture** | **Custom GPT-2 Small / Phi-style SLM (~125M–350M params)** | Trainable on consumer GPUs; small enough for laptop inference |
| **Inference Server** | **vLLM or Custom FastAPI Inference** | Optimized batched inference; fallback to raw PyTorch for simplicity |
| **Vector Database** | **Qdrant (Self-hosted, Docker)** | Rust-based, blazing fast, easy Docker deployment, great Python SDK |
| **Embedding Model** | **`sentence-transformers/all-MiniLM-L6-v2`** | 384-dim embeddings; fast, accurate, runs on CPU |
| **Primary Database** | **PostgreSQL 16** | Robust, scalable, JSONB support for flexible schemas |
| **ORM** | **SQLAlchemy 2.0 + Alembic** | Async support, migrations, mature ecosystem |
| **Authentication** | **Custom JWT + OAuth 2.0 (Google/GitHub)** | Full control; `python-jose` for JWT, `authlib` for OAuth |
| **Caching** | **Redis 7** | Session cache, rate limiting, inference result caching |
| **Task Queue** | **Celery + Redis (broker)** | Async RLHF training jobs, embedding generation, batch processing |
| **Message Format** | **Protocol Buffers (optional) / JSON** | JSON for v1 simplicity; Protobuf for v2 optimization |
| **Containerization** | **Docker + Docker Compose** | Consistent environments across all 4 laptops and cloud |
| **Load Balancer** | **Nginx (reverse proxy)** | Laptop 1 routes to Backend A (Laptop 2) and Backend B (Laptop 3) |
| **Monitoring** | **Prometheus + Grafana** | Dashboards for API latency, model inference times, system health |
| **CI/CD** | **GitHub Actions** | Automated testing, linting, Docker image builds |

---

## Detailed Stack Breakdown

### 1.1 Frontend — The Aesthetic UI Layer

```
next.js 14+
├── app/                    # App Router (Server + Client Components)
│   ├── (auth)/             # Auth pages (login, register, onboarding)
│   ├── (dashboard)/        # Main app (chat, preferences, history)
│   └── api/                # BFF (Backend-for-Frontend) API routes
├── components/
│   ├── ui/                 # Custom design system (buttons, inputs, cards)
│   ├── chat/               # Chat interface components
│   ├── preferences/        # Preference configuration UI
│   └── animations/         # GSAP/Framer Motion wrappers
├── styles/
│   ├── _variables.scss     # Design tokens (colors, spacing, typography)
│   ├── _mixins.scss        # Reusable SCSS mixins
│   ├── _animations.scss    # Keyframe animations
│   └── globals.scss        # Global styles
├── lib/
│   ├── api.ts              # API client (axios/fetch wrappers)
│   ├── ws.ts               # WebSocket client
│   └── store.ts            # Zustand stores
└── hooks/                  # Custom React hooks
```

**Design Philosophy**: 
- Dark-mode-first with glassmorphism accents
- Custom cursor effects and page transitions
- Typewriter-effect streaming for AI responses
- Floating particle backgrounds on landing page
- Bento grid layouts for the dashboard
- 3D tilt cards for feature showcases (vanilla-tilt.js)

**Key Libraries**:
| Library | Purpose |
|---|---|
| `framer-motion` | Layout animations, page transitions, gesture handling |
| `gsap` | Complex timeline animations, scroll-triggered effects |
| `lenis` | Smooth scrolling |
| `react-hot-toast` | Notification toasts |
| `react-syntax-highlighter` | Code/prompt syntax highlighting |
| `zustand` | Global state management |
| `socket.io-client` | WebSocket connection to backend |

---

### 1.2 Backend — FastAPI Service Layer

```
backend/
├── app/
│   ├── main.py             # FastAPI app entry point
│   ├── config.py           # Environment config (Pydantic Settings)
│   ├── dependencies.py     # Dependency injection
│   ├── middleware/
│   │   ├── auth.py         # JWT verification middleware
│   │   ├── rate_limit.py   # Redis-based rate limiting
│   │   └── cors.py         # CORS configuration
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py     # Login, Register, OAuth endpoints
│   │   │   ├── users.py    # User profile, preferences CRUD
│   │   │   ├── chat.py     # Chat sessions, message history
│   │   │   ├── inference.py# Prompt generation endpoint
│   │   │   ├── feedback.py # RLHF feedback collection
│   │   │   └── health.py   # Health check endpoints
│   │   └── ws/
│   │       └── stream.py   # WebSocket streaming endpoint
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   ├── embedding_service.py  # Vector embedding + Qdrant ops
│   │   ├── inference_service.py  # Model inference orchestration
│   │   └── feedback_service.py   # RLHF data pipeline
│   ├── core/
│   │   ├── security.py     # Password hashing, JWT creation
│   │   └── database.py     # Async SQLAlchemy engine + session
│   └── tasks/
│       ├── celery_app.py   # Celery configuration
│       ├── embedding_tasks.py  # Async embedding generation
│       └── training_tasks.py   # RLHF fine-tuning jobs
├── alembic/                # Database migrations
├── tests/                  # Pytest test suite
├── Dockerfile
└── requirements.txt
```

**Key API Endpoints**:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | User registration |
| `POST` | `/api/v1/auth/login` | JWT token pair generation |
| `POST` | `/api/v1/auth/oauth/{provider}` | OAuth callback |
| `GET/PUT` | `/api/v1/users/me/preferences` | Get/Update global prompt preferences |
| `POST` | `/api/v1/chat/sessions` | Create new chat session |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | Get chat history |
| `POST` | `/api/v1/inference/generate` | Generate optimized prompt (REST fallback) |
| `WS` | `/ws/stream/{session_id}` | Real-time streaming inference |
| `POST` | `/api/v1/feedback` | Submit RLHF feedback (thumbs up/down + text) |
| `GET` | `/api/v1/health` | Liveness + readiness probe |

---

### 1.3 AI / ML Layer

```
ai/
├── tokenizer/
│   ├── train_tokenizer.py      # Train SentencePiece BPE tokenizer
│   ├── tokenizer.model         # Trained tokenizer artifact
│   └── tokenizer_config.json
├── model/
│   ├── config.py               # Model hyperparameters
│   ├── architecture.py         # Custom transformer architecture
│   ├── dataset.py              # Dataset loading + preprocessing
│   ├── train.py                # Pre-training script
│   ├── finetune.py             # Supervised fine-tuning (SFT)
│   └── evaluate.py             # Evaluation metrics (BLEU, ROUGE, perplexity)
├── rlhf/
│   ├── reward_model.py         # Reward model architecture
│   ├── train_reward.py         # Train reward model on feedback data
│   ├── ppo_trainer.py          # PPO training loop (or DPO alternative)
│   └── data_pipeline.py        # Feedback data preprocessing
├── inference/
│   ├── engine.py               # Inference engine with KV-cache
│   ├── server.py               # Inference gRPC/HTTP server
│   └── quantize.py             # INT8/INT4 quantization for laptops
├── rag/
│   ├── embedder.py             # Sentence-transformer embedding wrapper
│   ├── retriever.py            # Qdrant retrieval logic
│   └── augmenter.py            # Context injection into prompts
├── data/
│   ├── raw/                    # Raw prompt datasets
│   ├── processed/              # Cleaned, tokenized data
│   └── feedback/               # RLHF feedback logs
└── notebooks/                  # Jupyter notebooks for experimentation
```

**Model Training Strategy**:

| Phase | What | How |
|---|---|---|
| **Phase 1: Pre-training** | Train a ~125M param GPT-2-style model from scratch | Causal language modeling on curated prompt-engineering corpus (~5-10GB text) |
| **Phase 2: SFT** | Supervised fine-tuning on prompt pairs | (bad_prompt → optimized_prompt) pairs; Instruction-tuning format |
| **Phase 3: RLHF/DPO** | Align model with human preferences | Collect user feedback → Train reward model → PPO/DPO alignment |

> [!IMPORTANT]
> **Realistic Scope Check**: Training a 125M model from scratch requires significant compute. Consider starting with a **pre-trained base** (like `gpt2-small` or `microsoft/phi-1_5`) and doing **SFT + RLHF** on top. This gives you a "custom model" while being achievable on consumer hardware. The custom tokenizer can still be trained independently and integrated.

---

### 1.4 Data Layer

**PostgreSQL Schema (Core Tables)**:

```sql
-- Users & Authentication
users (id, email, password_hash, display_name, avatar_url, oauth_provider, created_at, updated_at)
user_preferences (id, user_id FK, tone, verbosity, target_model, domain, custom_instructions, updated_at)

-- Chat & Sessions
chat_sessions (id, user_id FK, title, created_at, updated_at)
messages (id, session_id FK, role ENUM('user','assistant'), content TEXT, token_count, created_at)

-- RLHF Feedback
feedback (id, message_id FK, user_id FK, rating ENUM('positive','negative'), comment TEXT, created_at)

-- Analytics
usage_logs (id, user_id FK, endpoint, tokens_used, latency_ms, created_at)
```

**Qdrant Collections**:

| Collection | Embedding Dim | Payload | Purpose |
|---|---|---|---|
| `user_preferences` | 384 | `{user_id, preference_text, updated_at}` | Semantic search over user prefs |
| `chat_history` | 384 | `{user_id, session_id, message_id, role, content}` | RAG: retrieve relevant past conversations |
| `prompt_patterns` | 384 | `{category, pattern, quality_score}` | RAG: retrieve proven prompt templates |

---

# Part 2: The Architecture

## 2.1 High-Level System Architecture

```mermaid
graph TB
    subgraph "Laptop 4 — Client"
        CLIENT["Browser / Postman<br/>End User Simulation"]
    end

    subgraph "Laptop 1 — Load Balancer"
        NGINX["Nginx<br/>Reverse Proxy + LB"]
    end

    subgraph "Laptop 2 — Server Node A"
        API_A["FastAPI Server A<br/>(Port 8000)"]
        WORKER_A["AI Worker A<br/>(Celery + Model)"]
        API_A --> WORKER_A
    end

    subgraph "Laptop 3 — Server Node B"
        API_B["FastAPI Server B<br/>(Port 8000)"]
        WORKER_B["AI Worker B<br/>(Celery + Model)"]
        API_B --> WORKER_B
    end

    subgraph "Shared Services (Laptop 2 or dedicated)"
        PG["PostgreSQL"]
        REDIS["Redis"]
        QDRANT["Qdrant"]
    end

    CLIENT -->|"HTTPS/WSS"| NGINX
    NGINX -->|"Round Robin / Least Conn"| API_A
    NGINX -->|"Round Robin / Least Conn"| API_B
    API_A --> PG
    API_A --> REDIS
    API_A --> QDRANT
    API_B --> PG
    API_B --> REDIS
    API_B --> QDRANT
    WORKER_A -->|"Read model weights"| REDIS
    WORKER_B -->|"Read model weights"| REDIS
```

## 2.2 Hardware Topology — Physical Deployment (Phase 1)

> [!NOTE]
> All 4 laptops must be on the **same LAN** (Wi-Fi or Ethernet switch). Use static IPs or hostname resolution.

| Laptop | Role | Static IP (Example) | Services Running |
|---|---|---|---|
| **Laptop 1** | Load Balancer + Monitoring | `192.168.1.10` | Nginx, Prometheus, Grafana |
| **Laptop 2** | Backend Node A + Data Stores | `192.168.1.20` | FastAPI, Celery Worker, PostgreSQL, Redis, Qdrant, Model Inference |
| **Laptop 3** | Backend Node B | `192.168.1.30` | FastAPI, Celery Worker, Model Inference |
| **Laptop 4** | Client Simulation + Load Testing | `192.168.1.40` | Browser, k6/Locust load testing |

**Nginx Configuration** (Laptop 1):
```nginx
upstream prompt_polisher_api {
    # Load balancing strategy: least connections
    least_conn;
    
    server 192.168.1.20:8000 weight=5;  # Node A (also hosts DB, so slightly higher weight)
    server 192.168.1.30:8000 weight=5;  # Node B
    
    # Health checks
    keepalive 32;
}

upstream prompt_polisher_ws {
    # WebSocket connections: IP hash for sticky sessions
    ip_hash;
    
    server 192.168.1.20:8001;
    server 192.168.1.30:8001;
}

server {
    listen 80;
    listen 443 ssl;
    server_name promptpolisher.local;

    # SSL (self-signed for local dev)
    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    # API routes
    location /api/ {
        proxy_pass http://prompt_polisher_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for inference (model can take time)
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # WebSocket routes
    location /ws/ {
        proxy_pass http://prompt_polisher_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;  # Keep WS alive for 1 hour
    }

    # Frontend (served from CDN or Laptop 1 itself in dev)
    location / {
        proxy_pass http://localhost:3000;  # Next.js dev server on Laptop 1
    }
}
```

## 2.3 Data Flow — End-to-End Request Lifecycle

```mermaid
sequenceDiagram
    actor User as User (Laptop 4)
    participant Nginx as Nginx LB (Laptop 1)
    participant API as FastAPI (Laptop 2 or 3)
    participant Redis as Redis Cache
    participant PG as PostgreSQL
    participant Qdrant as Qdrant VectorDB
    participant Worker as AI Worker (Celery)
    participant Model as Custom SLM

    User->>Nginx: POST /api/v1/inference/generate<br/>{prompt: "Write me a...", session_id: "abc"}
    Nginx->>API: Route to least-loaded backend

    Note over API: Step 1: Auth & Rate Limit
    API->>Redis: Check JWT session + rate limit
    Redis-->>API: ✅ Authorized, 47/50 requests used

    Note over API: Step 2: Retrieve Context (RAG)
    API->>PG: Fetch user preferences
    PG-->>API: {tone: "professional", target: "GPT-4", domain: "marketing"}
    API->>API: Embed user prompt using SentenceTransformer
    API->>Qdrant: Vector search: top-5 similar past messages + top-3 prompt patterns
    Qdrant-->>API: Relevant context chunks

    Note over API: Step 3: Construct Augmented Prompt
    API->>API: Build system prompt:<br/>preferences + retrieved context + user input

    Note over API: Step 4: Model Inference
    API->>Worker: Dispatch inference task (Celery)
    Worker->>Model: Forward pass with augmented prompt
    Model-->>Worker: Generated tokens (streamed)
    Worker-->>API: Token stream via Redis Pub/Sub

    Note over API: Step 5: Stream to User
    API-->>Nginx: SSE / WebSocket token stream
    Nginx-->>User: Real-time token-by-token display

    Note over API: Step 6: Persist
    API->>PG: Save message to chat_history
    API->>Qdrant: Embed & store new message for future RAG
    API->>Redis: Cache generated prompt (TTL: 1hr)
```

## 2.4 RAG Integration Pipeline

The Vector Database is the **memory backbone** of the system. Here's how it works:

### Ingestion Flow (Write Path)
1. **User sets preferences** → Preferences text is embedded via `all-MiniLM-L6-v2` → Stored in Qdrant `user_preferences` collection
2. **User sends a message** → Message embedded → Stored in `chat_history` collection with metadata (user_id, session_id, timestamp)
3. **Model generates response** → Response embedded → Also stored in `chat_history`
4. **Admin curates prompt patterns** → High-quality prompt templates embedded → Stored in `prompt_patterns` collection

### Retrieval Flow (Read Path)
1. User's new prompt is embedded in real-time
2. **Three parallel Qdrant searches**:
   - `user_preferences`: Retrieve this user's style/tone preferences (filtered by `user_id`)
   - `chat_history`: Retrieve top-K most relevant past interactions (filtered by `user_id`, sorted by relevance + recency)
   - `prompt_patterns`: Retrieve top-K proven prompt templates (globally, no user filter)
3. Retrieved chunks are **injected into the system prompt** as context
4. The augmented prompt is sent to the custom SLM for generation

```
┌─────────────────────────────────────────────────────────────┐
│                    AUGMENTED PROMPT                          │
│                                                             │
│  [SYSTEM]                                                   │
│  You are a prompt optimization expert.                      │
│  User preferences: {from Qdrant: user_preferences}         │
│  Relevant past context: {from Qdrant: chat_history}         │
│  Proven patterns: {from Qdrant: prompt_patterns}            │
│                                                             │
│  [USER]                                                     │
│  Original prompt: "Write me a marketing email for..."       │
│                                                             │
│  [TASK]                                                     │
│  Generate an optimized version of the user's prompt         │
│  that follows the preferences and leverages the patterns.   │
└─────────────────────────────────────────────────────────────┘
```

## 2.5 RLHF Continuous Learning Pipeline

```mermaid
graph LR
    A["User Feedback<br/>👍/👎 + Comment"] --> B["Feedback Store<br/>(PostgreSQL)"]
    B --> C{"Batch Size<br/>Reached?<br/>(e.g., 100 samples)"}
    C -->|No| D["Wait for more feedback"]
    C -->|Yes| E["Celery Task:<br/>Train Reward Model"]
    E --> F["Reward Model<br/>(Binary classifier)"]
    F --> G["PPO/DPO Training<br/>on SLM"]
    G --> H["Updated Model<br/>Weights"]
    H --> I["A/B Test<br/>New vs Old"]
    I -->|Better| J["Deploy New Model"]
    I -->|Worse| K["Rollback"]

    style A fill:#4CAF50,color:#fff
    style G fill:#2196F3,color:#fff
    style J fill:#FF9800,color:#fff
```

**RLHF Implementation Options** (Choose Based on Compute):

| Approach | Complexity | Compute Needed | Recommendation |
|---|---|---|---|
| **DPO (Direct Preference Optimization)** | Low | Low | ✅ **Best for your setup** — no reward model needed |
| **PPO (with Reward Model)** | High | High | Full RLHF but needs GPU cluster |
| **Rejection Sampling + SFT** | Medium | Medium | Periodic re-fine-tuning on best outputs |

> [!TIP]
> **Start with DPO**. It's simpler than PPO, requires no separate reward model, and achieves comparable results. You collect (prompt, chosen_response, rejected_response) triples from user feedback and directly fine-tune. This is publishable and impressive for a final year project.

---

# Part 3: The 14-Week Roadmap

## Sprint Calendar Overview

```mermaid
gantt
    title Prompt Polisher — 14-Week Development Roadmap
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    
    section Foundation
    Week 1-2: Environment & Core Setup     :w1, 2026-04-21, 14d
    
    section Core Development
    Week 3-4: Auth, DB & Basic API         :w3, after w1, 14d
    Week 5-6: AI Model & Tokenizer         :w5, after w1, 14d
    Week 7-8: RAG Pipeline & Chat UI       :w7, after w3, 14d
    
    section Integration
    Week 9-10: Full System Integration     :w9, after w7, 14d
    
    section Advanced Features
    Week 11-12: RLHF & Optimization        :w11, after w9, 14d
    
    section Polish & Deploy
    Week 13: Load Testing & Polish         :w13, after w11, 7d
    Week 14: Cloud Deploy & Documentation  :w14, after w13, 7d
```

---

### 🏗️ Week 1–2: Foundation & Environment Setup

**Theme**: *"Everyone sets up and can run everything locally"*

| Task | Owner | Deliverable |
|---|---|---|
| Initialize monorepo structure with pnpm workspaces | DevOps | `prompt-polisher/` monorepo |
| Set up Next.js 14 project with App Router, SCSS | Frontend | Running `localhost:3000` |
| Set up FastAPI project with project structure | Backend | Running `localhost:8000` with `/health` |
| Docker Compose for all services (PG, Redis, Qdrant) | DevOps | `docker-compose.yml` — one command to start all infra |
| Set up PostgreSQL schema + Alembic migrations | Backend | Users + Sessions tables migrated |
| Set up AI project structure + Jupyter environment | AI Lead | `ai/` directory with notebook environment |
| Begin dataset collection for tokenizer training | AI Lead | Raw text corpus (~2GB target) |
| Design system creation: color palette, typography, spacing tokens | Frontend | `_variables.scss` + component sketches |
| Set up GitHub repo, branch strategy, PR templates | DevOps | `main`, `develop`, `feature/*` branches |
| Configure linting: ESLint, Prettier, Ruff, Black | DevOps | Pre-commit hooks running |

**Exit Criteria**: Every team member can run `docker compose up` and see all services start. Frontend shows a styled landing page. Backend returns health check. AI notebook runs.

---

### 🔐 Week 3–4: Authentication, Database & Basic API

**Theme**: *"Users can register, log in, and set preferences"*

| Task | Owner | Deliverable |
|---|---|---|
| JWT authentication (register, login, refresh tokens) | Backend | `/auth/register`, `/auth/login` working |
| OAuth 2.0 integration (Google + GitHub) | Backend | Social login flow complete |
| User preferences CRUD API | Backend | `/users/me/preferences` endpoint |
| Alembic migrations for all core tables | Backend | Full schema deployed |
| Redis session + rate limiting middleware | Backend | Rate limiter at 50 req/min/user |
| Login/Register pages with animations | Frontend | Glassmorphism auth pages |
| Onboarding flow: preference wizard UI | Frontend | Multi-step form with animations |
| Dashboard layout shell (sidebar, header, content area) | Frontend | Responsive dashboard frame |
| API client library (Axios interceptors, error handling) | Frontend | `lib/api.ts` with token refresh |
| Begin tokenizer training on collected corpus | AI Lead | SentencePiece BPE model (vocab=32K) |
| Nginx basic config + SSL on Laptop 1 | DevOps | Nginx routing to one backend |

**Exit Criteria**: Full signup → login → set preferences → see dashboard flow works end-to-end.

---

### 🤖 Week 5–6: AI Model Training & Inference Engine

**Theme**: *"The model can generate its first prompt"*

| Task | Owner | Deliverable |
|---|---|---|
| Finalize custom tokenizer (BPE, vocab=32K) | AI Lead | `tokenizer.model` artifact |
| Define model architecture (GPT-2 small style) | AI Lead | `architecture.py` with config |
| Curate SFT dataset: (bad_prompt, good_prompt) pairs | AI Lead | ~10K training samples |
| Pre-train or fine-tune base model (SFT Phase) | AI Lead | Checkpoint with loss < target |
| Build inference engine with KV-cache | AI Lead | `inference/engine.py` |
| INT8 quantization for laptop deployment | AI Lead | Quantized model artifact |
| Inference API endpoint (REST) | Backend | `POST /inference/generate` |
| Celery worker setup for async inference | Backend | Workers consuming inference tasks |
| WebSocket streaming infrastructure | Backend | Token-by-token streaming works |
| Chat session API (create, list, get messages) | Backend | CRUD for chat sessions |
| Chat UI component (message list, input box) | Frontend | Basic chat interface rendering |
| WebSocket client integration | Frontend | Real-time token streaming in UI |

**Exit Criteria**: User types a prompt in the UI → Backend dispatches to model → Model generates an optimized prompt → Tokens stream back to UI in real-time.

---

### 🔍 Week 7–8: RAG Pipeline & Chat Experience

**Theme**: *"The model remembers your preferences and past conversations"*

| Task | Owner | Deliverable |
|---|---|---|
| Embedding service (SentenceTransformer wrapper) | Backend | `embedding_service.py` |
| Qdrant collection setup (3 collections) | Backend | Qdrant schema + indexing |
| Ingestion pipeline: embed user prefs + messages | Backend | Auto-embed on preference save + message create |
| Retrieval service: multi-collection semantic search | Backend | `retriever.py` returning ranked results |
| Context augmentation: build augmented prompts | Backend | `augmenter.py` injecting RAG context |
| Integrate RAG into inference pipeline | Backend + AI | End-to-end: query → retrieve → augment → generate |
| Chat history page with search | Frontend | Searchable conversation history |
| Preference panel in dashboard | Frontend | Live preference editing with preview |
| Prompt comparison view (original vs optimized) | Frontend | Side-by-side diff view |
| Copy-to-clipboard with formatting | Frontend | One-click copy of optimized prompt |
| Streaming text effects (typewriter, cursor) | Frontend | Polished streaming UX |
| Prompt patterns seed data | AI Lead | Curated collection of 500+ prompt patterns |

**Exit Criteria**: User asks for a prompt → System retrieves their preferences + relevant history → Model generates a personalized, context-aware optimized prompt. The experience feels personalized.

---

### 🔗 Week 9–10: Full System Integration & Multi-Node Setup

**Theme**: *"All 4 laptops work together as one system"*

| Task | Owner | Deliverable |
|---|---|---|
| Multi-node Nginx load balancing (Laptop 1→2,3) | DevOps | Requests distributed across both backends |
| Docker Compose for production-like deployment | DevOps | Separate compose files per laptop role |
| Network configuration (static IPs, DNS, firewall) | DevOps | All laptops communicating |
| Shared PostgreSQL/Redis/Qdrant access from Node B | DevOps | Node B connects to data stores on Node A |
| WebSocket sticky sessions (ip_hash) | DevOps | WS connections maintain state |
| Health checks + auto-failover in Nginx | DevOps | Unhealthy node removed from rotation |
| End-to-end integration testing | All | Full flow works through load balancer |
| Performance baseline testing (k6, Locust) | DevOps | Baseline: requests/sec, p95 latency |
| Error handling & graceful degradation | Backend | Retries, circuit breakers, fallback responses |
| Loading states, error boundaries, offline handling | Frontend | Polished error UX |
| Model A/B testing infrastructure | AI Lead | Serve multiple model versions |
| Monitoring dashboards (Prometheus + Grafana) | DevOps | CPU, memory, inference latency dashboards |

**Exit Criteria**: Laptop 4 runs a load test → Nginx distributes to both backend nodes → Both respond correctly → Monitoring shows balanced load. System handles 100 concurrent users.

---

### 🧠 Week 11–12: RLHF, Optimization & Advanced Features

**Theme**: *"The model learns from feedback and the system is production-grade"*

| Task | Owner | Deliverable |
|---|---|---|
| Feedback collection UI (thumbs up/down + comment) | Frontend | Inline feedback widget on each response |
| Feedback API endpoint | Backend | `POST /feedback` storing ratings |
| DPO/RLHF training pipeline | AI Lead | Training script consuming feedback data |
| Reward model (if using PPO approach) | AI Lead | Binary preference classifier |
| Automated fine-tuning Celery task | Backend + AI | Periodic model retraining on feedback |
| Model versioning + weight management | AI Lead + DevOps | Model registry with version tagging |
| Response caching (Redis) for repeated prompts | Backend | Cache hit rate > 30% |
| API response compression (gzip/brotli) | Backend | Reduced payload sizes |
| Frontend performance optimization | Frontend | Lighthouse score > 90 |
| Prompt history analytics dashboard | Frontend | Usage graphs, common prompt categories |
| User analytics (most-used features, session duration) | Backend | Analytics API + dashboard |
| Security audit: SQL injection, XSS, CSRF | Backend | All OWASP Top 10 addressed |

**Exit Criteria**: Users provide feedback → Feedback is collected → Model retrained with DPO → New model version generates measurably better prompts. System handles 500+ concurrent users.

---

### 🧪 Week 13: Load Testing, Polish & Documentation

**Theme**: *"Stress test to 10K users and polish every pixel"*

| Task | Owner | Deliverable |
|---|---|---|
| Load test: simulate 1K → 5K → 10K users (Locust) | DevOps | Performance report with bottleneck analysis |
| Database query optimization (EXPLAIN ANALYZE) | Backend | All slow queries optimized with indexes |
| Connection pooling tuning (PgBouncer or SQLAlchemy) | Backend | Stable under high concurrency |
| Redis caching strategy refinement | Backend | Optimal TTLs, eviction policies |
| UI/UX final polish pass | Frontend | All animations smooth, responsive on all screens |
| Accessibility audit (WCAG 2.1 AA) | Frontend | Keyboard nav, screen reader, contrast |
| Dark/Light mode toggle | Frontend | Seamless theme switching |
| Landing page redesign (final version) | Frontend | Stunning hero section + feature grid |
| API documentation (OpenAPI/Swagger) | Backend | Auto-generated from FastAPI schemas |
| Architecture documentation | All | System design document with diagrams |
| Model evaluation report | AI Lead | Perplexity, BLEU, human eval scores |
| Demo video recording | All | 5-minute walkthrough video |

**Exit Criteria**: System handles simulated 10K users. All documentation complete. Demo video recorded.

---

### 🚀 Week 14: Cloud Deployment & Final Presentation

**Theme**: *"Go live on the internet"*

| Task | Owner | Deliverable |
|---|---|---|
| Purchase domain (e.g., `promptpolisher.dev`) | DevOps | Domain registered + DNS configured |
| Cloud provider setup (AWS/GCP/DigitalOcean) | DevOps | VPS instances provisioned |
| Docker image optimization (multi-stage builds) | DevOps | Slim production images |
| Kubernetes manifests or Docker Swarm config | DevOps | Orchestration config for cloud |
| CI/CD pipeline (GitHub Actions → deploy) | DevOps | Auto-deploy on `main` push |
| SSL certificate (Let's Encrypt) | DevOps | HTTPS enabled |
| Environment variable management (secrets) | DevOps | `.env` → secrets manager |
| Production PostgreSQL (managed or self-hosted) | Backend | Backup + restore tested |
| Final integration test on cloud | All | Full flow works on `promptpolisher.dev` |
| Presentation slides preparation | All | Project presentation deck |
| Final project report | All | Academic submission document |

**Exit Criteria**: `promptpolisher.dev` is live on the internet, SSL-secured, and all features work. Presentation is ready.

---

# Part 4: Division of Labor

## Role Assignments

```mermaid
graph TD
    subgraph "🎨 Member A: Frontend/UI Lead"
        A1["Design System & Components"]
        A2["Auth & Onboarding UI"]
        A3["Chat Interface & Streaming"]
        A4["Dashboard & Analytics UI"]
        A5["Landing Page & Polish"]
    end

    subgraph "🤖 Member B: AI/Model Architect"
        B1["Tokenizer Training"]
        B2["Model Architecture & Training"]
        B3["RAG: Embeddings & Retrieval"]
        B4["RLHF/DPO Pipeline"]
        B5["Model Evaluation & Optimization"]
    end

    subgraph "⚙️ Member C: Systems/DevOps Engineer"
        C1["Docker & Infrastructure"]
        C2["Nginx Load Balancer"]
        C3["Multi-Node Networking"]
        C4["Monitoring & CI/CD"]
        C5["Cloud Deployment"]
    end

    subgraph "🗄️ Member D: Data/Backend Engineer"
        D1["FastAPI Core & Auth"]
        D2["Database Schema & Migrations"]
        D3["Chat & Inference APIs"]
        D4["Celery Workers & Queues"]
        D5["Security & Performance"]
    end
```

---

## Detailed Role Breakdown

### 🎨 Member A: Frontend / UI Lead

**Primary Responsibility**: Everything the user sees and interacts with.

| Week(s) | Deliverables | Dependencies |
|---|---|---|
| 1–2 | Design system (tokens, SCSS variables), landing page wireframe, Next.js project setup | None |
| 3–4 | Auth pages (login/register/OAuth), onboarding wizard, dashboard shell | Backend: Auth API |
| 5–6 | Chat UI component, WebSocket client integration, message rendering | Backend: WS endpoint |
| 7–8 | Chat history page, preference panel, prompt diff view, copy button, typewriter effect | Backend: Chat API, RAG API |
| 9–10 | Error boundaries, loading states, offline handling, responsive design pass | Integration: All APIs stable |
| 11–12 | Feedback widget, analytics dashboard, performance optimization (Lighthouse) | Backend: Feedback API, Analytics API |
| 13 | Final UI polish, dark/light mode, accessibility audit, landing page v2 | None |
| 14 | Presentation slides UI sections, demo recording | All: System live |

**Key Technologies to Master**: Next.js 14 (App Router), Framer Motion, GSAP, SCSS Modules, Zustand, Socket.IO Client

---

### 🤖 Member B: AI / Model Architect

**Primary Responsibility**: The entire ML pipeline — tokenizer, model, RAG, RLHF.

| Week(s) | Deliverables | Dependencies |
|---|---|---|
| 1–2 | Dataset collection strategy, begin corpus scraping/curation, Jupyter env setup | None |
| 3–4 | Train SentencePiece tokenizer (BPE, 32K vocab), dataset preprocessing pipeline | Corpus data collected |
| 5–6 | Model architecture definition, pre-training/SFT, inference engine with KV-cache, INT8 quantization | Tokenizer complete |
| 7–8 | SentenceTransformer embedding wrapper, Qdrant retrieval logic, context augmenter, seed prompt patterns | Backend: Qdrant running |
| 9–10 | Model A/B testing framework, model evaluation (perplexity, BLEU), multi-node inference validation | DevOps: Multi-node ready |
| 11–12 | DPO training pipeline, reward model (optional), automated retraining Celery task | Backend: Feedback data collected |
| 13 | Model evaluation report, hyperparameter documentation, model card | None |
| 14 | Presentation AI sections, model demo preparation | All: System live |

**Key Technologies to Master**: PyTorch, HuggingFace Transformers, SentencePiece, Sentence-Transformers, Qdrant Python SDK, PEFT/LoRA, DPO/TRL

---

### ⚙️ Member C: Systems / DevOps Engineer

**Primary Responsibility**: Infrastructure, networking, deployment, monitoring.

| Week(s) | Deliverables | Dependencies |
|---|---|---|
| 1–2 | Monorepo structure, Docker Compose (PG, Redis, Qdrant), GitHub repo + branch strategy, pre-commit hooks | None |
| 3–4 | Nginx basic config on Laptop 1, self-signed SSL, initial Docker networking | None |
| 5–6 | Celery + Redis broker setup, Docker images for backend + AI worker | Backend: FastAPI running |
| 7–8 | Qdrant Docker deployment, persistent volume configuration, backup scripts | None |
| 9–10 | **Multi-node deployment**: Nginx LB across Laptop 2+3, static IP config, health checks, WebSocket sticky sessions, Prometheus + Grafana dashboards | All: Services running |
| 11–12 | Load testing with Locust/k6, bottleneck identification, Docker image optimization | All: System integrated |
| 13 | Final load test (simulate 10K users), performance report, stress testing | All: Optimized |
| 14 | **Cloud deployment**: Domain purchase, VPS setup, Docker/K8s deploy, Let's Encrypt SSL, CI/CD pipeline | All: Final code |

**Key Technologies to Master**: Docker, Docker Compose, Nginx, Prometheus, Grafana, Locust/k6, GitHub Actions, Let's Encrypt, Linux networking

---

### 🗄️ Member D: Data / Backend Engineer

**Primary Responsibility**: All API logic, database design, business logic, security.

| Week(s) | Deliverables | Dependencies |
|---|---|---|
| 1–2 | FastAPI project structure, config management (Pydantic Settings), PostgreSQL schema v1, Alembic setup | DevOps: Docker Compose running |
| 3–4 | Auth system (JWT + OAuth), user CRUD, preferences CRUD, Redis rate limiting middleware | None |
| 5–6 | Chat session API, message CRUD, inference endpoint (dispatches to Celery), WebSocket streaming endpoint | AI: Model can generate |
| 7–8 | Embedding service integration, Qdrant ingestion pipeline (auto-embed on save), retrieval service, RAG integration into inference | AI: Embedding model ready |
| 9–10 | Error handling (retries, circuit breakers), connection pooling, integration testing, Swagger documentation | DevOps: Multi-node ready |
| 11–12 | Feedback API, analytics API, RLHF data pipeline (export feedback for AI training), security audit (OWASP) | AI: DPO pipeline ready |
| 13 | Query optimization, caching strategy, API docs finalization, load test support | DevOps: Load testing |
| 14 | Production database setup, backup/restore testing, final integration verification | DevOps: Cloud ready |

**Key Technologies to Master**: FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis, Celery, Pydantic, python-jose (JWT), Qdrant client

---

## Cross-Team Dependency Matrix

> [!IMPORTANT]
> This matrix shows when one team member's work depends on another's. Plan handoffs accordingly.

| Week | Frontend (A) Needs From | AI (B) Needs From | DevOps (C) Needs From | Backend (D) Needs From |
|---|---|---|---|---|
| 3–4 | Backend: Auth API ready | — | — | DevOps: Docker infra |
| 5–6 | Backend: WS + Chat API | — | Backend: FastAPI running | AI: Model inference endpoint |
| 7–8 | Backend: RAG API | DevOps: Qdrant deployed | — | AI: Embeddings + Retriever |
| 9–10 | All APIs stable | DevOps: Multi-node ready | All services running | DevOps: Multi-node ready |
| 11–12 | Backend: Feedback API | Backend: Feedback data pipeline | All: Integrated system | AI: DPO scripts ready |

---

## Communication Protocols

### Daily
- **Async standup** (Slack/Discord): Each member posts what they did, what they'll do, blockers
- Format: `✅ Done: ... | 🎯 Today: ... | 🚫 Blocked: ...`

### Weekly
- **30-minute sync call** every Monday: Sprint review + planning
- **PR review rotation**: Everyone reviews at least 1 PR per week from another team member

### Integration Points
- **Week 4 end**: First integration checkpoint (Auth flow works E2E)
- **Week 6 end**: Second checkpoint (Model generates a prompt via API)
- **Week 8 end**: Third checkpoint (RAG-augmented generation works)
- **Week 10 end**: Full system demo on all 4 laptops

---

# Appendix: Conventions & Standards

## Git Workflow

```
main ← develop ← feature/[role]-[description]

Examples:
  feature/frontend-auth-pages
  feature/ai-tokenizer-training
  feature/devops-nginx-config
  feature/backend-chat-api
```

- All merges to `develop` via PR with at least 1 reviewer
- Weekly merge from `develop` → `main` after integration tests pass
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat(frontend): add glassmorphism login page`
  - `fix(backend): resolve JWT refresh token race condition`
  - `chore(devops): update docker-compose volumes`

## Environment Variables

All env vars go in `.env` files (git-ignored) with a `.env.example` template committed:

```bash
# .env.example
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/prompt_polisher
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
JWT_SECRET=your-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=30
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
MODEL_PATH=./ai/model/checkpoints/latest
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## API Design Standards

- All endpoints follow REST conventions
- Versioned: `/api/v1/...`
- Consistent error response format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [{"field": "email", "issue": "Invalid format"}]
  }
}
```
- Pagination: `?page=1&page_size=20` → Response includes `total_count`, `page`, `page_size`

## Testing Strategy

| Layer | Tool | Coverage Target |
|---|---|---|
| Backend Unit | `pytest` + `pytest-asyncio` | 80%+ on services |
| Backend Integration | `httpx` + TestClient | All API endpoints |
| Frontend Unit | `Jest` + React Testing Lib | 60%+ on components |
| Frontend E2E | `Playwright` | Critical user flows |
| AI Model | Custom eval scripts | BLEU, ROUGE, perplexity metrics |
| Load Testing | `Locust` or `k6` | 10K simulated users |

## Documentation Requirements

Each team member maintains:
1. **Technical docs** in their module's `README.md`
2. **API docs** auto-generated from FastAPI
3. **Architecture Decision Records (ADRs)** for significant decisions
4. **Weekly progress logs** in a shared doc

---

> [!NOTE]
> **How to use this document**: Each team member should copy the relevant sections for their role into their AI assistant's context. When starting a new work session, paste this document (or your role-specific section) as the system prompt to ensure your AI assistant understands the full architecture and your specific responsibilities.
