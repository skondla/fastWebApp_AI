#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: SQLAlchemy ORM models for Admin app (converted from Flask-SQLAlchemy)
#          Source: dockerized/ADMIN/models.py
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    """Primary admin user table — credentials and display name."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(1000), nullable=False)
    name = Column(String(1000))


class Users(Base):
    """Legacy alias of User kept for schema backwards-compatibility."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(1000), nullable=False)
    name = Column(String(1000))
