# ADR-0001: ArgoCD is the sole applier of Kubernetes manifests

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

Earlier pipeline iterations both `kubectl apply`-ed manifests from CI **and**
ran ArgoCD reconciliation against the same directories — two writers on the
same objects, where the last write silently wins and cluster state can't be
traced to a single source of truth.

## Decision

ArgoCD is the only system that applies manifests. CI's deploy job does
exactly two things: point the ArgoCD Application at the newly built image
(`argocd app set --kustomize-image`) and trigger/await a sync. Direct
`kubectl apply` from CI or from operator laptops is prohibited for app
workloads; every workflow carries a `concurrency` group so deploy triggers
queue rather than race.

## Consequences

- Cluster state is always derivable from git + the ArgoCD Application spec;
  drift is surfaced and reverted by reconciliation.
- Rollback is `argocd app rollback` or a git revert — one mechanism.
- Break-glass manual changes must be made through git (or are reverted by
  the next sync); this is intentional friction.
- Progressive delivery (canary/blue-green via Argo Rollouts) can be layered
  on later without changing the delivery model.
