# Incident Response Runbook

Applies to production incidents on any cloud (EKS/GKE/AKS): outage, SLO
fast-burn page, security event, or data incident.

## Severity levels

| Sev | Definition | Response target | Examples |
|---|---|---|---|
| SEV1 | Full outage or active security breach | Engage < 15 min, updates every 30 min | 0 available replicas; credential compromise; token-signing key leak |
| SEV2 | Degraded service / SLO fast burn | Engage < 1 h | Fast-burn alert firing; refresh-token reuse spike |
| SEV3 | Contained issue, budget-affecting | Next business day | Slow-burn alert; single-pod crash loop |

## Roles

- **Incident Commander (IC):** owns the timeline, comms, and decisions.
- **Operator:** hands on keyboard. No change without IC acknowledgement.
- **Scribe:** timestamps every action in the incident channel (the AI
  runbook generator consumes this log — keep it honest and granular).

## Response flow

1. **Acknowledge** the page; open a dedicated Slack channel `#inc-YYYYMMDD-slug`.
2. **Assess** with the Grafana golden-signals dashboard and
   `kubectl -n fastapi-namespace get pods,events --sort-by=.lastTimestamp`.
3. **Stabilize** — preferred order:
   - Roll back via GitOps: `argocd app rollback <app>` (never `kubectl edit`).
   - Scale: `kubectl -n fastapi-namespace scale deploy/<app> --replicas=N`
     only if HPA is the limiting factor, and record it for revert.
   - For auth compromise: rotate the JWT keypair secret, roll pods, and
     flush refresh families (`redis-cli KEYS 'jwt:family:*'` → delete).
4. **Communicate** status at the cadence for the severity.
5. **Close** when SLIs are inside SLO for 30 minutes.

## Security-incident addendum

- Preserve evidence before remediation: `kubectl logs --previous`, audit
  log export, CloudTrail/GCP audit query for the window.
- Revoke, don't just rotate: denylist active `jti`s, revoke refresh
  families, invalidate CI OIDC role trust if pipeline compromise is
  suspected.
- Check image provenance: `cosign verify` + `cosign verify-attestation` on
  the running digests; any unverifiable digest is treated as SEV1.

## Postmortem

Blameless, due within 5 business days for SEV1/SEV2. Generate the first
draft from the incident channel log:

```bash
python ai/runbooks/generate_runbook.py postmortem --input incident-log.txt
```

Review, correct, commit under `docs/postmortems/`, and file follow-up issues
for every action item. Error-budget consequences per [docs/slo.md](../slo.md).
