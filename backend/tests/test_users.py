"""
test_users.py — Tests for the user profile and preferences endpoints.

Task: Week 3-4 / User & Preferences API (task.md line 165)
  [ ] Write user + preferences tests

Covers:
  - GET    /api/v1/users/me              (get profile)
  - PUT    /api/v1/users/me              (update display name)
  - DELETE /api/v1/users/me              (soft-delete / deactivate)
  - GET    /api/v1/users/me/preferences  (get defaults, get existing)
  - PUT    /api/v1/users/me/preferences  (update, partial update, invalid values)
"""
import pytest
from httpx import AsyncClient


# ── Helper ────────────────────────────────────────────────────────────────────

def auth_header(tokens: dict) -> dict:
    """Build an Authorization header from a token dict."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /users/me
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_tokens: dict):
    """Authenticated user should see their own profile."""
    response = await client.get("/api/v1/users/me", headers=auth_header(auth_tokens))
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Unauthenticated request should be rejected."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
#  PUT /users/me
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_tokens: dict):
    """User should be able to update their display name."""
    response = await client.put(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"

    # Verify persistence
    verify = await client.get("/api/v1/users/me", headers=auth_header(auth_tokens))
    assert verify.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_profile_null_name(client: AsyncClient, auth_tokens: dict):
    """Sending null full_name should not crash (field is optional)."""
    response = await client.put(
        "/api/v1/users/me",
        json={"full_name": None},
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
#  DELETE /users/me
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_delete_me(client: AsyncClient, auth_tokens: dict):
    """Deleting account should deactivate (soft-delete) the user."""
    response = await client.delete("/api/v1/users/me", headers=auth_header(auth_tokens))
    assert response.status_code == 204

    # After deactivation, the user's token should no longer work
    # (get_current_user checks is_active)
    verify = await client.get("/api/v1/users/me", headers=auth_header(auth_tokens))
    assert verify.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /users/me/preferences
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_preferences_defaults(client: AsyncClient, auth_tokens: dict):
    """First-time fetch should return default preferences."""
    response = await client.get(
        "/api/v1/users/me/preferences",
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 200
    data = response.json()
    # Check defaults from the UserPreference model
    assert data["tone"] == "professional"
    assert data["verbosity"] == "balanced"
    assert data["target_model"] == "General"
    assert data["domain"] == "general"
    assert data["custom_instructions"] is None


# ═══════════════════════════════════════════════════════════════════════════════
#  PUT /users/me/preferences
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_update_preferences_full(client: AsyncClient, auth_tokens: dict):
    """User should be able to update all preference fields at once."""
    response = await client.put(
        "/api/v1/users/me/preferences",
        json={
            "tone": "casual",
            "verbosity": "concise",
            "target_model": "Claude",
            "domain": "coding",
            "custom_instructions": "Use Python examples.",
        },
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tone"] == "casual"
    assert data["verbosity"] == "concise"
    assert data["target_model"] == "Claude"
    assert data["domain"] == "coding"
    assert data["custom_instructions"] == "Use Python examples."


@pytest.mark.asyncio
async def test_update_preferences_partial(client: AsyncClient, auth_tokens: dict):
    """Partial update should only change the provided fields."""
    # Set initial values
    await client.put(
        "/api/v1/users/me/preferences",
        json={"tone": "academic", "domain": "writing"},
        headers=auth_header(auth_tokens),
    )
    # Partial update — only change tone
    response = await client.put(
        "/api/v1/users/me/preferences",
        json={"tone": "creative"},
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tone"] == "creative"
    # domain should remain unchanged from the first update
    assert data["domain"] == "writing"


@pytest.mark.asyncio
async def test_update_preferences_invalid_tone(client: AsyncClient, auth_tokens: dict):
    """Invalid tone value should be rejected with 422."""
    response = await client.put(
        "/api/v1/users/me/preferences",
        json={"tone": "super_fancy_invalid"},
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_preferences_invalid_domain(client: AsyncClient, auth_tokens: dict):
    """Invalid domain value should be rejected with 422."""
    response = await client.put(
        "/api/v1/users/me/preferences",
        json={"domain": "nonexistent_domain"},
        headers=auth_header(auth_tokens),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_preferences_unauthenticated(client: AsyncClient):
    """Unauthenticated requests to preferences should be rejected."""
    get_resp = await client.get("/api/v1/users/me/preferences")
    assert get_resp.status_code in (401, 403)

    put_resp = await client.put(
        "/api/v1/users/me/preferences",
        json={"tone": "casual"},
    )
    assert put_resp.status_code in (401, 403)
