#!/bin/bash

set -e

for iter in {1..10}
do
  echo "Iteration $iter: Testing ALB (HTTP Request)"
  # Add your test commands here
  curl -Ls http://app-lb-1870806161.us-west-2.elb.amazonaws.com/ | grep "ip-"
  sleep 1
done

for iter in {1..10}
do
  echo "Iteration $iter: Testing ALB (HTTPS Request)"
  # Add your test commands here
  curl -kLs https://app-lb-1870806161.us-west-2.elb.amazonaws.com/ | grep "ip-"
  sleep 1
done