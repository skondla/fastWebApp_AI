#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: AI triage of the pipeline's SARIF stream. Pulls every open
#          code-scanning alert from the GitHub Security tab (the SARIF the
#          DevSecOps workflows upload), then has Claude deduplicate, rank by
#          real exploitability in this codebase, and propose concrete fixes.
#          Output is a markdown report (job summary + rolling GitHub issue).
#
# Usage:
#   ANTHROPIC_API_KEY=... GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo \
#     python ai/triage/sarif_triage.py --output triage-report.md
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
MAX_ALERTS = 200

SYSTEM_PROMPT = """\
You are the security triage agent for a FastAPI + Kubernetes DevSecOps
reference repository (Python app, GitHub Actions pipelines, Terraform,
EKS/GKE/AKS manifests, Kyverno admission policies).

You receive the repository's open code-scanning alerts (from Bandit, Semgrep,
pip-audit, Trivy, Checkov, GitLeaks). Produce a triage report in GitHub
markdown with exactly these sections:

## Summary
Two or three sentences: overall posture, what changed matters most.

## Top findings (ranked)
A table: Rank | Alert #s | Finding | Severity | Exploitability here | Proposed fix.
- MERGE duplicates (same root cause reported by several tools or in both the
  USER and ADMIN app copies) into one row listing all alert numbers.
- Rank by realistic exploitability IN THIS SYSTEM (internet-facing FastAPI
  app, JWT auth, RDS access), not by the scanner's severity label alone.
- Fixes must be concrete: file, change, and — for dependencies — the version
  to move to.

## Likely false positives
Bullet list with one-line justification each; recommend the precise
suppression (tool config file + rule id), never a blanket disable.

## Recommended next actions
At most five bullets, ordered, each doable in under a day.

Be precise and terse. If there are no open alerts, say the stream is clean
and note the last-checked time.
"""


def fetch_alerts(repo: str, token: str) -> list[dict]:
    """All open code-scanning alerts, paginated, trimmed to triage-relevant fields."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    alerts, page = [], 1
    while len(alerts) < MAX_ALERTS:
        resp = session.get(
            f"https://api.github.com/repos/{repo}/code-scanning/alerts",
            params={"state": "open", "per_page": 100, "page": page},
            timeout=30,
        )
        if resp.status_code == 404:
            # Code scanning not enabled or no alerts ever uploaded.
            return []
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for a in batch:
            rule = a.get("rule") or {}
            inst = a.get("most_recent_instance") or {}
            loc = (inst.get("location") or {})
            alerts.append({
                "number": a.get("number"),
                "tool": ((a.get("tool") or {}).get("name")),
                "rule_id": rule.get("id"),
                "rule_description": rule.get("description"),
                "severity": rule.get("security_severity_level") or rule.get("severity"),
                "path": loc.get("path"),
                "start_line": loc.get("start_line"),
                "message": (inst.get("message") or {}).get("text"),
                "created_at": a.get("created_at"),
                "url": a.get("html_url"),
            })
        page += 1
    return alerts[:MAX_ALERTS]


def triage(alerts: list[dict], repo: str) -> str:
    client = Anthropic()
    user_prompt = (
        f"Repository: {repo}\n"
        f"Checked at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"Open code-scanning alerts ({len(alerts)}):\n\n"
        f"{json.dumps(alerts, indent=1)}"
    )
    # Streaming keeps long triage responses inside HTTP timeouts.
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        message = stream.get_final_message()
    return next(b.text for b in message.content if b.type == "text")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI triage of code-scanning alerts")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"),
                        help="owner/repo (default: $GITHUB_REPOSITORY)")
    parser.add_argument("--output", default="triage-report.md")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not args.repo or not token:
        print("GITHUB_REPOSITORY and GITHUB_TOKEN are required", file=sys.stderr)
        return 2

    alerts = fetch_alerts(args.repo, token)
    print(f"Fetched {len(alerts)} open alerts from {args.repo}")
    report = triage(alerts, args.repo)

    header = (
        f"_Generated by [ai/triage/sarif_triage.py](../../ai/triage/sarif_triage.py) "
        f"({MODEL}) at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — "
        f"advisory only; verify before acting._\n\n"
    )
    with open(args.output, "w") as fh:
        fh.write(header + report + "\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
