#!/bin/bash

###
SG_ID=$(aws ec2 create-security-group \
  --group-name app-security-group \
  --description "Security group for App host" \
  --vpc-id vpc-08696e4c5d00bd8dc \
  --region us-east-2 \
  --query 'GroupId' \
  --output text)
echo ${SG_ID}
echo ${SG_ID} > app_sg_id.txt

####

aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp \
  --port 22 \
  --cidr  10.1.0.0/16 \
  --region us-east-2

aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp \
  --port 80 \
  --cidr  10.1.0.0/16 \
  --region us-east-2

aws ec2 authorize-security-group-ingress \
  --group-id ${SG_ID} \
  --protocol tcp \
  --port 443 \
  --cidr  10.1.0.0/16 \
  --region us-east-2



# aws ec2 authorize-security-group-ingress \
#   --group-id ${SG_ID} \
#   --protocol tcp \
#   --port 3306 \
#   --cidr  162.198.11.200/32 \
#   --region us-east-2

#   aws ec2 authorize-security-group-ingress \
#   --group-id ${SG_ID} \
#   --protocol tcp \
#   --port 5432 \
#   --cidr  162.198.11.200/32 \
#   --region us-east-2