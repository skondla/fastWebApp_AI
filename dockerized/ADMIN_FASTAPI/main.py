#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: FastAPI Admin Portal — authentication and user profile management.
#          Converted from Flask (dockerized/ADMIN/) to FastAPI with JWT OAuth 2.0.
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

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DB Restore Admin Portal",
    description=(
        "FastAPI conversion of the Flask Admin app (dockerized/ADMIN/). "
        "Provides admin user registration and profile management. "
        "Authenticate via **POST /auth/token** (OAuth2) or the web login UI.\n\n"
        "**Security:** JWT OAuth 2.0 · bcrypt · OWASP Top 10 · rate-limiting · "
        "security headers · audit logging."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Middleware applied in LIFO order — last added runs first
app.add_middleware(SecurityAuditMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory="templates")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        if "text/html" in request.headers.get("Accept", ""):
            return RedirectResponse(url=f"/login?next={request.url.path}", status_code=302)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth.router)
app.include_router(main_router.router)


if __name__ == "__main__":
    import os
    ssl_cert = "/app/certs/certificate.pem"
    ssl_key = "/app/certs/key.pem"
    use_ssl = os.path.exists(ssl_cert) and os.path.exists(ssl_key)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=30443,
        ssl_certfile=ssl_cert if use_ssl else None,
        ssl_keyfile=ssl_key if use_ssl else None,
        reload=False,
    )
