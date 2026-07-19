#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: FastAPI application entry point — DB Restore Management Tool
#          Migrated from Flask with JWT OAuth 2.0 authentication
# -*- coding: utf-8 -*-

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

import models
from database import engine
from routers import auth, main_router
from security_middleware import (
    RateLimitMiddleware,
    SecurityAuditMiddleware,
    SecurityHeadersMiddleware,
)

# Create all tables on startup (idempotent — skips existing tables)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DB Restore Management Tool",
    description=(
        "FastAPI conversion of Flask DB restore app. "
        "Authenticate via the **POST /auth/token** OAuth2 endpoint or the web login UI. "
        "All protected routes require a valid JWT Bearer token.\n\n"
        "**Security:** JWT OAuth 2.0 · bcrypt · OWASP Top 10 mitigations · "
        "rate-limiting · security headers · audit logging."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware (applied in LIFO order — last added runs first) ────────────────
# 1. Audit logging — outermost so it captures final status codes
app.add_middleware(SecurityAuditMiddleware)
# 2. Security headers — applied to every response
app.add_middleware(SecurityHeadersMiddleware)
# 3. Rate limiting — reject abusive callers early
app.add_middleware(RateLimitMiddleware)
# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files & templates ─────────────────────────────────────────────────
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # static/ directory is optional

templates = Jinja2Templates(directory="templates")

# ─── Custom exception handler — redirect 401 HTML requests to login ───────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        accept = request.headers.get("Accept", "")
        if "text/html" in accept:
            next_path = request.url.path
            return RedirectResponse(url=f"/login?next={next_path}", status_code=302)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(main_router.router)


# ─── Entrypoint ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    ssl_cert = "/app/certs/certificate.pem"
    ssl_key = "/app/certs/key.pem"
    use_ssl = os.path.exists(ssl_cert) and os.path.exists(ssl_key)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=50443,
        ssl_certfile=ssl_cert if use_ssl else None,
        ssl_keyfile=ssl_key if use_ssl else None,
        reload=False,
    )
