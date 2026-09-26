# Prompt Polisher — API Documentation

> **Base URL:** `http://localhost:8000/api/v1`
> **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) | `http://localhost:8000/redoc` (ReDoc)
> **Authentication:** All endpoints except `/auth/*` and `/health` require a Bearer JWT token in the `Authorization` header.

---

## 1. Health Check

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | ❌ | Server health and readiness check |

**Response `200 OK`:**
```json
{
  "status": "ok",
  "message": "Prompt Polisher Backend is Live!",
  "database": "Connected & Migrated"
}
```

---

## 2. Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | ❌ | Register with email + password |
| `POST` | `/auth/login` | ❌ | Login, returns JWT tokens |
| `POST` | `/auth/refresh` | ❌ | Exchange refresh token for new pair |
| `POST` | `/auth/logout` | ❌ | Logout (invalidate tokens client-side) |
| `GET` | `/auth/oauth/google` | ❌ | Redirect to Google OAuth |
| `GET` | `/auth/oauth/google/callback` | ❌ | Handle Google OAuth callback |
| `GET` | `/auth/oauth/github` | ❌ | Redirect to GitHub OAuth |
| `GET` | `/auth/oauth/github/callback` | ❌ | Handle GitHub OAuth callback |

### `POST /auth/register`

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "SecurePass123!",
  "full_name": "Alice Smith"
}
```

**Password Policy:** Minimum 8 characters, at least one uppercase, one lowercase, one digit.

**Response `201 Created`:**
```json
{
  "message": "Registration successful!",
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "alice@example.com",
    "full_name": "Alice Smith",
    "is_active": true
  }
}
```

**Error `409 Conflict`:** `{"detail": "Email already registered"}`

### `POST /auth/login`

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error `401 Unauthorized`:** `{"detail": "Invalid email or password."}`

### `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`:** Same as login (new token pair).

---

## 3. Users & Preferences

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/users/me` | ✅ | Get current user profile |
| `PUT` | `/users/me` | ✅ | Update display name |
| `DELETE` | `/users/me` | ✅ | Soft-delete (deactivate) account |
| `GET` | `/users/me/preferences` | ✅ | Get prompt preferences |
| `PUT` | `/users/me/preferences` | ✅ | Update prompt preferences |

### `GET /users/me`

**Response `200 OK`:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "is_active": true
}
```

### `GET /users/me/preferences`

**Response `200 OK`:**
```json
{
  "tone": "professional",
  "verbosity": "balanced",
  "target_model": "GPT-4",
  "domain": "coding",
  "custom_instructions": "Always add code examples.",
  "has_api_key": true
}
```

> **Note:** The `target_model_api_key` is **never** returned in responses for security. The `has_api_key` boolean indicates if one is stored.

### `PUT /users/me/preferences`

**Request (all fields optional — only send what you want to change):**
```json
{
  "tone": "casual",
  "verbosity": "concise",
  "target_model": "Claude",
  "domain": "marketing",
  "custom_instructions": "Keep it under 100 words.",
  "target_model_api_key": "sk-abc123..."
}
```

**Valid Values:**
- `tone`: `professional` | `casual` | `academic` | `creative`
- `verbosity`: `concise` | `detailed` | `balanced`
- `target_model`: `GPT-4` | `Claude` | `Gemini` | `General`
- `domain`: `marketing` | `coding` | `writing` | `general`
- `target_model_api_key`: Any string (encrypted at rest with AES Fernet)

---

## 4. Chat Sessions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/chat/sessions` | ✅ | Create a new chat session |
| `GET` | `/chat/sessions` | ✅ | List all sessions for current user |
| `GET` | `/chat/sessions/{id}` | ✅ | Get a specific session |
| `DELETE` | `/chat/sessions/{id}` | ✅ | Delete a session |
| `GET` | `/chat/sessions/{id}/messages` | ✅ | Get all messages in a session |

### `POST /chat/sessions`

**Request:**
```json
{
  "title": "Marketing Brainstorm"
}
```

**Response `201 Created`:**
```json
{
  "id": "f8e7d6c5-b4a3-2190-fedc-ba0987654321",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Marketing Brainstorm",
  "created_at": "2026-09-26T12:00:00Z"
}
```

