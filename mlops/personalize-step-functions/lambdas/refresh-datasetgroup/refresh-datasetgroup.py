import os
from json import loads, dumps
from datetime import datetime
from boto3 import client

STEP_FUNCTIONS_CLI = client('stepfunctions')


def lambda_handler(event, context):
    bucket_name = event['bucket']
    
    # Execute DeployStateMachine
    response = STEP_FUNCTIONS_CLI.start_execution(
                    stateMachineArn=event['deployArn'],
                    name=datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                    input=dumps(
                        {
                            'bucket': bucket_name,
                            'currentDate': datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                            'params': event['params']
                        }
                    )
                )

    return response['executionArn']