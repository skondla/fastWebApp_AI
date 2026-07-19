#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: JWT OAuth 2.0 security utilities for the FastAPI Admin app.
#          Token creation/verification, password hashing, dependency injection.
#          RS256 asymmetric signing (keypair via env), refresh-token rotation
#          with reuse detection, and a server-side jti denylist for revocation.
# -*- coding: utf-8 -*-

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
import token_store
from database import get_db, SessionLocal

logger = logging.getLogger("security")

# ─── Signing configuration ────────────────────────────────────────────────────
# Preferred: RS256 with an asymmetric keypair. Provide the PEM material via
#   JWT_PRIVATE_KEY / JWT_PUBLIC_KEY (inline PEM) or
#   JWT_PRIVATE_KEY_FILE / JWT_PUBLIC_KEY_FILE (paths, e.g. a Secrets Store CSI
#   mount under /mnt/secrets-store). Rotate by publishing the new public key
#   alongside the old one is out of scope here — rotate keypair + roll pods.
# Fallback: HS256 with SECRET_KEY, for local development only.

def _read_env_or_file(env_key: str, file_key: str) -> Optional[str]:
    value = os.environ.get(env_key)
    if value:
        return value
    path = os.environ.get(file_key)
    if path and os.path.exists(path):
        with open(path, "r") as fh:
            return fh.read()
    return None


_PRIVATE_KEY = _read_env_or_file("JWT_PRIVATE_KEY", "JWT_PRIVATE_KEY_FILE")
_PUBLIC_KEY = _read_env_or_file("JWT_PUBLIC_KEY", "JWT_PUBLIC_KEY_FILE")

if _PRIVATE_KEY and _PUBLIC_KEY:
    ALGORITHM = "RS256"
    _SIGNING_KEY = _PRIVATE_KEY
    _VERIFY_KEY = _PUBLIC_KEY
else:
    ALGORITHM = "HS256"
    _SIGNING_KEY = _VERIFY_KEY = os.environ.get(
        "SECRET_KEY", "9OLWxND4o83j4K4iuopO-CHANGE-IN-PRODUCTION"
    )
    logger.warning(
        "JWT signing: falling back to HS256 with a shared SECRET_KEY. "
        "Set JWT_PRIVATE_KEY(_FILE)/JWT_PUBLIC_KEY(_FILE) for RS256 in production."
    )

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ─── Password hashing ─────────────────────────────────────────────────────────
# bcrypt for new passwords; werkzeug pbkdf2:sha256 handled explicitly below for
# migration safety from the legacy Flask app.
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
    payload.update({"exp": expire, "type": "access", "jti": uuid.uuid4().hex})
    return jwt.encode(payload, _SIGNING_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, family_id: Optional[str] = None) -> str:
    """Issue a refresh token belonging to a rotation family.

    A fresh login starts a new family; each /auth/refresh exchange rotates the
    family's current jti. Presenting a rotated-out token is treated as theft
    and revokes the whole family (see rotate_refresh_token).
    """
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4().hex
    fid = family_id or uuid.uuid4().hex
    payload.update({"exp": expire, "type": "refresh", "jti": jti, "fid": fid})
    token_store.register_refresh(fid, jti,
                                 REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return jwt.encode(payload, _SIGNING_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode + verify signature and expiry, then check server-side revocation."""
    try:
        payload = jwt.decode(token, _VERIFY_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    jti = payload.get("jti")
    if jti and token_store.is_denylisted(jti):
        return None
    return payload


def rotate_refresh_token(payload: dict) -> Optional[str]:
    """Exchange a valid refresh payload for a new refresh token (rotation).

    Returns the new refresh token, or None when reuse was detected — in that
    case the family has been revoked and the caller must force re-login.
    """
    fid, jti = payload.get("fid"), payload.get("jti")
    if not fid or not jti:
        return None  # pre-rotation legacy token — force re-login
    new_jti = uuid.uuid4().hex
    ttl = REFRESH_TOKEN_EXPIRE_DAYS * 86400
    if not token_store.rotate_refresh(fid, jti, new_jti, ttl):
        return None
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_payload = {"sub": payload.get("sub"), "exp": expire,
                   "type": "refresh", "jti": new_jti, "fid": fid}
    return jwt.encode(new_payload, _SIGNING_KEY, algorithm=ALGORITHM)


def revoke_token(payload: dict) -> None:
    """Server-side revocation: denylist the jti until its natural expiry and
    kill the refresh family if the payload names one."""
    jti = payload.get("jti")
    if jti:
        exp = payload.get("exp")
        remaining = 60
        if exp:
            remaining = max(int(exp - datetime.utcnow().timestamp()), 1)
        token_store.denylist_jti(jti, remaining)
    fid = payload.get("fid")
    if fid:
        token_store.revoke_family(fid)


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
