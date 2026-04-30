import httpx

base = "http://localhost:8000/api/v1/auth"

# Test 1: Register
print("--- TEST 1: Register ---")
r = httpx.post(f"{base}/register", json={"email": "test@example.com", "password": "securepass123", "full_name": "Test User"})
print(f"Status: {r.status_code}")
data = r.json()
access = data.get("access_token", "")
refresh = data.get("refresh_token", "")
print(f"Got access_token: {access[:40]}...")

# Test 2: Login with same credentials
print("\n--- TEST 2: Login ---")
r = httpx.post(f"{base}/login", json={"email": "test@example.com", "password": "securepass123"})
print(f"Status: {r.status_code}")

# Test 3: Login with WRONG password
print("\n--- TEST 3: Wrong Password ---")
r = httpx.post(f"{base}/login", json={"email": "test@example.com", "password": "wrongpass"})
print(f"Status: {r.status_code} (expected 401)")

# Test 4: Protected /me route
print("\n--- TEST 4: GET /me (protected) ---")
r = httpx.get(f"{base}/me", headers={"Authorization": f"Bearer {access}"})
print(f"Status: {r.status_code}")
print(f"User: {r.json()}")

# Test 5: Refresh tokens
print("\n--- TEST 5: Refresh ---")
r = httpx.post(f"{base}/refresh", json={"refresh_token": refresh})
print(f"Status: {r.status_code}")

# Test 6: Duplicate registration
print("\n--- TEST 6: Duplicate Register ---")
r = httpx.post(f"{base}/register", json={"email": "test@example.com", "password": "securepass123", "full_name": "Test User"})
print(f"Status: {r.status_code} (expected 409)")

print("\n=== ALL TESTS DONE ===")
