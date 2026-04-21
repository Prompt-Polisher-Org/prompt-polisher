# 📖 Prompt Polisher — The Complete Beginner's Walkthrough

> **Who is this for?** If you've never built a production system, never trained an AI model, or never set up a server — this document is for you. It explains **every single concept** from the ground up, **why** we're doing each step, and **how it connects** to everything else.

> **How to read this**: Go section by section. Each concept has:
> - 🧠 **What is it?** — Plain English explanation
> - 🤔 **Why do we need it?** — Why it matters for Prompt Polisher
> - 🔗 **How does it connect?** — What it links to in the bigger system
> - 🛠️ **How to actually do it** — Step-by-step instructions
> - 📚 **Learn more** — Links to tutorials

---

## Table of Contents

1. [The Big Picture — What Are We Actually Building?](#1-the-big-picture)
2. [Understanding the Tech Stack — Why Each Tool Exists](#2-understanding-the-tech-stack)
3. [Week 1–2 Deep Dive: Foundation](#3-week-12-deep-dive-foundation)
4. [Week 3–4 Deep Dive: Authentication & Database](#4-week-34-deep-dive-authentication--database)
5. [Week 5–6 Deep Dive: AI Model & Inference](#5-week-56-deep-dive-ai-model--inference)
6. [Week 7–8 Deep Dive: RAG Pipeline](#6-week-78-deep-dive-rag-pipeline)
7. [Week 9–10 Deep Dive: System Integration & Multi-Node](#7-week-910-deep-dive-system-integration)
8. [Week 11–12 Deep Dive: RLHF & Optimization](#8-week-1112-deep-dive-rlhf--optimization)
9. [Week 13–14 Deep Dive: Polish, Load Test & Deploy](#9-week-1314-deep-dive-polish--deploy)
10. [Glossary — Every Term Explained](#10-glossary)

---

# 1. The Big Picture

## What Are We Building?

Imagine you want to ask ChatGPT a question. The quality of the answer depends **heavily** on how well you write your prompt. Most people write vague, poorly structured prompts and get mediocre answers.

**Prompt Polisher** is a tool that takes a user's rough prompt and transforms it into an expertly crafted one. Think of it as **Grammarly, but for AI prompts**.

```
USER TYPES:  "Write me a marketing email"

PROMPT POLISHER GENERATES:
"Act as a senior email marketing strategist with 10 years of experience 
in B2B SaaS. Write a compelling cold outreach email for [product]. 
The email should: (1) Open with a personalized hook referencing the 
recipient's industry pain point, (2) Present value proposition in 
under 3 sentences, (3) Include a clear, low-commitment CTA. 
Tone: Professional yet conversational. Length: Under 150 words."
```

The user then copies that optimized prompt and pastes it into ChatGPT/Gemini/Claude to get a **dramatically better response**.

## What Makes It Special?

1. **It remembers you** — Through RAG (Retrieval Augmented Generation), it remembers your preferences, past prompts, and writing style
2. **It learns from feedback** — Through RLHF, the model gets smarter every time a user says "I liked this" or "I didn't like this"
3. **It's OUR model** — We're not calling OpenAI's API. We built and trained our own AI model from scratch
4. **It scales** — We designed it to handle 10,000 users with load balancing across multiple servers

## The User Journey (Step by Step)

```
1. User visits promptpolisher.dev
2. User creates an account (or logs in with Google/GitHub)
3. First-time users go through an onboarding wizard:
   - "What tone do you prefer?" → Professional / Casual / Academic
   - "How detailed should prompts be?" → Concise / Detailed
   - "Which AI do you primarily use?" → ChatGPT / Gemini / Claude
   - "What domain?" → Marketing / Coding / Writing / General
4. User lands on the Dashboard
5. User opens a new Chat session
6. User types their rough prompt
7. Behind the scenes:
   a. System retrieves user's preferences from Vector DB
   b. System retrieves relevant past conversations from Vector DB
   c. System retrieves proven prompt patterns from Vector DB
   d. All this context is combined with the user's prompt
   e. Our custom AI model generates an optimized prompt
   f. Tokens stream back to the UI in real-time (like ChatGPT's typing effect)
8. User sees the optimized prompt appear word by word
9. User clicks "Copy" to copy it to clipboard
10. User pastes into ChatGPT/Gemini/Claude
11. User gives feedback (thumbs up/down) on the quality
12. That feedback is used to make the model smarter over time
```

---

# 2. Understanding the Tech Stack — Why Each Tool Exists

## 2.1 Frontend: Next.js 14

### 🧠 What is it?
Next.js is a **React framework** built by Vercel. React is a JavaScript library for building user interfaces. Next.js adds server-side rendering, routing, API routes, and many optimizations on top of React.

### 🤔 Why not just plain React?
Plain React (Create React App) gives you a "Single Page Application" — the browser downloads one big JavaScript file and renders everything client-side. This is:
- **Slow for initial load** (user sees a blank page while JS downloads)
- **Bad for SEO** (search engines can't easily read it)
- **No built-in routing** (you need react-router)

Next.js 14 with App Router gives us:
- **Server Components** — Pages render on the server, so users see content instantly
- **File-based routing** — Create a file at `app/dashboard/page.tsx`, and you automatically get the route `/dashboard`
- **API routes** — We can write simple backend endpoints directly in Next.js (useful for BFF — Backend For Frontend)
- **Streaming** — Pages can stream content progressively, perfect for our AI token streaming

### 🔗 How does it connect?
```
User's Browser
    ↓ loads
Next.js Frontend (JavaScript running in browser)
    ↓ makes HTTP requests to
FastAPI Backend (Python server)
    ↓ which talks to
AI Model, Database, Vector DB, etc.
```

### 🛠️ How to set it up
```bash
# Install Node.js first (download from nodejs.org, LTS version)
# Verify installation:
node --version    # Should show v20.x or v22.x
npm --version     # Should show 10.x

# Create the Next.js project:
npx -y create-next-app@latest frontend --typescript --eslint --app --src-dir --no-tailwind

# Move into the project:
cd frontend

# Start the dev server:
npm run dev
# Open http://localhost:3000 — you should see the Next.js welcome page!
```

### 📚 Learn more
- [Next.js Docs](https://nextjs.org/docs) — Official docs, start here
- [React Tutorial](https://react.dev/learn) — If you're new to React itself

---

## 2.2 Styling: SCSS Modules (Not Tailwind, Not Bootstrap)

### 🧠 What is it?
SCSS (Sassy CSS) is a **superset of CSS** — meaning all valid CSS is valid SCSS, but SCSS adds extra features:
- **Variables**: `$primary-color: #6C63FF;`
- **Nesting**: Write CSS rules inside each other instead of repeating selectors
- **Mixins**: Reusable chunks of CSS (like functions)
- **Partials**: Split CSS into multiple files and import them

CSS Modules means each component gets its own **scoped** CSS file. Styles in `Button.module.scss` can't accidentally affect other components.

### 🤔 Why not Tailwind or Bootstrap?
- **Bootstrap**: Makes every website look the same. We want a **bespoke, unique** UI
- **Tailwind**: Utility-first CSS (you write `className="bg-blue-500 p-4 rounded-lg"` instead of actual CSS). It's powerful but produces HTML that's hard to read and limits creative control

With SCSS Modules, we have **100% control** over every pixel. This is how premium products (Linear, Vercel, Stripe) build their UIs.

### 🔗 How does it connect?
```
_variables.scss  ← Global design tokens (colors, fonts, spacing)
    ↓ imported by
_mixins.scss     ← Reusable CSS patterns
    ↓ imported by
Button.module.scss ← Specific component styles
    ↓ used by
Button.tsx         ← React component
```

### 🛠️ Example
```scss
// styles/_variables.scss
$color-primary: #6C63FF;
$color-bg-dark: #0A0A0F;
$color-surface: rgba(255, 255, 255, 0.05);
$font-main: 'Inter', sans-serif;
$radius-md: 12px;

// components/Button/Button.module.scss
@use '../../styles/variables' as *;

.button {
  background: $color-primary;
  font-family: $font-main;
  border-radius: $radius-md;
  padding: 12px 24px;
  border: none;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba($color-primary, 0.4);
  }
}
```

```tsx
// components/Button/Button.tsx
import styles from './Button.module.scss';

export function Button({ children, onClick }) {
  return (
    <button className={styles.button} onClick={onClick}>
      {children}
    </button>
  );
}
```

---

## 2.3 Animations: Framer Motion + GSAP

### 🧠 What are they?

**Framer Motion** is a React animation library. You wrap elements in `<motion.div>` and declare how they should animate:

```tsx
import { motion } from 'framer-motion';

// This div fades in and slides up when it appears
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
  Hello World
</motion.div>
```

**GSAP** (GreenSock Animation Platform) is for **complex timeline animations** — things like scroll-triggered effects, SVG morphing, parallax backgrounds. It's lower-level but more powerful.

### 🤔 Why both?
- **Framer Motion**: Simple component animations (fade in, slide, layout) — 90% of our animations
- **GSAP**: Landing page hero section, particle effects, scroll-triggered reveals — 10% of our animations

### 🔗 How does it connect?
Animations are purely visual — they don't affect the backend or AI. They make the difference between a "student project" and a "product that looks like it cost $50K to build."

---

## 2.4 Backend: FastAPI (Python)

### 🧠 What is it?
FastAPI is a **Python web framework** for building APIs. An API (Application Programming Interface) is a set of URLs that accept requests and return data. When the frontend needs user data, it sends a request to the backend API, and the backend responds with JSON data.

### 🤔 Why FastAPI and not Express.js (Node), Django, or Flask?

| Framework | Language | Why We Didn't Pick It |
|---|---|---|
| Express.js | JavaScript | Our AI model is in Python. We'd need two languages |
| Django | Python | Too heavy/opinionated, REST framework is slow |
| Flask | Python | No async support, no built-in validation |
| **FastAPI** | **Python** | ✅ Async, auto-docs, validation, same language as AI code |

The killer feature: **FastAPI is Python, and our AI model is Python**. No language boundary means the backend can directly import and call the model's inference code.

### 🔗 How does it connect?
```
Frontend (Next.js) 
    ↓ sends HTTP request: POST /api/v1/inference/generate {prompt: "..."}
    ↓
Nginx Load Balancer 
    ↓ forwards to one of the backend servers
    ↓
FastAPI Backend
    ↓ validates request (Pydantic)
    ↓ checks authentication (JWT)
    ↓ checks rate limit (Redis)
    ↓ retrieves context (Qdrant Vector DB)
    ↓ calls AI model (PyTorch)
    ↓ saves message (PostgreSQL)
    ↓ returns response
    ↓
Frontend displays the optimized prompt
```

### 🛠️ How to set it up
```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install FastAPI + dependencies:
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings python-jose[cryptography] passlib[bcrypt] redis celery

# Create app/main.py:
```

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Prompt Polisher API", version="1.0.0")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "prompt-polisher-api"}

# Run with: uvicorn app.main:app --reload --port 8000
# Visit: http://localhost:8000/docs → You'll see Swagger UI!
```

---

## 2.5 Database: PostgreSQL

### 🧠 What is it?
PostgreSQL (Postgres) is a **relational database** — it stores data in tables with rows and columns, like an Excel spreadsheet but much more powerful. Each table has a defined structure (schema).

```
USERS TABLE
┌────┬───────────────────┬──────────────────────────┬─────────────┐
│ id │ email             │ password_hash            │ created_at  │
├────┼───────────────────┼──────────────────────────┼─────────────┤
│ 1  │ alice@example.com │ $2b$12$LJ3m5... (hash)  │ 2026-05-01  │
│ 2  │ bob@example.com   │ $2b$12$Kx8p2... (hash)  │ 2026-05-02  │
└────┴───────────────────┴──────────────────────────┴─────────────┘
```

### 🤔 Why do we need it?
We need to permanently store:
- **User accounts** (email, password, profile info)
- **User preferences** (tone, verbosity, target model)
- **Chat sessions** (who started the chat, when)
- **Messages** (every prompt and response)
- **Feedback** (thumbs up/down ratings)

### 🤔 Why PostgreSQL and not MySQL or MongoDB?
- **MySQL**: Less feature-rich, no native JSON support
- **MongoDB**: NoSQL (no tables/relations) — great for unstructured data, but our data IS structured (users HAVE preferences, sessions HAVE messages). Relational databases model this perfectly
- **PostgreSQL**: Best of both worlds — relational tables + JSONB for flexible fields, extremely reliable, industry standard

### 🔗 How does it connect?
```
FastAPI Backend
    ↓ uses SQLAlchemy ORM (Object-Relational Mapper)
    ↓ which converts Python objects to SQL queries
    ↓
PostgreSQL Database
    ↓ stores data on disk
    ↓ returns results to SQLAlchemy
    ↓
FastAPI sends data back to Frontend as JSON
```

### 🧠 What is an ORM (SQLAlchemy)?
Instead of writing raw SQL:
```sql
SELECT * FROM users WHERE email = 'alice@example.com';
```

You write Python:
```python
user = await session.execute(
    select(User).where(User.email == "alice@example.com")
)
```

SQLAlchemy translates your Python code into SQL automatically. This is safer (prevents SQL injection) and more maintainable.

### 🧠 What are Migrations (Alembic)?
When you change your database schema (add a column, rename a table), you can't just edit the code — you need to **tell PostgreSQL** about the change. Alembic creates **migration scripts** — versioned Python files that describe each change:

```python
# migrations/0001_add_users_table.py
def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), unique=True),
        ...
    )

def downgrade():
    op.drop_table('users')
```

You run `alembic upgrade head` to apply all migrations. This way, every team member's database stays in sync.

---

## 2.6 Vector Database: Qdrant

### 🧠 What is it?
A **regular database** (PostgreSQL) stores data and lets you search by exact values ("find user with email = X"). A **vector database** stores data as **numerical vectors** (arrays of numbers) and lets you search by **similarity**.

### 🧠 What is a Vector/Embedding?
An **embedding** is a way to represent text as a list of numbers that capture its **meaning**. Similar texts get similar numbers:

```
"Write a marketing email" → [0.23, -0.41, 0.89, 0.15, ..., -0.33]  (384 numbers)
"Draft a promotional message" → [0.21, -0.38, 0.87, 0.18, ..., -0.31]  (very similar numbers!)
"Fix the Python bug" → [-0.55, 0.72, -0.11, 0.63, ..., 0.44]  (very different numbers!)
```

When you search a vector database, you give it a vector and it finds the **closest vectors** — meaning the most **semantically similar** texts.

### 🤔 Why do we need this?
This is the core of our **RAG (Retrieval Augmented Generation)** system. When a user types a new prompt:

1. We convert it to a vector
2. We search Qdrant for similar past conversations (from this user)
3. We search for similar proven prompt patterns
4. We inject this context into our model's prompt

This is how the system **"remembers"** past interactions and gets better at personalization.

### 🤔 Why Qdrant and not Pinecone or ChromaDB?
- **Pinecone**: Cloud-only, costs money — we need self-hosted for our laptop setup
- **ChromaDB**: Simple but slow at scale, limited filtering
- **Qdrant**: Written in Rust (fast), self-hosted via Docker (free), great filtering, excellent Python SDK

### 🔗 How does it connect?
```
User types: "Write me a marketing email for my SaaS product"
    ↓
Embedding Model (SentenceTransformer) converts text to 384 numbers
    ↓
Qdrant searches for similar vectors in 3 collections:
    1. user_preferences → finds: "User prefers professional tone, target: GPT-4"
    2. chat_history → finds: "2 days ago user asked for a product launch email"
    3. prompt_patterns → finds: "Best pattern for marketing emails"
    ↓
All this context is combined with the user's original prompt
    ↓
Our custom AI model generates a better optimized prompt
```

### 🛠️ How to run it (Docker)
```bash
# Pull and run Qdrant:
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# That's it! Qdrant is now running at http://localhost:6333
# You can see the web UI at http://localhost:6333/dashboard
```

---

## 2.7 Caching: Redis

### 🧠 What is it?
Redis is an **in-memory data store** — it stores data in RAM instead of on disk. This makes it extremely fast (microseconds vs. milliseconds for PostgreSQL).

### 🤔 Why do we need it?
We use Redis for **three different purposes**:

| Purpose | How It Works | Why It Matters |
|---|---|---|
| **Session Cache** | Store user's JWT session data in Redis | Faster than hitting PostgreSQL for every request |
| **Rate Limiting** | Track how many requests each user has made | Prevent abuse (50 requests/minute/user) |
| **Result Caching** | Cache generated prompts by their input hash | If someone asks the same thing twice, return cached result instantly instead of running the model again |
| **Celery Broker** | Redis acts as the message queue for Celery tasks | Backend says "generate a prompt" → Redis holds the message → Celery worker picks it up |

### 🔗 How does it connect?
```
Frontend sends request
    ↓
FastAPI checks Redis: "Has this user exceeded 50 req/min?" 
    ↓ (if no)
FastAPI checks Redis: "Is this exact prompt cached?"
    ↓ (if cache miss)
FastAPI puts inference task into Redis queue
    ↓
Celery worker reads from Redis queue → runs model → stores result in Redis
    ↓
FastAPI reads result from Redis → returns to frontend
```

---

## 2.8 Task Queue: Celery

### 🧠 What is it?
Celery is a **distributed task queue**. It lets you run heavy/slow tasks **in the background** instead of making the user wait.

### 🤔 Why do we need it?
Running our AI model takes 2-10 seconds. If the FastAPI server runs the model directly:
- The server is **blocked** — it can't handle any other requests while the model runs
- With 100 users, the server would need 100 threads all running models simultaneously → it would crash

With Celery:
1. FastAPI receives request: "Generate a prompt"
2. FastAPI puts a **task message** into Redis: "Hey, someone needs a prompt generated"
3. FastAPI **immediately** returns to handle the next request
4. A separate **Celery worker process** picks up the task from Redis
5. The worker runs the model
6. The worker puts the result back into Redis
7. FastAPI picks up the result and streams it to the user via WebSocket

```
WITHOUT CELERY:
FastAPI ──── [runs model 5 seconds] ──── responds
              (server is BLOCKED, can't serve anyone else)

WITH CELERY:
FastAPI ──── dispatches task ──── immediately free!
                    ↓
Celery Worker ──── [runs model 5 seconds] ──── puts result in Redis
                                                     ↓
FastAPI ──── reads result ──── sends to user
```

### 🔗 How does it connect?
Celery **workers** run on the **same laptops as the backends** (Laptop 2 and 3). Each worker process loads the AI model into memory and waits for tasks. When a task comes through Redis, the worker runs the model and returns the result.

---

## 2.9 Load Balancer: Nginx

### 🧠 What is it?
Nginx (pronounced "engine-X") is a **web server** and **reverse proxy**. A reverse proxy sits **in front of** your backend servers and distributes incoming requests among them.

### 🤔 Why do we need it?
We have **two backend servers** (Laptop 2 and Laptop 3). Without a load balancer, the user would need to know which server to connect to. With Nginx:

```
WITHOUT NGINX:
User → "Hmm, should I connect to Laptop 2 or Laptop 3?"

WITH NGINX:
User → Nginx (one address: promptpolisher.local) → Nginx picks the best server
```

### 🧠 Load Balancing Strategies

| Strategy | How It Works | When to Use |
|---|---|---|
| **Round Robin** | Request 1 → Server A, Request 2 → Server B, Request 3 → Server A... | Default, works for stateless APIs |
| **Least Connections** | Send to whichever server has fewer active connections | ✅ Best for our API (inference takes variable time) |
| **IP Hash** | Same user IP always goes to same server | ✅ Best for WebSockets (connection must be persistent) |

We use **least_conn** for REST API requests and **ip_hash** for WebSocket connections.

### 🔗 How does it connect?
```
Laptop 4 (User's Browser)
    ↓ connects to
Laptop 1 (Nginx) — listening on port 80/443
    ↓ forwards /api/* requests to
Laptop 2 (Backend A on port 8000) OR Laptop 3 (Backend B on port 8000)
    ↓ forwards /ws/* requests to
Laptop 2 (WS on port 8001) OR Laptop 3 (WS on port 8001) — sticky session
```

---

## 2.10 The AI Model: Custom Small Language Model (SLM)

### 🧠 What is a Language Model?
A language model is a neural network trained to **predict the next word** given previous words. When you train it on billions of words, it learns grammar, facts, reasoning, and writing style. ChatGPT, Gemini, and Claude are all language models.

### 🧠 What is "Small" Language Model?
| Model | Parameters | Size | Runs On |
|---|---|---|---|
| GPT-4 | ~1.7 Trillion | ~3TB | Massive GPU clusters |
| LLaMA 70B | 70 Billion | ~140GB | Enterprise GPUs |
| LLaMA 7B | 7 Billion | ~14GB | High-end consumer GPU |
| **Our Model** | **~125-350 Million** | **~500MB-1.5GB** | ✅ **Regular laptop CPU/GPU** |

Our model is tiny compared to ChatGPT, but it's **specialized**: it only needs to do ONE thing — optimize prompts. A specialist can be small and still be great at their specific task.

### 🧠 What is a Tokenizer?
Before text goes into a model, it must be converted to numbers. A **tokenizer** splits text into **tokens** (sub-word units) and maps each to a number:

```
"Hello, how are you?" 
    ↓ tokenizer
["Hello", ",", " how", " are", " you", "?"]
    ↓ vocabulary lookup
[15496, 11, 703, 389, 345, 30]
```

We train our own tokenizer using **SentencePiece BPE (Byte-Pair Encoding)**. This algorithm:
1. Starts with individual characters as tokens
2. Repeatedly merges the most common pair of adjacent tokens
3. Continues until vocabulary reaches desired size (32,000 tokens)

Training our own tokenizer means it's optimized for **prompt engineering vocabulary** — words like "persona", "chain-of-thought", "delimiters" get their own tokens instead of being split unnaturally.

### 🧠 What is a Transformer?
The **transformer architecture** is the foundation of all modern language models. Key components:

```
INPUT TOKENS: [15496, 11, 703, 389, 345, 30]
         ↓
┌─────────────────────────────┐
│  TOKEN EMBEDDINGS           │  ← Convert each number to a 768-dimensional vector
│  + POSITION EMBEDDINGS      │  ← Add information about token position
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  TRANSFORMER BLOCK (×12)    │  ← Repeated 12 times (12 layers)
│  ┌───────────────────────┐  │
│  │ SELF-ATTENTION        │  │  ← "Which other tokens should I focus on?"
│  │ (Multi-Head, Causal)  │  │     Each token looks at all PREVIOUS tokens
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ FEED-FORWARD NETWORK  │  │  ← Process each token independently through MLPs
│  └───────────────────────┘  │
│  + Residual Connections     │  ← Add the input back (prevents vanishing gradients)
│  + Layer Normalization      │  ← Stabilize training
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  OUTPUT HEAD (Linear layer) │  ← Convert 768-dim vector back to vocabulary probabilities
└─────────────────────────────┘
         ↓
PREDICTED NEXT TOKEN: [15496]  → "Hello"
```

**Self-Attention** is the magic: each token can "look at" every other token in the sequence and decide how much to pay attention to each one. "The cat sat on the ___" — the model attends strongly to "cat" and "sat" to predict "mat".

### 🔗 How does it connect to the bigger system?

```
User's prompt + RAG context (from Qdrant)
    ↓ tokenized by our custom SentencePiece tokenizer
    ↓
Token IDs fed into our Transformer model
    ↓
Model generates new tokens one at a time (autoregressive)
    ↓ each token is sent via WebSocket
    ↓
Frontend displays tokens as they arrive (typewriter effect)
```

### Training Phases (Explained Simply)

**Phase 1 — Pre-training** (Optional if using pretrained base):
- Feed the model billions of words of text
- It learns: grammar, word relationships, general knowledge
- Like teaching a child to read

**Phase 2 — Supervised Fine-Tuning (SFT)**:
- Show the model thousands of (bad_prompt → good_prompt) examples
- It learns: "When I see a vague prompt, here's how to make it better"
- Like teaching a student with example answers

**Phase 3 — RLHF/DPO Alignment**:
- Real users rate the model's outputs (thumbs up/down)
- The model learns which outputs humans prefer
- Like a tutor improving based on student satisfaction
- **This is what makes our model smarter over time!**

---

## 2.11 WebSockets — Real-time Streaming

### 🧠 What is it?
Normal HTTP is **request-response**: browser sends request → server sends response → connection closes. WebSocket is a **persistent, two-way connection**: once opened, both sides can send messages at any time.

### 🤔 Why do we need it?
When our model generates a response, it produces **one token at a time** — like someone typing. With regular HTTP, we'd have to wait for the ENTIRE response to be generated (5-10 seconds) and then send it all at once.

With WebSockets, we can **stream tokens as they're generated**, so the user sees text appearing word-by-word — just like ChatGPT's typing effect. This makes the app feel **fast and alive** even though the model is still generating.

### 🔗 How does it connect?
```
Browser opens WebSocket: ws://promptpolisher.local/ws/stream/session123
    ↕  (connection stays open)
Backend generates token → sends via WebSocket: {"token": "Act"}
Backend generates token → sends via WebSocket: {"token": " as"}
Backend generates token → sends via WebSocket: {"token": " a"}
Backend generates token → sends via WebSocket: {"token": " senior"}
...
Backend sends: {"done": true}
    ↕
Browser closes WebSocket
```

---

## 2.12 Docker — Containerization

### 🧠 What is it?
Docker lets you package your application **along with all its dependencies** into a **container** — a lightweight, isolated environment. Think of it as a shipping container for software: no matter what ship (computer) carries it, the contents arrive the same.

### 🤔 Why do we need it?
Without Docker:
- "It works on my machine but not on yours" — different Python versions, missing libraries, etc.
- Setting up PostgreSQL, Redis, and Qdrant manually on each laptop is painful
- Each team member has a different OS (Windows/Mac/Linux)

With Docker:
```bash
docker compose up   # ← One command starts EVERYTHING
```
PostgreSQL, Redis, Qdrant, Backend, Frontend — all running in isolated containers with exact same versions across all 4 laptops.

### 🧠 What is Docker Compose?
Docker runs individual containers. Docker Compose lets you define **multiple containers** that work together:

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_PASSWORD: secretpassword

  redis:
    image: redis:7
    ports: ["6379:6379"]

  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis, qdrant]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
```

Run `docker compose up` and all 5 services start together, connected on the same network.

---

# 3. Week 1–2 Deep Dive: Foundation

## Why This Phase Matters
Every building needs a foundation. If your project structure is messy, your database can't be reached, or team members can't run the code — you'll waste weeks debugging environment issues instead of building features.

**Goal**: After Week 2, every team member runs ONE command and sees all services working.

## Task: Setting Up the Monorepo

### 🧠 What is a Monorepo?
A monorepo is a **single Git repository** containing all your project's code (frontend, backend, AI, infrastructure) instead of separate repos for each.

```
prompt-polisher/             ← One repo to rule them all
├── frontend/                ← Next.js web app
├── backend/                 ← FastAPI Python API
├── ai/                      ← Model training & inference
├── infra/                   ← Docker, Nginx, configs
├── docs/                    ← Documentation
├── docker-compose.yml       ← Start everything
├── .github/                 ← PR templates, CI/CD
└── README.md
```

### 🤔 Why a monorepo?
- **One PR can change frontend + backend together** (e.g., add a new API endpoint AND the UI that calls it)
- **Shared configuration** (Docker Compose, env vars, CI/CD)
- **Easier for a 4-person team** (one place to look for everything)

### 🔗 How does it connect to the future?
Week 3–4: Backend dev creates auth API → Frontend dev can immediately see the code and build the login page
Week 9–10: DevOps creates Docker Compose per laptop → references all code in the same repo

---

## Task: Design System (CSS Variables & Tokens)

### 🧠 What is a Design System?
A design system is a **set of rules and reusable components** that keep your UI consistent. Instead of each team member picking random colors and font sizes, everyone uses the same predefined values.

### 🤔 Why do we need it now?
If you build the login page with `color: #6C63FF` and later the dashboard uses `color: #7066FF`, your app looks inconsistent. Design tokens ensure **every page uses the exact same visual language**.

### 🛠️ What to define:
```scss
// Every color, font, spacing value used ANYWHERE in the app
// lives in this ONE file. Change it here = changes everywhere.

$color-primary: #6C63FF;        // Main brand purple
$color-primary-light: #8B83FF;  // Hover state
$color-primary-dark: #4A42CC;   // Active state
$color-accent: #00D9FF;         // Cyan accent for highlights
$color-bg-primary: #0A0A0F;     // Main background (dark)
$color-bg-surface: #12121A;     // Card/container background
$color-bg-elevated: #1A1A28;    // Elevated surfaces (modals)
$color-text-primary: #FFFFFF;   // Main text
$color-text-secondary: #8888AA; // Subdued text
$color-success: #00C853;        // Green for success states
$color-error: #FF1744;          // Red for error states

$font-sans: 'Inter', -apple-system, sans-serif;
$font-mono: 'JetBrains Mono', monospace;

$space-xs: 4px;
$space-sm: 8px;
$space-md: 16px;
$space-lg: 24px;
$space-xl: 32px;
$space-2xl: 48px;
$space-3xl: 64px;

$radius-sm: 6px;
$radius-md: 12px;
$radius-lg: 20px;
$radius-full: 9999px;  // Pill shape
```

### 🔗 How does it connect?
- **Week 3–4**: Login page uses these exact tokens for colors, spacing, and fonts
- **Week 5–6**: Chat UI uses the same tokens, so it visually matches
- **Week 7–8**: History page, preferences — all consistent
- **Week 13**: Dark/light mode toggle just swaps these token values

---

# 4. Week 3–4 Deep Dive: Authentication & Database

## Why This Phase Matters
Without auth, anyone can pretend to be anyone. Without a database, nothing is saved. These are the **absolute prerequisites** for every other feature.

## Concept: JWT Authentication

### 🧠 What is JWT?
JWT (JSON Web Token) is a way to prove "I am user X" without sending your password every time. It works like a concert wristband:

1. You show your ticket at the entrance (login with email + password)
2. Guard checks it's valid and gives you a wristband (JWT token)
3. Now you can enter any area by showing your wristband (attach JWT to every request)
4. The wristband expires at midnight (token has an expiration time)

A JWT token is a long encoded string that contains:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.     ← Header (algorithm)
eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFsaWNlQC... ← Payload (user data + expiry)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  ← Signature (proof it's not tampered with)
```

### 🧠 Access Token vs Refresh Token
- **Access Token**: Short-lived (30 minutes). Sent with every request. If stolen, attacker has limited time
- **Refresh Token**: Long-lived (7 days). Used ONLY to get a new access token when the old one expires. Never sent with regular requests

```
Login → Get {access_token (30 min), refresh_token (7 days)}
    ↓
Make requests with access_token in header: Authorization: Bearer eyJ...
    ↓ (after 30 minutes, access token expires)
Send refresh_token to /auth/refresh → Get new access_token
    ↓ (after 7 days, refresh token expires)
User must log in again
```

### 🔗 How does it connect?
- **Week 5–6**: Inference endpoint checks JWT to know WHO is asking for prompt generation
- **Week 7–8**: RAG uses user_id from JWT to retrieve only THAT user's history
- **Week 9–10**: Nginx passes JWT through to both backend nodes
- **Week 11–12**: Feedback is linked to user_id from JWT

---

## Concept: OAuth 2.0 (Login with Google/GitHub)

### 🧠 What is it?
Instead of creating a username/password, users click "Sign in with Google" and Google confirms their identity. Your app never sees their Google password.

### Flow:
```
1. User clicks "Sign in with Google"
2. Browser redirects to Google's login page
3. User logs in on Google's page
4. Google redirects back to YOUR app with an authorization code
5. Your backend exchanges that code for user info (email, name, avatar)
6. Your backend creates a user account (if new) and returns a JWT
```

### 🔗 How does it connect?
Same JWT system as password login. After OAuth, the user has a JWT and everything works identically.

---

# 5. Week 5–6 Deep Dive: AI Model & Inference

## Why This Phase Matters
This is the **core product**. Without a working AI model, Prompt Polisher is just a chat UI that does nothing.

## Concept: Training a Model from Scratch vs Fine-Tuning

### From Scratch
```
Random weights → Train on billions of tokens → Model learns language
Time: Weeks to months
Cost: Thousands of GPU hours
Result: A model that understands English
```

### Fine-Tuning (Recommended)
```
Pre-trained model (GPT-2 small, already knows English)
    ↓ + our specific dataset (bad prompts → good prompts)
    ↓ train for a few hours
Result: A model that's great at optimizing prompts
```

### 🔗 Why this matters for the project
Fine-tuning a pre-trained model is **realistic for a final year project**. Training from absolute scratch on consumer hardware would take too long and not converge well. Using a pre-trained base + custom tokenizer + SFT + RLHF is still a completely valid "custom model" — this is exactly how companies like Meta built Llama.

## Concept: KV-Cache for Fast Inference

### 🧠 What is it?
When generating text, the model produces one token at a time. For each new token, it needs to process ALL previous tokens again. The KV-cache stores the computations from previous tokens so they don't need to be recomputed.

```
WITHOUT KV-CACHE:
Token 1: Process [token1]                    → predict token2
Token 2: Process [token1, token2]            → predict token3
Token 3: Process [token1, token2, token3]    → predict token4
                  ↑ recalculated every time!

WITH KV-CACHE:
Token 1: Process [token1] → cache key/value  → predict token2
Token 2: Process [token2] + read cache       → predict token3  (5x faster!)
Token 3: Process [token3] + read cache       → predict token4  (even faster!)
```

### 🔗 How does it connect?
Faster inference → lower latency → better user experience. Without KV-cache, each prompt generation could take 30+ seconds. With it, we target under 5 seconds.

## Concept: INT8 Quantization

### 🧠 What is it?
By default, model weights are stored as 32-bit floating point numbers. Quantization converts them to 8-bit integers — making the model **4x smaller** and **2-3x faster**, with minimal quality loss.

```
FP32: 3.14159265 → stored as 32 bits (4 bytes)
INT8: 3          → stored as 8 bits (1 byte)

Model size: 500MB → 125MB
Speed: 5 seconds → 2 seconds
Quality: 98% of FP32 quality
```

### 🔗 How does it connect?
Our model needs to run on **regular laptops**, not GPU servers. Quantization makes this possible. Without it, the model might not even fit in memory or would be too slow for real-time streaming.

---

# 6. Week 7–8 Deep Dive: RAG Pipeline

## Why This Phase Matters
Without RAG, the model treats every user the same — it doesn't know your preferences, it doesn't remember past conversations. RAG is what makes the experience **personalized**.

## Concept: RAG (Retrieval Augmented Generation)

### 🧠 What is it? (The Restaurant Analogy)
Imagine a chef (our AI model) who forgets everything after each order:

**Without RAG**: "I'd like the usual" → Chef: "I don't know your usual. Here's something generic."

**With RAG**: 
1. Waiter (retrieval system) checks the **guest book** (vector database)
2. Finds: "This customer always orders spicy food, prefers vegan options, loved the Thai curry last time"
3. Gives this info to the chef along with the order
4. Chef now makes a **personalized** dish

In our system:
1. User types a prompt
2. **Retriever** searches Qdrant for relevant context
3. This context is **injected** into the system prompt
4. The model generates with full awareness of user preferences and history

### The Three Collections

```
COLLECTION 1: user_preferences
Purpose: "What kind of prompts does this user want?"
Example search result: "User prefers professional tone, targets GPT-4, domain: marketing"

COLLECTION 2: chat_history
Purpose: "What has this user asked about before?"
Example search result: "3 days ago, user asked for an email marketing prompt and liked the result"

COLLECTION 3: prompt_patterns
Purpose: "What are proven prompt formats for this type of task?"
Example search result: "For marketing emails, the AIDA pattern works best: Attention → Interest → Desire → Action"
```

### 🔗 How does it connect?

```
Week 3–4 (Foundation): User sets preferences → these are the RAW data
Week 5–6 (AI Model): Model can generate → but without context, outputs are generic
Week 7–8 (THIS WEEK): RAG adds context → outputs become personalized and high-quality
Week 11–12 (RLHF): User feedback improves what patterns are retrieved
```

---

# 7. Week 9–10 Deep Dive: System Integration

## Why This Phase Matters
Up until now, everyone has been working on their own laptop, testing locally. Now we connect all 4 laptops into a single working system. **This is where it becomes real.**

## Concept: The 4-Laptop Topology

### 🧠 Why 4 Laptops?
This simulates a real production deployment:

| Real World | Our Laptops |
|---|---|
| Cloud Load Balancer (AWS ALB) | Laptop 1 (Nginx) |
| App Server Instance 1 | Laptop 2 (Backend + AI Worker) |
| App Server Instance 2 | Laptop 3 (Backend + AI Worker) |
| User's Browser | Laptop 4 (Testing) |

This is a **proof of concept** for horizontal scaling. In the real world, you'd have dozens of server instances behind a load balancer.

### 🛠️ Setting Up the Network

```
Step 1: Connect all laptops to the SAME Wi-Fi or Ethernet switch
Step 2: Assign static IPs:
  - Laptop 1: Open Network Settings → IPv4 → Manual → 192.168.1.10
  - Laptop 2: ... → 192.168.1.20
  - Laptop 3: ... → 192.168.1.30
  - Laptop 4: ... → 192.168.1.40
Step 3: Verify connectivity:
  - From Laptop 4, run: ping 192.168.1.10
  - Should get responses
Step 4: Open firewall ports (Windows):
  - netsh advfirewall firewall add rule name="PromptPolisher" dir=in action=allow protocol=TCP localport=8000,8001,5432,6379,6333,80,443
```

### 🔗 How does it connect to the future?
Week 14 (Cloud Deploy): Replace the 4 laptops with 4 cloud VPS instances. The Docker Compose files and Nginx config remain **almost identical**. This is the power of containerization — your laptop setup IS your cloud setup.

## Concept: Health Checks & Failover

### 🧠 What happens when a server crashes?
Without health checks, Nginx would keep sending requests to a dead server → users get errors.

With health checks:
```
Every 10 seconds:
  Nginx → GET http://192.168.1.20:8000/api/v1/health → 200 OK ✅
  Nginx → GET http://192.168.1.30:8000/api/v1/health → Connection refused ❌

Nginx removes Laptop 3 from rotation.
ALL traffic now goes to Laptop 2 only.

Later:
  Nginx → GET http://192.168.1.30:8000/api/v1/health → 200 OK ✅
Nginx adds Laptop 3 back to rotation.
```

### 🔗 Why this matters
This is **high availability** — the system stays operational even when one server goes down. For a 10K-user SaaS, downtime = lost users = lost revenue.

---

# 8. Week 11–12 Deep Dive: RLHF & Optimization

## Why This Phase Matters
This is the most **academically impressive** part of your project. RLHF (Reinforcement Learning from Human Feedback) is how OpenAI made ChatGPT useful. Implementing even a basic version is a significant achievement.

## Concept: DPO (Direct Preference Optimization)

### 🧠 What is it? (Simplified)
DPO is a simpler alternative to full RLHF. Instead of training a separate reward model and doing complex PPO (Proximal Policy Optimization), DPO directly updates the model weights based on human preferences.

### The Data:
```
From user feedback, we collect triples:

PROMPT: "Optimize: Write me an email about product launch"
CHOSEN (👍): "Act as a product marketing manager. Craft a launch email..."
REJECTED (👎): "Write a good email for launching a product..."

The model learns: "CHOSEN is preferred over REJECTED for this type of prompt"
```

### The Training Loop:
```
1. Collect feedback until batch_size = 100
2. Format as (prompt, chosen, rejected) triples
3. Run DPO training:
   - Model sees both CHOSEN and REJECTED
   - Loss function pushes model to generate outputs more like CHOSEN
   - After training, model is slightly better at generating preferred outputs
4. Save new checkpoint: model_v2
5. Deploy model_v2 (keep model_v1 as fallback)
6. Repeat (continuous improvement cycle)
```

### 🔗 Why DPO over PPO?

| Aspect | PPO (Full RLHF) | DPO |
|---|---|---|
| Needs reward model? | Yes (train a separate model) | No |
| Training stability | Tricky (PPO is finicky) | Stable |
| Implementation complexity | Very high | Medium |
| Results quality | Slightly better | Very competitive |
| **Feasibility for us** | **Hard on consumer hardware** | ✅ **Achievable** |

### 🔗 How does it connect?
```
Week 11: Build feedback UI (thumbs up/down button)
    ↓
Backend stores feedback in PostgreSQL
    ↓
When 100 feedbacks accumulate → Celery triggers DPO training task
    ↓
DPO training runs on AI worker (30 min – 2 hours depending on data)
    ↓
New model checkpoint saved with version tag
    ↓
Backend starts using new model for future requests
    ↓
Users notice: "Hey, the prompts are getting better!"
    ↓
This is the continuous learning loop! 🔄
```

---

# 9. Week 13–14 Deep Dive: Polish & Deploy

## Why This Phase Matters
A system that works locally but can't handle real users is a demo, not a product. This phase proves it can **scale**.

## Concept: Load Testing with Locust

### 🧠 What is it?
Locust is a Python tool that simulates thousands of virtual users hitting your system simultaneously.

```python
# locustfile.py
from locust import HttpUser, task, between

class PromptPolisherUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        # Login when the virtual user "arrives"
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]

    @task(3)  # Weight: this task runs 3x more often
    def generate_prompt(self):
        self.client.post("/api/v1/inference/generate",
            json={"prompt": "Write me a marketing email"},
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def view_history(self):
        self.client.get("/api/v1/chat/sessions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

```bash
# Run with 1000 simulated users, spawning 50 per second
locust -f locustfile.py --host=http://192.168.1.10 --users 1000 --spawn-rate 50
```

### 🔗 What do the results tell you?

| Metric | Good | Concerning | Critical |
|---|---|---|---|
| **Requests/sec** | > 100 | 20–100 | < 20 |
| **p95 Latency** | < 2s | 2–5s | > 5s |
| **Error Rate** | < 1% | 1–5% | > 5% |

If metrics are bad, you need to optimize: add caching, optimize queries, increase worker count, or add more servers.

## Concept: Cloud Deployment

### 🧠 What changes from laptops to cloud?
Almost nothing! That's the beauty of Docker.

```
LAPTOP SETUP:                        CLOUD SETUP:
Laptop 1 (Nginx)          →    VPS 1 (Nginx + Let's Encrypt SSL)
Laptop 2 (Backend + Data) →    VPS 2 (Backend + Managed PostgreSQL/Redis)
Laptop 3 (Backend)        →    VPS 3 (Backend)
Laptop 4 (User)           →    Real users on the internet!

WHAT CHANGES:
- IPs change from 192.168.1.X → public cloud IPs
- Self-signed SSL → real SSL (Let's Encrypt, free)
- Add domain name → DNS points to VPS 1
- Add CI/CD → push code → auto-deploys
```

### Recommended Cloud Providers (Budget-Friendly)

| Provider | Cost (2 servers) | Good For |
|---|---|---|
| DigitalOcean | ~$24/mo | Simple, great docs, student credits |
| Hetzner | ~$12/mo | Cheapest, EU-based |
| AWS (Free Tier) | Free for 12 months | Resume item, but complex |
| GCP (Free Tier) | $300 credits | Great for ML workloads |

---

# 10. Glossary — Every Term Explained

| Term | Plain English Explanation |
|---|---|
| **API** | A set of URLs that your frontend can call to get/send data. Like a waiter that takes your order to the kitchen |
| **Async/Await** | A way to write code that can wait for slow operations (database queries, network calls) without blocking everything else |
| **BPE** | Byte-Pair Encoding — an algorithm that builds a vocabulary by repeatedly merging the most common character pairs |
| **Causal Mask** | Ensures the model can only look at PREVIOUS tokens when predicting the next one (can't "cheat" by looking ahead) |
| **Celery** | A Python library that runs heavy tasks in background workers instead of blocking the web server |
| **CORS** | Cross-Origin Resource Sharing — security mechanism that controls which websites can call your API |
| **CRUD** | Create, Read, Update, Delete — the four basic operations on any data |
| **Docker** | Packages your app + all its dependencies into a portable container that runs the same everywhere |
| **Docker Compose** | Tool to run multiple Docker containers together (database + backend + frontend) |
| **DPO** | Direct Preference Optimization — a simpler alternative to PPO that trains the model directly on human preferences |
| **Embedding** | Converting text into a list of numbers (vector) that captures its semantic meaning |
| **FastAPI** | A Python web framework for building APIs, with async support and auto-generated docs |
| **Fine-tuning** | Taking a pre-trained model and training it further on your specific data |
| **Grafana** | A dashboard tool for visualizing metrics (CPU usage, request latency, etc.) |
| **gRPC** | A fast protocol for server-to-server communication (alternative to REST) |
| **Health Check** | An endpoint that returns "I'm alive" so load balancers know the server is working |
| **JWT** | JSON Web Token — an encoded string that proves a user's identity without sending passwords |
| **KV-Cache** | Key-Value Cache — stores intermediate computations during text generation to avoid redundant work |
| **Load Balancer** | A server that distributes incoming requests across multiple backend servers |
| **Locust** | A Python tool for simulating thousands of users to test system performance |
| **Migration** | A versioned script that modifies the database schema (add table, change column, etc.) |
| **Nginx** | A web server that can also act as a reverse proxy and load balancer |
| **OAuth 2.0** | A protocol that lets users "Sign in with Google/GitHub" without sharing their password with you |
| **ORM** | Object-Relational Mapper — lets you interact with databases using Python classes instead of raw SQL |
| **PPO** | Proximal Policy Optimization — a reinforcement learning algorithm used in full RLHF |
| **Prometheus** | A monitoring system that collects metrics from your services |
| **Pydantic** | A Python library for data validation — ensures API requests have the right format |
| **Quantization** | Converting model weights from 32-bit to 8-bit numbers to reduce size and increase speed |
| **RAG** | Retrieval Augmented Generation — fetching relevant context from a database and injecting it into the AI prompt |
| **Redis** | An extremely fast in-memory data store used for caching, rate limiting, and message queuing |
| **REST** | Representational State Transfer — the standard pattern for web APIs (GET, POST, PUT, DELETE) |
| **RLHF** | Reinforcement Learning from Human Feedback — using human ratings to improve AI model outputs |
| **Reverse Proxy** | A server that sits between users and your backend, forwarding requests and adding features (SSL, caching) |
| **SFT** | Supervised Fine-Tuning — training a model on input-output pairs where you provide the correct answer |
| **SLM** | Small Language Model — a language model with fewer parameters that can run on regular hardware |
| **SQLAlchemy** | Python's most popular ORM — maps Python classes to database tables |
| **SSL/TLS** | Encryption that makes HTTPS secure — the padlock icon in your browser |
| **Sticky Session** | Load balancer sends the same user to the same server (needed for WebSocket connections) |
| **Token (AI)** | A sub-word unit that the model processes — "unhappiness" might be split into ["un", "happiness"] |
| **Token (Auth)** | A JWT string used to prove identity (different from AI tokens, confusing but common terminology) |
| **Transformer** | The neural network architecture behind all modern language models (GPT, BERT, etc.) |
| **Vector Database** | A database optimized for storing and searching high-dimensional vectors (embeddings) |
| **WebSocket** | A protocol for persistent, two-way communication between browser and server |
| **Worker** | A background process that picks up and executes tasks from a queue |

---

> **Study strategy**: Don't try to learn everything at once. Focus on YOUR role's technologies first. The Frontend lead doesn't need to understand transformer architecture in detail, and the AI lead doesn't need to master SCSS mixins. Learn what you need for this week's sprint, then expand as you integrate.

> **Remember**: Every expert was once a beginner. If something doesn't make sense, re-read the analogy, Google the specific concept, or ask your AI assistant to explain it differently. The important thing is to **build** — understanding deepens through implementation, not just reading.
