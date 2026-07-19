# AI-Native DevSecOps Layer

The agentic/AI practices from the modernization plan, implemented. Everything
here is **advisory-by-default**: AI drafts, ranks and proposes; humans merge,
deploy and remediate (see [ADR-0005](../docs/adr/0005-ai-native-devsecops.md)).

| Capability | Entry point | Runs |
|---|---|---|
| Agentic restore workflow | [`dockerized/USER_FASTAPI/lib/agent_orchestrator.py`](../dockerized/USER_FASTAPI/lib/agent_orchestrator.py) | In-app (LangGraph + Claude), `/agent/restore-workflow` |
| AI triage of the SARIF stream | [`triage/sarif_triage.py`](triage/sarif_triage.py) | Nightly via [`actions/ai-security-triage.yml`](../actions/ai-security-triage.yml), or locally |
| AI code review on PRs | [`actions/ai-code-review.yml`](../actions/ai-code-review.yml) | Every pull request (Claude Code action) |
| AI runbooks / postmortems | [`runbooks/generate_runbook.py`](runbooks/generate_runbook.py) | On demand |
| MCP server (Git/SARIF/cluster bridge) | [`mcp/devsecops_mcp_server.py`](mcp/devsecops_mcp_server.py) | Registered in [`.mcp.json`](../.mcp.json) for Claude Code / Desktop |
| Automated dependency proposals | [`renovate.json`](../renovate.json) | Renovate app |
| Shift-left hooks | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Developer keyboard |

## Setup

```bash
pip install -r ai/requirements.txt
export ANTHROPIC_API_KEY=...      # for triage + runbooks
export GITHUB_TOKEN=...           # repo-scoped, for alerts/pipeline access
export GITHUB_REPOSITORY=owner/repo
```

## Examples

```bash
# Triage all open code-scanning alerts into a ranked, deduplicated report
python ai/triage/sarif_triage.py --output triage.md

# Draft a blameless postmortem from an incident channel log
python ai/runbooks/generate_runbook.py postmortem --input incident-log.txt

# Draft an operational runbook for an alert
python ai/runbooks/generate_runbook.py runbook \
  --title "FastApiErrorBudgetFastBurn" \
  --input kubernetes/observability/prometheus-rules.yaml

# Use the MCP server from Claude Code (auto-detected via .mcp.json):
#   "What's our current security posture?"
#   "Any failing pipeline runs today?"
```
