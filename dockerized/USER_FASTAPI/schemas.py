#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Pydantic v2 request/response schemas for FastAPI
# -*- coding: utf-8 -*-

from pydantic import BaseModel
from typing import Optional


# ─── User schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str

    model_config = {"from_attributes": True}


# ─── Auth / token schemas ──────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ─── DB operation schemas ──────────────────────────────────────────────────────

class RestoreRequest(BaseModel):
    snapshotname: str
    endpoint: str


class StatusRequest(BaseModel):
    snapshotname: str
    endpoint: str


class AttachRequest(BaseModel):
    endpoint: str
    instanceclass: str
