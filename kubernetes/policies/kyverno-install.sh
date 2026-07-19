#!/usr/bin/env bash
# Author: skondla@me.com
# Purpose: Install Kyverno (policy-as-code admission controller) via Helm,
#          then apply the cluster policies in this directory.
set -euo pipefail

helm repo add kyverno https://kyverno.github.io/kyverno/ >/dev/null
helm repo update >/dev/null

helm upgrade --install kyverno kyverno/kyverno \
  --namespace kyverno --create-namespace \
  --set replicaCount=3 \
  --wait

echo "Kyverno installed. Applying cluster policies..."
kubectl apply -f "$(dirname "$0")"

echo "Policies applied:"
kubectl get clusterpolicy
