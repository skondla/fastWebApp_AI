#!/bin/bash
for i in {1..50} ; do curl --silent -X GET http://demonlb-b641f74013d481dd.elb.us-east-1.amazonaws.com; done
