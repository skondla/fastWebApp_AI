# Cluster admission policies (Kyverno)

Policy-as-code admission control for the FastAPI clusters. Individual pod
hardening already exists in the deployment manifests; these policies make the
**cluster enforce it** so a future manifest edit (or a manual `kubectl run`)
cannot silently regress the posture.

| Policy | File | Enforces |
|---|---|---|
| Verify image signatures | [verify-image-signatures.yaml](verify-image-signatures.yaml) | Only Cosign-signed images (keyless, signed by this repo's GitHub Actions OIDC identity) with an attested SBOM + SLSA provenance are admitted |
| Pod Security restricted | [require-pod-security.yaml](require-pod-security.yaml) | runAsNonRoot, seccomp RuntimeDefault, all capabilities dropped, no privilege escalation, read-only root FS |
| Default-deny NetworkPolicy | [require-networkpolicy.yaml](require-networkpolicy.yaml) | Auto-generates a default-deny NetworkPolicy in every new namespace |
| Disallow mutable tags | [disallow-latest-tag.yaml](disallow-latest-tag.yaml) | Images must be pinned (digest or immutable tag), never `:latest` |

## Install

```bash
./kyverno-install.sh          # installs Kyverno via Helm
kubectl apply -f .            # applies every policy in this directory
```

All policies run with `validationFailureAction: Enforce`. To roll out safely
on an existing cluster, first apply with `Audit`, review the PolicyReports
(`kubectl get polr -A`), then flip to `Enforce` — the warn-then-block pattern.

## Verifying

```bash
# Should be rejected — unsigned public image with a mutable tag:
kubectl run test --image=nginx:latest -n fastapi-namespace
```
