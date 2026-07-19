#!/usr/bin/env python
# Author: Sudheer Kondla, 04/21/17, skondla@me.com
# Purpose: RDS Instance Administration
# -*- coding: utf-8 -*-

import boto3
import sys
import json

class RDSCreate:

    def rds_create_db_cluster_snapshot(self, snapshotName, dbname, tagName):
        client = boto3.client('rds')
        response = client.create_db_cluster_snapshot(
            DBClusterSnapshotIdentifier=snapshotName, 
            DBClusterIdentifier=dbname,
            Tags=[
                {'Key': 'Name', 'Value': tagName}, 
                ]
        )
        print(response)

    def rds_create_db_snapshot(self, snapshotName, dbname, tagName):
        client = boto3.client('rds')
        response = client.create_db_snapshot(
            DBSnapshotIdentifier=snapshotName, 
            DBInstanceIdentifier=dbname,
            Tags=[
                {'Key': 'Name', 'Value': tagName}, 
                ]
        )
        print(response)
    
    def create_cluster_db_instance(self, *kwargs):
        client = boto3.client('rds')
        response = client.create_db_instance(
            DBInstanceIdentifier=kwargs[0],
            Engine=kwargs[1],
            EngineVersion=kwargs[2],
            DBSubnetGroupName=kwargs[3],
            VpcSecurityGroupIds=[
                kwargs[4],
            ],
            DBInstanceClass=kwargs[5],
        DBClusterIdentifier=kwargs[6]
        )
        print(response)   
         
    def create_db_cluster_instance(self,instanceName,clusterName,engine,engineVersion,instanceClass):
        client = boto3.client('rds')
        response = client.create_db_instance(
            DBInstanceClass=instanceClass,
            DBInstanceIdentifier=instanceName,
            Engine=engine,
            EngineVersion=engineVersion,
            DBClusterIdentifier=clusterName
        )
        print(response)

class RDSDelete:
    def rds_delete_db_cluster_snapshot(self, snapshotName):
        client = boto3.client('rds')
        response = client.delete_db_cluster_snapshot(DBClusterSnapshotIdentifier=snapshotName)
        print(response)

    def delete_db_snapshot(self,dbSnapshotName):
        client = boto3.client('rds')
        response = client.delete_db_snapshot(
            DBSnapshotIdentifier=dbSnapshotName
        )
        print(response)
 
class RDSDescribe:
    def rds_desc_db_instances(self, dbname):
        client = boto3.client('rds')
        response = client.describe_db_instances(DBInstanceIdentifier=dbname)
        print(response)
    
    def getDBInstanceStatus(self, dbname):
        client = boto3.client('rds')
        response = client.describe_db_instances(
            DBInstanceIdentifier=dbname
        )
        return response['DBInstances'][0]['DBInstanceStatus']

    def describe_db_cluster_snapshots(self, snapshotName):
        client = boto3.client('rds')
        response = client.describe_db_cluster_snapshots(
            DBClusterSnapshotIdentifier=snapshotName,
        )
        print(response)
    def db_cluster_snapshot_status(self, snapshotName):
        client = boto3.client('rds')
        response = client.describe_db_cluster_snapshots(
            DBClusterSnapshotIdentifier=snapshotName,
        )
        return response['DBClusterSnapshots'][0]['Status']

    #jsbeautifier response

    def describe_db_clusters(self, dbClusterName):
        client = boto3.client('rds')
        response = client.describe_db_clusters(
            DBClusterIdentifier=dbClusterName)
        print(response)

    def getDBClusterStatus(self, dbClusterName):
        client = boto3.client('rds')
        response = client.describe_db_clusters(
            DBClusterIdentifier=dbClusterName
        )
        return response['DBClusters'][0]['Status']

    def describe_db_snapshots(self, dbSnapshotName):
        client = boto3.client('rds')
        response = client.describe_db_snapshots(
        DBSnapshotIdentifier=dbSnapshotName
        )
        print(response)

    def db_snapshot_status(self, dbSnapshotName):
        client = boto3.client('rds')
        response = client.describe_db_snapshots(
        DBSnapshotIdentifier=dbSnapshotName
        )
        return response['DBSnapshots'][0]['Status']

    def dbInstanceInfo(self,instanceName):
        if 'cluster' in instanceName:
            instanceName = instanceName.split('.')[0]
            print ('instanceName: ' + instanceName)
            client = boto3.client('rds')
            response = client.describe_db_clusters(DBClusterIdentifier=instanceName)
            getDBInfo = list()
            getDBInfo.append(response['DBClusters'][0]['VpcSecurityGroups'][0]['VpcSecurityGroupId'])
            getDBInfo.append(response['DBClusters'][0]['DBSubnetGroup'])
            getDBInfo.append(response['DBClusters'][0]['Engine'])
            getDBInfo.append(response['DBClusters'][0]['DatabaseName'])
            getDBInfo.append(response['DBClusters'][0]['EngineVersion'])
            #print(getDBInfo)
            return getDBInfo
        else:
            instanceName = instanceName.split('.')[0]
            print ('instanceName: ' + instanceName)
            client = boto3.client('rds')
            response = client.describe_db_instances(DBInstanceIdentifier=instanceName)
            getDBInfo = list()
            getDBInfo.append(response['DBInstances'][0]['VpcSecurityGroups'][0]['VpcSecurityGroupId'])
            getDBInfo.append(response['DBInstances'][0]['DBSubnetGroup']['DBSubnetGroupName'])
            getDBInfo.append(response['DBInstances'][0]['Engine'])
            getDBInfo.append(response['DBInstances'][0]['DBName'])
            getDBInfo.append(response['DBInstances'][0]['EngineVersion'])
            getDBInfo.append(response['DBInstances'][0]['DBInstanceClass'])
            #print(getDBInfo)
            return getDBInfo


class RDSRestore:
    def restore_db_instance_from_db_snapshot(self, *kwargs):
        client = boto3.client('rds')
        response = client.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=kwargs[0],
            DBSnapshotIdentifier=kwargs[1],
            PubliclyAccessible=False,
            DBSubnetGroupName=kwargs[2],
            #VpcSecurityGroupIds=kwargs[3],
            VpcSecurityGroupIds=[
                kwargs[3],
            ],
            Engine=kwargs[4],
        #EngineVersion=kwargs[5],
        #DBInstanceClass=kwargs[6]
        DBInstanceClass=kwargs[5]
        )
        print(response)
        #return response['DBInstance'][0]['DBInstanceStatus']
    
    def restore_db_cluster_from_snapshot(self,*kwargs):
        client = boto3.client('rds')
        response = client.restore_db_cluster_from_snapshot(
            DBClusterIdentifier=kwargs[0],
            SnapshotIdentifier=kwargs[1],
            DBSubnetGroupName=kwargs[2],
            VpcSecurityGroupIds=[
                kwargs[3],
            ],
            Engine=kwargs[4],
        EngineVersion=kwargs[5]
        )
        print(response)
        #return response['DBCluster'][0]['Status']

