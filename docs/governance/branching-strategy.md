# Branching Strategy

Trunk-based, GitOps-delivered.

## Branches

- **`main`** — the trunk and the single source of production truth. Always
  releasable; ArgoCD reconciles production from it (ADR-0001).
- **`feature/<slug>`**, **`fix/<slug>`**, **`sec/<slug>`** — short-lived
  (days, not weeks), branched from `main`, merged back via PR. `sec/` marks
  security work for reviewer prioritization.
- No long-lived `develop`/release branches: environments differ by
  *promotion* (ArgoCD app targets + workflow environment gates), not by
  branch.

## Protection rules for `main`

Configure in repository settings:

1. PRs only — no direct pushes, no force pushes.
2. Required status checks: every job of the DevSecOps workflow for the
   touched paths (secret-scan, SAST, SCA, container-scan, IaC-scan,
   dast-pr) — these are the "branch-protection required checks for each
   gate" from the enforcement plan.
3. Required review from CODEOWNERS (≥1).
4. Conversation resolution required; linear history (squash merge).

## Releases

Squash-merges to `main` deploy to staging automatically; production is the
`workflow_dispatch` path with the `production` environment approval gate.
Tag releases `vMAJOR.MINOR.PATCH` and record them in CHANGELOG.md.
