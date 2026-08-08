# 🌐 Network Setup Guide — Prompt Polisher

> **Audience**: All team members  
> **Last Updated**: Week 3-4  
> **Owner**: ⚙️ DO (Member C)

---

## Overview

Prompt Polisher uses **Nginx as a reverse proxy** sitting in front of the backend API and frontend. All traffic flows through Nginx, which handles:

- **SSL termination** (HTTPS)
- **Reverse proxying** (routes `/api/*` → Backend, everything else → Frontend)
- **WebSocket proxying** (for real-time AI streaming)
- **Load balancing** (Week 9-10, across multiple backend nodes)

```
┌──────────────────────────────────────────────────────┐
│                    Client Browser                     │
│              (Laptop 4 or any device)                │
└──────────────────┬───────────────────────────────────┘
                   │ HTTPS (port 443)
                   ▼
┌──────────────────────────────────────────────────────┐
│               Nginx (Laptop 1)                       │
│         SSL termination + Reverse proxy              │
│                                                      │
│  /api/*  ──────►  Backend (FastAPI :8000)             │
│  /ws/*   ──────►  Backend (WebSocket)                │
│  /*      ──────►  Frontend (Next.js :3000)           │
└──────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites

- **Docker & Docker Compose** installed on your machine
- **OpenSSL** installed (comes with Git for Windows)
- All machines on the **same LAN / Wi-Fi network**

---

## 2. Generate SSL Certificate (First-Time Setup)

### On Linux / macOS / Git Bash:
```bash
cd infra/nginx/ssl
bash generate-ssl.sh
```

### On Windows (PowerShell):
```powershell
cd infra\nginx\ssl
powershell -ExecutionPolicy Bypass -File generate-ssl.ps1
```

This generates `server.key` and `server.crt` in `infra/nginx/ssl/`. These files are gitignored — each developer generates their own.

> ⚠️ Your browser will show a "Not Secure" warning for self-signed certs. Click **Advanced → Proceed** to bypass it during development.

---

## 3. Start the Stack

```bash
# From project root
docker compose up -d
```

This starts:
| Service | Container | Port |
|---------|-----------|------|
| PostgreSQL | `prompt_polisher_db` | 5433 |
| Redis | `prompt_polisher_redis` | 6379 |
| Qdrant | `prompt_polisher_qdrant` | 6333, 6334 |
| Nginx | `prompt_polisher_nginx` | 80, 443 |

The backend and frontend containers are currently commented out (run them locally with `uvicorn` and `npm run dev`).

---

## 4. Accessing the System

### From the same machine (localhost):
| URL | Destination |
|-----|------------|
| `https://localhost/api/v1/health` | Backend health check |
| `https://localhost/docs` | Swagger API docs |
| `https://localhost/` | Frontend (when running) |

### From another machine on the LAN:
1. Find the host machine's IP: `ipconfig` (Windows) or `ifconfig` (macOS/Linux)
2. Replace `localhost` with that IP, e.g.: `https://192.168.1.100/api/v1/health`
3. Ensure the host's **firewall allows ports 80 and 443**

---

## 5. Firewall Configuration

### Windows:
```powershell
# Allow Nginx ports through Windows Firewall
netsh advfirewall firewall add rule name="Prompt Polisher HTTP" dir=in action=allow protocol=tcp localport=80
netsh advfirewall firewall add rule name="Prompt Polisher HTTPS" dir=in action=allow protocol=tcp localport=443
```

### macOS:
Ports are open by default on macOS. No action needed.

### Linux (ufw):
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## 6. Verify the Setup

### Test 1: Nginx is running
```bash
docker ps | grep nginx
# Should show prompt_polisher_nginx as "Up"
```

### Test 2: HTTP → HTTPS redirect works
```bash
curl -I http://localhost
# Should return 301 redirect to https://
```

### Test 3: HTTPS serves content
```bash
curl -k https://localhost/api/v1/health
# Should return {"status": "ok", ...}
# (-k flag ignores self-signed cert warning)
```

### Test 4: Another machine can reach you
From Laptop 4 (or any LAN device):
```bash
curl -k https://<YOUR_IP>/api/v1/health
```

---

## 7. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ERR_CONNECTION_REFUSED` | Check `docker ps` — is Nginx running? |
| `502 Bad Gateway` | Backend isn't running. Start it with `uvicorn` or uncomment in compose |
| `SSL_ERROR_*` in browser | Normal for self-signed certs. Click "Advanced → Proceed" |
| Can't reach from LAN | Check firewall rules (section 5) and verify IP address |
| Port 80/443 already in use | Stop other web servers (Apache, IIS, etc.) or change ports in `docker-compose.yml` |

---

## 8. File Reference

```
infra/nginx/
├── nginx.conf                 # Main Nginx configuration
└── ssl/
    ├── generate-ssl.sh        # SSL cert generator (Linux/macOS)
    ├── generate-ssl.ps1       # SSL cert generator (Windows)
    ├── .gitignore             # Prevents committing actual certs
    ├── server.key             # (generated, gitignored)
    └── server.crt             # (generated, gitignored)
```

---

## 9. What's Next (Week 9-10)

In the multi-node phase, this Nginx config will be expanded to:
- Load balance across **two backend nodes** (`least_conn`)
- Use **`ip_hash`** for sticky WebSocket sessions
- Health-check backends every 10 seconds
- Automatically remove unhealthy nodes from the upstream
