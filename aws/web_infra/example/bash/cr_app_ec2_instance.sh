#!/bin/bash
#set -e
set -x
# #app subnet-id: subnet-06528b49fb9e23223 subnet-0e5b70a3b50f93b30 subnet-0edaf44aa9afe1b32
# APP_SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
#     --filters "Name=group-name,Values=app-security-group" \
#     --query 'SecurityGroups[0].GroupId' \
#     --output text \
#     --region ${REGION})
# echo ${APP_SECURITY_GROUP_ID}
# echo ${APP_SECURITY_GROUP_ID} > app_sg_id.sg

read -p "Enter Number of App EC2 instances: " NUMBER
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


APP_SG_GROUP_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=app-security-group" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region ${REGION})
echo ${APP_SG_GROUP_ID} > APP_SG_GROUP_ID.sg

for i in $(seq 1 ${NUMBER})
do
    INSTANCE_ID=$(aws ec2 run-instances \
    --instance-type t2.micro \
    --key-name ssh-key1-app-us-east-2 \
    --region ${REGION} \
    --subnet-id subnet-06528b49fb9e23223 \
    --image-id ami-0d0f28110d16ee7d6 \
    --security-group-ids ${APP_SG_GROUP_ID} \
    --no-associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2-app-instance}]' \
    --query 'Instances[0].InstanceId' \
    --output text \
    --user-data file://bootstrap2.sh)
    echo ${INSTANCE_ID}
    echo ${INSTANCE_ID} > ${INSTANCE_ID}-app.txt
done

# INSTANCE_ID=$(aws ec2 run-instances \
#     --instance-type t2.micro \
#     --key-name ssh-key1-app-us-east-2 \
#     --region ${REGION} \
#     --subnet-id subnet-06528b49fb9e23223 \
#     --image-id ami-0d0f28110d16ee7d6 \
#     --security-group-ids ${APP_SG_GROUP_ID} \
#     --no-associate-public-ip-address \
#     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2-app-instance-1}]' \
#     --query 'Instances[0].InstanceId' \
#     --output text \
#     --user-data file://bootstrap2.sh \
#     --count ${NUMBER})
# echo ${INSTANCE_ID}
    
# echo ${INSTANCE_ID} > ${INSTANCE_ID}-app.txt