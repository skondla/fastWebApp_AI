#!/bin/bash

source ~/.bash_profile
export GKE_PROJECT=${GCP_PROJECT_ID} #env variable from  ~/.secrets
export GKE_CLUSTER="flaskapp1-demo-cluster"
export GKE_APP_ADMIN_NAME="flaskapp1-admin-ui"
export GKE_SERVICE="flaskapp1-service"
export GKE_SERVICE_ACCOUNT="flaskapp1-serviceaccount"
export GKE_DEPLOYMENT_NAME="flaskapp1-deployment"
export MANIFESTS_DIR="deploy/manifests/flaskapp1"
export APP_ADMIN_DIR="../../../dockerized/ADMIN"
export GKE_NAMESPACE="flaskapp1-namespace"
export GKE_APP_PORT=30443

gcloud config set project $GKE_PROJECT

# Delete the cluster
gcloud container clusters delete $GKE_CLUSTER --region $GKE_ZONE

# Delete service account
gcloud iam service-accounts delete "$GKE_SERVICE_ACCOUNT@$GKE_PROJECT.iam.gserviceaccount.com"

# Delete repository
gcloud artifacts repositories delete $GKE_PROJECT --location $GKE_REGION