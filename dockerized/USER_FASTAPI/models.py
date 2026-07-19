#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: SQLAlchemy ORM models (migrated from Flask-SQLAlchemy)
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(1000), nullable=False)
    name = Column(String(1000))


class Userinfo(Base):
    """Audit log table tracking every user action."""
    __tablename__ = "userinfo"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True)   # NOT unique — audit logs need many rows per user
    ip = Column(String(50))
    time = Column(String(60))
    requesttype = Column(String(30))   # e.g. "Initial Login", "DB Restore", "DB Status"
    endpoint = Column(String(300))
    comments = Column(String(200))
