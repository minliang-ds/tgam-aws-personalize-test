import os
from json import loads, dumps
from datetime import datetime
from boto3 import client

STEP_FUNCTIONS_CLI = client('stepfunctions')


def get_files(bucket_name, prefix):
    list = []
    s3_result = client('s3').list_objects_v2(
        Bucket=bucket_name,
        Prefix=prefix
    )
    for key in s3_result['Contents']:
        if "params" in key['Key']:
            list.append(key['Key'])
            print("processing config:" + key['Key'])

    return list



def get_params(bucket_name, object):
    params = loads(
        client('s3').get_object(Bucket=bucket_name,
                                Key=object)['Body'].read().decode('utf-8')
    )
    return params


def lambda_handler(event, context):
    bucket_name = os.environ['INPUT_BUCKET']

    for object_name in get_files(bucket_name, os.environ['CONFIG_PREFIX']):
        dumps(
            STEP_FUNCTIONS_CLI.start_execution(
                stateMachineArn=os.environ['STEP_FUNCTIONS_ARN'],
                name=datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                input=dumps(
                    {
                        'bucket': bucket_name,
                        'currentDate': datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                        'params':
                            get_params(bucket_name, object_name)
                    }
                )
            ),
            default=str
        )
