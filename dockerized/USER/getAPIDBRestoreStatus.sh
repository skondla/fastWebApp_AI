#!/bin/bash
#Author: skondla@me.com
#Purpose: Check DB Restore Status


if [ $# -lt 2 ];
then
	echo "Provide snapshotname , db endpoint"
	echo "example: bash getDBRestoreStatus.sh custdb-stage-aurora-snapshot-2020-10-20-17-54-40 
	custdb-aurora-snapshot-2018-10-30-17-54-40.cluster-mynet.us-east-1.rds.amazonaws.com"
exit 1
fi

snapshotname=${1}
endpoint=${2}

EMAIL=`cat ~/.password/mySecrets2 | grep email | awk '{print $2}'`
PASSWORD=`cat ~/.password/mySecrets2 | grep password | awk '{print $2}'`

#/usr/bin/curl -k "https://localhost:50443/login" \
/usr/bin/curl -k "https://10.20.17.124:50443/login" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "password=${PASSWORD}" \
    --cookie "cookies.txt" \
    --cookie-jar "cookies.txt" \
    --verbose \
    > "login_log.html"

#/usr/bin/curl -k "https://localhost:50443/status" \
/usr/bin/curl -k "https://10.20.17.124:50443/status" \
    --data-urlencode "snapshotname=${snapshotname}" \
    --data-urlencode "endpoint=${endpoint}" \
    --cookie "cookies.txt" \
    --cookie-jar "cookies.txt"; \
    echo


#/usr/bin/curl -k "https://localhost:50443/status" \
#    --data-urlencode "snapshotname=custdb-stage-aurora-snapshot-2020-10-20-17-54-40" \
#    --data-urlencode "endpoint=custdb-aurora-snapshot-2018-10-30-17-54-40.cluster-mynet.us-east-1.rds.amazonaws.com" \
#    --cookie "cookies.txt" \
#    --cookie-jar "cookies.txt"; \
#    echo

