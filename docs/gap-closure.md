# Gap Closure Matrix

Every finding from the *Exhaustive Expert Analysis* deck (8 gap categories,
45+ findings), mapped to its implementation in this repository. Status:
✅ closed · 🟡 partially closed (with note) · 📋 documented decision (ADR).

## 1. Enforcement — "Scanners that report but cannot block"

| Finding | Status | Where |
|---|---|---|
| `\|\| true` on Bandit / Semgrep / pip-audit | ✅ | All scanners blocking in [actions/](../actions/) — Bandit `--severity-level high`, Semgrep `--error`, pip-audit plain exit code |
| Trivy `exit-code: 0` | ✅ | `exit-code: "1"` on HIGH/CRITICAL (FS + image scans, all clouds) |
| Checkov `soft_fail: true` | ✅ | `soft_fail: false` (Terraform + K8s, all clouds) |
| ZAP `fail_action: false` | ✅ | `fail_action: true` on main; FAIL-level alerts block PRs in the `dast-pr` job |
| Secret-scan findings non-blocking | ✅ | TruffleHog `--only-verified` + GitLeaks, blocking |
| Branch-protection required checks | 📋 | Settings checklist in [governance/branching-strategy.md](governance/branching-strategy.md) (repo-settings action, not code) |
| Warn-then-block rollout | 📋 | Kyverno Audit→Enforce procedure in [kubernetes/policies/README.md](../kubernetes/policies/README.md) |

## 2. Supply chain — "Unsigned images, no SBOM, no provenance"

| Finding | Status | Where |
|---|---|---|
| Cosign signing | ✅ | Keyless sign step in every workflow's `sign-and-sbom` job |
| SBOM | ✅ | Syft (anchore/sbom-action) SPDX SBOM, attached with `cosign attest --type spdxjson` |
| SLSA provenance | ✅ | Provenance predicate generated per build, attached with `cosign attest --type slsaprovenance1` (all three workflows) |
| Admission verification | ✅ | [kubernetes/policies/verify-image-signatures.yaml](../kubernetes/policies/verify-image-signatures.yaml) — signature **and** SBOM **and** provenance must validate; tags mutated to digests |

## 3. Secrets & identity — "Dual pattern, static JWT keys"

| Finding | Status | Where |
|---|---|---|
| JWT HS256 static key | ✅ | RS256 keypair via env/CSI mount, HS256 only as warned dev fallback — `dockerized/*/security.py`, [ADR-0002](adr/0002-jwt-rs256-rotation-revocation.md) |
| No refresh rotation | ✅ | Rotation-on-use with families + reuse detection (`rotate_refresh_token`, `token_store.py`) |
| No server-side revocation | ✅ | `jti` denylist checked on every decode; logout revokes access jti + refresh family |
| Dual secrets pattern | ✅ | Secrets Store CSI is the single runtime path (`secretproviderclass.yaml` in manifests); JWT keys load from the CSI mount |
| Static creds in env.sh | ✅ | Legacy Flask dirs only; FastAPI startup scripts contain no cloud keys; CI is OIDC-only |
| Cookies `secure=False` | ✅ | Secure+HttpOnly+SameSite by default (`COOKIE_SECURE=0` opt-out for local dev) |
| CORS wildcard with credentials | ✅ | `CORS_ALLOW_ORIGINS` allowlist; credentials disabled under wildcard (`main.py`, both apps) |

## 4. Runtime & policy — "Hardened pods on an unpoliced cluster"

| Finding | Status | Where |
|---|---|---|
| NetworkPolicy default-allow | ✅ | Per-app `networkpolicy.yaml` + Kyverno-generated default-deny in every namespace ([require-networkpolicy.yaml](../kubernetes/policies/require-networkpolicy.yaml)) |
| PSS not enforced | ✅ | Namespace `enforce: restricted` labels + Kyverno policy requiring them ([require-pod-security.yaml](../kubernetes/policies/require-pod-security.yaml)) |
| Read-only root FS on app pods | ✅ | Set in `deployment.yaml` and cluster-enforced by Kyverno |
| No policy-as-code admission | ✅ | Kyverno: signed images, PSS, netpol generation, `:latest` ban ([kubernetes/policies/](../kubernetes/policies/), [ADR-0003](adr/0003-kyverno-admission-control.md)) |
| No workflow concurrency guard | ✅ | `concurrency:` block in all DevSecOps workflows |
| Service mesh / mTLS | 📋 | Deliberately deferred with revisit triggers — [ADR-0004](adr/0004-defer-service-mesh.md); in-pod TLS + default-deny netpol bound the risk |

## 5. Delivery discipline — "Two appliers, no promotion, no rollback"

