#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: SQLAlchemy database engine and session factory for FastAPI Admin app
# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_user = os.environ.get("suser", "skondla")
_password = os.environ.get("spassword", "password")
_host = os.environ.get("shost", "localhost")
_port = os.environ.get("sport", "5432")
_db = os.environ.get("sdatabase", "flaskapp")

SQLALCHEMY_DATABASE_URL = f"postgresql://{_user}:{_password}@{_host}:{_port}/{_db}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
