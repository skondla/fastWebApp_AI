#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: MCP server bridging this repository's DevSecOps surfaces — the
#          GitHub SARIF/alert stream, pipeline runs, and cluster deployment
#          state — to any MCP client (Claude Code, Claude Desktop).
#          Registered in the repo-root .mcp.json.
#
#          All tools are READ-ONLY (ADR-0005): the server reports; humans
#          and the pipelines act.
#
# Env: GITHUB_TOKEN + GITHUB_REPOSITORY for the GitHub-backed tools;
#      a configured kubectl context for the cluster tool (optional).
# -*- coding: utf-8 -*-

import json
import os
import pathlib
import subprocess
from collections import Counter

import requests
from mcp.server.fastmcp import FastMCP

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

mcp = FastMCP(
    "devsecops",
    instructions=(
        "Read-only DevSecOps state for the fastAPIWebApp repository: "
        "code-scanning alerts, pipeline runs, cluster deployments, and the "
        "SLO/policy documents. Use it to answer posture questions and to "
        "ground triage/incident work in current data."
    ),
)


def _gh() -> tuple[requests.Session, str]:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPOSITORY must be set")
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return session, repo


@mcp.tool()
def security_posture() -> str:
    """Summarize the repository's open code-scanning alerts by severity and
    tool — the fastest answer to 'what does our security posture look like?'."""
    session, repo = _gh()
    resp = session.get(
        f"https://api.github.com/repos/{repo}/code-scanning/alerts",
        params={"state": "open", "per_page": 100}, timeout=30,
    )
    if resp.status_code == 404:
        return "Code scanning has no open alerts (or is not enabled) for this repo."
    resp.raise_for_status()
    alerts = resp.json()
    by_sev = Counter(
        (a.get("rule", {}).get("security_severity_level")
         or a.get("rule", {}).get("severity") or "unknown")
        for a in alerts
    )
    by_tool = Counter(a.get("tool", {}).get("name", "unknown") for a in alerts)
    return json.dumps({
        "open_alerts": len(alerts),
        "by_severity": dict(by_sev),
        "by_tool": dict(by_tool),
    }, indent=2)


@mcp.tool()
def list_security_alerts(severity: str = "", limit: int = 20) -> str:
    """List open code-scanning alerts, optionally filtered by severity
    (critical|high|medium|low). Returns number, tool, rule, file, and URL."""
    session, repo = _gh()
    resp = session.get(
        f"https://api.github.com/repos/{repo}/code-scanning/alerts",
        params={"state": "open", "per_page": 100}, timeout=30,
    )
    if resp.status_code == 404:
        return "[]"
    resp.raise_for_status()
    rows = []
    for a in resp.json():
        rule = a.get("rule") or {}
        sev = rule.get("security_severity_level") or rule.get("severity") or ""
        if severity and sev.lower() != severity.lower():
            continue
        loc = ((a.get("most_recent_instance") or {}).get("location") or {})
        rows.append({
            "number": a.get("number"),
            "tool": (a.get("tool") or {}).get("name"),
            "rule": rule.get("id"),
            "severity": sev,
            "path": loc.get("path"),
            "line": loc.get("start_line"),
            "url": a.get("html_url"),
        })
        if len(rows) >= limit:
            break
    return json.dumps(rows, indent=2)


@mcp.tool()
def pipeline_runs(limit: int = 10) -> str:
    """Latest GitHub Actions workflow runs: name, branch, conclusion, URL.
    Use to answer 'did the last deploy pass?' / 'which gate failed?'."""
    session, repo = _gh()
    resp = session.get(
        f"https://api.github.com/repos/{repo}/actions/runs",
        params={"per_page": min(limit, 50)}, timeout=30,
    )
    resp.raise_for_status()
    runs = [{
        "workflow": r.get("name"),
        "branch": r.get("head_branch"),
        "event": r.get("event"),
        "status": r.get("status"),
        "conclusion": r.get("conclusion"),
        "created_at": r.get("created_at"),
        "url": r.get("html_url"),
    } for r in resp.json().get("workflow_runs", [])]
    return json.dumps(runs, indent=2)


@mcp.tool()
def deployment_status(namespace: str = "fastapi-namespace") -> str:
    """Live deployment state from the current kubectl context: replicas,
    images (with digests), and rollout conditions. Requires cluster access."""
    try:
        out = subprocess.run(
            ["kubectl", "-n", namespace, "get", "deployments", "-o", "json"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout
    except FileNotFoundError:
        return "kubectl is not installed in this environment."
    except subprocess.CalledProcessError as exc:
        return f"kubectl failed: {exc.stderr.strip()}"
    data = json.loads(out)
    result = []
    for d in data.get("items", []):
        status = d.get("status", {})
        result.append({
            "name": d["metadata"]["name"],
            "ready": f'{status.get("readyReplicas", 0)}/{status.get("replicas", 0)}',
            "images": [c["image"] for c in d["spec"]["template"]["spec"]["containers"]],
            "conditions": [
                {"type": c["type"], "status": c["status"]}
                for c in status.get("conditions", [])
            ],
        })
    return json.dumps(result, indent=2)


@mcp.tool()
def read_governance_doc(name: str) -> str:
    """Read one of the repo's operational documents by name:
    slo | incident-response | disaster-recovery | data-classification |
    audit-log-retention | branching-strategy | gap-closure."""
    docs = {
        "slo": "docs/slo.md",
        "incident-response": "docs/governance/incident-response.md",
        "disaster-recovery": "docs/governance/disaster-recovery.md",
        "data-classification": "docs/governance/data-classification.md",
        "audit-log-retention": "docs/governance/audit-log-retention.md",
        "branching-strategy": "docs/governance/branching-strategy.md",
        "gap-closure": "docs/gap-closure.md",
    }
    rel = docs.get(name)
    if not rel:
        return f"Unknown doc '{name}'. One of: {', '.join(sorted(docs))}"
    path = REPO_ROOT / rel
    return path.read_text() if path.exists() else f"{rel} does not exist yet."


if __name__ == "__main__":
    mcp.run()
