#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Authentication router — web UI login/signup/logout + OAuth2 JWT API.
#          Converted from dockerized/ADMIN/auth.py (Flask) to FastAPI.
# -*- coding: utf-8 -*-

import os
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
import schemas
import security
from database import get_db

router = APIRouter(tags=["authentication"])
templates = Jinja2Templates(directory="templates")

_ACCESS_MIN = security.ACCESS_TOKEN_EXPIRE_MINUTES


# ══════════════════════════════════════════════════════════════════════════════
#  Web UI  —  Login / Signup / Logout
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    signup: Optional[str] = None,
    next: str = "/profile",
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    """Render login form. Redirect to /profile if already authenticated."""
    if current_user:
        return RedirectResponse(url="/profile", status_code=302)
    message = "Account created — please log in." if signup == "success" else None
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": message,
        "next": next,
    })


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: Optional[str] = Form(default=None),
    next: str = Form(default="/profile"),
    db: Session = Depends(get_db),
):
    """Process login form, issue JWT stored in HttpOnly cookie."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password.", "next": next},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    max_age = 604_800 if remember else _ACCESS_MIN * 60
    access_token = security.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(seconds=max_age),
    )
    refresh_token = security.create_refresh_token(data={"sub": user.email})

    response = RedirectResponse(url=next, status_code=302)
    _set_auth_cookies(response, access_token, refresh_token, max_age)
    return response


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    """Render sign-up form."""
    if current_user:
        return RedirectResponse(url="/profile", status_code=302)
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request: Request,
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Create new admin account and redirect to login."""
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Email address already registered."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    hashed = security.get_password_hash(password)
    db.add(models.User(email=email, name=name, password=hashed))
    db.commit()
    return RedirectResponse(url="/login?signup=success", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    """Revoke tokens server-side, clear auth cookies, redirect to login."""
    for cookie_name in ("access_token", "refresh_token"):
        raw = request.cookies.get(cookie_name, "")
        raw = raw[7:] if raw.startswith("Bearer ") else raw
        if raw:
            payload = security.decode_token(raw)
            if payload:
                security.revoke_token(payload)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


# ══════════════════════════════════════════════════════════════════════════════
#  OAuth2 / JWT  API  Endpoints  (JSON)
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/auth/token",
    response_model=schemas.Token,
    summary="OAuth2 Password Flow — get JWT",
    tags=["OAuth2"],
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Standard OAuth2 password-flow token endpoint.

    - **username**: your email address
    - **password**: your password
    - Returns `access_token` (30 min) and `refresh_token` (7 days)
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    return schemas.Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/auth/refresh",
    response_model=schemas.Token,
    summary="Refresh access token",
    tags=["OAuth2"],
)
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    """Exchange a valid refresh token (cookie) for a new access token.

    Rotation-on-use: every exchange issues a NEW refresh token and invalidates
    the presented one. Replaying an already-rotated refresh token revokes the
    whole token family and forces re-login (theft detection).
    """
    refresh_tok = request.cookies.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    payload = security.decode_token(refresh_tok)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_refresh = security.rotate_refresh_token(payload)
    if new_refresh is None:
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Refresh token reuse detected — session revoked. Log in again."},
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

    new_access = security.create_access_token(data={"sub": user.email})
    token_body = schemas.Token(
        access_token=new_access, refresh_token=new_refresh, token_type="bearer"
    )
    response = JSONResponse(content=token_body.model_dump(exclude_none=True))
    _set_auth_cookies(response, new_access, new_refresh, _ACCESS_MIN * 60)
    return response


@router.get(
    "/auth/me",
    response_model=schemas.UserResponse,
    summary="Get current user info",
    tags=["OAuth2"],
)
async def get_me(current_user: models.User = Depends(security.get_current_user)):
    """Return profile of the currently authenticated admin user."""
    return current_user


@router.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new admin user (API)",
    tags=["OAuth2"],
)
async def api_register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """API endpoint to create a new admin account (returns JSON)."""
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed = security.get_password_hash(user_data.password)
    user = models.User(email=user_data.email, name=user_data.name, password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Private helpers ────────────────────────────────────────────────────────────

def _set_auth_cookies(response, access_token: str, refresh_token: str, access_max_age: int):
    # Secure by default (the app serves HTTPS); set COOKIE_SECURE=0 for local HTTP dev.
    secure = os.environ.get("COOKIE_SECURE", "1") != "0"
    cookie_kwargs = dict(httponly=True, samesite="lax", secure=secure)
    response.set_cookie("access_token", f"Bearer {access_token}", max_age=access_max_age, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh_token, max_age=604_800, **cookie_kwargs)
