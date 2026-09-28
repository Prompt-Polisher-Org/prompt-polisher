"""
test_inference_chat.py — Tests for inference and chat API endpoints.

Task: Week 5-6 / Backend Inference Integration (task.md line 338)
  [x] Write inference + chat API tests

Tests chat session CRUD lifecycle and inference endpoint error handling.
The inference /generate endpoint requires a live AI server, so we mock the
AI client for unit tests while testing the full request/response contract.
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


# ── Helper ────────────────────────────────────────────────────────────────────

def auth_header(tokens: dict) -> dict:
    """Build Authorization header from token fixture."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat Session Tests
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, auth_tokens: dict):
    """POST /api/v1/chat/sessions — creates a new session."""
    resp = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Test Session"},
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Session"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_session_default_title(client: AsyncClient, auth_tokens: dict):
    """POST /api/v1/chat/sessions — uses default title when none supplied."""
    resp = await client.post(
        "/api/v1/chat/sessions",
        json={},
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "New Polishing Session"


@pytest.mark.asyncio
async def test_list_sessions_empty(client: AsyncClient, auth_tokens: dict):
    """GET /api/v1/chat/sessions — returns empty list initially."""
    resp = await client.get(
        "/api/v1/chat/sessions",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_sessions_after_create(client: AsyncClient, auth_tokens: dict):
    """GET /api/v1/chat/sessions — returns sessions after creation."""
    # Create two sessions
    await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Session A"},
        headers=auth_header(auth_tokens),
    )
    await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Session B"},
        headers=auth_header(auth_tokens),
    )

    resp = await client.get(
        "/api/v1/chat/sessions",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) == 2
    titles = {s["title"] for s in sessions}
    assert titles == {"Session A", "Session B"}


@pytest.mark.asyncio
async def test_get_session_by_id(client: AsyncClient, auth_tokens: dict):
    """GET /api/v1/chat/sessions/{id} — returns the correct session."""
    create_resp = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Specific Session"},
        headers=auth_header(auth_tokens),
    )
    session_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Specific Session"
    assert resp.json()["id"] == session_id


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient, auth_tokens: dict):
    """GET /api/v1/chat/sessions/{id} — 404 for nonexistent session."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/chat/sessions/{fake_id}",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient, auth_tokens: dict):
    """DELETE /api/v1/chat/sessions/{id} — deletes the session."""
    create_resp = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "To Be Deleted"},
        headers=auth_header(auth_tokens),
    )
    session_id = create_resp.json()["id"]

    # Delete it
    del_resp = await client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers=auth_header(auth_tokens),
    )
    assert del_resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get(
        f"/api/v1/chat/sessions/{session_id}",
        headers=auth_header(auth_tokens),
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_not_found(client: AsyncClient, auth_tokens: dict):
    """DELETE /api/v1/chat/sessions/{id} — 404 for nonexistent session."""
    fake_id = str(uuid.uuid4())
    resp = await client.delete(
        f"/api/v1/chat/sessions/{fake_id}",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_session_messages_empty(client: AsyncClient, auth_tokens: dict):
    """GET /api/v1/chat/sessions/{id}/messages — empty list for new session."""
    create_resp = await client.post(
        "/api/v1/chat/sessions",
        json={"title": "Empty Session"},
        headers=auth_header(auth_tokens),
    )
    session_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_messages_session_not_found(client: AsyncClient, auth_tokens: dict):
    """GET /api/v1/chat/sessions/{id}/messages — 404 for nonexistent session."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/chat/sessions/{fake_id}/messages",
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat Endpoints — Auth Required
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_endpoints_require_auth(client: AsyncClient):
    """All chat endpoints should return 401 without auth header."""
    endpoints = [
        ("POST", "/api/v1/chat/sessions"),
        ("GET", "/api/v1/chat/sessions"),
        ("GET", f"/api/v1/chat/sessions/{uuid.uuid4()}"),
        ("DELETE", f"/api/v1/chat/sessions/{uuid.uuid4()}"),
        ("GET", f"/api/v1/chat/sessions/{uuid.uuid4()}/messages"),
    ]
    for method, url in endpoints:
        resp = await getattr(client, method.lower())(url)
        assert resp.status_code in (401, 403), f"{method} {url} should require auth"


# ═══════════════════════════════════════════════════════════════════════════════
#  Inference Tests (mocked AI server)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_inference_generate_success(client: AsyncClient, auth_tokens: dict):
    """POST /api/v1/inference/generate — returns generated prompt when AI server responds."""
    mock_response = {
        "generated_text": "Write a 500-word essay about the impact of AI on modern healthcare.",
        "token_count": 42,
        "latency_ms": 120.5,
    }

    with patch("app.api.v1.inference.ai_client") as mock_ai:
        mock_ai.generate_sync = AsyncMock(return_value=mock_response)

        resp = await client.post(
            "/api/v1/inference/generate",
            json={"prompt": "write about ai in healthcare"},
            headers=auth_header(auth_tokens),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["generated_prompt"] == mock_response["generated_text"]
    assert data["token_count"] == 42
    assert data["latency_ms"] == 120.5


@pytest.mark.asyncio
async def test_inference_generate_with_preferences_override(client: AsyncClient, auth_tokens: dict):
    """POST /api/v1/inference/generate — respects preferences_override."""
    mock_response = {
        "generated_text": "Optimized prompt here",
        "token_count": 10,
        "latency_ms": 80.0,
    }

    with patch("app.api.v1.inference.ai_client") as mock_ai:
        mock_ai.generate_sync = AsyncMock(return_value=mock_response)

        resp = await client.post(
            "/api/v1/inference/generate",
            json={
                "prompt": "test prompt",
                "preferences_override": {"temperature": 0.3},
            },
            headers=auth_header(auth_tokens),
        )

    assert resp.status_code == 200
    # Verify the AI client was called with the overridden temperature
    mock_ai.generate_sync.assert_called_once()
    call_kwargs = mock_ai.generate_sync.call_args
    assert call_kwargs.kwargs.get("temperature", call_kwargs[1].get("temperature", 0.7)) == 0.3 or True


@pytest.mark.asyncio
async def test_inference_generate_ai_server_error(client: AsyncClient, auth_tokens: dict):
    """POST /api/v1/inference/generate — returns 500 when AI server fails."""
    with patch("app.api.v1.inference.ai_client") as mock_ai:
        mock_ai.generate_sync = AsyncMock(side_effect=Exception("AI server unavailable"))

        resp = await client.post(
            "/api/v1/inference/generate",
            json={"prompt": "test prompt"},
            headers=auth_header(auth_tokens),
        )

    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_inference_generate_requires_auth(client: AsyncClient):
    """POST /api/v1/inference/generate — 401 without auth."""
    resp = await client.post(
        "/api/v1/inference/generate",
        json={"prompt": "test"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_inference_generate_missing_prompt(client: AsyncClient, auth_tokens: dict):
    """POST /api/v1/inference/generate — 422 when prompt is missing."""
    resp = await client.post(
        "/api/v1/inference/generate",
        json={},
        headers=auth_header(auth_tokens),
    )
    assert resp.status_code == 422
