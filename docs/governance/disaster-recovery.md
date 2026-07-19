# Disaster Recovery Plan

## Objectives

| Component | RTO (restore service) | RPO (max data loss) |
|---|---|---|
| FastAPI apps (stateless) | **30 minutes** | n/a |
| PostgreSQL / Aurora | **2 hours** | **15 minutes** (PITR) |
| Cluster + platform (Kyverno, operators, ArgoCD) | **4 hours** | n/a (declarative) |
| Registry images | **1 hour** | 0 (multi-region replication) |

## Why these are achievable

- **Apps are stateless and declarative.** Everything a cluster needs is in
  git (Terraform → cluster; ArgoCD Applications → workloads; this repo →
  policies/observability). Recovery is re-provision + re-point ArgoCD.
- **Database:** Aurora/RDS automated backups with point-in-time recovery;
  snapshots retained 35 days. The app's own restore workflow
  (`/restore`, agent-orchestrated) is exercised routinely, which doubles as
  a continuous restore test of snapshots.
- **Images:** every deployed digest is signed and attested; registries are
  replicated cross-region. Provenance lets us prove a rebuilt image matches.

## Recovery procedures

### Scenario A — cluster loss (region intact)
1. `terraform apply` the cluster stack (`aws/eks/deploy/terraform/`).
2. Install platform: ArgoCD (`argocd/helm/argocd.sh`), Kyverno
   (`kubernetes/policies/kyverno-install.sh`), operators
   (`kubernetes/operators/*`).
3. Re-register ArgoCD apps (`argocd/apps/*.yaml`) and sync — workloads,
   policies and observability reconcile from git.
4. Verify: synthetic monitor green, Kyverno policies `Ready`, SLIs in SLO.

### Scenario B — database loss/corruption
1. Identify last-good time; PITR-restore to a new instance/cluster.
2. Point the app at the restored endpoint via the secret manager entry
   (CSI picks it up on pod restart) — or use the app's guided restore
   workflow for snapshot-based recovery.
3. Validate row counts / latest `user_info` audit entries against RPO.

### Scenario C — region loss
Re-run Scenario A in the DR region (Terraform variables select region),
restore the DB from cross-region snapshot copy, update DNS. Target: RTO 8h.

## Drills

- **Quarterly:** Scenario B tabletop + actual PITR restore into an isolated
  VPC, timed against RTO/RPO.
- **Semi-annual:** Scenario A full rebuild in a sandbox account.
- Drill results are recorded in `docs/postmortems/` with gaps filed as issues.