### `GET /chat/sessions/{id}/messages`

**Response `200 OK`:**
```json
[
  {
    "id": "msg-uuid-1",
    "session_id": "session-uuid",
    "raw_content": "Write about dogs",
    "polished_content": "Write a comprehensive 800-word blog post exploring the most popular dog breeds...",
    "created_at": "2026-09-26T12:01:00Z"
  }
]
```

---

## 5. AI Inference (Prompt Generation)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/generate` | ✅ | Generate an optimized prompt (REST) |
| `WS` | `/ws/stream/{session_id}` | ✅ | Stream tokens in real-time (WebSocket) |

### `POST /generate`

**Request:**
```json
{
  "prompt": "Write about machine learning",
  "session_id": "optional-session-uuid",
  "preferences_override": {
    "temperature": 0.8
  }
}
```

**Response `200 OK`:**
```json
{
  "generated_prompt": "Write a comprehensive technical article about machine learning that covers supervised, unsupervised, and reinforcement learning paradigms...",
  "token_count": 87,
  "latency_ms": 245.3
}
```

### `WS /ws/stream/{session_id}`

**Client sends:**
```json
{
  "prompt": "Explain quantum computing",
  "preferences_override": {"temperature": 0.7}
}
```

**Server streams:**
```json
{"type": "token", "text": "Write"}
{"type": "token", "text": " a"}
{"type": "token", "text": " detailed"}
...
{"type": "done", "full_text": "Write a detailed explanation of quantum computing..."}
```

---

## 6. Feedback & Analytics

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/feedback` | ✅ | Submit thumbs up/down on a message |
| `GET` | `/feedback/stats` | ✅ | Get aggregated feedback statistics |
| `GET` | `/feedback/export` | ✅ | Export RLHF data as CSV |

### `POST /feedback`

**Request:**
```json
{
  "message_id": "msg-uuid",
  "rating": 1,
  "comment": "This was a great improvement!"
}
```

**`rating`:** `1` = thumbs up, `-1` = thumbs down

**Response `201 Created`:**
```json
{
  "id": "feedback-uuid",
  "message_id": "msg-uuid",
  "user_id": "user-uuid",
  "rating": 1,
  "comment": "This was a great improvement!",
  "created_at": "2026-09-26T12:05:00Z"
}
```

---

## 7. A/B Testing

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/ab/experiments` | ✅ | Create a new A/B experiment |
| `GET` | `/ab/experiments` | ✅ | List all experiments |
| `GET` | `/ab/experiments/{id}/stats` | ✅ | Get comparison statistics |
| `POST` | `/ab/results/{id}/rate` | ✅ | Rate an A/B result |

### `POST /ab/experiments`

**Request:**
```json
{
  "name": "SFT vs DPO",
  "description": "Compare base SFT model against DPO-aligned model",
  "model_a": "checkpoints/sft_best.pt",
  "model_b": "checkpoints/dpo_best.pt",
  "traffic_pct_b": 50
}
```

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| `400` | Bad Request — malformed input |
| `401` | Unauthorized — missing or invalid JWT |
| `403` | Forbidden — insufficient permissions |
| `404` | Not Found — resource doesn't exist |
| `409` | Conflict — duplicate resource (e.g., email already registered) |
| `422` | Unprocessable Entity — validation error |
| `429` | Too Many Requests — rate limited (50 req/min) |
| `500` | Internal Server Error |

---

## Rate Limiting

All API endpoints are rate-limited to **50 requests per minute** per user (or per IP for unauthenticated endpoints). When the limit is exceeded, the API returns `429 Too Many Requests`.

## Security

- All passwords are hashed with **bcrypt** before storage.
- JWT tokens use **HS256** with a configurable secret key.
- Sensitive fields (e.g., `target_model_api_key`) are encrypted at rest using **AES Fernet** (AES-128-CBC + HMAC-SHA256).
- API keys are **write-only** — they are never returned in API responses.
- All responses include security headers (CSP, X-Frame-Options, X-Content-Type-Options).
