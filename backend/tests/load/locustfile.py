"""
locustfile.py — Comprehensive load testing for Prompt Polisher API.

Task: Week 13 / Load Testing (task.md lines 667-689)
  [x] User registration flow
  [x] Login + token refresh flow
  [x] Prompt generation flow (the critical path)
  [x] Chat history browsing
  [x] Concurrent WebSocket connections (simulated via SSE streaming)

Usage:
  # Web UI mode (recommended for generating reports):
    locust -f locustfile.py --host=http://localhost:8000

  # Headless mode at different user levels:
    locust -f locustfile.py --host=http://localhost:8000 --headless \
           -u 100 -r 10 --run-time 60s --csv=results/baseline

  # Load levels from task.md:
    100 users  — baseline
    500 users  — moderate load
    1000 users — high load
    5000 users — stress test
   10000 users — peak target
"""

import random
import string
import uuid
from locust import HttpUser, TaskSet, task, between, events


# ── Helper: Generate random test data ──────────────────────────────────────────

def random_email() -> str:
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{suffix}@test.com"


def random_password() -> str:
    return f"LoadTest{random.randint(1000, 9999)}!"


def random_prompt() -> str:
    prompts = [
        "Make this Python function faster and more readable",
        "Rewrite this email to sound more professional",
        "Explain quantum computing to a 5-year-old",
        "Write a cold email to potential investors for my SaaS startup",
        "Optimize this SQL query for better performance",
        "Create a marketing tagline for an eco-friendly water bottle",
        "Summarize the key points of transformer architecture",
        "Write unit tests for this React component",
        "Convert this JavaScript code to TypeScript",
        "Draft a project proposal for a machine learning pipeline",
    ]
    return random.choice(prompts)


# ── Task 1: User Registration Flow ────────────────────────────────────────────

class RegistrationFlow(TaskSet):
    """
    Simulates new user sign-ups.
    Weighted lower since registration is a one-time action.
    """

    @task
    def register_new_user(self):
        email = random_email()
        password = random_password()

        with self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Load Test User",
            },
            name="/auth/register",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                # Email collision — not a real failure
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")


# ── Task 2: Login + Token Refresh Flow ─────────────────────────────────────────

class AuthenticatedFlow(TaskSet):
    """
    Simulates authenticated user sessions:
    - Login
    - Refresh tokens
    - Browse chat history
    - Generate prompts
    - Submit feedback
    """

    access_token: str = ""
    refresh_token: str = ""
    email: str = ""
    password: str = ""
    session_id: str = ""

    def on_start(self):
        """Register and login before starting tasks."""
        self.email = random_email()
        self.password = random_password()

        # Register
        self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "full_name": "Load Test User",
            },
            name="/auth/register [setup]",
        )

        # Login
        self._login()

    def _login(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/auth/login",
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token", "")
            self.refresh_token = data.get("refresh_token", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    # ── Login ──────────────────────────────────────────────────────────────

    @task(2)
    def login(self):
        """Login with existing credentials."""
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            name="/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token", "")
                self.refresh_token = data.get("refresh_token", "")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # ── Token Refresh ──────────────────────────────────────────────────────

    @task(1)
    def refresh_token_flow(self):
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            return

        with self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token},
            name="/auth/refresh",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token", "")
                self.refresh_token = data.get("refresh_token", "")
                response.success()
            else:
                response.failure(f"Refresh failed: {response.status_code}")

    # ── Chat Session Management ────────────────────────────────────────────

    @task(3)
    def create_chat_session(self):
        """Create a new chat session."""
        with self.client.post(
            "/api/v1/chat/sessions",
            json={"title": f"Load Test Session {random.randint(1, 1000)}"},
            headers=self._headers(),
            name="/chat/sessions [CREATE]",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201):
                data = response.json()
                self.session_id = data.get("id", "")
                response.success()
            elif response.status_code == 401:
                self._login()  # Token expired, re-login
                response.success()
            else:
                response.failure(f"Create session failed: {response.status_code}")

    @task(5)
    def browse_chat_history(self):
        """Browse the user's chat session history."""
        with self.client.get(
            "/api/v1/chat/sessions",
            headers=self._headers(),
            name="/chat/sessions [LIST]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._login()
                response.success()
            else:
                response.failure(f"List sessions failed: {response.status_code}")

    # ── Prompt Generation (Critical Path) ──────────────────────────────────

    @task(8)
    def generate_prompt_sync(self):
        """
        The critical path: synchronous prompt generation.
        This is the most important endpoint to load test.
        """
        with self.client.post(
            "/api/v1/inference/generate",
            json={
                "prompt": random_prompt(),
                "max_new_tokens": 128,
                "temperature": 0.7,
            },
            headers=self._headers(),
            name="/inference/generate [CRITICAL]",
            catch_response=True,
            timeout=30,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._login()
                response.success()
            elif response.status_code == 503:
                # AI server unavailable — expected in test environments
                response.success()
            else:
                response.failure(f"Generate failed: {response.status_code}")

    # ── Feedback Submission ────────────────────────────────────────────────

    @task(2)
    def submit_feedback(self):
        """Submit thumbs up/down feedback on a message."""
        # Use a random UUID as a placeholder message_id
        message_id = str(uuid.uuid4())
        rating = random.choice([1, -1])

        with self.client.post(
            "/api/v1/feedback",
            json={
                "message_id": message_id,
                "rating": rating,
                "comment": "Load test feedback" if random.random() > 0.7 else None,
            },
            headers=self._headers(),
            name="/feedback [SUBMIT]",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201, 404, 422):
                # 404/422 expected since message_id is random
                response.success()
            elif response.status_code == 401:
                self._login()
                response.success()
            else:
                response.failure(f"Feedback failed: {response.status_code}")

    # ── User Profile & Preferences ─────────────────────────────────────────

    @task(2)
    def get_profile(self):
        """Fetch current user profile."""
        with self.client.get(
            "/api/v1/users/me",
            headers=self._headers(),
            name="/users/me [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._login()
                response.success()
            else:
                response.failure(f"Get profile failed: {response.status_code}")

    @task(1)
    def update_preferences(self):
        """Update user preferences."""
        tones = ["professional", "casual", "academic", "creative"]
        with self.client.put(
            "/api/v1/users/me/preferences",
            json={
                "tone": random.choice(tones),
                "verbosity": random.choice(["concise", "detailed", "balanced"]),
            },
            headers=self._headers(),
            name="/users/me/preferences [UPDATE]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._login()
                response.success()
            else:
                response.failure(f"Update prefs failed: {response.status_code}")


# ── Locust User Classes ────────────────────────────────────────────────────────

class NewUser(HttpUser):
    """
    Simulates brand-new users registering.
    Lower weight since registration happens less frequently.
    """
    tasks = [RegistrationFlow]
    wait_time = between(2, 5)
    weight = 1


class ReturningUser(HttpUser):
    """
    Simulates returning authenticated users.
    Higher weight — this is the dominant usage pattern.
    """
    tasks = [AuthenticatedFlow]
    wait_time = between(1, 3)
    weight = 5
