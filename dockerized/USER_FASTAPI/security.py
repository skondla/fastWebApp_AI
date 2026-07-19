#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: JWT OAuth 2.0 security utilities — token creation, verification,
#          password hashing, and FastAPI dependency injection helpers.
# -*- coding: utf-8 -*-

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
from database import get_db, SessionLocal

# ─── Configuration ─────────────────────────────────────────────────────────────
SECRET_KEY: str = os.environ.get(
    "SECRET_KEY", "s3dgMHEPR47DlmXNmb9hvHfj99U53beO-CHANGE-IN-PRODUCTION"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ─── Password hashing ─────────────────────────────────────────────────────────
# bcrypt for new passwords; passlib also handles werkzeug pbkdf2:sha256 via
# the "django" scheme, but we handle it explicitly below for migration safety.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── OAuth2 Bearer scheme ─────────────────────────────────────────────────────
# auto_error=False so we can fall back to the HttpOnly cookie.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


# ─── Password utilities ────────────────────────────────────────────────────────

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password.

    Supports:
    - bcrypt (new passwords created by this FastAPI app)
    - werkzeug pbkdf2:sha256 (passwords created by the Flask app)
    """
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        pass
    # Fallback: werkzeug pbkdf2:sha256:... format used by Flask predecessor
    try:
        from werkzeug.security import check_password_hash  # type: ignore
        return check_password_hash(hashed, plain)
    except Exception:
        return False


# ─── JWT utilities ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def _token_from_request(request: Request, bearer_token: Optional[str]) -> Optional[str]:
    """Extract raw JWT from Authorization header or HttpOnly cookie."""
    if bearer_token:
        return bearer_token
    cookie = request.cookies.get("access_token", "")
    if cookie.startswith("Bearer "):
        return cookie[7:]
    return cookie or None


# ─── FastAPI dependency helpers ───────────────────────────────────────────────

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Dependency for API routes — raises HTTP 401 if not authenticated."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    raw = _token_from_request(request, token)
    if not raw:
        raise exc
    payload = decode_token(raw)
    if not payload or payload.get("type") != "access":
        raise exc
    email: Optional[str] = payload.get("sub")
    if not email:
        raise exc
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise exc
    return user


def get_optional_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    """Dependency for web UI routes — returns None instead of raising 401."""
    try:
        return get_current_user(request, token, db)
    except HTTPException:
        return None


def get_current_user_from_cookie(request: Request) -> Optional[models.User]:
    """Standalone helper (no Depends) for use inside other dependencies/helpers."""
    cookie = request.cookies.get("access_token", "")
    raw = cookie[7:] if cookie.startswith("Bearer ") else cookie or None
    if not raw:
        return None
    payload = decode_token(raw)
    if not payload or payload.get("type") != "access":
        return None
    email = payload.get("sub")
    if not email:
        return None
    db = SessionLocal()
    try:
        return db.query(models.User).filter(models.User.email == email).first()
    finally:
        db.close()
