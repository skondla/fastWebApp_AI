#!/bin/bash
source ~/.secrets
envsubst < secret_pg.yaml | kubectl apply -f -
envsubst < pv_pg.yaml | kubectl apply -f -
envsubst < pvc_pg.yaml | kubectl apply -f -
envsubst < deployment_pg.yaml | kubectl apply -f -
envsubst < service_pg.yaml | kubectl apply -f -
