#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Main web UI router — home, DB restore/status/attachdb pages and POST handlers.
#          Converted from Flask Blueprints (USER/main.py + USER/auth.py DB operations).
# -*- coding: utf-8 -*-

import datetime
import json
import os
from typing import Optional

import requests as http_requests
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
import security
from database import get_db
from rdsAdmin import RDSCreate, RDSDescribe, RDSRestore

router = APIRouter(tags=["web-ui"])
templates = Jinja2Templates(directory="templates")


# ══════════════════════════════════════════════════════════════════════════════
#  Shared helpers (extracted from Flask auth.py)
# ══════════════════════════════════════════════════════════════════════════════

def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _log_user_action(
    db: Session, email: str, ip: str,
    requesttype: str, endpoint: str, comments: str,
):
    """Persist a row in the userinfo audit-log table."""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    db.add(models.Userinfo(
        email=email, ip=ip, time=now,
        requesttype=requesttype, endpoint=endpoint, comments=comments,
    ))
    db.commit()


def _slack_post(snapshot_name: str, new_endpoint: str, db_state: str, action: str, username: str):
    webhook_url = os.environ.get(
        "SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/services/XXXX/XXXX/xyyyybbbbssssrm01",
    )
    today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    payload = {
        "channel": "@skondla",
        "username": username,
        "text": (
            f"{today}: {action} Database: {snapshot_name} is {db_state} "
            f"for dB Endpoint: {new_endpoint}"
        ),
        "icon_emoji": ":man-biking:",
    }
    try:
        resp = http_requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        if resp.status_code != 200:
            print(f"Slack error {resp.status_code}: {resp.text}")
    except Exception as exc:
        print(f"Slack post failed: {exc}")


def _send_email(snapshot_name: str, endpoint: str, db_state: str):
    try:
        with open("/app/email_distro") as f:
            email_distro = f.read().strip()
        os.system(
            f"echo 'dB: {snapshot_name} is {db_state} for dB: {endpoint}'"
            f" | mailx -s 'dB Restore' {email_distro}"
        )
    except Exception as exc:
        print(f"Email send failed: {exc}")


def _db_status(endpoint: str, new_endpoint: str) -> str:
    if "cluster" in endpoint:
        return RDSDescribe().getDBClusterStatus(new_endpoint)
    return RDSDescribe().getDBInstanceStatus(new_endpoint)


def _db_restore(snapshot_name: str, db_url: str) -> None:
    info = RDSDescribe().dbInstanceInfo(db_url)
    security_group = str(info[0])
    subnet = str(info[1])
    engine = str(info[2])
    engine_version = str(info[4])
    if "cluster" in db_url:
        RDSRestore().restore_db_cluster_from_snapshot(
            snapshot_name, snapshot_name, subnet, security_group, engine, engine_version
        )
    else:
        instance_class = str(info[5])
        RDSRestore().restore_db_instance_from_db_snapshot(
            snapshot_name, snapshot_name, subnet, security_group, engine, instance_class
        )


def _db_attach(db_url: str, instance_class: str) -> str:
    today = datetime.datetime.now().strftime("%m%d-%H%M")
    cluster_name = db_url.split(".")[0]
    instance_name = f"{cluster_name}-{today}"
    info = RDSDescribe().dbInstanceInfo(db_url)
    engine = str(info[2])
    engine_version = str(info[4])
    RDSCreate().create_db_cluster_instance(
        instance_name, cluster_name, engine, engine_version, instance_class
    )
    return instance_name


