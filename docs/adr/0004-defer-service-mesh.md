# ADR-0004: Defer service mesh / mTLS

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

The gap analysis flagged cleartext pod-to-pod traffic and no service mesh.
A mesh (Istio/Linkerd) would add mTLS and fine-grained authZ — at the cost
of a sidecar or ambient dataplane, upgrade coupling, and significant
operational surface for a two-service system.

## Decision

**Defer the mesh.** The current risk is bounded by: default-deny
NetworkPolicy (only explicitly allowed flows exist), TLS termination at the
app itself (uvicorn serves HTTPS in-pod, so "pod-to-pod" app traffic is
already encrypted), single-tenant namespaces, and PSS `restricted`.

Revisit when any of these become true: more than ~5 internal services,
cross-namespace service-to-service calls, a compliance requirement naming
mTLS explicitly, or multi-tenant clusters. Impact/effort places the mesh in
the "reconsider" quadrant — necessary only if a specific requirement drives it.

## Consequences

- No sidecar overhead or mesh upgrade treadmill today.
- East-west authZ stays at L3/L4 (NetworkPolicy) + JWT at L7 rather than
  mesh-level identities; this is accepted and recorded.
