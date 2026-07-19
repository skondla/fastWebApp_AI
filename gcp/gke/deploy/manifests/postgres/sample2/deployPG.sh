#!/bin/bash
source ~/.secrets
envsubst < secret_pg.yaml | kubectl apply -f -
envsubst < csi_storage_class_pg.yaml | kubectl apply -f -
envsubst < csi_pvc_pg.yaml | kubectl apply -f -
#envsubst < pv_pg.yaml | kubectl apply -f -
#envsubst < pvc_pg.yaml | kubectl apply -f -
envsubst < deployment_pg.yaml | kubectl apply -f -
envsubst < service_pg.yaml | kubectl apply -f -
