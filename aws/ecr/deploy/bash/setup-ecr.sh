#!/bin/bash
#Author: skondla@me.com
#Purpose: Create a Elastic Container Registry, Docker Build and instance of ECS cluster and deploy a container web application

#enviroment variables


#source ./ecr_env.sh

####################### Build and push the docker image #######################

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
########################################################################################

#Authenticate Docker to ECR
aws ecr get-login-password \
 --region ${AWS_REGION} | docker login --username AWS \
 --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

#Cretate ECR repo
aws ecr create-repository \
 --repository-name ${ECR_REPOSITORY} \
 --region ${AWS_REGION} \
 --image-scanning-configuration scanOnPush=true \
 --image-tag-mutability MUTABLE


# Build and push the docker image ADMIN application Image
imagename_admin=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG-admin

echo "Build and push ADMIN flask API application image $imagename_admin"
docker build -t $imagename_admin $ADMIN_APP_DIR

#Push image to ECR

echo "Build and push ADMIN flask API application image.." 
docker push $imagename_admin
echo "ADMIN APPLICATION image name: $imagename_admin" > ~/Downloads/flaskapp_ecr_image.txt
#echo "ADMIN APPLICATION image tag: $IMAGE_TAG" >> ~/Downloads/flaskapp_ecr_image.txt


# Build and push the docker image for USER application Image
imagename_user=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG-user

echo "Build and push USER flask API application image.."
echo "Build and push USER flask API application image $imagename_user"
docker build -t $imagename_user $USER_APP_DIR

#Push image to ECR
docker push $imagename_user
echo "USER APPLICATION image name: $imagename_user" >> ~/Downloads/flaskapp_ecr_image.txt
#echo "USER APPLICATION image tag: $IMAGE_TAG" >> ~/Downloads/flaskapp_ecr_image.txt