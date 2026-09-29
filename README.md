<h1 align="center">
  ✨ Prompt Polisher
</h1>

<p align="center">
  <strong>Your AI prompts, perfected.</strong><br/>
  A scalable SaaS platform that transforms rough prompts into expertly crafted ones using a custom-trained Small Language Model with RAG and RLHF.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch" alt="PyTorch" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis" alt="Redis" />
  <img src="https://img.shields.io/badge/Qdrant-Vector_DB-24B47E" alt="Qdrant" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker" />
</p>

---

## 🚀 What is Prompt Polisher?

Most people write vague, poorly structured prompts and get mediocre AI responses. **Prompt Polisher** takes your rough prompt and transforms it into an expertly optimized version — personalized to your preferences, writing style, and target AI model.

```
Input:  "Write me a marketing email"

Output: "Act as a senior email marketing strategist with 10 years of
        experience in B2B SaaS. Write a compelling cold outreach email
        for [product]. The email should: (1) Open with a personalized
        hook, (2) Present value proposition in under 3 sentences,
        (3) Include a clear, low-commitment CTA.
        Tone: Professional yet conversational. Length: Under 150 words."
```

Copy the optimized prompt → Paste into ChatGPT/Gemini/Claude → Get dramatically better results.

---

## ✨ Key Features

- 🤖 **Custom AI Model** — Our own Small Language Model trained specifically for prompt optimization
- 🧠 **RAG Memory** — Remembers your preferences and past conversations via vector embeddings
- 📈 **Continuous Learning (RLHF/DPO)** — Model improves daily from user feedback
- ⚡ **Real-time Streaming** — Token-by-token generation via WebSockets
- 🎨 **Bespoke UI** — Glassmorphism, dark mode, custom animations — not a template
- 🔄 **Load Balanced** — Nginx distributes across multiple backend nodes
- 🐳 **Fully Dockerized** — One command to start everything

---

## 🏗️ Architecture

```
                    ┌──────────────┐
                    │   Browser    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Nginx (LB)   │
                    └──┬───────┬───┘
                       │       │
              ┌────────▼──┐ ┌──▼────────┐
              │ Backend A │ │ Backend B  │
              │ + Worker  │ │ + Worker   │
              └─────┬─────┘ └─────┬─────┘
                    │             │
         ┌──────────┼─────────────┼──────────┐
         │          │             │           │
    ┌────▼───┐ ┌────▼───┐  ┌─────▼────┐ ┌────▼───┐
    │ Postgres│ │ Redis  │  │  Qdrant  │ │ Model  │
    └────────┘ └────────┘  └──────────┘ └────────┘
```

---

## 📂 Project Structure

```
prompt-polisher/
├── frontend/          # Next.js 14 — UI & client-side logic
├── backend/           # FastAPI — API, auth, business logic
├── ai/                # PyTorch — Model training, inference, RAG
├── infra/             # Docker, Nginx, monitoring configs
├── docs/              # Architecture, API, model card, demo prep
├── project-docs/      # Planning docs (roadmap, tasks, walkthrough)
├── docker-compose.yml # Start all services
├── .env.example       # Environment variable template
└── README.md          # You are here
```

---

## 🛠️ Quick Start

> Running this for a demo? Follow **[docs/final_demo_prep.md](./docs/final_demo_prep.md)**
> instead — it has the full checklist, run order and troubleshooting.

### Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) (v24+)
- [Node.js](https://nodejs.org/) (v20+ LTS)
- [Python](https://www.python.org/) (3.11+)
- [Git](https://git-scm.com/)

### Option A — Everything in Docker (simplest)

```bash
git clone https://github.com/Prompt-Polisher-Org/prompt-polisher.git
cd prompt-polisher
cp .env.example .env          # defaults work as-is for a local demo

docker compose --profile full up -d --build
```

Then apply the database migrations once the containers are up:

```bash
docker compose exec backend alembic upgrade head
```

### Option B — Data stores in Docker, apps on the host (best for development)

**1. Start the data stores**

```bash
cp .env.example .env
docker compose up -d postgres redis qdrant
```

**2. Backend** (terminal 1)

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**3. AI inference server** (terminal 2 — from the repo root)

```bash
pip install -r ai/requirements.txt
uvicorn ai.src.inference.server:app --reload --port 8001
```

Without a trained checkpoint at `ai/models/checkpoints/final_model.pt` this
serves clearly-labelled mock responses, so the rest of the stack still works.

**4. Frontend** (terminal 3)

```bash
cd frontend
npm install
npm run dev
```

### Open in Browser

- Frontend: [http://localhost:3000](http://localhost:3000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- AI Inference health: [http://localhost:8001/health](http://localhost:8001/health)
- Qdrant UI: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 👥 Team

| Role | Responsibility |
|---|---|
| 🎨 **Frontend / UI Lead** | Next.js, SCSS, Framer Motion, GSAP |
| 🤖 **AI / Model Architect** | PyTorch, Tokenizer, RAG, RLHF/DPO |
| ⚙️ **Systems / DevOps** | Docker, Nginx, CI/CD, Monitoring |
| 🗄️ **Data / Backend** | FastAPI, PostgreSQL, Redis, Celery |

---

## 🔀 Git Workflow

```
main ← develop ← feature/[role]-[description]
```

- All merges to `develop` via PR with 1 approval
- Conventional Commits: `feat(frontend): add login page`
- Weekly merge `develop` → `main`

See [project-docs/](./project-docs/) for the full implementation plan, task tracker, and walkthrough.

---

## 📄 License

This project is part of a Final Year Engineering Project and is not currently licensed for public use.
