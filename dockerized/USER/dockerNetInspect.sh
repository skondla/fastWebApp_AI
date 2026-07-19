#!/bin/bash

for i in `docker info | grep Network | awk '{print $2,$3,$4,$5,$6,$7,$8}'`; do echo "network : $i"; docker network inspect $i; done
