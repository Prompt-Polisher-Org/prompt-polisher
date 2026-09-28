# Manual Tasks Remaining

> These are the remaining tasks that **require human action** — they can't be automated by code.

## Priority 1: Things Needed ASAP

### 🎥 Record Demo Video (5 minutes)
**Estimated time: 1–2 hours**

1. Install OBS Studio or use Loom
2. Start the system locally:
   ```bash
   docker compose up -d                     # PostgreSQL, Redis, Qdrant
   cd backend && uvicorn app.main:app --reload  # Backend :8000
   cd frontend && npm run dev                   # Frontend :3000
   ```
3. Record these flows (in order):
   - [ ] User registration (email + password)
   - [ ] Onboarding wizard (select tone, verbosity, model, domain)
   - [ ] Generate an optimized prompt (type a vague prompt → show AI response)
   - [ ] Show RAG personalization (preferences influence the output)
   - [ ] Provide feedback (thumbs up/down)
   - [ ] Show dark/light mode toggle
   - [ ] Show the analytics dashboard
4. Export as MP4, save to `docs/demo.mp4`

### 🤖 DPO Human Evaluation (50 Samples)
**Estimated time: 2–3 hours**

1. Run the evaluation script:
   ```bash
   python -m ai.src.training.evaluate --checkpoint ai/models/checkpoints/best_model.pt --num-samples 50
   ```
2. Review the 50 generated outputs
3. For each, score on a 1–5 scale:
   - **Clarity**: Is the optimized prompt clearer than the input?
   - **Specificity**: Does it add useful detail?
   - **Fluency**: Is it grammatically correct?
4. Calculate average scores and add to `docs/model-card.md` under "Evaluation"

---

## Priority 2: Cloud Deployment

### 🌐 Purchase Domain + DNS
**Estimated time: 30 minutes**

1. Purchase `promptpolisher.dev` (or similar) from Namecheap/GoDaddy
2. Set DNS records:
   - `A` record → VPS IP address
   - `CNAME` for `www` → apex domain

### ☁️ Provision Cloud Infrastructure
**Estimated time: 2–4 hours**

1. Spin up VPS instances (DigitalOcean, AWS, etc.):
   - 1x Load Balancer (2 vCPU, 4GB RAM)
   - 2x Backend nodes (2 vCPU, 4GB RAM each)
   - 1x Database server (4 vCPU, 8GB RAM) — or use managed RDS
2. SSH into each server:
   ```bash
   ssh root@<IP>
   apt update && apt install -y docker.io docker-compose-v2
   ```
3. Clone the repo and deploy using the Docker Compose files:
   ```bash
   git clone https://github.com/Prompt-Polisher-Org/prompt-polisher.git
   cd prompt-polisher
   # On DB server:
   docker compose -f docker-compose.node-a.yml up -d
   # On compute server:
   docker compose -f docker-compose.node-b.yml up -d
   # On LB server:
   docker compose -f docker-compose.lb.yml up -d
   ```

### 🔒 Configure SSL (Let's Encrypt)
**Estimated time: 15 minutes**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d promptpolisher.dev -d www.promptpolisher.dev
echo "0 0 * * 0 certbot renew --quiet" | sudo crontab -
```

### 🔄 Set Up CI/CD (GitHub Actions)
**Estimated time: 1–2 hours**

Create `.github/workflows/deploy.yml`:
1. On push to `main`: build Docker images → push to registry → SSH deploy
2. Run tests before deploy (backend: pytest, frontend: eslint)
3. Set up GitHub Secrets: `SSH_KEY`, `SERVER_IP`, `DOCKER_REGISTRY_TOKEN`

---

## Priority 3: Testing & Verification

### 🧪 Cross-Browser Testing
**Estimated time: 1 hour**

Open the live site in each browser and verify all features work:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

### 🔐 Security Audit
**Estimated time: 30 minutes**

1. Run SSL Labs test: https://www.ssllabs.com/ssltest/ → target A+ rating
2. Run PageSpeed Insights: https://pagespeed.web.dev/ → target score > 90

### 🖥️ Multi-Node Verification
**Estimated time: 1 hour**

1. Assign static IPs to all 4 laptops (see `docs/infrastructure.md`)
2. Start services on each laptop per the deployment runbook
3. Send 100 requests via Locust and verify they distribute across both nodes
4. Stop Node B → verify Node A handles all traffic → restart Node B

---

## Priority 4: Presentation

### 📊 Prepare Presentation Slides
**Estimated time: 3–4 hours**

Create slides covering:
- [ ] Problem statement (why prompt optimization matters)
- [ ] Solution overview (Prompt Polisher)
- [ ] Architecture diagram (copy from `docs/architecture.md`)
- [ ] Tech stack rationale (copy from architecture doc)
- [ ] Live demo walkthrough (use the recorded video)
- [ ] AI model details (copy from `docs/model-card.md`)
- [ ] Performance results (load test numbers)
- [ ] Future roadmap
- [ ] Q&A slide

### 🎤 Rehearse Presentation
**Estimated time: 1 hour**

- Rehearse within the 30-minute time slot
- Prepare for anticipated questions:
  - "Why build a custom model instead of using GPT-4?"
  - "How does the DPO training improve results?"
  - "What's the scalability limit of the current architecture?"
  - "How do you handle malicious prompts?"

### 📝 Final Project Report
**Estimated time: 4–6 hours**

Write the academic report (PDF) covering:
- Abstract, Introduction, Literature Review
- System Design & Architecture
- Implementation Details
- Testing & Evaluation
- Results & Discussion
- Conclusion & Future Work
- References
