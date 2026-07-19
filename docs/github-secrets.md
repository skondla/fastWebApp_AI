# GitHub Actions — Required Secrets & Variables

Configure these in **Settings → Secrets and variables → Actions** of your GitHub repository.

---

## Secrets common to all three pipelines

| Secret | Description | Example |
|--------|-------------|---------|
| `JWT_SECRET_KEY` | JWT signing key — must be long, random, unique per environment | `openssl rand -hex 32` |
| `SLACK_WEBHOOK_URL` | Slack incoming-webhook URL for deploy notifications | `https://hooks.slack.com/services/T.../B.../...` |
| `DB_PASSWORD` | PostgreSQL password injected into the K8s Secret manifest | — |
| `ANTHROPIC_API_KEY` | Claude API key powering the USER app's `/agent/restore-workflow` orchestrator | `sk-ant-...` |
| `ARGOCD_SERVER` | Hostname:port of the ArgoCD API server CI talks to (no direct `kubectl apply` anymore — see [ArgoCD GitOps setup](#argocd-gitops-setup--sole-applier)) | `argocd.example.com:443` |
| `ARGOCD_AUTH_TOKEN` | ArgoCD account auth token used by CI to set the image and trigger a sync | `argocd account generate-token --account ci` |

> `ANTHROPIC_API_KEY` is a **runtime** secret for the USER_FASTAPI app (see
> `dockerized/USER_FASTAPI/startup.sh`), not currently wired into the K8s
> Secret manifests or deploy workflows. For a cluster deployment, add it to
> `secret.yaml` / `deployment.yaml` (and the corresponding `envsubst`
> variables in the deploy workflow) the same way `JWT_SECRET_KEY` is handled.
> For local/dev runs, just `export ANTHROPIC_API_KEY=...` before `startup.sh`.

---

## AWS EKS — `devsecops-fastapi-eks.yml`

### Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | IAM Role ARN for GitHub OIDC authentication (no long-lived keys) |
| `AWS_SECRETS_MANAGER_SECRET_ARN` | ARN of the Secrets Manager secret the Secrets Store CSI Driver syncs into `fastapi-db-secret` / `fastapi-admin-db-secret` (see [Secrets Store CSI Driver](#secrets-store-csi-driver-replacing-the-plaintext-k8s-secret)) |

### Setup: AWS OIDC trust

```bash
# 1. Create OIDC provider for GitHub in IAM (one-time per account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# 2. Create IAM Role with this trust policy (replace ORG/REPO):
# {
#   "Effect": "Allow",
#   "Principal": {"Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"},
#   "Action": "sts:AssumeRoleWithWebIdentity",
#   "Condition": {
#     "StringLike": {"token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:*"},
#     "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"}
#   }
# }
# Attach policies: AmazonEKSClusterPolicy, AmazonEC2ContainerRegistryPowerUser

# 3. Set secret
gh secret set AWS_ROLE_ARN --body "arn:aws:iam::<ACCOUNT_ID>:role/<ROLE_NAME>"
```

### Workflow variables (edit directly in the yml)

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region |
| `EKS_CLUSTER` | `fastapi-demo-cluster` | EKS cluster name |
| `ECR_REPOSITORY` | `fastapi-user-app` | ECR repository name |
| `EKS_NAMESPACE` | `fastapi-namespace` | Kubernetes namespace |

---

## Azure AKS — `devsecops-fastapi-aks.yml`

### Secrets

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | App Registration client ID (for OIDC Workload Identity) |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_KEYVAULT_NAME` | Key Vault the Secrets Store CSI Driver reads from (see [Secrets Store CSI Driver](#secrets-store-csi-driver-replacing-the-plaintext-k8s-secret)) |
| `AZURE_KEYVAULT_CLIENT_ID` | Workload-identity client ID granted `get` access on that Key Vault |

### Setup: Azure OIDC Workload Identity

```bash
# 1. Create App Registration
az ad app create --display-name "github-actions-fastapi"

# 2. Create Service Principal
az ad sp create --id <APP_ID>

# 3. Add Federated Credential (replace ORG/REPO/BRANCH)
az ad app federated-credential create \
  --id <APP_ID> \
  --parameters '{
    "name": "github-actions",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<ORG>/<REPO>:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# 4. Assign roles
az role assignment create \
  --assignee <APP_ID> \
  --role "Contributor" \
  --scope /subscriptions/<SUBSCRIPTION_ID>

# 5. Set secrets
gh secret set AZURE_CLIENT_ID       --body "<APP_ID>"
gh secret set AZURE_TENANT_ID       --body "<TENANT_ID>"
gh secret set AZURE_SUBSCRIPTION_ID --body "<SUBSCRIPTION_ID>"
```

### Workflow variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_RESOURCE_GROUP` | `fastapi-rg` | Resource group name |
| `AKS_CLUSTER` | `fastapi-aks-cluster` | AKS cluster name |
| `ACR_NAME` | `fastapiregistry` | Azure Container Registry name (globally unique) |
| `AKS_NAMESPACE` | `fastapi-namespace` | Kubernetes namespace |

---

## GCP GKE — `devsecops-fastapi-gke.yml`

### Secrets

| Secret | Description |
|--------|-------------|
| `GKE_PROJECT` | GCP project ID |
| `GKE_SA` | GCP Service Account email used as Workload Identity annotation |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity Provider resource name |
| `GCP_SERVICE_ACCOUNT` | GCP Service Account email for GitHub Actions OIDC |
| `GCP_PROJECT_NUMBER` | GCP project **number** (not the project ID) — required by Secret Manager resource names in the Secrets Store CSI Driver config |

### Setup: GCP Workload Identity Federation

```bash
# 1. Enable APIs
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com

# 2. Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="${GCP_PROJECT}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 3. Create OIDC Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${GCP_PROJECT}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 4. Create Service Account
gcloud iam service-accounts create "github-actions-sa" \
  --project="${GCP_PROJECT}" \
  --display-name="GitHub Actions Service Account"

# 5. Bind roles
gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
  --member="serviceAccount:github-actions-sa@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --role="roles/container.developer"
gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
  --member="serviceAccount:github-actions-sa@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# 6. Allow GitHub to impersonate the SA (replace ORG/REPO)
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions-sa@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/attribute.repository/<ORG>/<REPO>"

# 7. Set secrets
PROVIDER="projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
gh secret set GKE_PROJECT                    --body "${GCP_PROJECT}"
gh secret set GKE_SA                         --body "github-actions-sa@${GCP_PROJECT}.iam.gserviceaccount.com"
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body "${PROVIDER}"
gh secret set GCP_SERVICE_ACCOUNT           --body "github-actions-sa@${GCP_PROJECT}.iam.gserviceaccount.com"
```

### Workflow variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GKE_CLUSTER` | `fastapi-demo-cluster` | GKE cluster name |
| `GKE_REGION` | `us-east4` | GCP region |
| `GKE_ZONE` | `us-east4-a` | GCP zone for zonal cluster |
| `GKE_NAMESPACE` | `fastapi-namespace` | Kubernetes namespace |

---

## Setting all secrets at once

```bash
# Prerequisites: GitHub CLI (gh) authenticated, terraform outputs available

# Common
gh secret set JWT_SECRET_KEY    --body "$(openssl rand -hex 32)"
gh secret set SLACK_WEBHOOK_URL --body "<your-slack-webhook>"
gh secret set DB_PASSWORD       --body "<your-db-password>"
gh secret set ANTHROPIC_API_KEY --body "<claude-api-key>"
gh secret set ARGOCD_SERVER     --body "<argocd-host>:443"
gh secret set ARGOCD_AUTH_TOKEN --body "$(argocd account generate-token --account ci)"

# AWS
gh secret set AWS_ROLE_ARN                     --body "arn:aws:iam::<ACCOUNT>:role/<ROLE>"
gh secret set AWS_SECRETS_MANAGER_SECRET_ARN   --body "arn:aws:secretsmanager:<region>:<account>:secret:<name>"

# Azure
gh secret set AZURE_CLIENT_ID          --body "<client-id>"
gh secret set AZURE_TENANT_ID          --body "<tenant-id>"
gh secret set AZURE_SUBSCRIPTION_ID    --body "<subscription-id>"
gh secret set AZURE_KEYVAULT_NAME      --body "<keyvault-name>"
gh secret set AZURE_KEYVAULT_CLIENT_ID --body "<workload-identity-client-id>"

# GCP
gh secret set GKE_PROJECT                    --body "<project-id>"
gh secret set GKE_SA                         --body "<sa@project.iam.gserviceaccount.com>"
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body "projects/<num>/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
gh secret set GCP_SERVICE_ACCOUNT           --body "<sa@project.iam.gserviceaccount.com>"
gh secret set GCP_PROJECT_NUMBER            --body "<project-number>"
```

---

## K8s Secret manifest — deprecated, superseded by the CSI driver

Each `secret.yaml` (plaintext `stringData`, `envsubst`-templated) is now marked
`# DEPRECATED` and is **no longer applied by CI** — see
[Secrets Store CSI Driver](#secrets-store-csi-driver-replacing-the-plaintext-k8s-secret)
below. It's kept in the repo only for manual/local use on a cluster that doesn't
have the CSI driver installed yet.

---

## Secrets Store CSI Driver — replacing the plaintext K8s Secret

Every `fastapi1/` and `fastapi-admin/` manifest directory now includes a
`secretproviderclass.yaml` that syncs DB credentials + the JWT signing key from
a real secret store (AWS Secrets Manager / Azure Key Vault / GCP Secret
Manager) into the same `fastapi-db-secret` / `fastapi-admin-db-secret` K8s
Secret the app already reads via `envFrom`. This closes the "secrets in a
plaintext K8s Secret" gap without changing anything in the application code.

**Prerequisites** (cluster-side, not something a repo edit can provision):

1. Install the [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/) and the cloud-specific provider on each cluster:
   - AWS: [`secrets-store-csi-driver-provider-aws`](https://github.com/aws/secrets-store-csi-driver-provider-aws)
   - Azure: [`azure-keyvault-secrets-provider`](https://learn.microsoft.com/azure/aks/csi-secrets-store-driver) AKS add-on
   - GCP: [`secrets-store-csi-driver-provider-gcp`](https://github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp)
2. Grant each workload's ServiceAccount (already annotated for workload identity — `fastapi-sa` / `fastapi-admin-serviceaccount` / IRSA / Workload Identity) read access to the secret(s):
   - AWS: an IAM policy on the role in `eks.amazonaws.com/role-arn` allowing `secretsmanager:GetSecretValue` on `AWS_SECRETS_MANAGER_SECRET_ARN`.
   - Azure: an access policy or RBAC role on the Key Vault for `AZURE_KEYVAULT_CLIENT_ID`.
   - GCP: `roles/secretmanager.secretAccessor` on the GSA in `iam.gke.io/gcp-service-account` for each `projects/<num>/secrets/*`.
3. Populate the secret store itself with `shost`/`sport`/`suser`/`spassword`/`sdatabase`/`SECRET_KEY` values (AWS: one JSON secret at `AWS_SECRETS_MANAGER_SECRET_ARN`; Azure/GCP: one secret object per key, named per the `objectName`/`fileName` entries in each `secretproviderclass.yaml`).

Once the driver is installed and the store is populated, the CSI volume mount
on the main container (`/mnt/secrets-store`) triggers the sync — no app code
or further CI change needed.

---

## ArgoCD GitOps setup — sole applier

CI no longer runs `kubectl apply` against any cluster. Each `deploy` job now
only calls the ArgoCD API to point an `Application` at the new image and
trigger a sync — **ArgoCD itself** (running in-cluster, already authenticated
via its own service account) does the actual reconciliation. This also means
CI's OIDC credentials for AKS/EKS/GKE are no longer usable for direct cluster
writes — only for the (unchanged, read-only) `dast` job's service-IP lookup
and image push/scan steps.

Setup, once per cluster:

```bash
# 1. Install ArgoCD (the directory was previously mislabeled and installed
#    Argo Workflows instead — argocd.sh now installs the real thing)
./argocd/helm/argocd.sh

# 2. Register each app x cloud deployment as an ArgoCD Application
kubectl apply -f argocd/apps/

# 3. Create a scoped CI account + token (don't reuse the admin login)
argocd account update-password --account ci   # or configure via argocd-cm/RBAC
argocd account generate-token --account ci
# -> set as the ARGOCD_AUTH_TOKEN secret; the server address as ARGOCD_SERVER
```

Each `Application` (`argocd/apps/*.yaml`) has `syncPolicy.automated` set, so
ArgoCD also self-heals drift and prunes removed resources on every poll —
independent of whether CI ever runs.

### One-time `CHANGEME` placeholders

Converting the manifests to Kustomize bases (required so ArgoCD can render
them without a `envsubst` step) meant values that used to flow in from
GitHub Actions `env:` at apply-time now had to become literal, committed
values. Anything that isn't a stable, non-secret constant (like `APP_NAME` or
the namespace) is left as a clearly-marked `CHANGEME-*` placeholder — search
for it before your first sync:

```bash
grep -rl CHANGEME azure/ aws/ gcp/
```

These cover: Azure Key Vault name/client-ID and tenant ID, the AWS Secrets
Manager ARN, the GCP project number and GSA email, the EKS/AKS IRSA/workload-identity
role ARNs, and the Slack webhook URL baked into each `configmap.yaml`. Fill
them in directly (they're resource identifiers, not secret values — the
actual credentials stay in the secret store) before applying `argocd/apps/`.
The container image itself is the one thing that *doesn't* need filling in —
CI overrides it per-deploy via `argocd app set --kustomize-image`.

---

## GitHub Environments (recommended)

Create **`staging`** and **`production`** environments in **Settings → Environments**:

- **staging**: Auto-deploy on every merge to `main`
- **production**: Require manual approval + 1 reviewer before deploy
- Set environment-specific secrets (different DB passwords, JWT keys per environment)
