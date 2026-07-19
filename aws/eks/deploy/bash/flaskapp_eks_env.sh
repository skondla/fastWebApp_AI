#!/bin/bash


export ECR_REPOSITORY="flaskapp1-demo-shop"
export EKS_CLUSTER_NAME="webapps-demo"
export ADMIN_APP_DIR="../../../../dockerized/ADMIN/"
export USER_APP_DIR="../../../../dockerized/USER/"
export AWS_ACCOUNT_ID=`aws sts get-caller-identity --query Account --output text`
export AWS_REGION=`cat ~/.aws/config | grep region | awk '{print $3}'`
export AWS_ACCESS_KEY_ID=`cat ~/.aws/credentials|grep aws_access_key_id | awk '{print $3}'`
export AWS_SECRET_ACCESS_KEY=`cat ~/.aws/credentials|grep aws_secret_access_key | awk '{print $3}'`
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export IMAGE_TAG=$(openssl rand -hex 32)
export ECR_REPOSITORY_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"
export EKS_APP_NAME="flaskapp1-demo-shop"
export EKS_SERVICE="flaskapp1"
export EKS_SERVICE_ACCOUNT="flaskapp1-sa"
export EKS_NAMESPACE="flaskapp"
export IMAGE_NAME=`cat ~/Downloads/ecr_image.txt | grep imageName|awk '{print $2}'`
export APP_MANIFEST_DIR="../manifest/flaskapp1"
# export EKS_PRIVATE_SUBNET1="subnet-076afdef0f9911f16"
# export EKS_PRIVATE_SUBNET2="subnet-001ae6deda7adaf15"
# export EKS_PUBLIC_SUBNET1="subnet-065bbff8f2e547c0e"
# export EKS_PUBLIC_SUBNET2="subnet-078382a4e4f2333da"
export SUBNET_FILE=~/Downloads/subnets.list
export EKS_PUBLIC_SUBNET1=`awk 'NR==1' ${SUBNET_FILE}`
export EKS_PUBLIC_SUBNET2=`awk 'NR==2' ${SUBNET_FILE}`
export EKS_PRIVATE_SUBNET1=`awk 'NR==3' ${SUBNET_FILE}`
export EKS_PRIVATE_SUBNET2=`awk 'NR==4' ${SUBNET_FILE}`
export EKS_APP_ADMIN_NAME="flaskapp1-admin"
export EKS_APP_USER_NAME="flaskapp1-user"
export FLASK_ADMIN_IMAGE_NAME=`cat ~/Downloads/ecr_image.txt|grep "ADMIN APP" | awk '{print $5}'`
export FLASK_USER_IMAGE_NAME=`cat ~/Downloads/ecr_image.txt|grep "USER APP" | awk '{print $5}'`
