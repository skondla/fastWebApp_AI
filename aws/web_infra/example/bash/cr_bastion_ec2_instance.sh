#!/bin/bash
#set -e
set -x


read -p "Enter Number of Bastion EC2 instances: " NUMBER
echo "Hello, ${NUMBER} to be created!"
read -p "Enter region: " REGION
echo "You are in ${REGION}"


read -p "Are you sure you want to CREATE ${NUMBER} EC2 instances in region ${REGION} ? (y/n): " confirm
 if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    CONTINUE
    echo "Creating ${NUMBER} EC2 instances in region ${REGION}"
elif [[ "$confirm" == "n" || "$confirm" == "N" ]]; then
    echo "CANCELLED ${NUMBER} EC2 instances in region ${REGION} will NOT be created."
    exit 0
fi


INSTANCE_ID=$(aws ec2 run-instances \
    --instance-type t2.micro \
    --key-name ssh-key-new-us-east-2 \
    --region us-east-2 \
    --subnet-id subnet-09f74d4bd93ea0ab3 \
    --image-id ami-0d0f28110d16ee7d6 \
    --security-group-ids sg-09c2bb2ef4fb0187b \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2-instance-1}]' \
    --query 'Instances[0].InstanceId' \
    --output text \
    --user-data file://bootstrap2.sh \
    --count 1)
echo ${INSTANCE_ID}
    
echo ${INSTANCE_ID} > ${INSTANCE_ID}-bastion.txt