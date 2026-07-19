#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: OWASP Top 10 security middleware for FastAPI
# Covers: A01-A10 mitigations at the application middleware layer
# -*- coding: utf-8 -*-

import asyncio
import logging
import re
import time
from collections import defaultdict
from typing import Callable, Optional
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("security")

# ═══════════════════════════════════════════════════════════════════════════════
#  A05 — Security Misconfiguration
#  Add OWASP-recommended security response headers to every response.
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects OWASP-recommended HTTP security headers.

    OWASP A05:2021 — Security Misconfiguration mitigation.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing (A05)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking (A05)
        response.headers["X-Frame-Options"] = "DENY"

        # XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information leakage (A02)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable dangerous browser features (A05)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), usb=(), payment=()"
        )

        # Content Security Policy — restrict resource origins (A03/A05)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "font-src 'self' cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # HSTS — enforce HTTPS (A02)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Disable caching of sensitive pages (A02)
        if request.url.path in ("/login", "/signup", "/auth/token", "/auth/me"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        # Hide server fingerprint (A05)
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        return response


# ═══════════════════════════════════════════════════════════════════════════════
#  A07 — Identification and Authentication Failures
#  Rate-limit all requests; apply stricter limits on authentication endpoints.
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window in-memory rate limiter.

    - General endpoints: 200 requests / minute per IP
    - Auth endpoints (/login, /auth/token, /signup): 10 requests / minute per IP
    - Returns HTTP 429 with Retry-After header when limit exceeded.

    OWASP A07:2021 — Identification and Authentication Failures mitigation.
    """

    AUTH_PATHS = {"/login", "/auth/token", "/signup", "/auth/register"}
    GENERAL_LIMIT = 200
    AUTH_LIMIT = 10
    WINDOW = 60  # seconds

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip = self._client_ip(request)
        path = request.url.path
        limit = self.AUTH_LIMIT if path in self.AUTH_PATHS else self.GENERAL_LIMIT
        key = f"{ip}:{path if path in self.AUTH_PATHS else 'general'}"

        async with self._lock:
            now = time.monotonic()
            cutoff = now - self.WINDOW
            self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]
            if len(self._buckets[key]) >= limit:
                logger.warning("Rate limit exceeded: ip=%s path=%s", ip, path)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please slow down."},
                    headers={"Retry-After": str(self.WINDOW)},
                )
            self._buckets[key].append(now)

        return await call_next(request)

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
#  A09 — Security Logging and Monitoring Failures
#  Log every request with security-relevant attributes.
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Structured security audit log for every HTTP request/response.

    Logs: timestamp, method, path, status, client IP, user-agent, duration.
    OWASP A09:2021 — Security Logging and Monitoring Failures mitigation.
    """

    # Paths that always warrant an audit entry regardless of status
    SENSITIVE_PATHS = {"/login", "/logout", "/signup", "/auth/token",
                       "/auth/refresh", "/auth/me", "/restore", "/attachdb"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.monotonic()
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        status = response.status_code
        path = request.url.path

        # Always log auth paths, errors, and suspicious status codes
        if path in self.SENSITIVE_PATHS or status >= 400:
            level = logging.WARNING if status >= 400 else logging.INFO
            logger.log(
                level,
                "AUDIT method=%s path=%s status=%d ip=%s ua=%r duration_ms=%s",
                request.method,
                path,
                status,
                ip,
                request.headers.get("user-agent", "")[:200],
                duration_ms,
            )

        return response


# ═══════════════════════════════════════════════════════════════════════════════
#  A10 — Server-Side Request Forgery (SSRF)
#  Validate any user-supplied URL / endpoint before making outbound calls.
# ═══════════════════════════════════════════════════════════════════════════════

# Allowed hostnames for DB endpoints (RDS patterns)
_ALLOWED_ENDPOINT_PATTERN = re.compile(
    r"^[a-z0-9\-]+\.[a-z0-9\-]+\.(rds|cluster|aurora)\.amazonaws\.com$",
    re.IGNORECASE,
)

_PRIVATE_IP_RANGES = re.compile(
    r"^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.|0\.|169\.254\.|::1|fc|fd)",
    re.IGNORECASE,
)


def validate_rds_endpoint(endpoint: str) -> str:
    """
    Validate that an RDS endpoint is a legitimate AWS hostname.
    Raises ValueError on suspicious or private-network URLs.

    OWASP A10:2021 — SSRF mitigation.
    """
    endpoint = endpoint.strip()
    if not endpoint:
        raise ValueError("Endpoint must not be empty.")
    if len(endpoint) > 255:
        raise ValueError("Endpoint too long.")

    parsed = urlparse(f"https://{endpoint}")
    host = parsed.hostname or ""

    if _PRIVATE_IP_RANGES.match(host):
        raise ValueError(f"Endpoint '{host}' resolves to a private/reserved address.")

    if not _ALLOWED_ENDPOINT_PATTERN.match(endpoint):
        raise ValueError(
            f"Endpoint '{endpoint}' does not match the expected AWS RDS hostname pattern."
        )
    return endpoint
