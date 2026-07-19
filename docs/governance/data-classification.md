# Data Classification & Handling

## Classes

| Class | Definition | Examples here | Handling |
|---|---|---|---|
| **Secret** | Compromise grants access | JWT signing keypair, DB credentials, cloud OIDC role trust, Slack webhook, `ANTHROPIC_API_KEY` | Cloud secret manager only, mounted via Secrets Store CSI; never in env.sh, git, logs, or AI prompts |
| **PII** | Identifies a person | `user` table: email, name; audit log client IPs | Encrypted at rest (RDS) and in transit (TLS end-to-end); access via the apps only; retention per audit-log policy; deletion on verified request within 30 days |
| **Sensitive-internal** | Operational exposure | RDS endpoints, snapshot names, SARIF findings, triage reports | Repo/org-internal; endpoints validated by the SSRF guard before use |
| **Public** | Intended for publication | Source code, manifests, docs | MIT-licensed |

## PII inventory & flows

- **Collected:** email + name at signup; password stored only as a bcrypt
  hash (legacy werkzeug hashes verified then upgraded on login).
- **Flows:** browser → app (TLS) → PostgreSQL (TLS). PII is **not** sent to
  Slack notifications, Prometheus metrics, traces, or the Anthropic API —
  the agent orchestrator and triage agent receive infrastructure
  identifiers and findings, never user rows.
- **Logs:** the security audit log records IP + user-agent (PII-adjacent);
  emails are not logged. Retention per
  [audit-log-retention.md](audit-log-retention.md).

## Rules

1. New data fields must be classified in the PR that introduces them
   (PR template prompts for this).
2. Anything class Secret entering git history is an incident: rotate first,
   then scrub history — TruffleHog/GitLeaks gates plus the pre-commit hook
   exist to make this rare.
3. AI tooling (`ai/`, PR review) operates on code and findings only. Do not
   paste production data into prompts.