# ══════════════════════════════════════════════════════════════════════════════
#  Home
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  Restore DB
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/restore", response_class=HTMLResponse)
async def restore_page(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/restore", status_code=302)
    return templates.TemplateResponse("restore.html", {
        "request": request,
        "current_user": current_user,
        "name": current_user.name,
        "client_ip": _get_client_ip(request),
    })


@router.post("/restore", response_class=PlainTextResponse)
async def restore_post(
    request: Request,
    snapshotname: str = Form(...),
    endpoint: str = Form(...),
    current_user: Optional[models.User] = Depends(security.get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/restore", status_code=302)

    snapshot_name = snapshotname.strip()
    endpoint = endpoint.strip()
    new_endpoint = snapshot_name + "." + endpoint.split(".", 1)[1]

    try:
        _db_restore(snapshot_name, endpoint)
    except ClientError as exc:
        return PlainTextResponse(f"Restore error: {exc}", status_code=500)

    try:
        db_state = _db_status(endpoint, snapshot_name)
    except ClientError as exc:
        return PlainTextResponse(f"Status error: {exc}", status_code=500)

    _log_user_action(db, current_user.email, _get_client_ip(request), "DB Restore", new_endpoint, snapshot_name)
    _slack_post(snapshot_name, new_endpoint, db_state, "Restoring", "dbRestore")
    _send_email(snapshot_name, endpoint, db_state)

    return PlainTextResponse(
        f"Database: {snapshot_name} is being restored. "
        f"New Endpoint: {new_endpoint}. DB Restore status: {db_state}",
        status_code=202,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  DB Status
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/status", response_class=HTMLResponse)
async def status_page(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/status", status_code=302)
    return templates.TemplateResponse("status.html", {
        "request": request,
        "current_user": current_user,
        "name": current_user.name,
        "client_ip": _get_client_ip(request),
    })


@router.post("/status", response_class=PlainTextResponse)
async def status_post(
    request: Request,
    snapshotname: str = Form(...),
    endpoint: str = Form(...),
    current_user: Optional[models.User] = Depends(security.get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/status", status_code=302)

    snapshot_name = snapshotname.strip()
    endpoint = endpoint.strip()

    try:
        db_state = _db_status(endpoint, snapshot_name)
    except ClientError as exc:
        return PlainTextResponse(f"Status error: {exc}", status_code=500)

    _log_user_action(db, current_user.email, _get_client_ip(request), "DB Status", endpoint, snapshot_name)
    _slack_post(snapshot_name, endpoint, db_state, "Status of", "dbStatus")
    _send_email(snapshot_name, endpoint, db_state)

    return PlainTextResponse(
        f"Database: {snapshot_name} status: {db_state}",
        status_code=202,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Attach DB Instance to Cluster
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/attachdb", response_class=HTMLResponse)
async def attachdb_page(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/attachdb", status_code=302)
    return templates.TemplateResponse("attachdb.html", {
        "request": request,
        "current_user": current_user,
        "name": current_user.name,
        "client_ip": _get_client_ip(request),
    })


@router.post("/attachdb", response_class=PlainTextResponse)
async def attachdb_post(
    request: Request,
    endpoint: str = Form(...),
    instanceclass: str = Form(...),
    current_user: Optional[models.User] = Depends(security.get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/attachdb", status_code=302)

    endpoint = endpoint.strip()
    instance_class = instanceclass.strip()

    if "cluster" not in endpoint:
        return PlainTextResponse(
            f"{endpoint} is not a cluster and cannot attach to a cluster",
            status_code=400,
        )

    try:
        instance_name = _db_attach(endpoint, instance_class)
    except ClientError as exc:
        return PlainTextResponse(f"Attach error: {exc}", status_code=500)

    new_endpoint = f"{instance_name}.{endpoint.split('.', 1)[1]}"

    _log_user_action(db, current_user.email, _get_client_ip(request), "DB Attach", endpoint, instance_name)
    _slack_post(instance_name, new_endpoint, "being attached", "Attaching", "dbAttach")
    _send_email(instance_name, endpoint, "attached")

    return PlainTextResponse(
        f"Database Instance: {instance_name} is being attached to cluster. "
        f"New Endpoint: {new_endpoint}",
        status_code=202,
    )
