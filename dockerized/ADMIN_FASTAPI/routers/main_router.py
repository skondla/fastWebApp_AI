#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Main web UI router — home page and protected admin profile.
#          Converted from dockerized/ADMIN/main.py (Flask) to FastAPI.
# -*- coding: utf-8 -*-

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import models
import security

router = APIRouter(tags=["web-ui"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    """Landing page — visible to unauthenticated visitors."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user,
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    """Protected admin profile page — redirects to /login if not authenticated."""
    if not current_user:
        return RedirectResponse(url="/login?next=/profile", status_code=302)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": current_user,
        "name": current_user.name,
    })
