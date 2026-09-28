# Infrastructure Documentation

## Network Topology

The Prompt Polisher system runs on a **4-laptop multi-node architecture** for the local/university deployment scenario. In production, this maps to cloud VPS instances.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            NETWORK TOPOLOGY                                 │
│                                                                             │
│  ┌──────────────────┐                                                       │
│  │   Laptop 4        │  ← User's Browser                                   │
│  │   (Client)        │     https://promptpolisher.dev                       │
│  └────────┬─────────┘                                                       │
│           │ HTTPS :443                                                      │
│           ▼                                                                 │
│  ┌──────────────────────────────────────────────────┐                       │
│  │   Laptop 1 — Load Balancer + Monitoring          │                       │
│  │                                                  │                       │
│  │   ┌──────────┐  ┌────────────┐  ┌─────────────┐  │                       │
│  │   │  Nginx   │  │ Prometheus │  │   Grafana   │  │                       │
│  │   │  :80/443 │  │   :9090    │  │   :3001     │  │                       │
│  │   └────┬─────┘  └────────────┘  └─────────────┘  │                       │
│  │        │                                          │                       │
│  │        │ least_conn (REST) / ip_hash (WebSocket)  │                       │
│  └────────┼──────────────────────────────────────────┘                       │
│           │                                                                 │
│     ┌─────┴──────┐                                                          │
│     │            │                                                          │
│     ▼            ▼                                                          │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐              │
│  │  Laptop 2 — Node A       │  │  Laptop 3 — Node B          │              │
│  │  (Primary Data Node)     │  │  (Compute-only Node)        │              │
│  │                          │  │                             │              │
│  │  ┌─────────┐ ┌────────┐  │  │  ┌─────────┐ ┌──────────┐  │              │
│  │  │ FastAPI │ │ Celery │  │  │  │ FastAPI │ │  Celery  │  │              │
│  │  │  :8000  │ │ Worker │  │  │  │  :8000  │ │  Worker  │  │              │
│  │  └─────────┘ └────────┘  │  │  └─────────┘ └──────────┘  │              │
│  │                          │  │        │                    │              │
│  │  ┌──────────┐ ┌───────┐  │  │        │ connects to       │              │
│  │  │ Postgres │ │ Redis │  │  │        │ Laptop 2's DBs    │              │
│  │  │  :5432   │ │ :6379 │  │  │        └────────────────►  │              │
│  │  └──────────┘ └───────┘  │  │                             │              │
│  │  ┌──────────┐            │  └─────────────────────────────┘              │
│  │  │ Qdrant   │            │                                               │
│  │  │  :6333   │            │                                               │
│  │  └──────────┘            │                                               │
│  └──────────────────────────┘                                               │
│                                                                             │
│  ┌──────────────────────────┐                                               │
│  │  Laptop 4 — AI Worker    │                                               │
│  │  (GPU Node)              │                                               │
│  │                          │                                               │
│  │  ┌─────────────────────┐ │                                               │
│  │  │ AI Inference Server │ │                                               │
│  │  │  :8001              │ │                                               │
│  │  │  (PyTorch model)    │ │                                               │
│  │  └─────────────────────┘ │                                               │
│  └──────────────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Port Map

| Service | Port | Protocol | Host |
|---------|------|----------|------|
| Nginx (HTTP) | 80 | TCP | Laptop 1 |
| Nginx (HTTPS) | 443 | TCP | Laptop 1 |
| FastAPI (Node A) | 8000 | TCP | Laptop 2 |
| FastAPI (Node B) | 8000 | TCP | Laptop 3 |
| AI Inference Server | 8001 | TCP | Laptop 4 |
| PostgreSQL | 5432 | TCP | Laptop 2 |
| Redis | 6379 | TCP | Laptop 2 |
| Qdrant (REST) | 6333 | TCP | Laptop 2 |
| Qdrant (gRPC) | 6334 | TCP | Laptop 2 |
| Prometheus | 9090 | TCP | Laptop 1 |
| Grafana | 3001 | TCP | Laptop 1 |

### Docker Compose Files

