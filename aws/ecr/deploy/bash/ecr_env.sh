#!/bin/bash

export ECR_REPOSITORY="flaskapp1-demo-shop"
export ADMIN_APP_DIR="../../../../dockerized/ADMIN/"
export USER_APP_DIR="../../../../dockerized/USER/"
export AWS_ACCOUNT_ID=`aws sts get-caller-identity --query Account --output text`
export AWS_REGION=`cat ~/.aws/config | grep region | awk '{print $3}'`
export AWS_ACCESS_KEY_ID=`cat ~/.aws/credentials|grep aws_access_key_id | awk '{print $3}'`
export AWS_SECRET_ACCESS_KEY=`cat ~/.aws/credentials|grep aws_secret_access_key | awk '{print $3}'`
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export IMAGE_TAG=$(openssl rand -hex 32)
export EKS_APP_ADMIN_NAME="flaskapp1-admin"
export EKS_APP_USER_NAME="flaskapp1-user"