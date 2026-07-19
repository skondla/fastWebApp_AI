#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: RDS operation wrappers + notification helpers shared by the web-UI
#          router and the agent orchestrator. Extracted from main_router.py
#          so both callers can use the same logic without a circular import.
# -*- coding: utf-8 -*-

import datetime
import json
import os

import requests as http_requests

from rdsAdmin import RDSCreate, RDSDescribe, RDSRestore


def slack_post(snapshot_name: str, new_endpoint: str, db_state: str, action: str, username: str):
    webhook_url = os.environ.get(
        "SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/services/XXXX/XXXX/xyyyybbbbssssrm01",
    )
    today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    payload = {
        "channel": "@skondla",
        "username": username,
        "text": (
            f"{today}: {action} Database: {snapshot_name} is {db_state} "
            f"for dB Endpoint: {new_endpoint}"
        ),
        "icon_emoji": ":man-biking:",
    }
    try:
        resp = http_requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        if resp.status_code != 200:
            print(f"Slack error {resp.status_code}: {resp.text}")
    except Exception as exc:
        print(f"Slack post failed: {exc}")


def send_email(snapshot_name: str, endpoint: str, db_state: str):
    try:
        distro_file = "/app/email_distro"
        with open(distro_file) as f:
            email_distro = f.read().strip()
        os.system(
            f"echo 'dB: {snapshot_name} is {db_state} for dB: {endpoint}'"
            f" | mailx -s 'dB Restore' {email_distro}"
        )
    except Exception as exc:
        print(f"Email send failed: {exc}")


def db_status(endpoint: str, new_endpoint: str) -> str:
    if "cluster" in endpoint:
        return RDSDescribe().getDBClusterStatus(new_endpoint)
    return RDSDescribe().getDBInstanceStatus(new_endpoint)


def db_restore(snapshot_name: str, db_url: str) -> None:
    info = RDSDescribe().dbInstanceInfo(db_url)
    security_group = str(info[0])
    subnet = str(info[1])
    engine = str(info[2])
    engine_version = str(info[4])
    if "cluster" in db_url:
        RDSRestore().restore_db_cluster_from_snapshot(
            snapshot_name, snapshot_name, subnet, security_group, engine, engine_version
        )
    else:
        instance_class = str(info[5])
        RDSRestore().restore_db_instance_from_db_snapshot(
            snapshot_name, snapshot_name, subnet, security_group, engine, instance_class
        )


def db_attach(db_url: str, instance_class: str) -> str:
    today = datetime.datetime.now().strftime("%m%d-%H%M")
    cluster_name = db_url.split(".")[0]
    instance_name = f"{cluster_name}-{today}"
    info = RDSDescribe().dbInstanceInfo(db_url)
    engine = str(info[2])
    engine_version = str(info[4])
    RDSCreate().create_db_cluster_instance(
        instance_name, cluster_name, engine, engine_version, instance_class
    )
    return instance_name