| File | Runs On | Services |
|------|---------|----------|
| `docker-compose.yml` | Any (dev) | PostgreSQL, Redis, Qdrant, Nginx |
| `docker-compose.lb.yml` | Laptop 1 | Nginx LB, Prometheus, Grafana |
| `docker-compose.node-a.yml` | Laptop 2 | FastAPI, Celery, PostgreSQL, Redis, Qdrant |
| `docker-compose.node-b.yml` | Laptop 3 | FastAPI, Celery (connects to Laptop 2's DBs) |

---

## Deployment Runbook

### Prerequisites

- Docker 24+ and Docker Compose v2+ installed on all laptops
- Git access to the `prompt-polisher` repository
- All laptops connected to the same LAN
- Static IPs assigned (see Step 1)

### Step 1: Assign Static IPs

On each laptop, assign a static IP on the local network:

| Laptop | Role | Suggested IP |
|--------|------|-------------|
| Laptop 1 | Load Balancer | `192.168.1.101` |
| Laptop 2 | Node A (Primary) | `192.168.1.102` |
| Laptop 3 | Node B (Compute) | `192.168.1.103` |
| Laptop 4 | AI Worker / Client | `192.168.1.104` |

**Windows:** Settings → Network → Ethernet → Edit IP → Manual → Set IPv4 address.
**Linux:** `sudo ip addr add 192.168.1.10X/24 dev eth0`

### Step 2: Clone the Repository (All Laptops)

```bash
git clone https://github.com/Prompt-Polisher-Org/prompt-polisher.git
cd prompt-polisher
cp .env.example .env
# Edit .env with your secrets (SECRET_KEY, ENCRYPTION_KEY, DB credentials)
```

### Step 3: Start Node A — Primary Data Node (Laptop 2)

```bash
docker compose -f docker-compose.node-a.yml up -d
```

Wait for all services to be healthy:

```bash
docker compose -f docker-compose.node-a.yml ps
# All should show "Up (healthy)" or "Up"
```

Verify PostgreSQL is reachable:

```bash
docker exec -it pp_postgres pg_isready
# → accepting connections
```

### Step 4: Run Database Migrations (Laptop 2)

```bash
# Enter the backend container
docker exec -it pp_backend_a bash

# Inside the container:
alembic upgrade head
python -m app.scripts.seed  # seed development data
exit
```

### Step 5: Start Node B — Compute Node (Laptop 3)

First, update the `.env` file on Laptop 3 to point to Laptop 2's databases:

```env
DATABASE_URL=postgresql+asyncpg://user:password@192.168.1.102:5432/prompt_db
REDIS_URL=redis://192.168.1.102:6379/0
QDRANT_URL=http://192.168.1.102:6333
```

Then start:

```bash
docker compose -f docker-compose.node-b.yml up -d
```

### Step 6: Start the Load Balancer (Laptop 1)

Edit `infra/nginx/nginx-lb.conf` to set the correct upstream IPs:

```nginx
upstream backend_api {
    least_conn;
    server 192.168.1.102:8000;  # Node A
    server 192.168.1.103:8000;  # Node B
}
```

Then start:

```bash
docker compose -f docker-compose.lb.yml up -d
```

### Step 7: Start the AI Inference Server (Laptop 4)

```bash
cd ai
python -m ai.src.inference.server \
    --checkpoint ai/models/checkpoints/best_model.pt \
    --port 8001
```

### Step 8: Verify the Full System

From any machine on the LAN:

```bash
# Health check
curl -k https://192.168.1.101/api/v1/health

# Swagger UI
open https://192.168.1.101/docs

# Grafana dashboards
open http://192.168.1.101:3001
# Login: admin / promptpolisher
```

### Step 9: Generate SSL Certificates (Production Only)

For cloud deployment with a real domain:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d promptpolisher.dev -d www.promptpolisher.dev

# Auto-renewal (cron)
echo "0 0 * * 0 certbot renew --quiet" | sudo crontab -
```

---

## Troubleshooting Guide

### Common Issues

#### 1. Container won't start — port already in use

```bash
# Find what's using the port
# Windows:
netstat -ano | findstr :8000
# Linux:
sudo lsof -i :8000

# Kill the process or change the port in docker-compose
```

#### 2. Node B can't connect to PostgreSQL on Node A

**Symptoms:** `Connection refused` or `timeout` errors in Node B logs.

**Fix:**
1. Verify Laptop 2's firewall allows port 5432:
   ```bash
   # Linux
   sudo ufw allow from 192.168.1.0/24 to any port 5432
   # Windows
   netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432
   ```
2. Edit PostgreSQL's `pg_hba.conf` to allow remote connections:
   ```
   host all all 192.168.1.0/24 md5
   ```
3. Set `listen_addresses = '*'` in `postgresql.conf`.
4. Restart the postgres container: `docker restart pp_postgres`

#### 3. WebSocket connections dropping

**Symptoms:** Chat streaming stops mid-generation.

**Fix:**
- Increase Nginx timeouts in `nginx.conf`:
  ```nginx
  proxy_read_timeout 3600s;
  proxy_send_timeout 3600s;
  ```
- Ensure `ip_hash` is used for WebSocket upstream (so reconnects hit the same backend).
- Check client-side reconnect logic in `frontend/src/lib/socket.ts`.

#### 4. AI Inference Server returns 503

**Symptoms:** `/api/v1/inference/generate` returns HTTP 500.

**Fix:**
1. Check if the AI server is running: `curl http://192.168.1.104:8001/health`
2. Verify the model checkpoint exists: `ls ai/models/checkpoints/best_model.pt`
3. Check GPU memory: `nvidia-smi` (if using CUDA)
4. Try CPU fallback: `CUDA_VISIBLE_DEVICES="" python -m ai.src.inference.server ...`

#### 5. Redis connection errors

**Symptoms:** Rate limiting or caching fails silently.

**Fix:**
1. Check Redis is running: `docker exec -it pp_redis redis-cli ping` → should return `PONG`
2. Verify connection string in `.env`: `REDIS_URL=redis://localhost:6379/0`
3. If using remote Redis, ensure firewall allows port 6379.

#### 6. Alembic migration fails

**Symptoms:** `alembic upgrade head` throws errors.

**Fix:**
1. Check DB connectivity: `python backend/test_db.py`
2. Verify the current migration state: `alembic current`
3. If stuck, stamp the current head: `alembic stamp head`
4. Regenerate migration: `alembic revision --autogenerate -m "fix"`

#### 7. Frontend shows blank page

**Symptoms:** `localhost:3000` loads but renders nothing.

**Fix:**
1. Check the browser console for JS errors.
2. Verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local` points to the correct backend.
3. Rebuild: `cd frontend && npm run build && npm start`

#### 8. High latency on prompt generation

**Symptoms:** Generation takes >10 seconds.

**Fix:**
1. Check model quantization: INT8 is ~2x faster than FP32.
2. Verify KV-cache is enabled in the inference server.
3. Reduce `max_new_tokens` (default 512 → try 256).
4. Check Nginx is load-balancing properly: `docker logs pp_loadbalancer`
5. Monitor with Grafana → API Latency dashboard.

### Health Check Endpoints

| Service | Endpoint | Expected |
|---------|----------|----------|
| FastAPI Backend | `GET /api/v1/health` | `{"status": "ok", "database": "connected", "redis": "connected"}` |
| AI Inference Server | `GET /health` | `{"status": "ok", "model_loaded": true}` |
| Nginx | `GET /health` | `200 OK` |
| Prometheus | `GET /-/healthy` | `Prometheus Server is Healthy.` |
| Grafana | `GET /api/health` | `{"database": "ok"}` |

### Monitoring URLs

| Dashboard | URL | Credentials |
|-----------|-----|-------------|
| Swagger UI | `https://<LB_IP>/docs` | JWT token |
| ReDoc | `https://<LB_IP>/redoc` | Public |
| Prometheus | `http://<LB_IP>:9090` | None |
| Grafana | `http://<LB_IP>:3001` | admin / promptpolisher |

### Log Locations

| Service | Location |
|---------|----------|
| Nginx | `docker logs pp_loadbalancer` |
| FastAPI (Node A) | `docker logs pp_backend_a` |
| FastAPI (Node B) | `docker logs pp_backend_b` |
| Celery Workers | `docker logs pp_celery_a` / `pp_celery_b` |
| PostgreSQL | `docker logs pp_postgres` |
| Redis | `docker logs pp_redis` |
| Prometheus | `docker logs pp_prometheus` |
| Grafana | `docker logs pp_grafana` |
