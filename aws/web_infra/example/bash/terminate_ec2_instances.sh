#!/bin/bash

read -p "Enter EC2 instance ID to be TERMINATED!: " EC2_INSTANCE_ID
echo "Hello, ${EC2_INSTANCE_ID} to be terminated!"
read -p "Enter region: " REGION
echo "You are in ${REGION}"


read -p "Are you sure you want to TERMINATE EC2 instance ${EC2_INSTANCE_ID} from region ${REGION} ? (y/n): " confirm
 if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    CONTINUE
    echo "TERMINATEING ... EC2 instance ${EC2_INSTANCE_ID} from region ${REGION}"
elif [[ "$confirm" == "n" || "$confirm" == "N" ]]; then
    echo "CANCELLED ... EC2 instance ${EC2_INSTANCE_ID} from region ${REGION} will NOT be TERMINATED, exiting..."
    exit 0
fi

aws ec2 terminate-instances --instance-ids ${EC2_INSTANCE_ID} --region ${REGION}
#terminate multiple ec2 instances
#aws ec2 terminate-instances --instance-ids i-0d3d27f3b0a0cbd14 i-0d3d27f3b0a0cbd15 --region us-east-2
