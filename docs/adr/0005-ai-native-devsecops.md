# ADR-0005: AI-native DevSecOps — agents, MCP, AI review

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

The pipelines produce a high volume of SARIF findings that need human triage;
incidents are diagnosed manually; dependency updates land only when someone
remembers; and the repo's operational knowledge (restore workflow, pipeline
status, security posture) is not accessible to AI assistants in a structured
way.

## Decision

Adopt four AI-native practices, all under `ai/` unless noted:

1. **Agentic workflow orchestration** — the LangGraph + Claude orchestrator
   (`dockerized/USER_FASTAPI/lib/agent_orchestrator.py`) plans and executes
   the restore → status → attach → notify workflow with hard tool budgets.
2. **AI triage of the SARIF stream** — `ai/triage/sarif_triage.py` runs
   nightly, deduplicates and ranks open code-scanning alerts, proposes
   fixes, and maintains a rolling triage issue.
3. **AI code review** — `anthropics/claude-code-action` reviews every PR
   with a security-first checklist. Advisory only; CODEOWNERS approval
   remains mandatory.
4. **MCP integration** — `ai/mcp/devsecops_mcp_server.py` exposes read-only
   DevSecOps operations (security posture, alerts, deployment state) to any
   MCP client (Claude Code, Claude Desktop) via `.mcp.json`.

Plus the supporting modernization: Renovate for dependency proposals,
pre-commit hooks for shift-left scanning, and an AI runbook/postmortem
generator (`ai/runbooks/generate_runbook.py`).

## Consequences

- Humans stay in the loop for every mutating decision: AI output is
  advisory (review comments, triage reports, draft runbooks) — merge, deploy
  and remediation remain gated on human approval.
- An `ANTHROPIC_API_KEY` secret is required in CI; its absence degrades
  gracefully (AI jobs fail independently of the security gates).
- MCP server is read-only by design except for the explicitly-labelled
  restore-workflow tools, which reuse the same guarded code paths as the app.
