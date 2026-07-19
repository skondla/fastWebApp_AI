#!/bin/bash -x
#Author: skondla@me.com
#Purpose run Docker container for FLask Auth App (DB Restore tool)

if [ $# -lt 1 ];
then
    echo "USAGE: bash $0 [containerName"]
    echo "example: $ bash dockerRunFlaskAuthAdmin.sh flaskauthadmin"
    echo "Please enter Constainer Name.  !!!Exiting !!!"
    exit 1
fi

containerName=${1}

#Remove old container if exists
if [[ `docker ps -a | grep ${containerName} | awk '{print $1}'|wc -l` -ge 1 ]]; then
    docker rm `docker ps -a | grep ${containerName} | awk '{print $1}'`
fi

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd ${SCRIPTPATH}
AWS_ACCESS_KEY_ID=`cat ~/.aws/credentials|grep aws_access_key_id | awk '{print $3}'`
AWS_SECRET_ACCESS_KEY=`cat ~/.aws/credentials|grep aws_secret_access_key | awk '{print $3}'`
REGION=`aws configure get region`
#postgres 
POSTGRES_HOST=`cat ~/.pgconfig | grep POSTGRES_HOST|awk '{print $2}'`
POSTGRES_PORT=`cat ~/.pgconfig | grep POSTGRES_PORT|awk '{print $2}'`
POSTGRES_USERNAME=`cat ~/.pgconfig | grep POSTGRES_USERNAME|awk '{print $2}'`
POSTGRES_PASSWORD=`cat ~/.pgconfig | grep POSTGRES_PASSWORD|awk '{print $2}'`
docker run \
 -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
 -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
 -e AWS_DEFAULT_REGION=${REGION} -d \
 -p 17344:30443 \
 -e POSTGRES_HOST=${POSTGRES_HOST} \
 -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
 -e POSTGRES_USERNAME=${POSTGRES_USERNAME} \
 -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
 --env-file ./env.sh \
 --name ${containerName} flaskauthadmin
 
