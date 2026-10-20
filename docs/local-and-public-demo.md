# Local and public demo setup

This guide is for getting the checked-out project running before a short
presentation. Start locally first. The demo app can use the AI service's labeled
mock mode while you verify the rest of the flow, but do not describe that as
the trained model.

## Do these first

- [ ] Make sure Docker Engine/Desktop is running and `docker compose version` works.
- [ ] Check free disk space: the first build downloads several service images and Python/Node dependencies.
- [ ] Keep the repository's root `.env` private. If it is missing, create it with `cp .env.example .env`.
- [ ] Ask the teammate who trained the model for the checkpoint **and matching tokenizer** from the same training run. Both are needed for trained inference; model artifacts are not in Git.
- [ ] Use email/password for the first demo. Google/GitHub OAuth needs provider app credentials and registered callback URLs.

The current development copy has a checkpoint file but is missing its matching tokenizer. The inference service therefore starts in `degraded (mock mode)` until a complete, trusted pair is configured. Check `http://localhost:8001/health` after startup.

## 1. First local run — Docker

The laptop currently has Node 22, but the frontend packages are not installed;
the system Python is 3.14, while the Docker images provide Python 3.12. Using
Compose avoids installing Python packages on the host.

From the repository root:

```bash
# Only if you don't already have a root .env
cp .env.example .env

# Start the frontend, API, AI inference service, Postgres, Redis, Qdrant and worker
docker compose --profile full up -d --build

# Create/update the database tables
docker compose --profile full exec backend alembic upgrade head

# Check containers
docker compose --profile full ps
```

Open these local URLs:

- Web app: <http://localhost:3000>
- API health: <http://localhost:8000/api/v1/health>
- API docs: <http://localhost:8000/docs>
- AI health: <http://localhost:8001/health>

Register an account, sign in, start a chat, submit a prompt, switch theme, reload
the page, and check that the session is still there. If AI health says
`degraded (mock mode)` or chat output includes `MOCK:`, the UI/API path is up,
but trained inference still needs the matching artifacts.

Stop the stack and keep its local database data:

```bash
docker compose --profile full down
```

Avoid `down -v` unless you intentionally want to erase the local database and
vector-store volumes.

## 2. If you want to run app code on the host

Use this when you want hot reload or to inspect app logs directly. Install
Python 3.12, Node 20 or newer, and the dependencies first. Then:

```bash
# From the repo root: database and cache services only
docker compose up -d postgres redis qdrant

# Terminal 1
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 2, from repo root
python3.12 -m venv .venv-ai
source .venv-ai/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r ai/requirements.txt
uvicorn ai.src.inference.server:app --reload --port 8001

# Terminal 3
cd frontend
npm ci
npm run dev
```

Use a separate Python environment for the backend and AI requirements. The
root `.env.example` defaults are set for host-run services (`localhost`, with
Postgres published on port `5433`).

## 3. Show it to someone on the same Wi-Fi

Find your laptop's LAN IP address and set the root `.env` before building:

```dotenv
NEXT_PUBLIC_API_URL=http://YOUR_LAPTOP_LAN_IP:8000/api/v1
```

Then rebuild/start the Compose stack and share
`http://YOUR_LAPTOP_LAN_IP:3000`. The frontend bakes `NEXT_PUBLIC_API_URL` into
its browser bundle at build time, so changing it requires rebuilding the
frontend. Permit inbound TCP 3000 and 8000 on your laptop firewall for that
network. Keep the laptop awake and connected. Use this only on a network you
trust.

## 4. Temporary internet demo from your laptop

For a short remote demo, a tunnel avoids building and operating an EC2 host.
Cloudflare Quick Tunnels create random `trycloudflare.com` URLs and are meant
for development/testing. The app needs two public routes because the browser
loads the web page from port 3000 and calls the API/WebSocket on port 8000.

