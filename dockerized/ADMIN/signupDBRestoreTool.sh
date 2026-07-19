#!/bin/bash
#Author: skondla@me.com
#Purpose: Sign up for DB Restore Tool

if [ $# -lt 2 ];
then
	echo "Provide email, full name"
	echo "example: bash signupDBRestoreTool.sh skondla@me.com 'Sudheer Kondla'"
exit 1
fi

EMAIL=${1}
FULLNAME=${2}
PASSWORD=`cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`
echo "${EMAIL}:${PASSWORD}" > $EMAIL.password

/usr/bin/curl -k "https://10.20.8.11:17344/signup" \
    --data-urlencode "email=${EMAIL}" \
    --data-urlencode "name=${FULLNAME}" \
    --data-urlencode "password=${PASSWORD}"; \
	echo

#echo "Hello" | mailx -s "Test Hello Flask" skondla@me.com

cat $EMAIL.password | mailx -s "DB Restore Credentials" $EMAIL
mv $EMAIL.password ~/secret/
