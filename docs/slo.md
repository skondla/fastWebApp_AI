# Service Level Objectives — FastAPI USER & ADMIN apps

Defined per the deck finding "No SLOs / SLIs defined". The alert rules in
[kubernetes/observability/prometheus-rules.yaml](../kubernetes/observability/prometheus-rules.yaml)
and the dashboard in
[kubernetes/observability/grafana-dashboard.yaml](../kubernetes/observability/grafana-dashboard.yaml)
are generated from this table — change the SLO here first, then the rules.

## SLIs and SLOs

| SLI | Measurement | SLO (28-day window) | Error budget |
|---|---|---|---|
| **Availability** | `1 − (5xx responses / all responses)` from app metrics | **99.5%** | 0.5% of requests ≈ 3h 21m full outage / 28d |
| **Latency** | p95 of `http_request_duration_seconds` | **95% of requests < 500 ms** | 5% of requests may exceed 500 ms |
| **Durability (restore workflow)** | Successful `/restore` operations / attempted | **99%** | tracked via audit log, reviewed monthly |

Black-box availability is additionally measured from outside the cluster by
the [synthetic monitor workflow](../actions/synthetic-monitor.yml) every 10
minutes — LB, DNS and certificate failures count against the availability SLO
even when in-cluster metrics look healthy.

## Alerting policy (multi-window, multi-burn-rate)

| Condition | Burn rate | Windows | Action |
|---|---|---|---|
| Fast burn | 14.4× budget | 5m AND 1h | **Page** (`severity: critical`) |
| Slow burn | 3× budget | 1h, for 15m | Ticket (`severity: warning`) |
| Latency breach | p95 > 500 ms | 10m | Ticket |
| Outage | 0 available replicas | 2m | **Page** |

## Error-budget policy

- Budget remaining > 50%: normal feature velocity.
- Budget remaining 10–50%: releases require an explicit sign-off from the
  on-call; prefer reliability work.
- Budget exhausted: feature freeze; only reliability fixes and security
  patches ship until the 28-day window recovers.

## Review cadence

SLO attainment is reviewed monthly alongside the audit-log review
(see [governance/audit-log-retention.md](governance/audit-log-retention.md)).
Postmortems for budget-exhausting incidents follow
[governance/incident-response.md](governance/incident-response.md) and may be
drafted with the [AI runbook generator](../ai/runbooks/generate_runbook.py).
