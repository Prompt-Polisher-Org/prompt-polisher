"""
test_auth.py — Tests for the authentication endpoints.

Task: Week 3-4 / Authentication System (task.md line 147)
  [ ] Write auth tests (register, login, token refresh, invalid token)

Covers:
  - POST /api/v1/auth/register  (success, duplicate email, missing fields)
  - POST /api/v1/auth/login     (success, wrong password, wrong email)
  - POST /api/v1/auth/refresh   (success, invalid token, access token rejected)
  - POST /api/v1/auth/logout    (returns 204)
  - Token structure validation  (access vs refresh types)
"""
import pytest
from httpx import AsyncClient


# ═══════════════════════════════════════════════════════════════════════════════
#  REGISTER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """A new user should be able to register and get a success response."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "SecurePass123!",
            "full_name": "Alice Smith",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Registration successful! Please log in."
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["full_name"] == "Alice Smith"
    assert data["user"]["is_active"] is True
    # Password should NEVER appear in the response
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with an already-taken email should return 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePass123!",
        "full_name": "First User",
    }
    # First registration — should succeed
    response1 = await client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    # Second registration with same email — should fail
    response2 = await client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """An invalid email format should be rejected by Pydantic validation (422)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_password(client: AsyncClient):
    """Missing required field 'password' should return 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "nopass@example.com"},
    )
    assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """A registered user should be able to log in and receive tokens."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "SecurePass123!",
        },
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # Tokens should be non-empty strings
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Wrong password should return 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@example.com",
            "password": "CorrectPassword1!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpw@example.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """An email that was never registered should return 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "ghost@example.com",
            "password": "AnyPassword1!",
        },
    )
    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
#  TOKEN REFRESH TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, auth_tokens: dict):
    """A valid refresh token should return a new access + refresh token pair."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    """A garbage string should be rejected as an invalid refresh token."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "this.is.not.a.valid.jwt.token"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_with_access_token_rejected(client: AsyncClient, auth_tokens: dict):
    """Using an access token in place of a refresh token should be rejected."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth_tokens["access_token"]},
    )
    assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGOUT TEST
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_logout_returns_204(client: AsyncClient):
    """Logout should return 204 No Content (stateless — client discards tokens)."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 204


# ═══════════════════════════════════════════════════════════════════════════════
#  PROTECTED ROUTE TEST (uses get_current_user dependency)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """Accessing a protected endpoint without a token should return 403."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient, auth_tokens: dict):
    """Accessing a protected endpoint with a valid access token should succeed."""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(client: AsyncClient):
    """A garbage token should be rejected on protected routes."""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.garbage.token"},
    )
    assert response.status_code in (401, 403)
