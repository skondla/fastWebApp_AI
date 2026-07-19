# Audit Log Retention Policy

Covers the security-relevant logs this system produces and how long each is
kept, satisfying the "no audit-log retention policy (user_info)" finding.

| Log | Source | Contains | Retention | Store |
|---|---|---|---|---|
| Application security audit | `SecurityAuditMiddleware` (auth paths, 4xx/5xx, IP, UA, duration) | PII-adjacent (IP/UA) | **400 days** | Cluster log pipeline → CloudWatch/Cloud Logging, locked retention |
| `user_info` DB audit rows | App database | User identifiers | **400 days**, then anonymized (IDs hashed) not deleted, preserving counts | PostgreSQL |
| Kubernetes API audit | Managed control plane | Actor, verb, object | **1 year** | Cloud provider audit sink |
| Cloud control plane (CloudTrail / GCP Audit / Azure Activity) | Provider | IAM actions | **1 year** minimum | Provider-native, org bucket |
| CI security artifacts (SARIF, SBOM, ZAP) | GitHub Actions | Findings | 30 days as artifacts; **indefinitely** as code-scanning alerts + Rekor transparency log entries | GitHub / Sigstore |
| Alert & incident records | Alertmanager, incident channels | Ops metadata | **2 years** | Slack export + `docs/postmortems/` |

## Principles

- **Tamper-evidence over volume:** signing/attestation events live in the
  public Rekor log; DB audit rows are append-only to the app role.
- **PII minimization:** logs never contain passwords, tokens, or emails;
  IPs age out with the 400-day window (aligned with common webauthn/fraud
  lookback guidance).
- **Deletion requests:** user-deletion requests anonymize audit rows rather
  than deleting them, retaining security value without identity.
- **Review:** retention configuration is checked during the monthly SLO +
  audit review; drift is filed as a security issue.
