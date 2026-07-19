#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Pydantic v2 request/response schemas for FastAPI Admin app
# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
