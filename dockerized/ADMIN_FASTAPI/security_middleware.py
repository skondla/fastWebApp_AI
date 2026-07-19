#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: OWASP Top 10 security middleware for FastAPI Admin app
# Covers: A01-A10 mitigations at the application middleware layer
# -*- coding: utf-8 -*-

import asyncio
import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects OWASP-recommended HTTP security headers. OWASP A05:2021."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), usb=(), payment=()"
        )
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
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        if request.url.path in ("/login", "/signup", "/auth/token", "/auth/me"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window in-memory rate limiter. OWASP A07:2021.

    - General endpoints: 200 req/min per IP
    - Auth endpoints: 10 req/min per IP
    """

    AUTH_PATHS = {"/login", "/auth/token", "/signup", "/auth/register"}
    GENERAL_LIMIT = 200
    AUTH_LIMIT = 10
    WINDOW = 60

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


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Structured security audit log for every HTTP request/response. OWASP A09:2021."""

    SENSITIVE_PATHS = {"/login", "/logout", "/signup", "/auth/token",
                       "/auth/refresh", "/auth/me", "/profile"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.monotonic()
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        status_code = response.status_code
        path = request.url.path

        if path in self.SENSITIVE_PATHS or status_code >= 400:
            level = logging.WARNING if status_code >= 400 else logging.INFO
            logger.log(
                level,
                "AUDIT method=%s path=%s status=%d ip=%s ua=%r duration_ms=%s",
                request.method,
                path,
                status_code,
                ip,
                request.headers.get("user-agent", "")[:200],
                duration_ms,
            )

        return response