1. Start the full Compose stack locally and confirm the local URLs above work.
2. In one terminal, run `cloudflared tunnel --url http://localhost:8000` and
   copy the generated **HTTPS API URL** from its output.
3. Put that URL in the root `.env` (include `/api/v1`):

   ```dotenv
   NEXT_PUBLIC_API_URL=https://YOUR-API.trycloudflare.com/api/v1
   ```

4. Rebuild and restart the frontend so its browser bundle uses the public API:

   ```bash
   docker compose --profile full build frontend
   docker compose --profile full up -d frontend
   ```

5. In a second terminal, run `cloudflared tunnel --url http://localhost:3000`.
   Share that generated HTTPS URL with the reviewer. Keep both tunnel terminals
   and the Compose stack running until the demo ends.

Cloudflare Tunnel supports WebSockets, which this chat uses. Quick Tunnels do
not support Server-Sent Events, so an SSE-based route would need another demo
path. OAuth is best left off for this short demo: the random tunnel URLs change
and OAuth providers require exact callback URLs. Use email/password and demo
data only. Close both tunnels and stop Compose as soon as you finish.

## 5. EC2 demo host

Use EC2 after the local Compose run is reliable, or when the demo needs to stay
available while your laptop is offline. Choose a Linux AMI, a key pair, and an
instance with enough RAM/disk for all containers; the AI image is CPU-based and
has a substantial dependency footprint. Estimate the exact instance cost in
the AWS calculator for your region before launch.

1. Launch an EBS-backed instance and connect over SSH. In its security group,
   allow SSH (TCP 22) only from your current public IP. Allow TCP 3000 and 8000
   only from the audience's IP range where possible. Do not open Postgres 5433,
   Redis 6379, Qdrant 6333/6334, or AI 8001 to the internet.
2. Install Git, Docker Engine, and the Docker Compose plugin using the official
   instructions for the selected Linux distribution.
3. Clone the repository onto the instance, create `.env` from `.env.example`,
   and replace the sample `SECRET_KEY`, database password, and encryption key
   with fresh random values. Never commit or send `.env` in chat.
4. Set the frontend's browser API URL to the instance's public address **before
   building**. For a temporary HTTP-only test:

   ```dotenv
   NEXT_PUBLIC_API_URL=http://YOUR_EC2_PUBLIC_IP:8000/api/v1
   FRONTEND_URL=http://YOUR_EC2_PUBLIC_IP:3000
   OAUTH_REDIRECT_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000
   ```

5. Start the stack and migrate the database:

   ```bash
   docker compose --profile full up -d --build
   docker compose --profile full exec backend alembic upgrade head
   docker compose --profile full ps
   ```

6. Visit `http://YOUR_EC2_PUBLIC_IP:3000`. Sign up and use the app. Verify the
   API endpoint is reachable at `http://YOUR_EC2_PUBLIC_IP:8000/api/v1/health`.
7. When finished, stop the instance in the EC2 console. A stopped instance
   stops compute charges, but EBS storage remains billable. Terminate the
   instance if you no longer need it and have saved anything you want to keep.

The HTTP/IP instructions above are only for a brief test. Do not use real
accounts, secrets, or private data over a public HTTP demo. For a longer-lived
deployment, put the app behind a domain and valid HTTPS, restrict CORS and
security-group access, and use managed/secured credentials. The repository's
optional Nginx profile currently uses a self-signed certificate, so browsers
will show a certificate warning until it is replaced with a trusted cert.

## OAuth callback URLs

If you decide to configure OAuth, register exact callback URLs with each
provider and set all four client ID/secret values in `.env`:

```text
http://localhost:8000/api/v1/auth/oauth/google/callback
http://localhost:8000/api/v1/auth/oauth/github/callback
```

For a public demo, replace `localhost:8000` with the public HTTPS API hostname,
and set `OAUTH_REDIRECT_BASE_URL` and `FRONTEND_URL` to the public API and
frontend URLs respectively. Provider callback validation may require HTTPS.
