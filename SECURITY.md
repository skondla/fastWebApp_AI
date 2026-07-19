# Security Policy

## Supported versions

The `main` branch is the only supported line. Container images are built,
signed and attested per commit; deploy only images whose Cosign signature,
SBOM and SLSA provenance verify (enforced at admission by
[kubernetes/policies/verify-image-signatures.yaml](kubernetes/policies/verify-image-signatures.yaml)).

## Reporting a vulnerability

**Do not open a public issue for security problems.**

1. Preferred: open a **private security advisory** on GitHub
   (*Security → Advisories → Report a vulnerability*).
2. Alternatively email **skondla@me.com** with subject `SECURITY:` and
   include reproduction steps, impact, and affected component
   (app / pipeline / IaC / Kubernetes).

You will receive an acknowledgement within **2 business days** and a triage
decision (accepted severity + remediation target) within **7 days**. Please
allow up to **90 days** of coordinated disclosure before publishing.

## Scope

In scope: everything in this repository — the FastAPI apps, GitHub Actions
workflows, Terraform, Kubernetes manifests and policies, and the AI/MCP
tooling under `ai/`. Out of scope: the third-party services these integrate
with (AWS, GCP, Azure, Slack, Anthropic API), and volumetric DoS.

## Handling

Accepted reports are tracked in a private advisory, fixed on a private fork
branch when severity warrants, and released with a CHANGELOG entry crediting
the reporter (unless anonymity is requested). Incident response for exploited
vulnerabilities follows
[docs/governance/incident-response.md](docs/governance/incident-response.md).

## Hardening baseline

- JWT: RS256 keypair, 30-min access tokens with `jti`, refresh rotation with
  reuse detection, server-side denylist (`dockerized/*/security.py`).
- Secrets: cloud secret manager via Secrets Store CSI; no static cloud keys
  in CI (OIDC federation only).
- Pipeline: every scanner (TruffleHog, GitLeaks, Bandit, Semgrep, pip-audit,
  Trivy, Checkov, ZAP) is **blocking**; images are signed (Cosign keyless)
  with SPDX SBOM + SLSA provenance attestations.
- Cluster: PSS `restricted`, default-deny NetworkPolicy, Kyverno admission
  verification of signatures/SBOM/provenance.
