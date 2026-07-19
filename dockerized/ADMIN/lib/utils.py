#!/usr/bin/env python3
#Author: skondla@me.com

import boto3
import botocore
from botocore.exceptions import ClientError

def getPassword(secret_name,region):
    try:
        client = boto3.client('secretsmanager',region_name=region)
        response = client.get_secret_value(
            SecretId=secret_name
        )
        return response['SecretString']
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        print(error_code)
        if error_code == '404':
            print('Secret Namee: ' +  secret_name + ' does not exists!!')
