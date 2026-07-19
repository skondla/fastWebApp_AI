# ADR-0002: JWT — RS256 signing, refresh rotation, server-side revocation

- **Status:** Accepted
- **Date:** 2026-07-18

## Context

The original implementation signed all JWTs with HS256 and a static
`SECRET_KEY` shared by every service; refresh tokens lived 7 days without
rotation; logout only cleared cookies, so a stolen token stayed valid until
expiry.

## Decision

1. **RS256 by default.** The signing keypair is provided via
   `JWT_PRIVATE_KEY(_FILE)` / `JWT_PUBLIC_KEY(_FILE)` — in Kubernetes, from
   the cloud secret manager through the Secrets Store CSI mount. Verifiers
   only ever hold the public key. HS256 remains solely as a local-dev
   fallback and logs a warning.
2. **Rotation-on-use with families.** Every refresh token carries `jti` +
   family id (`fid`). Each `/auth/refresh` invalidates the presented token
   and issues a new one in the same family; presenting a rotated-out token
   is treated as theft and revokes the entire family.
3. **Server-side revocation.** Logout (and family revocation) denylists the
   `jti` until natural expiry. `decode_token` checks the denylist on every
   request.
4. **Shared state in Redis** (`REDIS_URL`) so revocation and the rate limits
   are global across replicas, with an in-process fallback for dev.

## Consequences

- Key compromise scope shrinks: services holding only the public key cannot
  mint tokens; key rotation is a secret update + rolling restart.
- A Redis dependency appears in production; its unavailability degrades to
  per-pod enforcement (fail-open on scope, never fail-closed on requests).
- One extra store lookup per authenticated request (sub-millisecond).
