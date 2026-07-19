#!/bin/bash
#Author: skondla@me.com
#Purpose: Check DB Restore Status


if [ $# -lt 2 ];
then
	echo "Provide snapshotname , db endpoint"
	echo "example: bash getDBRestoreStatus.sh custdb-aurora-2019-10-23-17-54-40 
	custdb-aurora-2019-10-23-17-54-40.cluster-mynet.us-east-1.rds.amazonaws.com"
exit 1
fi

snapshotname=${1}
endpoint=${2}

EMAIL=`cat ~/.password/mySecrets | grep email | awk '{print $2}'`
PASSWORD=`cat ~/.password/mySecrets | grep password | awk '{print $2}'`

/usr/bin/curl -k "https://localhost:50443/login" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --cookie "cookies.txt" \
    --cookie-jar "cookies.txt" \
    --verbose \
    > "login_log.html"

/usr/bin/curl -k "https://localhost:50443/status" \
    --data-urlencode "snapshotname=${snapshotname}" \
    --data-urlencode "endpoint=${endpoint}" \
    --cookie "cookies.txt" \
    --cookie-jar "cookies.txt"; \
    echo


#/usr/bin/curl -k "https://localhost:50443/status" \
#    --data-urlencode "snapshotname=custdb-aurora-2019-10-23-17-54-40" \
#    --data-urlencode "endpoint=custdb-aurora-2019-10-23-17-54-40.cluster-mynet.us-east-1.rds.amazonaws.com" \
#    --cookie "cookies.txt" \
#    --cookie-jar "cookies.txt"; \
#    echo

