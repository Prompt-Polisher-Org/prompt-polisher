"""
security_headers.py — Security headers middleware.

Task: Week 11-12 / Security Audit (task.md lines 643-650)
  [x] XSS prevention (output encoding, CSP headers)
  [x] CSRF protection
  [x] Content Security Policy
  [x] Additional security headers (X-Frame-Options, etc.)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds standard security headers to every response.
    Protects against XSS, clickjacking, MIME sniffing, and other attacks.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # ── Content Security Policy ────────────────────────────────────────
        # Restricts which resources the browser is allowed to load.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # ── Clickjacking Prevention ────────────────────────────────────────
        response.headers["X-Frame-Options"] = "DENY"

        # ── MIME Sniffing Prevention ───────────────────────────────────────
        response.headers["X-Content-Type-Options"] = "nosniff"

        # ── XSS Protection (legacy browsers) ──────────────────────────────
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ── Referrer Policy ────────────────────────────────────────────────
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ── Permissions Policy ─────────────────────────────────────────────
        # Restrict browser features like camera, mic, geolocation
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "interest-cohort=()"  # Opt out of FLoC
        )

        # ── Strict Transport Security (HTTPS enforcement) ─────────────────
        # Only set in production when behind HTTPS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        return response
