# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org/).

## [Unreleased]

### Added
- **Supply chain:** SLSA provenance attestation in every pipeline (alongside
  the existing Cosign keyless signing + SPDX SBOM attestations); Kyverno
  admission verification of signature + SBOM + provenance.
- **Runtime policy:** Kyverno cluster policies — PSS `restricted`
  enforcement, generated default-deny NetworkPolicy per namespace, `:latest`
  tag ban (`kubernetes/policies/`).
- **App security:** RS256 JWT signing (env-provided keypair, HS256 dev
  fallback), `jti` claims, refresh-token rotation with reuse detection,
  server-side revocation denylist, Redis-backed global rate limiting,
  hardened cookies, CORS allowlist, `/healthz` probe.
- **Observability:** Prometheus `/metrics` in both apps, optional
  OpenTelemetry tracing, JSON logs; committed PrometheusRule SLO alerts,
  AlertmanagerConfig, Grafana dashboard, ServiceMonitor; SLO definitions
  (`docs/slo.md`); external synthetic monitor workflow.
- **Pipeline:** concurrency guards on all workflows, DAST on pull requests
  (ZAP vs a locally-run candidate container), reusable security-scan
  workflow (`actions/reusable-security-scans.yml`).
- **AI-native DevSecOps** (`ai/`): SARIF triage agent (Claude), incident
  runbook/postmortem generator, MCP server exposing DevSecOps operations,
  AI code review on PRs (Claude Code action).
- **Governance:** SECURITY.md, CODEOWNERS, CONTRIBUTING.md, PR/issue
  templates, ADRs, incident-response runbook, DR plan with RTO/RPO, data
  classification, audit-log retention policy, branching strategy, Renovate
  config, pre-commit hooks.

## [2.0.0] — FastAPI migration
- Flask → FastAPI conversion of USER and ADMIN apps with JWT OAuth 2.0,
  OWASP middleware chain, 9-stage DevSecOps pipelines across EKS/GKE/AKS,
  ArgoCD GitOps delivery, LangGraph agent orchestrator for the DB restore
  workflow.
