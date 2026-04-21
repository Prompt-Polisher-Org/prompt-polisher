# ⚙️ Infrastructure — Docker, Nginx & Monitoring

> **Tech Stack**: Docker · Docker Compose · Nginx · Prometheus · Grafana · Let's Encrypt

## Directory Structure

```
infra/
├── docker/
│   ├── backend.Dockerfile     # Backend production image
│   ├── frontend.Dockerfile    # Frontend production image
│   └── ai-worker.Dockerfile   # AI worker image
├── nginx/
│   ├── nginx.conf             # Main Nginx config
│   ├── ssl/                   # SSL certificates
│   └── conf.d/                # Per-site configs
├── monitoring/
│   ├── prometheus.yml         # Prometheus scrape config
│   └── grafana/               # Grafana dashboard JSON
├── scripts/
│   ├── setup-network.sh       # LAN setup helper
│   └── backup-db.sh           # Database backup script
└── compose/
    ├── docker-compose.lb.yml      # Laptop 1: Load Balancer
    ├── docker-compose.node-a.yml  # Laptop 2: Backend A + Data
    └── docker-compose.node-b.yml  # Laptop 3: Backend B
```

## Owner
⚙️ **Systems / DevOps Engineer** (Member C)
