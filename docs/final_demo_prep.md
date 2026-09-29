# 🎬 Final Demo Preparation

Everything needed to run Prompt Polisher end-to-end on a laptop and demo it with
confidence. Work top to bottom the first time; after that, **[Run Order](#4-run-order)**
and the **[Demo Script](#7-demo-script)** are the only two sections you need.

> **Do this first, before anything else:** [§2 Day-Before Checklist](#2-day-before-checklist).
> Two of those steps download hundreds of MB and *cannot* be done on venue wifi.

---

## 1. What state the project is in

### ✅ Working and demo-ready

| Area | Notes |
|---|---|
| Auth | Email/password register, login, JWT refresh, logout |
| Chat | Session CRUD, message history, preferences |
| Prompt optimization | REST + WebSocket token streaming |
| RAG | Qdrant-backed preferences / history / prompt-pattern retrieval |
| Feedback | Thumbs up/down, stats, RLHF export |
| A/B testing | Experiments, stats, result rating |
| Frontend | 9 routes, dark/light theme, production build clean |
| Backend tests | 67 passing (`pytest`) |
| Docker | Full stack builds and runs via Compose profiles |

### ⚠️ Known gaps — say these out loud before someone asks

| Gap | What to say |
|---|---|
| **No trained model checkpoint** | `ai/models/checkpoints/` is gitignored and empty. The inference server detects this and returns responses prefixed `MOCK:`. Every other layer — RAG, streaming, feedback, caching — is real. |
| **No trained tokenizer** | Same: `ai/models/tokenizer/` is gitignored. Needed only if you load a real checkpoint. |
| **OAuth not configured** | Google/GitHub buttons return `501 Not Implemented` until credentials are set in `.env`. **Demo with email/password.** |
| **16 ESLint errors** | Mostly `no-explicit-any` and `react-hooks/set-state-in-effect`. They do not fail the production build. Don't run `npm run lint` on stage. |
| **No CI workflow** | `.github/workflows/` does not exist yet. |

---

## 2. Day-Before Checklist

### Downloads that need real internet — do these at home

- [ ] **Embedding model (~90 MB).** RAG silently returns empty results without it.
      Pre-warm the cache so it is never fetched live:
      ```bash
      python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
      ```
      It lands in `~/.cache/huggingface/`. Confirm that directory is non-empty.

- [ ] **Docker images.** Pre-pull so `up` doesn't stall:
      ```bash
      docker compose pull
      docker compose --profile full build
      ```

- [ ] **Python + Node dependencies** (see §3).

### Accounts and files

- [ ] `.env` exists at the repo root (`cp .env.example .env`).
- [ ] `docker compose config -q` exits silently.
- [ ] Repo is on the branch you intend to demo, and it is pushed.

### Rehearsal

- [ ] Run §4 from a cold boot, timed. Target: under 5 minutes to a usable UI.
- [ ] Walk §7 once end-to-end without notes.
- [ ] **Record a backup video** of the full flow. If the live demo fails, you play this.

---

## 3. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Docker Desktop | 24+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| Node.js | 20+ LTS | `node --version` |
| Python | 3.11+ | `python --version` |
| Git | any recent | `git --version` |

Free ports: **3000** (frontend), **8000** (backend), **8001** (AI inference),
**5433** (Postgres), **6379** (Redis), **6333/6334** (Qdrant).

```bash
# Linux/macOS — anything printed here is a conflict to resolve
lsof -i :3000 -i :8000 -i :8001 -i :5433 -i :6379 -i :6333
# Windows PowerShell
netstat -ano | findstr "3000 8000 8001 5433 6379 6333"
```

### Install dependencies

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# AI (CPU-only laptops: install torch from the CPU index first — saves ~2.5GB)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r ai/requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

---

## 4. Run Order

Order matters: data stores → migrations → AI → backend → frontend.

### Path A — Everything in Docker (fewest moving parts, best for the demo)

```bash
cp .env.example .env
docker compose --profile full up -d --build

# Wait for health, then create the schema (once per fresh volume)
docker compose exec backend alembic upgrade head
```

Stop with `docker compose --profile full down`. Add `-v` to also wipe the data
volumes and start clean.

### Path B — Data stores in Docker, apps on the host (easier to show logs and edit live)

```bash
# Terminal 0 — data stores
cp .env.example .env
docker compose up -d postgres redis qdrant

# Terminal 1 — backend
cd backend && source venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 2 — AI inference server (from the repo root)
uvicorn ai.src.inference.server:app --reload --port 8001

# Terminal 3 — frontend
cd frontend && npm run dev
```

> **Why `.env` says `POSTGRES_PORT=5433`:** Compose publishes Postgres on 5433 so it
> cannot collide with a Postgres already installed on the host. Inside Docker the
> backend talks to `postgres:5432`, which `docker-compose.yml` sets for you — so the
> same `.env` works for both paths. Don't "fix" the 5433.

### Optional — Nginx reverse proxy (HTTPS on :443)

```bash
bash infra/nginx/ssl/generate-ssl.sh          # Windows: generate-ssl.ps1
docker compose --profile full --profile proxy up -d
```

Self-signed certificate ⇒ the browser shows a warning. **Skip this in a live demo**
unless HTTPS/load balancing is specifically part of what you're presenting.

---

## 5. Seed the demo data

Empty screens demo badly. Seed before you present.

```bash
cd backend && source venv/bin/activate

# Prompt template library → Qdrant (500+ patterns; powers RAG retrieval)
python -m scripts.seed_prompt_patterns

# Demo users, chat sessions and messages
python -m scripts.seed_data

# Optional: mock RLHF feedback pairs, so the analytics page has numbers
python -m app.scripts.seed_dpo_feedback
```

To start over, prefer wiping the volumes so Alembic and the schema stay in sync:

```bash
docker compose --profile full down -v
docker compose up -d postgres redis qdrant
cd backend && alembic upgrade head    # then re-seed
```

`python -m app.scripts.reset_db` also works — it drops and recreates every table
directly — but it bypasses Alembic, so the `alembic_version` table is left stale.
Fine for a quick reset, not before a migration.

> Seeding prompt patterns loads the embedding model. If §2 was skipped, this is
> where it downloads 90 MB — do not discover that on stage.

---

## 6. Pre-flight verification

Run all of these immediately before presenting. Every one should pass.

```bash
# 1. Containers up and healthy
docker compose ps

# 2. Backend alive
curl http://localhost:8000/api/v1/health
# → {"status":"ok",...}

# 3. AI inference alive
curl http://localhost:8001/health
# → {"status":"degraded (mock mode)"}  ← expected without a checkpoint
# → {"status":"healthy","model":{...}} ← with a checkpoint loaded

# 4. Qdrant collections exist and are populated
curl http://localhost:6333/collections

# 5. Full round trip through the API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"DemoPass123!","full_name":"Demo User"}'
# → 201 with a user object
```

Browser checks:

- [ ] http://localhost:3000 — landing page renders **with colours** (not black-on-black)
- [ ] http://localhost:8000/docs — Swagger lists 23 endpoints
- [ ] http://localhost:6333/dashboard — Qdrant UI loads

Backend test suite (nice to be able to show):

```bash
cd backend && python -m pytest tests/ --ignore=tests/load -q
# → 67 passed
```

---

## 7. Demo Script

Roughly 6–8 minutes. Keep the browser at 100% zoom and hide bookmarks.

| # | Step | What to say |
|---|---|---|
| 1 | Landing page (`/`) | The problem: vague prompts → mediocre AI output. |
| 2 | Register (`/register`) | Password rules are enforced server-side; bcrypt hashing, never plaintext. |
| 3 | Onboarding (`/onboarding`) | Pick tone, verbosity, domain, target model — this is what personalises RAG. |
| 4 | Dashboard chat | Type a deliberately vague prompt: *"write me a marketing email"*. |
| 5 | Watch it stream | Tokens arrive over a WebSocket, not one blocking response. |
| 6 | Comparison view | Before/after side by side. Point at the added role, constraints and format. |
| 7 | Thumbs up/down | This feeds the DPO retraining pipeline — the model improves from real usage. |
| 8 | Preferences (`/dashboard/preferences`) | Change tone → re-run the same prompt → different output. **This is the RAG payoff; don't rush it.** |
| 9 | History (`/dashboard/history`) | Sessions persist in Postgres; embeddings in Qdrant. |
| 10 | Analytics (`/dashboard/analytics`) | Feedback stats and A/B experiment results. |
| 11 | Theme toggle | Dark/light, bespoke design system — not a template. |
| 12 | Swagger (`/docs`) | 23 documented endpoints, live try-it-out. Good place to end. |

**If you have a trained checkpoint**, drop it at
`ai/models/checkpoints/final_model.pt` (plus the tokenizer at
`ai/models/tokenizer/`) and restart the AI server. `/health` flips from
`degraded (mock mode)` to `healthy` — worth showing on screen.

**If you don't**, say so at step 4 before anyone notices the `MOCK:` prefix:
*"the model checkpoint isn't loaded on this machine, so the AI server is serving
labelled mock responses — everything around it is live."* Owning it reads as
rigour; being caught reads as a bug.

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Page loads but is unstyled / black-on-black | Stale `.next` build from before the CSS variable fix | `rm -rf frontend/.next && npm run dev` |
| `MOCK:` prefix on every response | No checkpoint at `ai/models/checkpoints/final_model.pt` | Expected. See §7. |
| Login returns 500 | Old `passlib`/`bcrypt` install in the venv | `pip install -r backend/requirements.txt --force-reinstall` |
| `ModuleNotFoundError: ai.src...` | AI server started from the wrong directory | Run `uvicorn ai.src.inference.server:app` **from the repo root** |
| Backend can't reach Postgres | Wrong port | Host runs use `5433`; containers use `postgres:5432` |
| `relation "users" does not exist` | Migrations never applied | `alembic upgrade head` |
| Frontend calls 404 | `NEXT_PUBLIC_API_URL` missing the `/api/v1` suffix | Must be `http://localhost:8000/api/v1`; **rebuild** after changing — it's inlined at build time |
| RAG returns nothing | Qdrant empty, or embedding model missing | `python -m scripts.seed_prompt_patterns`; check `~/.cache/huggingface/` |
| Rate limited (429) | 50 req/min per user or IP | Wait a minute, or `docker compose restart redis` |
| Nginx restart loop | Missing TLS certs | `bash infra/nginx/ssl/generate-ssl.sh`, or drop the `proxy` profile |
| Port already in use | Another process | See the port check in §3 |
| Everything is wedged | — | `docker compose --profile full down -v && docker compose --profile full up -d --build`, then re-migrate and re-seed |

### Reading logs fast

```bash
docker compose logs -f backend          # or: frontend, ai-inference, celery-worker
docker compose ps                       # health status of every service
```

---

## 9. Optional extras

Only if they're part of what you're presenting.

**Celery worker** (embeddings, nightly DPO retraining) — included in the `full`
profile. On the host:

```bash
cd backend && celery -A app.core.celery_app worker --loglevel=info
```

**Load test** (throughput numbers for the report):

```bash
cd backend
locust -f tests/load/locustfile.py --host http://localhost:8000
# → http://localhost:8089
```

**Multi-node / load-balanced setup** — see
[`infrastructure.md`](./infrastructure.md) and [`network-setup.md`](./network-setup.md),
plus `docker-compose.node-a.yml`, `docker-compose.node-b.yml`, `docker-compose.lb.yml`.
This needs several machines on one LAN with static IPs. **Not a laptop demo.**

---

## 10. Still to do by hand

Tracked in [`../project-docs/manual_tasks_remaining.md`](../project-docs/manual_tasks_remaining.md).
The ones that gate a good demo, in priority order:

1. **Record the backup demo video** — the single highest-value hour you can spend.
2. **Train (or obtain) a model checkpoint + tokenizer** — the only thing standing
   between a mock demo and a real one.
3. **Presentation slides** — architecture diagram from
   [`architecture.md`](./architecture.md), model details from
   [`model-card.md`](./model-card.md).
4. **Human evaluation of 50 DPO samples** — needed for the results section.
5. **Rehearse the Q&A**: *why a custom model instead of GPT-4? how does DPO help?
   what's the scalability ceiling? how do you handle malicious prompts?*
