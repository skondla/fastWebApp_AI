#!/bin/bash
read -p "Enter Name of Security group to be DELETED!!: " SG_NAME
read -p "Enter Region: " REGION
echo "Hello, ${SG_NAME}!"
echo "You are in ${REGION}"
echo "Deleting Security Group ${SG_NAME} in region ${REGION}"

read -p "Are you sure you want to delete '$filename'? (y/n): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        aws ec2 delete-security-group --group-id ${SG_NAME} --region ${REGION}
        echo "Security Group ${SG_NAME} in region ${REGION} has been deleted."
    elif [[ "$confirm" == "n" || "$confirm" == "N" ]]; then
        echo "Security Group ${SG_NAME} in region ${REGION} has NOT been deleted."
    fi


