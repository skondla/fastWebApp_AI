#!/bin/bash
# Author: skondla@me.com
# Purpose: Install ArgoCD (GitOps continuous-delivery controller) — the sole
#          applier of cluster state for the fastAPIWebApp deployments.
#
# NOTE: the previous version of this script installed the Bitnami
# "argo-workflows" chart (a CI pipeline/workflow engine) despite living in a
# directory named argocd/ — that was a different, unrelated project from
# ArgoCD. This installs the real thing.

set -euo pipefail

NAMESPACE="${ARGOCD_NAMESPACE:-argocd}"

helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm upgrade --install argocd argo/argo-cd \
  --namespace "${NAMESPACE}" \
  --create-namespace

echo ""
echo "ArgoCD installed in namespace '${NAMESPACE}'."
echo "Fetch the initial admin password with:"
echo "  kubectl -n ${NAMESPACE} get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo ""
echo "Port-forward the UI/API with:"
echo "  kubectl -n ${NAMESPACE} port-forward svc/argocd-server 8080:443"
echo ""
echo "Next: apply the Application manifests in argocd/apps/ to register each"
echo "app x cloud deployment, and generate an auth token for CI:"
echo "  argocd account generate-token --account <service-account>"
