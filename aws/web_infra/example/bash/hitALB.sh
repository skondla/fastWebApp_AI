#!/bin/bash
rm -f hitALB.log
#for i in {1..50} ; do curl --silent -X GET http://demoalb-194028509.us-east-1.elb.amazonaws.com; done
#for i in {1..60} ; do curl --silent -X GET http://demoalb-297342669.us-east-1.elb.amazonaws.com/; done > hitALB.log
#for i in {1..60} ; do curl -c cookie.txt --silent -X GET http://demoalb-297342669.us-east-1.elb.amazonaws.com/; done > hitALB.log
for i in {1..60} ; do curl -c cookie.txt --silent -kL -X GET https://demoalb-297342669.us-east-1.elb.amazonaws.com/; done > hitALB.log
echo "ip-172-31-25-3 count: `grep 'ip-172-31-25-3' hitALB.log | wc -l`";
echo "ip-172-31-23-5 count: `grep 'ip-172-31-23-65' hitALB.log | wc -l`";
echo "ip-172-31-19-204 count: `grep 'ip-172-31-19-204' hitALB.log | wc -l`";

