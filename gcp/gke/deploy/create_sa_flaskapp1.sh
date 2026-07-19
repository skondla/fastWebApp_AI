#!/bin/bash
#Author: skondla@me.com
#Purpose: Create a new instance of GKE cluster and deploy a container web application

# Create a project and set GKE_PROJECT to the project id:
# See https://console.cloud.google.com/projectselector2/home/dashboard

# Set parameters
source ~/.bash_profile
export GKE_PROJECT=${GCP_PROJECT_ID} #env variable from  ~/.secrets
export GKE_CLUSTER="webapp1-demo-cluster"
export GKE_APP_ADMIN_NAME="flaskapp1-admin-ui"
export GKE_SERVICE="flaskapp1-service"
export GKE_SERVICE_ACCOUNT="flaskapp1-serviceaccount"
export GKE_DEPLOYMENT_NAME="flaskapp1-deployment"
export MANIFESTS_DIR="deploy/manifests/flaskapp1"
export APP_ADMIN_DIR="../../../dockerized/ADMIN"
export GKE_NAMESPACE="webapp1-namespace"
export GKE_APP_PORT=30443

# Get a list of regions:
# $ gcloud compute regions list
#
# Get a list of zones:
# $ gcloud compute zones list
export GKE_REGION="us-east4"
export GKE_ZONE="us-east4-a"
export GKE_ADDITIONAL_ZONE="us-east4-b"


# Just a placeholder for the first deployment
export GITHUB_SHA="flaskapp1-demo-shop"

#Login to gcloud
gcloud auth login

gcloud config set project $GKE_PROJECT
gcloud config set compute/zone $GKE_ZONE
#gcloud config set compute/zone $GKE_ADDITIONAL_ZONE
gcloud config set compute/region $GKE_REGION

# enable API
gcloud services enable \
 compute.googleapis.com \
 containerregistry.googleapis.com \
 container.googleapis.com \
 artifactregistry.googleapis.com


# Create a GKE cluster
#GKE cluster has alreay been created - just create a new node pool

#gcloud container clusters create $GKE_CLUSTER --num-nodes=1

# Configure kubctl
gcloud container clusters get-credentials $GKE_CLUSTER

# Create repository
# Use existing repository

# Create a service account
gcloud iam service-accounts create $GKE_SERVICE_ACCOUNT \
  --display-name "GitHub Deployment" \
  --description "Used to deploy from GitHub Actions to GKE"

# Get mail of service account
gcloud iam service-accounts list

export GKE_SVC_MAIL="$GKE_SERVICE_ACCOUNT@$GKE_PROJECT.iam.gserviceaccount.com"

# Add 'container.clusterAdmin' role:
gcloud projects add-iam-policy-binding $GKE_PROJECT \
  --member=serviceAccount:$GKE_SVC_MAIL \
  --role=roles/container.clusterAdmin 


# Add 'artifactregistry.admin' role:
gcloud projects add-iam-policy-binding $GKE_PROJECT \
  --member=serviceAccount:$GKE_SVC_MAIL \
  --role=roles/artifactregistry.admin

# Download JSON
#gcloud iam service-accounts keys create ~/.private/flaskapp_key.json --iam-account=$GKE_SVC_MAIL

# Build and push the docker image
docker build --tag \
  "$GKE_REGION-docker.pkg.dev/$GKE_PROJECT/$GKE_PROJECT/$GKE_APP_ADMIN_NAME:$GITHUB_SHA" \
  ${APP_ADMIN_DIR}/
gcloud auth configure-docker $GKE_REGION-docker.pkg.dev --quiet
docker push "$GKE_REGION-docker.pkg.dev/$GKE_PROJECT/$GKE_PROJECT/$GKE_APP_ADMIN_NAME:$GITHUB_SHA"

# Build and push the docker image via git actions

#Check envsubst is configured correctly (this example is on MacOS only) - Already done in the workflow

##########
#To be tested why this is needed: give the Google Service Acccount cluster-admin clusterrole binding
export check=`kubectl get clusterrolebinding | grep $GKE_SERVICE_ACCOUNT | awk '{print $1}' | wc -l`
if [ ${check} -le 1 ]; then
  kubectl create clusterrolebinding $GKE_SERVICE_ACCOUNT \
   --clusterrole cluster-admin \
   --user $GKE_SVC_MAIL
else
  echo "clusterrolebinding $GKE_SERVICE_ACCOUNT already exists"
  echo "${check}"
fi
##########
# Create deployment via git actions
# Create service via git actions


kubectl get service
echo ""
echo "Note: if the EXTERNAL-IP is still pending you have to wait and run 'kubectl get service' again to find out the external ip to test the application!"
echo ""

echo ""
echo "Please create a secret named 'GKE_SA_KEY' in GitHub with the followign content:"
echo ""
cat ~/.private/flaskapp_key.json | base64
echo ""
