#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Main web UI router — home page, DB restore / status / attach pages,
#          and the corresponding POST handlers that call AWS RDS operations.
#          Migrated from Flask blueprints (main.py + auth.py DB operations).
# -*- coding: utf-8 -*-

import datetime
from typing import Optional

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
import rds_ops
import security
from agent_orchestrator import RestoreOrchestrator
from database import get_db

router = APIRouter(tags=["web-ui"])
templates = Jinja2Templates(directory="templates")


# ═══════════════════════════════════════════════════════════════════════════════
#  Helper utilities
# ═══════════════════════════════════════════════════════════════════════════════

def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _log_user_action(
    db: Session,
    email: str,
    ip: str,
    requesttype: str,
    endpoint: str,
    comments: str,
):
    """Persist a row in the userinfo audit-log table."""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    info = models.Userinfo(
        email=email,
        ip=ip,
        time=now,
        requesttype=requesttype,
        endpoint=endpoint,
        comments=comments,
    )
    db.add(info)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  Home
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  Restore DB
# ═══════════════════════════════════════════════════════════════════════════════

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
        rds_ops.db_restore(snapshot_name, endpoint)
    except ClientError as exc:
        return PlainTextResponse(f"Restore error: {exc}", status_code=500)

    try:
        db_state = rds_ops.db_status(endpoint, snapshot_name)
    except ClientError as exc:
        return PlainTextResponse(f"Status error: {exc}", status_code=500)

    ip = _get_client_ip(request)
    _log_user_action(db, current_user.email, ip, "DB Restore", new_endpoint, snapshot_name)
    rds_ops.slack_post(snapshot_name, new_endpoint, db_state, "Restoring", "dbRestore")
    rds_ops.send_email(snapshot_name, endpoint, db_state)

    return PlainTextResponse(
        f"Database: {snapshot_name} is being restored. "
        f"New Endpoint: {new_endpoint}. DB Restore status: {db_state}",
        status_code=202,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  DB Status
# ═══════════════════════════════════════════════════════════════════════════════

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
        db_state = rds_ops.db_status(endpoint, snapshot_name)
    except ClientError as exc:
        return PlainTextResponse(f"Status error: {exc}", status_code=500)

    ip = _get_client_ip(request)
    _log_user_action(db, current_user.email, ip, "DB Status", endpoint, snapshot_name)
    rds_ops.slack_post(snapshot_name, endpoint, db_state, "Status of", "dbStatus")
    rds_ops.send_email(snapshot_name, endpoint, db_state)

    return PlainTextResponse(
        f"Database: {snapshot_name} status: {db_state}",
        status_code=202,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Attach DB Instance to Cluster
# ═══════════════════════════════════════════════════════════════════════════════

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
            f"{endpoint} is not a cluster and cannot attach to a cluster", status_code=400
        )

    try:
        instance_name = rds_ops.db_attach(endpoint, instance_class)
    except ClientError as exc:
        return PlainTextResponse(f"Attach error: {exc}", status_code=500)

    today = datetime.datetime.now().strftime("%m%d-%H%M")
    new_endpoint = f"{instance_name}.{endpoint.split('.', 1)[1]}"

    ip = _get_client_ip(request)
    _log_user_action(db, current_user.email, ip, "DB Attach", endpoint, instance_name)
    rds_ops.slack_post(instance_name, new_endpoint, "being attached", "Attaching", "dbAttach")
    rds_ops.send_email(instance_name, endpoint, "attached")

    return PlainTextResponse(
        f"Database Instance: {instance_name} is being attached to cluster. "
        f"New Endpoint: {new_endpoint}",
        status_code=202,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Agentic Restore Workflow — orchestrates restore -> status -> attach -> notify
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/agent/restore-workflow", response_class=HTMLResponse)
async def agent_workflow_page(
    request: Request,
    current_user: Optional[models.User] = Depends(security.get_optional_user),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/agent/restore-workflow", status_code=302)
    return templates.TemplateResponse("agent_workflow.html", {
        "request": request,
        "current_user": current_user,
        "name": current_user.name,
        "client_ip": _get_client_ip(request),
    })


@router.post("/agent/restore-workflow", response_class=PlainTextResponse)
async def agent_workflow_post(
    request: Request,
    snapshotname: str = Form(...),
    endpoint: str = Form(...),
    instanceclass: str = Form(""),
    goal: str = Form(""),
    current_user: Optional[models.User] = Depends(security.get_optional_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        return RedirectResponse(url="/login?next=/agent/restore-workflow", status_code=302)

    snapshot_name = snapshotname.strip()
    source_endpoint = endpoint.strip()
    target_instance_class = instanceclass.strip() or None
    ip = _get_client_ip(request)

    default_goal = f"Restore snapshot {snapshot_name} and report the resulting status."
    if target_instance_class:
        default_goal += f" Then attach a {target_instance_class} instance if the endpoint is a cluster."
    operator_goal = goal.strip() or default_goal

    def on_step(tool: str, tool_input: str, result: str) -> None:
        _log_user_action(db, current_user.email, ip, f"Agent: {tool}", source_endpoint, result[:200])

    try:
        orchestrator = RestoreOrchestrator()
    except RuntimeError as exc:
        return PlainTextResponse(f"Agent orchestration unavailable: {exc}", status_code=503)

    try:
        result = orchestrator.run(
            goal=operator_goal,
            snapshot_name=snapshot_name,
            source_endpoint=source_endpoint,
            target_instance_class=target_instance_class,
            on_step=on_step,
        )
    except Exception as exc:  # Anthropic API errors, unexpected tool failures, etc.
        return PlainTextResponse(f"Agent workflow error: {exc}", status_code=500)

    transcript_lines = [
        f"[{i}] {step.tool}({step.input}) -> {step.result}"
        for i, step in enumerate(result.steps, start=1)
    ]
    body = "\n".join(transcript_lines + ["", result.final_message])
    return PlainTextResponse(body, status_code=202)
