# ADR-0003: Kyverno for policy-as-code admission control

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

Pod hardening lived only in the deployment manifests: nothing prevented a
future manifest edit, a `kubectl run`, or a compromised pipeline from
admitting an unsigned or unhardened workload. The supply chain ended at the
registry — the cluster would run anything.

## Decision

Adopt **Kyverno** (over OPA/Gatekeeper) as the admission controller, with
four enforced cluster policies (`kubernetes/policies/`):

1. `verifyImages` — Cosign keyless signature **and** SPDX SBOM **and** SLSA
   provenance attestations must validate against this repo's GitHub Actions
   OIDC identity; tags are mutated to digests at admission.
2. PSS `restricted` semantics + read-only root FS on app namespaces.
3. Generated default-deny NetworkPolicy in every namespace.
4. `:latest` / untagged images rejected.

Kyverno was chosen because policies are plain Kubernetes YAML (no Rego),
`verifyImages` supports Sigstore natively, and `generate` rules cover the
default-deny NetworkPolicy requirement declaratively.

## Consequences

- The supply chain is closed end-to-end: build → sign/attest → verify at
  admission. A leaked registry credential alone can no longer deploy code.
- Rollouts of new policies must follow warn-then-block (Audit → Enforce) to
  avoid blocking existing workloads.
- Kyverno itself becomes cluster-critical; it runs with 3 replicas and
  `failurePolicy: Fail` on the signature policy (deliberate: no verification,
  no admission).