| Finding | Status | Where |
|---|---|---|
| Push + pull both applying | ✅ | ArgoCD is the sole applier; CI only sets image + syncs ([ADR-0001](adr/0001-argocd-sole-applier.md)) |
| No concurrency guard | ✅ | See §4 |
| Six near-duplicated workflows | 🟡 | Shared stages consolidated into [actions/reusable-security-scans.yml](../actions/reusable-security-scans.yml) (`workflow_call`); cloud workflows to migrate to it incrementally |
| DAST main/master only | ✅ | `dast-pr` job: ZAP baseline against a locally-run candidate container + Postgres sidecar, FAILs block merge |
| Environment promotion / progressive delivery | 🟡 | staging→production via environment approval gates today; Argo Rollouts canary with SLO-based auto-rollback is the next step (SLOs + PrometheusRules that would drive it now exist) |

## 6. Observability & SRE — "Operators installed, practice missing"

| Finding | Status | Where |
|---|---|---|
| No SLOs/SLIs | ✅ | [docs/slo.md](slo.md) — availability 99.5%, latency p95<500ms, error-budget policy |
| No alert rules committed | ✅ | [prometheus-rules.yaml](../kubernetes/observability/prometheus-rules.yaml) — multi-window burn-rate, latency, outage, auth-abuse + AlertmanagerConfig (Slack) |
| No dashboards committed | ✅ | [grafana-dashboard.yaml](../kubernetes/observability/grafana-dashboard.yaml) — golden signals + SLO overlays, operator-reconciled |
| No distributed tracing | ✅ | OpenTelemetry (OTLP) in both apps via `telemetry.py`, env-gated |
| App logs unstructured | ✅ | JSON logging via `LOG_FORMAT=json` (`telemetry.py`) |
| No app metrics | ✅ | Prometheus `/metrics` (instrumentator) + [servicemonitor.yaml](../kubernetes/observability/servicemonitor.yaml) |
| No synthetic monitoring | ✅ | [actions/synthetic-monitor.yml](../actions/synthetic-monitor.yml) — external probe every 10 min, Slack alerting; `/healthz` endpoints added |
| Async pattern unrealised (RabbitMQ) | 🟡 | Operator retained; producer/consumer remains future work — notifications are currently synchronous by design |
| Cost visibility | 🟡 | Renovate dashboards cover dependency currency; Infracost PR comments remain future work |

## 7. Governance & compliance — "The lowest-scoring domain"

| Finding | Status | Where |
|---|---|---|
| SECURITY.md | ✅ | [/SECURITY.md](../SECURITY.md) |
| CODEOWNERS | ✅ | [.github/CODEOWNERS](../.github/CODEOWNERS) |
| CONTRIBUTING.md | ✅ | [/CONTRIBUTING.md](../CONTRIBUTING.md) |
| PR / issue templates | ✅ | [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md), [.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/) |
| ADRs | ✅ | [docs/adr/](adr/) — five records + template |
| Branching strategy | ✅ | [governance/branching-strategy.md](governance/branching-strategy.md) |
| Renovate/Dependabot | ✅ | [/renovate.json](../renovate.json) |
| Releases + changelog | ✅ | [/CHANGELOG.md](../CHANGELOG.md) |
| Incident response runbook | ✅ | [governance/incident-response.md](governance/incident-response.md) |
| DR plan / RTO / RPO / drills | ✅ | [governance/disaster-recovery.md](governance/disaster-recovery.md) |
| Data classification / PII handling | ✅ | [governance/data-classification.md](governance/data-classification.md) |
| Audit-log retention (user_info) | ✅ | [governance/audit-log-retention.md](governance/audit-log-retention.md) |
| Control-framework mapping (SOC 2 / ISO) | 🟡 | Control evidence now exists (policies, retention, IR/DR); formal mapping is organization-level future work |
| Third-party risk register | 🟡 | Renovate vulnerability alerts + SBOM per image provide the live register; a curated doc is future work |

## 8. Modernization — "AI-native practices"

| Finding | Status | Where |
|---|---|---|
| Agentic AI absent | ✅ | LangGraph + Claude restore-workflow orchestrator (in-app) + nightly SARIF triage agent ([ai/triage/](../ai/triage/)) |
| No MCP integration | ✅ | [ai/mcp/devsecops_mcp_server.py](../ai/mcp/devsecops_mcp_server.py) + [.mcp.json](../.mcp.json) — SARIF/pipeline/cluster/doc bridge for Claude Code/Desktop |
| No AI code review | ✅ | [actions/ai-code-review.yml](../actions/ai-code-review.yml) — Claude reviews every PR (advisory; CODEOWNERS still required) |
| No AI runbooks | ✅ | [ai/runbooks/generate_runbook.py](../ai/runbooks/generate_runbook.py) — postmortem + runbook drafting, wired into the IR process |
| No Renovate/Dependabot | ✅ | [/renovate.json](../renovate.json) — grouped updates, pinned action digests, prioritized vulnerability PRs |
| No pre-commit hooks | ✅ | [/.pre-commit-config.yaml](../.pre-commit-config.yaml) — GitLeaks, Bandit, private-key detection at the keyboard |

## Deployment note

Workflow sources live in [actions/](../actions/) and are copied to
`.github/workflows/` in the deployed repository. The Kyverno signature policy
contains a `CHANGEME-github-org` placeholder that must be set to the real
repository slug, and `verify-image-signatures.yaml` assumes the CI OIDC
identity — both are called out inline.
